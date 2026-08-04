#!/usr/bin/env python3
"""
객관 게이트: 근거 등급(GRADE) ↔ 권고 정합성
==============================================
정책 산출물(브리프·보고서·메모·인포그래픽)의 권고가 **실제 근거에, 등급에 맞게** 뿌리내리고
있는지 LLM 없이 검사한다.
출처: other_projects/harness-templates/.../policyforge/scripts/evidence_grade.py (GATE 1)
      — 이식하면서 **원본이 검사한다고 선언만 하고 실제로는 안 하던 두 가지를 추가**했다.

⚠️ 이식 중 발견한 원본의 구멍 두 개 (docs/13 §5):
  1. **환각 인용이 통과했다** — `grades.get(eid)` 가 None(=근거 목록에 없는 id)이면 low 도
     very-low 도 아니므로 조용히 넘어갔다. `e99` 를 지어내도 PASS 다. → 미상 id 는 FAIL.
  2. **"모든 핵심 권고가 high/moderate 근거에서 유래"를 검사하지 않았다** — docstring 과
     CLAUDE.md 는 그렇게 선언했지만 코드는 "인용이 0건인가"만 봤다. 근거 e5(low) 하나만
     달아둔 권고도 caveat 만 붙이면 통과했다. → 권고 절에 high/moderate 인용 1건 이상 요구.
  3. **한국어에서 인용을 못 읽었다** — `\\b(e\\d+)\\b` 는 `e1을`·`e3에서` 처럼 조사가 붙으면
     `1`↔`을` 사이에 경계가 없어(둘 다 \\w) 매칭에 실패한다. → lookaround 로 교체.

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.evidence_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : formats/ 디렉터리(브리프·보고서·메모·인포그래픽) 또는 단일 문서

근거 목록은 미션 루트의 `evidence.md` 에서 읽는다(draft 의 상위 디렉터리).
  ```evidence
  - id: e1
    grade: high          # high | moderate | low | very_low (높음·중간·낮음·매우낮음 허용)
    statement: ...
  ```

정책 필드(evidence_policy)
  evidence_file (기본 evidence.md) · caveat_grades (기본 [low, very_low])
  caveat_terms · min_refs_per_format (기본 1)
  recommendation_headings · recommendation_required_in (기본 [brief, report, memo])
  strong_grades (기본 [high, moderate])

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
EVIDENCE_BLOCK_RE = re.compile(r"```evidence\s*\n(.*?)\n```", re.DOTALL)
# ⚠️ \b 금지 — 한국어 조사(`e1을`)에서 무너진다. 앞뒤가 영숫자가 아니기만 하면 인용으로 본다.
EVIDENCE_REF_RE = re.compile(r"(?<![0-9A-Za-z])(e\d+)(?![0-9A-Za-z])")
ID_LINE_RE = re.compile(r"^\s*-\s*id:\s*(\S+)")
GRADE_LINE_RE = re.compile(r"^\s+grade:\s*(\S+)")

GRADE_ALIASES = {
    "high": "high", "높음": "high", "상": "high",
    "moderate": "moderate", "중간": "moderate", "중": "moderate", "medium": "moderate",
    "low": "low", "낮음": "low", "하": "low",
    "very_low": "very_low", "verylow": "very_low", "매우낮음": "very_low", "최하": "very_low",
}
DEFAULT_CAVEAT_TERMS = [
    "⚠️", "잠정", "예비적", "신중", "추가 연구", "추가 모니터링", "근거 부족", "제한적 근거",
    "낮은 등급", "low-grade evidence", "preliminary", "exploratory", "tentative",
]
DEFAULT_REC_HEADINGS = ["권고", "정책 권고", "권고사항", "제언", "recommendation", "recommendations"]
DEFAULT_REC_REQUIRED_IN = ["brief", "report", "memo"]
CAVEAT_WINDOW = 400  # 문단이 지나치게 길 때 인용 주변으로 좁히는 폭(자)


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("evidence_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("evidence_policy", {}) or {}


def normalize_grade(raw: str) -> str:
    key = str(raw).strip().strip('"\'').lower().replace("-", "_").replace(" ", "")
    return GRADE_ALIASES.get(key, key)


def parse_grades(evidence_path: str) -> dict[str, str]:
    """evidence.md 의 ```evidence``` 블록에서 {id: grade} 추출."""
    try:
        text = open(evidence_path, encoding="utf-8").read()
    except OSError:
        return {}
    m = EVIDENCE_BLOCK_RE.search(text)
    if not m:
        return {}
    grades: dict[str, str] = {}
    current = None
    for line in m.group(1).splitlines():
        m_id = ID_LINE_RE.match(line)
        if m_id:
            current = m_id.group(1)
            continue
        if current:
            m_g = GRADE_LINE_RE.match(line)
            if m_g:
                grades[current] = normalize_grade(m_g.group(1))
    return grades


def paragraph_bounds(text: str, pos: int) -> tuple[int, int]:
    """pos 를 감싸는 문단(빈 줄 구분)의 [시작, 끝). caveat 탐색 범위."""
    start = text.rfind("\n\n", 0, pos)
    start = 0 if start < 0 else start + 2
    end = text.find("\n\n", pos)
    end = len(text) if end < 0 else end
    return start, end


def caveat_scope(text: str, start: int, end: int) -> str:
    """인용을 감싸는 문단. 문단이 길면 인용 주변 ±CAVEAT_WINDOW 로 좁힌다
    (긴 절 어딘가의 무관한 caveat 이 다른 권고를 면제해 주는 것을 막는다)."""
    p_start, p_end = paragraph_bounds(text, start)
    return text[max(p_start, start - CAVEAT_WINDOW): min(p_end, end + CAVEAT_WINDOW)]


def has_caveat(scope: str, terms: list[str]) -> bool:
    low = scope.lower()
    return any(t.lower() in low for t in terms)


def recommendation_scope(text: str, headings: list[str]) -> str | None:
    """권고 절(제목이 headings 중 하나를 포함하는 ## 절)의 본문. 없으면 None."""
    out, capture, level = [], False, 0
    for line in text.splitlines():
        m = re.match(r"^(#{1,6})\s*(.+?)\s*$", line)
        if m:
            depth, title = len(m.group(1)), m.group(2).lower()
            if capture and depth <= level:
                capture = False
            if not capture and any(h.lower() in title for h in headings):
                capture, level = True, depth
                continue
        if capture:
            out.append(line)
    return "\n".join(out) if out else None


def format_files(draft: str) -> list[str]:
    if os.path.isdir(draft):
        return [os.path.join(draft, f) for f in sorted(os.listdir(draft)) if f.endswith(".md")]
    return [draft] if os.path.isfile(draft) else []


def mission_root(draft: str) -> str:
    p = os.path.abspath(draft)
    return os.path.dirname(p) if os.path.isdir(p) else os.path.dirname(os.path.dirname(p))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", default=None, help="미사용(gate_keeper 규약상 전달됨)")
    ap.add_argument("--draft", default=None, help="formats/ 디렉터리 또는 단일 문서")
    args = ap.parse_args()

    if not args.draft:
        print("FAIL(usage): --draft(formats/) 필수 — fail-closed", file=sys.stderr); return 2
    try:
        policy = load_policy(args.policy)
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e} — fail-closed", file=sys.stderr); return 2

    files = format_files(args.draft)
    if not files:
        print(f"FAIL(usage): 정책 문서를 찾지 못했다({args.draft}) — fail-closed", file=sys.stderr)
        return 2

    evidence_path = os.path.join(mission_root(args.draft), policy.get("evidence_file") or "evidence.md")
    grades = parse_grades(evidence_path)
    if not grades:
        print(f"FAIL(usage): 근거 목록을 읽지 못했다({evidence_path}) — "
              f"```evidence``` 블록에 `- id:` / `grade:` 가 필요하다. fail-closed", file=sys.stderr)
        return 2

    caveat_grades = {normalize_grade(g) for g in (policy.get("caveat_grades") or ["low", "very_low"])}
    strong_grades = {normalize_grade(g) for g in (policy.get("strong_grades") or ["high", "moderate"])}
    caveat_terms = policy.get("caveat_terms") or DEFAULT_CAVEAT_TERMS
    rec_headings = policy.get("recommendation_headings") or DEFAULT_REC_HEADINGS
    rec_required = [str(x).lower() for x in
                    (policy.get("recommendation_required_in") or DEFAULT_REC_REQUIRED_IN)]
    min_refs = int(policy.get("min_refs_per_format", 1))

    dist = {g: sum(1 for v in grades.values() if v == g) for g in
            ("high", "moderate", "low", "very_low")}
    print(f"근거 {len(grades)}건 · 등급분포 {dist} · 정책 문서 {len(files)}건")

    fail = False
    for path in files:
        stem = os.path.basename(path).rsplit(".md", 1)[0].lower()
        bad = False
        try:
            text = open(path, encoding="utf-8").read()
        except OSError as e:
            print(f"FAIL: {stem} 읽기 실패 ({e})"); fail = True; continue

        refs = list(EVIDENCE_REF_RE.finditer(text))
        if len(refs) < min_refs:
            print(f"FAIL: {stem} — 근거 인용 {len(refs)}건 < {min_refs}건. "
                  f"모든 정책 산출물은 근거 id(e1 …)를 명시 인용해야 한다")
            bad = True

        unknown = sorted({m.group(1) for m in refs if m.group(1) not in grades})
        if unknown:
            print(f"FAIL: {stem} — 근거 목록에 없는 id 인용(환각 가능) {unknown} "
                  f"→ evidence.md 의 ```evidence``` 블록에 정의하거나 인용을 지워라")
            bad = True

        no_caveat = []
        for m in refs:
            eid = m.group(1)
            if grades.get(eid) in caveat_grades:
                if not has_caveat(caveat_scope(text, m.start(), m.end()), caveat_terms):
                    excerpt = " ".join(text[max(0, m.start() - 40):m.end() + 40].split())
                    no_caveat.append((eid, grades[eid], excerpt))
        if no_caveat:
            print(f"FAIL: {stem} — 낮은 등급 근거를 유보 표현 없이 인용 {len(no_caveat)}건")
            for eid, g, ex in no_caveat[:3]:
                print(f"       · {eid}({g}): …{ex}…")
            bad = True

        strong = []
        if stem in rec_required:
            scope = recommendation_scope(text, rec_headings)
            if scope is None:
                print(f"FAIL: {stem} — 권고 절을 찾지 못했다(제목에 {rec_headings[:3]} 중 하나 필요)")
                bad = True
            else:
                rec_refs = {m.group(1) for m in EVIDENCE_REF_RE.finditer(scope)}
                strong = sorted(r for r in rec_refs if grades.get(r) in strong_grades)
                if not strong:
                    print(f"FAIL: {stem} — 권고 절이 {sorted(strong_grades)} 등급 근거를 하나도 "
                          f"인용하지 않는다(인용: {sorted(rec_refs) or '없음'}). 핵심 권고는 높은 "
                          f"등급 근거에 뿌리내려야 한다")
                    bad = True
        if bad:
            fail = True
        else:
            print(f"  ✓ {stem} — 인용 {len(refs)}건"
                  + (f" · 권고 절 강근거 {strong}" if strong else ""))

    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
