#!/usr/bin/env python3
"""
객관 게이트: 테스트 통과율 · 회귀
===================================
마이그레이션 후 테스트가 **기준선 대비 나빠지지 않았는지** LLM 없이 검사한다.
출처: other_projects/harness-templates/.../migrateforge/scripts/test_pass_rate.py (GATE 1)

⚠️ 이식하며 고친 것 — **원본의 가장 큰 구멍은 기준선을 안 본다는 것이다** (docs/13 §5):
  1. **회귀를 못 잡는다** — 원본은 통과율이 임계(95%) 이상이기만 하면 PASS 다. 마이그레이션
     **전에 100%(200/200)** 이던 것이 **후에 96%(192/200)** 가 돼도 통과한다. 8건이 깨졌는데
     "합격"이다. 마이그레이션 게이트의 존재 이유가 회귀 탐지인데 회귀를 못 본다.
     → 기준선(baseline.md)과 **대조**한다. 통과 건수가 줄면 FAIL.
  2. **분모를 스스로 줄일 수 있다** — 통과율의 분모는 실행한 테스트 수이고, 그 수는 산출물이
     적어 낸 값이다. **깨진 테스트를 지우면 통과율이 100% 가 된다.** (code-docs 에서 만난
     '분모 자기결정' 과 같은 계열 — §5.) → 기준선 대비 **테스트 수 감소**를 FAIL 로.
  3. **결과가 없으면 0.0 으로 계산돼 조용히 FAIL** — `parse_int_field` 는 필드가 없으면 0을
     돌려주므로, 보고 형식이 어긋나면 "0/0 → 0%" 라는 무의미한 판정이 나온다.
     → 필드 누락은 usage 오류(exit 2, fail-closed)로 구분한다.

⚠️ 이 게이트는 **테스트를 실행하지 않는다.** Tester profile 이 실행해 남긴 보고를 검사할
   뿐이다(게이트키퍼가 미션 코드를 실행하면 임의 코드 실행 통로가 된다 — docs/13 §7).
   따라서 자기보고 신뢰 구간이 남아 있고, 그 몫은 LLM 검증자(fact-checker)가 본다.

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.test_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : verify/ 디렉터리(regression.md · new-test.md) 또는 regression.md

기준선은 미션 루트의 `baseline.md` 에서 읽는다.

기대 형식(둘 다 `키: 정수` 줄)
  baseline.md   : n_tests_total: 200 / n_passed: 200
  regression.md : n_tests_total_after: 200 / n_passed_after: 198
  new-test.md   : n_new_tests_added: 12 / n_passed: 12

정책 필드(test_policy)
  threshold (기본 0.95) · allow_test_count_drop (기본 false)
  allow_pass_count_drop (기본 false) · baseline_file (기본 baseline.md)

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


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("test_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("test_policy", {}) or {}


def field(text: str, key: str) -> int | None:
    """`키: 정수` 를 찾는다. **없으면 None** — 원본처럼 0 으로 때우면 형식 오류가
    '0/0 = 0%' 라는 그럴듯한 판정으로 둔갑한다."""
    m = re.search(rf"^\s*{re.escape(key)}\s*:\s*(\d+)\s*$", text, re.MULTILINE)
    return int(m.group(1)) if m else None


def read(path: str) -> str:
    return open(path, encoding="utf-8").read() if os.path.isfile(path) else ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", default=None, help="미사용(gate_keeper 규약상 전달됨)")
    ap.add_argument("--draft", default=None, help="verify/ 디렉터리 또는 regression.md")
    args = ap.parse_args()

    if not args.draft or not os.path.exists(args.draft):
        print("FAIL(usage): --draft(verify/) 필요 — fail-closed", file=sys.stderr); return 2
    try:
        policy = load_policy(args.policy)
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e} — fail-closed", file=sys.stderr); return 2

    if os.path.isdir(args.draft):
        reg_path = os.path.join(args.draft, "regression.md")
        new_path = os.path.join(args.draft, "new-test.md")
        root = os.path.dirname(os.path.abspath(args.draft))
    else:
        reg_path = args.draft
        new_path = os.path.join(os.path.dirname(args.draft), "new-test.md")
        root = os.path.dirname(os.path.dirname(os.path.abspath(args.draft)))

    if not os.path.isfile(reg_path):
        print(f"FAIL(usage): 회귀 테스트 보고가 없다({reg_path}) — fail-closed", file=sys.stderr)
        return 2
    base_path = os.path.join(root, policy.get("baseline_file") or "baseline.md")
    if not os.path.isfile(base_path):
        print(f"FAIL(usage): 기준선이 없다({base_path}) — **비교 대상 없이는 회귀를 판정할 수 "
              f"없다.** fail-closed", file=sys.stderr)
        return 2

    base_text, reg_text = read(base_path), read(reg_path)
    b_total, b_passed = field(base_text, "n_tests_total"), field(base_text, "n_passed")
    a_total, a_passed = field(reg_text, "n_tests_total_after"), field(reg_text, "n_passed_after")
    missing = [k for k, v in (("baseline.n_tests_total", b_total), ("baseline.n_passed", b_passed),
                              ("regression.n_tests_total_after", a_total),
                              ("regression.n_passed_after", a_passed)) if v is None]
    if missing:
        print(f"FAIL(usage): 필수 수치 누락 {missing} — 형식이 어긋나면 '0/0 = 0%' 라는 "
              f"무의미한 판정이 나온다. fail-closed", file=sys.stderr)
        return 2

    n_total, n_passed = field(read(new_path), "n_new_tests_added"), field(read(new_path), "n_passed")
    n_total, n_passed = n_total or 0, n_passed or 0

    threshold = float(policy.get("threshold", 0.95))
    allow_count_drop = bool(policy.get("allow_test_count_drop", False))
    allow_pass_drop = bool(policy.get("allow_pass_count_drop", False))

    combined_total, combined_passed = a_total + n_total, a_passed + n_passed
    rate = combined_passed / combined_total if combined_total else 0.0

    print(f"기준선 {b_passed}/{b_total} · 마이그레이션 후 {a_passed}/{a_total} "
          f"· 신규 {n_passed}/{n_total}")
    print(f"합계 통과율 {combined_passed}/{combined_total} = {rate:.1%} (임계 {threshold:.0%})")

    fail = False
    if rate < threshold:
        print(f"FAIL: 통과율 {rate:.1%} < 임계 {threshold:.0%}")
        fail = True
    if not allow_pass_drop and a_passed < b_passed:
        print(f"FAIL: **회귀** — 통과 건수가 {b_passed} → {a_passed} 로 {b_passed - a_passed}건 "
              f"줄었다. 원본은 임계만 봐서 이것을 통과시켰다(100%→96% 도 '합격')")
        fail = True
    if not allow_count_drop and a_total < b_total:
        print(f"FAIL: 테스트 수가 {b_total} → {a_total} 로 {b_total - a_total}건 줄었다 "
              f"— 깨진 테스트를 지워 통과율을 올리는 경로를 막는다(분모 자기결정)")
        fail = True

    if not fail:
        print("  ✓ 회귀 없음 · 통과율 충족")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
