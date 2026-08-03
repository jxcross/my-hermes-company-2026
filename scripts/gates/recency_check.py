#!/usr/bin/env python3
"""
객관 게이트: 최신성(Recency)
=============================
인용/선별 소스가 정책상 충분히 최신인지 LLM 없이 검사한다.
harness-templates(paperforge/trendforge)의 recency_check.py 를 이식·일반화.
출처: other_projects/harness-templates/.../scripts/recency_check.py (표준 라이브러리만).

입력
  --policy <path>   : 정책. JSON(pipeline.json: policy.recency_policy) 또는
                      frontmatter 있는 .md/.yaml(recency_policy). offset 키 지원.
  --sources <path>  : sources.yaml (YAML 리스트: id·published_year·source_type·status·seminal)
  --draft <path>    : (선택) 보고서. 있으면 인용된 id 만 평가(citation 매칭 실패 시 전체 평가).

정책 필드(recency_policy)
  cutoff_year 또는 cutoff_year_offset(현재년 기준)  : 이 연도 이상이면 'recent'
  recent_ratio (기본 0.6)                          : recent 비율 하한
  hard_block_year 또는 hard_block_year_offset       : 이 미만은 seminal 아니면 금지
  seminal_exceptions (기본 true)

exit: 0 PASS · 1 FAIL · 2 usage/error
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from datetime import datetime, timezone

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML 필요", file=sys.stderr); sys.exit(2)

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
CITATION_RE = re.compile(r"\[([a-z][a-z0-9_\-]*)\]", re.IGNORECASE)


def load_policy(path: str, key: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get(key, {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get(key, {}) or {}


def load_sources(path: str) -> list[dict]:
    data = yaml.safe_load(open(path, encoding="utf-8").read())
    if isinstance(data, dict):
        data = data.get("sources", [])
    return [s for s in (data or []) if isinstance(s, dict)]


def resolve_year(policy: dict, abs_key: str, off_key: str, default_off: int, now_year: int) -> int:
    if abs_key in policy:
        return int(policy[abs_key])
    if off_key in policy:
        return now_year + int(policy[off_key])
    return now_year + default_off


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", required=True)
    ap.add_argument("--draft", default=None)
    args = ap.parse_args()

    try:
        policy = load_policy(args.policy, "recency_policy")
        sources = load_sources(args.sources)
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e}", file=sys.stderr); return 2

    now_year = datetime.now(timezone.utc).year
    cutoff_year = resolve_year(policy, "cutoff_year", "cutoff_year_offset", -2, now_year)
    recent_ratio = float(policy.get("recent_ratio", 0.6))
    hard_block_year = resolve_year(policy, "hard_block_year", "hard_block_year_offset", -5, now_year)
    seminal_exceptions = bool(policy.get("seminal_exceptions", True))

    # 선별된 소스만(status failed/excluded 제외)
    cited = [s for s in sources if str(s.get("status", "selected")).lower() not in ("failed", "excluded")]

    # draft 인용 필터(매칭되면 적용, 아니면 전체)
    if args.draft:
        try:
            dtext = open(args.draft, encoding="utf-8").read()
            keys = {k.lower() for k in CITATION_RE.findall(dtext)}
            matched = [s for s in cited if str(s.get("id", "")).lower() in keys]
            if matched:
                cited = matched
        except OSError:
            pass

    total = len(cited)
    if total == 0:
        print("FAIL: 평가할 소스 없음"); return 1
    missing_year = [s.get("id") for s in cited if s.get("published_year") in (None, "")]
    if missing_year:
        print(f"FAIL: published_year 누락: {missing_year}"); return 1

    def yr(s):  # '2026-05' 같은 값도 허용
        return int(str(s["published_year"])[:4])

    recent = [s for s in cited if yr(s) >= cutoff_year]
    pre_hard = [s for s in cited if yr(s) < hard_block_year
                and not (seminal_exceptions and bool(s.get("seminal", False)))]
    actual = len(recent) / total
    passes = (actual >= recent_ratio) and (not pre_hard)

    print(f"policy: cutoff>={cutoff_year}, recent_ratio>={recent_ratio:.2f}, hard_block<{hard_block_year}, seminal_exc={seminal_exceptions}")
    print(f"evaluated: {total} source(s)" + (f" (draft-filtered)" if args.draft else ""))
    print(f"recent (>= {cutoff_year}): {len(recent)} ({actual*100:.1f}%) {'OK' if actual>=recent_ratio else 'FAIL'}")
    if pre_hard:
        print("hard-block violations (< {}, not seminal):".format(hard_block_year))
        for s in pre_hard:
            print(f"  - {s.get('id')} ({s.get('published_year')})")
    print(f"\nverdict: {'PASS' if passes else 'FAIL'}")
    return 0 if passes else 1


if __name__ == "__main__":
    sys.exit(main())
