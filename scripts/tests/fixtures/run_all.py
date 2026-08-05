#!/usr/bin/env python3
"""
깨뜨린 픽스처 E2E 하네스 일괄 실행
====================================
각 하네스를 별도 프로세스로 돌리고 통과/실패를 집계한다. 자세한 설명은 README.md.

실행:
  docker exec hermes-solomon sh -c 'cd /work/company && python3 scripts/tests/fixtures/run_all.py'

exit: 0 전부 통과 · 1 하나라도 실패
"""
from __future__ import annotations
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESSES = [
    ("policy", "G 정책 브리프"),
    ("legal", "H 법률 문서"),
    ("docs", "I 코드 문서화"),
    ("lecture", "J 강의 자료"),
    ("migrate", "K 마이그레이션"),
    ("sec", "L 보안 감사"),
    ("agent", "M AI 시스템 평가"),
    ("dataset", "N 데이터셋 배포"),
    ("repro", "O 재현 패키지"),
    ("sim", "P 시뮬레이션 실험"),
    ("proposal", "Q 연구제안서"),
    ("rebuttal", "R 리뷰어 응답서"),
    ("outreach", "S 성과 발신"),
    ("slide", "T 발표 슬라이드"),
]


def draft_drift() -> None:
    """`lint_gate_drafts.py` 를 **보고 전용**으로 먼저 돌린다.

    ⚠️ 하네스가 통과했다는 것과 실미션이 통과한다는 것은 다르다 — 하네스는 게이트마다
       편한 `--draft` 를 골라 주지만 실미션은 stage 당 **하나를 공유한다**
       (`gate_keeper.py:239-247`). 아키타입 S 는 하네스 53/53 인 채로 실미션에서
       3종이 `exit 2` 로 막혔다(`docs/13 §5`).

    ⚠️ **여기서는 차단하지 않는다.** 현재 미해결 드리프트가 남아 있고, 그걸로 하네스
       전체를 못 돌리게 만들면 이 점검이 오히려 꺼진다. 대신 **미션 착수 런북에서
       `lint_gate_drafts.py <template>` 를 차단 조건으로** 쓴다 — 고쳐야 할 시점에서
       정확히 막는 것이 전역으로 막는 것보다 낫다.
    """
    lint = os.path.join(HERE, "..", "..", "lint_gate_drafts.py")
    if not os.path.exists(lint):
        return
    r = subprocess.run([sys.executable, lint], capture_output=True, text=True)
    fails = [l.strip() for l in r.stdout.splitlines() if l.strip().startswith("FAIL")]
    warns = [l.strip() for l in r.stdout.splitlines() if l.strip().startswith("WARN")]
    if fails or warns:
        print(f"△ draft 정합: FAIL {len(fails)} · WARN {len(warns)} "
              "— `python3 scripts/lint_gate_drafts.py` 로 상세 확인 (하네스는 계속 진행)")
    else:
        print("✓ draft 정합: 하네스와 템플릿이 일치")
    print()


def main() -> int:
    draft_drift()
    results = []
    for name, label in HARNESSES:
        path = os.path.join(HERE, f"{name}.py")
        r = subprocess.run([sys.executable, path], capture_output=True, text=True)
        tail = [l for l in r.stdout.splitlines() if "통과" in l and "/" in l]
        summary = tail[-1] if tail else "(요약 없음)"
        ok = r.returncode == 0
        results.append((name, ok))
        print(f"{'✓' if ok else '✗'} {name:9s} {label:14s} {summary}")
        if not ok:
            for line in r.stdout.splitlines():
                if line.startswith("‼️"):
                    print(f"      {line}")
            if r.stderr.strip():
                print("      stderr:", r.stderr.strip().splitlines()[-1])

    n_ok = sum(1 for _n, ok in results if ok)
    print(f"\n{n_ok}/{len(results)} 하네스 통과")
    return 0 if n_ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
