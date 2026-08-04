#!/usr/bin/env python3
"""
객관 게이트: PRISMA 카운트 일관성
=================================
체계적 문헌고찰(아키타입 B')의 선별 단계 산출물이 **산술적으로 앞뒤가 맞는지** LLM 없이 검사한다.
출처: other_projects/harness-templates/.../reviewforge/scripts/prisma_count_tracker.py
      (우리 gate_keeper CLI 규약 `--policy --sources --draft` 로 이식)

검사하는 항등식 (PRISMA 2020 flow)
    after_dedup            = identified − duplicates_removed
    eligibility_assessed   = after_dedup − excluded_screen
    included               = eligibility_assessed − excluded_eligibility
  + ```included``` 블록의 항목 수 == included
  + ```exclusion_reasons``` 합계 == excluded_eligibility

screening.md 가 담아야 할 형식
    ```prisma_counts
    identified: 412
    duplicates_removed: 88
    after_dedup: 324
    excluded_screen: 251
    eligibility_assessed: 73
    excluded_eligibility: 46
    included: 27
    ```
    ```included
    - bibkey: smith2023
    ```
    ```exclusion_reasons
    - reason: "non-empirical"  count: 14
    ```

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.prisma_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : screening.md

정책 필드(prisma_policy)
  strict_exclusion_reasons (기본 false) : exclusion_reasons 블록 부재를 FAIL 로 볼지

exit: 0 PASS · 1 FAIL · 2 usage/입력없음(fail-closed)
"""
from __future__ import annotations
import argparse
import json
import re
import sys

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML 필요", file=sys.stderr); sys.exit(2)

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
COUNTS_RE = re.compile(r"```prisma_counts\s*\n(.*?)\n```", re.DOTALL)
INCLUDED_RE = re.compile(r"```included\s*\n(.*?)\n```", re.DOTALL)
REASONS_RE = re.compile(r"```exclusion_reasons\s*\n(.*?)\n```", re.DOTALL)
BIBKEY_RE = re.compile(r"^\s*-\s+bibkey:\s*\S", re.M)

REQUIRED = ("identified", "duplicates_removed", "after_dedup", "excluded_screen",
            "eligibility_assessed", "excluded_eligibility", "included")


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("prisma_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("prisma_policy", {}) or {}


def parse_counts(block: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for line in block.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        k, _, v = line.partition(":")
        try:
            out[k.strip()] = int(v.strip())
        except ValueError:
            raise ValueError(f"정수가 아님: {k.strip()}={v.strip()!r}")
    return out


def parse_reasons(block: str) -> dict[str, int]:
    """'- reason: "X"  count: N' 형식. count 필수."""
    out: dict[str, int] = {}
    for line in block.splitlines():
        if not line.strip().startswith("-"):
            continue
        mr = re.search(r"reason:\s*\"?([^\"]+?)\"?\s+count:", line)
        mc = re.search(r"count:\s*(\d+)", line)
        if mr and mc:
            out[mr.group(1).strip()] = int(mc.group(1))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", default=None, help="미사용(gate_keeper 규약상 전달됨)")
    ap.add_argument("--draft", default=None, help="screening.md")
    args = ap.parse_args()

    if not args.draft:
        print("FAIL(usage): --draft(screening.md) 필수 — fail-closed", file=sys.stderr); return 2
    try:
        policy = load_policy(args.policy)
        text = open(args.draft, encoding="utf-8").read()
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e} — fail-closed", file=sys.stderr); return 2

    m = COUNTS_RE.search(text)
    if not m:
        print("FAIL: ```prisma_counts``` 블록이 없다 — 선별 단계가 카운트를 방출해야 한다.",
              file=sys.stderr)
        return 1
    try:
        counts = parse_counts(m.group(1))
    except ValueError as e:
        print(f"FAIL: prisma_counts 파싱 실패 — {e}", file=sys.stderr); return 1

    missing = [k for k in REQUIRED if k not in counts]
    if missing:
        print(f"FAIL: prisma_counts 키 누락: {missing}", file=sys.stderr); return 1

    issues: list[str] = []
    if counts["after_dedup"] != counts["identified"] - counts["duplicates_removed"]:
        issues.append(f"after_dedup {counts['after_dedup']} ≠ identified({counts['identified']}) "
                      f"− duplicates({counts['duplicates_removed']})")
    if counts["eligibility_assessed"] != counts["after_dedup"] - counts["excluded_screen"]:
        issues.append(f"eligibility_assessed {counts['eligibility_assessed']} ≠ "
                      f"after_dedup({counts['after_dedup']}) − excluded_screen({counts['excluded_screen']})")
    if counts["included"] != counts["eligibility_assessed"] - counts["excluded_eligibility"]:
        issues.append(f"included {counts['included']} ≠ eligibility_assessed"
                      f"({counts['eligibility_assessed']}) − excluded_eligibility"
                      f"({counts['excluded_eligibility']})")

    mi = INCLUDED_RE.search(text)
    if not mi:
        issues.append("```included``` 블록이 없다(선별 단계가 방출해야 한다)")
    else:
        n = len(BIBKEY_RE.findall(mi.group(1)))
        if n != counts["included"]:
            issues.append(f"```included``` 항목 {n}건 ≠ prisma_counts.included {counts['included']}")

    mr = REASONS_RE.search(text)
    if not mr:
        msg = "```exclusion_reasons``` 블록이 없다(PRISMA flow diagram 근거)"
        if policy.get("strict_exclusion_reasons", False):
            issues.append(msg)
        else:
            print(f"WARNING: {msg}")
    else:
        total = sum(parse_reasons(mr.group(1)).values())
        if total != counts["excluded_eligibility"]:
            issues.append(f"exclusion_reasons 합계 {total} ≠ excluded_eligibility "
                          f"{counts['excluded_eligibility']}")

    print("PRISMA counts:")
    for k in REQUIRED:
        print(f"  {k:24s} {counts[k]}")
    if issues:
        print("issues:")
        for i in issues:
            print(f"  - {i}")
    print("VERDICT:", "FAIL" if issues else "PASS")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
