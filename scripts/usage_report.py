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
   근거는 두 가지 기록물뿐이다:
     · `hermes insights` — 누적 세션·토큰(모델별)
     · `hermes-home/kanban/logs/*.log` — 워커 세션의 429 응답(`resets_at` 포함)

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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
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

    exhausted = bool(latest and latest["resets_at"] > now)
    report = {
        "backend": backend,
        "exhausted": exhausted,
        "limit_record": latest,
        "seconds_to_reset": (latest["resets_at"] - now) if exhausted else 0,
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
        print("── 한도 ──")
        if exhausted:
            h = report["seconds_to_reset"] / 3600
            when = dt.datetime.fromtimestamp(latest["resets_at"]).strftime("%Y-%m-%d %H:%M")
            print(f"  ⚠️ **소진 중** ({latest['type']} · plan={latest['plan'] or '?'})")
            print(f"     리셋 {when} — 약 {h:.1f}시간 남음 · 근거 task {latest['task']}")
            print("     → 미션을 새로 시작하지 마라. 진행 중 미션은 그 자리에 세워 둔다.")
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
