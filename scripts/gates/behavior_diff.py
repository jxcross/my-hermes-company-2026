#!/usr/bin/env python3
"""
객관 게이트: 행동 동등성(Behavior Diff)
=========================================
마이그레이션 전후의 행동 차이가 **계획에 선언된 의도적 변경뿐인지** LLM 없이 검사한다.
출처: other_projects/harness-templates/.../migrateforge/scripts/behavior_diff.py (GATE 2)

⚠️ 이식하며 고친 것 — **원본은 계획을 읽고도 쓰지 않는다** (docs/13 §5):
  1. **자기 신고가 곧 판정이었다** — docstring 은 "any behavior diffs found are explicitly
     accounted for **in 03-plan**" 을 검증한다고 선언하는데, 코드는 `plan_text` 를 읽어
     **변수에 담아 놓고 한 번도 참조하지 않는다**(죽은 변수). 실제 판정은
     `acceptable: yes` 한 줄뿐이다 — **바꾼 쪽이 스스로 '괜찮다'고 적으면 통과**한다.
     → 각 차이가 계획의 ```intentional``` 블록에 **선언된 id 를 참조**해야 인정한다.
  2. **`"yes" in acceptable`** — `acceptable: not yes` 도, `acceptable: yes, 확인 안 함` 도
     통과한다. → 정확히 `yes`/`true` 만 인정.
  3. **차이가 0건이면 무조건 통과** — 행동 지문을 하나도 실행하지 못했어도 PASS 다.
     빈 검사는 통과가 아니다. → 기준선이 선언한 지문 케이스 수와 대조해 **커버리지**를 본다.

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.behavior_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : verify/ 디렉터리(diff.md) 또는 diff.md

계획·기준선은 미션 루트의 `plan.md` · `baseline.md` 에서 읽는다.

기대 형식
  baseline.md : ```fingerprint\n- case: f1\n  input: ...\n  output: ...\n```
  plan.md     : ```intentional\n- id: ic1\n  change: Py3 에서 문자열은 bytes 가 아니다\n```
  diff.md     : ```diffs\n- entry: f3\n  acceptable: yes\n  intentional_id: ic1\n
                reason: 계획된 문자열 타입 변경\n```

정책 필드(behavior_policy)
  require_intentional_ref (기본 true) · min_case_coverage (기본 1.0)
  plan_file · baseline_file

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
ACCEPT_OK = {"yes", "true", "y", "예"}


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("behavior_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("behavior_policy", {}) or {}


def parse_items(text: str, block: str, id_field: str) -> list[dict]:
    m = re.search(BLOCK_RE.format(block), text, re.DOTALL)
    if not m:
        return []
    items, current = [], None
    for line in m.group(1).splitlines():
        mi = re.match(rf"^\s*-\s+{re.escape(id_field)}:\s*(.+)$", line)
        if mi:
            if current:
                items.append(current)
            current = {id_field: mi.group(1).strip().strip('"\'')}
            continue
        if current is None:
            continue
        mf = re.match(r"^\s+(\w+):\s*(.*)$", line)
        if mf:
            current[mf.group(1)] = mf.group(2).strip().strip('"\'')
    if current:
        items.append(current)
    return items


def read(path: str) -> str:
    return open(path, encoding="utf-8").read() if os.path.isfile(path) else ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", default=None, help="미사용(gate_keeper 규약상 전달됨)")
    ap.add_argument("--draft", default=None, help="verify/ 디렉터리 또는 diff.md")
    args = ap.parse_args()

    if not args.draft or not os.path.exists(args.draft):
        print("FAIL(usage): --draft(verify/) 필요 — fail-closed", file=sys.stderr); return 2
    try:
        policy = load_policy(args.policy)
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e} — fail-closed", file=sys.stderr); return 2

    if os.path.isdir(args.draft):
        diff_path = os.path.join(args.draft, "diff.md")
        root = os.path.dirname(os.path.abspath(args.draft))
    else:
        diff_path = args.draft
        root = os.path.dirname(os.path.dirname(os.path.abspath(args.draft)))
    if not os.path.isfile(diff_path):
        print(f"FAIL(usage): 행동 차이 보고가 없다({diff_path}) — fail-closed", file=sys.stderr)
        return 2

    plan_path = os.path.join(root, policy.get("plan_file") or "plan.md")
    base_path = os.path.join(root, policy.get("baseline_file") or "baseline.md")
    for p in (plan_path, base_path):
        if not os.path.isfile(p):
            print(f"FAIL(usage): 필요한 산출물이 없다({p}) — fail-closed", file=sys.stderr)
            return 2

    diff_text = read(diff_path)
    cases = parse_items(read(base_path), "fingerprint", "case")
    intentional = parse_items(read(plan_path), "intentional", "id")
    diffs = parse_items(diff_text, "diffs", "entry")

    if not cases:
        print(f"FAIL(usage): 기준선에 행동 지문(```fingerprint```)이 없다 — 비교 대상 없이 "
              f"'차이 0건'은 의미가 없다. fail-closed", file=sys.stderr)
        return 2

    require_ref = bool(policy.get("require_intentional_ref", True))
    min_cov = float(policy.get("min_case_coverage", 1.0))
    known_ic = {i.get("id") for i in intentional}

    # 실행된 케이스 = diff 보고가 명시한 checked 목록(없으면 diffs 의 entry 로 추정)
    m = re.search(r"^\s*checked_cases\s*:\s*(\d+)\s*$", diff_text, re.MULTILINE)
    checked = int(m.group(1)) if m else len({d.get("entry") for d in diffs})
    coverage = checked / len(cases) if cases else 0.0

    print(f"기준선 지문 {len(cases)}건 · 재실행 {checked}건(커버리지 {coverage:.0%}, "
          f"하한 {min_cov:.0%}) · 보고된 차이 {len(diffs)}건 · 계획된 의도 변경 {len(known_ic)}건")

    fail = False
    if coverage < min_cov:
        print(f"FAIL: 행동 지문 재실행 커버리지 {coverage:.0%} < {min_cov:.0%} — "
              f"실행하지 않은 케이스는 '차이 없음'이 아니다(원본은 차이 0건이면 무조건 통과)")
        print(f"      diff.md 상단에 `checked_cases: {len(cases)}` 를 적어라")
        fail = True

    unexplained, bad_ref = [], []
    for d in diffs:
        entry = d.get("entry", "?")
        acc = str(d.get("acceptable", "")).strip().lower()
        if acc not in ACCEPT_OK:
            unexplained.append((entry, d.get("reason", "(사유 없음)")))
            continue
        if require_ref:
            ic = d.get("intentional_id")
            if not ic or ic not in known_ic:
                bad_ref.append((entry, ic or "(미선언)"))
    if unexplained:
        print(f"FAIL: 설명되지 않은 행동 변화 {len(unexplained)}건 — 마이그레이션이 동작을 "
              f"바꿨다")
        for e, r in unexplained[:5]:
            print(f"       · {e}: {r}")
        fail = True
    if bad_ref:
        print(f"FAIL: '의도된 변경'이라면서 계획의 ```intentional``` 항목을 참조하지 않는다 "
              f"{bad_ref[:5]}")
        print(f"      원본은 계획을 읽어 놓고 **한 번도 참조하지 않았다**(죽은 변수) — "
              f"바꾼 쪽이 스스로 '괜찮다'고 적으면 통과했다")
        fail = True

    if not fail:
        print("  ✓ 행동 동등 · 예외는 전부 계획에 선언됨")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
