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
]


def main() -> int:
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
