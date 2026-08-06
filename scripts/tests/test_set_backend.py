#!/usr/bin/env python3
"""
set_backend 회귀 테스트
=======================
백엔드 전환기는 **남의 파일을 고친다** — 라이브 `hermes-home/profiles/*/config.yaml` 에는
Hermes 가 스스로 써 넣은 `onboarding:` 이 있고, root `hermes-home/config.yaml` 에는 6KB 짜리
`platform_toolsets:`·`personalities:` 가 있다. 이것들을 날리면 컨테이너가 조용히 다르게 동작한다.
그래서 이 테스트의 절반은 **안 건드려야 할 것을 안 건드렸는지**를 본다.

⚠️ 이 스크립트는 PyYAML 을 쓰지 않는다(호스트 python3 에 없다) — 행 단위 블록 치환이다.
   그러므로 블록 경계 판정이 유일한 위험 지점이고, 여기 테스트가 집중돼 있다.

실행: python3 scripts/tests/test_set_backend.py
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import set_backend as sb  # noqa: E402

SRC_CONFIG = """\
# named 프로필은 루트 config 미상속 → provider/model 명시. OAuth는 계정 공유(hermes auth).
model:
  default: gpt-5.6-terra
  provider: openai-codex
  base_url: https://chatgpt.com/backend-api/codex
agent:
  max_turns: 150
  reasoning_effort: medium
"""

LIVE_CONFIG = """\
model:
  default: gpt-5.6-sol
  provider: openai-codex
  base_url: https://chatgpt.com/backend-api/codex
agent:
  max_turns: 150
  reasoning_effort: medium
onboarding:
  seen:
    tool_progress_prompt: true
"""

ROOT_CONFIG = """\
model:
  default: gpt-5.6-terra
  provider: openai-codex
  base_url: https://chatgpt.com/backend-api/codex
database:
  journal_mode: wal
agent:
  max_turns: 150
  reasoning_effort: medium
  personalities:
    pirate: 'Arrr! Ye be talkin'' to Captain Hermes!'
platform_toolsets:
  cli:
    - browser
    - terminal
_config_version: 33
"""


def _repo(profiles: dict[str, str] | None = None, root: str | None = ROOT_CONFIG) -> str:
    """profiles-src + hermes-home 을 갖춘 임시 저장소를 만든다."""
    d = tempfile.mkdtemp()
    named = [p for p in sb.profile_of_tier() if p != "default"]
    for name in named:
        for sub in (os.path.join("profiles-src", name),
                    os.path.join("hermes-home", "profiles", name)):
            os.makedirs(os.path.join(d, sub), exist_ok=True)
        src = (profiles or {}).get(name, SRC_CONFIG)
        live = (profiles or {}).get(name, LIVE_CONFIG)
        _write(os.path.join(d, "profiles-src", name, "config.yaml"), src)
        _write(os.path.join(d, "hermes-home", "profiles", name, "config.yaml"), live)
    os.makedirs(os.path.join(d, "hermes-home"), exist_ok=True)
    if root is not None:
        _write(os.path.join(d, "hermes-home", "config.yaml"), root)
    return d


def _write(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


# ── 배치표 불변식 ───────────────────────────────────────────────────────────
def test_writer_and_verifier_share_a_model_only_by_explicit_declaration():
    """★ 작성자≠검증자 불변식 — 같은 모델이면 같은 맹점을 공유해 독립검증이 성립하지 않는다.

    2026-08-05 Sam 승인으로 ollama 백엔드는 속도 우선 통일을 택했다. 그 결정을 **코드에
    남기고** 지나가려면 `shared_verifier_model` 선언이 있어야 한다 — 선언 없이 같아지면
    실수다. 불변식을 조용히 잃지 않기 위한 장치다(삭제하지 않고 예외로 만든 이유).
    """
    for name, spec in sb.BACKENDS.items():
        if spec["models"]["writer"] == spec["models"]["verifier"]:
            assert spec.get("shared_verifier_model"), (
                f"{name}: 작성자와 검증자가 같은 모델인데 `shared_verifier_model` 선언이 없다 "
                "— 의도한 것이면 사유를 적어라")


def test_window_escapes_the_degenerate_compaction_branch():
    """★★ 이 테스트가 M-2026-005 를 멈춰 세운 결함의 회귀 방어다.

    Hermes 의 압축 발동 지점은 `context_length` 가 아니라 **입력 예산**에서 나온다
    (`context_compressor.py:2113`):
        effective = context_length - max_tokens
        floored   = max(effective × threshold, MINIMUM_CONTEXT_LENGTH=64000)
        floored >= effective  →  **퇴화 분기** = effective × 0.85
    `effective <= 64000` 이면 어떤 threshold 를 줘도 퇴화 분기라서 **compression.threshold
    가 완전히 무력**해진다. 65536-16384=49152 이 정확히 그 상태였고, 41,779 토큰에서
    압축이 걸려 stage 5 가 압축 루프에 갇혔다.
    """
    MINIMUM_CONTEXT_LENGTH = 64000   # /opt/hermes/agent/model_metadata.py:300
    common = sb.BACKENDS["ollama"]["common"]
    effective = common["context_length"] - common["max_tokens"]
    assert effective > MINIMUM_CONTEXT_LENGTH, (
        f"입력 예산 {effective} <= {MINIMUM_CONTEXT_LENGTH} — 퇴화 분기다. "
        "compression.threshold 가 무력해지고 압축이 창의 85%에서 상시 발동한다")


def test_compression_threshold_is_written_per_profile():
    """★ `compression.*` 는 루트 config 에서 **상속되지 않는다** — 프로필에 직접 써야 한다.

    named 프로필은 HERMES_HOME=<root>/profiles/<name> 이라 자기 config.yaml 만 읽는다
    (`hermes_cli/config.py:694` get_config_path). 루트에만 두면 조용히 기본값이 쓰인다.
    """
    extra = sb.BACKENDS["ollama"].get("extra_blocks", {})
    assert "compression" in extra, "compression 블록을 프로필에 쓰지 않는다"
    th = extra["compression"]["threshold"]
    # <512K 창은 0.75 로 하한이 강제된다(`_effective_threshold_percent`) — 그 이하는 무의미
    assert th > 0.75, f"threshold {th} 는 0.75 하한에 먹혀 아무 효과가 없다"


def test_every_profile_has_exactly_one_tier():
    seen: list[str] = []
    for profiles in sb.TIERS.values():
        seen.extend(profiles)
    assert len(seen) == len(set(seen)), f"중복 배치: {seen}"
    assert len(seen) == 11, f"프로필 11종이어야 한다 (현재 {len(seen)})"
    assert "default" in seen, "Solomon(default) 이 배치표에 없다"


def test_ollama_block_carries_every_required_key():
    """★ context_length·ollama_num_ctx 중 하나라도 빠지면 프롬프트가 조용히 잘린다."""
    keys = set(sb.BACKENDS["ollama"]["common"])
    for key in sb.REQUIRED_OLLAMA_KEYS:
        assert key in keys, f"ollama 백엔드에 {key} 가 없다"
    common = sb.BACKENDS["ollama"]["common"]
    assert common["context_length"] == common["ollama_num_ctx"], \
        "압축 임계와 실제 서빙 창이 다르면 프롬프트가 잘린다"
    assert common["base_url"].endswith("/v1"), "로컬 서버 URL 은 /v1 로 끝나야 한다"
    assert "host.docker.internal" in common["base_url"], \
        "컨테이너에서 localhost 는 컨테이너 자신이다"


def test_every_ollama_model_is_a_context_pinned_derivative():
    """★ 실측: Ollama 의 /v1 은 `options.num_ctx` 를 무시한다(=config 로는 창을 못 줄인다).

    창은 Modelfile 로 **서버 쪽에** 못박아야 한다. 원본 태그를 배치표에 그대로 쓰면
    모델 최대 창(262144)으로 로드돼 메모리를 몇 배로 먹는다 — 실측으로 llama3.1:8b 이
    8192 에서 5.9GB, 131072 에서 22GB 였다.
    """
    for model in sb.backend_models("ollama"):
        assert model in sb.BASE_MODELS, \
            f"{model} 이 파생본이 아니다 — 원본을 그대로 쓰면 창이 안 잡힌다"


def test_modelfile_pins_each_models_own_window():
    """Modelfile 의 num_ctx 는 **모델별**이다 — 전 모델이 하나를 공유하지 않는다.

    폴백 `gemma4:e4b` 는 천장이 131072 이라 262144 를 서빙할 수 없다. 배치 모델의 창을
    올릴 때 이 모델에까지 같은 값을 못박으면 로드가 실패하거나 조용히 깎인다.
    """
    for derived, spec in sb.BASE_MODELS.items():
        text = sb.modelfile(derived)
        assert f"PARAMETER num_ctx {spec['num_ctx']}" in text, text
        assert f"FROM {spec['base']}\n" in text, text


def test_no_model_is_pinned_above_its_measured_ceiling():
    """★ 천장은 추측이 아니라 실측이다(`/api/show` 의 `<family>.context_length`).

    창을 천장 위로 못박으면 Ollama 가 조용히 깎아서 로드한다 — config 는 큰 창을
    주장하고 서버는 작은 창을 서빙하는, 두 층 떨어진 실패가 된다(docs/11 §7 ⑦ 계열).
    """
    for derived, spec in sb.BASE_MODELS.items():
        assert spec["num_ctx"] <= spec["ceiling"], \
            f"{derived}: num_ctx {spec['num_ctx']} > 천장 {spec['ceiling']} ({spec['base']})"


def test_deployed_models_pin_the_same_window_as_the_config():
    """**배치에 쓰이는** 파생본은 config 의 context_length 와 창이 같아야 한다.

    갈라지면 프롬프트가 조용히 잘린다. 폴백은 배치에 안 쓰이므로 대상이 아니다.
    """
    common = sb.BACKENDS["ollama"]["common"]
    assert common["context_length"] == sb.OLLAMA_NUM_CTX
    for model in sb.backend_models("ollama"):
        assert sb.BASE_MODELS[model]["num_ctx"] == common["ollama_num_ctx"], \
            f"{model} 의 Modelfile 창이 config 의 ollama_num_ctx 와 다르다"


def test_derived_name_carries_its_window():
    """★ 파생본 이름은 창을 담는다 — 창이 바뀌면 이름이 바뀌어야 한다.

    `cmd_build_models` 는 존재를 **이름으로만** 판정한다(같은 이름이면 "이미 있음"으로
    건너뛴다). 창만 올리고 이름을 그대로 두면 서버는 옛 창을 계속 서빙하는데 config 는
    새 값을 주장한다. 이 테스트가 그 실수를 이름 규약으로 막는다.
    """
    for derived, spec in sb.BASE_MODELS.items():
        suffix = f"-{spec['num_ctx'] // 1024}k"
        assert derived.endswith(suffix), \
            f"{derived} 의 이름이 창({spec['num_ctx']})을 담고 있지 않다 — {suffix} 로 끝나야 한다"


def test_model_names_with_colons_are_quoted():
    """`qwen3.6:35b` 를 따옴표 없이 쓰면 YAML 해석이 애매해진다."""
    block = sb.render_model_block("ollama", "qwen3.6:35b", with_header=False)
    assert '  default: "qwen3.6:35b"' in block, block


# ── 블록 경계 (유일한 위험 지점) ────────────────────────────────────────────
def test_finds_model_block_and_stops_at_next_top_level_key():
    lines = SRC_CONFIG.splitlines()
    start, end = sb.find_model_block(lines)
    assert lines[start].startswith("#"), "바로 위 주석을 블록에 포함해야 한다"
    assert lines[end] == "agent:", f"블록이 다음 최상위 키를 삼켰다: {lines[start:end]}"


def test_parses_values_and_strips_quotes():
    cfg = sb.parse_model_block(['model:', '  default: "qwen3.6:35b"', '  provider: ollama'])
    assert cfg["default"] == "qwen3.6:35b" and cfg["provider"] == "ollama", cfg


def test_nested_keys_are_not_read_as_top_level():
    cfg = sb.parse_model_block(['model:', '  default: x', '  aliases:', '    fast: y'])
    assert "fast" not in cfg and cfg["default"] == "x", cfg


# ── 안 건드려야 할 것 ───────────────────────────────────────────────────────
def test_preserves_agent_block_in_source_config():
    """`agent:` 블록은 살아남는다.

    ⚠️ `reasoning_effort` 는 **백엔드가 정한다**(ollama → `none`). 이 테스트는 원래
       `medium` 이 남는 것을 단언했는데, 그건 **버그를 못박아 둔 것**이었다 —
       그 값이 그대로 로컬로 전달돼 thinking 없는 모델을 HTTP 400 으로 죽였다.
    """
    d = _repo()
    path = os.path.join(d, "profiles-src", "scout", "config.yaml")
    sb.apply_to_file(path, "ollama", "qwen3.6:35b", with_header=True)
    text = _read(path)
    assert "agent:" in text and "max_turns: 150" in text, text
    assert sb.parse_model_block(text.splitlines(), "agent")["reasoning_effort"] == "none", text


def test_writes_compression_block_and_keeps_other_blocks():
    d = _repo()
    path = os.path.join(d, "profiles-src", "scout", "config.yaml")
    sb.apply_to_file(path, "ollama", "gemma4-26b-256k", with_header=True)
    text = _read(path)
    assert "compression:" in text, text
    cfg = sb.parse_model_block(text.splitlines(), "compression")
    assert float(cfg["threshold"]) == sb.COMPRESSION_THRESHOLD, cfg
    assert "agent:" in text and "max_turns: 150" in text, "agent 블록이 사라졌다"
    assert sb.parse_model_block(text.splitlines())["provider"] == "ollama"


def test_ollama_turns_off_reasoning_effort_left_behind_by_codex():
    """★ codex 의 `reasoning_effort: medium` 이 남으면 로컬 모델이 **HTTP 400 으로 죽는다.**

    실측 2026-08-06 (3): `custom` 프로바이더가 이 값을 top-level `reasoning_effort` 로
    실어 보내고, thinking 능력이 없는 모델(devstral)은 Ollama 가
    `"<model>" does not support thinking` 400 으로 거절한다. 워커는 툴콜 0회로 죽고
    카드에는 `protocol violation` 만 남아 **증상과 원인이 두 층 떨어진다.**
    """
    d = _repo()
    for name in ("scout",):
        path = os.path.join(d, "profiles-src", name, "config.yaml")
        assert "reasoning_effort: medium" in _read(path), "픽스처 전제가 깨졌다"
        sb.apply_to_file(path, "ollama", sb.BACKENDS["ollama"]["models"]["writer"],
                         with_header=True)
        agent = sb.parse_model_block(_read(path).splitlines(), "agent")
        assert agent["reasoning_effort"] == "none", agent
        assert agent["max_turns"] == "150", "같은 블록의 다른 키를 건드렸다"


def test_codex_switch_restores_reasoning_effort():
    """★ 되돌릴 때 추론 강도도 같이 돌아와야 한다 — 안 그러면 codex 가 조용히 약해진다.

    ⚠️ **기대값을 배치표에서 읽는다.** 예전엔 `"medium"` 을 박아 뒀는데, 2026-08-06 (6)
       Sam 이 `low` 로 낮추자 이 테스트가 깨졌다 — 검사하려던 성질(**전환이 강도를
       되살리는가**)은 그대로인데 상수만 낡은 것이다. 같은 함정을 이 세션에 두 번
       밟았다(`test_usage_report` 의 '틀린 창' 상수 131072). **상수는 언젠가 진짜 값이 된다.**
    """
    d = _repo()
    path = os.path.join(d, "profiles-src", "scout", "config.yaml")
    want = sb.BACKENDS["codex"]["patch_keys"]["agent"]["reasoning_effort"]
    off = sb.BACKENDS["ollama"]["patch_keys"]["agent"]["reasoning_effort"]
    assert want != off, "두 백엔드의 추론 강도가 같으면 이 테스트는 아무것도 안 잰다"
    sb.apply_to_file(path, "ollama", sb.BACKENDS["ollama"]["models"]["writer"], with_header=True)
    assert sb.parse_model_block(_read(path).splitlines(), "agent")["reasoning_effort"] == off
    sb.apply_to_file(path, "codex", sb.BACKENDS["codex"]["models"]["writer"], with_header=True)
    assert sb.parse_model_block(_read(path).splitlines(), "agent")["reasoning_effort"] == want


def test_patching_a_key_never_eats_the_rest_of_the_block():
    """★ `agent:` 를 블록 교체하면 루트 config 의 `personalities` 가 사라진다.

    그래서 `patch_keys` 는 splice 가 아니라 **그 키 한 줄만** 바꾼다.
    """
    d = _repo()
    path = os.path.join(d, "hermes-home", "config.yaml")
    assert "personalities:" in _read(path), "픽스처 전제가 깨졌다"
    sb.apply_to_file(path, "ollama", sb.BACKENDS["ollama"]["models"]["writer"], with_header=False)
    text = _read(path)
    assert "personalities:" in text, "agent 블록의 나머지가 지워졌다"
    assert "max_turns: 150" in text, text
    assert sb.parse_model_block(text.splitlines(), "agent")["reasoning_effort"] == "none"


def test_patch_keys_does_not_invent_absent_keys():
    """★ 없는 키를 심지 않는다 — 우리가 Hermes 스키마를 발명하면 안 된다."""
    lines = ["model:", "  default: x", "agent:", "  max_turns: 150"]
    out = sb.patch_block_keys(lines, "ollama")
    assert "reasoning_effort" not in "\n".join(out), out


def test_codex_switch_removes_the_ollama_only_compression_block():
    """★ 백엔드를 되돌릴 때 다른 백엔드의 블록이 남으면 설정이 섞인다."""
    d = _repo()
    path = os.path.join(d, "profiles-src", "scout", "config.yaml")
    sb.apply_to_file(path, "ollama", "gemma4-26b-256k", with_header=True)
    assert "compression:" in _read(path)
    sb.apply_to_file(path, "codex", "gpt-5.6-terra", with_header=True)
    text = _read(path)
    assert "compression:" not in text, text
    assert "agent:" in text and "max_turns: 150" in text, "agent 블록이 사라졌다"


def test_preserves_onboarding_block_written_by_hermes():
    """★ 라이브 파일은 Hermes 가 스스로 고쳐 놓는다 — 통째로 덮어쓰면 그 상태를 날린다."""
    d = _repo()
    path = os.path.join(d, "hermes-home", "profiles", "reviewer", "config.yaml")
    sb.apply_to_file(path, "ollama", "glm-4.7-flash", with_header=False)
    text = _read(path)
    assert "onboarding:" in text and "tool_progress_prompt: true" in text, text


def test_preserves_root_config_large_blocks():
    d = _repo()
    path = os.path.join(d, "hermes-home", "config.yaml")
    before = _read(path)
    sb.apply_to_file(path, "ollama", "qwen3.6:35b", with_header=False)
    text = _read(path)
    for marker in ("database:", "journal_mode: wal", "platform_toolsets:",
                   "personalities:", "Captain Hermes", "_config_version: 33"):
        assert marker in text, f"root config 에서 {marker!r} 가 사라졌다"
    assert len(text.splitlines()) >= len(before.splitlines()) - 1


def test_live_file_gets_no_generated_header():
    """라이브 파일에 주석을 넣어봐야 Hermes 가 다음 rewrite 에서 지운다 — 소스에만 넣는다."""
    d = _repo()
    path = os.path.join(d, "hermes-home", "profiles", "reviewer", "config.yaml")
    sb.apply_to_file(path, "ollama", "glm-4.7-flash", with_header=False)
    assert not _read(path).startswith("#"), _read(path)


# ── 적용·판정·복귀 ─────────────────────────────────────────────────────────
def test_apply_switches_every_target_and_show_agrees():
    d = _repo()
    assert sb.main(["--backend", "ollama", "--repo-root", d]) == 0
    state = sb.inspect(d)
    assert state["active"] == "ollama", state["active"]
    assert state["consistent"], [r for r in state["rows"] if r["missing_keys"]]
    by_profile = {r["profile"]: r for r in state["rows"]}
    assert by_profile["scout"]["model"] == sb.BACKENDS["ollama"]["models"]["writer"]
    assert by_profile["reviewer"]["model"] == sb.BACKENDS["ollama"]["models"]["verifier"]
    assert by_profile["developer"]["model"] == sb.BACKENDS["ollama"]["models"]["coder"]


def test_round_trip_returns_to_original_codex_placement():
    """★ 복귀 경로 — 되돌린 뒤 **배치표와** 같아야 한다.

    ⚠️ 모델명을 리터럴로 박지 않는다. 이 테스트가 보려는 성질은 "왕복이 손실 없는가"지
       특정 모델명이 아니다. 리터럴을 박으면 배치를 바꿀 때마다 **성질과 무관하게**
       깨져서, 고치는 사람이 테스트를 배치표에 맞춰 수정하는 습관이 든다
       (2026-08-05 (3) 전 티어 gpt-5.5 단일화에서 실제로 이 테스트만 깨졌다).
    """
    d = _repo()
    sb.main(["--backend", "ollama", "--repo-root", d])
    sb.main(["--backend", "codex", "--repo-root", d])
    state = sb.inspect(d)
    assert state["active"] == "codex" and state["consistent"], state["active"]
    by_profile = {r["profile"]: r for r in state["rows"]}
    tier_of = sb.profile_of_tier()
    for name, row in by_profile.items():
        want = sb.BACKENDS["codex"]["models"][tier_of[name]]
        assert row["model"] == want, f"{name}: {row['model']} != {want}"


def test_detects_mixed_state():
    """일부만 전환된 상태는 **정상으로 보이면 안 된다** — 절반이 한도를 계속 태운다."""
    d = _repo()
    sb.main(["--backend", "ollama", "--repo-root", d])
    _write(os.path.join(d, "profiles-src", "writer", "config.yaml"), SRC_CONFIG)
    state = sb.inspect(d)
    assert state["active"] == "mixed", state["active"]
    assert not state["consistent"]
    assert sb.main(["--show", "--repo-root", d]) == 1, "불일치인데 exit 0 이다"


def test_inconsistent_model_within_one_backend_is_reported():
    """백엔드는 맞는데 모델이 배치표와 다른 경우(수작업 흔적)도 잡아야 한다."""
    d = _repo()
    sb.main(["--backend", "ollama", "--repo-root", d])
    path = os.path.join(d, "profiles-src", "reviewer", "config.yaml")
    _write(path, _read(path).replace(sb.BACKENDS["ollama"]["models"]["verifier"], "llama3.1:8b"))
    state = sb.inspect(d)
    assert state["active"] == "ollama" and not state["consistent"], state


def test_missing_hermes_home_does_not_fail():
    """새 PC 에는 hermes-home 이 없다 — 소스만 갱신하고 넘어가야 한다."""
    d = _repo(root=None)
    import shutil
    shutil.rmtree(os.path.join(d, "hermes-home"))
    assert sb.main(["--backend", "ollama", "--repo-root", d]) == 0
    assert sb.inspect(d)["active"] == "ollama"


def test_inserts_block_when_config_has_none():
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "profiles-src", "scout"))
    path = os.path.join(d, "profiles-src", "scout", "config.yaml")
    _write(path, "agent:\n  max_turns: 150\n")
    did, _ = sb.apply_to_file(path, "ollama", "qwen3.6:35b", with_header=True)
    text = _read(path)
    assert did and "model:" in text and "agent:" in text, text
    assert sb.parse_model_block(text.splitlines())["provider"] == "ollama"


def test_second_apply_is_a_no_op():
    d = _repo()
    sb.main(["--backend", "ollama", "--repo-root", d])
    path = os.path.join(d, "profiles-src", "scout", "config.yaml")
    before = _read(path)
    did, msg = sb.apply_to_file(path, "ollama", sb.BACKENDS["ollama"]["models"]["writer"],
                                with_header=True)
    assert not did and msg == "이미 동일", (did, msg, before)


def test_dry_run_changes_nothing():
    d = _repo()
    path = os.path.join(d, "profiles-src", "scout", "config.yaml")
    before = _read(path)
    assert sb.main(["--backend", "ollama", "--dry-run", "--repo-root", d]) == 0
    assert _read(path) == before, "dry-run 이 파일을 고쳤다"


def test_backend_models_helper():
    models = sb.backend_models("ollama")
    assert sb.BACKENDS["ollama"]["models"]["verifier"] in models
    assert len(models) == len(set(models)), models


def test_active_backend_helper_on_real_repo_shape():
    d = _repo()
    assert sb.active_backend(d) == "codex"
    sb.main(["--backend", "ollama", "--repo-root", d])
    assert sb.active_backend(d) == "ollama"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
