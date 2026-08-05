#!/usr/bin/env python3
"""
객관 게이트: 출처 다양성(Source Balance)
========================================
선별 소스가 정책상 카테고리 균형을 만족하는지 LLM 없이 검사한다.
harness-templates(trendforge)의 source_balance.py 를 이식하되 **카테고리를 정책에서
읽도록 일반화**(하드코딩 4종 제거). 우리 taxonomy 는 template policy 에 선언한다.
출처: other_projects/harness-templates/.../scripts/source_balance.py (표준 라이브러리만).

입력
  --policy <path>   : JSON(pipeline.json: policy.source_balance_policy) 또는 frontmatter .md/.yaml
  --sources <path>  : sources.yaml (각 항목 source_type 필드)
  --draft <path>    : (선택) 인용된 id 만 평가

정책 필드(source_balance_policy)
  categories: [academic, vendor, research_org, standards, news]   # 우리 taxonomy
  min_per_category: {academic: 2, vendor: 2, research_org: 1, ...}
  hard_block_if_missing: bool (기본 false) — min>0 인데 0건이면 FAIL

exit: 0 PASS · 1 FAIL · 2 usage/error
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
CITATION_RE = re.compile(r"\[([a-z][a-z0-9_\-]*)\]", re.IGNORECASE)


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("source_balance_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("source_balance_policy", {}) or {}


def load_sources(path: str) -> list[dict]:
    data = yaml.safe_load(open(path, encoding="utf-8").read())
    if isinstance(data, dict):
        data = data.get("sources", [])
    return [s for s in (data or []) if isinstance(s, dict)]


# ⚠️ **제외 어휘는 하나가 아니다.** 예전 코드는 `("failed","excluded")` 두 단어만 걸렀는데,
# `academic-paper` 템플릿은 curator 에게 **`status=selected/rejected` 로 판정하라**고 지시한다.
# 그래서 **선별에서 버린 자료가 정책 카운트에 그대로 잡혔다**(실측 2026-08-05 · M-2026-005).
# 게이트가 재는 것이 '수집한 것'이지 '선별한 것'이 아니게 된다 — 하한을 정확히 맞춘 수집에서
# 한 건만 버려져도 실제로는 미달인데 PASS 가 난다.
# 문서(템플릿 지시)와 코드(게이트)가 서로 다른 어휘를 말하면 규약을 지킨 쪽이 손해를 본다
# (docs/13 §5 의 거짓 FAIL 과 같은 계열이되 여기서는 **거짓 PASS** 다).
# → 접두 기준 deny-list 로 넓히고 정책으로 뺀다. 모르는 단어는 **포함**으로 둔다
#   (M-2026-003 의 `new`·`reuse_existing_wiki` 처럼 정상적으로 쓰는 값이 있다).
DEFAULT_EXCLUDED_STATUS = ("failed", "excluded", "rejected", "dropped", "duplicate", "skipped")


def included_sources(sources: list, policy: dict) -> tuple[list, list]:
    """(포함, 제외) — status 가 제외 접두로 시작하면 카운트에서 뺀다."""
    pref = tuple(str(x).strip().lower()
                 for x in (policy.get("status_excluded_prefixes") or DEFAULT_EXCLUDED_STATUS))
    inc, exc = [], []
    for s in sources:
        (exc if str(s.get("status", "selected")).strip().lower().startswith(pref) else inc).append(s)
    return inc, exc


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", required=True)
    ap.add_argument("--draft", default=None)
    args = ap.parse_args()

    try:
        policy = load_policy(args.policy)
        sources = load_sources(args.sources)
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e}", file=sys.stderr); return 2

    categories = policy.get("categories") or ["academic", "vendor", "research_org", "standards", "news"]
    raw_min = policy.get("min_per_category") or {}
    min_per = {c: int(raw_min.get(c, 0)) for c in categories}
    hard_block_if_missing = bool(policy.get("hard_block_if_missing", False))

    cited, dropped = included_sources(sources, policy)
    if dropped:
        print(f"status 제외 {len(dropped)}건: "
              + ", ".join(sorted({str(s.get('status')) for s in dropped})))
    if args.draft:
        try:
            keys = {k.lower() for k in CITATION_RE.findall(open(args.draft, encoding="utf-8").read())}
            matched = [s for s in cited if str(s.get("id", "")).lower() in keys]
            if matched:
                cited = matched
        except OSError:
            pass

    counts = {c: 0 for c in categories}
    untyped, invalid = [], []
    for s in cited:
        st = s.get("source_type")
        if st is None:
            untyped.append(s.get("id"))
        elif st not in counts:
            invalid.append((s.get("id"), st))
        else:
            counts[st] += 1

    violations = [f"  - {c}: {counts[c]} < {min_per[c]}" for c in categories if counts[c] < min_per[c]]
    missing = [c for c in categories if counts[c] == 0 and min_per[c] > 0]
    fail = bool(violations)
    if hard_block_if_missing and missing:
        fail = True

    print("policy min_per_category: " + ", ".join(f"{c}={min_per[c]}" for c in categories)
          + f"  hard_block_if_missing={hard_block_if_missing}")
    print(f"evaluated: {len(cited)} source(s)" + (" (draft-filtered)" if args.draft else ""))
    print("counts: " + ", ".join(f"{c}={counts[c]}{'OK' if counts[c]>=min_per[c] else 'FAIL'}" for c in categories))
    if untyped:
        print(f"WARNING source_type 누락(제외): {untyped}")
    if invalid:
        print(f"WARNING 미지정 카테고리(제외): {invalid}")
    if violations:
        print("violations:"); [print(v) for v in violations]
    if hard_block_if_missing and missing:
        print(f"hard_block: 누락 카테고리 {missing}")
    print(f"\nverdict: {'PASS' if not fail else 'FAIL'}")
    return 0 if not fail else 1


if __name__ == "__main__":
    sys.exit(main())
