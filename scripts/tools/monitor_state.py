#!/usr/bin/env python3
"""
도구: 모니터 지속 상태 (미션 간 공유)
=====================================
주기 실행 아키타입(E — 문헌 모니터)의 **미션 간 지속 상태**를 관리한다.
출처: other_projects/harness-templates/.../litmonitor/scripts/seen_tracker.py 를
우리 구조(미션 = 1회 실행)로 이식.

⚠️ 왜 미션 밖에 두는가 — 우리 모델은 **미션 1건 = 파이프라인 1회 실행**이다. 주간 모니터는
매주 새 미션(M-2026-0NN)으로 돌지만 "이미 본 논문" 기억은 **미션을 가로질러** 살아야 한다.
그래서 상태를 `monitors/<monitor_id>/`에 두고 미션은 이를 읽고 갱신만 한다(git 추적 =
PC 간 이동 가능). 미션 디렉터리(`reports/<MID>/`)는 그 회차의 산출만 담는다.

레이아웃
  monitors/<monitor_id>/watchlist.yaml   감시 대상(키워드·저자·학회·소스) — Scoping 에서 확정
  monitors/<monitor_id>/_seen.tsv        본 논문 id 로그(append-only): "<id>\\t<YYYY-MM-DD>"
  monitors/<monitor_id>/history/         회차별 다이제스트 보관

부명령
  seen   <id> [...]          하나라도 이미 본 것이면 exit 1(스크립트 판정용)
  add    <id> [...] --date D 신규만 추가(멱등). 추가 건수 출력
  list                       id 목록
  count                      "<n> seen"
  filter --ids-file <path>   줄단위 id 목록에서 **처음 보는 것만** 출력(수집 단계 dedup 용)
  prune  --days N --today D  N일보다 오래된 항목 제거

⚠️ `--date`/`--today`는 명시적으로 받는다(컨테이너 시계·타임존 차이로 회차가 어긋나는 것을 막는다).
   생략하면 시스템 날짜(UTC)를 쓴다.

exit: 0 정상 · 1 query 형 '없음/이미 있음' · 2 usage
"""
from __future__ import annotations
import argparse
import os
import sys
from datetime import datetime, timedelta, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 기본은 repo 의 monitors/ (git 추적 = PC 간 이동). 테스트·다중 인스턴스용 override.
MONITORS = os.environ.get("HERMES_MONITORS_ROOT") or os.path.join(REPO_ROOT, "monitors")


def monitors_root() -> str:
    """호출 시점에 다시 읽는다 — 테스트가 env 를 바꿔도 반영되도록."""
    return os.environ.get("HERMES_MONITORS_ROOT") or os.path.join(REPO_ROOT, "monitors")


def seen_path(monitor_id: str) -> str:
    return os.path.join(monitors_root(), monitor_id, "_seen.tsv")


def load_seen(monitor_id: str) -> dict[str, str]:
    """{id: first_seen_date}. 파일이 없으면 빈 dict(첫 회차)."""
    path = seen_path(monitor_id)
    out: dict[str, str] = {}
    if not os.path.isfile(path):
        return out
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t") if "\t" in line else line.split()
            if parts:
                out.setdefault(parts[0], parts[1] if len(parts) > 1 else "")
    return out


def append_seen(monitor_id: str, ids: list[str], date: str) -> int:
    have = load_seen(monitor_id)
    fresh = [i for i in dict.fromkeys(ids) if i and i not in have]
    if not fresh:
        return 0
    path = seen_path(monitor_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        for i in fresh:
            f.write(f"{i}\t{date}\n")
    return len(fresh)


def today(explicit: str | None) -> str:
    return explicit or datetime.now(timezone.utc).strftime("%Y-%m-%d")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--monitor", required=True, help="monitor_id (monitors/<id>/)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("seen"); p.add_argument("ids", nargs="+")
    p = sub.add_parser("add"); p.add_argument("ids", nargs="+"); p.add_argument("--date", default=None)
    sub.add_parser("list")
    sub.add_parser("count")
    p = sub.add_parser("filter"); p.add_argument("--ids-file", required=True)
    p = sub.add_parser("prune"); p.add_argument("--days", type=int, required=True); p.add_argument("--today", default=None)

    args = ap.parse_args()
    have = load_seen(args.monitor)

    if args.cmd == "seen":
        hit = [i for i in args.ids if i in have]
        for i in hit:
            print(f"{i}\t{have[i]}")
        return 1 if hit else 0

    if args.cmd == "add":
        n = append_seen(args.monitor, args.ids, today(args.date))
        print(f"{n} added ({len(args.ids) - n} already seen)")
        return 0

    if args.cmd == "list":
        for i in have:
            print(i)
        return 0

    if args.cmd == "count":
        print(f"{len(have)} seen")
        return 0

    if args.cmd == "filter":
        try:
            lines = [l.strip() for l in open(args.ids_file, encoding="utf-8")]
        except OSError as e:
            print(f"ERROR: {e}", file=sys.stderr); return 2
        fresh = [l for l in lines if l and not l.startswith("#") and l not in have]
        for i in fresh:
            print(i)
        return 0

    if args.cmd == "prune":
        cutoff = datetime.strptime(today(args.today), "%Y-%m-%d") - timedelta(days=args.days)
        kept = {i: d for i, d in have.items()
                if not d or datetime.strptime(d, "%Y-%m-%d") >= cutoff}
        path = seen_path(args.monitor)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            for i, d in kept.items():
                f.write(f"{i}\t{d}\n")
        print(f"{len(have) - len(kept)} pruned, {len(kept)} kept")
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
