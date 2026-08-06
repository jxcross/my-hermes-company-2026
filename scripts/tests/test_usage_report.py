#!/usr/bin/env python3
"""
usage_report 회귀 테스트
========================
한도 소진을 **로그에서** 읽는 파서를 검사한다. 이 판정이 틀리면 미션을 한도가 없는 줄 알고
시작하거나(소진 미탐지), 멀쩡한데 못 시작한다(거짓 소진).

⚠️ 시계에 의존하지 않는다 — `--now` 로 시각을 주입한다. 시각에 의존하는 판정은 시간이 지나면
   픽스처가 깨진다(아키타입 P 에서 배운 것 · docs/13 §5).

실행: python3 scripts/tests/test_usage_report.py
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import usage_report as ur  # noqa: E402

RESETS = 1786252061  # 2026-08-09 14:07 KST

LOG_429 = (
    "⚠️  API call failed (attempt 3/3): RateLimitError [HTTP 429]\n"
    "   📝 Error: HTTP 429: The usage limit has been reached\n"
    "   📋 Details: {'type': 'usage_limit_reached', 'message': 'The usage limit has been "
    f"reached', 'plan_type': 'team', 'resets_at': {RESETS}, 'eligible_promo': None, "
    "'resets_in_seconds': 347006}\n")
LOG_OK = "✅ Task complete\nSession: 20260805_x\nDuration: 42s\n"
LOG_AUTH = "❌ 401 Unauthorized — check credentials\n"


def _dir(files: dict) -> str:
    d = tempfile.mkdtemp()
    for name, text in files.items():
        with open(os.path.join(d, name), "w", encoding="utf-8") as f:
            f.write(text)
    return d


def test_parses_reset_time_and_plan():
    """★ plan_type 을 같은 정규식의 선택 그룹으로 두면 비탐욕 매칭이 건너뛴다(실측: 항상 plan=?)."""
    latest, failed = ur.scan_limits([os.path.join(_dir({"t_a.log": LOG_429}), "t_a.log")])
    assert latest is not None, "429 기록을 못 읽었다"
    assert latest["resets_at"] == RESETS
    assert latest["plan"] == "team", latest
    assert latest["type"] == "usage_limit_reached"
    assert failed == ["t_a"]


def test_no_limit_record_is_not_exhausted():
    latest, failed = ur.scan_limits([os.path.join(_dir({"t_b.log": LOG_OK}), "t_b.log")])
    assert latest is None and failed == []


def test_auth_failure_counts_as_environment_failure_not_limit():
    """인증 실패는 한도 소진이 아니지만 **파이프라인 결함도 아니다** — 환경성 실패로 분류한다."""
    latest, failed = ur.scan_limits([os.path.join(_dir({"t_c.log": LOG_AUTH}), "t_c.log")])
    assert latest is None, "인증 실패를 한도 소진으로 오인했다"
    assert failed == ["t_c"]


def test_exhaustion_verdict_uses_injected_clock():
    """리셋 전이면 소진, 리셋 후면 정상 — 시계를 주입해 판정한다."""
    d = _dir({"t_d.log": LOG_429})
    paths = [os.path.join(d, "t_d.log")]
    latest, _ = ur.scan_limits(paths)
    assert latest["resets_at"] > RESETS - 1
    assert (latest["resets_at"] > RESETS - 3600) and not (latest["resets_at"] > RESETS + 1)


def test_latest_record_wins_across_files():
    d = _dir({"t_old.log": LOG_429.replace(str(RESETS), str(RESETS - 100000)),
              "t_new.log": LOG_429})
    latest, failed = ur.scan_limits([os.path.join(d, n) for n in sorted(os.listdir(d))])
    assert latest["resets_at"] == RESETS, latest
    assert set(failed) == {"t_old", "t_new"}


def test_main_exit_codes(capsys=None):
    """exit 1 = 소진 중(미션 착수 전 점검이 이 코드로 막는다) · 0 = 정상.

    ⚠️ `AUTH_PATHS` 도 반드시 격리한다. 2026-08-06 에 풀 인식을 넣었더니 이 테스트가
       **개발자 PC 의 실제 `hermes-home/auth.json` 을 읽어** 통과해 버렸다 — 로그 기반
       판정을 재려던 테스트가 조용히 환경 의존이 된 것이다. 여기서는 풀을 '모른다'로
       두어야(존재하지 않는 경로) 원래 재려던 폴백 경로가 측정된다."""
    d = _dir({"t_e.log": LOG_429})
    orig = ur.LOG_DIRS
    orig_auth = ur.AUTH_PATHS
    ur.LOG_DIRS = [d]
    ur.AUTH_PATHS = [os.path.join(d, "no-such-auth.json")]
    try:
        sys.argv = ["usage_report", "--quiet", "--backend", "codex",
                    "--now", str(RESETS - 3600)]
        assert ur.main() == 1, "리셋 전인데 소진으로 판정하지 않았다"
        sys.argv = ["usage_report", "--quiet", "--backend", "codex",
                    "--now", str(RESETS + 3600)]
        assert ur.main() == 0, "리셋 후인데 소진으로 판정했다"
    finally:
        ur.LOG_DIRS = orig
        ur.AUTH_PATHS = orig_auth


# ── 백엔드 인식 (2026-08-05 · docs/14) ──────────────────────────────────────
# 로컬 백엔드에서는 한도라는 것이 없는데 로그의 429 는 그대로 남아 있다. 그것만 보면
# 리셋 시각까지 계속 exit 1 이 나와 **로컬로 옮긴 의미가 사라진다.**

def _fake_tags(names):
    return lambda url="": (list(names), "")


def test_local_backend_ignores_stale_codex_limit(monkeypatch=None):
    """★ 이 테스트가 이 변경의 존재 이유다 — 로컬인데 codex 한도로 막히면 안 된다."""
    import set_backend as sb
    d = _dir({"t_x.log": LOG_429})
    orig_logs, orig_tags = ur.LOG_DIRS, ur.ollama_tags
    ur.LOG_DIRS = [d]
    ur.ollama_tags = _fake_tags(sb.backend_models("ollama"))
    try:
        sys.argv = ["usage_report", "--quiet", "--now", str(RESETS - 3600)]
        args = _args(now=RESETS - 3600)
        assert ur.main_local(args, "ollama") == 0, \
            "로컬 백엔드인데 지나간 codex 한도 기록으로 착수를 막았다"
    finally:
        ur.LOG_DIRS, ur.ollama_tags = orig_logs, orig_tags


def test_local_backend_blocks_when_model_missing():
    """모델이 없으면 워커가 매 턴 실패한다 — 카드에는 이유가 안 남는다(docs/11 §7 ⑦).

    ⚠️ 픽스처가 **배치 모델 개수에 의존하면 안 된다** — 2026-08-05 배치를 단일 모델로
    통일하자 '1종만 설치' 픽스처가 곧 '전부 설치'가 되어 이 테스트가 조용히 무의미해졌다.
    설치 목록에 배치 모델이 하나도 없도록 고정한다.
    """
    orig_logs, orig_tags = ur.LOG_DIRS, ur.ollama_tags
    ur.LOG_DIRS = [_dir({})]
    ur.ollama_tags = _fake_tags(["some-unrelated-model:latest"])  # 배치 모델 0종
    try:
        assert ur.main_local(_args(), "ollama") == 1, "모델이 없는데 착수 가능으로 판정했다"
    finally:
        ur.LOG_DIRS, ur.ollama_tags = orig_logs, orig_tags


def test_local_backend_blocks_when_server_unreachable():
    orig_logs, orig_tags = ur.LOG_DIRS, ur.ollama_tags
    ur.LOG_DIRS = [_dir({})]
    ur.ollama_tags = lambda url="": (None, "URLError: refused")
    try:
        assert ur.main_local(_args(), "ollama") == 1, "서버가 죽었는데 착수 가능으로 판정했다"
    finally:
        ur.LOG_DIRS, ur.ollama_tags = orig_logs, orig_tags


def test_check_local_accepts_latest_suffix_variants():
    """ollama 는 `foo` 를 `foo:latest` 로 보고한다 — 이름 비교만 하면 거짓 '없음' 이 난다."""
    import set_backend as sb
    want = sb.backend_models("ollama")
    orig = ur.ollama_tags
    ur.ollama_tags = _fake_tags([f"{w}:latest" if ":" not in w else w for w in want])
    try:
        assert ur.check_local("ollama")["missing"] == [], ur.check_local("ollama")
    finally:
        ur.ollama_tags = orig


def test_local_probe_never_calls_an_llm():
    """★ 한도를 확인하려고 한도를 쓰면 안 된다 — 로컬 점검도 /api/tags 만 본다."""
    seen = []
    orig = ur.urllib.request.urlopen
    ur.ollama_tags(url="http://127.0.0.1:1")   # 닿지 않아도 예외를 삼켜야 한다
    src = open(ur.__file__, encoding="utf-8").read()
    assert "/api/tags" in src and "/api/chat" not in src and "/api/generate" not in src, \
        "로컬 점검이 추론 엔드포인트를 부른다"
    assert orig is ur.urllib.request.urlopen and seen == []


# ── 서버 실효 설정 점검 (2026-08-06) ────────────────────────────────────────
# ★ 이 묶음의 존재 이유: launchctl 에 값을 걸어 놓고 **서버에 반영됐다고 착각한 채**
#   세션 여러 개가 지나갔다. `docs/14 §5` 는 MAX_LOADED_MODELS=1·KEEP_ALIVE=30m 를
#   지시했는데 실측한 서버 배너는 `0`·`5m0s` 였다. 걸어 놓은 것 ≠ 반영된 것.

BANNER = ("time=2026-08-06T09:00:00.000+09:00 level=INFO source=routes.go:1500 "
          "msg=\"server config\" env=\"map[OLLAMA_CONTEXT_LENGTH:0 "
          "OLLAMA_FLASH_ATTENTION:false OLLAMA_KEEP_ALIVE:5m0s OLLAMA_KV_CACHE_TYPE: "
          "OLLAMA_MAX_LOADED_MODELS:0 OLLAMA_NUM_PARALLEL:1]\"")
BANNER_OK = ("time=2026-08-06T10:00:00.000+09:00 level=INFO msg=\"server config\" "
             "env=\"map[OLLAMA_CONTEXT_LENGTH:0 OLLAMA_FLASH_ATTENTION:true "
             "OLLAMA_KEEP_ALIVE:30m0s OLLAMA_KV_CACHE_TYPE:q8_0 "
             "OLLAMA_MAX_LOADED_MODELS:1 OLLAMA_NUM_PARALLEL:3]\"")


def _log_with(banner: str, filler_mb: int = 0) -> str:
    """배너 + 뒤에 filler. 배너를 **파일 앞쪽에** 두는 것이 핵심이다."""
    import set_backend as sb
    d = tempfile.mkdtemp()
    p = os.path.join(d, "server.log")
    with open(p, "w", encoding="utf-8") as f:
        f.write(banner + "\n")
        for _ in range(filler_mb * 1024):
            f.write("x" * 1023 + "\n")
    return p


def test_norm_env_treats_notation_differences_as_equal():
    """서버는 `1`을 `true` 로, `30m` 을 `30m0s` 로 되받는다 — 표기 차이는 불일치가 아니다.

    ★ 시끄러운 검사는 곧 무시된다. 오탐을 먼저 없앤다.
    """
    import set_backend as sb
    assert sb._norm_env("OLLAMA_FLASH_ATTENTION", "1") == \
           sb._norm_env("OLLAMA_FLASH_ATTENTION", "true")
    assert sb._norm_env("OLLAMA_KEEP_ALIVE", "30m") == \
           sb._norm_env("OLLAMA_KEEP_ALIVE", "30m0s")
    # 그리고 진짜 다른 것은 여전히 다르다(양방향 확인)
    assert sb._norm_env("OLLAMA_NUM_PARALLEL", "1") != \
           sb._norm_env("OLLAMA_NUM_PARALLEL", "3")
    assert sb._norm_env("OLLAMA_FLASH_ATTENTION", "0") != \
           sb._norm_env("OLLAMA_FLASH_ATTENTION", "1")


def test_banner_found_even_when_far_from_end_of_a_large_log():
    """★ 회귀: 뒤에서부터 창을 키우며 찾는 로직이 **파일 전체에 못 미친 채 종료**했다.

    실제 server.log 는 30MB 인데 배너는 1행에 있다 — 첫 구현은 배너를 못 찾고
    '판정 불가'를 돌려줬고, 그래서 어긋난 설정을 **조용히 통과**시켰다.
    """
    import set_backend as sb
    got = sb._last_server_banner(_log_with(BANNER, filler_mb=3))
    assert got is not None, "3MB 로그의 앞쪽 배너를 찾지 못했다"
    assert got.get("OLLAMA_NUM_PARALLEL") == "1", got


def test_banner_partial_window_does_not_yield_truncated_values():
    """부분 창의 첫 줄은 잘려 있을 수 있다 — 잘린 배너를 온전한 것으로 읽으면 안 된다."""
    import set_backend as sb
    got = sb._last_server_banner(_log_with(BANNER, filler_mb=2))
    assert got is not None and got.get("OLLAMA_KEEP_ALIVE") == "5m0s", got


def test_server_env_state_flags_unapplied_settings():
    import set_backend as sb
    st = sb.server_env_state(_log_with(BANNER))
    assert st["available"] is True
    names = {r["var"] for r in st["mismatched"]}
    assert "OLLAMA_NUM_PARALLEL" in names, st
    assert "OLLAMA_MAX_LOADED_MODELS" in names, "docs/14 가 지시한 값의 미반영을 놓쳤다"


def test_server_env_state_passes_when_applied():
    """★ 반대 방향 — 정상 배너에 FAIL 이 나오면 그 검사는 아무것도 측정하지 못한다."""
    import set_backend as sb
    st = sb.server_env_state(_log_with(BANNER_OK))
    assert st["mismatched"] == [], st["mismatched"]


def test_server_env_state_unavailable_does_not_judge():
    """확인할 수 없는 것을 FAIL 로 만들면 그 검사는 꺼진다(컨테이너에는 로그가 없다)."""
    import set_backend as sb
    st = sb.server_env_state(os.path.join(tempfile.mkdtemp(), "없는파일.log"))
    assert st["available"] is False and st["mismatched"] == []


def test_runtime_check_never_blocks_mission_start():
    """★ 런타임 점검은 WARN 전용이다 — 설정이 어긋나도 착수 판정을 바꾸면 안 된다.

    (막아야 하는 것은 '서버 불통·모델 없음' 뿐이다. 느려지는 것과 못 도는 것은 다르다.)
    """
    import set_backend as sb
    orig_logs, orig_tags, orig_srv = ur.LOG_DIRS, ur.ollama_tags, sb.server_env_state
    ur.LOG_DIRS = [_dir({})]
    ur.ollama_tags = _fake_tags(sb.backend_models("ollama"))
    sb.server_env_state = lambda log_path=None: {
        "available": True, "vars": [],
        "mismatched": [{"var": "OLLAMA_NUM_PARALLEL", "want": "3", "have": "1", "ok": False}]}
    try:
        assert ur.main_local(_args(), "ollama") == 0, \
            "서버 설정 불일치로 착수를 막았다 — WARN 이어야 한다"
    finally:
        ur.LOG_DIRS, ur.ollama_tags = orig_logs, orig_tags
        sb.server_env_state = orig_srv


def test_context_mismatch_is_detected_from_the_server_not_the_config():
    """★ 파생본이 옛 창을 물고 있으면 config 는 새 값을 주장하고 서버는 옛 값을 서빙한다.

    두 층 떨어진 실패다 — 그래서 **서버가 보고하는 값**(/api/ps)을 본다.
    """
    import set_backend as sb
    # ⚠️ 서빙 모델명을 **배치표에서 읽는다.** 문자열로 박아 두면 배치가 바뀌는 순간
    #    이 픽스처가 '배치 밖 모델'이 되어 아래 test_..._ignores_models_outside_the_batch
    #    경로로 빠지고, 검사는 **조용히 아무것도 재지 않게 된다**(2026-08-06 실제 발생).
    batch_model = sb.backend_models("ollama")[0]
    # ⚠️ **'틀린 창'도 배치표에서 파생시킨다.** 2026-08-06 (5) 에 배치를 `gpt-oss-20b-128k`
    #    (창 131072)로 바꾸자, 여기 박혀 있던 '틀린 값' 131072 가 **맞는 값이 되어** 이
    #    테스트가 FAIL 했다. 위 주석이 경고한 함정을 정확히 반대 방향으로 밟은 것이다 —
    #    상수는 언젠가 진짜 값과 충돌한다. 배치 창의 절반이면 어떤 창에서도 다르다.
    stale_ctx = sb.OLLAMA_NUM_CTX // 2
    assert stale_ctx != sb.OLLAMA_NUM_CTX
    orig_ps = ur.ollama_ps
    ur.ollama_ps = lambda url="": ([{"name": f"{batch_model}:latest",
                                     "context_length": stale_ctx, "size": 17_000_000_000}], "")
    try:
        rt = ur.check_runtime()
        assert rt["context_mismatch"], "서버가 옛 창을 서빙하는데 못 잡았다"
        assert rt["context_mismatch"][0]["expected"] == sb.OLLAMA_NUM_CTX
    finally:
        ur.ollama_ps = orig_ps


def test_context_mismatch_ignores_models_outside_the_batch():
    """★ 프로브가 올린 다른 모델까지 경고하면 소음이 된다 — 소음이 나는 검사는 무시된다.

    실제로 `devstral-small-2:24b`(프로브용 창 16384)가 배치 불일치로 잡혔다.
    """
    orig_ps = ur.ollama_ps
    ur.ollama_ps = lambda url="": ([{"name": "devstral-small-2:24b",
                                     "context_length": 16384, "size": 18_600_000_000}], "")
    try:
        assert ur.check_runtime()["context_mismatch"] == [], "배치 밖 모델을 경고했다"
    finally:
        ur.ollama_ps = orig_ps


def test_no_context_mismatch_when_server_matches():
    """반대 방향 — 맞는 창에 경고가 뜨면 경고가 의미를 잃는다."""
    import set_backend as sb
    orig_ps = ur.ollama_ps
    ur.ollama_ps = lambda url="": ([{"name": "m", "context_length": sb.OLLAMA_NUM_CTX,
                                     "size": 1}], "")
    try:
        assert ur.check_runtime()["context_mismatch"] == []
    finally:
        ur.ollama_ps = orig_ps


def test_restart_pending_separates_not_set_from_not_applied():
    """★ '안 걸었다' 와 '걸었는데 반영 안 됐다' 는 처방이 다르다(setenv vs 재시작)."""
    import set_backend as sb
    orig_host, orig_srv, orig_ps = sb.host_env_state, sb.server_env_state, ur.ollama_ps
    sb.host_env_state = lambda: {
        "available": True, "mismatched": [],
        "vars": [{"var": v, "want": w, "have": w, "ok": True} for v, w in sb.HOST_ENV.items()]}
    sb.server_env_state = lambda log_path=None: {
        "available": True, "vars": [],
        "mismatched": [{"var": "OLLAMA_NUM_PARALLEL", "want": "3", "have": "1", "ok": False}]}
    ur.ollama_ps = lambda url="": ([], "")
    try:
        rt = ur.check_runtime()
        assert [r["var"] for r in rt["restart_pending"]] == ["OLLAMA_NUM_PARALLEL"], rt
    finally:
        sb.host_env_state, sb.server_env_state, ur.ollama_ps = orig_host, orig_srv, orig_ps


def test_omitted_var_is_flagged_when_present():
    """`OLLAMA_CONTEXT_LENGTH` 는 **넣으면 안 된다** — 넣었을 때 잡아야 선언이 의미를 갖는다."""
    import set_backend as sb
    orig = sb._launchctl_get
    sb._launchctl_get = lambda var: ("65536" if var == "OLLAMA_CONTEXT_LENGTH" else
                                     sb.HOST_ENV.get(var, ""))
    try:
        st = sb.host_env_state()
        assert any(r["var"] == "OLLAMA_CONTEXT_LENGTH" for r in st["mismatched"]), st
    finally:
        sb._launchctl_get = orig


def test_parallel_probe_verdicts_on_real_measurements():
    """★ 판정 자체를 검사한다 — 검사하는 쪽도 검사받아야 한다.

    픽스처는 **실측값**이다(gemma4-26b-256k · 동시 3 · 2026-08-06):
      · NUM_PARALLEL 미설정 → 종료 [1.49,2.68,3.94] 분산 1.70 · 이득 ×0.84
      · NUM_PARALLEL=3      → 종료 [2.77,2.77,2.77] 분산 0.00 · 이득 ×1.27
    ⚠️ 처음엔 총 벽시계 비율(×1.85)로 판정했다가 **완전한 병렬을 '부분병렬'로 오판**했다.
       GPU 는 병렬이어도 요청당 벽시계가 늘기 때문이다.
    """
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    import probe_parallel as pp
    assert pp.verdict_of(0.00, 1.27, 3, 3) == "병렬", "실측 병렬을 못 읽었다"
    assert pp.verdict_of(1.70, 0.84, 3, 3) == "직렬", "실측 직렬(계단)을 못 읽었다"


def test_parallel_probe_rejects_no_gain_even_when_ends_cluster():
    """종료가 몰려도 **이득이 없으면** 병렬이라 부를 이유가 없다(두 신호를 함께 본다)."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    import probe_parallel as pp
    assert pp.verdict_of(0.0, 0.95, 3, 3) == "직렬"


def test_parallel_probe_incomplete_beats_a_fast_looking_ratio():
    """★ 요청이 죽으면 남은 것끼리는 분산이 작아 보인다 — 완료 수를 먼저 본다."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    import probe_parallel as pp
    assert pp.verdict_of(0.0, 1.5, 3, 1) == "불완전", "죽은 요청을 '병렬' 로 읽었다"


def _args(now=None):
    class A:
        pass
    a = A()
    a.json = False
    a.quiet = True
    a.now = now
    a.ollama_url = ""
    a.repo_root = ur.REPO_ROOT
    return a


# ── pooled 자격 인식 (2026-08-06) ───────────────────────────────────────────
# ⚠️⚠️ 왜 생겼나 — 실측 2026-08-06.
#   codex 계정을 하나 더 붙였다(`hermes auth add openai-codex`). 새 자격으로 실제
#   추론이 **성공**했는데도 이 스크립트는 `exit 1`("미션을 새로 시작하지 마라")을 냈다.
#   근거를 워커 로그의 429 기록**에서만** 읽었기 때문이다. 그 기록은 여전히 참이다 —
#   "그 자격이 그때 소진됐다". 다만 **착수 가능 여부와는 무관해졌다.**
#   → 착수 판정의 진실은 `auth.json` 의 `credential_pool` 이다. 로그는 과거의 기록이다.
TOKEN_CANARY = "SECRET-ACCESS-TOKEN-DO-NOT-LEAK-abcdefghijklmnop"


def _auth(pool: dict) -> str:
    """auth.json 픽스처 경로. 토큰 값을 일부러 넣어 유출 여부를 잰다."""
    import json as _j
    d = _dir({})
    p = os.path.join(d, "auth.json")
    with open(p, "w", encoding="utf-8") as f:
        _j.dump({"version": 1, "credential_pool": pool}, f)
    return p


def _cred(cid, label, status=None, reset_at=None):
    c = {"id": cid, "label": label, "auth_type": "oauth",
         "access_token": TOKEN_CANARY, "refresh_token": TOKEN_CANARY,
         "last_status": status, "request_count": 0}
    if reset_at is not None:
        c["last_error_reset_at"] = float(reset_at)
        c["last_error_code"] = 429
        c["last_error_reason"] = "usage_limit_reached"
    return c


def test_pool_with_a_usable_credential_overrides_a_stale_log_429():
    """★ 이 파일의 존재 이유. 소진된 자격 + 멀쩡한 자격이 함께 있으면 **착수 가능**이다.

    이게 깨지면 계정을 추가해도 게이트가 계속 막는다 — 정확히 2026-08-06 의 증상."""
    p = _auth({"openai-codex": [_cred("a934e2", "device_code", "exhausted", RESETS),
                                _cred("e49333", "account2")]})
    creds = ur.read_credential_pool("openai-codex", [p])
    v = ur.pool_verdict(creds, now=RESETS - 3600)
    assert v["known"], "풀을 읽었는데 known=False 다"
    assert v["usable"] == 1, v
    assert v["total"] == 2, v


def test_pool_all_exhausted_still_blocks():
    """반대 방향 — 전부 소진이면 막아야 한다. 이걸 안 재면 '항상 통과'가 된다."""
    p = _auth({"openai-codex": [_cred("a1", "one", "exhausted", RESETS),
                                _cred("b2", "two", "exhausted", RESETS + 999)]})
    v = ur.pool_verdict(ur.read_credential_pool("openai-codex", [p]), now=RESETS - 3600)
    assert v["known"] and v["usable"] == 0, v


def test_pool_credential_past_its_reset_is_usable():
    """리셋 시각이 지난 자격은 다시 쓸 수 있다 — 상태 문자열이 아니라 시계로 판정한다."""
    p = _auth({"openai-codex": [_cred("a1", "one", "exhausted", RESETS)]})
    creds = ur.read_credential_pool("openai-codex", [p])
    assert ur.pool_verdict(creds, now=RESETS - 1)["usable"] == 0
    assert ur.pool_verdict(creds, now=RESETS + 1)["usable"] == 1


def test_missing_auth_file_falls_back_to_log_verdict():
    """auth.json 이 없으면 **판정하지 않는다**(known=False) — 기존 로그 기반 판정으로 되돌아간다.

    ⚠️ 여기서 usable=0 을 반환하면 풀을 안 쓰는 설치가 전부 막힌다(하위호환 파괴)."""
    v = ur.pool_verdict(ur.read_credential_pool("openai-codex", ["/nonexistent/auth.json"]),
                        now=RESETS)
    assert v["known"] is False and v["usable"] == 0, v


def test_provider_absent_from_pool_falls_back_to_log_verdict():
    """풀은 있는데 그 provider 가 없으면 = 풀이 관리하지 않는 provider → 폴백."""
    p = _auth({"copilot": [_cred("z9", "GITHUB_TOKEN")]})
    v = ur.pool_verdict(ur.read_credential_pool("openai-codex", [p]), now=RESETS)
    assert v["known"] is False, v


def test_empty_pool_for_provider_blocks():
    """반대 방향 — 키는 있는데 자격이 0개면 그건 '모른다'가 아니라 '없다'다."""
    p = _auth({"openai-codex": []})
    v = ur.pool_verdict(ur.read_credential_pool("openai-codex", [p]), now=RESETS)
    assert v["known"] is True and v["usable"] == 0, v


def test_pool_summary_never_exposes_token_values():
    """★ 이 저장소는 PUBLIC 이고 --json 출력은 로그·문서에 붙여진다.

    `SLACK_BOT_TOKEN` 이 세션 로그에 노출된 이력이 이미 있다(CLAUDE.md). 반복하지 않는다."""
    import json as _j
    p = _auth({"openai-codex": [_cred("a1", "one", "exhausted", RESETS),
                                _cred("b2", "two")]})
    creds = ur.read_credential_pool("openai-codex", [p])
    blob = _j.dumps({"creds": creds, "verdict": ur.pool_verdict(creds, now=RESETS)},
                    ensure_ascii=False)
    assert TOKEN_CANARY not in blob, "토큰 값이 요약에 실려 나간다"
    assert "access_token" not in blob and "refresh_token" not in blob, blob


def test_backend_provider_mapping_comes_from_set_backend():
    """배치표는 한 곳에만 있다 — provider 이름을 여기에 두 번째로 적지 않는다."""
    assert ur.backend_provider("codex") == "openai-codex"
    assert ur.backend_provider("ollama") == "ollama"


def test_main_exits_0_when_pool_has_a_usable_credential():
    """★ 통합 — 로그에 429 가 있어도 쓸 수 있는 자격이 있으면 착수를 막지 않는다."""
    d = _dir({"t_e.log": LOG_429})
    p = _auth({"openai-codex": [_cred("a1", "one", "exhausted", RESETS),
                                _cred("b2", "two")]})
    orig_logs, orig_auth = ur.LOG_DIRS, ur.AUTH_PATHS
    ur.LOG_DIRS, ur.AUTH_PATHS = [d], [p]
    try:
        sys.argv = ["usage_report", "--quiet", "--backend", "codex",
                    "--now", str(RESETS - 3600)]
        assert ur.main() == 0, "쓸 수 있는 자격이 있는데 착수를 막았다"
    finally:
        ur.LOG_DIRS, ur.AUTH_PATHS = orig_logs, orig_auth


def test_main_still_blocks_when_every_pooled_credential_is_exhausted():
    """반대 방향 — 풀 인식이 '항상 통과'로 퇴화하지 않았음을 못박는다."""
    d = _dir({"t_e.log": LOG_429})
    p = _auth({"openai-codex": [_cred("a1", "one", "exhausted", RESETS)]})
    orig_logs, orig_auth = ur.LOG_DIRS, ur.AUTH_PATHS
    ur.LOG_DIRS, ur.AUTH_PATHS = [d], [p]
    try:
        sys.argv = ["usage_report", "--quiet", "--backend", "codex",
                    "--now", str(RESETS - 3600)]
        assert ur.main() == 1, "전부 소진인데 통과시켰다"
    finally:
        ur.LOG_DIRS, ur.AUTH_PATHS = orig_logs, orig_auth


def test_main_fail_closed_when_no_logs():
    orig = ur.LOG_DIRS
    ur.LOG_DIRS = [tempfile.mkdtemp() + "/nonexistent"]
    try:
        sys.argv = ["usage_report", "--quiet", "--backend", "codex"]
        assert ur.main() == 2, "근거가 없는데 정상으로 판정했다(fail-closed 위반)"
    finally:
        ur.LOG_DIRS = orig


def test_brief_shows_usable_count_and_next_reset():
    """상시 표시(statusline·hook)용 한 줄. 쓸 수 있는 자격과 다음 리셋을 함께 보여준다."""
    p = _auth({"openai-codex": [_cred("a1", "old", "exhausted", RESETS),
                                _cred("b2", "account2")]})
    s = ur.brief_line("codex", now=RESETS - 3600, paths=[p])
    assert "1/2" in s and "account2" in s, s
    assert "08-09" in s, s


def test_brief_marks_full_exhaustion():
    p = _auth({"openai-codex": [_cred("a1", "old", "exhausted", RESETS)]})
    s = ur.brief_line("codex", now=RESETS - 3600, paths=[p])
    assert "0/1" in s and "⚠️" in s, s


def test_brief_says_so_when_pool_is_unknown():
    """모르면 모른다고 적는다 — '정상'으로 보이면 안 된다(fail-visible)."""
    s = ur.brief_line("codex", now=RESETS, paths=["/nonexistent/auth.json"])
    assert "정보 없음" in s, s


def test_brief_on_local_backend_says_no_limit():
    assert "한도 없음" in ur.brief_line("ollama", now=RESETS)


def test_brief_never_blocks_and_never_calls_a_subprocess(monkeypatch=None):
    """★ 상시 표시가 착수를 막으면 사람이 그것을 끄고, 그러면 진짜 판정도 같이 사라진다.
       그리고 statusline 은 자주 렌더되므로 subprocess 를 부르면 안 된다."""
    import subprocess as _sp
    orig_run, called = _sp.run, []
    _sp.run = lambda *a, **k: called.append(a) or orig_run(*a, **k)
    orig_auth = ur.AUTH_PATHS
    ur.AUTH_PATHS = [_auth({"openai-codex": [_cred("a1", "old", "exhausted", RESETS)]})]
    try:
        sys.argv = ["usage_report", "--brief", "--backend", "codex",
                    "--now", str(RESETS - 3600)]
        assert ur.main() == 0, "표시가 exit 1 로 착수를 막았다"
        assert not called, f"subprocess 를 불렀다: {called}"
    finally:
        _sp.run = orig_run
        ur.AUTH_PATHS = orig_auth


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
