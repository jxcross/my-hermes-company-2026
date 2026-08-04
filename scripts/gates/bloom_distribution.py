#!/usr/bin/env python3
"""
객관 게이트: Bloom 인지수준 분포
==================================
학습목표의 Bloom 단계 분포가 교육 수준에 맞는지 LLM 없이 검사한다.
출처: other_projects/harness-templates/.../lectureforge/scripts/bloom_check.py (GATE 2)

⚠️ 이식하며 고친 것 (docs/13 §5):
  1. **WARN 이 곧 FAIL 이었다** — docstring 은 "Remember+Understand ≤ 70% (**warn** else)"
     라 했지만 코드는 `return 0 if verdict == "PASS" else 1` 이라 WARN 도 exit 1 이다.
     하위 단계 비중이 조금 높은 입문 강의가 **하드 반려**된다(legalforge 의 law_citation 과
     같은 결함 — §5). → WARN 과 FAIL 을 정책에서 갈라 실제로 다르게 취급한다.
  2. **선언한 임계를 강제하지 않았다** — CLAUDE.md·docstring 은 "Evaluate+Create ≥ 10%"
     라고 적어 두고 코드는 **정확히 0% 일 때만** FAIL 이다. 5% 도 통과한다. → 임계를 정책에서
     읽어 실제로 적용한다.
  3. **한국어 Bloom 표기를 못 읽었다** — `bloom: 적용` 처럼 국문으로 쓰면 어느 단계에도
     세지 않고 조용히 분모에서 빠진다. → 국문 별칭을 넣었다.
  4. `^\\s+bloom:` — 들여쓰기가 **필수**라 최상위 표기를 놓쳤다. → 선택으로.

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.bloom_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : objectives.md

교육 수준은 미션 루트 `SCOPE.md` frontmatter 의 `education_level:` 이 우선한다.

정책 필드(bloom_policy)
  education_level (기본 undergraduate)
  levels: {undergraduate: {lower_max: 0.7, lower_is_fail: false, higher_min: 0.1}, ...}
    lower  = remember + understand · higher = evaluate + create
  require_all_levels_declared (기본 true) — 단계 미표기 LO 가 있으면 FAIL

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
OBJECTIVES_BLOCK_RE = re.compile(r"```objectives\s*\n(.*?)\n```", re.DOTALL)
ID_LINE_RE = re.compile(r"^\s*-\s+id:\s*(\S+)", re.MULTILINE)
BLOOM_LINE_RE = re.compile(r"^\s*bloom:\s*(\S+)", re.MULTILINE)   # 들여쓰기 선택

LEVELS = ("remember", "understand", "apply", "analyze", "evaluate", "create")
ALIASES = {
    "remember": "remember", "기억": "remember", "암기": "remember",
    "understand": "understand", "이해": "understand",
    "apply": "apply", "적용": "apply", "응용": "apply",
    "analyze": "analyze", "분석": "analyze",
    "evaluate": "evaluate", "평가": "evaluate",
    "create": "create", "창안": "create", "창조": "create", "종합": "create",
}
DEFAULT_LEVEL_POLICY = {
    "undergraduate": {"lower_max": 0.7, "lower_is_fail": False, "higher_min": 0.1},
    "graduate":      {"lower_max": 0.5, "lower_is_fail": False, "higher_min": 0.2},
    "adult":         {"lower_max": 0.7, "lower_is_fail": False, "higher_min": 0.0,
                      "remember_max": 0.3},
    "mooc":          {"lower_max": 0.8, "lower_is_fail": False, "higher_min": 0.0,
                      "remember_max": 0.3},
}


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("bloom_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("bloom_policy", {}) or {}


def scope_level(root: str) -> str | None:
    try:
        m = FRONTMATTER_RE.match(open(os.path.join(root, "SCOPE.md"), encoding="utf-8").read())
    except OSError:
        return None
    v = (yaml.safe_load(m.group(1)) or {}).get("education_level") if m else None
    return str(v).strip().lower() if v else None


def normalize(raw: str) -> str | None:
    key = str(raw).strip().strip('"\',').lower()
    return ALIASES.get(key)


def parse_objectives(text: str) -> list[tuple[str, str | None]]:
    """(LO id, 정규화된 bloom 단계) 목록. 단계 미표기는 None."""
    m = OBJECTIVES_BLOCK_RE.search(text)
    if not m:
        return []
    out = []
    for ch in re.split(r"\n(?=\s*-\s+id:)", m.group(1)):
        im = ID_LINE_RE.search(ch)
        if not im:
            continue
        bm = BLOOM_LINE_RE.search(ch)
        out.append((im.group(1).lower(), normalize(bm.group(1)) if bm else None))
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
    level = scope_level(root) or str(policy.get("education_level") or "undergraduate").lower()
    levels_cfg = policy.get("levels") or DEFAULT_LEVEL_POLICY
    cfg = levels_cfg.get(level) or DEFAULT_LEVEL_POLICY.get(level) \
        or DEFAULT_LEVEL_POLICY["undergraduate"]
    require_all = bool(policy.get("require_all_levels_declared", True))

    los = parse_objectives(open(args.draft, encoding="utf-8").read())
    if not los:
        print(f"FAIL(usage): 학습목표를 읽지 못했다({args.draft}) — fail-closed", file=sys.stderr)
        return 2

    undeclared = [i for i, b in los if b is None]
    counts = {l: 0 for l in LEVELS}
    for _i, b in los:
        if b:
            counts[b] += 1
    total = sum(counts.values())

    print(f"교육 수준 {level} · 학습목표 {len(los)}개(단계 표기 {total}개)")
    for l in LEVELS:
        pct = counts[l] / total * 100 if total else 0
        print(f"  {l:11s} {counts[l]:2d}  ({pct:5.1f}%)")

    fail = False
    if require_all and undeclared:
        print(f"FAIL: Bloom 단계가 표기되지 않은 학습목표 {undeclared} — 표기 누락은 분모에서 "
              f"조용히 빠져 분포를 왜곡한다(국문 표기 '적용'·'분석' 도 인정된다)")
        fail = True
    if total == 0:
        print("FAIL: 단계가 표기된 학습목표가 하나도 없다")
        print("VERDICT: FAIL")
        return 1

    lower = (counts["remember"] + counts["understand"]) / total
    higher = (counts["evaluate"] + counts["create"]) / total
    lower_max = float(cfg.get("lower_max", 0.7))
    higher_min = float(cfg.get("higher_min", 0.1))
    lower_is_fail = bool(cfg.get("lower_is_fail", False))

    print(f"  기억+이해 {lower:.1%} (상한 {lower_max:.0%}"
          f"{'·FAIL' if lower_is_fail else '·WARN'}) · "
          f"평가+창안 {higher:.1%} (하한 {higher_min:.0%}·FAIL)")

    if lower > lower_max:
        msg = (f"{'FAIL' if lower_is_fail else 'WARNING'}: 기억+이해 {lower:.1%} > "
               f"{lower_max:.0%} — 하위 인지단계에 치우쳤다(깊이 보강 권장)")
        print(msg)
        if lower_is_fail:
            fail = True
    if higher < higher_min:
        print(f"FAIL: 평가+창안 {higher:.1%} < {higher_min:.0%} — 고차 인지목표가 부족하다"
              f"(원본은 **정확히 0%** 일 때만 잡아 5% 도 통과시켰다)")
        fail = True
    rmax = cfg.get("remember_max")
    if rmax is not None:
        r = counts["remember"] / total
        if r > float(rmax):
            print(f"WARNING: 기억 {r:.1%} > {float(rmax):.0%} — 성인·MOOC 학습자에게 "
                  f"단순 암기 비중이 높다")

    if not fail:
        print("  ✓ 분포가 교육 수준 정책을 만족")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
