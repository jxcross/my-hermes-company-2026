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
#    (`--build-models`). 파생본 이름의 접미사(`-256k`)가 **창을 담는다** — 창이 바뀌면
#    이름이 바뀐다. 파생본은 원본과 **같은 blob 을
#    공유**하므로 디스크가 늘지 않는다.
#    config 의 `ollama_num_ctx` 는 그대로 둔다 — 무시되더라도 해가 없고, Hermes 가 `/api/chat`
#    경로를 쓰게 되면 그때는 유효하다.
#
# ⚠️⚠️ **창 크기는 성능 손잡이가 아니라 정확성 손잡이다 (2026-08-05 실미션에서 배움)**
#    처음에 65536 으로 잡았더니 M-2026-005 stage 5 가 **압축 루프에 갇혀 사실상 멈췄다.**
#    Hermes 의 압축 발동 지점은 `context_length` 가 아니라 **입력 예산**에서 계산된다
#    (`/opt/hermes/agent/context_compressor.py:2113` `_compute_threshold_tokens`):
#        effective_window = context_length - max_tokens
#        floored = max(effective_window × threshold, MINIMUM_CONTEXT_LENGTH=64000)
#        floored >= effective_window 이면 → **퇴화 분기**: effective_window × 0.85
#    65536 - 16384 = 49152 < 64000 이라 **항상 퇴화 분기**로 떨어져 41,779 토큰에서
#    압축이 걸렸고, `compression.threshold` 를 0.9 로 올려도 **값이 바뀌지 않았다**(무력).
#    → `context_length - max_tokens > 64000` 을 만족해야 한다. 262144-16384=245760 ✓
#    실측 대조: 65536→41,779 · 131072→97,484 · **262144→208,896(현재 설정 · th 0.85)**
#
# ⚠️ 창을 바꾸면 **파생본 이름도 바꿔라**(`-256k`). `cmd_build_models` 는 존재를
#    **이름으로만** 판정하므로, 이름을 그대로 두고 이 상수만 올리면 "이미 있음"을 찍고
#    서버는 옛 창을 계속 서빙한다. config 는 새 값을 주장하고 서버는 옛 값을 서빙하는,
#    두 층 떨어진 실패가 된다(docs/11 §7 ⑦ 계열 — 표면 증상과 원인이 멀어진다).
OLLAMA_NUM_CTX = 262144

# ── 호스트 Ollama **서버** 설정 (launchctl) ─────────────────────────────────
# config 가 아니라 **서버**가 들고 있는 값이다. 프로필 config 를 아무리 맞춰도 서버가
# 다르게 서빙하면 소용이 없으므로, 기대값을 여기 한 곳에 선언하고 `--host-setup` 이
# 적용하고 `usage_report.py` 가 착수 전에 대조한다(선언·적용·검사가 같은 표를 본다).
#
# ⚠️⚠️ **`OLLAMA_NUM_PARALLEL` 이 없으면 동시 요청이 서버에서 직렬화된다 (실측 2026-08-06)**
#    `scripts/probe_parallel.py` 로 쟀다. 미설정 상태에서 동시 3요청:
#      단일 1.44초 · 동시 3개 총 3.94초(**×2.74**) · 종료 오프셋 [1.49, 2.68, 3.94]
#      = 1.2초 간격의 **계단** · 합산 처리량 73.1 tok/s < 단일 86.7 tok/s(이득이 음수다).
#    `docs/11 §5` 의 스테이지 내 팬아웃은 subagent 3개가 동시에 `/v1` 을 때리는데,
#    서버가 큐에 세우면 **아무 오류 없이 3배 느려질 뿐**이다 — 병렬화가 조용히 사라진다.
#    병렬 파일럿 M-2026-004 는 codex 에서 돌아 이걸 볼 기회가 없었다.
#
# ⚠️ `NUM_PARALLEL` 은 **템플릿 `parallel.batch_size`(기본 3)와 같은 수여야 한다.**
#    둘은 독립 선언이다 — 서버 슬롯이 적으면 초과분이 큐에 서고, 많으면 KV 만 낭비한다.
#
# ⚠️ 슬롯마다 KV 캐시가 따로 잡힌다 → `NUM_PARALLEL` 을 올리면 메모리가 배수로 는다.
#    그래서 `KV_CACHE_TYPE=q8_0`(f16 대비 절반) + `FLASH_ATTENTION=1` 과 **짝으로** 건다.
HOST_ENV: dict[str, str] = {
    "OLLAMA_NUM_PARALLEL":      "3",      # = delegation.max_concurrent_children · 템플릿 batch_size
    "OLLAMA_KV_CACHE_TYPE":     "q8_0",   # 슬롯 3개분 KV 를 감당하기 위한 짝
    "OLLAMA_FLASH_ATTENTION":   "1",      # q8_0 KV 의 전제
    "OLLAMA_MAX_LOADED_MODELS": "1",      # 배치가 단일 모델이라 1로 충분(docs/14 §5)
    "OLLAMA_KEEP_ALIVE":        "30m",
}

# ⚠️ **일부러 설정하지 않는 것** — 넣으면 안 되는 이유를 남긴다. 비워 두면 다음 사람이
#    "빠뜨렸나?" 하고 채워 넣는다(외부 가이드가 실제로 이걸 권한다 — docs/14 §5.2).
HOST_ENV_OMITTED: dict[str, str] = {
    "OLLAMA_CONTEXT_LENGTH":
        "서버 전역값이라 모델별 천장(e4b=131072)을 표현하지 못한다. "
        "창은 Modelfile 파생본(-256k)이 담는다 — §3.1",
}

# ⚠️ 프로필마다 직접 써야 한다 — `compression.*` 는 **루트 config 에서 상속되지 않는다**
#    (named 프로필은 HERMES_HOME=<root>/profiles/<name> 이라 자기 config.yaml 만 읽는다).
#    그리고 <512K 창에서는 0.75 로 하한이 강제되므로 0.75 이하 값은 의미가 없다.
COMPRESSION_THRESHOLD = 0.85

# 파생 모델 → {원본, Modelfile 에 못박을 창, 모델 천장}. `--build-models` 가 없는 것만 만든다.
#
# ⚠️ **`ceiling` 은 추측이 아니라 실측이다** — `curl /api/show` 의 `<family>.context_length`.
#    2026-08-05 재측정: 26b 262144 · e4b **131072** · qwen3.6 262144 · qwen3-coder 262144.
#    **e4b 만 131072 이 천장이라 256k 를 줄 수 없다.** 전 모델이 창 하나를 공유한다고 두면
#    이 모델에 서빙 불가능한 값을 못박게 된다 — 그래서 창을 모델별로 들고 있는다.
#
# ⚠️ 폴백 3종을 **지우지 않는 이유**: 배치에서 빠졌을 뿐 측정으로 검증된 대안이다
#    (docs/14 §2.1). 어설션을 맞추려고 측정 기록을 버리는 것은, 이 저장소가
#    `shared_verifier_model` 선언으로 막아둔 바로 그 실패 모양이다.
BASE_MODELS: dict[str, dict] = {
    "gemma4-26b-256k":   {"base": "gemma4:26b",      "num_ctx": 262144, "ceiling": 262144},
    # 폴백(배치에서 빠졌지만 측정으로 검증된 대안 — docs/14 §2.1)
    "gemma4-e4b-128k":   {"base": "gemma4:e4b",      "num_ctx": 131072, "ceiling": 131072},
    "qwen3.6-256k":      {"base": "qwen3.6:35b",     "num_ctx": 262144, "ceiling": 262144},
    "qwen3-coder-256k":  {"base": "qwen3-coder:30b", "num_ctx": 262144, "ceiling": 262144},
}


# ── 백엔드 정의 ─────────────────────────────────────────────────────────────
BACKENDS: dict[str, dict] = {
    "codex": {
        "label": "openai-codex (ChatGPT OAuth)",
        # ⚠️ 2026-08-05 (3) Sam 지시로 **전 티어 `gpt-5.5` 단일화**.
        #    배경: 로컬 `gemma4-26b-256k` 가 실미션에서 두 번 무너졌다 — 산출물 날조
        #    (분석 11편 중 8편)와 **작업 보고 날조**(디스크 무변경인데 완료 선언).
        #    창을 262144 로 올려도 같았다. 자세한 것은 docs/11 §7 ⑧·⑧-d.
        #    ↩︎ 이전 배치(참고): writer/coder `gpt-5.6-terra` · verifier `gpt-5.6-sol`.
        #       티어를 다시 가르려면 아래 3줄만 바꾸면 된다.
        "models": {
            "writer":   "gpt-5.5",
            "verifier": "gpt-5.5",
            "coder":    "gpt-5.5",
        },
        # ⚠️ **작성자≠검증자를 모델 계열 수준에서 다시 포기했다** — 의도된 예외다.
        #    Sam 지시(2026-08-05 (3)): "전체 모델을 codex 5.5 로 모두 바꿔라".
        #    남는 분리: profile 경계 · SOUL(역할 프롬프트) · 객관 게이트 62종 ·
        #    작성 task ≠ 검증 task.
        #    ⚠️ 이번 세션이 보여준 것: **LLM 검증자는 두 번 다 틀렸고**(11건 중 2·5건만
        #    대조하고 PASS), 잡아낸 것은 객관 게이트였다. 즉 지금 실질적인 독립검증은
        #    모델 계열이 아니라 `scripts/gates/` 다. 검증자를 다시 다른 모델로 가르고
        #    싶으면 verifier 를 `gpt-5.5-pro` 나 `gpt-5.6-sol` 로 되돌려라.
        "shared_verifier_model": "Sam 지시 2026-08-05 (3): 전 티어 gpt-5.5 단일화",
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
        # ⚠️ 배치 모델은 **-256k 파생본**이다(원본이 아니다). 이유는 위 BASE_MODELS 주석.
        # 선정 근거는 추측이 아니라 측정이다 — `scripts/probe_protocol.py` (docs/14 §2.1).
        # 무경합 실측(2026-08-05): 프로토콜 3회 벽시계 26b 45s = e4b 45s < 12b 97s ·
        # 실작업(18.8k 입력) 26b 61.5s ≈ e4b 57.2s. 속도가 동률이라 **창 여유**로 갈랐다
        # (26b 262144 > e4b 131072=천장) + 마지막줄 규격 26b 100% vs e4b 33%.
        # → 2026-08-05 (3) Sam 지시로 그 여유를 실제로 쓴다: 131072 → **262144(천장)**.
        # ⚠️ 창은 성실성을 사주지 않는다 — 26b 는 131072 에서 원문을 가지고 있으면서
        #    읽지 않고 분석 7편을 지어냈다(docs/11 §7 ⑧). 날조는 `analysis_substance`
        #    게이트가 막는다. 창 증설은 그것과 **별개의** 조치다.
        "models": {
            "writer":   "gemma4-26b-256k",
            "verifier": "gemma4-26b-256k",
            "coder":    "gemma4-26b-256k",
        },
        # ⚠️ **작성자≠검증자를 모델 계열 수준에서 포기한 것은 의도된 예외다.**
        # Sam 승인(2026-08-05): 속도 우선으로 전 프로필 단일 모델. 남는 분리는
        # profile 경계·SOUL(역할 프롬프트)·객관 게이트 62종·작성 task ≠ 검증 task 다.
        # 이 선언이 없으면 테스트가 통일을 FAIL 시킨다 — 불변식을 조용히 잃지 않기 위해서다.
        "shared_verifier_model": "Sam 승인 2026-08-05: 속도 우선 통일(docs/14 §2.2)",
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
        # `model:` 외에 프로필 config 에 함께 써야 하는 최상위 블록.
        # ⚠️ 루트 hermes-home/config.yaml 의 compression 은 named 프로필에 **상속되지 않는다.**
        "extra_blocks": {
            "compression": {"threshold": COMPRESSION_THRESHOLD},
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


# ── 최상위 블록 읽기/쓰기 (PyYAML 비의존) ───────────────────────────────────
def find_block(lines: list[str], name: str = "model") -> tuple[int, int] | None:
    """`<name>:` 최상위 블록의 [start, end) 행 범위. 바로 위의 주석 줄도 포함한다.

    끝은 '다음 0열 시작 행' 직전이다(들여쓴 줄과 빈 줄은 블록 내부로 본다).
    """
    idx = None
    for i, line in enumerate(lines):
        if line.rstrip() == f"{name}:" and not line[:1].isspace():
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


def find_model_block(lines: list[str]) -> tuple[int, int] | None:
    """하위 호환 별칭."""
    return find_block(lines, "model")


def parse_model_block(lines: list[str], name: str = "model") -> dict[str, str]:
    """블록의 1단계 키/값만 읽는다(중첩 없음 — 실제 스키마가 평면이다)."""
    span = find_block(lines, name)
    if span is None:
        return {}
    start, end = span
    out: dict[str, str] = {}
    for line in lines[start:end]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped == f"{name}:":
            continue
        if not line.startswith("  ") or line.startswith("   "):
            continue  # 2칸 들여쓰기(=1단계)만
        if ":" not in stripped:
            continue
        key, _, val = stripped.partition(":")
        out[key.strip()] = val.strip().strip("'\"")
    return out


def _kv(key, val) -> str:
    return f'  {key}: "{val}"' if isinstance(val, str) else f"  {key}: {val}"


def render_model_block(backend: str, model: str, with_header: bool) -> list[str]:
    spec = BACKENDS[backend]
    out: list[str] = []
    if with_header:
        out.extend(spec["header"])
    out.append("model:")
    out.append(f'  default: "{model}"')
    for key, val in spec["common"].items():
        out.append(_kv(key, val))
    return out


def render_extra_block(backend: str, name: str) -> list[str]:
    """`compression:` 처럼 model 외에 프로필에 직접 써야 하는 최상위 블록."""
    return [f"{name}:"] + [_kv(k, v)
                           for k, v in BACKENDS[backend].get("extra_blocks", {})[name].items()]


def apply_to_file(path: str, backend: str, model: str, with_header: bool) -> tuple[bool, str]:
    """(변경됨?, 메시지). 파일이 없으면 (False, 사유)."""
    if not os.path.isfile(path):
        return False, "파일 없음"
    with open(path, encoding="utf-8") as fh:
        original = fh.read()
    lines = original.splitlines()

    def splice(lines_: list[str], name: str, block: list[str]) -> list[str]:
        span = find_block(lines_, name)
        if span is None:
            return lines_ + [""] + block if lines_ else list(block)
        start, end = span
        return lines_[:start] + block + lines_[end:]

    lines = splice(lines, "model", render_model_block(backend, model, with_header))
    # 다른 백엔드에서 남은 블록은 지우고, 이 백엔드가 요구하는 것만 남긴다
    for name in set(BACKENDS["codex"].get("extra_blocks", {})) \
            | set(BACKENDS["ollama"].get("extra_blocks", {})):
        if name in BACKENDS[backend].get("extra_blocks", {}):
            lines = splice(lines, name, render_extra_block(backend, name))
        else:
            span = find_block(lines, name)
            if span:
                lines = lines[:span[0]] + lines[span[1]:]

    new_lines = lines
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
    """파생 모델의 Modelfile 본문. 창을 **서버 쪽에** 못박는다.

    ⚠️ 창은 `OLLAMA_NUM_CTX` 가 아니라 **모델별 `num_ctx`** 다 — 폴백 중 `gemma4:e4b` 는
       천장이 131072 이라 262144 를 서빙할 수 없다.
    """
    spec = BASE_MODELS[derived]
    return f"FROM {spec['base']}\nPARAMETER num_ctx {spec['num_ctx']}\n"


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
        spec = BASE_MODELS.get(derived)
        if spec is None:
            print(f"  {derived:<20} 파생본이 아니다 — 건너뜀")
            continue
        base = spec["base"]
        # ⚠️ 존재 판정은 **이름으로만** 한다 — 이미 있는 파생본의 창이 맞는지는 확인하지
        #    못한다. 그래서 창을 바꿀 때는 반드시 이름도 바꾼다(위 OLLAMA_NUM_CTX 주석).
        #    실제 서빙 창은 `ollama ps` 의 CONTEXT 로 확인하라(docs/14 §3.1).
        if derived in installed or f"{derived}:latest" in installed:
            print(f"  {derived:<20} 이미 있음 (서빙 창은 `ollama ps` 의 CONTEXT 로 확인하라)")
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
            print(f"  {derived:<20} 생성됨 (FROM {base} · num_ctx {spec['num_ctx']})")
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


# ── 호스트 서버 설정 (launchctl) ────────────────────────────────────────────
def _launchctl_get(var: str) -> str | None:
    """`launchctl getenv` 1건. macOS 호스트가 아니면 None(=판정 불가)."""
    import shutil as _shutil
    import subprocess as _subprocess
    if not _shutil.which("launchctl"):
        return None
    try:
        out = _subprocess.run(["launchctl", "getenv", var],
                              capture_output=True, text=True, timeout=5)
    except (OSError, _subprocess.SubprocessError):
        return None
    return out.stdout.strip()


# Ollama 는 기동 시 실효 환경변수를 로그 첫 줄에 `KEY:VALUE` 로 찍는다. **이것이 서버 쪽
# 유일한 권위 있는 근거다** — launchctl 값은 "걸어 놨다"일 뿐 "반영됐다"가 아니다.
OLLAMA_SERVER_LOG = os.path.expanduser("~/.ollama/logs/server.log")


def _norm_env(var: str, val: str) -> str:
    """launchctl 표기와 서버 표기를 같은 자로 만든다.

    서버는 `1`을 `true` 로, `30m` 을 `30m0s` 로 되받아 찍는다. 표기 차이를 불일치로
    오판하면 이 검사는 늘 시끄러워지고, 시끄러운 검사는 곧 무시된다.
    """
    v = (val or "").strip().lower()
    if var == "OLLAMA_FLASH_ATTENTION":
        if v in ("1", "true"):
            return "true"
        return "false" if v in ("0", "false", "") else v
    if var == "OLLAMA_KEEP_ALIVE" and v.endswith("0s") and len(v) > 2:
        return v[:-2]           # 30m0s → 30m
    return v


def _last_server_banner(log_path: str | None = None) -> dict[str, str] | None:
    """서버 기동 배너의 `OLLAMA_*` 값. 없으면 None(=판정 불가).

    ⚠️ 로그는 수십 MB 까지 자란다 — **뒤에서부터** 찾는다(착수 전 점검은 빨라야 한다).
    """
    path = log_path or OLLAMA_SERVER_LOG
    if not os.path.isfile(path):
        return None
    needle = "OLLAMA_NUM_PARALLEL:"
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as fh:
            window, line = 1 << 20, None
            while True:
                partial = window < size
                fh.seek(max(0, size - window))
                lines = fh.read().decode("utf-8", "replace").splitlines()
                # 부분 창의 첫 줄은 잘려 있을 수 있다 — 잘린 배너를 온전한 것으로
                # 읽으면 앞쪽 키가 통째로 사라진 채 "없음"으로 오판된다.
                if partial and lines:
                    lines = lines[1:]
                hits = [ln for ln in lines if needle in ln]
                if hits:
                    line = hits[-1]
                    break
                if not partial:          # 파일 전체를 봤는데 없다
                    break
                window = min(window * 8, size)
    except OSError:
        return None
    if not line:
        return None
    out: dict[str, str] = {}
    for tok in line.split():
        if tok.startswith("OLLAMA_") and ":" in tok:
            k, _, v = tok.partition(":")
            # ⚠️ 배너는 `env="map[K:V K:V]"` 로 감싸여 있다 — **맨 끝 키의 값에 `]"` 가
            #    붙어 온다.** 안 떼면 그 키 하나만 영원히 '불일치' 로 보인다(실제로
            #    `NUM_PARALLEL:3]"` != `3` 이 나왔다). 마지막 키가 무엇인지는 정렬 순서라
            #    모델·버전에 따라 바뀐다 — 값 쪽을 항상 다듬는다.
            out[k] = v.rstrip(']"\',')
    return out or None


def server_env_state(log_path: str | None = None) -> dict:
    """기대값 대 **서버가 실제로 들고 있는** 값.

    ⚠️⚠️ **왜 launchctl 로 부족한가 (실측 2026-08-06)**
       `launchctl getenv` 는 `MAX_LOADED_MODELS=1`·`KEEP_ALIVE=30m` 을 돌려줬는데
       실행 중인 서버 배너는 `MAX_LOADED_MODELS:0`·`KEEP_ALIVE:5m0s` 였다 —
       `docs/14 §5` 가 지시한 설정이 **서버에는 한 번도 반영된 적이 없었다.**
       `launchctl setenv` 는 이후 기동하는 프로세스에만 붙기 때문이다.
       걸어 놓은 것과 반영된 것은 다르다. 여기서는 반영된 쪽만 본다.
    """
    banner = _last_server_banner(log_path)
    if banner is None:
        return {"available": False, "vars": [], "mismatched": []}
    rows = []
    for var, want in HOST_ENV.items():
        have = banner.get(var, "")
        rows.append({"var": var, "want": want, "have": have or "(없음)",
                     "ok": _norm_env(var, have) == _norm_env(var, want)})
    return {"available": True, "vars": rows,
            "mismatched": [r for r in rows if not r["ok"]]}


def host_env_state() -> dict:
    """기대값(HOST_ENV) 대 현재 launchctl 값.

    ⚠️ 컨테이너·리눅스에는 `launchctl` 이 없다 → `available: False` 로 돌려주고
       **판정하지 않는다.** 확인할 수 없는 것을 FAIL 로 만들면 그 검사는 꺼진다.
    """
    probe = _launchctl_get("OLLAMA_MAX_LOADED_MODELS")
    if probe is None:
        return {"available": False, "vars": [], "mismatched": []}
    rows = []
    for var, want in HOST_ENV.items():
        have = _launchctl_get(var) or ""
        rows.append({"var": var, "want": want, "have": have, "ok": have == want})
    # 넣으면 안 되는 것이 들어가 있는가
    for var, why in HOST_ENV_OMITTED.items():
        have = _launchctl_get(var) or ""
        if have:
            rows.append({"var": var, "want": "(설정하지 말 것)", "have": have,
                         "ok": False, "why": why})
    return {"available": True, "vars": rows,
            "mismatched": [r for r in rows if not r["ok"]]}


def cmd_host_setup(dry_run: bool) -> int:
    """launchctl 에 HOST_ENV 를 건다. **Ollama 재시작까지 해야 반영된다.**"""
    import shutil as _shutil
    import subprocess as _subprocess
    if not _shutil.which("launchctl"):
        print("⚠️ `launchctl` 이 없다 — 이 명령은 macOS 호스트에서만 쓴다.", file=sys.stderr)
        return 2

    print("── 호스트 Ollama 서버 설정 ──" + ("   [dry-run]" if dry_run else ""))
    for var, want in HOST_ENV.items():
        have = _launchctl_get(var) or ""
        mark = "그대로" if have == want else f"{have or '(없음)'} → {want}"
        print(f"  {var:<26} {mark}")
        if not dry_run and have != want:
            _subprocess.run(["launchctl", "setenv", var, want], check=False, timeout=5)
    for var, why in HOST_ENV_OMITTED.items():
        have = _launchctl_get(var) or ""
        if have:
            print(f"  ⚠️ {var} = {have} — 설정돼 있으면 안 된다: {why}")
            print(f"     → launchctl unsetenv {var}")

    if dry_run:
        print("\n(dry-run) 변경하지 않았다.")
        return 0
    print("\n⚠️ **launchctl 값은 서버 재시작 전까지 반영되지 않는다:**")
    print("     osascript -e 'quit app \"Ollama\"' && sleep 3 && open -a Ollama")
    print("⚠️ launchctl setenv 는 로그인 세션 단위라 **재부팅하면 사라진다** — 다시 걸어라.")
    print("\n검증(파일이 아니라 서버가 보고하는 값을 봐라):")
    print("  ollama ps                          # CONTEXT · SIZE")
    print("  python3 scripts/probe_parallel.py  # 동시 요청이 실제로 병렬인가")
    print("  python3 scripts/usage_report.py    # 착수 전 점검이 이 표를 대조한다")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--backend", choices=sorted(BACKENDS), help="전환할 백엔드")
    ap.add_argument("--show", action="store_true", help="현재 백엔드·배치 출력")
    ap.add_argument("--json", action="store_true", help="기계 판독(--show 와 함께)")
    ap.add_argument("--dry-run", action="store_true", help="변경 없이 대상만 출력")
    ap.add_argument("--build-models", action="store_true",
                    help="없는 로컬 파생 모델(-256k 등)을 ollama create 로 생성")
    ap.add_argument("--host-setup", action="store_true",
                    help="호스트 Ollama 서버 설정(launchctl)을 HOST_ENV 대로 건다")
    ap.add_argument("--repo-root", default=REPO_ROOT, help="저장소 루트(테스트용)")
    args = ap.parse_args(argv)

    if not args.backend and not args.show and not args.build_models and not args.host_setup:
        ap.error("--backend · --show · --build-models · --host-setup 중 하나가 필요하다")
    if args.host_setup:
        rc = cmd_host_setup(args.dry_run)
        if not args.backend and not args.show and not args.build_models:
            return rc
    if args.build_models:
        backend = args.backend or active_backend(args.repo_root)
        # 창은 모델별이다(폴백 e4b 는 천장 131072) — 하나로 뭉뚱그려 찍지 않는다.
        print(f"── 로컬 파생 모델 준비 ──  배치 창 {OLLAMA_NUM_CTX} (폴백은 모델별 천장을 따른다)")
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
