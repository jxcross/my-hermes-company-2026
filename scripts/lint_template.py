#!/usr/bin/env python3
"""
템플릿 불변식 린터
==================
템플릿(및 협상 중인 미션 스펙)이 Layer 0 불변식을 만족하는지 검사한다. 설계: docs/11 §3.E · docs/12.

`instantiate_template.py`에 인라인이던 검사를 **독립 CLI로 분리**했다. 이유: 협상은
"조정 → 검사 → 재제시"를 여러 번 도는 루프인데(docs/12 §4), 인스턴스화 시점에만 도는
검사로는 그 루프를 받칠 수 없다. 번역기는 이제 이 모듈을 import 해서 쓴다(단일 진실).

검사 항목
  [불변식] scoping_gate      : 첫 단계에 Sam 게이트
  [불변식] deliver_gate      : 마지막 단계에 Sam 게이트
  [불변식] revision_loop     : 검증자 단계 존재
  [불변식] 작성자≠검증자      : 검증자 profile ≠ 직전 producer profile
  [불변식] 게이트 겹침 금지    : 한 stage 에 sam_gate + 검증자 downstream 동시 금지
                              (카드당 block 하나 → sam_gate 가 검증 게이트를 덮어써 우회 발생)
  [경고]   미등록 profile     : profiles-src/ 에 없는 profile (거부가 아니라 "생성할까요?" — docs/12 §2⑤)

사용
  python3 scripts/lint_template.py trend-report              # 이름 또는 경로
  python3 scripts/lint_template.py templates/*.yaml          # 여러 개
  python3 scripts/lint_template.py --all                     # templates/ 전체(_ 로 시작하는 것 제외)

exit: 0 통과(경고는 허용) · 1 불변식 위반 · 2 usage/로드 실패
"""
from __future__ import annotations
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instantiate_template import (  # noqa: E402  단일 진실 — 검사 로직은 여기 한 곳
    REPO_ROOT, check_invariants, load_template, missing_profiles, registered_profiles,
)

__all__ = ["check_invariants", "missing_profiles", "registered_profiles", "lint"]


def lint(name_or_path: str) -> tuple[list[str], list[str]]:
    """(위반, 경고) 반환."""
    tpl = load_template(name_or_path)
    return check_invariants(tpl), missing_profiles(tpl)


def all_templates() -> list[str]:
    d = os.path.join(REPO_ROOT, "templates")
    return [os.path.join(d, f) for f in sorted(os.listdir(d))
            if f.endswith((".yaml", ".yml")) and not f.startswith("_")]


def main() -> int:
    ap = argparse.ArgumentParser(description="템플릿 불변식 린터")
    ap.add_argument("templates", nargs="*", help="템플릿 이름 또는 경로")
    ap.add_argument("--all", action="store_true", help="templates/ 전체 검사")
    args = ap.parse_args()

    targets = all_templates() if args.all else args.templates
    if not targets:
        ap.print_usage(sys.stderr)
        print("검사할 템플릿을 지정하거나 --all 을 쓰라.", file=sys.stderr)
        return 2

    failed = 0
    for t in targets:
        label = os.path.basename(t).rsplit(".yaml", 1)[0]
        try:
            errs, warns = lint(t)
        except (OSError, ValueError) as e:
            print(f"✗ {label}: 로드 실패 — {e}")
            failed += 1
            continue
        if errs:
            failed += 1
            print(f"✗ {label}: 불변식 위반 {len(errs)}건")
            for e in errs:
                print(f"    - {e}")
        else:
            print(f"✓ {label}: 불변식 통과")
        if warns:
            print(f"  ⚠ 미등록 profile {len(warns)}종: {', '.join(warns)}")
            print(f"    → profiles-src/<name>/(SOUL·config) + hermes profile create 필요"
                  f"(Sam 승인 사항). 인스턴스화는 중단된다.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
