#!/usr/bin/env python3
"""
객관 게이트: 이해관계자 커버리지
=================================
`context.md` 가 식별한 이해관계자가 정책 산출물에서 **실제로 다뤄졌는지** LLM 없이 검사한다.
출처: other_projects/harness-templates/.../policyforge/scripts/stakeholder_check.py (GATE 3)

⚠️ 이식하며 고친 것 · 보강한 것 (docs/13 §5):
  1. **한국어에서 id 매칭이 무너졌다** — `\\b{sid}\\b` 는 `s1의`·`s3에` 처럼 조사가 붙으면
     `1`↔`의` 사이에 경계가 없어(둘 다 \\w) 실패한다. → lookaround 로 교체.
  2. **이해관계자 '언급'과 '분석'을 구별하지 못했다** — 원본은 이름이 한 번이라도 나오면
     covered 로 봤다. 우리는 context.md 쪽에서 `interest`·`position` 이 비어 있으면
     FAIL 로 잡는다(CLAUDE.md 의 "영향 받는 집단의 이해·의견 명시" 요구를 기계화).
  3. **핵심 문서 강제** — 원본은 "아무 문서에나 나오면 통과"였다. 정책 보고서(report)처럼
     전수 분석이 목적인 산출물은 `require_in` 으로 전 이해관계자를 요구할 수 있게 했다.

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.stakeholder_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : formats/ 디렉터리 또는 단일 문서

이해관계자 목록은 미션 루트의 `context.md` 에서 읽는다(draft 의 상위 디렉터리).
  ```stakeholders
  - id: s1
    name: 중소기업
    category: industry
    interest: 규제 준수 비용
    position: 유예기간 요구
  ```

정책 필드(stakeholder_policy)
  context_file (기본 context.md) · require_in (기본 []) — 이 문서들에는 전원이 등장해야 한다
  require_fields (기본 [interest, position]) · min_name_len (기본 2)

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
STAKEHOLDERS_BLOCK_RE = re.compile(r"```stakeholders\s*\n(.*?)\n```", re.DOTALL)
ID_LINE_RE = re.compile(r"^\s*-\s+id:\s*(\S+)")
FIELD_LINE_RE = re.compile(r"^\s+(\w+):\s*(.*)$")
DEFAULT_REQUIRE_FIELDS = ["interest", "position"]


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("stakeholder_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("stakeholder_policy", {}) or {}


def parse_stakeholders(context_path: str) -> list[dict]:
    try:
        text = open(context_path, encoding="utf-8").read()
    except OSError:
        return []
    m = STAKEHOLDERS_BLOCK_RE.search(text)
    if not m:
        return []
    out: list[dict] = []
    current: dict | None = None
    for line in m.group(1).splitlines():
        m_id = ID_LINE_RE.match(line)
        if m_id:
            if current:
                out.append(current)
            current = {"id": m_id.group(1)}
            continue
        if current is None:
            continue
        m_f = FIELD_LINE_RE.match(line)
        if m_f:
            current[m_f.group(1)] = m_f.group(2).strip().strip('"\'')
    if current:
        out.append(current)
    return out


def id_ref_re(sid: str) -> re.Pattern:
    """⚠️ \\b 금지 — 한국어 조사(`s1의`)에서 무너진다."""
    return re.compile(rf"(?<![0-9A-Za-z]){re.escape(sid)}(?![0-9A-Za-z])")


def covered_in(s: dict, text: str, min_name_len: int) -> bool:
    sid = s.get("id", "")
    if sid and id_ref_re(sid).search(text):
        return True
    name = s.get("name", "")
    return bool(name) and len(name) >= min_name_len and name in text


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

    context_path = os.path.join(mission_root(args.draft), policy.get("context_file") or "context.md")
    stakeholders = parse_stakeholders(context_path)
    if not stakeholders:
        print(f"FAIL(usage): 이해관계자 목록을 읽지 못했다({context_path}) — "
              f"```stakeholders``` 블록에 `- id:` 가 필요하다. fail-closed", file=sys.stderr)
        return 2

    require_in = [str(x).lower() for x in (policy.get("require_in") or [])]
    require_fields = policy.get("require_fields") or DEFAULT_REQUIRE_FIELDS
    min_name_len = int(policy.get("min_name_len", 2))

    texts: dict[str, str] = {}
    for path in files:
        stem = os.path.basename(path).rsplit(".md", 1)[0].lower()
        try:
            texts[stem] = open(path, encoding="utf-8").read()
        except OSError as e:
            print(f"FAIL(usage): {path} 읽기 실패 ({e}) — fail-closed", file=sys.stderr)
            return 2

    print(f"이해관계자 {len(stakeholders)}명 · 정책 문서 {len(texts)}건({', '.join(sorted(texts))}) "
          f"· 전원 등장 요구 문서={require_in or '없음'}")

    fail = False

    # ① context.md 기재 충실도 — 이해·입장이 비면 '분석했다'고 할 수 없다.
    thin = [(s.get("id"), f) for s in stakeholders for f in require_fields if not s.get(f)]
    if thin:
        print(f"FAIL: context.md 기재 누락 {len(thin)}건 — {thin[:6]}")
        print(f"      이해관계자마다 {require_fields} 를 채워야 한다(단순 나열은 분석이 아니다)")
        fail = True

    # ② 커버리지 매트릭스
    uncovered, missing_required = [], []
    for s in stakeholders:
        hits = [f for f, t in texts.items() if covered_in(s, t, min_name_len)]
        label = f"{s.get('id')}({s.get('name', '')})"
        if not hits:
            uncovered.append(label)
        for f in require_in:
            if f in texts and f not in hits:
                missing_required.append(f"{label}→{f}")
        print(f"  {'✓' if hits else '✗'} {label:28s} {sorted(hits) or '어느 문서에도 없음'}")

    if uncovered:
        print(f"FAIL: 어느 정책 문서에도 등장하지 않는 이해관계자 {len(uncovered)}명: {uncovered}")
        fail = True
    if missing_required:
        print(f"FAIL: 전수 분석 문서에서 누락 {len(missing_required)}건: {missing_required}")
        fail = True

    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
