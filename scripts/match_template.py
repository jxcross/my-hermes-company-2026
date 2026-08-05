#!/usr/bin/env python3
"""
미션 → 템플릿 매처 (docs/12 §5 제안 C · 3-way 판정)
=====================================================
미션 요청 한 줄을 받아 **어느 아키타입으로 돌릴지** 제안한다. 템플릿이 20종이 되면서 사람이
목록을 외워 고르는 것이 부담이 됐다.

3-way 판정 (docs/12 §5)
  · **높음**   — 그대로 제시 → 조정 협상
  · **어중간** — **경고와 함께** 제시 + 안 맞는 부분 명시 + **신규 구성도 함께** 제안
  · **낮음**   — 억지로 고르지 않는다 → 골격에서 신규 구성

⚠️ **매칭 결과는 항상 근거와 함께 낸다**(docs/12 §5). 점수만 보여주면 Sam 이 판단할 수 없다.
   그래서 이 스크립트는 **어떤 낱말이 맞았는지**를 함께 출력한다.

⚠️ **maturity 를 점수에 반영하고 `draft` 를 고를 때는 경고한다**(docs/12 §11).
   현재 20종 중 19종이 `draft`(실미션 완주 0회)이므로 이 경고가 거의 항상 뜬다 — 정상이다.

⚠️ **manifest 는 손으로 유지하지 않는다.** `templates/*.yaml` 에서 매번 만든다.
   손으로 유지하는 목록은 템플릿과 어긋나고, 그 어긋남은 **매처가 존재하지 않는 템플릿을
   추천하거나 새 템플릿을 영영 추천하지 않는** 형태로 조용히 나타난다. `--rebuild` 는
   사람이 들여다보기 위한 스냅샷일 뿐 판정의 근거가 아니다.

⚠️ **LLM 을 호출하지 않는다** — 순수 어휘 매칭이다. 한국어는 조사가 붙으므로 토큰 경계
   (`\\b`)를 쓰지 않고 **부분 문자열 포함**으로 본다(docs/13 §5 의 반복된 교훈).

사용
  python3 scripts/match_template.py "온디바이스 LLM 추론 최적화 동향을 조사해줘"
  python3 scripts/match_template.py --json "이 논문으로 학회 발표 슬라이드 만들어줘"
  python3 scripts/match_template.py --rebuild        # templates/manifest.json 스냅샷 기록

exit: 0 높음 · 1 어중간 · 2 낮음(신규 구성 권고) · 3 usage/로드 실패
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
    print("ERROR: PyYAML 필요", file=sys.stderr); sys.exit(3)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(REPO_ROOT, "templates")
MANIFEST = os.path.join(TEMPLATES_DIR, "manifest.json")

# maturity 가중 — 실증된 것을 우대한다. 없으면 draft 로 본다(가장 보수적).
MATURITY_WEIGHT = {"proven": 1.0, "tested": 0.92, "draft": 0.82}
HIGH, MID = 0.42, 0.18
# 신호 포화점 — 선언 키워드(3.0) 하나면 0.75, 둘이면 포화. 흔한 낱말(1.0)은 넷이 필요하다.
SIGNAL_TARGET = 4.0

# 한국어 조사·영어 기능어. 매칭 신호가 되지 못한다.
STOP = {"그리고", "그런데", "해줘", "해줄", "만들어", "만들어줘", "작성", "작성해", "해야",
        "대한", "관한", "위한", "우리", "이번", "다음", "하나", "가지", "정도", "필요",
        "the", "and", "for", "with", "into", "from", "this", "that", "our", "make",
        "please", "미션", "파이프라인", "템플릿"}


def tokens(text: str) -> list[str]:
    """2글자 이상 낱말. 한국어는 조사가 붙어 있어도 앞부분이 남으므로 그대로 쓴다."""
    raw = re.split(r"[^0-9A-Za-z가-힣]+", (text or "").lower())
    return [w for w in raw if len(w) >= 2 and w not in STOP]


def load_templates() -> list[dict]:
    out = []
    for f in sorted(os.listdir(TEMPLATES_DIR)):
        if not f.endswith((".yaml", ".yml")) or f.startswith("_"):
            continue
        try:
            d = yaml.safe_load(open(os.path.join(TEMPLATES_DIR, f), encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            continue
        if not d.get("name"):
            continue
        out.append({
            "name": d["name"],
            "file": f,
            "category": d.get("category", ""),
            "display_name": d.get("display_name", ""),
            "goal_kr": d.get("goal_kr", ""),
            "maturity": str(d.get("maturity") or "draft").strip().lower(),
            "keywords": [str(k).lower() for k in (d.get("keywords") or [])],
            "stages": len(d.get("stages") or []),
        })
    return out


def template_terms(t: dict) -> list[str]:
    """매칭 대상 낱말. 선언된 `keywords:` 를 **가장 무겁게** 본다."""
    terms = [(k, 3.0) for k in t["keywords"]]
    terms += [(w, 2.0) for w in tokens(t["display_name"])]
    terms += [(w, 1.0) for w in tokens(t["goal_kr"])]
    terms += [(w, 1.5) for w in tokens(t["name"].replace("-", " "))]
    best: dict[str, float] = {}
    for w, wt in terms:
        best[w] = max(best.get(w, 0.0), wt)
    return sorted(best.items(), key=lambda x: -x[1])


def score(query: str, t: dict) -> tuple[float, list[str]]:
    """(0~1 점수, 맞은 낱말). 한국어 조사 때문에 **부분 문자열 포함**으로 본다."""
    q = re.sub(r"[^0-9a-z가-힣]+", " ", (query or "").lower())
    terms = template_terms(t)
    total = sum(w for _, w in terms) or 1.0
    hit, matched = 0.0, []
    for term, w in terms:
        if term in q:
            hit += w
            matched.append(term)
    # ⚠️ 신호를 **맞은 개수**로 세면 안 된다 — "마이그레이션" 처럼 **하나로 충분히 특정되는
    #    낱말**이 있고, 반대로 흔한 낱말 셋이 맞아도 신호가 아니다. 실측: 개수 기준일 때
    #    "코드를 파이썬 3.13으로 마이그레이션" 이 0.16(낮음)으로 떨어졌다.
    #    → 선언 키워드(3.0)가 하나만 맞아도 유의미하도록 **가중치 합**으로 잰다.
    signal = min(1.0, hit / SIGNAL_TARGET)
    coverage = hit / total          # 템플릿 어휘를 얼마나 덮었나(장황한 템플릿일수록 작다)
    s = signal * 0.8 + coverage * 0.2
    return round(min(1.0, s) * MATURITY_WEIGHT.get(t["maturity"], 0.82), 4), matched


def rank(query: str, tpls: list[dict]) -> list[dict]:
    out = []
    for t in tpls:
        s, m = score(query, t)
        out.append({**t, "score": s, "matched": m})
    return sorted(out, key=lambda x: (-x["score"], x["name"]))


def verdict(top: float) -> str:
    return "높음" if top >= HIGH else ("어중간" if top >= MID else "낮음")


def rebuild_manifest(tpls: list[dict]) -> str:
    data = {
        "_note": "templates/*.yaml 에서 생성한 스냅샷이다. 손으로 고치지 마라 — "
                 "판정은 항상 템플릿 원본에서 다시 만든다(match_template.py --rebuild).",
        "count": len(tpls),
        "templates": [{k: t[k] for k in
                       ("name", "file", "category", "display_name", "maturity",
                        "keywords", "stages")} for t in tpls],
    }
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return MANIFEST


def main() -> int:  # noqa: C901
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("query", nargs="*", help="미션 요청(자연어)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--top", type=int, default=3, help="상위 N개 표시(기본 3)")
    ap.add_argument("--rebuild", action="store_true", help="manifest.json 스냅샷 갱신")
    args = ap.parse_args()

    tpls = load_templates()
    if not tpls:
        print("FAIL(usage): templates/ 를 읽지 못했다", file=sys.stderr)
        return 3
    if args.rebuild:
        print(f"manifest 갱신: {rebuild_manifest(tpls)} ({len(tpls)}종)")
        if not args.query:
            return 0

    query = " ".join(args.query).strip()
    if not query:
        ap.print_usage(sys.stderr)
        print("미션 요청을 한 줄로 주라.", file=sys.stderr)
        return 3

    ranked = rank(query, tpls)
    top = ranked[0]
    v = verdict(top["score"])

    if args.json:
        print(json.dumps({"query": query, "verdict": v,
                          "candidates": [{k: c[k] for k in
                                          ("name", "score", "maturity", "matched",
                                           "display_name", "stages")}
                                         for c in ranked[:args.top]]},
                         ensure_ascii=False, indent=2))
        return {"높음": 0, "어중간": 1, "낮음": 2}[v]

    print(f'요청: "{query}"')
    print(f"판정: **{v}** (최고점 {top['score']:.2f} · 임계 높음≥{HIGH} 어중간≥{MID})\n")
    for i, c in enumerate(ranked[:args.top], 1):
        mark = "★" if i == 1 else " "
        print(f"{mark} {i}. {c['name']:<20} {c['score']:.2f}  [{c['maturity']}] "
              f"{c['stages']}단계 — {c['display_name']}")
        print(f"      맞은 낱말: {', '.join(c['matched'][:8]) or '(없음)'}")

    print()
    if v == "높음":
        print(f"→ `{top['name']}` 으로 진행을 제안한다. 협상 미리보기(비파괴):")
        print(f"   python3 scripts/instantiate_template.py {top['name']} M-2026-NNN \\\n"
              f"     --topic \"…\" --dry-run --render mermaid")
    elif v == "어중간":
        print(f"⚠️ `{top['name']}` 이 최고점이지만 **확신할 수 없다**. 안 맞는 부분을 Sam 에게")
        print("   명시하고, **신규 구성도 함께** 제안하라(docs/12 §5).")
        print(f"   맞은 근거가 {len(top['matched'])}개뿐이다: {', '.join(top['matched']) or '없음'}")
    else:
        print("→ 억지로 고르지 마라. 기존 아키타입 어느 것과도 충분히 맞지 않는다.")
        print("   골격에서 **신규 구성**을 제안하고, 유사한 것을 참고본으로만 쓰라.")

    if top["maturity"] != "proven":
        print(f"\n⚠️ **`{top['name']}` 은 `{top['maturity']}` 다** — 실미션 완주 "
              f"{'0회' if top['maturity'] == 'draft' else '1회'}. Sam 에게 알리고 시작하라."
              f" 검증되지 않은 파이프라인은 중간에 멈출 수 있다(docs/12 §11).")
    return {"높음": 0, "어중간": 1, "낮음": 2}[v]


if __name__ == "__main__":
    sys.exit(main())
