#!/usr/bin/env python3
"""
객관 게이트: 테스트 실행 결과(Test Run)
=======================================
웹개발 아키타입(D)의 Test & Verify 단계에서 LLM 없이 **구현이 실제로 도는지**를 검사한다.

⚠️ 이 게이트는 **테스트를 실행하지 않는다.** Tester 가 남긴 기계 판독 결과
(`test/results.json`)를 검사할 뿐이다. 게이트키퍼가 미션 코드를 임의 실행하면
임의 코드 실행 통로가 되므로, 실행은 격리된 Tester profile 이 하고 게이트는 **판정만** 한다.
결과 파일이 없거나 형식이 깨졌으면 fail-closed(exit 2).

검사 항목
  1. 실패 케이스가 0인가                                    (require_e2e_green)
  2. 시나리오 id(S-xx) 전건이 pass 인가                      (require_scenario_coverage)
  3. 실행계획의 완료조건 체크박스가 모두 채워졌는가            (require_task_checkboxes)

results.json 스키마(최소)
  {"total": 12, "passed": 12, "failed": 0,
   "scenarios": {"S-01": "pass", "S-02": "fail|missing|skip"}}

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.completion_policy)
  --sources <path>  : 미사용(규약상 항상 전달됨)
  --draft   <path>  : test/results.json. 이 파일 기준으로 미션 루트를 거슬러 올라가
                      spec/(시나리오·실행계획)을 찾는다.

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
SCN_RE = re.compile(r"\bS-(\d{1,3})\b")
UNCHECKED_RE = re.compile(r"^\s*[-*]\s*\[ \]", re.M)
CHECKED_RE = re.compile(r"^\s*[-*]\s*\[[xX]\]", re.M)
PASS_WORDS = {"pass", "passed", "ok", "green", "true"}


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("completion_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("completion_policy", {}) or {}


def find_spec_doc(start_dir: str, *needles: str) -> str | None:
    """results.json 위치에서 최대 3단계 위까지 올라가며 spec/ 안의 문서를 찾는다."""
    d = os.path.abspath(start_dir)
    for _ in range(4):
        spec = os.path.join(d, "spec")
        if os.path.isdir(spec):
            for n in sorted(os.listdir(spec)):
                low = n.lower()
                if low.endswith(".md") and any(x in low for x in needles):
                    return os.path.join(spec, n)
        d = os.path.dirname(d)
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", default=None, help="미사용(gate_keeper 규약상 전달됨)")
    ap.add_argument("--draft", default=None, help="test/results.json")
    args = ap.parse_args()

    if not args.draft:
        print("FAIL(usage): --draft(test/results.json) 필수 — fail-closed", file=sys.stderr); return 2
    try:
        policy = load_policy(args.policy)
        res = json.loads(open(args.draft, encoding="utf-8").read())
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): results.json 없음/형식오류 ({e}) — fail-closed", file=sys.stderr); return 2
    if not isinstance(res, dict):
        print("FAIL(usage): results.json 최상위가 객체가 아니다 — fail-closed", file=sys.stderr); return 2

    need_green = bool(policy.get("require_e2e_green", True))
    need_cov = bool(policy.get("require_scenario_coverage", True))
    need_boxes = bool(policy.get("require_task_checkboxes", True))

    total = int(res.get("total") or 0)
    failed = int(res.get("failed") or 0)
    passed = int(res.get("passed") or 0)
    scen = res.get("scenarios") or {}
    if not isinstance(scen, dict):
        print("FAIL(usage): scenarios 가 객체가 아니다 — fail-closed", file=sys.stderr); return 2

    print(f"policy: e2e_green={need_green} scenario_coverage={need_cov} task_checkboxes={need_boxes}")
    print(f"results: total={total} passed={passed} failed={failed} scenarios={len(scen)}")

    fail = False
    if total <= 0:
        print("FAIL: 실행된 테스트가 0건이다 — 통과로 볼 수 없다(fail-closed).", file=sys.stderr)
        return 1
    if failed > 0 and need_green:
        print(f"FAIL: 실패 케이스 {failed}건")
        fail = True

    # 선언된 시나리오 전건이 pass 인가 (spec/3-scenarios.md 를 진실로 삼는다)
    scn_doc = find_spec_doc(os.path.dirname(os.path.abspath(args.draft)), "scenario", "시나리오")
    if need_cov:
        if not scn_doc:
            print("FAIL(usage): spec/ 에서 시나리오 문서를 찾지 못함 — 커버리지 검증 불가(fail-closed)",
                  file=sys.stderr)
            return 2
        declared = {str(int(m)) for m in SCN_RE.findall(open(scn_doc, encoding="utf-8").read())}
        reported = {str(int(m)): str(v).lower()
                    for k, v in scen.items() for m in SCN_RE.findall(str(k))}
        not_passed = sorted([s for s in declared if reported.get(s) not in PASS_WORDS], key=int)
        print(f"scenario coverage: {len(declared) - len(not_passed)}/{len(declared)} "
              f"(선언={os.path.basename(scn_doc)})")
        if not declared:
            print("FAIL: 시나리오 문서에서 S-id 를 찾지 못했다(fail-closed).", file=sys.stderr)
            return 1
        if not_passed:
            print(f"미통과·미커버 시나리오: {['S-%02d' % int(s) for s in not_passed]}")
            fail = True

    # 실행계획 체크박스 — 미체크가 남아 있으면 구현 미완
    if need_boxes:
        plan = find_spec_doc(os.path.dirname(os.path.abspath(args.draft)), "plan", "실행계획")
        if not plan:
            print("FAIL(usage): spec/ 에서 실행계획 문서를 찾지 못함 — fail-closed", file=sys.stderr)
            return 2
        text = open(plan, encoding="utf-8").read()
        done, todo = len(CHECKED_RE.findall(text)), len(UNCHECKED_RE.findall(text))
        print(f"plan checkboxes: {done} 완료 / {todo} 미완 ({os.path.basename(plan)})")
        if done + todo == 0:
            print("FAIL: 실행계획에 완료조건 체크박스가 없다 — 계약 부재(fail-closed).", file=sys.stderr)
            return 1
        if todo > 0:
            print(f"FAIL: 미완 체크박스 {todo}건")
            fail = True

    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
