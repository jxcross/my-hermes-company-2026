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


source_balance = _load("source_balance")
recency_check = _load("recency_check")
prisma_counts = _load("prisma_counts")
prisma_checklist = _load("prisma_checklist")
doc_consistency = _load("doc_consistency")
test_run = _load("test_run")
digest_shape = _load("digest_shape")
seen_dedup = _load("seen_dedup")
claim_consistency = _load("claim_consistency")
patent_format = _load("patent_format")
evidence_grade = _load("evidence_grade")
stakeholder_coverage = _load("stakeholder_coverage")
format_consistency = _load("format_consistency")
clause_completeness = _load("clause_completeness")
law_citation = _load("law_citation")
legal_safety = _load("legal_safety")
symbol_truth = _load("symbol_truth")
api_coverage = _load("api_coverage")
doc_links = _load("doc_links")
objective_coverage = _load("objective_coverage")
bloom_distribution = _load("bloom_distribution")
course_consistency = _load("course_consistency")
content_accessibility = _load("content_accessibility")
atomic_commit = _load("atomic_commit")
test_pass_rate = _load("test_pass_rate")
behavior_diff = _load("behavior_diff")
owasp_coverage = _load("owasp_coverage")
cve_remediation = _load("cve_remediation")
finding_completeness = _load("finding_completeness")
secret_redaction = _load("secret_redaction")
eval_set_quality = _load("eval_set_quality")
stat_significance = _load("stat_significance")
repro_determinism = _load("repro_determinism")
run_completeness = _load("run_completeness")
pii_presence = _load("pii_presence")
license_compat = _load("license_compat")
schema_conformance = _load("schema_conformance")
datasheet_completeness = _load("datasheet_completeness")
result_tolerance = _load("result_tolerance")
env_consistency = _load("env_consistency")
install_evidence = _load("install_evidence")
reproduce_doc = _load("reproduce_doc")
bit_exact = _load("bit_exact")
solver_pin = _load("solver_pin")
doe_completeness = _load("doe_completeness")
analysis_integrity = _load("analysis_integrity")

proposal_format = _load("proposal_format")
budget_integrity = _load("budget_integrity")
call_alignment = _load("call_alignment")
proposal_traceability = _load("proposal_traceability")

comment_fidelity = _load("comment_fidelity")
comment_coverage = _load("comment_coverage")
change_consistency = _load("change_consistency")
response_quality = _load("response_quality")

claim_provenance = _load("claim_provenance")
channel_format = _load("channel_format")
outreach_tone = _load("outreach_tone")
release_readiness = _load("release_readiness")

slide_budget = _load("slide_budget")
deck_format = _load("deck_format")
diagram_integrity = _load("diagram_integrity")


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


# ── digest_shape (아키타입 E) ─────────────────────────────────────────────
DIGEST = """# 주간
서문

### [arxiv:1] 첫 논문
요약 본문이 여기에 충분히 길게 들어간다 하나 둘 셋 넷 다섯 여섯 일곱 여덟 아홉 열.
**행동**: cite — 근거

### [scholar:2] 둘째 논문
짧다.
**행동**: 대충 — 잘못된 라벨
"""


def test_digest_splits_items_by_id():
    items = digest_shape.split_items(DIGEST)
    assert [i[0] for i in items] == ["arxiv:1", "scholar:2"]


def test_digest_word_count_excludes_action_line():
    """행동 줄이 요약 분량에 섞이면 짧은 요약이 통과해버린다."""
    _, body = digest_shape.split_items(DIGEST)[1]
    assert digest_shape.word_count(body) == 1          # '짧다.' 만


def test_digest_action_label_captured_even_if_invalid():
    """'행동 줄 없음'과 '라벨이 틀림'을 구분해야 집필자에게 정확히 알려줄 수 있다."""
    _, body = digest_shape.split_items(DIGEST)[1]
    m = digest_shape.ACTION_RE.search(body)
    assert m and m.group(1) == "대충"


def test_digest_no_items_when_format_ignored():
    assert digest_shape.split_items("그냥 산문입니다.") == []


def test_digest_default_actions():
    assert set(digest_shape.DEFAULT_ACTIONS) == {"cite", "rebut", "monitor", "skip", "handoff"}


# ── seen_dedup (아키타입 E) ───────────────────────────────────────────────
def test_id_format_requires_source_prefix():
    """id 는 `<source>:<key>` 여야 seen 추적이 소스 간 충돌 없이 된다."""
    assert seen_dedup.ID_RE.match("arxiv:2505.01234")
    assert seen_dedup.ID_RE.match("openreview:AbC-1_2")
    assert not seen_dedup.ID_RE.match("no-colon-id")
    assert not seen_dedup.ID_RE.match(":missing-source")


def test_scope_monitor_id_read_from_frontmatter():
    import tempfile, os as _os
    d = tempfile.mkdtemp()
    with open(_os.path.join(d, "SCOPE.md"), "w", encoding="utf-8") as f:
        f.write("---\nmonitor_id: weekly-llm\n---\n# 범위\n")
    assert seen_dedup.scope_monitor_id(d) == "weekly-llm"


def test_scope_monitor_id_absent_returns_none():
    import tempfile
    assert seen_dedup.scope_monitor_id(tempfile.mkdtemp()) is None


# ── monitor_state (지속 상태) ─────────────────────────────────────────────
def _monitor_state():
    path = os.path.join(GATES, "..", "tools", "monitor_state.py")
    spec = importlib.util.spec_from_file_location("monitor_state", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_monitor_state_roundtrip_is_idempotent():
    import tempfile
    ms = _monitor_state()
    root = tempfile.mkdtemp()
    os.environ["HERMES_MONITORS_ROOT"] = root
    try:
        assert ms.load_seen("w") == {}                       # 첫 회차
        assert ms.append_seen("w", ["arxiv:1", "arxiv:2"], "2026-08-04") == 2
        assert ms.append_seen("w", ["arxiv:1", "arxiv:3"], "2026-08-11") == 1   # 멱등
        seen = ms.load_seen("w")
        assert set(seen) == {"arxiv:1", "arxiv:2", "arxiv:3"}
        assert seen["arxiv:1"] == "2026-08-04"               # 최초 관측일 보존
    finally:
        os.environ.pop("HERMES_MONITORS_ROOT", None)


def test_monitor_state_root_is_overridable():
    """테스트가 repo 의 monitors/ 를 오염시키지 않아야 한다."""
    ms = _monitor_state()
    os.environ["HERMES_MONITORS_ROOT"] = "/tmp/does-not-exist-xyz"
    try:
        assert ms.seen_path("w").startswith("/tmp/does-not-exist-xyz")
    finally:
        os.environ.pop("HERMES_MONITORS_ROOT", None)


# ── claim_consistency (아키타입 F) ────────────────────────────────────────
SPEC = """# 명세서
## 【청구범위】
### 청구항 1
입력을 분석하는 프로파일링 모듈과, 결과를 저장하는 캐시 부를 포함하는 시스템.
### 청구항 2
제1항에 있어서, 상기 프로파일링 모듈은 실시간인 것을 특징으로 하는 시스템.
## 【과제의 해결 수단】
프로파일링 모듈이 분석하고 캐시 부에 저장한다.
## 【발명을 실시하기 위한 구체적인 내용】
캐시 부는 LRU 를 쓴다.
"""


def test_claims_section_not_truncated_by_h3():
    """이식 결함 회귀: 원본의 `(?=^##|\\Z)` 는 `### 청구항 1` 에도 걸려 청구범위 절이
    즉시 잘렸다(청구항을 하나도 못 읽었다)."""
    cs = claim_consistency.claims_section(SPEC)
    assert "청구항 1" in cs and "청구항 2" in cs, cs


def test_claim_blocks_numbered():
    blocks = claim_consistency.claim_blocks(claim_consistency.claims_section(SPEC))
    assert [n for n, _ in blocks] == [1, 2]


def test_elements_extract_korean_with_josa():
    """이식 결함 회귀: 조사가 붙은 '모듈과'·'부를' 을 원본은 놓치고 대신 동사구
    '포함하는 시스템' 을 요소로 잡아, 게이트가 아무것도 측정하지 못했다."""
    _, b1 = claim_consistency.claim_blocks(claim_consistency.claims_section(SPEC))[0]
    els = claim_consistency.elements_of(b1)
    assert ("프로파일링", "모듈") in els, els
    assert ("캐시", "부") in els, els


def test_elements_reject_verbal_phrases():
    els = claim_consistency.elements_of("데이터를 포함하는 시스템과 처리하는 장치")
    mods = [m for m, _ in els]
    assert "포함하는" not in mods and "처리하는" not in mods, els


def test_spec_body_joins_two_sections():
    body = claim_consistency.spec_body(SPEC)
    assert "프로파일링 모듈이 분석" in body and "LRU" in body


def test_dependent_ref_regex():
    assert claim_consistency.DEPENDENT_REF_RE.findall("제1항에 있어서, 제 12 항") == ["1", "12"]


# ── patent_format (아키타입 F) ────────────────────────────────────────────
def test_required_sections_cover_four_jurisdictions():
    assert set(patent_format.REQUIRED_SECTIONS) == {"kipo", "uspto", "pct", "epo"}


def test_jurisdiction_inferred_from_filename():
    known = list(patent_format.REQUIRED_SECTIONS)
    assert patent_format.jurisdiction_of("/x/applications/uspto.md", known) == "uspto"
    assert patent_format.jurisdiction_of("/x/applications/06-kipo.md", known) == "kipo"
    assert patent_format.jurisdiction_of("/x/applications/notes.md", known) is None


def test_disclaimer_terms_include_korean_default():
    """고지는 원본에 없던 것을 우리가 게이트로 승격한 항목 — 기본값이 비면 무의미해진다."""
    assert any("변리사" in t for t in patent_format.DEFAULT_DISCLAIMER_TERMS)


def test_scope_jurisdictions_from_frontmatter():
    import tempfile, os as _os
    d = tempfile.mkdtemp()
    with open(_os.path.join(d, "SCOPE.md"), "w", encoding="utf-8") as f:
        f.write("---\njurisdictions: [kipo, USPTO]\n---\n")
    assert patent_format.scope_jurisdictions(d) == ["kipo", "uspto"]


# ── evidence_grade (아키타입 G · 원본 GATE 1) ─────────────────────────────
def test_evidence_ref_survives_korean_particles():
    """이식 중 발견한 결함의 회귀 방어 — 원본 `\\b(e\\d+)\\b` 는 조사가 붙은 `e1을`·`e2에서`
    에서 무너져 **인용을 한 건도 못 읽었다**(caveat·환각 검사가 통째로 무력화된다)."""
    t = "e1을 근거로 한다. e2에서 확인됐다. [e3]도 보라."
    assert evidence_grade.EVIDENCE_REF_RE.findall(t) == ["e1", "e2", "e3"]


def test_evidence_ref_does_not_match_inside_words():
    """`phase1`·`stage12` 를 근거 인용으로 오인하면 환각 검사가 거짓 경보를 낸다."""
    assert evidence_grade.EVIDENCE_REF_RE.findall("phase1 stage12 releve4") == []


def test_grade_aliases_accept_korean():
    assert evidence_grade.normalize_grade("높음") == "high"
    assert evidence_grade.normalize_grade("Very-Low") == "very_low"
    assert evidence_grade.normalize_grade("매우낮음") == "very_low"


def test_parse_grades_reads_evidence_block(tmp=None):
    import tempfile, os as _os
    d = tempfile.mkdtemp()
    p = _os.path.join(d, "evidence.md")
    with open(p, "w", encoding="utf-8") as f:
        f.write("# x\n\n```evidence\n- id: e1\n  grade: high\n- id: e2\n  grade: 낮음\n```\n")
    assert evidence_grade.parse_grades(p) == {"e1": "high", "e2": "low"}


def test_recommendation_scope_stops_at_next_heading():
    """권고 절 밖의 강근거 인용이 권고를 대신 통과시켜선 안 된다."""
    text = "## 배경\ne1 을 소개한다\n\n## 정책 권고\nO2 를 권고한다 e4\n\n## 부록\ne1 재인용\n"
    scope = evidence_grade.recommendation_scope(text, ["권고"])
    assert "e4" in scope and "e1" not in scope


def test_caveat_scope_does_not_reach_other_paragraph():
    """다른 문단 어딘가의 '잠정' 이 저근거 인용을 면제해 주면 게이트가 무의미해진다."""
    text = "이것은 잠정 판단이다.\n\ne4 에 따라 즉시 도입한다.\n"
    pos = text.index("e4")
    scope = evidence_grade.caveat_scope(text, pos, pos + 2)
    assert not evidence_grade.has_caveat(scope, evidence_grade.DEFAULT_CAVEAT_TERMS)


# ── stakeholder_coverage (아키타입 G · 원본 GATE 3) ────────────────────────
def test_stakeholder_id_ref_survives_korean_particles():
    """원본 `\\b{sid}\\b` 는 `s1의` 에서 실패 — id 로만 지칭된 이해관계자가 미커버로 오판된다."""
    assert stakeholder_coverage.id_ref_re("s1").search("s1의 이해는 비용이다")
    assert not stakeholder_coverage.id_ref_re("s1").search("us12 는 무관하다")


def test_parse_stakeholders_collects_fields():
    import tempfile, os as _os
    d = tempfile.mkdtemp()
    p = _os.path.join(d, "context.md")
    with open(p, "w", encoding="utf-8") as f:
        f.write("```stakeholders\n- id: s1\n  name: 노동조합\n  interest: 안전\n"
                "  position: 즉시 시행\n- id: s2\n  name: 협회\n```\n")
    got = stakeholder_coverage.parse_stakeholders(p)
    assert [s["id"] for s in got] == ["s1", "s2"]
    assert got[0]["position"] == "즉시 시행"
    assert "position" not in got[1]      # 공란은 게이트가 FAIL 로 잡는다


def test_covered_in_matches_by_name_when_id_absent():
    s = {"id": "s9", "name": "노동조합"}
    assert stakeholder_coverage.covered_in(s, "노동조합의 입장을 반영했다", 2)
    assert not stakeholder_coverage.covered_in(s, "관계 부처와 협의했다", 2)


# ── format_consistency (아키타입 G) ────────────────────────────────────────
def test_option_token_survives_korean_particles():
    """원본 `\\bO\\d+\\b` 는 `O2를` 에서 무너져 **권고 일치 검사가 항상 FAIL** 이 된다."""
    rx = format_consistency.re.compile(format_consistency.OPTION_RE_TMPL.format("O2"))
    assert rx.search("O2를 권고한다")
    assert not rx.search("O21 은 다른 옵션이다")


def test_count_words_strips_frontmatter_and_code():
    text = "---\na: 1\n---\n\n본문 어절 셋\n\n```\n코드 는 세지 않는다\n```\n"
    assert format_consistency.count_words(text) == 3


def test_default_word_ranges_are_korean_calibrated():
    """원본은 영문 word 기준(brief 1200~2400 · report 9000~18000)이라 규격에 맞는
    국문 문서를 분량 미달로 반려한다. 국문 어절 기준으로 되돌려 놓은 것의 회귀 방어."""
    assert format_consistency.DEFAULT_WORD_RANGES["brief"][0] < 1200
    assert format_consistency.DEFAULT_WORD_RANGES["report"][0] < 9000
    assert format_consistency.DEFAULT_WORD_RANGES["memo"] == [350, 900]


def test_scope_formats_from_frontmatter():
    import tempfile, os as _os
    d = tempfile.mkdtemp()
    with open(_os.path.join(d, "SCOPE.md"), "w", encoding="utf-8") as f:
        f.write("---\nformats: [brief, MEMO]\n---\n")
    assert format_consistency.scope_formats(d) == ["brief", "memo"]


def test_recommended_option_parsed():
    import tempfile, os as _os
    d = tempfile.mkdtemp()
    p = _os.path.join(d, "options.md")
    with open(p, "w", encoding="utf-8") as f:
        f.write("# 옵션\n\nrecommended_option: O2\n")
    assert format_consistency.recommended_option(p) == "O2"


# ── clause_completeness (아키타입 H · 원본 HARD GATE) ──────────────────────
def test_clause_pattern_survives_fstring_quantifier():
    """이식 중 발견한 **치명 결함**의 회귀 방어 — 원본은 raw f-string 안에 `{1,3}` 을 써서
    수량자가 보간으로 평가됐다(정규식이 `^#(1, 3)\\s+…` 가 됨). 어떤 제목에도 맞지 않아
    하드게이트가 **항상 FAIL** 했다(완벽한 계약서도 finalize 불가)."""
    pats = clause_completeness.clause_patterns("해지")
    assert not any("(1, 3)" in p.pattern for p in pats), [p.pattern for p in pats]
    assert any(p.search("## 제9조 (해지)\n내용\n") for p in pats)
    assert any(p.search("### 해지\n내용\n") for p in pats)


def test_clause_requires_heading_not_passing_mention():
    """본문에 단어가 스쳐 나오는 것은 조항이 아니다 — 그러면 게이트가 아무것도 막지 않는다."""
    body = "갑과 을은 비밀유지 의무를 진다.\n"
    assert clause_present_none(body, "비밀유지")


def clause_present_none(body, label):
    return clause_completeness.clause_present(label, {}, body) is None


def test_clause_alias_is_accepted():
    """'대가'를 '용역대금'으로 쓰는 것은 실무 표준이다 — 이름이 다르다고 누락이 아니다."""
    aliases = {"대가": ["용역대금", "보수"]}
    got = clause_completeness.clause_present("대가", aliases, "## 제5조 (용역대금)\n금액\n")
    assert got == "용역대금"


def test_clause_bold_line_counts_as_heading():
    assert clause_completeness.clause_present("해지", {}, "**제9조 (해지)**\n내용\n") == "해지"


def test_scope_field_reads_doc_types():
    import tempfile, os as _os
    d = tempfile.mkdtemp()
    with open(_os.path.join(d, "SCOPE.md"), "w", encoding="utf-8") as f:
        f.write("---\ndoc_types: [contract, terms]\ndomain: it_sw\n---\n")
    assert clause_completeness.scope_field(d, "doc_types") == ["contract", "terms"]
    assert clause_completeness.scope_field(d, "domain") == "it_sw"


# ── law_citation (아키타입 H) ──────────────────────────────────────────────
WL = set(law_citation.DEFAULT_WHITELIST)


def test_law_name_does_not_swallow_preceding_sentence():
    """원본 회귀 방어 — 탐욕적 문자 클래스(`[가-힣…\\s]+`)가 앞 문장을 삼켜 법령명이
    '본 계약은 민법' 으로 잡혔다. 화이트리스트가 항상 빗나가 정상 문서도 FAIL 했다."""
    t = "본 계약은 민법 제105조에 따른다"
    assert law_citation.law_name_before(t, t.index("제105조"), WL) == "민법"


def test_law_name_prefers_bracketed_form():
    t = "「개인정보 보호법」 제29조"
    assert law_citation.law_name_before(t, t.index("제29조"), WL) == "개인정보 보호법"


def test_law_name_longest_whitelist_suffix():
    """긴 공식 명칭을 통째로 잡아야 한다 — 마지막 어절만 취하면 '법률' 이 된다."""
    t = "사용자는 정보통신망 이용촉진 및 정보보호 등에 관한 법률 제48조를 준수한다"
    assert (law_citation.law_name_before(t, t.index("제48조"), WL)
            == "정보통신망 이용촉진 및 정보보호 등에 관한 법률")


def test_internal_article_reference_is_not_a_law_citation():
    """계약서의 '제5조에 따라' 는 자기 조항 참조다 — 법령 인용으로 세면 오탐이 쏟아진다."""
    t = "본 계약 제5조에 따라 해지할 수 있다"
    assert law_citation.law_name_before(t, t.index("제5조"), WL) is None


def test_article_regex_captures_missing_je():
    """'민법 105조'(제 누락)를 형식 오류로 잡으려면 `제` 유무를 따로 봐야 한다."""
    m = law_citation.ARTICLE_RE.search("민법 105조")
    assert m and m.group("je") is None and m.group("num") == "105"


# ── legal_safety (아키타입 H · 신설) ────────────────────────────────────────
def test_placeholder_is_not_treated_as_pii():
    """초안은 플레이스홀더로 쓴다 — `000-00-00000` 을 개인정보로 막으면 쓸 수가 없다."""
    assert legal_safety.is_placeholder("000-00-00000")
    assert legal_safety.is_placeholder("111111-1111111")
    assert not legal_safety.is_placeholder("214-86-53075")


def test_resident_registration_number_is_blocked():
    """저장소가 PUBLIC 이고 Deliver 가 push 한다 — 주민등록번호는 되돌릴 수 없는 사고다."""
    hits = legal_safety.scan_pii("대표자 850101-1234567", ["주민등록번호"], True)
    assert [k for k, _ in hits] == ["주민등록번호"]


def test_business_number_blocked_but_placeholder_passes():
    kinds = ["사업자등록번호"]
    assert legal_safety.scan_pii("사업자등록번호: 214-86-53075", kinds, True)
    assert not legal_safety.scan_pii("사업자등록번호: 000-00-00000", kinds, True)


def test_disclaimer_terms_include_lawyer_review():
    """고지는 우리가 게이트로 승격한 항목 — 기본값이 비면 무의미해진다."""
    assert any("변호사" in t for t in legal_safety.DEFAULT_DISCLAIMER_TERMS)


# ── symbol_truth (아키타입 I · 신설) ────────────────────────────────────────
def _pysrc(code):
    import tempfile, os as _os
    d = tempfile.mkdtemp()
    with open(_os.path.join(d, "m.py"), "w", encoding="utf-8") as f:
        f.write(code)
    return d


def test_extract_python_skips_private_symbols():
    """`_` 접두 심볼은 공개 API 가 아니다 — 분모에 넣으면 커버리지가 왜곡된다."""
    syms, _mods = symbol_truth.extract_python(_pysrc(
        "def pub(a):\n    pass\n\ndef _priv(b):\n    pass\n"), [])
    assert "pub" in syms and "_priv" not in syms


def test_extract_python_collects_methods_qualified():
    syms, _mods = symbol_truth.extract_python(_pysrc(
        "class E:\n    def run(self, task):\n        pass\n    def _x(self):\n        pass\n"), [])
    assert syms["E.run"] == ["task"]          # self 는 파라미터가 아니다
    assert "E._x" not in syms


def test_sig_params_ignores_defaults_and_hints():
    assert symbol_truth.sig_params("f(a, b: int = 1, *args, **kw)") == ["a", "b", "args", "kw"]
    assert symbol_truth.sig_params("f()") == []
    assert symbol_truth.sig_params("설명만 있고 괄호 없음") is None


def test_sig_params_handles_nested_commas():
    """`Dict[str, int]` 안의 쉼표로 파라미터를 쪼개면 대조가 무의미해진다."""
    assert symbol_truth.sig_params("f(a: Dict[str, int], b=(1, 2))") == ["a", "b"]


def test_parse_declared_binds_signature_to_its_entry():
    import tempfile, os as _os
    d = tempfile.mkdtemp()
    p2 = _os.path.join(d, "symbols.md")
    with open(p2, "w", encoding="utf-8") as f:
        f.write("```functions\n- name: a\n  signature: a(x)\n- name: b\n  signature: b(y)\n```\n")
    got = symbol_truth.parse_declared(p2)
    assert [(g["name"], g["signature"]) for g in got] == [("a", "a(x)"), ("b", "b(y)")]


# ── api_coverage (아키타입 I) ──────────────────────────────────────────────
def test_substring_brush_is_not_documentation():
    """이식 중 발견한 결함의 회귀 방어 — 원본은 `keyword in api_text` 부분 문자열 검사라
    'running'·'get_configuration' 만 있어도 run·get_config 가 문서화된 것으로 셌다.
    실측: 아무것도 문서화하지 않은 문서에 3/3 = 100% PASS."""
    text = ("# API\n\n## 개요\n현재 running 상태에서 get_configuration 을 "
            "parse_tree_node 로 넘긴다. 자세한 것은 추후 작성 예정이다.\n")
    entries = api_coverage.documented_entries(text, 40)
    assert "run" not in entries and "get_config" not in entries and "parse_tree" not in entries


def test_documented_entry_requires_body():
    """제목만 있고 본문이 없으면 문서가 아니다(목차 나열·TODO 를 커버리지로 세지 않는다)."""
    assert api_coverage.documented_entries("### parse_tree(node)\nTODO\n", 40) == {}
    got = api_coverage.documented_entries(
        "### parse_tree(node)\n" + "설명이 충분히 길게 이어진다. " * 4 + "\n", 40)
    assert "parse_tree" in got


def test_documented_entry_name_strips_signature():
    got = api_coverage.documented_entries(
        "### `Engine.run(task)`\n" + "가" * 60 + "\n", 40)
    assert "Engine.run" in got and "run" in got     # 마지막 조각도 인정


# ── doc_links (아키타입 I) ─────────────────────────────────────────────────
def test_slug_follows_github_rules():
    """원본은 구두점을 하이픈으로 **바꿔** `parse(x)` → `parse-x-` 로 만들어 정상 앵커를
    깨진 것으로 판정했다. GitHub 은 구두점을 **삭제**한다."""
    assert doc_links.slug("parse_tree(node, depth=0)") == "parse_treenode-depth0"
    assert doc_links.slug("## 구조 개요") == "-구조-개요".lstrip("-")


def test_link_regex_ignores_images():
    """`![alt](x.png)` 는 문서 간 링크가 아니다 — 원본은 이것도 깨진 링크로 셌다."""
    found = [m.group(2) for m in doc_links.LINK_RE.finditer("![그림](a.png) 와 [문서](b.md)")]
    assert found == ["b.md"]



# ── objective_coverage (아키타입 J · 원본 GATE 1) ──────────────────────────
def test_lo_ref_survives_korean_particles():
    """원본 `\\blo\\d+\\b` 는 `lo3을`·`lo4에서` 에서 무너진다(실측 `[]`)."""
    assert objective_coverage.LO_RE.findall("lo3을 다룬다. lo4에서 확장") == ["lo3", "lo4"]


def test_only_declared_los_field_counts():
    """스치는 언급은 배치가 아니다 — 원본은 블록 안 아무 곳의 loN 이든 커버리지로 셌다."""
    blk = "- week: 1\n  title: 개요\n  # lo5 는 다음 학기\n  los: [lo1]\n"
    entries = objective_coverage.entries_with_los(blk)
    assert entries[0][1] == {"lo1"}          # 주석의 lo5 는 제외


def test_entries_split_per_item():
    blk = "- week: 1\n  los: [lo1]\n- week: 2\n  los: [lo2, lo3]\n"
    got = objective_coverage.entries_with_los(blk)
    assert [s for _l, s in got] == [{"lo1"}, {"lo2", "lo3"}]


def test_defined_los_from_objectives_block():
    text = "```objectives\n- id: lo1\n  bloom: apply\n- id: lo2\n  bloom: create\n```\n"
    assert objective_coverage.defined_los(text) == ["lo1", "lo2"]


# ── bloom_distribution (아키타입 J · 원본 GATE 2) ──────────────────────────
def test_bloom_korean_aliases():
    """`bloom: 평가` 를 못 읽으면 그 LO 가 분모에서 조용히 빠져 분포가 왜곡된다."""
    assert bloom_distribution.normalize("평가") == "evaluate"
    assert bloom_distribution.normalize("창안") == "create"
    assert bloom_distribution.normalize("Apply") == "apply"
    assert bloom_distribution.normalize("없는단계") is None


def test_bloom_parse_marks_undeclared():
    text = "```objectives\n- id: lo1\n  bloom: apply\n- id: lo2\n  statement: x\n```\n"
    got = bloom_distribution.parse_objectives(text)
    assert got == [("lo1", "apply"), ("lo2", None)]


def test_bloom_default_policy_separates_warn_and_fail():
    """원본은 WARN 도 exit 1 이었다 — 하위단계 초과는 WARN, 고차단계 부족은 FAIL 이다."""
    ug = bloom_distribution.DEFAULT_LEVEL_POLICY["undergraduate"]
    assert ug["lower_is_fail"] is False and ug["higher_min"] == 0.1
    assert bloom_distribution.DEFAULT_LEVEL_POLICY["graduate"]["higher_min"] == 0.2


# ── course_consistency (아키타입 J) ────────────────────────────────────────
def test_week_regex_reads_korean_and_field_forms():
    """원본은 영문 산문형만 잡아 국문 `3주차` 와 필드형 `week: 3` 을 통째로 놓쳤다
    (실측 `[]` → canonical_weeks 가 비어 주차 커버리지 검사가 공회전)."""
    assert course_consistency.weeks("3주차 개요") == {3}
    assert course_consistency.weeks("제5주 실습") == {5}
    assert course_consistency.weeks("- week: 7") == {7}
    assert course_consistency.weeks("Week 2 overview") == {2}


def test_weight_field_parsed_for_sum():
    """원본은 이 합계 검사의 본문이 문자 그대로 `pass` 였다(죽은 코드)."""
    blk = "- id: a1\n  weight: 30\n- id: a2\n  weight: 70\n"
    assert sum(float(x) for x in course_consistency.WEIGHT_FIELD_RE.findall(blk)) == 100.0


def test_course_lo_regex_korean_safe():
    assert course_consistency.los("lo2를 다룬다") == {"lo2"}


# ── content_accessibility (아키타입 J · 원본 GATE 3) ───────────────────────
def test_bullets_are_separate_sentences():
    """원본은 마침표 없는 불릿 블록을 문장 1개로 뭉쳐 슬라이드를 부당하게 위반으로 몰았다."""
    md = "# 제목\n\n- 손실함수의 정의\n- 오차의 종류\n- 회귀와 분류의 차이\n"
    sents = content_accessibility.sentences(md)
    assert len(sents) == 3 and max(len(s.split()) for s in sents) <= 4


def test_image_without_alt_is_flagged():
    got = content_accessibility.images("![](a.png)")
    assert got and got[0][1] is False
    got2 = content_accessibility.images("![학습 곡선 그래프](a.png)")
    assert got2 and got2[0][1] is True


def test_korean_image_hint_alt_recognized():
    text = "> 이미지: 학습 곡선 (대체 텍스트: 에폭별 손실 변화)"
    got = content_accessibility.images(text)
    assert got and got[0][1] is True


def test_headings_are_not_counted_as_sentences():
    assert content_accessibility.sentences("## 학습목표 복습\n") == []



# ── atomic_commit (아키타입 K · 원본 GATE 3) ───────────────────────────────
def test_missing_commit_message_is_failed_not_skipped():
    """원본 `if msg and not RE.match(msg)` — 메시지가 **비어 있으면 검사를 건너뛴다**.
    안 적으면 통과하는 형식 검사는 형식 검사가 아니다."""
    steps = [{"id": "s1", "files": "[a.py]", "rollback": "revert"}]     # commit_message 없음
    assert atomic_commit.check_plan(steps, "migrate", True, False) is True


def test_file_overlap_between_steps_is_failed():
    """겹치면 개별 revert 가 불가능해져 원자성이 깨진다(원본에 없던 검사)."""
    steps = [
        {"id": "s1", "files": "[a.py]", "rollback": "r", "commit_message": "migrate(x): 하나"},
        {"id": "s2", "files": "[a.py]", "rollback": "r", "commit_message": "migrate(x): 둘"},
    ]
    assert atomic_commit.check_plan(steps, "migrate", True, False) is True
    assert atomic_commit.check_plan(steps, "migrate", True, True) is False   # 허용 정책이면 통과


def test_missing_rollback_is_failed():
    steps = [{"id": "s1", "files": "[a.py]", "commit_message": "migrate(x): 하나"}]
    assert atomic_commit.check_plan(steps, "migrate", True, False) is True
    assert atomic_commit.check_plan(steps, "migrate", False, False) is False


def test_as_list_parses_inline_yaml_list():
    assert atomic_commit.as_list("[a.py, b/c.py]") == ["a.py", "b/c.py"]
    assert atomic_commit.as_list("") == []


# ── test_pass_rate (아키타입 K · 원본 GATE 1) ──────────────────────────────
def test_field_returns_none_when_absent():
    """원본 `parse_int_field` 는 없으면 0 을 준다 — 형식 오류가 '0/0 = 0%' 라는
    그럴듯한 판정으로 둔갑한다. 우리는 None 으로 구분해 fail-closed 한다."""
    assert test_pass_rate.field("n_passed: 19\n", "n_passed") == 19
    assert test_pass_rate.field("n_passed: 19\n", "n_tests_total") is None


def test_field_requires_whole_line_integer():
    """`n_passed_after: 19건` 같은 값은 숫자로 받지 않는다(조용한 오독 방지)."""
    assert test_pass_rate.field("n_passed: 열아홉\n", "n_passed") is None


# ── behavior_diff (아키타입 K · 원본 GATE 2) ───────────────────────────────
def test_accept_only_exact_yes():
    """원본 `"yes" in acceptable` — `not yes` 도 `yes, 확인 안 함` 도 통과했다."""
    assert "yes" in behavior_diff.ACCEPT_OK and "true" in behavior_diff.ACCEPT_OK
    assert "not yes" not in behavior_diff.ACCEPT_OK


def test_parse_items_binds_fields_to_entry():
    text = ("```diffs\n- entry: f1\n  acceptable: yes\n  intentional_id: ic1\n"
            "- entry: f2\n  acceptable: no\n```\n")
    got = behavior_diff.parse_items(text, "diffs", "entry")
    assert got[0]["intentional_id"] == "ic1" and got[1]["acceptable"] == "no"
    assert "intentional_id" not in got[1]


def test_fingerprint_block_parsed_from_baseline():
    text = "```fingerprint\n- case: f1\n  input: x\n- case: f2\n  input: y\n```\n"
    assert [c["case"] for c in behavior_diff.parse_items(text, "fingerprint", "case")] == ["f1", "f2"]



# ── owasp_coverage (아키타입 L · 원본 GATE 2) ──────────────────────────────
def test_owasp_requires_structured_entry_not_bare_mention():
    """원본은 `re.search(r"\\bA01_?")` — 문서 어딘가에 글자만 있으면 covered 로 셌다.
    실측: 'A01 … A10 은 앞으로 점검할 예정이다' 한 줄에 **커버리지 10/10 PASS**."""
    text = "A01 A02 A03 A04 A05 A06 A07 A08 A09 A10 은 앞으로 점검할 예정이다.\n"
    assert owasp_coverage.parse_entries(text) == {}      # 구조화 항목이 없으면 0건


def test_owasp_entry_fields_bound():
    text = ("```owasp\n- id: A01\n  status: audited\n  findings: 2\n  evidence: 근거\n"
            "- id: A02\n  status: not_applicable\n  evidence: 해당 없음 사유\n```\n")
    got = owasp_coverage.parse_entries(text)
    assert got["A01"]["findings"] == "2" and got["A02"]["status"] == "not_applicable"


def test_owasp_ids_normalized_uppercase():
    got = owasp_coverage.parse_entries("```owasp\n- id: a03\n  status: audited\n```\n")
    assert "A03" in got


# ── cve_remediation (아키타입 L · 원본 GATE 3) ─────────────────────────────
def test_cve_scan_evidence_fields():
    """원본은 스캔을 몇 개 대조했는지 묻지 않아 'CVE 0건'을 그대로 받았다."""
    text = "scanned_manifests: 2\nscanned_packages: 137\n"
    assert cve_remediation.int_field(text, "scanned_manifests") == 2
    assert cve_remediation.int_field(text, "scanned_packages") == 137
    assert cve_remediation.int_field(text, "scanned_images") is None


def test_cve_items_keep_severity_and_remediation():
    blk = ("- cve_id: CVE-1\n  severity: high\n  remediation: 올린다\n"
           "- cve_id: CVE-2\n  severity: low\n")
    got = cve_remediation.parse_cves(blk)
    assert got[0]["severity"] == "high" and got[0]["remediation"] == "올린다"
    assert "remediation" not in got[1]


# ── finding_completeness (아키타입 L · 원본 GATE 1을 뒤집은 것) ─────────────
def test_findings_parsed_with_all_fields():
    blk = ("- id: f1\n  severity: high\n  location: a.py:1\n  evidence: 근거\n"
           "  impact: 영향\n  remediation: 조치\n")
    got = finding_completeness.parse_findings(blk)
    assert got[0]["location"] == "a.py:1" and got[0]["remediation"] == "조치"


def test_declared_count_field_is_none_when_absent():
    """원본 `parse_int` 는 없으면 0 을 줘서 **보고서가 깨져도 PASS**(fail-open)였다."""
    assert finding_completeness.int_field("n_high: 2\n", "n_high") == 2
    assert finding_completeness.int_field("n_high: 2\n", "n_critical") is None


def test_default_caps_are_unlimited():
    """감사 게이트가 '취약점 0건'을 요구하면 **발견할수록 보고서가 막힌다**(§5).
    기본값은 무제한이어야 한다 — 건수 판단은 사람의 몫."""
    import json as _json, tempfile, os as _os
    d = tempfile.mkdtemp()
    p2 = _os.path.join(d, "pipeline.json")
    with open(p2, "w", encoding="utf-8") as f:
        _json.dump({"policy": {"finding_policy": {}}}, f)
    pol = finding_completeness.load_policy(p2)
    assert pol.get("max_critical") is None and pol.get("max_high") is None


# ── secret_redaction (아키타입 L · 신설) ────────────────────────────────────
def test_masked_secret_is_allowed():
    """마스킹 표기를 막으면 발견을 보고할 수 없다 — 값만 막아야 한다."""
    assert secret_redaction.is_redacted("AKIA****")
    assert secret_redaction.is_redacted("<redacted>")
    assert not secret_redaction.is_redacted("AKIAIOSFODNN7EXAMPLE")


def test_real_aws_key_is_blocked():
    hits = secret_redaction.scan("키 AKIAIOSFODNN7EXAMPLE 노출", ["AWS 액세스키"])
    assert [k for k, _ in hits] == ["AWS 액세스키"]


def test_private_key_block_is_blocked():
    hits = secret_redaction.scan("-----BEGIN RSA PRIVATE KEY-----", ["개인키"])
    assert hits


def test_private_dir_excluded_from_scan():
    """`_private/` 는 gitignore 대상이라 커밋되지 않는다 — 검사 대상이 아니다."""
    import tempfile, os as _os
    d = tempfile.mkdtemp()
    _os.makedirs(_os.path.join(d, "_private"))
    open(_os.path.join(d, "a.md"), "w").write("x")
    open(_os.path.join(d, "_private", "b.md"), "w").write("y")
    got = [_os.path.basename(f) for f in secret_redaction.files_of(d)]
    assert got == ["a.md"]


def test_disclaimer_terms_mention_not_formal_audit():
    assert any("정식 보안 감사" in t for t in secret_redaction.DEFAULT_DISCLAIMER_TERMS)


def test_scan_extensions_default_stays_md_only():
    """아키타입 M 이 확장자를 정책으로 뺐다 — **기본값은 L 의 동작 그대로**여야 한다."""
    import tempfile, os as _os
    d = tempfile.mkdtemp()
    open(_os.path.join(d, "a.md"), "w").write("x")
    open(_os.path.join(d, "b.py"), "w").write("y")
    assert [_os.path.basename(f) for f in secret_redaction.files_of(d)] == ["a.md"]
    got = sorted(_os.path.basename(f) for f in secret_redaction.files_of(d, [".md", ".py"]))
    assert got == ["a.md", "b.py"]


# ── eval_set_quality (아키타입 M · 신설 — 원본엔 스크립트가 없다) ──────────
def test_difficulty_aliases_accept_korean():
    """라벨이 한국어라고 분포 검사가 무력해지면 안 된다(§5 한국어 함정)."""
    assert eval_set_quality.norm_difficulty("쉬움") == "easy"
    assert eval_set_quality.norm_difficulty("어려움") == "hard"
    assert eval_set_quality.norm_difficulty("MEDIUM") == "medium"
    assert eval_set_quality.norm_difficulty("몰라") is None


def test_question_normalization_catches_reworded_duplicate():
    a = eval_set_quality.norm_question("설치는 어떻게 하나요?")
    b = eval_set_quality.norm_question("설치는  어떻게 하나요 ?")
    assert a == b


def test_gold_context_accepts_str_and_list():
    assert eval_set_quality.gold_contexts({"gold_context": "c1"}) == ["c1"]
    assert eval_set_quality.gold_contexts({"gold_context": ["c1", "c2"]}) == ["c1", "c2"]
    assert eval_set_quality.gold_contexts({}) == []


# ── stat_significance (원본 결함 3건) ───────────────────────────────────────
def test_zero_variance_effect_size_is_not_infinite():
    """원본은 표준편차 0 일 때 float('inf') 를 돌려줘 **균일한 +0.001 을 '무한대 효과'**
    로 통과시켰다. None 이어야 하고, 판정은 실질 유의성이 맡는다(§5)."""
    assert stat_significance.cohens_d_paired([0.001] * 20) is None
    d = stat_significance.cohens_d_paired([0.1, 0.2, 0.3])
    assert d is not None and d > 0


def test_metric_alias_and_at_k_extraction():
    m = {"per_item": [{"id": "q1", "answer_correctness_score": 0.5},
                      {"id": "q2", "answer_correctness": 0.7}]}
    assert stat_significance.per_item_values(m, "answer_correctness") == {"q1": 0.5, "q2": 0.7}
    m2 = {"per_item": [{"id": "q1", "recall_at_k": {"5": 1.0}}]}
    assert stat_significance.per_item_values(m2, "recall@5") == {"q1": 1.0}


def test_roles_parsed_from_systems_block():
    import tempfile, os as _os
    d = tempfile.mkdtemp()
    open(_os.path.join(d, "design.md"), "w", encoding="utf-8").write(
        "```systems\n- id: a\n  role: baseline\n- id: b\n  role: proposed\n```\n")
    assert stat_significance.parse_systems(d) == {"a": "baseline", "b": "proposed"}


# ── repro_determinism (원본 결함: 자기 기본값을 반려) ──────────────────────
def test_documented_default_embedding_is_not_rejected():
    """원본의 '숫자 2개 이상' 휴리스틱은 agentforge 자신의 기본값
    `text-embedding-3-small` 을 FAIL 시켰다(실측 exit=1) — 반대 방향의 고장(§5)."""
    assert repro_determinism.check_model_pin(
        "text-embedding-3-small", "embedding", "r1", repro_determinism.DEFAULT_VAGUE) == []


def test_unpinned_alias_is_rejected():
    assert repro_determinism.check_model_pin("gpt-4o", "llm", "r1",
                                             repro_determinism.DEFAULT_VAGUE)
    assert repro_determinism.check_model_pin("claude-sonnet-latest", "llm", "r1",
                                             repro_determinism.DEFAULT_VAGUE)
    assert repro_determinism.check_model_pin("gpt-4o-2024-08-06", "llm", "r1",
                                             repro_determinism.DEFAULT_VAGUE) == []


def test_scalars_flattens_nested_metrics():
    got = repro_determinism.scalars({"a": 1, "b": {"c": 2.5}, "d": "x", "e": True})
    assert got == {"a": 1.0, "b.c": 2.5}


# ── run_completeness (신설) ────────────────────────────────────────────────
def test_run_name_regex_splits_system_and_seed():
    m = run_completeness.RUN_NAME_RE.match("abl-no-rerank__seed22")
    assert m and m.group("sys") == "abl-no-rerank" and m.group("seed") == "22"
    assert run_completeness.RUN_NAME_RE.match("run-01") is None


# ── pii_presence (아키타입 N · 원본 정규식이 양방향으로 무너졌다) ──────────
def test_plain_long_number_is_not_a_phone():
    """원본 `0?1[016789]` 는 선두 0 이 선택이라 평범한 10자리 수를 전화번호(HIGH)로 잡았다.
    실측: `측정값 1012345678` → phone_kr·phone_us 둘 다 HIGH → 하드게이트 FAIL.
    숫자 id 를 가진 정상 데이터셋이 영영 배포되지 않는다(§5)."""
    assert pii_presence.scan_text("측정값 1012345678", ["phone_kr", "phone_us"]) == []
    assert pii_presence.scan_text("행 id 20191055512345", ["phone_kr"]) == []


def test_real_korean_phone_is_detected():
    hits = pii_presence.scan_text("연락처 010-1234-5678", ["phone_kr"])
    assert [n for n, _s, _r in hits] == ["phone_kr"]
    assert pii_presence.scan_text("01012345678", ["phone_kr"])


def test_luhn_uses_the_match_not_a_fixed_window():
    """원본은 `text[p:p+19]` 고정 창으로 Luhn 을 돌려 뒤따르는 문자를 끌어들였다.
    실측: `금액 4111111111111111.50 원` → 자릿수 18 → 미검출(§5)."""
    assert pii_presence.luhn_valid("4111111111111111")
    assert not pii_presence.luhn_valid("4111111111111112")
    hits = pii_presence.scan_text("금액 4111111111111111.50 원", ["credit_card"])
    assert [n for n, _s, _r in hits] == ["credit_card"]


def test_masked_values_are_allowed():
    """마스킹을 막으면 정제된 데이터셋을 배포할 방법이 없다(secret_redaction 과 같은 규율)."""
    assert pii_presence.scan_text("연락처 <EMAIL> 참조", ["email"]) == []
    assert pii_presence.scan_text("주민 900101-1******", ["ssn_kr"]) == []


def test_ssn_kr_accepts_spaces_around_hyphen():
    assert pii_presence.scan_text("주민 900101 - 1234567", ["ssn_kr"])


def test_walk_json_reaches_nested_strings():
    got = pii_presence.walk_json({"a": ["x", {"b": "y"}], "c": 3})
    assert sorted(got) == ["x", "y"]


# ── license_compat (원본 결함 4건) ──────────────────────────────────────────
def test_restrictive_clause_beats_permissive_header():
    """원본은 green→yellow→red 순서라 독점 조건이 덧붙은 Apache 헤더를 green 으로 분류했다.
    실측: ('green', 'Apache-2.0')(§5)."""
    text = "Apache License\nVersion 2.0\n...\nAll Rights Reserved. Proprietary and Confidential."
    assert license_compat.classify_text(text)[0] == "red"
    assert license_compat.classify_text("Apache License\nVersion 2.0\n")[0] == "green"


def test_unidentifiable_license_is_red():
    assert license_compat.classify_text("알 수 없는 이용 약관") == ("red", "UNKNOWN")
    assert license_compat.classify_text("") == ("red", "UNKNOWN")


def test_unknown_compatibility_is_not_compatible():
    """원본은 `overall_pass` 가 INCOMPATIBLE 만 막아 UNKNOWN 을 통과시켰다."""
    assert license_compat.compatibility("UNKNOWN", "MIT") == "UNKNOWN"
    assert license_compat.compatibility("GPL-3.0", "MIT") == "INCOMPATIBLE"
    assert license_compat.compatibility("MIT", "MIT") == "COMPATIBLE"


def test_extra_compatible_widens_the_conservative_matrix():
    """이식한 표는 코드 라이선스 기준이라 보수적이다 — 닫아 두면 legalforge 의
    '어떤 입력에도 FAIL' 과 같은 자리에 이른다. 넓히는 것은 정책(=Sam)의 몫이다."""
    assert license_compat.compatibility("Apache-2.0", "CC-BY-4.0") == "INCOMPATIBLE"
    assert license_compat.compatibility(
        "Apache-2.0", "CC-BY-4.0", {"Apache-2.0": ["CC-BY-4.0"]}) == "COMPATIBLE"


# ── schema_conformance · datasheet_completeness (신설) ─────────────────────
def test_schema_accepts_both_columns_and_json_schema_shapes():
    import tempfile, os as _os, json as _json
    d = tempfile.mkdtemp()
    p1 = _os.path.join(d, "a.json")
    open(p1, "w").write(_json.dumps({"n_rows": 3, "columns": [{"name": "id"}]}))
    assert schema_conformance.parse_schema(p1) == ([{"name": "id"}], 3)
    p2 = _os.path.join(d, "b.json")
    open(p2, "w").write(_json.dumps({"properties": {"id": {"type": "string"}}}))
    cols, n = schema_conformance.parse_schema(p2)
    assert cols[0]["name"] == "id" and cols[0]["dtype"] == "string" and n is None


def test_row_count_field_accepts_thousands_separator():
    assert schema_conformance.int_field("rows_out: 1,024\n", "rows_out") == 1024
    assert schema_conformance.int_field("rows_in: 20\n", "rows_out") is None


def test_body_chars_ignores_markdown_decoration():
    """분량은 어절이 아니라 **글자**로 잰다(국문 대응) — 장식 문자는 내용이 아니다."""
    assert datasheet_completeness.body_chars("- **가나다** `라마`\n\n> 바사") == 7


def test_section_alias_matches_korean_heading():
    secs = {"3. 수집 과정과 절차": "본문"}
    hit = datasheet_completeness.match_section(secs, ["collection", "수집"])
    assert hit and hit[1] == "본문"
    assert datasheet_completeness.match_section(secs, ["maintenance", "유지보수"]) is None


# ── result_tolerance (아키타입 O · 원본 결함 3건) ───────────────────────────
def test_declared_metric_count_is_compared_with_parsed():
    """원본은 `expected:` 없는 항목을 조용히 건너뛰어 3개 중 1개만 검사하고 PASS 했다.
    선언 개수를 따로 세야 그 소실을 잡을 수 있다(§5)."""
    block = ("- metric: accuracy\n  expected: 0.873\n"
             "- metric: f1\n  tolerance: {abs: 0.005}\n"
             "- metric: auc\n  tolerance: {abs: 0.005}\n")
    items, n_declared = result_tolerance.parse_key_results(block)
    assert n_declared == 3 and len(items) == 3
    have_expected = [it for it in items if result_tolerance.NUM_RE.match(str(it.get("expected", "")))]
    assert [it["metric"] for it in have_expected] == ["accuracy"]


def test_run_status_regex_reads_the_report():
    """빌드 실패 보고서를 통과시키던 구멍 — 원본은 measurements 숫자만 읽었다."""
    m = result_tolerance.STATUS_RE.search("build_status: failed\nrun_status: failed\n")
    assert m and m.group(1) == "failed"
    assert result_tolerance.STATUS_RE.search("run_status: success\n").group(1) == "success"


# ── env_consistency (원본 결함 3건) ─────────────────────────────────────────
def test_pin_is_extracted_only_from_exact_equality():
    """`>=`·`~=` 는 핀이 아니다 — 원본은 버전을 한 번도 비교하지 않았다(§5)."""
    assert env_consistency.split_spec("numpy==1.24.0") == ("numpy", "1.24.0")
    assert env_consistency.split_spec("torch>=99.0") == ("torch", None)
    assert env_consistency.split_spec("numpy") == ("numpy", None)
    assert env_consistency.split_spec("scikit-learn=1.3.2") == ("scikit-learn", "1.3.2")


def test_package_name_normalization():
    """`Scikit_Learn` 과 `scikit-learn` 은 같은 패키지다 — 다르게 세면 거짓 미달이 뜬다."""
    assert env_consistency.norm("Scikit_Learn") == "scikit-learn"
    assert env_consistency.norm("NumPy") == "numpy"


def test_dockerfile_mention_is_not_installation():
    """원본은 파일 전체에서 `requirements.txt` 문자열만 찾아, 주석 한 줄에 전 패키지를
    커버로 셌다(실측). COPY 와 RUN 이 **둘 다** 있어야 인정한다(§5)."""
    import tempfile, os as _os
    d = tempfile.mkdtemp()
    p = _os.path.join(d, "Dockerfile")
    open(p, "w").write("FROM python:3.11\n# TODO: requirements.txt 추가\n")
    pkgs, notes = env_consistency.parse_docker(p, {"numpy": "1.24.0"})
    assert pkgs == {} and notes
    open(p, "w").write("FROM python:3.11\nCOPY requirements.txt .\n"
                       "RUN pip install -r requirements.txt\n")
    pkgs, _n = env_consistency.parse_docker(p, {"numpy": "1.24.0"})
    assert pkgs == {"numpy": "1.24.0"}


# ── install_evidence · reproduce_doc (신설) ────────────────────────────────
def test_field_reader_handles_quotes():
    assert install_evidence.field('method: "venv"\n', "method") == "venv"
    assert install_evidence.field("exit_code: 0\n", "exit_code") == "0"
    assert install_evidence.field("# 없음\n", "method") is None


def test_success_words_exclude_failure():
    for w in ("success", "ok", "passed"):
        assert w in install_evidence.SUCCESS_WORDS
    assert "failed" not in install_evidence.SUCCESS_WORDS
    assert "skipped" not in install_evidence.SUCCESS_WORDS


def test_document_title_does_not_shadow_a_section():
    """픽스처가 잡은 자체 결함 — `# 재현 절차` 라는 H1 제목이 'run' 절 별칭에 걸려
    진짜 `## 실행` 절을 덮었다. 하위 제목을 우선한다."""
    secs = reproduce_doc.sections_of("# 재현 절차\n\n서문\n\n## 실행\n\n본문\n")
    hit = reproduce_doc.match_section(secs, ["run", "실행", "재현 절차"])
    assert hit == ("실행", "본문")


def test_body_chars_excludes_code_fences():
    """코드 블록은 설명이 아니다 — 명령만 붙여 놓고 설명을 생략하는 것을 잡는다."""
    body = "설명이다.\n\n```bash\npip install -r requirements.txt\n```\n"
    assert reproduce_doc.body_chars(body) == len("설명이다.")


def test_command_file_tokens_extracted():
    got = set(reproduce_doc.FILE_TOKEN_RE.findall("bash reproduce.sh && cat key-results.json"))
    assert got == {"reproduce.sh", "key-results.json"}


# ── bit_exact (아키타입 P · 원본 결함 3건) ─────────────────────────────────
def test_hash_directory_matches_original_algorithm():
    """원본 `hash_outputs.py` 와 같은 누적 규약(<rel>\\0<sha256>\\n)이어야 한다 —
    다르면 정상 산출물이 전부 반려된다."""
    import tempfile, os as _os, hashlib
    d = tempfile.mkdtemp()
    _os.makedirs(_os.path.join(d, "sub"))
    open(_os.path.join(d, "a.json"), "w").write("A")
    open(_os.path.join(d, "sub", "b.json"), "w").write("B")
    want = hashlib.sha256()
    for rel, content in (("a.json", b"A"), ("sub/b.json", b"B")):
        want.update(rel.encode()); want.update(b"\0")
        want.update(hashlib.sha256(content).hexdigest().encode()); want.update(b"\n")
    assert bit_exact.hash_directory(d, []) == want.hexdigest()


def test_hash_excludes_volatile_files():
    """로그·타임스탬프가 해시에 들어가면 어떤 재실행도 bit-exact 가 아니게 된다."""
    import tempfile, os as _os
    d = tempfile.mkdtemp()
    open(_os.path.join(d, "a.json"), "w").write("A")
    h1 = bit_exact.hash_directory(d, ["*.log"])
    open(_os.path.join(d, "solver.log"), "w").write("iteration 412")
    assert bit_exact.hash_directory(d, ["*.log"]) == h1


def test_design_point_comparison_is_numeric():
    """`0.10` 과 `0.1` 은 같은 설계점이다 — 문자열로 비교하면 거짓 드리프트가 뜬다."""
    assert bit_exact.num_eq("0.10", 0.1)
    assert bit_exact.num_eq(100, "100")
    assert not bit_exact.num_eq(0.1, 0.25)
    assert bit_exact.num_eq("abc", "abc")


# ── solver_pin (원본에 스크립트가 없던 Gate 1) ──────────────────────────────
def test_unpinned_tags_rejected():
    tags = solver_pin.DEFAULT_UNPINNED
    assert solver_pin.is_unpinned("latest", tags)
    assert solver_pin.is_unpinned("main", tags)
    assert solver_pin.is_unpinned("openfoam:latest", tags)
    assert not solver_pin.is_unpinned("11.0", tags)
    assert not solver_pin.is_unpinned("3f2a91c8d4", tags)


def test_token_value_detected_but_env_var_name_allowed():
    """`auth_env_var: EDISON_API_TOKEN` 은 이름이므로 통과, 값은 차단."""
    assert solver_pin.TOKEN_VALUE_RE.search("api_key: abcdefghijklmnopqrstuvwxyz0123")
    assert not solver_pin.TOKEN_VALUE_RE.search("auth_env_var: EDISON_API_TOKEN")


# ── doe_completeness (원본에 스크립트가 없던 Gate 3) ────────────────────────
def test_declared_count_fixes_the_denominator():
    """설계점을 표에서도 지우면 회계가 **내부적으로 일관**해진다 — 픽스처가 잡은 자체 결함.
    분모를 따로 선언하게 해서 조용한 축소를 막는다."""
    import tempfile, os as _os
    d = tempfile.mkdtemp()
    open(_os.path.join(d, "doe.md"), "w", encoding="utf-8").write(
        "n_design_points: 6\n\n```runs\n- id: run-01\n  status: done\n```\n")
    assert doe_completeness.declared_count(d) == 6
    open(_os.path.join(d, "doe.md"), "w", encoding="utf-8").write("```runs\n- id: run-01\n```\n")
    assert doe_completeness.declared_count(d) is None


def test_output_schema_is_key_set():
    import tempfile, os as _os, json as _json
    d = tempfile.mkdtemp()
    p = _os.path.join(d, "outputs.json")
    open(p, "w").write(_json.dumps({"drag": 1.0, "lift": 2.0}))
    assert doe_completeness.schema_of(p) == frozenset({"drag", "lift"})
    open(p, "w").write("not json")
    assert doe_completeness.schema_of(p) is None


# ── analysis_integrity (신설) ──────────────────────────────────────────────
def test_declared_independent_vars_parsed():
    import tempfile, os as _os
    d = tempfile.mkdtemp()
    open(_os.path.join(d, "hypothesis.md"), "w", encoding="utf-8").write(
        "```independent_vars\n- name: mesh\n  range: [1, 2]\n- name: reynolds\n```\n")
    assert analysis_integrity.declared_vars(d) == ["mesh", "reynolds"]


def test_csv_reference_extraction():
    got = set(analysis_integrity.CSV_REF_RE.findall("표는 `data/drag.csv` 와 data/lift.csv 에"))
    assert got == {"data/drag.csv", "data/lift.csv"}


def test_caveat_terms_cover_korean_and_english():
    for t in ("근사", "proxy"):
        assert any(t in c for c in analysis_integrity.DEFAULT_CAVEATS)


def test_systems_block_parses_change_field():
    got = run_completeness.parse_systems(
        "- id: a\n  role: ablation\n  change: 리랭커 제거\n- id: b\n  role: baseline\n")
    assert got[0]["change"] == "리랭커 제거" and got[1]["role"] == "baseline"



# ── 아키타입 Q: proposal_format ──────────────────────────────────────────
def test_gantt_tasks_ignores_directives():
    """`gantt`·`title`·`section` 은 task 가 아니다 — 원본은 블록 존재만 봤다."""
    text = "```mermaid\ngantt\n    title 일정\n    dateFormat YYYY-MM-DD\n" \
           "    section 활동\n    설계 :a1, 2026-03-01, 90d\n```"
    assert proposal_format.gantt_tasks(text) == ["설계 :a1, 2026-03-01, 90d"]


def test_gantt_tasks_empty_chart_is_not_none():
    """빈 도표는 None(블록 없음)이 아니라 [] — 이 구별이 원본 결함의 자리다."""
    assert proposal_format.gantt_tasks("```mermaid\ngantt\n```") == []
    assert proposal_format.gantt_tasks("# 제목뿐") is None


def test_ascii_ratio_detects_korean_abstract():
    assert proposal_format.ascii_ratio("This is an English abstract.") == 1.0
    assert proposal_format.ascii_ratio("이것은 국문 초록이다") < 0.3


def test_section_path_accepts_korean_alias():
    import tempfile, os as _os
    d = tempfile.mkdtemp()
    open(_os.path.join(d, "연구목표.md"), "w", encoding="utf-8").write("x")
    assert proposal_format.section_path(d, "aims", {"aims": ["연구목표"]})
    assert proposal_format.section_path(d, "aims", {}) is None


# ── 아키타입 Q: budget_integrity ─────────────────────────────────────────
def test_parse_amount_rejects_non_numeric():
    """원본은 숫자가 아닌 셀을 0 으로 읽었다. 우리는 None(=FAIL)."""
    assert budget_integrity.parse_amount(" 1,200,000 원 ") == 1200000
    assert budget_integrity.parse_amount("") == 0
    assert budget_integrity.parse_amount("삼천만원") is None
    assert budget_integrity.parse_amount("1-2") is None


def test_parse_amount_keeps_negative_visible():
    """음수를 '읽지 못하는' 것이 아니라 읽고 정책으로 막는다(조정 행 우회)."""
    assert budget_integrity.parse_amount("-160000000") == -160000000


def test_parse_resources_reads_kind_and_missing_block():
    """예산의 분모는 plan.md 선언이다 — 블록이 없으면 None(=FAIL)이어야 한다."""
    import tempfile, os as _os
    d = tempfile.mkdtemp()
    p1 = _os.path.join(d, "plan.md")
    open(p1, "w", encoding="utf-8").write(
        "```resources\n- id: r1\n  kind: equipment\n  item: GPU 서버\n```\n")
    assert budget_integrity.parse_resources(p1) == [
        {"id": "r1", "kind": "equipment", "item": "GPU 서버"}]
    p2 = _os.path.join(d, "empty.md")
    open(p2, "w", encoding="utf-8").write("# 계획만 있고 자원 선언이 없다\n")
    assert budget_integrity.parse_resources(p2) is None


# ── 아키타입 Q: call_alignment ───────────────────────────────────────────
def test_match_program_allows_suffix_but_not_unknown():
    rules = {"신진": {"max_years_post_phd": 7}, "리더": {"min_years_post_phd": 10}}
    assert call_alignment.match_program("신진연구자사업(2026)", rules)[0] == "신진"
    # 원본은 여기서 자동 PASS 였다 — 우리는 None → FAIL
    assert call_alignment.match_program("기본연구", rules)[0] is None
    assert call_alignment.match_program("", rules)[0] is None


def test_criteria_block_parsed_with_korean_ids():
    import tempfile, os as _os
    p = _os.path.join(tempfile.mkdtemp(), "outline.md")
    open(p, "w", encoding="utf-8").write(
        "```criteria\n- id: 창의성\n  section: aims\n  evidence: 근거 서술\n```\n")
    got = call_alignment.parse_criteria(p)
    assert got == [{"id": "창의성", "section": "aims", "evidence": "근거 서술"}]


# ── 아키타입 Q: proposal_traceability ────────────────────────────────────
def test_mentions_survives_korean_particles():
    """`\\ba1\\b` 는 `a1을` 에서 실패한다(docs/13 §5). lookaround 로 잡는다."""
    assert proposal_traceability.mentions("활동 a1을 먼저 수행한다", "a1")
    assert proposal_traceability.mentions("a2의 결과를 (a3)와 비교한다", "a3")
    assert not proposal_traceability.mentions("a10 은 다른 활동이다", "a1")


def test_id_list_parses_bracket_and_bare():
    assert proposal_traceability.id_list("[g1, g2]") == ["g1", "g2"]
    assert proposal_traceability.id_list("g1") == ["g1"]
    assert proposal_traceability.id_list("") == []


# ── 아키타입 R: comment_fidelity ─────────────────────────────────────────
def test_normalize_strips_list_markers_on_both_sides():
    """파싱하며 목록 기호를 떼는 것은 정상이다 — 양쪽에서 똑같이 떼야 정상 산출물이 통과한다."""
    raw = comment_fidelity.normalize("1. The experiments are limited;\n   validation is missing.")
    cited = comment_fidelity.normalize("The experiments are limited; validation is missing.")
    assert cited in raw


def test_numbered_items_counts_only_consecutive():
    """`1. 2. 3.` 은 항목이지만 본문의 연도·수치 나열은 항목이 아니다."""
    assert comment_fidelity.numbered_items("1. first\n2. second\n3. third\n") == 3
    assert comment_fidelity.numbered_items("산문형 리뷰입니다. 번호가 없습니다.\n") == 0
    assert comment_fidelity.numbered_items("1. only one\n5. out of order\n") == 1


def test_verbatim_sections_split_by_id():
    got = comment_fidelity.verbatim_sections("## R1.1\n첫 지적\n\n## R1.2\n둘째 지적\n")
    assert sorted(got) == ["R1.1", "R1.2"] and "첫 지적" in got["R1.1"]


# ── 아키타입 R: comment_coverage ─────────────────────────────────────────
def test_body_words_excludes_frontmatter_and_changes_block():
    """빈 응답(프론트매터만)은 0 어절이어야 한다 — 원본은 이런 파일을 '응답'으로 셌다."""
    import tempfile, os as _os
    d = tempfile.mkdtemp()
    p1 = _os.path.join(d, "R1.1.md")
    open(p1, "w", encoding="utf-8").write("---\ncomment_id: R1.1\nverdict: accept\n---\n")
    assert comment_coverage.body_words(p1) == 0
    p2 = _os.path.join(d, "R1.2.md")
    open(p2, "w", encoding="utf-8").write(
        "---\nverdict: accept\n---\n답변 본문 세 어절\n\n```changes\n- action: replace\n```\n")
    assert comment_coverage.body_words(p2) == 4   # changes 블록은 답변이 아니다


def test_response_id_prefers_frontmatter_then_filename():
    import tempfile, os as _os
    d = tempfile.mkdtemp()
    p1 = _os.path.join(d, "anything.md")
    open(p1, "w", encoding="utf-8").write("---\ncomment_id: R2.3\n---\n본문\n")
    assert comment_coverage.response_id(p1) == "R2.3"
    p2 = _os.path.join(d, "R1.1.md")
    open(p2, "w", encoding="utf-8").write("본문만 있다\n")
    assert comment_coverage.response_id(p2) == "R1.1"
    p3 = _os.path.join(d, "notes.md")
    open(p3, "w", encoding="utf-8").write("메모\n")
    assert comment_coverage.response_id(p3) is None


# ── 아키타입 R: change_consistency ───────────────────────────────────────
def test_log_line_accepts_bullet_forms():
    """원본은 `- R1.1: …` 을 0건으로 읽어 **정상 변경기록을 반려**했다(실측)."""
    for line in ("R1.1: 고쳤다", "- R1.1: 고쳤다", "* R1.1: 고쳤다", "1. R1.1: 고쳤다",
                 "  - R1.1: 고쳤다"):
        m = change_consistency.LOG_LINE_RE.match(line)
        assert m and m.group(1) == "R1.1", line


def test_log_line_rejects_empty_description():
    assert change_consistency.LOG_LINE_RE.match("- R1.1:") is None


def test_strip_tags_removes_change_markers():
    import re as _re
    tag = _re.compile(r"\[CHANGE-(R\d+\.\d+)\s*:[^\]]*\]")
    got = change_consistency.strip_tags("[CHANGE-R1.1: 실험 추가] 본문이 남는다", tag)
    assert change_consistency.normalize(got) == "본문이 남는다"


# ── 아키타입 R: response_quality ─────────────────────────────────────────
def test_evidence_markers_require_a_locator_not_a_substring():
    """한국어 부분 일치 함정 — `적절히` 안에 `절` 이 있다(docs/13 §5)."""
    assert not response_quality.has_any("적절히 수정했습니다", response_quality.DEFAULT_EVIDENCE)
    assert not response_quality.has_any("100% 동의합니다", response_quality.DEFAULT_EVIDENCE)
    assert response_quality.has_any("3.2절에 근거가 있다", response_quality.DEFAULT_EVIDENCE)
    assert response_quality.has_any("see Table 4", response_quality.DEFAULT_EVIDENCE)


def test_banned_phrase_matching_is_literal():
    assert response_quality.has_phrase("리뷰어가 오해하신 듯합니다",
                                       response_quality.DEFAULT_BANNED) == ["리뷰어가 오해"]
    assert response_quality.has_phrase("리뷰어의 지적에 감사드립니다",
                                       response_quality.DEFAULT_BANNED) == []


# ── 아키타입 S: claim_provenance ─────────────────────────────────────────
def test_citations_are_scoped_to_the_paragraph():
    """'주변 N자' 창은 옆 트윗의 인용을 끌어온다(픽스처가 잡았다)."""
    text = "## 1/2\n정확도 0.873 [e1].\n\n## 2/2\n기존 대비 8배 빠르다.\n"
    segs = claim_provenance.segments(text)
    assert claim_provenance.citations_at(segs, text.index("0.873")) == {"e1"}
    assert claim_provenance.citations_at(segs, text.index("8배")) == set()


def test_bare_decimal_is_a_number_claim():
    """단위 없는 소수(정확도 0.873)가 발신물에서 가장 흔한 수치다."""
    import re as _re
    pats = claim_provenance.DEFAULT_NUMBER
    assert any(_re.search(p, "정확도는 0.873 이다") for p in pats)
    assert any(_re.search(p, "3.2배 빠르다") for p in pats)
    assert not any(_re.search(p, "버전 v2 를 냈다") for p in pats)


def test_cited_ids_returns_unknown_ids_too():
    """아는 id 만 걸러 내면 환각 인용을 영영 못 잡는다."""
    assert claim_provenance.cited_ids("정확도 [e9] 라고 썼다") == {"e9"}


def test_norm_num_compares_values_not_substrings():
    assert claim_provenance.norm_num("0.873") == claim_provenance.norm_num(" 0.873 ")
    assert claim_provenance.norm_num("8배") != claim_provenance.norm_num("0.873")


# ── 아키타입 S: channel_format ───────────────────────────────────────────
def test_url_counts_as_23_chars():
    n = channel_format.chars_with_url_rule("보라 https://example.com/very/long/path/indeed")
    assert n == len("보라 ") + 23


def test_twitter_numbering_and_cta():
    ok = "## 1/2\n첫 글\n\n## 2/2\n마지막 https://x.com\n"
    assert channel_format.check_twitter(ok, {"min_posts": 2, "max_posts": 2}) == []
    bad = "## 1/2\n첫 글\n\n## 3/2\n마지막 https://x.com\n"
    assert any("번호" in e for e in
               channel_format.check_twitter(bad, {"min_posts": 2, "max_posts": 2}))


def test_medium_word_range_is_korean_eojeol():
    """영문 word 수치를 그대로 쓰면 정상 국문 글이 반려된다(원본 결함)."""
    text = "# 제목\n\n> Hero image hint: 그림\n\n" + "## 절\n\n" * 3 + "낱말 " * 1000
    errs = channel_format.check_medium(text, {"word_range": [900, 2100],
                                              "min_headings": 3, "max_headings": 6})
    assert errs == [], errs


# ── 아키타입 S: outreach_tone ────────────────────────────────────────────
def test_hype_counting_is_cumulative():
    hits = outreach_tone.count_hype("획기적이고 혁명적인 놀라운 breakthrough 이며 전례없는 성과",
                                    outreach_tone.DEFAULT_HYPE)
    assert len(hits) == 5      # 원본은 이것을 PASS 로 판정했다


def test_posts_split_by_thread_numbering():
    posts = outreach_tone.posts_of("## 1/2\n가\n\n## 2/2\n나\n")
    assert len(posts) == 2


# ── 아키타입 S: release_readiness ────────────────────────────────────────
def test_embargo_compared_to_launch_without_a_clock():
    """시각에 의존하는 판정은 시간이 지나면 픽스처가 깨진다(P 에서 배운 것)."""
    assert "2026-10-01" > "2026-09-01"     # 게이트가 쓰는 비교 그대로
    assert not ("2026-08-15" > "2026-09-01")


def test_visuals_block_requires_source_and_license():
    import tempfile, os as _os
    p = _os.path.join(tempfile.mkdtemp(), "visuals.md")
    open(p, "w", encoding="utf-8").write(
        "```visuals\n- id: v1\n  source: fig.png\n  license: own\n```\n")
    got = release_readiness.parse_visuals(p)
    assert got == [{"id": "v1", "source": "fig.png", "license": "own"}]
    open(p, "w", encoding="utf-8").write("# 그림만 있고 블록이 없다\n")
    assert release_readiness.parse_visuals(p) is None


# ── 아키타입 T: slide_budget ─────────────────────────────────────────────
def test_note_placeholder_is_substring_not_equality():
    """원본은 `body.lower() in ("tbd","todo","...")` 완전 일치라 `TBD.` 가 통과했다."""
    terms = slide_budget.DEFAULT_PLACEHOLDERS
    assert slide_budget.is_placeholder("TBD.", terms) == "TBD"
    assert slide_budget.is_placeholder("작성 예정", terms) == "작성 예정"
    assert slide_budget.is_placeholder("이 장에서는 배경을 짧게 말한다", terms) is None


def test_speaker_block_body_extracted():
    text = "## 제목\n\n- 불릿\n\n<!-- speaker:\n할 말이다\n-->\n"
    assert slide_budget.note_body(text) == "할 말이다"
    assert slide_budget.note_body("## 제목\n- 불릿\n") is None


def test_note_items_recognize_korean_and_english_headings():
    text = "## Slide 3: 제목\n본문\n### 슬라이드 4 제목\n본문\n## Q&A 예상 질문\n"
    got = {int(m.group(1)) for m in slide_budget.NOTE_ITEM_RE.finditer(text)}
    assert got == {3, 4}, got          # Q&A 절은 슬라이드 항목이 아니다


def test_slides_block_parsed_with_fields():
    got = slide_budget.parse_block(
        "```slides\n- id: 1\n  section: intro\n  time_min: 0.8\n```\n",
        slide_budget.SLIDE_BLOCK_RE)
    assert got == [{"id": "1", "section": "intro", "time_min": "0.8"}]


# ── 아키타입 T: deck_format ──────────────────────────────────────────────
def test_body_excludes_speaker_notes_and_frontmatter():
    text = ("---\nslide_number: 1\n---\n\n## 제목\n\n- 하나\n- 둘\n\n"
            "<!-- speaker:\n노트에도 - 불릿처럼 보이는 줄이 있다\n-->\n")
    body = deck_format.body_of(text)
    assert "slide_number" not in body and "노트에도" not in body
    assert deck_format.count_bullets(body) == 2


def test_visual_counts_image_and_mermaid_placeholder():
    body = "![설명](a.png)\n\n{{mermaid:d1}}\n"
    assert deck_format.count_visuals(body) == 2


def test_deck_chunks_exclude_deck_frontmatter():
    deck = "---\nmarp: true\ntheme: default\n---\n\n## 1\n\n---\n\n## 2\n"
    assert len(deck_format.deck_slide_chunks(deck)) == 2


# ── 아키타입 T: diagram_integrity ────────────────────────────────────────
def test_bracket_check_is_a_stack_not_a_tally():
    """원본은 문자 총계를 세어 `A[Input) --> B(Encoder]` 를 통과시켰다(실측)."""
    ok = ["flowchart LR", "    A[입력] --> B(인코더)"]
    bad = ["flowchart LR", "    A[입력) --> B(인코더]"]
    assert diagram_integrity.bracket_issue(ok) is None
    assert diagram_integrity.bracket_issue(bad) is not None


def test_er_diagram_cardinality_is_not_a_bracket():
    """`||--o{` 는 괄호가 아니다 — 정상 erDiagram 을 반려하면 안 된다."""
    lines = ["erDiagram", "    CUSTOMER ||--o{ ORDER : places"]
    assert diagram_integrity.bracket_issue(lines) is None


def test_quoted_label_parens_are_ignored():
    lines = ["flowchart LR", '    A["설명 (괄호 포함)"] --> B[출력]']
    assert diagram_integrity.bracket_issue(lines) is None


def test_node_count_only_for_flowchart():
    lines = ["flowchart LR", "    A[a] --> B[b]", "    B --> C[c]"]
    assert diagram_integrity.count_nodes("flowchart", lines) == 3
    assert diagram_integrity.count_nodes("sequenceDiagram", lines) == 0


def test_empty_mermaid_is_not_valid():
    issues = diagram_integrity.lint_mermaid("", diagram_integrity.DEFAULT_TYPES, 8, 2)
    assert issues and "빈 파일" in issues[0]


def test_source_ids_read_evidence_and_figures_blocks():
    import tempfile, os as _os
    p = _os.path.join(tempfile.mkdtemp(), "source.md")
    open(p, "w", encoding="utf-8").write(
        "```evidence\n- id: e1\n  grade: verified\n- id: e2\n```\n")
    assert diagram_integrity.known_source_ids(p) == {"e1", "e2"}


# ── 아키타입 T: claim_provenance 의 citation_scope 축 ─────────────────────
def test_file_scope_is_one_segment():
    """슬라이드는 파일 하나가 한 화면이다 — 제목의 수치와 불릿의 인용이 빈 줄로 갈린다."""
    text = "## 3.2배 빠른 추론\n\n- 속도가 개선됐다 [e3]\n"
    para = claim_provenance.segments(text)
    assert claim_provenance.citations_at(para, text.index("3.2")) == set()
    whole = [(0, len(text), claim_provenance.cited_ids(text))]
    assert claim_provenance.citations_at(whole, text.index("3.2")) == {"e3"}


# ── status 제외 어휘 (2026-08-05 · M-2026-005 라이브 발견) ──────────────────
def test_rejected_sources_are_not_counted():
    """★ 결함 재현: 템플릿은 curator 에게 `status=selected/rejected` 로 판정하라고 지시하는데
    게이트는 `("failed","excluded")` 두 단어만 걸렀다 → **버린 자료가 정책 카운트에 잡힌다.**
    하한을 정확히 맞춘 수집에서 한 건만 버려져도 실제로는 미달인데 PASS 가 난다."""
    srcs = [{"status": "selected"}, {"status": "rejected"}, {"status": "Excluded"},
            {"status": "failed"}, {"status": "duplicate_of_s3"}, {}]
    inc, exc = source_balance.included_sources(srcs, {})
    assert len(inc) == 2, [s.get("status") for s in inc]      # selected + 무status(기본 selected)
    assert len(exc) == 4, [s.get("status") for s in exc]


def test_unknown_status_words_are_included_not_dropped():
    """모르는 단어는 **포함**으로 둔다 — M-2026-003 은 `new`·`reuse_existing_wiki` 를 정상 값으로 썼다.
    deny-list 를 allow-list 로 뒤집으면 그 미션들이 조용히 0건이 된다."""
    srcs = [{"status": "new"}, {"status": "reuse_existing_wiki"}]
    inc, exc = recency_check.included_sources(srcs, {})
    assert len(inc) == 2 and not exc


def test_status_exclusion_is_policy_overridable():
    srcs = [{"status": "quarantined"}, {"status": "selected"}]
    inc, _ = source_balance.included_sources(srcs, {"status_excluded_prefixes": ["quarantine"]})
    assert len(inc) == 1


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
