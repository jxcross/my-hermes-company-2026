#!/usr/bin/env python3
"""
객관 게이트: OWASP Top 10 감사 커버리지
=========================================
OWASP Top 10(2021) 10개 범주를 **실제로 점검했는지** LLM 없이 검사한다.
출처: other_projects/harness-templates/.../secforge/scripts/owasp_coverage.py (GATE 2)

⚠️ 이식하며 고친 것 (docs/13 §5):
  1. **문서 어딘가에 'A01' 이라는 글자만 있으면 통과했다** — `re.search(rf"\\b{cat}_?", text)`.
     `A01 A02 A03 … A10` 이라고 목차만 나열해도 **커버리지 100%** 다. 더 나쁜 것은
     "A01 은 점검하지 않았다" 라고 써도 covered 로 센다는 것이다. 점검했다는 증거가 아니라
     **글자의 존재**를 셌다.
  2. **입력이 없으면 통과했다(fail-open)** — 파일이 없을 때만 exit 2 이고, 내용이 비어 있으면
     10개 전부 missing 이라 FAIL 이 되긴 하지만, 반대로 **목차 한 줄로 통과**하는 쪽이 뚫려
     있었다. 보안 게이트는 **읽지 못하면 막아야 한다.**
  → 범주마다 **구조화된 항목**(status + 근거)을 요구한다. `audited` 는 근거를,
     `not_applicable` 은 사유를 반드시 동반해야 한다.

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.owasp_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : findings.md(```owasp``` 블록 포함) 또는 그 블록을 담은 문서

기대 형식
  ```owasp
  - id: A01
    name: 취약한 접근 통제
    status: audited            # audited | not_applicable
    findings: 2                # 발견 건수(0 도 유효한 감사 결과다)
    evidence: src/auth/ 라우트 권한 검사 전수 확인
  ```

정책 필드(owasp_policy)
  categories (기본 A01~A10) · allowed_status (기본 [audited, not_applicable])
  require_evidence (기본 true) · min_evidence_chars (기본 10)

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
OWASP_BLOCK_RE = re.compile(r"```owasp\s*\n(.*?)\n```", re.DOTALL)
DEFAULT_CATEGORIES = ["A01", "A02", "A03", "A04", "A05", "A06", "A07", "A08", "A09", "A10"]
DEFAULT_STATUS = ["audited", "not_applicable"]


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("owasp_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("owasp_policy", {}) or {}


def parse_entries(text: str) -> dict[str, dict]:
    m = OWASP_BLOCK_RE.search(text)
    if not m:
        return {}
    out: dict[str, dict] = {}
    current = None
    for line in m.group(1).splitlines():
        mi = re.match(r"^\s*-\s+id:\s*(\S+)", line)
        if mi:
            current = {"id": mi.group(1).strip().upper()}
            out[current["id"]] = current
            continue
        if current is None:
            continue
        mf = re.match(r"^\s+(\w+):\s*(.*)$", line)
        if mf:
            current[mf.group(1)] = mf.group(2).strip().strip('"\'')
    return out


def find_draft(draft: str) -> str | None:
    if os.path.isfile(draft):
        return draft
    if os.path.isdir(draft):
        for n in sorted(os.listdir(draft)):
            if n.endswith(".md") and OWASP_BLOCK_RE.search(
                    open(os.path.join(draft, n), encoding="utf-8").read()):
                return os.path.join(draft, n)
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", default=None, help="미사용(gate_keeper 규약상 전달됨)")
    ap.add_argument("--draft", default=None, help="```owasp``` 블록을 담은 문서 또는 디렉터리")
    args = ap.parse_args()

    if not args.draft:
        print("FAIL(usage): --draft 필수 — fail-closed", file=sys.stderr); return 2
    try:
        policy = load_policy(args.policy)
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e} — fail-closed", file=sys.stderr); return 2

    path = find_draft(args.draft)
    if not path:
        print(f"FAIL(usage): ```owasp``` 블록을 담은 문서를 찾지 못했다({args.draft}) "
              f"— **보안 게이트는 읽지 못하면 막는다.** fail-closed", file=sys.stderr)
        return 2

    entries = parse_entries(open(path, encoding="utf-8").read())
    if not entries:
        print(f"FAIL(usage): ```owasp``` 블록이 비었다({path}) — fail-closed", file=sys.stderr)
        return 2

    categories = [str(c).upper() for c in (policy.get("categories") or DEFAULT_CATEGORIES)]
    allowed = [str(s).lower() for s in (policy.get("allowed_status") or DEFAULT_STATUS)]
    require_ev = bool(policy.get("require_evidence", True))
    min_ev = int(policy.get("min_evidence_chars", 10))

    print(f"OWASP 범주 {len(categories)}개 · 기재 {len(entries)}건 · 허용 상태 {allowed}")

    fail = False
    n_findings = 0
    for cat in categories:
        e = entries.get(cat)
        if not e:
            print(f"FAIL: {cat} 항목이 없다 — 목차에 글자만 있으면 통과하던 원본과 달리 "
                  f"**구조화된 항목**이 필요하다")
            fail = True
            continue
        status = str(e.get("status", "")).lower()
        if status not in allowed:
            print(f"FAIL: {cat} status 가 없거나 허용값이 아니다({status or '없음'}) "
                  f"— 허용: {allowed}")
            fail = True
            continue
        ev = e.get("evidence", "")
        if require_ev and len(ev) < min_ev:
            what = "점검 근거" if status == "audited" else "해당 없음 사유"
            print(f"FAIL: {cat}({status}) 에 {what}가 없다(또는 {min_ev}자 미만) "
                  f"— '점검했다'는 주장만으로는 감사가 아니다")
            fail = True
            continue
        if status == "audited":
            try:
                n_findings += int(e.get("findings", 0))
            except ValueError:
                print(f"FAIL: {cat} findings 가 정수가 아니다({e.get('findings')})")
                fail = True
                continue
        print(f"  ✓ {cat} {status}"
              + (f" · 발견 {e.get('findings', 0)}건" if status == "audited" else "")
              + f" · 근거 {len(ev)}자")

    extra = sorted(set(entries) - set(categories))
    if extra:
        print(f"WARNING: 정책에 없는 범주 항목 {extra} (무시함)")

    print(f"감사된 범주의 총 발견 {n_findings}건")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
