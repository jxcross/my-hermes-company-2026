#!/usr/bin/env python3
"""
도구: 관련성 점수 (결정적)
==========================
주기 문헌 모니터(아키타입 E)의 선별 단계를 **회차 간 재현 가능하게** 만든다.
출처: other_projects/harness-templates/.../litmonitor/scripts/relevance_score.py 를
우리 watchlist.yaml / sources.yaml 스키마로 재작성.

⚠️ 이것은 **게이트가 아니라 산출 도구**다(판정하지 않는다) — 그래서 `tools/`에 둔다.
   선별 단계는 대부분 기계적이라 결정적 점수가 회차 간 흔들림을 없앤다. 경계선 사례만
   curator 가 판단으로 조정하고, 조정하면 사유를 남긴다.

점수 신호 (합산 후 max_score 로 클램프)
  키워드 일치   watchlist.keywords ∩ (title+abstract)   개당 1.0 (상한 2.0)
  저자 일치     watchlist.authors  ∩ authors            2.0 (상한 2.0)
  학회/저널     watchlist.venues   ∩ venue              1.0
  주제 근접     watchlist.topics 의 어휘와 title 겹침    최대 1.0 (자카드 유사도)

watchlist.yaml
    keywords: [on-device inference, quantization]
    authors:  [Han Song]
    venues:   [NeurIPS, MLSys]
    topics:   ["효율적 LLM 추론"]
    max_score: 5.0        # 선택(기본 5.0)

입력
  --watchlist  <path>  monitors/<id>/watchlist.yaml
  --candidates <path>  reports/<MID>/raw/sources.yaml
  --out        <path>  점수가 붙은 목록(YAML). 기본 candidates 옆의 scored.yaml
  --threshold  <float> 이 점수 미만은 status=rejected 로 표시(기본 0.0 = 전부 유지)

exit: 0 성공 · 2 usage/입력오류
"""
from __future__ import annotations
import argparse
import os
import re
import sys

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML 필요", file=sys.stderr); sys.exit(2)

WORD_RE = re.compile(r"[a-z0-9]+|[가-힣]{2,}")


def norm(s) -> str:
    return re.sub(r"\s+", " ", str(s or "")).strip().lower()


def words(s) -> set[str]:
    return set(WORD_RE.findall(norm(s)))


def as_list(v) -> list[str]:
    if v is None:
        return []
    if isinstance(v, (list, tuple)):
        return [str(x) for x in v]
    return [str(v)]


def load_yaml(path: str):
    return yaml.safe_load(open(path, encoding="utf-8").read())


def load_candidates(path: str) -> list[dict]:
    data = load_yaml(path)
    if isinstance(data, dict):
        data = data.get("sources", data.get("candidates", []))
    return [c for c in (data or []) if isinstance(c, dict)]


def score_one(c: dict, wl: dict) -> tuple[float, list[str]]:
    """(점수, 근거) — 근거를 남겨야 curator 가 경계선 판단을 할 수 있다."""
    why: list[str] = []
    hay = norm(c.get("title")) + " " + norm(c.get("abstract")) + " " + norm(c.get("summary"))

    kws = [k for k in as_list(wl.get("keywords")) if norm(k) and norm(k) in hay]
    kw_score = min(2.0, 1.0 * len(kws))
    if kws:
        why.append(f"keyword×{len(kws)}({', '.join(kws[:3])})")

    cand_authors = norm(" ; ".join(as_list(c.get("authors"))))
    hits = [a for a in as_list(wl.get("authors")) if norm(a) and norm(a) in cand_authors]
    au_score = 2.0 if hits else 0.0
    if hits:
        why.append(f"author({', '.join(hits[:2])})")

    venue = norm(c.get("venue"))
    vhit = [v for v in as_list(wl.get("venues")) if norm(v) and norm(v) in venue]
    v_score = 1.0 if vhit else 0.0
    if vhit:
        why.append(f"venue({vhit[0]})")

    tw = set()
    for t in as_list(wl.get("topics")):
        tw |= words(t)
    title_w = words(c.get("title"))
    t_score = 0.0
    if tw and title_w:
        j = len(tw & title_w) / len(tw | title_w)
        t_score = round(min(1.0, j * 3), 2)   # 자카드는 값이 작아 3배 후 클램프
        if t_score:
            why.append(f"topic~{t_score}")

    total = kw_score + au_score + v_score + t_score
    return round(min(float(wl.get("max_score", 5.0)), total), 2), why


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--watchlist", required=True)
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--threshold", type=float, default=0.0)
    args = ap.parse_args()

    try:
        wl = load_yaml(args.watchlist) or {}
        cands = load_candidates(args.candidates)
    except (OSError, yaml.YAMLError) as e:
        print(f"ERROR: {e}", file=sys.stderr); return 2
    if not isinstance(wl, dict):
        print("ERROR: watchlist 최상위가 매핑이 아니다", file=sys.stderr); return 2
    if not cands:
        print("ERROR: 후보가 비었다", file=sys.stderr); return 2

    scored = []
    for c in cands:
        s, why = score_one(c, wl)
        d = dict(c)
        d["relevance_score"] = s
        d["relevance_why"] = "; ".join(why) or "no signal"
        if s < args.threshold:
            d["status"] = "rejected"
            d.setdefault("reject_reason", f"score {s} < threshold {args.threshold}")
        else:
            d.setdefault("status", "selected")
        scored.append(d)

    scored.sort(key=lambda d: (-d["relevance_score"], str(d.get("id"))))
    out = args.out or os.path.join(os.path.dirname(os.path.abspath(args.candidates)), "scored.yaml")
    try:
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            yaml.safe_dump(scored, f, allow_unicode=True, sort_keys=False)
    except OSError as e:
        print(f"ERROR: 쓰기 실패 ({e})", file=sys.stderr); return 2

    kept = sum(1 for d in scored if d.get("status") != "rejected")
    print(f"{len(scored)}건 점수화 → {out} (threshold {args.threshold} 통과 {kept}건)")
    for d in scored[:10]:
        print(f"  {d['relevance_score']:>4}  {d.get('id')}  {d['relevance_why']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
