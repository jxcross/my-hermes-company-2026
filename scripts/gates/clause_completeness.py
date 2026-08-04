#!/usr/bin/env python3
"""
객관 게이트: 필수 조항 완전성
==============================
문서 종류(계약서·의견서·자문서·약관)별 표준 필수 조항과 도메인 추가 조항이 실제 문서에
**절(節)로** 존재하는지 LLM 없이 검사한다.
출처: other_projects/harness-templates/.../legalforge/scripts/clause_completeness.py (HARD GATE)

⚠️ **원본은 통째로 고장나 있었다** (docs/13 §5):
   `rf"^#{{1,3}}\\s+..."` 가 **raw f-string** 이라 `{{1,3}}` 이 정규식 수량자가 아니라
   **f-string 보간**으로 평가된다 → 튜플 `(1, 3)` → 실제 패턴은 `^#(1, 3)\\s+…`.
   **어떤 제목에도 매칭되지 않는다.** 결과: 완벽한 계약서를 넣어도 모든 조항이 '누락' 으로
   판정돼 **하드게이트가 항상 FAIL** 하고 finalize 가 영원히 차단된다.
   → 수량자를 f-string 밖으로 빼고(문자열 결합), 조항 별칭·부재 검사를 추가했다.

이식하며 보강한 것
  · **조항 명칭 별칭** — '대가'를 '용역대금'·'보수'로 쓰는 것은 정상이다. 정책에서 별칭 선언.
  · **선언된 문서의 부재** — 원본은 파일이 없으면 누락 1건으로만 셌다. 명시 FAIL 로.
  · **조항 taxonomy 를 정책으로** — 원본은 `standard_clause_lib.py` 에 하드코딩. 우리는
    템플릿 policy 소유(도메인마다 갈아끼운다 — docs/13 §2⑦).

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.clause_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : docs/ 디렉터리(문서종류별 <doc_type>.md) 또는 단일 문서

정책 필드(clause_policy)
  doc_types · domain            : SCOPE.md frontmatter 의 `doc_types:`·`domain:` 이 우선
  required_clauses  : {contract: [...], opinion: [...], ...}
  domain_clauses    : {contract: {it_sw: [...], employment: [...]}, ...}
  aliases           : {대가: [용역대금, 보수, 지급], ...}

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

# 조항이 '절' 로 존재하는지 보는 제목 형태들. ⚠️ 수량자 {1,6} 은 f-string 밖에 둔다 —
# 원본이 바로 이 지점에서 무너졌다(raw f-string 안의 {1,3} 이 보간돼 정규식이 깨졌다).
HEADING = r"^\s{0,3}#{1,6}\s*"
BOLD_LINE = r"^\s{0,3}\*\*\s*"          # **제5조 (해지)** 처럼 굵은 글씨로 절을 여는 서식
ARTICLE = r"(?:제\s*\d+\s*조(?:의\s*\d+)?)?\s*"
OPEN = r"[\(（\[「]?\s*"


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("clause_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("clause_policy", {}) or {}


def scope_field(root: str, key: str):
    """SCOPE.md frontmatter 값(있으면 정책 기본값보다 우선)."""
    try:
        m = FRONTMATTER_RE.match(open(os.path.join(root, "SCOPE.md"), encoding="utf-8").read())
    except OSError:
        return None
    if not m:
        return None
    return (yaml.safe_load(m.group(1)) or {}).get(key)


def strip_frontmatter(text: str) -> str:
    return FRONTMATTER_RE.sub("", text, count=1)


def clause_patterns(label: str) -> list[re.Pattern]:
    """조항 라벨이 **절 제목으로** 등장하는지 보는 패턴들.
    본문 중 스치듯 언급된 단어는 조항이 아니다 — 제목·굵은줄만 인정한다."""
    lab = re.escape(label)
    return [re.compile(p, re.MULTILINE) for p in (
        HEADING + ARTICLE + OPEN + lab,          # ## 제5조 (해지)  ·  ### 해지
        HEADING + r".*[\(（]\s*" + lab + r"\s*[\)）]",   # ## 제5조 (해지) 형태 일반
        HEADING + r"\d+\s*[.)]\s*" + lab,        # ## 1. 당사자
        BOLD_LINE + ARTICLE + OPEN + lab,        # **제5조 (해지)**
    )]


def clause_present(label: str, aliases: dict, body: str) -> str | None:
    """존재하면 실제로 쓰인 이름(별칭 포함)을 반환, 없으면 None."""
    for name in [label] + list(aliases.get(label, []) or []):
        if any(p.search(body) for p in clause_patterns(name)):
            return name
    return None


def doc_files(draft: str) -> dict[str, str]:
    if os.path.isdir(draft):
        return {f.rsplit(".md", 1)[0].lower(): os.path.join(draft, f)
                for f in sorted(os.listdir(draft)) if f.endswith(".md")}
    if os.path.isfile(draft):
        return {os.path.basename(draft).rsplit(".md", 1)[0].lower(): draft}
    return {}


def mission_root(draft: str) -> str:
    p = os.path.abspath(draft)
    return os.path.dirname(p) if os.path.isdir(p) else os.path.dirname(os.path.dirname(p))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", default=None, help="미사용(gate_keeper 규약상 전달됨)")
    ap.add_argument("--draft", default=None, help="docs/ 디렉터리 또는 단일 문서")
    args = ap.parse_args()

    if not args.draft:
        print("FAIL(usage): --draft(docs/) 필수 — fail-closed", file=sys.stderr); return 2
    try:
        policy = load_policy(args.policy)
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e} — fail-closed", file=sys.stderr); return 2

    present = doc_files(args.draft)
    if not present:
        print(f"FAIL(usage): 법률 문서를 찾지 못했다({args.draft}) — fail-closed", file=sys.stderr)
        return 2

    root = mission_root(args.draft)
    declared = scope_field(root, "doc_types") or policy.get("doc_types") or []
    if isinstance(declared, str):
        declared = [x.strip() for x in declared.split(",")]
    declared = [str(x).strip().lower() for x in declared]
    domain = str(scope_field(root, "domain") or policy.get("domain") or "general").strip().lower()
    required = policy.get("required_clauses") or {}
    domain_map = policy.get("domain_clauses") or {}
    aliases = policy.get("aliases") or {}

    if not declared:
        print("FAIL(usage): 검사할 doc_types 가 없다 — SCOPE.md frontmatter 에 "
              "`doc_types: [contract, ...]` 를 선언하라. fail-closed", file=sys.stderr)
        return 2

    print(f"문서종류 {declared} · 도메인 {domain} · 존재 {sorted(present)}")

    fail = False
    for dt in declared:
        clauses = list(required.get(dt) or []) + list((domain_map.get(dt) or {}).get(domain) or [])
        if dt not in present:
            print(f"FAIL: 선언된 문서 {dt}.md 가 없다 — 병렬 집필 워커가 실패했을 수 있다")
            fail = True
            continue
        if not clauses:
            print(f"  ⚠ {dt}: 필수 조항이 정책에 선언되지 않았다(검사 생략)")
            continue
        try:
            body = strip_frontmatter(open(present[dt], encoding="utf-8").read())
        except OSError as e:
            print(f"FAIL: {dt} 읽기 실패 ({e})"); fail = True; continue

        found, missing = [], []
        for c in clauses:
            hit = clause_present(c, aliases, body)
            (found if hit else missing).append(hit or c)
        if missing:
            print(f"FAIL: {dt} 필수 조항 누락 {len(missing)}/{len(clauses)}건: {missing}")
            print(f"      (조항은 **절 제목**으로 있어야 한다 — '## 제N조 (해지)' 또는 '### 해지')")
            fail = True
        else:
            print(f"  ✓ {dt} 조항 {len(found)}/{len(clauses)}건 충족: {found}")

    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
