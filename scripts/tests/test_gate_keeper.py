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
