#!/usr/bin/env python3
"""
객관 게이트: 학습목표(LO) 커버리지
====================================
정의된 학습목표가 **주차 구조와 평가 양쪽에** 실제로 배치됐는지, 그리고 **빈 주차가 없는지**
LLM 없이 검사한다.
출처: other_projects/harness-templates/.../lectureforge/scripts/objective_coverage.py (GATE 1)

⚠️ 이식하며 고친 것 · 보강한 것 (docs/13 §5):
  1. **한국어에서 LO 참조를 못 읽었다** — `\\blo\\d+\\b` 는 `lo3을`·`lo4에서` 처럼 조사가 붙으면
     실패한다(실측: `[]`). → lookaround 로 교체.
  2. **스치는 언급도 커버리지로 셌다** — 원본은 블록 안 어디에 있든 `loN` 토큰이면 배치된
     것으로 봤다. 주석에 `# lo5 는 다음 학기` 라고 써도 커버된다. → 주차·평가 항목의
     **`los:` 필드에 선언된 것만** 인정한다.
  3. **역방향 검사가 없었다** — 모든 LO 가 1주차에 몰려 있어도 통과했다. **모든 주차가
     최소 1개 LO 를 가져야** 한다(LO 없는 주차는 목표 없는 수업이다).
  4. **LO 개수 범위가 강제되지 않았다** — 원본 CLAUDE.md 는 5~10개를 기본값으로 적어 두고
     검사하지 않는다. LO 를 2개만 정의하면 커버리지가 저절로 쉬워진다(docforge 의
     '분모 자기결정' 과 같은 계열 — §5). → `min_los`·`max_los` 로 강제한다.

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.objective_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : objectives.md

주차 구조와 평가 계획은 미션 루트의 `structure.md` · `assessment.md` 에서 읽는다.

기대 형식
  objectives.md:  ```objectives\\n- id: lo1\\n  bloom: apply\\n  statement: ...\\n```
  structure.md:   ```units\\n- week: 1\\n  title: 개요\\n  los: [lo1, lo2]\\n```
  assessment.md:  ```assignments|quizzes|exams``` 각 항목에 `los: [...]`

정책 필드(objective_policy)
  min_los (5) · max_los (10) · require_every_unit_has_lo (true)
  structure_file · assessment_file

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
BLOCK_RE = r"```{}\s*\n(.*?)\n```"
# ⚠️ \b 금지 — 한국어 조사(`lo3을`)에서 무너진다.
LO_RE = re.compile(r"(?<![0-9A-Za-z])(lo\d+)(?![0-9A-Za-z])", re.IGNORECASE)
ID_LINE_RE = re.compile(r"^\s*-\s+id:\s*(lo\d+)", re.MULTILINE | re.IGNORECASE)
LOS_FIELD_RE = re.compile(r"^\s*los:\s*(.+?)\s*$", re.MULTILINE | re.IGNORECASE)


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("objective_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("objective_policy", {}) or {}


def block(text: str, name: str) -> str | None:
    m = re.search(BLOCK_RE.format(name), text, re.DOTALL)
    return m.group(1) if m else None


def defined_los(objectives_text: str) -> list[str]:
    b = block(objectives_text, "objectives")
    return [x.lower() for x in ID_LINE_RE.findall(b)] if b else []


def entries_with_los(blk: str) -> list[tuple[str, set[str]]]:
    """블록을 항목 단위로 쪼개 (항목 라벨, 선언된 LO 집합) 목록을 만든다.
    ⚠️ `los:` 필드에 선언된 것만 센다 — 스치는 언급을 배치로 인정하면 게이트가 무의미해진다."""
    out = []
    chunks = re.split(r"\n(?=\s*-\s+\w)", blk)
    for ch in chunks:
        if not ch.strip():
            continue
        label = ch.strip().splitlines()[0].strip()[:40]
        los: set[str] = set()
        for m in LOS_FIELD_RE.finditer(ch):
            los |= {x.lower() for x in LO_RE.findall(m.group(1))}
        out.append((label, los))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", default=None, help="미사용(gate_keeper 규약상 전달됨)")
    ap.add_argument("--draft", default=None, help="objectives.md")
    args = ap.parse_args()

    if not args.draft or not os.path.isfile(args.draft):
        print("FAIL(usage): --draft(objectives.md) 필요 — fail-closed", file=sys.stderr); return 2
    try:
        policy = load_policy(args.policy)
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e} — fail-closed", file=sys.stderr); return 2

    root = os.path.dirname(os.path.abspath(args.draft))
    st_path = os.path.join(root, policy.get("structure_file") or "structure.md")
    as_path = os.path.join(root, policy.get("assessment_file") or "assessment.md")
    for p in (st_path, as_path):
        if not os.path.isfile(p):
            print(f"FAIL(usage): 필요한 산출물이 없다({p}) — fail-closed", file=sys.stderr)
            return 2

    defined = defined_los(open(args.draft, encoding="utf-8").read())
    if not defined:
        print(f"FAIL(usage): 학습목표를 읽지 못했다({args.draft}) — ```objectives``` 블록에 "
              f"`- id: lo1` 이 필요하다. fail-closed", file=sys.stderr)
        return 2

    min_los = int(policy.get("min_los", 5))
    max_los = int(policy.get("max_los", 10))
    require_unit_lo = bool(policy.get("require_every_unit_has_lo", True))

    units_blk = block(open(st_path, encoding="utf-8").read(), "units")
    if units_blk is None:
        print(f"FAIL(usage): {os.path.basename(st_path)} 에 ```units``` 블록이 없다 — fail-closed",
              file=sys.stderr)
        return 2
    units = entries_with_los(units_blk)

    asm_text = open(as_path, encoding="utf-8").read()
    asm_entries = []
    for name in ("assignments", "quizzes", "exams"):
        b = block(asm_text, name)
        if b:
            asm_entries += [(f"{name}:{lbl}", los) for lbl, los in entries_with_los(b)]
    if not asm_entries:
        print(f"FAIL(usage): {os.path.basename(as_path)} 에 평가 블록이 없다"
              f"(```assignments|quizzes|exams```) — fail-closed", file=sys.stderr)
        return 2

    in_units = set().union(*[s for _l, s in units]) if units else set()
    in_asm = set().union(*[s for _l, s in asm_entries]) if asm_entries else set()
    dset = set(defined)

    print(f"학습목표 {len(defined)}개(범위 {min_los}~{max_los}) · 주차 {len(units)}개 "
          f"· 평가 {len(asm_entries)}건")

    fail = False
    if not (min_los <= len(defined) <= max_los):
        print(f"FAIL: 학습목표 개수 {len(defined)} 가 범위 {min_los}~{max_los} 밖이다 "
              f"— 너무 적으면 커버리지가 저절로 쉬워지고, 너무 많으면 한 학기에 못 담는다")
        fail = True

    miss_u = sorted(dset - in_units)
    miss_a = sorted(dset - in_asm)
    if miss_u:
        print(f"FAIL: 어느 주차에도 배치되지 않은 학습목표 {miss_u} "
              f"— 주차 항목의 `los:` 필드에 선언해야 인정된다")
        fail = True
    if miss_a:
        print(f"FAIL: 어느 평가에도 연결되지 않은 학습목표 {miss_a} "
              f"— 측정하지 않는 목표는 목표가 아니다")
        fail = True

    if require_unit_lo:
        empty = [lbl for lbl, los in units if not los]
        if empty:
            print(f"FAIL: 학습목표가 없는 주차 {len(empty)}건: {empty[:6]} "
                  f"— 목표 없는 수업 주차는 설계 누락이다(원본에 없던 역방향 검사)")
            fail = True

    ghost = sorted((in_units | in_asm) - dset)
    if ghost:
        print(f"FAIL: 정의되지 않은 학습목표를 참조한다 {ghost} — objectives.md 에 정의하라")
        fail = True

    if not fail:
        print(f"  ✓ 전 목표가 주차·평가 양쪽에 배치 · 빈 주차 없음")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
