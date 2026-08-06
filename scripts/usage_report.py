#!/usr/bin/env python3
"""
사용량·한도 상태 리포트 (미션 착수 전 점검 · LLM 호출 없음)
================================================================
누적 사용량과 **현재 한도 소진 여부**를 보고한다. 미션을 돌리기 전에 이것부터 본다.

⚠️ **왜 만들었나 — 실측(2026-08-05 · M-2026-005)**
   실미션 1차가 stage 4 에서 멈췄고 카드에 남은 것은
   `worker exited cleanly (rc=0) without calling kanban_complete — protocol violation` 뿐이었다.
   진짜 원인은 **LLM 사용량 한도 소진**(HTTP 429 `usage_limit_reached` · plan=team)이었고
   그것은 **세션 로그에만** 있었다. 카드만 봐서는 왜 멈췄는지 알 수 없다(docs/11 §7 ⑦).
   그리고 한도를 쓰는 줄 모르고 쓰다 소진됐다 — **보이지 않는 자원은 관리되지 않는다.**

⚠️ **이 스크립트는 LLM 을 호출하지 않는다.** 한도를 확인하려고 한도를 쓰면 안 된다.
   근거는 세 가지 기록물뿐이다:
     · `hermes insights` — 누적 세션·토큰(모델별)
     · `hermes-home/kanban/logs/*.log` — 워커 세션의 429 응답(`resets_at` 포함)
     · `hermes-home/auth.json` 의 `credential_pool` — **착수 가능 여부의 진실**

⚠️⚠️ **로그의 429 는 과거의 기록이지 현재의 판정이 아니다**(2026-08-06 추가).
   codex 계정을 하나 더 붙이자(`hermes auth add openai-codex`) 새 자격으로 추론이
   **성공하는데도** 이 스크립트가 `exit 1`("미션을 새로 시작하지 마라")을 냈다.
   로그 기록은 여전히 참이었다 — "그 자격이 그때 소진됐다". 다만 **착수 가능 여부와는
   무관해졌다.** 그래서 판정을 둘로 갈랐다:
     · **막을지 말지** → `credential_pool` 에 쓸 수 있는 자격이 하나라도 있는가
     · **왜 멈췄나**  → 로그의 429 기록(사후 진단용으로 계속 표시한다)
   풀을 읽을 수 없으면(구 설치·파일 없음) 옛 로그 기반 판정으로 폴백한다.

⚠️ **백엔드에 따라 무엇을 점검할지가 달라진다**(2026-08-05 추가 · `docs/14`).
   `scripts/set_backend.py` 로 로컬 Ollama 백엔드로 전환하면 **API 한도라는 것이 없다.**
   그런데 로그의 429 `resets_at` 은 그대로 남아 있어, 그것만 보면 리셋 시각까지 계속
   `exit 1` 이 나온다 — 로컬로 옮긴 의미가 사라진다. 그래서 활성 백엔드를 먼저 읽고:
     · `codex`  → 한도 소진 여부(기존 판정)
     · `ollama` → **Ollama 서버 도달 + 배치 모델 설치 여부**(한도 판정은 참고로만 표시)
   로컬 점검도 LLM 을 호출하지 않는다 — `/api/tags` 는 메타데이터 조회다.

사용
  python3 scripts/usage_report.py               # 사람이 읽는 요약
  python3 scripts/usage_report.py --json        # 기계 판독
  python3 scripts/usage_report.py --quiet       # exit code 만 (미션 착수 전 점검용)

exit: 0 정상 · 1 **착수 불가**(codex=한도 소진 · ollama=서버 불통/모델 없음) · 2 근거를 읽지 못함
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import set_backend as sb  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIRS = [os.path.join(REPO_ROOT, "hermes-home", "kanban", "logs"),
            "/opt/data/kanban/logs"]
# pooled 자격(`hermes auth add`). 호스트 경로 → 컨테이너 경로 순.
AUTH_PATHS = [os.path.join(REPO_ROOT, "hermes-home", "auth.json"),
              "/opt/data/auth.json"]

# 로컬 백엔드 점검용. 호스트에서 도는 것을 전제로 한다(컨테이너에서는
# host.docker.internal 을 쓴다 — set_backend.BACKENDS 의 base_url 참조).
OLLAMA_URL = os.environ.get("OLLAMA_PROBE_URL", "http://127.0.0.1:11434")

# 429 본문. resets_at 은 epoch 초.
# ⚠️ plan_type 을 같은 정규식의 **선택 그룹**으로 두면 비탐욕 매칭이 그것을 건너뛰고
#    바로 resets_at 으로 간다(실측: 항상 plan=? 였다). 매칭 구간 안에서 따로 찾는다.
LIMIT_RE = re.compile(
    r"'type':\s*'(?P<type>usage_limit_reached|rate_limit\w*)'.*?"
    r"'resets_at':\s*(?P<resets>\d+)", re.DOTALL)
PLAN_RE = re.compile(r"'plan_type':\s*'([^']*)'")
# 인증 실패 — 429 와 함께 '환경성 실패' 로 묶는다(파이프라인 결함이 아니다)
AUTH_RE = re.compile(r"(401 Unauthorized|invalid_api_key|authentication_error|"
                     r"credentials? (?:expired|invalid))", re.IGNORECASE)


def hermes_bin() -> list[str]:
    if shutil.which("hermes"):
        return ["hermes"]
    return ["docker", "exec", "hermes-solomon", "hermes"]


def insights() -> dict:
    """`hermes insights` 요약. 실패해도 치명적이지 않다(한도 판정의 근거가 아니다)."""
    try:
        p = subprocess.run(hermes_bin() + ["insights"], capture_output=True, text=True,
                           timeout=60)
        out = p.stdout
    except (OSError, subprocess.SubprocessError):
        return {}
    d: dict = {}
    m = re.search(r"Period:\s*(.+)", out)
    if m:
        d["period"] = m.group(1).strip()
    for key, pat in (("sessions", r"Sessions:\s*([\d,]+)"),
                     ("total_tokens", r"Total tokens:\s*([\d,]+)"),
                     ("input_tokens", r"Input tokens:\s*([\d,]+)"),
                     ("output_tokens", r"Output tokens:\s*([\d,]+)")):
        m = re.search(pat, out)
        if m:
            d[key] = int(m.group(1).replace(",", ""))
    models = re.findall(r"^\s{2}(\S+)\s+(\d+)\s+([\d,]+)\s*$", out, re.MULTILINE)
    if models:
        d["models"] = [{"model": a, "sessions": int(b), "tokens": int(c.replace(",", ""))}
                       for a, b, c in models]
    return d


def log_files() -> list[str]:
    for d in LOG_DIRS:
        if os.path.isdir(d):
            return [os.path.join(d, f) for f in os.listdir(d) if f.endswith(".log")]
    return []


def scan_limits(paths: list[str]) -> tuple[dict | None, list[str]]:
    """가장 최근의 한도 소진 기록과, 환경성 실패가 있는 task 목록."""
    latest: dict | None = None
    env_failed: list[str] = []
    for p in paths:
        try:
            text = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        tid = os.path.basename(p)[:-4]
        hit = None
        for m in LIMIT_RE.finditer(text):
            plan = PLAN_RE.search(m.group(0))
            hit = {"task": tid, "type": m.group("type"),
                   "plan": plan.group(1) if plan else "",
                   "resets_at": int(m.group("resets")),
                   "mtime": os.path.getmtime(p)}
        if hit:
            env_failed.append(tid)
            if latest is None or hit["resets_at"] > latest["resets_at"] \
                    or hit["mtime"] > latest["mtime"]:
                latest = hit
        elif AUTH_RE.search(text):
            env_failed.append(tid)
    return latest, sorted(set(env_failed))


# ── pooled 자격 (2026-08-06) ───────────────────────────────────────────────
# ⚠️⚠️ **로그의 429 는 과거의 기록이지 현재의 판정이 아니다.**
#    2026-08-06 에 codex 계정을 하나 더 붙였더니(`hermes auth add openai-codex`)
#    새 자격으로 추론이 **성공**하는데도 이 스크립트가 `exit 1` 을 냈다. 로그 기록은
#    여전히 참이었다 — "그 자격이 그때 소진됐다". 다만 착수 가능 여부와는 무관해졌다.
#    → 착수 판정의 진실은 `auth.json` 의 `credential_pool` 이다. 로그는 **왜 멈췄나**를
#      설명하는 사후 근거로 계속 쓰되, **막을지 말지**는 풀이 정한다.
def backend_provider(backend: str) -> str:
    """백엔드 이름 → provider id. `set_backend.PROVIDER_TO_BACKEND` 를 뒤집는다.

    ⚠️ provider 이름을 여기에 두 번째로 적지 마라 — 배치표는 한 곳에만 있다."""
    for prov, be in sb.PROVIDER_TO_BACKEND.items():
        if be == backend and prov != "custom":   # custom 은 alias 라 자격의 주인이 아니다
            return prov
    return ""


def read_credential_pool(provider: str, paths: list[str] | None = None) -> list[dict] | None:
    """`auth.json` 의 pooled 자격 요약. 판정할 근거가 없으면 **None**(≠ 빈 리스트).

    반환값은 `{id,label,status,reset_at,reason}` 뿐이다 —
    ⚠️ **토큰 값을 절대 담지 마라.** 이 저장소는 PUBLIC 이고 `--json` 출력은 로그·문서에
       붙여진다. `SLACK_BOT_TOKEN` 이 세션 로그에 노출된 이력이 이미 있다(CLAUDE.md).

    None 을 돌려주는 경우(= '모른다', 로그 기반 판정으로 폴백):
      · auth.json 이 없거나 읽을 수 없다
      · `credential_pool` 키 자체가 없다(풀을 안 쓰는 구 설치)
      · 그 provider 를 풀이 관리하지 않는다
    빈 리스트를 돌려주는 경우(= '자격이 없다', 착수 불가): 키는 있는데 항목이 0개.
    """
    if not provider:
        return None
    for p in (paths if paths is not None else AUTH_PATHS):
        try:
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        pool = d.get("credential_pool")
        if not isinstance(pool, dict) or provider not in pool:
            return None
        entries = pool.get(provider) or []
        out = []
        for e in entries:
            if not isinstance(e, dict):
                continue
            reset = e.get("last_error_reset_at")
            out.append({
                "id": e.get("id") or "?",
                "label": e.get("label") or "?",
                "status": e.get("last_status"),
                "reset_at": int(reset) if isinstance(reset, (int, float)) else None,
                "reason": e.get("last_error_reason") or "",
            })
        return out
    return None


def pool_verdict(creds: list[dict] | None, now: int) -> dict:
    """풀 기준 착수 가능 판정. `known=False` 면 판정하지 않았다는 뜻이다(폴백하라).

    자격 하나가 '쓸 수 있다'는 것은 **상태 문자열이 아니라 시계**로 정한다 —
    `exhausted` 로 표시돼 있어도 `reset_at` 이 지났으면 다시 쓸 수 있다."""
    if creds is None:
        return {"known": False, "usable": 0, "total": 0, "creds": []}
    usable = 0
    for c in creds:
        exhausted = (c.get("status") == "exhausted"
                     and (c.get("reset_at") or 0) > now)
        c["usable"] = not exhausted
        usable += 0 if exhausted else 1
    return {"known": True, "usable": usable, "total": len(creds), "creds": creds}


def ollama_tags(url: str = "") -> tuple[list[str] | None, str]:
    """(설치된 모델 태그 목록, 오류). LLM 을 호출하지 않는다 — /api/tags 는 메타데이터다."""
    base = (url or OLLAMA_URL).rstrip("/")
    try:
        with urllib.request.urlopen(base + "/api/tags", timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError, TimeoutError) as exc:
        return None, f"{type(exc).__name__}: {exc}"
    return [m.get("name", "") for m in (data.get("models") or [])], ""


def ollama_ps(url: str = "") -> tuple[list[dict] | None, str]:
    """(현재 **로드된** 모델 목록, 오류). `/api/ps` 는 메타데이터다 — LLM 을 호출하지 않는다."""
    base = (url or OLLAMA_URL).rstrip("/")
    try:
        with urllib.request.urlopen(base + "/api/ps", timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError, TimeoutError) as exc:
        return None, f"{type(exc).__name__}: {exc}"
    return list(data.get("models") or []), ""


def check_runtime(url: str = "") -> dict:
    """**서버가 실제로 무엇을 서빙하는가** — config 가 주장하는 값과 대조한다.

    ⚠️ 왜 필요한가(docs/14 §3.1 이 실제로 밟은 실패):
       파생본 이름을 그대로 둔 채 `OLLAMA_NUM_CTX` 만 올리면 `--build-models` 가
       "이미 있음"을 찍고 **서버는 옛 창을 계속 서빙한다.** config 는 새 값을 주장하고
       서버는 옛 값을 준다 — 두 층 떨어진 실패라 증상만 보고는 못 찾는다.
       그래서 **파일이 아니라 서버가 보고하는 값**(`/api/ps`)을 본다.

    ⚠️ 판정하지 못하는 것은 WARN 으로도 만들지 않는다:
       모델이 아직 로드되지 않았으면 창을 알 수 없다(`loaded: []`) — 그건 정상이다.
    """
    host = sb.host_env_state()          # 걸어 놨는가 (launchctl)
    server = sb.server_env_state()      # **반영됐는가** (서버 기동 배너) ← 이쪽이 권위다
    loaded, err = ollama_ps(url)
    # ⚠️ **배치 모델만** 대조한다. 프로브·다른 작업이 올린 모델까지 경고하면 소음이 되고,
    #    소음이 나는 검사는 곧 무시된다(그러면 진짜 불일치도 같이 묻힌다).
    batch = set(sb.backend_models("ollama"))
    ctx_mismatch = []
    for m in (loaded or []):
        name = m.get("name", "")
        if name not in batch and name.split(":")[0] not in batch:
            continue
        got = m.get("context_length")
        if got is not None and got != sb.OLLAMA_NUM_CTX:
            ctx_mismatch.append({"model": name or "?", "serving": got,
                                 "expected": sb.OLLAMA_NUM_CTX})
    # 걸어 놨는데 반영이 안 된 것 — 재시작만 하면 되는 상태다. 진단이 처방으로 이어지도록
    # 이 조합을 따로 이름 붙여 둔다("설정은 맞는데 왜 느리지"가 가장 오래 걸리는 질문이다).
    pending = []
    if host["available"] and server["available"]:
        want_ok = {r["var"] for r in host["vars"] if r["ok"]}
        pending = [r for r in server["mismatched"] if r["var"] in want_ok]
    return {
        "host_env_available": host["available"],
        "host_env_mismatched": host["mismatched"],
        "server_env_available": server["available"],
        "server_env_mismatched": server["mismatched"],
        "restart_pending": pending,
        "loaded": [{"name": m.get("name", "?"),
                    "context_length": m.get("context_length"),
                    "size_gb": round(m.get("size", 0) / 1e9, 2)} for m in (loaded or [])],
        "context_mismatch": ctx_mismatch,
        "error": err,
    }


def check_local(backend: str, url: str = "") -> dict:
    """로컬 백엔드의 착수 가능 여부. 근거는 두 가지뿐이다 — 서버 도달 · 모델 존재."""
    want = sb.backend_models(backend)
    tags, err = ollama_tags(url)
    if tags is None:
        return {"reachable": False, "error": err, "wanted": want,
                "missing": want, "installed": []}
    # `qwen3.6:35b` 와 `qwen3.6:35b` 는 같지만, ollama 는 `:latest` 를 생략해 보고하기도 한다.
    have = set(tags) | {t.split(":")[0] for t in tags if t.endswith(":latest")}
    missing = [m for m in want if m not in have and f"{m}:latest" not in have]
    return {"reachable": True, "error": "", "wanted": want,
            "missing": missing, "installed": tags}


def main_local(args, backend: str) -> int:
    """로컬 백엔드 착수 점검 — 한도가 아니라 **모델이 거기 있는지**를 본다."""
    local = check_local(backend, args.ollama_url)
    ok = local["reachable"] and not local["missing"]
    # ⚠️ 런타임 점검은 **착수를 막지 않는다**(WARN 전용). 서버 설정이 어긋나도 미션은
    #    돌아간다 — 다만 조용히 느려지거나(병렬 미설정) 조용히 잘린다(창 불일치).
    #    막지 않는 대신 **반드시 보이게** 한다.
    runtime = check_runtime(args.ollama_url) if local["reachable"] else {}
    # 과거 codex 소진 기록은 참고용으로 계속 읽는다(복귀 시점 판단에 쓴다).
    latest, env_failed = scan_limits(log_files())
    now = args.now if args.now is not None else int(dt.datetime.now().timestamp())
    report = {
        "backend": backend,
        "exhausted": False,          # 로컬은 한도가 없다
        "local": local,
        "runtime": runtime,          # 서버가 실제로 서빙하는 것(WARN 전용)
        "limit_record": latest,      # 참고: codex 복귀 시 이 시각 이후여야 한다
        "seconds_to_reset": max(0, latest["resets_at"] - now) if latest else 0,
        "env_failed_tasks": env_failed,
        "insights": insights() if not args.quiet else {},
        "log_files": len(log_files()),
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if ok else 1
    if args.quiet:
        return 0 if ok else 1

    print(f"── 백엔드 ──  {backend} (로컬) — API 한도 없음")
    print(f"  모델: {', '.join(local['wanted'])}")
    print("── 로컬 준비 상태 ──")
    if not local["reachable"]:
        print(f"  ⚠️ Ollama 서버에 닿지 않는다 ({args.ollama_url or OLLAMA_URL}) — {local['error']}")
        print("     → Ollama 를 켜라. 이 상태로 미션을 걸면 워커가 매 턴 실패한다.")
    elif local["missing"]:
        print(f"  ⚠️ 모델 없음: {', '.join(local['missing'])}")
        print(f"     → ollama pull {local['missing'][0]}")
    else:
        print(f"  ✓ 서버 도달 · 배치 모델 {len(local['wanted'])}종 모두 설치됨")

    # ── 서버 런타임 설정 (WARN 전용 — 착수는 막지 않는다) ──
    if runtime:
        print("── 서버 설정 ──")
        # ⚠️ 판정의 근거는 **서버 기동 배너**다. launchctl 은 "걸어 놨다"일 뿐이고,
        #    실제로 그 둘이 어긋난 채 몇 세션이 지나간 적이 있다(docs/14 §5.1).
        if not runtime["server_env_available"]:
            print("  ℹ️ Ollama 서버 로그를 읽지 못해 실효 설정을 확인하지 못했다"
                  " (컨테이너에서 실행 중이면 정상 — 호스트에서 다시 보라)")
        elif runtime["restart_pending"]:
            for r in runtime["restart_pending"]:
                print(f"  ⚠️ {r['var']} — launchctl 은 {r['want']} 인데 **서버는 {r['have']}**")
            print("     → 걸어 놨지만 **반영되지 않았다.** Ollama 를 재시작하라:")
            print("       osascript -e 'quit app \"Ollama\"' && sleep 3 && open -a Ollama")
        elif runtime["server_env_mismatched"]:
            for r in runtime["server_env_mismatched"]:
                print(f"  ⚠️ {r['var']} = {r['have']} — 기대값 {r['want']}")
            print("     → python3 scripts/set_backend.py --host-setup  (그 뒤 Ollama 재시작)")
        else:
            print(f"  ✓ 서버 실효 설정 {len(sb.HOST_ENV)}종 일치"
                  f" (NUM_PARALLEL={sb.HOST_ENV['OLLAMA_NUM_PARALLEL']}"
                  f" · KV={sb.HOST_ENV['OLLAMA_KV_CACHE_TYPE']})")
        if runtime["server_env_mismatched"]:
            print("     ⚠️ NUM_PARALLEL 이 어긋나면 스테이지 내 팬아웃이 **조용히 직렬화**된다"
                  " — `probe_parallel.py` 로 확인하라")
        for r in runtime["host_env_mismatched"]:
            if r.get("why"):
                print(f"  ⚠️ {r['var']} = {r['have']} — 설정하면 안 된다: {r['why']}")
        for m in runtime["context_mismatch"]:
            print(f"  ⚠️ {m['model']} 이 **창 {m['serving']}** 로 서빙 중 — 배치는 {m['expected']}")
            print("     → 파생본이 옛 창을 물고 있다. 이름(-256k)을 바꿔 다시 만들어라(docs/14 §3.1)")
        for m in runtime["loaded"]:
            print(f"  · 로드됨: {m['name']} · 창 {m['context_length']} · {m['size_gb']}GB")
        if not runtime["loaded"]:
            print("  · 로드된 모델 없음 — 창은 첫 요청 뒤에 확인할 수 있다")

    if latest:
        when = dt.datetime.fromtimestamp(latest["resets_at"]).strftime("%Y-%m-%d %H:%M")
        state = "리셋 전" if latest["resets_at"] > now else "리셋됨"
        print(f"── 참고: codex 한도 ──  {when} {state} "
              f"(복귀는 `set_backend.py --backend codex`)")
    ins = report["insights"]
    if ins:
        print("── 누적 사용량 ──")
        print(f"  기간 {ins.get('period', '?')} · 세션 {ins.get('sessions', '?')} · "
              f"총 토큰 {ins.get('total_tokens', 0):,}")
    return 0 if ok else 1


# ── 업스트림 잔량 (2026-08-06) ──────────────────────────────────────────────
# ⚠️ Hermes 는 잔량을 **기록하지 않는다** — codex 응답의 rate-limit 헤더를 읽는 코드가
#    없고(`usage_limit` 문자열 매칭은 429 처리에만 있다) `hermes insights` 는 계정별로
#    가르지 못한다(`--days`·`--source` 뿐). 그래서 업스트림에 직접 묻는다.
# ⚠️⚠️ **400 응답에는 헤더가 안 온다**(실측). 추론이 실제로 시작돼야 `x-codex-*` 가 붙는다
#    → 잔량 조회는 **공짜가 아니다.** 그래서 캐시를 두고 상시 표시는 캐시만 읽는다.
QUOTA_CACHE = os.path.join(REPO_ROOT, "hermes-home", "codex_quota.json")
QUOTA_HEADERS = (
    "x-codex-plan-type", "x-codex-active-limit",
    "x-codex-primary-used-percent", "x-codex-primary-window-minutes",
    "x-codex-primary-reset-at", "x-codex-secondary-used-percent",
    "x-codex-secondary-window-minutes", "x-codex-secondary-reset-at",
    "x-codex-credits-balance", "x-codex-credits-unlimited",
)


def parse_quota_headers(headers: dict, cred_id: str = "", now: int = 0) -> dict:
    """`x-codex-*` 응답 헤더 → 잔량 요약. 순수 함수(네트워크 없음 = 테스트 가능).

    ⚠️ 헤더 이름은 대소문자를 가리지 않는다 — 서버가 바꿔 보내도 깨지지 않게 정규화한다.
    ⚠️ 값이 빈 문자열인 헤더가 실제로 온다(`x-codex-secondary-reset-at:`) — int() 가 터진다."""
    low = {str(k).lower(): str(v) for k, v in (headers or {}).items()}

    def num(key):
        v = low.get(key, "").strip()
        try:
            return int(float(v))
        except (TypeError, ValueError):
            return None

    return {
        "credential": cred_id,
        "checked_at": now,
        "plan": low.get("x-codex-plan-type", "") or "",
        "active_limit": low.get("x-codex-active-limit", "") or "",
        "primary_used_pct": num("x-codex-primary-used-percent"),
        "primary_window_min": num("x-codex-primary-window-minutes"),
        "primary_reset_at": num("x-codex-primary-reset-at"),
        "secondary_used_pct": num("x-codex-secondary-used-percent"),
        "secondary_window_min": num("x-codex-secondary-window-minutes"),
        "secondary_reset_at": num("x-codex-secondary-reset-at"),
        "credits_balance": num("x-codex-credits-balance"),
        "found": any(k.startswith("x-codex-") for k in low),
    }


def format_quota(q: dict | None, now: int) -> str:
    """잔량 한 조각. 창 길이를 사람 단위로 옮긴다(10080분 = 주간)."""
    if not q or not q.get("found"):
        return ""
    parts = []
    for tag, pct, win, reset in (
            ("", q.get("primary_used_pct"), q.get("primary_window_min"), q.get("primary_reset_at")),
            ("2차 ", q.get("secondary_used_pct"), q.get("secondary_window_min"),
             q.get("secondary_reset_at"))):
        if pct is None or not win:      # 창 0 = 그 한도는 비활성
            continue
        label = {10080: "주간", 1440: "일간", 300: "5시간", 60: "시간"}.get(win, f"{win}분")
        seg = f"{tag}{label} {pct}%"
        if reset:
            seg += f"(리셋 {dt.datetime.fromtimestamp(reset).strftime('%m-%d %H:%M')})"
        parts.append(seg)
    age = ""
    if q.get("checked_at"):
        mins = max(0, (now - q["checked_at"]) // 60)
        age = f" · {mins}분 전" if mins else " · 방금"
    return (" · ".join(parts) + age) if parts else ""


def load_quota_cache(path: str | None = None) -> dict | None:
    try:
        with open(path or QUOTA_CACHE, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def probe_codex_quota(now: int, auth_paths: list[str] | None = None,
                      cache_path: str | None = None) -> dict | None:
    """업스트림에 최소 요청 1회를 보내 잔량 헤더를 읽고 캐시에 쓴다.

    ⚠️ **한도를 소비한다**(작지만 0 이 아니다). 상시 표시 경로에서 부르지 마라 —
       `--live` 로만 부른다. 실패는 None(호출자가 캐시로 폴백)."""
    for p in (auth_paths if auth_paths is not None else AUTH_PATHS):
        try:
            with open(p, encoding="utf-8") as f:
                store = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        entries = (store.get("credential_pool") or {}).get("openai-codex") or []
        # 런타임과 **같은 규칙**으로 고른다: 리스트 순서대로, 쿨다운이 아닌 첫 항목
        # (auth.py:4280 `_pool_codex_access_token`). priority 는 codex 경로에서 안 쓴다.
        pick = next((e for e in entries if isinstance(e, dict) and e.get("access_token")
                     and not (isinstance(e.get("last_error_reset_at"), (int, float))
                              and e["last_error_reset_at"] > now)), None)
        if not pick:
            return None
        body = json.dumps({
            "model": os.environ.get("USAGE_PROBE_MODEL", "gpt-5.6-terra"),
            "instructions": "",
            "input": [{"type": "message", "role": "user",
                       "content": [{"type": "input_text", "text": "hi"}]}],
            "stream": True, "store": False,
        }).encode()
        req = urllib.request.Request(
            f"{pick.get('base_url') or 'https://chatgpt.com/backend-api/codex'}/responses",
            data=body, method="POST",
            headers={"Authorization": f"Bearer {pick['access_token']}",
                     "Content-Type": "application/json", "Accept": "text/event-stream",
                     "User-Agent": "codex-cli/1.0", "originator": "codex_cli_rs"})
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                hdrs = dict(r.headers.items())
                r.read(1)          # 스트림을 끝까지 읽지 않는다 — 헤더만 필요하다
        except urllib.error.HTTPError as e:
            hdrs = dict(e.headers.items())
        except Exception:          # noqa: BLE001 — 잔량 조회 실패가 점검을 막지 않는다
            return None
        q = parse_quota_headers(hdrs, cred_id=pick.get("id") or "", now=now)
        if not q["found"]:
            return None
        try:
            with open(cache_path or QUOTA_CACHE, "w", encoding="utf-8") as f:
                json.dump(q, f, ensure_ascii=False)
        except OSError:
            pass
        return q
    return None


def brief_line(backend: str, now: int, paths: list[str] | None = None,
               quota: dict | None = None) -> str:
    """한 줄 요약. **파일 하나만 읽는다** — subprocess·네트워크 없음.

    ⚠️ 상시 표시(statusline·hook)에 쓰려고 만들었다. `main()` 은 `hermes insights` 를
       `docker exec` 로 부르므로 초 단위가 걸린다 — 매 렌더마다 부를 수 없다.
       여기서는 `insights` 도 로그 스캔도 하지 않는다."""
    prov = backend_provider(backend)
    if backend != "codex":
        return f"{backend} · 한도 없음(로컬)"
    pv = pool_verdict(read_credential_pool(prov, paths), now)
    if not pv["known"]:
        return "codex · 자격 풀 정보 없음"
    ok = [c for c in pv["creds"] if c["usable"]]
    if not ok:
        nxt = min((c["reset_at"] for c in pv["creds"] if c["reset_at"]), default=None)
        when = dt.datetime.fromtimestamp(nxt).strftime("%m-%d %H:%M") if nxt else "?"
        h = f" ({(nxt - now) / 3600:.0f}h)" if nxt else ""
        return f"codex ⚠️ 소진 0/{pv['total']} · 리셋 {when}{h}"
    tail = ""
    spent = [c for c in pv["creds"] if not c["usable"] and c["reset_at"]]
    if spent:
        w = dt.datetime.fromtimestamp(min(c["reset_at"] for c in spent)).strftime("%m-%d %H:%M")
        tail = f" · 소진 {len(spent)} 리셋 {w}"
    # ⚠️ 캐시된 잔량은 **그 자격의 것**이다. 활성 자격이 바뀌었는데 옛 잔량을 붙이면
    #    남의 숫자를 자기 것으로 읽는다 — id 가 일치할 때만 붙인다.
    #    `ok[0]` 은 런타임의 선택과 같다(리스트 순서 · auth.py:4280).
    q = format_quota(quota, now) if quota and quota.get("credential") == ok[0]["id"] else ""
    return f"codex ✓ {pv['usable']}/{pv['total']} [{ok[0]['label']}]{tail}" + (f" · {q}" if q else "")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--brief", action="store_true",
                    help="한 줄 요약만(파일 1개만 읽는다 — statusline·hook 용)")
    ap.add_argument("--live", action="store_true",
                    help="업스트림에 물어 잔량을 갱신한다 ⚠️ 한도를 소비한다(최소 요청 1회)")
    ap.add_argument("--json", action="store_true", help="기계 판독 출력")
    ap.add_argument("--quiet", action="store_true", help="exit code 만")
    ap.add_argument("--now", type=int, default=None,
                    help="현재 시각(epoch) 주입 — 테스트용. 미지정 시 시스템 시계")
    ap.add_argument("--repo-root", default=REPO_ROOT, help="저장소 루트(테스트용)")
    ap.add_argument("--ollama-url", default="", help="로컬 백엔드 점검 URL(테스트용)")
    ap.add_argument("--backend", choices=["auto", "codex", "ollama"], default="auto",
                    help="점검 대상 백엔드. 기본 auto = config 에서 판정")
    args = ap.parse_args()

    # ── 어느 백엔드인가 ──
    # 로컬(ollama) 이면 codex 한도는 착수 판정의 근거가 아니다. 소진 기록은 리셋 후 복귀
    # 판단에 필요하므로 계속 **보여주되**, exit code 는 로컬 준비 상태로 정한다.
    backend = args.backend if args.backend != "auto" else sb.active_backend(args.repo_root)
    if args.brief:
        # ⚠️ 상시 표시는 **판정을 막지 않는다** — exit 0 고정. 표시가 착수를 막으면
        #    사람이 그것을 끄게 되고, 그러면 진짜 판정도 같이 사라진다.
        now = args.now if args.now is not None else int(dt.datetime.now().timestamp())
        # ⚠️ 기본은 **캐시만** 읽는다 — 상시 표시가 매번 한도를 쓰면 안 된다.
        quota = (probe_codex_quota(now) if args.live else None) or load_quota_cache()
        line = brief_line(backend, now, quota=quota)
        # `--brief --json` = Claude Code 훅 형식. 셸에서 따옴표를 겹쳐 JSON 을 짓는 것보다
        # 여기서 만드는 편이 안전하다(줄바꿈·따옴표·이모지가 그대로 통과한다).
        print(json.dumps({"systemMessage": line}, ensure_ascii=False) if args.json else line)
        return 0
    if backend in ("ollama",):
        return main_local(args, backend)

    paths = log_files()
    if not paths:
        if not args.quiet:
            print("FAIL(usage): 워커 로그를 찾지 못했다 "
                  f"({' 또는 '.join(LOG_DIRS)}) — 소진 여부를 판단할 근거가 없다",
                  file=sys.stderr)
        return 2

    now = args.now if args.now is not None else int(dt.datetime.now().timestamp())
    latest, env_failed = scan_limits(paths)
    ins = insights()

    # 로그는 '왜 멈췄나'를 설명하고, 풀은 '지금 돌릴 수 있나'를 정한다. 둘은 다른 질문이다.
    log_exhausted = bool(latest and latest["resets_at"] > now)
    pv = pool_verdict(read_credential_pool(backend_provider(backend)), now)
    exhausted = (pv["usable"] == 0) if pv["known"] else log_exhausted
    # ⚠️ `--live` 없이는 업스트림에 묻지 않는다 — 점검이 한도를 쓰면 안 된다(캐시만 읽는다).
    quota = (probe_codex_quota(now) if args.live else None) or load_quota_cache()
    report = {
        "backend": backend,
        "exhausted": exhausted,
        "limit_record": latest,
        "log_exhausted": log_exhausted,
        "credential_pool": pv,
        "quota": quota,
        "seconds_to_reset": (latest["resets_at"] - now) if log_exhausted else 0,
        "env_failed_tasks": env_failed,
        "insights": ins,
        "log_files": len(paths),
    }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif not args.quiet:
        print(f"── 백엔드 ──  {backend}"
              + ("   ⚠️ 프로필마다 백엔드가 다르다 — `set_backend.py --show`"
                 if backend == "mixed" else ""))
        print("── 사용량 ──")
        if ins:
            print(f"  기간 {ins.get('period', '?')} · 세션 {ins.get('sessions', '?')} · "
                  f"총 토큰 {ins.get('total_tokens', 0):,} "
                  f"(입력 {ins.get('input_tokens', 0):,} / 출력 {ins.get('output_tokens', 0):,})")
            for m in (ins.get("models") or [])[:5]:
                print(f"    {m['model']:<18} 세션 {m['sessions']:>3}  토큰 {m['tokens']:>12,}")
        else:
            print("  (hermes insights 를 읽지 못했다 — 누적 사용량 없음)")
        if pv["known"]:
            print(f"── 자격 풀 ──  {backend_provider(backend)} · "
                  f"{pv['usable']}/{pv['total']} 사용 가능")
            # 런타임은 **리스트 순서**대로 훑어 쿨다운이 아닌 첫 항목을 쓴다(auth.py:4280).
            # priority 는 codex 경로에서 읽지 않는다 — 순서가 곧 선택이다.
            active = next((c["id"] for c in pv["creds"] if c["usable"]), None)
            for c in pv["creds"]:
                mark = "✓" if c["usable"] else "✗"
                note = ""
                if not c["usable"] and c["reset_at"]:
                    w = dt.datetime.fromtimestamp(c["reset_at"]).strftime("%m-%d %H:%M")
                    note = f"  {c['reason'] or 'exhausted'} · 리셋 {w}"
                if c["id"] == active:
                    note += "  ← 지금 쓰이는 자격"
                    q = format_quota(quota, now) if quota and \
                        quota.get("credential") == c["id"] else ""
                    if q:
                        note += f"\n        잔량 {q}"
                    elif quota is None:
                        note += "\n        잔량 미조회 — `--live` 로 확인(요청 1회 소비)"
                print(f"    {mark} #{c['id']} {c['label']}{note}")
        print("── 한도 ──")
        if exhausted:
            print("  ⚠️ **착수 불가**", end="")
            if pv["known"]:
                print(f" — 자격 {pv['total']}개가 모두 소진됐다")
            else:
                print()
            if latest:
                h = (latest["resets_at"] - now) / 3600
                when = dt.datetime.fromtimestamp(latest["resets_at"]).strftime("%Y-%m-%d %H:%M")
                print(f"     {latest['type']} · plan={latest['plan'] or '?'} · "
                      f"리셋 {when} — 약 {h:.1f}시간 남음 · 근거 task {latest['task']}")
            print("     → 미션을 새로 시작하지 마라. 진행 중 미션은 그 자리에 세워 둔다.")
        elif pv["known"] and log_exhausted:
            # ⚠️ 가장 헷갈리는 경우 — 로그에는 429 가 있는데 착수는 가능하다.
            #    "소진 기록이 있다"와 "지금 못 돈다"를 사람이 구분할 수 있게 **말로** 적는다.
            when = dt.datetime.fromtimestamp(latest["resets_at"]).strftime("%Y-%m-%d %H:%M")
            print(f"  ✓ 착수 가능 — 사용 가능한 자격 {pv['usable']}개")
            print(f"     (로그의 소진 기록은 다른 자격의 것이다: {latest['task']} · "
                  f"리셋 {when} — 착수 판정과 무관)")
        elif latest:
            when = dt.datetime.fromtimestamp(latest["resets_at"]).strftime("%Y-%m-%d %H:%M")
            print(f"  ✓ 정상 (마지막 소진 기록은 {when} 에 이미 리셋됨)")
        else:
            print("  ✓ 정상 (소진 기록 없음)")
        if env_failed:
            print(f"  환경성 실패가 기록된 task {len(env_failed)}건: {', '.join(env_failed[:6])}"
                  + (" …" if len(env_failed) > 6 else ""))
            print("     ⚠️ 이런 task 는 카드에 'protocol violation' 으로만 보인다 — "
                  "파이프라인 결함으로 오진하지 마라(docs/11 §7 ⑦)")
    return 1 if exhausted else 0


if __name__ == "__main__":
    sys.exit(main())
