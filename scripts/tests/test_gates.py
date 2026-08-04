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
