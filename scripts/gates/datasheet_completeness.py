#!/usr/bin/env python3
"""
객관 게이트: 데이터시트 완결성(3표준)
=====================================
데이터셋 문서(Datasheets for Datasets · Data Statements · Croissant ML)가 **필수 절을 실제
내용으로 채웠는지** LLM 없이 검사한다.
출처: datasetforge 의 `datasheet-completeness-check` critic — **스크립트가 없다**(LLM 크리틱뿐). 신설.

⚠️ 이 게이트가 필요한 이유는 데이터시트가 **형식만 갖추기 가장 쉬운 산출물**이기 때문이다.
   표준이 정한 절 제목을 나열하고 각 절에 "TBD" 를 적으면 겉보기에 완성된 문서가 된다.
   원본 크리틱의 판정 기준도 "no empty placeholders" 라는 **서술**뿐이라, 무엇을
   플레이스홀더로 볼지가 매번 달라진다.

⚠️ **병렬 산출물은 "선언 목록 대비 존재"를 항상 확인한다**(docs/13 §5). 3표준을 subagent
   3개가 병렬로 쓴다. 워커 하나가 죽어 `data-statement.md` 가 아예 없으면, 있는 파일만
   훑는 검사는 **검사할 것이 없어 통과**한다(policy-brief 의 `formats/*.md` glob 함정).

⚠️ **분량은 글자로 잰다.** 국문 데이터시트의 한 절은 어절 수가 적어도 충분히 서술적이다
   (policy-brief 에서 겪은 한국어 분량 함정 — docs/13 §5).

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.datasheet_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : 미션 디렉터리 또는 datasheets/ 디렉터리

정책 필드(datasheet_policy)
  standards (기본 [gebru, bender, croissant]) — 선언한 것은 반드시 존재해야 한다
  min_section_chars (기본 60) · placeholder_terms (기본 TBD·TODO·미정·N/A)
  sections_gebru · sections_bender (기본은 아래 표준 절 목록)
  croissant_required (기본 @context·@type·name·description·license·recordSet)

exit: 0 PASS · 1 FAIL · 2 usage/입력없음(fail-closed)
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML 필요", file=sys.stderr); sys.exit(2)

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
HEADING_RE = re.compile(r"^(#{1,4})\s+(.+?)\s*$", re.MULTILINE)
DEFAULT_PLACEHOLDERS = ["TBD", "TODO", "미정", "N/A", "작성 예정", "FIXME", "추후", "lorem ipsum"]

# Gebru et al. 2018 — Datasheets for Datasets 의 7개 축(국문 표기 별칭 포함)
SECTIONS_GEBRU = {
    "motivation": ["motivation", "동기", "제작 동기", "목적"],
    "composition": ["composition", "구성", "구성 요소", "데이터 구성"],
    "collection": ["collection", "collection process", "수집", "수집 과정", "수집 절차"],
    "preprocessing": ["preprocessing", "cleaning", "labeling", "전처리", "정제", "라벨링"],
    "uses": ["uses", "용도", "사용", "활용"],
    "distribution": ["distribution", "배포", "유통"],
    "maintenance": ["maintenance", "유지보수", "관리", "유지 관리"],
}
# Bender & Friedman 2018 — Data Statements for NLP
SECTIONS_BENDER = {
    "curation_rationale": ["curation rationale", "큐레이션", "선별 기준", "수집 기준"],
    "language_variety": ["language variety", "언어", "언어 변종"],
    "speaker_demographic": ["speaker demographic", "화자", "화자 인구", "발화자"],
    "annotator_demographic": ["annotator demographic", "주석자", "레이블러", "annotator"],
    "speech_situation": ["speech situation", "발화 상황", "수집 상황"],
    "text_characteristics": ["text characteristics", "텍스트 특성", "본문 특성"],
    "provenance": ["provenance", "출처", "출처 이력"],
}
CROISSANT_REQUIRED = ["@context", "@type", "name", "description", "license", "recordSet"]
FILES = {"gebru": "datasheet.md", "bender": "data-statement.md", "croissant": "croissant.json"}


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("datasheet_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("datasheet_policy", {}) or {}


def find_dir(draft: str) -> str | None:
    p = os.path.abspath(draft)
    if os.path.isfile(p):
        p = os.path.dirname(p)
    if os.path.basename(p) == "datasheets":
        return p
    cand = os.path.join(p, "datasheets")
    return cand if os.path.isdir(cand) else None


def sections_of(text: str) -> dict[str, str]:
    """제목 → 본문. 목차 나열이 아니라 **본문 길이**로 채움을 판정하기 위해 쪼갠다."""
    out: dict[str, str] = {}
    marks = list(HEADING_RE.finditer(text))
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        out[m.group(2).strip()] = text[m.end():end].strip()
    return out


def body_chars(body: str) -> int:
    """공백·마크다운 장식을 뺀 실질 글자 수(어절이 아니라 글자 — 국문 대응)."""
    return len(re.sub(r"[\s`*_>#\-|\[\]()]+", "", body))


def match_section(secs: dict[str, str], aliases: list[str]) -> tuple[str, str] | None:
    for title, body in secs.items():
        low = title.lower()
        if any(a.lower() in low for a in aliases):
            return title, body
    return None


def main() -> int:  # noqa: C901
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", default=None, help="미사용(gate_keeper 규약상 전달됨)")
    ap.add_argument("--draft", default=None, help="미션 디렉터리 또는 datasheets/")
    args = ap.parse_args()

    if not args.draft:
        print("FAIL(usage): --draft 필수 — fail-closed", file=sys.stderr); return 2
    try:
        policy = load_policy(args.policy)
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e} — fail-closed", file=sys.stderr); return 2

    base = find_dir(args.draft)
    if not base:
        print(f"FAIL(usage): datasheets/ 를 찾지 못했다({args.draft}) — 데이터시트 없이 "
              f"데이터셋을 배포할 수 없다. fail-closed", file=sys.stderr)
        return 2

    standards = [str(s).lower() for s in (policy.get("standards") or ["gebru", "bender", "croissant"])]
    min_chars = int(policy.get("min_section_chars", 60))
    placeholders = policy.get("placeholder_terms") or DEFAULT_PLACEHOLDERS
    secs_gebru = policy.get("sections_gebru") or SECTIONS_GEBRU
    secs_bender = policy.get("sections_bender") or SECTIONS_BENDER
    croissant_req = policy.get("croissant_required") or CROISSANT_REQUIRED

    fail = False
    print(f"표준 {standards} · 절 최소 {min_chars}자(공백 제외)")

    # ① 선언 목록 대비 존재 — 병렬 워커가 죽으면 파일이 통째로 없다
    for std in standards:
        fn = FILES.get(std)
        if not fn:
            print(f"FAIL(usage): 알 수 없는 표준 {std!r} — fail-closed", file=sys.stderr)
            return 2
        if not os.path.isfile(os.path.join(base, fn)):
            print(f"FAIL: 선언한 표준 {std}({fn})의 파일이 없다 — **있는 파일만 훑는 검사는 "
                  f"부재를 통과시킨다**(병렬 워커 하나가 죽은 경우)")
            fail = True

    # ② 마크다운 2표준
    for std, spec in (("gebru", secs_gebru), ("bender", secs_bender)):
        if std not in standards:
            continue
        path = os.path.join(base, FILES[std])
        if not os.path.isfile(path):
            continue
        text = open(path, encoding="utf-8").read()
        secs = sections_of(text)
        print(f"  [{std}] {FILES[std]} — 절 {len(secs)}개")
        for key, aliases in spec.items():
            hit = match_section(secs, aliases if isinstance(aliases, list) else [aliases])
            if hit is None:
                print(f"FAIL: {FILES[std]} 에 '{key}' 절이 없다 (인정 표기: "
                      f"{(aliases if isinstance(aliases, list) else [aliases])[:3]})")
                fail = True
                continue
            title, body = hit
            n = body_chars(body)
            bad = [t for t in placeholders if t.lower() in body.lower()]
            if n < min_chars:
                print(f"FAIL: {FILES[std]} '{title}' 절의 본문이 {n}자 — 제목만 있고 내용이 "
                      f"없다(하한 {min_chars}자)")
                fail = True
            elif bad:
                print(f"FAIL: {FILES[std]} '{title}' 절이 플레이스홀더를 담고 있다 {bad[:3]} — "
                      f"'채우지 않았다'를 '채웠다'로 셀 수 없다")
                fail = True

    # ③ Croissant JSON-LD
    if "croissant" in standards:
        path = os.path.join(base, FILES["croissant"])
        if os.path.isfile(path):
            try:
                d = json.loads(open(path, encoding="utf-8").read())
            except (ValueError, json.JSONDecodeError) as e:
                print(f"FAIL: croissant.json 파싱 실패 ({e}) — 기계가 읽을 메타데이터가 "
                      f"기계에 안 읽힌다")
                fail = True
                d = None
            if isinstance(d, dict):
                missing = [k for k in croissant_req if k not in d or d[k] in (None, "", [], {})]
                if missing:
                    print(f"FAIL: croissant.json 필수 필드 누락 {missing}")
                    fail = True
                rs = d.get("recordSet")
                if isinstance(rs, list) and not rs:
                    print("FAIL: croissant.json `recordSet` 이 빈 목록이다 — 필드가 있다고 "
                          "내용이 있는 것이 아니다")
                    fail = True
                blob = json.dumps(d, ensure_ascii=False)
                bad = [t for t in placeholders if t.lower() in blob.lower()]
                if bad:
                    print(f"FAIL: croissant.json 에 플레이스홀더 {bad[:3]}")
                    fail = True
                desc = str(d.get("description") or "")
                if len(desc.strip()) < min_chars:
                    print(f"FAIL: croissant.json `description` 이 {len(desc.strip())}자 "
                          f"(하한 {min_chars})")
                    fail = True

    if not fail:
        print(f"  ✓ 표준 {len(standards)}종이 모두 존재하고 필수 절이 실제 내용으로 채워졌다")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
