#!/usr/bin/env python3
"""
gate_keeper 회귀 테스트
=======================
근본 결함(fail-open on transient None): 검증자 downstream 자식의 상태 조회가
transient 하게 실패(None)하면, 기존 코드는 그 자식을 '종단(done/archived)'과
동일 취급해 actionable 에서 제거 → 검증자를 processed 로 확정 → blocked downstream
을 영구 고아화했다(게이트 조용히 통과 = fail-open). fail-closed 원칙 위반.

classify_children 은 자식을 (actionable, unknown) 으로 분리해 None(조회실패)을
종단과 구분한다. 실행: python3 -m pytest scripts/tests/test_gate_keeper.py
(pytest 없으면) python3 scripts/tests/test_gate_keeper.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import gate_keeper as gk


def test_none_status_child_is_unknown_not_terminal():
    """★ 결함 재현: 조회 실패(None) 자식은 종단이 아니라 unknown 이어야 한다."""
    actionable, unknown = gk.classify_children(["c1"], lambda c: None)
    assert unknown == ["c1"], "None 자식이 unknown 으로 분류되지 않음(fail-open)"
    assert actionable == []


def test_blocked_child_is_actionable():
    actionable, unknown = gk.classify_children(["c1"], lambda c: "blocked")
    assert actionable == ["c1"] and unknown == []


def test_done_and_archived_children_are_terminal():
    actionable, unknown = gk.classify_children(["a", "b"], {"a": "done", "b": "archived"}.get)
    assert actionable == [] and unknown == []


def test_mixed_children():
    st = {"a": "done", "b": "blocked", "c": None, "d": "todo"}
    actionable, unknown = gk.classify_children(["a", "b", "c", "d"], st.get)
    assert actionable == ["b", "d"]
    assert unknown == ["c"]


# ── Sam 승인 게이트 파싱/매칭 ───────────────────────────────────────────────
def test_parse_approval_bare():
    ok, tid = gk.parse_approval("승인")
    assert ok is True and tid is None


def test_parse_approval_with_explicit_id():
    ok, tid = gk.parse_approval("승인 t_2daad491")
    assert ok is True and tid == "t_2daad491"


def test_parse_approval_english():
    ok, tid = gk.parse_approval("approve t_abc123")
    assert ok is True and tid == "t_abc123"


def test_parse_approval_deny_word_is_not_approval():
    # ★ 오탐 방지: 반려/보류가 있으면 승인 아님
    assert gk.parse_approval("반려한다")[0] is False
    assert gk.parse_approval("이건 보류")[0] is False
    assert gk.parse_approval("아직 승인 못함, 보류")[0] is False


def test_parse_approval_non_approval_text():
    assert gk.parse_approval("보고서 잘 봤어요")[0] is False
    assert gk.parse_approval("")[0] is False


def test_resolve_target_explicit_match():
    gates = [{"task_id": "t_1"}, {"task_id": "t_2"}]
    target, _ = gk.resolve_approval_target("t_2", gates)
    assert target == "t_2"


def test_resolve_target_explicit_not_a_gate():
    gates = [{"task_id": "t_1"}]
    target, why = gk.resolve_approval_target("t_9", gates)
    assert target is None and "아님" in why


def test_resolve_target_single_bare():
    target, _ = gk.resolve_approval_target(None, [{"task_id": "t_only"}])
    assert target == "t_only"


def test_resolve_target_ambiguous_bare():
    target, why = gk.resolve_approval_target(None, [{"task_id": "t_1"}, {"task_id": "t_2"}])
    assert target is None and "모호" in why


def test_resolve_target_none_pending():
    target, why = gk.resolve_approval_target(None, [])
    assert target is None and "없음" in why


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
