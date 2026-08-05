#!/usr/bin/env python3
"""
사용량·한도 상태 리포트 (미션 착수 전 점검 · LLM 호출 없음)
================================================================
누적 사용량과 **현재 한도 소진 여부**를 보고한다. 미션을 돌리기 전에 이것부터 본다.

⚠️ **왜 만들었나 — 실측(2026-08-05 · M-2026-005)**
   실미션 1차가 stage 4 에서 멈췄고 카드에 남은 것은
   `worker exited cleanly (rc=0) without calling kanban_complete — protocol violation` 뿐이었다.
   진짜 원인은 **LLM 사용량 한도 소진**(HTTP 429 `usage_limit_reached` · plan=team)이었고
   그것은 **세션 로그에만** 있었다. 카드만 봐서는 왜 멈췄는지 알 수 없다(docs/11 §7 ⑦).
   그리고 한도를 쓰는 줄 모르고 쓰다 소진됐다 — **보이지 않는 자원은 관리되지 않는다.**

⚠️ **이 스크립트는 LLM 을 호출하지 않는다.** 한도를 확인하려고 한도를 쓰면 안 된다.
   근거는 두 가지 기록물뿐이다:
     · `hermes insights` — 누적 세션·토큰(모델별)
     · `hermes-home/kanban/logs/*.log` — 워커 세션의 429 응답(`resets_at` 포함)

사용
  python3 scripts/usage_report.py               # 사람이 읽는 요약
  python3 scripts/usage_report.py --json        # 기계 판독
  python3 scripts/usage_report.py --quiet       # exit code 만 (미션 착수 전 점검용)

exit: 0 정상 · 1 **한도 소진 중**(리셋 전) · 2 근거를 읽지 못함
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIRS = [os.path.join(REPO_ROOT, "hermes-home", "kanban", "logs"),
            "/opt/data/kanban/logs"]

# 429 본문. resets_at 은 epoch 초.
# ⚠️ plan_type 을 같은 정규식의 **선택 그룹**으로 두면 비탐욕 매칭이 그것을 건너뛰고
#    바로 resets_at 으로 간다(실측: 항상 plan=? 였다). 매칭 구간 안에서 따로 찾는다.
LIMIT_RE = re.compile(
    r"'type':\s*'(?P<type>usage_limit_reached|rate_limit\w*)'.*?"
    r"'resets_at':\s*(?P<resets>\d+)", re.DOTALL)
PLAN_RE = re.compile(r"'plan_type':\s*'([^']*)'")
# 인증 실패 — 429 와 함께 '환경성 실패' 로 묶는다(파이프라인 결함이 아니다)
AUTH_RE = re.compile(r"(401 Unauthorized|invalid_api_key|authentication_error|"
                     r"credentials? (?:expired|invalid))", re.IGNORECASE)


def hermes_bin() -> list[str]:
    if shutil.which("hermes"):
        return ["hermes"]
    return ["docker", "exec", "hermes-solomon", "hermes"]


def insights() -> dict:
    """`hermes insights` 요약. 실패해도 치명적이지 않다(한도 판정의 근거가 아니다)."""
    try:
        p = subprocess.run(hermes_bin() + ["insights"], capture_output=True, text=True,
                           timeout=60)
        out = p.stdout
    except (OSError, subprocess.SubprocessError):
        return {}
    d: dict = {}
    m = re.search(r"Period:\s*(.+)", out)
    if m:
        d["period"] = m.group(1).strip()
    for key, pat in (("sessions", r"Sessions:\s*([\d,]+)"),
                     ("total_tokens", r"Total tokens:\s*([\d,]+)"),
                     ("input_tokens", r"Input tokens:\s*([\d,]+)"),
                     ("output_tokens", r"Output tokens:\s*([\d,]+)")):
        m = re.search(pat, out)
        if m:
            d[key] = int(m.group(1).replace(",", ""))
    models = re.findall(r"^\s{2}(\S+)\s+(\d+)\s+([\d,]+)\s*$", out, re.MULTILINE)
    if models:
        d["models"] = [{"model": a, "sessions": int(b), "tokens": int(c.replace(",", ""))}
                       for a, b, c in models]
    return d


def log_files() -> list[str]:
    for d in LOG_DIRS:
        if os.path.isdir(d):
            return [os.path.join(d, f) for f in os.listdir(d) if f.endswith(".log")]
    return []


def scan_limits(paths: list[str]) -> tuple[dict | None, list[str]]:
    """가장 최근의 한도 소진 기록과, 환경성 실패가 있는 task 목록."""
    latest: dict | None = None
    env_failed: list[str] = []
    for p in paths:
        try:
            text = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        tid = os.path.basename(p)[:-4]
        hit = None
        for m in LIMIT_RE.finditer(text):
            plan = PLAN_RE.search(m.group(0))
            hit = {"task": tid, "type": m.group("type"),
                   "plan": plan.group(1) if plan else "",
                   "resets_at": int(m.group("resets")),
                   "mtime": os.path.getmtime(p)}
        if hit:
            env_failed.append(tid)
            if latest is None or hit["resets_at"] > latest["resets_at"] \
                    or hit["mtime"] > latest["mtime"]:
                latest = hit
        elif AUTH_RE.search(text):
            env_failed.append(tid)
    return latest, sorted(set(env_failed))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true", help="기계 판독 출력")
    ap.add_argument("--quiet", action="store_true", help="exit code 만")
    ap.add_argument("--now", type=int, default=None,
                    help="현재 시각(epoch) 주입 — 테스트용. 미지정 시 시스템 시계")
    args = ap.parse_args()

    paths = log_files()
    if not paths:
        if not args.quiet:
            print("FAIL(usage): 워커 로그를 찾지 못했다 "
                  f"({' 또는 '.join(LOG_DIRS)}) — 소진 여부를 판단할 근거가 없다",
                  file=sys.stderr)
        return 2

    now = args.now if args.now is not None else int(dt.datetime.now().timestamp())
    latest, env_failed = scan_limits(paths)
    ins = insights()

    exhausted = bool(latest and latest["resets_at"] > now)
    report = {
        "exhausted": exhausted,
        "limit_record": latest,
        "seconds_to_reset": (latest["resets_at"] - now) if exhausted else 0,
        "env_failed_tasks": env_failed,
        "insights": ins,
        "log_files": len(paths),
    }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif not args.quiet:
        print("── 사용량 ──")
        if ins:
            print(f"  기간 {ins.get('period', '?')} · 세션 {ins.get('sessions', '?')} · "
                  f"총 토큰 {ins.get('total_tokens', 0):,} "
                  f"(입력 {ins.get('input_tokens', 0):,} / 출력 {ins.get('output_tokens', 0):,})")
            for m in (ins.get("models") or [])[:5]:
                print(f"    {m['model']:<18} 세션 {m['sessions']:>3}  토큰 {m['tokens']:>12,}")
        else:
            print("  (hermes insights 를 읽지 못했다 — 누적 사용량 없음)")
        print("── 한도 ──")
        if exhausted:
            h = report["seconds_to_reset"] / 3600
            when = dt.datetime.fromtimestamp(latest["resets_at"]).strftime("%Y-%m-%d %H:%M")
            print(f"  ⚠️ **소진 중** ({latest['type']} · plan={latest['plan'] or '?'})")
            print(f"     리셋 {when} — 약 {h:.1f}시간 남음 · 근거 task {latest['task']}")
            print("     → 미션을 새로 시작하지 마라. 진행 중 미션은 그 자리에 세워 둔다.")
        elif latest:
            when = dt.datetime.fromtimestamp(latest["resets_at"]).strftime("%Y-%m-%d %H:%M")
            print(f"  ✓ 정상 (마지막 소진 기록은 {when} 에 이미 리셋됨)")
        else:
            print("  ✓ 정상 (소진 기록 없음)")
        if env_failed:
            print(f"  환경성 실패가 기록된 task {len(env_failed)}건: {', '.join(env_failed[:6])}"
                  + (" …" if len(env_failed) > 6 else ""))
            print("     ⚠️ 이런 task 는 카드에 'protocol violation' 으로만 보인다 — "
                  "파이프라인 결함으로 오진하지 마라(docs/11 §7 ⑦)")
    return 1 if exhausted else 0


if __name__ == "__main__":
    sys.exit(main())
