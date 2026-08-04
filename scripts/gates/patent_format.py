#!/usr/bin/env python3
"""
객관 게이트: 관할별 출원서식 준수 + 고지 의무
=============================================
관할(KIPO·USPTO·PCT·EPO)별 필수 절이 출원 문서에 모두 있는지, 그리고 **"변리사 자문이 아님"
고지가 붙어 있는지** LLM 없이 검사한다.
출처: other_projects/harness-templates/.../patentforge/scripts/format_compliance.py
      (우리 gate_keeper CLI 규약으로 이식 + 고지 검사 추가)

⚠️ 고지 검사는 원본에 없던 것을 우리가 **게이트로 승격**한 항목이다. 원본은 finalize 단계에서
   `usage-disclaimer.md` 를 첨부하도록 지시만 한다. 특허 초안이 고지 없이 유통되면 변리사
   자문으로 오인될 수 있으므로, 지시가 아니라 **기계 검사**로 강제한다.

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.patent_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : 관할별 출원 문서 디렉터리(applications/) 또는 단일 파일

정책 필드(patent_policy)
  jurisdictions   : 검사할 관할 목록(기본 [kipo]). SCOPE.md frontmatter 의 `jurisdictions:` 가 우선
  require_disclaimer (기본 true) : 고지 문구 필수 여부
  disclaimer_terms : 고지로 인정할 문구 목록(하나라도 있으면 통과)

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

REQUIRED_SECTIONS: dict[str, list[str]] = {
    "kipo": [r"발명의\s*명칭", r"기술\s*분야", r"배경\s*기술",
             r"(?:과제의\s*해결\s*수단|해결\s*수단)", r"발명의\s*효과", r"청구범위", r"요약서"],
    "uspto": [r"TITLE\s+OF\s+(?:THE\s+)?INVENTION", r"FIELD\s+OF\s+(?:THE\s+)?INVENTION",
              r"BACKGROUND\s+OF\s+(?:THE\s+)?INVENTION", r"SUMMARY\s+OF\s+(?:THE\s+)?INVENTION",
              r"DETAILED\s+DESCRIPTION", r"CLAIMS", r"ABSTRACT"],
    "pct": [r"TITLE", r"(?:Technical\s+)?Field", r"Background", r"Disclosure|Summary",
            r"(?:Detailed\s+)?Description", r"Claims", r"Abstract"],
    "epo": [r"Title", r"Technical\s+Field", r"Background\s+Art",
            r"(?:Disclosure|Summary)\s+of\s+(?:the\s+)?Invention",
            r"Brief\s+Description\s+of\s+(?:the\s+)?Drawings",
            r"(?:Best\s+Mode|Detailed\s+Description)", r"Claims", r"Abstract"],
}
DEFAULT_DISCLAIMER_TERMS = ["변리사 자문이 아닙니다", "변리사 자문 아님", "변리사 검토",
                            "not patent attorney", "not legal advice"]


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("patent_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("patent_policy", {}) or {}


def scope_jurisdictions(mission_root: str) -> list[str]:
    try:
        m = FRONTMATTER_RE.match(open(os.path.join(mission_root, "SCOPE.md"), encoding="utf-8").read())
    except OSError:
        return []
    if not m:
        return []
    d = yaml.safe_load(m.group(1)) or {}
    v = d.get("jurisdictions")
    if isinstance(v, str):
        v = [x.strip() for x in v.split(",")]
    return [str(x).strip().lower() for x in (v or [])]


def app_files(draft: str) -> list[str]:
    if os.path.isdir(draft):
        return [os.path.join(draft, f) for f in sorted(os.listdir(draft)) if f.endswith(".md")]
    return [draft] if os.path.isfile(draft) else []


def jurisdiction_of(path: str, known: list[str]) -> str | None:
    stem = os.path.basename(path).rsplit(".md", 1)[0].lower()
    for j in known:
        if j in stem:
            return j
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", default=None, help="미사용(gate_keeper 규약상 전달됨)")
    ap.add_argument("--draft", default=None, help="applications/ 디렉터리 또는 단일 문서")
    args = ap.parse_args()

    if not args.draft:
        print("FAIL(usage): --draft(applications/) 필수 — fail-closed", file=sys.stderr); return 2
    try:
        policy = load_policy(args.policy)
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e} — fail-closed", file=sys.stderr); return 2

    files = app_files(args.draft)
    if not files:
        print(f"FAIL(usage): 출원 문서를 찾지 못했다({args.draft}) — fail-closed", file=sys.stderr)
        return 2

    # 미션 루트 = applications/ 의 상위(단일 파일이면 그 파일의 상위의 상위)
    root = os.path.dirname(os.path.abspath(args.draft)) if os.path.isdir(args.draft) \
        else os.path.dirname(os.path.dirname(os.path.abspath(args.draft)))
    juris = scope_jurisdictions(root) or [str(j).lower() for j in (policy.get("jurisdictions") or ["kipo"])]
    require_disc = bool(policy.get("require_disclaimer", True))
    terms = policy.get("disclaimer_terms") or DEFAULT_DISCLAIMER_TERMS

    print(f"관할 {juris} · 출원 문서 {len(files)}건 · 고지 필수={require_disc}")

    fail = False
    covered: set[str] = set()
    for path in files:
        name = os.path.basename(path)
        j = jurisdiction_of(path, list(REQUIRED_SECTIONS))
        try:
            text = open(path, encoding="utf-8").read()
        except OSError as e:
            print(f"FAIL: {name} 읽기 실패 ({e})"); fail = True; continue
        if not j:
            print(f"WARNING: {name} — 파일명에서 관할을 식별하지 못했다(검사 생략). "
                  f"파일명을 <관할>.md 로 하라")
            continue
        covered.add(j)
        missing = [p for p in REQUIRED_SECTIONS[j] if not re.search(p, text, re.IGNORECASE)]
        if missing:
            print(f"FAIL: {name}({j}) 필수 절 누락 {len(missing)}건: {missing}")
            fail = True
        else:
            print(f"  ✓ {name}({j}) 필수 절 {len(REQUIRED_SECTIONS[j])}개 충족")
        if require_disc and not any(t.lower() in text.lower() for t in terms):
            print(f"FAIL: {name} 에 고지 문구가 없다 — 특허 초안은 변리사 자문으로 오인될 수 "
                  f"있으므로 고지가 필수다(인정 문구: {terms[:2]}…)")
            fail = True

    absent = [j for j in juris if j not in covered]
    if absent:
        print(f"FAIL: 선언된 관할 {absent} 의 출원 문서가 없다")
        fail = True

    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
