#!/usr/bin/env python3
"""
객관 게이트: PRISMA 2020 27항목 체크리스트 커버리지
==================================================
체계적 문헌고찰 원고가 PRISMA 2020 보고 항목을 **최소한이라도 다루고 있는지** LLM 없이 검사한다.
출처: other_projects/harness-templates/.../reviewforge/scripts/prisma_audit.py
      (우리 gate_keeper CLI 규약으로 이식. 항목 정의는 Page et al. 2021 BMJ 372:n71)

⚠️ 이것은 **존재 검사이지 품질 검사가 아니다.** 통과는 "각 항목이 최소한 언급됐다"는 뜻이며,
   충분한지는 LLM 검증자(reviewer)와 Sam 이 판단한다 — 그래서 이중 게이트다.

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.prisma_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : 원고(report.md)

정책 필드(prisma_policy)
  checklist_strict (기본 false)  : PARTIAL 을 FAIL 로 볼지
  checklist_min_yes (기본 0)     : YES 최소 개수(0이면 미적용). NO 는 항상 FAIL 사유

exit: 0 PASS · 1 FAIL · 2 usage/입력없음(fail-closed)
"""
from __future__ import annotations
import argparse
import json
import re
import sys

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML 필요", file=sys.stderr); sys.exit(2)

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)

# (번호, 항목명, 키워드(하나 이상 등장해야 함), 절 힌트(등장하면 매칭 강화))
PRISMA_2020: list[tuple[int, str, tuple[str, ...], tuple[str, ...]]] = [
    (1,  "Title",                         ("systematic review", "scoping review", "meta-analysis", "체계적 문헌고찰", "메타분석"), ()),
    (2,  "Abstract",                      ("background", "objective", "method", "result", "conclusion", "초록", "요약"), ("abstract", "초록", "요약")),
    (3,  "Rationale",                     ("rationale", "motivation", "gap", "배경", "필요성"), ("introduction", "서론")),
    (4,  "Objectives",                    ("objective", "research question", "pico", "연구질문", "목적"), ("introduction", "서론")),
    (5,  "Eligibility criteria",          ("eligibility", "inclusion criteria", "exclusion criteria", "포함 기준", "배제 기준"), ("method", "방법")),
    (6,  "Information sources",           ("database", "data source", "information source", "데이터베이스"), ("method", "방법", "search", "검색")),
    (7,  "Search strategy",               ("search strategy", "search string", "query", "boolean", "검색식", "검색 전략"), ("method", "방법", "search", "검색")),
    (8,  "Selection process",             ("selection", "screening", "two reviewer", "선별", "스크리닝"), ("method", "방법")),
    (9,  "Data collection process",       ("data collection", "data extraction", "extract", "데이터 추출"), ("method", "방법")),
    (10, "Data items",                    ("data item", "variables extracted", "outcome", "추출 항목", "변수"), ("method", "방법")),
    (11, "Study risk of bias assessment", ("risk of bias", "quality appraisal", "casp", "mmat", "jbi", "비뚤림", "질 평가"), ("method", "방법")),
    (12, "Effect measures",               ("effect size", "odds ratio", "risk ratio", "standardized mean difference", "narrative", "효과크기"), ("method", "방법", "synthesis", "종합")),
    (13, "Synthesis methods",             ("synthesis", "meta-analysis", "narrative synthesis", "thematic", "종합", "메타분석"), ("method", "방법", "synthesis", "종합")),
    (14, "Reporting bias assessment",     ("publication bias", "reporting bias", "funnel plot", "출판 비뚤림"), ("method", "방법")),
    (15, "Certainty assessment",          ("certainty", "grade", "confidence in evidence", "근거 수준", "확실성"), ("method", "방법", "discussion", "논의")),
    (16, "Study selection",               ("flow diagram", "prisma flow", "selection process", "흐름도", "선별 흐름"), ("result", "결과")),
    (17, "Study characteristics",         ("study characteristic", "table of included studies", "연구 특성", "포함 연구"), ("result", "결과")),
    (18, "Risk of bias in studies",       ("risk of bias", "quality score", "appraisal score", "비뚤림", "질 점수"), ("result", "결과")),
    (19, "Results of individual studies", ("individual study", "per-study", "study-level", "개별 연구"), ("result", "결과")),
    (20, "Results of syntheses",          ("synthesis result", "pooled", "narrative synthesis", "main finding", "종합 결과", "주요 발견"), ("result", "결과")),
    (21, "Reporting biases",              ("publication bias", "funnel plot", "egger", "출판 비뚤림"), ("result", "결과", "discussion", "논의")),
    (22, "Certainty of evidence",         ("certainty of evidence", "grade rating", "근거 확실성", "근거 수준"), ("result", "결과", "discussion", "논의")),
    (23, "Discussion",                    ("discussion", "interpretation", "implication", "limitation", "논의", "한계"), ("discussion", "논의")),
    (24, "Registration and protocol",     ("prospero", "registration", "protocol", "preregistered", "프로토콜", "등록"), ("method", "방법")),
    (25, "Support",                       ("funding", "support", "grant", "연구비", "지원"), ("acknowledg", "감사", "기타")),
    (26, "Competing interests",           ("competing interest", "conflict of interest", "coi", "이해관계", "이해 상충"), ()),
    (27, "Availability of data",          ("data availability", "code availability", "supplementary", "데이터 공개", "부록"), ()),
]


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("prisma_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("prisma_policy", {}) or {}


def normalize(t: str) -> str:
    return re.sub(r"\s+", " ", t.lower())


def check_item(item, text_norm: str) -> str:
    """키워드가 하나도 없으면 NO. 절 힌트는 PARTIAL→YES 로 **올리기만** 하고 NO 를 구제하지 않는다.

    ⚠️ 원본(reviewforge prisma_audit.py)은 `keyword or section` 이면 PARTIAL 을 줬는데,
    절 힌트는 대부분 'methods'·'results' 같은 흔한 제목이라 **어느 원고나 맞는다**. 그래서
    가장 자주 누락되는 항목(프로토콜 등록·연구비·이해상충·근거 확실성)이 키워드가 통째로
    없는데도 PARTIAL 로 살아남아 게이트를 통과했다(이식 중 픽스처로 발견). 근거는 키워드다."""
    _, _, keywords, hints = item
    kw = any(k.lower() in text_norm for k in keywords)
    if not kw:
        return "NO"
    sec = any(h.lower() in text_norm for h in hints) if hints else True
    return "YES" if sec else "PARTIAL"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", default=None, help="미사용(gate_keeper 규약상 전달됨)")
    ap.add_argument("--draft", default=None, help="원고(report.md)")
    args = ap.parse_args()

    if not args.draft:
        print("FAIL(usage): --draft(원고) 필수 — fail-closed", file=sys.stderr); return 2
    try:
        policy = load_policy(args.policy)
        text = open(args.draft, encoding="utf-8").read()
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e} — fail-closed", file=sys.stderr); return 2
    if not text.strip():
        print("FAIL(usage): 원고가 비어 있다 — fail-closed", file=sys.stderr); return 2

    strict = bool(policy.get("checklist_strict", False))
    min_yes = int(policy.get("checklist_min_yes", 0) or 0)

    norm = normalize(text)
    results = [(n, name, check_item(it, norm)) for it in PRISMA_2020 for n, name, _, _ in [it]]
    no = [(n, name) for n, name, v in results if v == "NO"]
    partial = [(n, name) for n, name, v in results if v == "PARTIAL"]
    yes = [r for r in results if r[2] == "YES"]

    print(f"policy: checklist_strict={strict} checklist_min_yes={min_yes or '미적용'}")
    print(f"PRISMA 2020 27항목: YES {len(yes)} · PARTIAL {len(partial)} · NO {len(no)}")
    if no:
        print("미커버(NO):")
        for n, name in no:
            print(f"  - {n:2d}. {name}")
    if partial:
        print("부분커버(PARTIAL)" + (" ← strict 이므로 FAIL" if strict else " ← 경고") + ":")
        for n, name in partial:
            print(f"  - {n:2d}. {name}")

    fail = bool(no)
    if strict and partial:
        fail = True
    if min_yes and len(yes) < min_yes:
        print(f"FAIL: YES {len(yes)}건 < 최소 {min_yes}건")
        fail = True

    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
