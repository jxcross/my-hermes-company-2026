#!/usr/bin/env python3
"""
산출 도구(게이트 아님): NRF 예산표 생성
=========================================
인력·장비·재료 명세(JSON)를 받아 **연차별 × 비목별 예산표**를 `budget.md`(사람용)와
`budget.csv`(기계용)로 낸다. 인건비 단가·간접비율을 적용하고 연차 총계를 계산한다.
출처: other_projects/harness-templates/.../proposalforge/scripts/budget_build.py

⚠️ **이것은 게이트가 아니라 산출 도구다**(docs/13 §2④ — `bib_export` 와 같은 판정).
   판정은 `scripts/gates/budget_integrity.py` 가 한다. 그리고 **판정은 이 도구가 만든 표
   안에서 끝나면 안 된다** — 도구가 만든 합계를 도구의 규칙으로 검사하면 언제나 맞는다
   (docs/13 §5 '표가 스스로를 선언하고 스스로를 만족시킨다'). 그래서 게이트는 cap·연차 수·
   간접비율을 **SCOPE.md 선언**에서, 인력·장비 근거를 **plan.md 선언**에서 가져와 대조한다.

입력 JSON
  {
    "years": 5,
    "indirect_rate": 0.17,
    "team":      [{"role": "PI", "fte": 0.3, "months": 12, "monthly_krw": null}],
    "equipment": [{"item": "GPU 서버", "year": 1, "cost_krw": 30000000}],
    "materials": [{"item": "클라우드 크레딧", "year": 1, "cost_krw": 5000000}],
    "travel":    [{"item": "국제학회 2회", "year": 2, "cost_krw": 4000000}],
    "meetings":  [], "other": []
  }

사용
  python3 scripts/tools/budget_build.py --input spec.json \
      --md reports/<MID>/_private/bundle/budget.md \
      --csv reports/<MID>/_private/bundle/budget.csv

exit: 0 성공 · 2 usage/입력오류
  (cap 위반은 여기서 판정하지 않는다 — 게이트의 일이다. 참고로 경고만 출력한다.)
"""
from __future__ import annotations
import argparse
import csv
import json
import os
import sys

# NRF 월 단가 기본값(KRW). 미션에서 `monthly_krw` 로 덮어쓸 수 있다.
NRF_DEFAULT_MONTHLY_KRW = {
    "PI": 5_000_000,
    "CoPI": 4_500_000,
    "PostDoc": 4_000_000,
    "Researcher": 3_500_000,
    "PhDStudent": 1_500_000,
    "MSStudent": 900_000,
}

# 비목 taxonomy. budget_integrity 의 `categories` 기본값과 같아야 한다.
DIRECT_BUCKETS = ["인건비", "학생인건비", "장비비", "재료비", "출장비", "회의비", "기타"]
SUBTOTAL_ROW = "직접비_소계"
TOTAL_ROW = "연차_총계"


def role_monthly(role: str, override) -> int:
    if override is not None:
        return int(override)
    return NRF_DEFAULT_MONTHLY_KRW.get(role, 3_500_000)


def build_table(spec: dict) -> dict:
    years = int(spec["years"])
    if years < 1:
        raise ValueError("years 는 1 이상이어야 한다")
    table = {b: [0] * years for b in DIRECT_BUCKETS}

    for m in spec.get("team", []):
        monthly = role_monthly(m["role"], m.get("monthly_krw"))
        per_year = int(monthly * float(m.get("fte", 1.0)) * int(m.get("months", 12)))
        bucket = "학생인건비" if "Student" in str(m["role"]) else "인건비"
        for y in range(years):
            table[bucket][y] += per_year

    def add(items, bucket):
        for it in items:
            y = max(1, min(years, int(it.get("year", 1)))) - 1
            table[bucket][y] += int(it.get("cost_krw", 0))

    add(spec.get("equipment", []), "장비비")
    add(spec.get("materials", []), "재료비")
    add(spec.get("travel", []), "출장비")
    add(spec.get("meetings", []), "회의비")
    add(spec.get("other", []), "기타")

    direct = [sum(table[b][y] for b in DIRECT_BUCKETS) for y in range(years)]
    rate = float(spec.get("indirect_rate", 0.17))
    indirect = [int(round(d * rate)) for d in direct]
    total = [d + i for d, i in zip(direct, indirect)]
    return {"table": table, "direct": direct, "indirect": indirect,
            "total": total, "rate": rate, "years": years}


def indirect_label(rate: float) -> str:
    """`간접비_17pct` — 게이트가 이 접두어(`간접비`)로 행을 찾는다."""
    pct = rate * 100
    return f"간접비_{int(pct) if abs(pct - round(pct)) < 1e-9 else pct}pct"


def write_md(s: dict, out: str) -> None:
    years, table = s["years"], s["table"]
    headers = ["비목"] + [f"Year {y + 1}" for y in range(years)] + ["합계"]
    lines = ["---", "stage: budget", "status: complete",
             f"total_krw: {sum(s['total'])}", f"n_years: {years}",
             f"indirect_rate: {s['rate']}", "---", "",
             "# 예산 (NRF · 단위 KRW)", "",
             "| " + " | ".join(headers) + " |",
             "|" + "|".join(["---"] * len(headers)) + "|"]
    for b in DIRECT_BUCKETS:
        lines.append("| " + " | ".join([b] + [f"{table[b][y]:,}" for y in range(years)]
                                       + [f"{sum(table[b]):,}"]) + " |")
    lines.append("| **직접비 소계** | " + " | ".join(f"{s['direct'][y]:,}" for y in range(years))
                 + f" | {sum(s['direct']):,} |")
    lines.append(f"| 간접비 ({s['rate'] * 100:g}%) | "
                 + " | ".join(f"{s['indirect'][y]:,}" for y in range(years))
                 + f" | {sum(s['indirect']):,} |")
    lines.append("| **연차 총계** | " + " | ".join(f"{s['total'][y]:,}" for y in range(years))
                 + f" | {sum(s['total']):,} |")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")


def write_csv(s: dict, out: str) -> None:
    years, table = s["years"], s["table"]
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["비목"] + [f"Year {y + 1}" for y in range(years)] + ["Sum"])
        for b in DIRECT_BUCKETS:
            w.writerow([b] + table[b] + [sum(table[b])])
        w.writerow([SUBTOTAL_ROW] + s["direct"] + [sum(s["direct"])])
        w.writerow([indirect_label(s["rate"])] + s["indirect"] + [sum(s["indirect"])])
        w.writerow([TOTAL_ROW] + s["total"] + [sum(s["total"])])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True, help="예산 명세 JSON")
    ap.add_argument("--md", required=True)
    ap.add_argument("--csv", required=True)
    ap.add_argument("--cap", type=int, default=None, help="(참고) 연차별 상한 — 초과 시 경고만")
    args = ap.parse_args()

    try:
        spec = json.loads(open(args.input, encoding="utf-8").read())
        s = build_table(spec)
    except (OSError, ValueError, KeyError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    write_md(s, args.md)
    write_csv(s, args.csv)
    print(f"OK — {s['years']}개년 총 {sum(s['total']):,} KRW (간접비율 {s['rate'] * 100:g}%)")
    for y, t in enumerate(s["total"], start=1):
        print(f"   Year {y}: 직접 {s['direct'][y - 1]:,} + 간접 {s['indirect'][y - 1]:,} = {t:,}")
    if args.cap:
        over = [y for y, t in enumerate(s["total"], start=1) if t > args.cap]
        if over:
            print(f"WARN: 연차 상한 {args.cap:,} 초과 — Year {over} "
                  f"(판정은 budget_integrity 게이트가 한다)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
