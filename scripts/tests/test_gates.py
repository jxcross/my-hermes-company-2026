#!/usr/bin/env python3
"""
객관 게이트 회귀 테스트
=======================
`scripts/gates/*.py` 의 판정 로직(순수함수 위주)을 검사한다. gate_keeper 는 이들을
exit code 로만 읽으므로(0 PASS · 1 FAIL · 2 fail-closed), 판정이 조용히 느슨해지면
이중 게이트가 반쪽이 된다.

실행: python3 -m pytest scripts/tests/test_gates.py
     (pytest 없으면) python3 scripts/tests/test_gates.py
"""
import importlib.util
import os
import sys

GATES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "gates")


def _load(name):
    path = os.path.join(GATES, f"{name}.py")
    spec = importlib.util.spec_from_file_location(f"gate_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


prisma_counts = _load("prisma_counts")
prisma_checklist = _load("prisma_checklist")
doc_consistency = _load("doc_consistency")
test_run = _load("test_run")


# ── prisma_counts ────────────────────────────────────────────────────────
def test_counts_parse():
    d = prisma_counts.parse_counts("identified: 412\nduplicates_removed: 88\n")
    assert d == {"identified": 412, "duplicates_removed": 88}


def test_counts_parse_rejects_non_integer():
    try:
        prisma_counts.parse_counts("identified: 사백십이\n")
    except ValueError:
        return
    raise AssertionError("정수 아닌 값을 통과시켰다")


def test_reasons_parse_sums():
    block = '- reason: "non-empirical"  count: 14\n- reason: "language"  count: 8\n'
    assert sum(prisma_counts.parse_reasons(block).values()) == 22


def test_reasons_parse_skips_countless_lines():
    """count 없는 줄은 무시된다 — 합계를 부풀리면 항등식 검사가 무력해진다."""
    block = '- reason: "no count here"\n- reason: "ok"  count: 5\n'
    assert prisma_counts.parse_reasons(block) == {"ok": 5}


def test_bibkey_counting():
    block = "- bibkey: a2020\n- bibkey: b2021\n  note: 무시\n- bibkey: c2022\n"
    assert len(prisma_counts.BIBKEY_RE.findall(block)) == 3


# ── prisma_checklist ─────────────────────────────────────────────────────
def test_checklist_has_27_items():
    assert len(prisma_checklist.PRISMA_2020) == 27
    assert [i[0] for i in prisma_checklist.PRISMA_2020] == list(range(1, 28))


def test_checklist_no_is_not_rescued_by_section_hint():
    """이식 중 발견한 결함의 회귀 방어 — 원본은 절 힌트만 맞아도 PARTIAL 을 줘서
    가장 자주 누락되는 항목(등록·연구비·이해상충)이 통과했다. 근거는 키워드다."""
    item = (24, "Registration and protocol", ("prospero", "registration"), ("method", "방법"))
    # 절 힌트('방법')만 있고 키워드는 없다 → NO 여야 한다
    assert prisma_checklist.check_item(item, prisma_checklist.normalize("## 방법\n검색식을 적었다")) == "NO"


def test_checklist_yes_needs_keyword_and_hint():
    item = (24, "Registration and protocol", ("prospero",), ("method",))
    assert prisma_checklist.check_item(item, "methods ... prospero crd42024") == "YES"
    assert prisma_checklist.check_item(item, "we registered on prospero") == "PARTIAL"  # 힌트 없음


def test_checklist_korean_keywords_match():
    """국문 원고도 판정돼야 한다(이식 시 한국어 키워드 추가)."""
    item = next(i for i in prisma_checklist.PRISMA_2020 if i[0] == 26)  # Competing interests
    assert prisma_checklist.check_item(item, prisma_checklist.normalize("이해 상충 없음")) != "NO"


# ── doc_consistency ──────────────────────────────────────────────────────
def test_ids_normalize_zero_padding():
    """R-1 과 R-01 은 같은 요구사항이다 — 다르게 세면 커버리지가 거짓 미달로 뜬다."""
    assert doc_consistency.ids(doc_consistency.REQ_RE, "R-1 과 R-01 과 R-002") == {"1", "2"}


def test_scenario_ids_extracted():
    assert doc_consistency.ids(doc_consistency.SCN_RE, "S-01 S-02 S-02") == {"1", "2"}


def test_nongoal_terms_from_prd():
    prd = "# PRD\n## 요구사항\n- R-01 로그인\n## 비범위\n- 결제 연동\n- 다국어 지원\n## 다음 절\n- 무시"
    terms = doc_consistency.nongoal_terms(prd)
    assert "결제 연동" in terms and "다국어 지원" in terms and "무시" not in terms


def test_nongoal_terms_absent_section():
    assert doc_consistency.nongoal_terms("# PRD\n- R-01 로그인\n") == []


# ── test_run ─────────────────────────────────────────────────────────────
def test_checkbox_regexes():
    text = "- [x] 완료\n- [ ] 미완\n* [X] 완료2\n- 일반 항목"
    assert len(test_run.CHECKED_RE.findall(text)) == 2
    assert len(test_run.UNCHECKED_RE.findall(text)) == 1


def test_pass_words_cover_common_spellings():
    for w in ("pass", "passed", "ok", "green", "true"):
        assert w in test_run.PASS_WORDS
    assert "fail" not in test_run.PASS_WORDS and "skip" not in test_run.PASS_WORDS


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
