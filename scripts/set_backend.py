#!/usr/bin/env python3
"""
추론 백엔드 전환기 — codex(OAuth) ↔ ollama(로컬)
================================================================
프로필 11종(default + named 10종)이 어느 LLM 을 쓰는지를 **한 곳에서 선언**하고,
`profiles-src/`(git 소스)와 `hermes-home/`(라이브) 양쪽 config.yaml 을 함께 갱신한다.

⚠️ **왜 만들었나 (2026-08-05)**
   `openai-codex` 주간 한도가 소진돼(리셋 2026-08-09 14:07) 파이프라인을 전혀 테스트할 수 없게
   됐다. 호스트(M4 Max·64GB)의 Ollama 로 백엔드를 돌려 작업을 잇되, **한도가 리셋되면 한 줄로
   되돌아와야 한다.** 배치가 11개 파일에 흩어져 있으면 되돌리기가 위험한 수작업이 된다.

⚠️ **작성자≠검증자 불변식은 모델 *계열* 수준까지 지킨다.**
   같은 계열 모델은 같은 맹점을 공유하므로, 검증자에 작성자와 같은 모델을 쓰면 독립검증이
   성립하지 않는다. `TIERS` 의 writer/verifier 가 항상 다른 계열이도록 유지하라.

사용
  python3 scripts/set_backend.py --show                 # 현재 백엔드·배치
  python3 scripts/set_backend.py --backend ollama       # 로컬로 전환
  python3 scripts/set_backend.py --backend codex        # 한도 리셋 후 복귀
  python3 scripts/set_backend.py --backend ollama --dry-run
  python3 scripts/set_backend.py --show --json

exit: 0 정상 · 1 백엔드 불일치(일부 파일만 전환됨) · 2 대상 파일을 읽지 못함

설계 메모
  · **PyYAML 에 의존하지 않는다** — 호스트 python3 에는 PyYAML 이 없다(컨테이너에만 있다).
    이 스크립트는 `usage_report.py` 처럼 호스트에서 도는 운영 도구여야 하므로, `model:`
    **최상위 블록만 행 단위로 치환**한다. `agent:` · `onboarding:` · root config 의 거대한
    `platform_toolsets:` 블록은 손대지 않는다.
  · **상태 파일을 두지 않는다** — 현재 백엔드는 config 파일 자체를 읽어 판정한다(단일 진실원).
    상태 파일과 실제 설정이 어긋나는 사고를 애초에 만들지 않는다.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── 티어 → 프로필 ────────────────────────────────────────────────────────────
# `default` 는 Solomon 자신(hermes-home/config.yaml). named 프로필은 루트 config 를
# 상속하지 않으므로(docs/10 §2.1) 각자 model 블록을 가진다.
TIERS: dict[str, list[str]] = {
    "writer":   ["default", "scout", "reader", "curator", "synthesizer", "writer"],
    "verifier": ["fact-checker", "reviewer", "tester"],
    "coder":    ["architect", "developer"],
}

# ── 로컬 모델 파생본 ────────────────────────────────────────────────────────
# ⚠️ **실측(2026-08-05): Ollama 의 `/v1/chat/completions` 는 `options.num_ctx` 를 무시한다.**
#    Hermes 는 /v1 로 말하므로 config 의 `ollama_num_ctx` 만으로는 창을 못 줄인다.
#      · /v1  + options.num_ctx=8192 → llama3.1:8b 이 **131072** 로 로드(22GB)
#      · /api/chat + 같은 옵션        → **8192** 로 로드(5.9GB)
#    그래서 창은 **서버 쪽에 못박는다** — Modelfile `PARAMETER num_ctx` 로 파생 모델을 만든다
#    (`--build-models`). 이미 있던 `qwen3-coder-64k` 가 바로 이 방식이고, 원본과 **같은 blob 을
#    공유**하므로 디스크가 늘지 않는다.
#    config 의 `ollama_num_ctx` 는 그대로 둔다 — 무시되더라도 해가 없고, Hermes 가 `/api/chat`
#    경로를 쓰게 되면 그때는 유효하다.
OLLAMA_NUM_CTX = 65536

# 파생 모델 → 원본. `--build-models` 가 없는 것만 만든다.
BASE_MODELS: dict[str, str] = {
    "qwen3.6-64k":       "qwen3.6:35b",
    "glm-4.7-flash-64k": "glm-4.7-flash",
    "qwen3-coder-64k":   "qwen3-coder:30b",
}


# ── 백엔드 정의 ─────────────────────────────────────────────────────────────
BACKENDS: dict[str, dict] = {
    "codex": {
        "label": "openai-codex (ChatGPT OAuth)",
        "models": {
            "writer":   "gpt-5.6-terra",
            "verifier": "gpt-5.6-sol",
            "coder":    "gpt-5.6-terra",
        },
        # 모든 프로필에 공통으로 들어가는 model 키 (default 는 티어별로 채운다)
        "common": {
            "provider": "openai-codex",
            "base_url": "https://chatgpt.com/backend-api/codex",
        },
        "header": [
            "# named 프로필은 루트(default) config 를 상속하지 않으므로 provider/model 을 명시한다.",
            "# 인증(OAuth)은 hermes-home/auth.json 및 `hermes auth` 의 pooled 자격을 계정 단위로 공유한다.",
            "# 이 블록은 scripts/set_backend.py 가 생성한다 — 직접 고치지 말 것.",
        ],
    },
    "ollama": {
        "label": "ollama (호스트 로컬 · host.docker.internal:11434)",
        # ⚠️ 배치 모델은 **-64k 파생본**이다(원본이 아니다). 이유는 아래 BASE_MODELS 주석.
        "models": {
            "writer":   "qwen3.6-64k",
            "verifier": "glm-4.7-flash-64k",
            "coder":    "qwen3-coder-64k",
        },
        "common": {
            # `ollama` 는 Hermes 내부에서 `custom` 프로바이더로 매핑된다
            # (/opt/hermes/hermes_cli/auth.py resolve_provider).
            "provider": "ollama",
            # ⚠️ 로컬 서버는 `/v1` 접미사가 필요하다(model_setup_flows.py:946).
            # ⚠️ provider 와 base_url 은 **같은 파일에** 있어야 한다 — 아니면 Hermes 가
            #    base_url 을 버리고 OpenRouter 로 흘린다(runtime_provider.py:73).
            "base_url": "http://host.docker.internal:11434/v1",
            # Ollama 는 키를 무시하지만 비어 있으면 클라이언트가 거부한다.
            "api_key": "ollama",
            "api_mode": "chat_completions",
            # ⚠️ context_length 를 빼면 Hermes 가 /api/show 로 모델 최대(262144)를 읽어
            #    그 값으로 압축 임계를 잡는데 Ollama 는 num_ctx 만 서빙한다 → 프롬프트가
            #    조용히 잘린다. 두 값을 반드시 같이 맞춘다.
            "context_length": OLLAMA_NUM_CTX,
            "ollama_num_ctx": OLLAMA_NUM_CTX,
            # 미지정 시 provider 기본값이 65536 이라 출력이 창을 다 먹는다
            # (plugins/model-providers/custom/__init__.py default_max_tokens).
            "max_tokens": 16384,
        },
        "header": [
            "# 로컬 Ollama 백엔드 — scripts/set_backend.py 가 생성한다. 직접 고치지 말 것.",
            "# 전환: python3 scripts/set_backend.py --backend codex|ollama   (docs/14 참조)",
        ],
    },
}

# provider 값 → 백엔드 이름 (--show 판정용)
PROVIDER_TO_BACKEND = {
    "openai-codex": "codex",
    "ollama": "ollama",
    "custom": "ollama",   # Hermes 가 alias 를 풀어 다시 쓰는 경우
}

# 로컬 백엔드에서 반드시 존재해야 하는 model 키 (누락되면 조용한 오작동)
REQUIRED_OLLAMA_KEYS = ("provider", "base_url", "context_length", "ollama_num_ctx", "max_tokens")


# ── 경로 ────────────────────────────────────────────────────────────────────
def profile_of_tier() -> dict[str, str]:
    """profile 이름 → 티어."""
    return {p: tier for tier, profiles in TIERS.items() for p in profiles}


def targets(repo_root: str = REPO_ROOT) -> list[tuple[str, str, str]]:
    """(profile, kind, path) 목록. kind 는 'src'(git 소스) 또는 'live'(hermes-home).

    `default` 는 profiles-src 에 대응 파일이 없다 — Solomon 의 config 는 루트
    `hermes-home/config.yaml` 하나뿐이다.
    """
    out: list[tuple[str, str, str]] = []
    for profile in profile_of_tier():
        if profile == "default":
            out.append((profile, "live", os.path.join(repo_root, "hermes-home", "config.yaml")))
            continue
        out.append((profile, "src",
                    os.path.join(repo_root, "profiles-src", profile, "config.yaml")))
        out.append((profile, "live",
                    os.path.join(repo_root, "hermes-home", "profiles", profile, "config.yaml")))
    return out


# ── model 블록 읽기/쓰기 (PyYAML 비의존) ────────────────────────────────────
def find_model_block(lines: list[str]) -> tuple[int, int] | None:
    """`model:` 최상위 블록의 [start, end) 행 범위. 바로 위의 주석 줄도 포함한다.

    끝은 '다음 0열 시작 행' 직전이다(들여쓴 줄과 빈 줄은 블록 내부로 본다).
    """
    idx = None
    for i, line in enumerate(lines):
        if line.rstrip() == "model:" and not line[:1].isspace():
            idx = i
            break
    if idx is None:
        return None

    # 바로 위에 붙어 있는 주석 줄들을 블록에 포함(생성 헤더 교체용)
    start = idx
    while start > 0:
        prev = lines[start - 1].strip()
        if prev.startswith("#"):
            start -= 1
        else:
            break

    end = idx + 1
    while end < len(lines):
        line = lines[end]
        if line.strip() == "" or line[:1].isspace():
            end += 1
            continue
        break
    # 블록 끝의 빈 줄은 다음 블록에 돌려준다
    while end - 1 > idx and lines[end - 1].strip() == "":
        end -= 1
    return start, end


def parse_model_block(lines: list[str]) -> dict[str, str]:
    """model 블록의 1단계 키/값만 읽는다(중첩 없음 — 실제 스키마가 평면이다)."""
    span = find_model_block(lines)
    if span is None:
        return {}
    start, end = span
    out: dict[str, str] = {}
    for line in lines[start:end]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped == "model:":
            continue
        if not line.startswith("  ") or line.startswith("   "):
            continue  # 2칸 들여쓰기(=1단계)만
        if ":" not in stripped:
            continue
        key, _, val = stripped.partition(":")
        out[key.strip()] = val.strip().strip("'\"")
    return out


def render_model_block(backend: str, model: str, with_header: bool) -> list[str]:
    spec = BACKENDS[backend]
    out: list[str] = []
    if with_header:
        out.extend(spec["header"])
    out.append("model:")
    out.append(f'  default: "{model}"')
    for key, val in spec["common"].items():
        out.append(f'  {key}: "{val}"' if isinstance(val, str) else f"  {key}: {val}")
    return out


def apply_to_file(path: str, backend: str, model: str, with_header: bool) -> tuple[bool, str]:
    """(변경됨?, 메시지). 파일이 없으면 (False, 사유)."""
    if not os.path.isfile(path):
        return False, "파일 없음"
    with open(path, encoding="utf-8") as fh:
        original = fh.read()
    lines = original.splitlines()
    block = render_model_block(backend, model, with_header)

    span = find_model_block(lines)
    if span is None:
        new_lines = block + [""] + lines
    else:
        start, end = span
        new_lines = lines[:start] + block + lines[end:]

    new_text = "\n".join(new_lines) + "\n"
    if new_text == original:
        return False, "이미 동일"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(new_text)
    return True, "갱신"


# ── 현재 상태 판정 ──────────────────────────────────────────────────────────
def inspect(repo_root: str = REPO_ROOT) -> dict:
    """대상 파일들을 읽어 현재 백엔드 상태를 보고한다."""
    tier_of = profile_of_tier()
    rows: list[dict] = []
    for profile, kind, path in targets(repo_root):
        row = {"profile": profile, "tier": tier_of[profile], "kind": kind, "path": path}
        if not os.path.isfile(path):
            row.update(present=False, backend=None, model=None, missing_keys=[])
            rows.append(row)
            continue
        with open(path, encoding="utf-8") as fh:
            cfg = parse_model_block(fh.read().splitlines())
        provider = cfg.get("provider", "")
        backend = PROVIDER_TO_BACKEND.get(provider)
        missing = []
        if backend == "ollama":
            missing = [k for k in REQUIRED_OLLAMA_KEYS if k not in cfg]
        row.update(present=True, backend=backend, provider=provider,
                   model=cfg.get("default") or cfg.get("model"), missing_keys=missing)
        rows.append(row)

    found = {r["backend"] for r in rows if r["present"]}
    if not found:
        active = "unknown"
    elif len(found) == 1:
        active = found.pop() or "unknown"
    else:
        active = "mixed"

    expected_ok = True
    if active in BACKENDS:
        want = BACKENDS[active]["models"]
        for r in rows:
            if r["present"] and (r["model"] != want[r["tier"]] or r["missing_keys"]):
                expected_ok = False
    return {"active": active, "consistent": active in BACKENDS and expected_ok, "rows": rows}


def active_backend(repo_root: str = REPO_ROOT) -> str:
    """usage_report.py 등이 쓰는 공개 헬퍼. 'codex' | 'ollama' | 'mixed' | 'unknown'."""
    return inspect(repo_root)["active"]


def modelfile(derived: str) -> str:
    """파생 모델의 Modelfile 본문. 창을 **서버 쪽에** 못박는다."""
    return f"FROM {BASE_MODELS[derived]}\nPARAMETER num_ctx {OLLAMA_NUM_CTX}\n"


def cmd_build_models(backend: str) -> int:
    """배치 모델 중 없는 파생본을 `ollama create` 로 만든다. 원본 blob 을 공유한다."""
    import subprocess
    import tempfile

    if backend != "ollama":
        print(f"{backend} 백엔드는 로컬 모델을 쓰지 않는다 — 할 일 없음")
        return 0
    have = subprocess.run(["ollama", "list"], capture_output=True, text=True)
    if have.returncode != 0:
        print("ollama CLI 를 실행하지 못했다 — Ollama 가 켜져 있는지 확인하라", file=sys.stderr)
        return 2
    installed = {ln.split()[0] for ln in have.stdout.splitlines()[1:] if ln.split()}
    installed |= {n.split(":")[0] for n in installed}

    rc = 0
    for derived in backend_models(backend):
        base = BASE_MODELS.get(derived)
        if base is None:
            print(f"  {derived:<20} 파생본이 아니다 — 건너뜀")
            continue
        if derived in installed or f"{derived}:latest" in installed:
            print(f"  {derived:<20} 이미 있음")
            continue
        if base not in installed and f"{base}:latest" not in installed:
            print(f"  {derived:<20} ⚠️ 원본 {base} 이 없다 → `ollama pull {base}` 먼저")
            rc = 1
            continue
        with tempfile.NamedTemporaryFile("w", suffix=".Modelfile", delete=False) as fh:
            fh.write(modelfile(derived))
            path = fh.name
        try:
            proc = subprocess.run(["ollama", "create", derived, "-f", path],
                                  capture_output=True, text=True)
        finally:
            os.unlink(path)
        if proc.returncode == 0:
            print(f"  {derived:<20} 생성됨 (FROM {base} · num_ctx {OLLAMA_NUM_CTX})")
        else:
            print(f"  {derived:<20} ⚠️ 생성 실패: {proc.stderr.strip()[:200]}")
            rc = 1
    return rc


def backend_models(backend: str) -> list[str]:
    """해당 백엔드가 실제로 쓰는 모델 목록(중복 제거, 선언 순서 유지)."""
    seen: list[str] = []
    for tier in TIERS:
        model = BACKENDS[backend]["models"][tier]
        if model not in seen:
            seen.append(model)
    return seen


# ── CLI ─────────────────────────────────────────────────────────────────────
def cmd_show(repo_root: str, as_json: bool) -> int:
    state = inspect(repo_root)
    if as_json:
        print(json.dumps(state, ensure_ascii=False, indent=2))
        return 0 if state["consistent"] else 1

    active = state["active"]
    label = BACKENDS[active]["label"] if active in BACKENDS else "—"
    print(f"── 현재 백엔드 ──  {active}  ({label})")
    print(f"{'profile':<14}{'tier':<10}{'kind':<6}{'model':<20}backend")
    for r in state["rows"]:
        if not r["present"]:
            print(f"{r['profile']:<14}{r['tier']:<10}{r['kind']:<6}{'(파일 없음)':<20}—")
            continue
        note = ""
        if r["missing_keys"]:
            note = "  ⚠️ 누락: " + ", ".join(r["missing_keys"])
        print(f"{r['profile']:<14}{r['tier']:<10}{r['kind']:<6}"
              f"{str(r['model']):<20}{r['backend'] or r['provider']}{note}")

    if active == "mixed":
        print("\n⚠️ **불일치** — 일부 파일만 전환돼 있다. "
              "`--backend <name>` 으로 다시 적용하라.")
    elif not state["consistent"]:
        print("\n⚠️ 백엔드는 하나지만 모델·키가 배치표와 어긋난다. "
              "`--backend <name>` 으로 다시 적용하라.")
    return 0 if state["consistent"] else 1


def cmd_apply(repo_root: str, backend: str, dry_run: bool) -> int:
    tier_of = profile_of_tier()
    models = BACKENDS[backend]["models"]
    changed = skipped = missing = 0
    print(f"── {backend} 로 전환 ──  {BACKENDS[backend]['label']}"
          + ("   [dry-run]" if dry_run else ""))
    for profile, kind, path in targets(repo_root):
        model = models[tier_of[profile]]
        rel = os.path.relpath(path, repo_root)
        if dry_run:
            status = "적용 대상" if os.path.isfile(path) else "파일 없음"
            if not os.path.isfile(path):
                missing += 1
            print(f"  {profile:<14}{model:<20}{status:<10}{rel}")
            continue
        did, msg = apply_to_file(path, backend, model, with_header=(kind == "src"))
        if msg == "파일 없음":
            missing += 1
        elif did:
            changed += 1
        else:
            skipped += 1
        print(f"  {profile:<14}{model:<20}{msg:<10}{rel}")

    if dry_run:
        print(f"\n(dry-run) 파일 없음 {missing}건 — 실제 변경은 하지 않았다.")
        return 0

    print(f"\n갱신 {changed} · 변화없음 {skipped} · 파일없음 {missing}")
    if missing:
        print("  ℹ️ hermes-home/ 은 로컬 전용이라 새 PC 에서는 비어 있을 수 있다"
              "(부트스트랩 후 다시 실행하라).")
    print("\n다음:")
    print("  docker compose up -d --force-recreate hermes-solomon hermes-gatekeeper")
    print("  docker exec hermes-solomon hermes profile list")
    if backend == "ollama":
        print("  python3 scripts/usage_report.py     # 로컬 모델 준비 상태 점검")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--backend", choices=sorted(BACKENDS), help="전환할 백엔드")
    ap.add_argument("--show", action="store_true", help="현재 백엔드·배치 출력")
    ap.add_argument("--json", action="store_true", help="기계 판독(--show 와 함께)")
    ap.add_argument("--dry-run", action="store_true", help="변경 없이 대상만 출력")
    ap.add_argument("--build-models", action="store_true",
                    help="없는 로컬 파생 모델(-64k)을 ollama create 로 생성")
    ap.add_argument("--repo-root", default=REPO_ROOT, help="저장소 루트(테스트용)")
    args = ap.parse_args(argv)

    if not args.backend and not args.show and not args.build_models:
        ap.error("--backend · --show · --build-models 중 하나가 필요하다")
    if args.build_models:
        backend = args.backend or active_backend(args.repo_root)
        print(f"── 로컬 파생 모델 준비 ──  num_ctx {OLLAMA_NUM_CTX}")
        rc = cmd_build_models(backend)
        if not args.backend:
            return rc
        if rc:
            return rc
    if args.backend:
        rc = cmd_apply(args.repo_root, args.backend, args.dry_run)
        if rc or args.dry_run:
            return rc
        print()
        return cmd_show(args.repo_root, as_json=False)
    return cmd_show(args.repo_root, args.json)


if __name__ == "__main__":
    sys.exit(main())
