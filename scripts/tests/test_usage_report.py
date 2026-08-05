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
    """exit 1 = 소진 중(미션 착수 전 점검이 이 코드로 막는다) · 0 = 정상."""
    d = _dir({"t_e.log": LOG_429})
    orig = ur.LOG_DIRS
    ur.LOG_DIRS = [d]
    try:
        sys.argv = ["usage_report", "--quiet", "--now", str(RESETS - 3600)]
        assert ur.main() == 1, "리셋 전인데 소진으로 판정하지 않았다"
        sys.argv = ["usage_report", "--quiet", "--now", str(RESETS + 3600)]
        assert ur.main() == 0, "리셋 후인데 소진으로 판정했다"
    finally:
        ur.LOG_DIRS = orig


def test_main_fail_closed_when_no_logs():
    orig = ur.LOG_DIRS
    ur.LOG_DIRS = [tempfile.mkdtemp() + "/nonexistent"]
    try:
        sys.argv = ["usage_report", "--quiet"]
        assert ur.main() == 2, "근거가 없는데 정상으로 판정했다(fail-closed 위반)"
    finally:
        ur.LOG_DIRS = orig


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
