#!/usr/bin/env python3
"""
빈 입력 프리플라이트 — 게이트가 **아무것도 재지 않는지** 미션 착수 전에 확인한다
=============================================================================
`<template>` 의 각 검증 stage 에 선언된 객관 게이트를 **텅 빈 미션**에 대고 돌려
**전부 non-zero exit** 인지 본다. 빈 미션을 통과시키는 게이트는 아무것도 재지 않는
게이트다 — 그런 게이트가 붙은 stage 는 사실상 게이트가 없다.

왜 필요한가
-----------
① **아키타입 A~F 는 E2E 하네스가 아예 없다**(`scripts/tests/fixtures/run_all.py` 는 G~T
   14종뿐). 그런데 캠페인 초반 후보들의 게이트 집합이 정확히 거기다.
② **공집합 버그가 이 저장소에서 11회 반복됐다.** `len(s) <= 1` · `all(...)` ·
   `not any(...)` · `glob` 0건 · 항목 0개는 전부 공집합에서 참이다.
③ 그리고 아키타입 Q 에서 새 모양이 나왔다 — **검사 대상이 있는데 측정값이 0** 인 경우
   (빈 섹션 파일 5개 + 빈 간트가 '규격 통과').

⚠️ **이 스크립트는 PASS 를 확인하지 않는다.** 정상 산출물에서 PASS 하는지는 E2E 하네스와
   단위 테스트의 몫이다(legalforge 게이트 2종이 **어떤 입력에도 FAIL** 이었던 반대 방향
   사고 — `docs/13 §5`). 둘 다 필요하다.

⚠️ **`--draft` 는 템플릿이 선언한 값을 그대로 쓴다.** 한 stage 의 객관 게이트는 draft 를
   **하나만 공유**하므로(`gate_keeper.py:239-247`), 게이트마다 편한 경로를 골라 주면
   실미션에서만 깨지는 조합을 영영 못 본다(아키타입 S 가 실제로 그랬다 · `docs/13 §5`).

사용
  python3 scripts/preflight_gates.py <template> [MID]
  python3 scripts/preflight_gates.py --all

exit: 0 전 게이트가 빈 입력을 반려 · 1 통과시킨 게이트 있음 · 2 usage/error
"""
from __future__ import annotations
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML 필요 — 컨테이너 내부에서 실행하라", file=sys.stderr); sys.exit(2)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES = os.path.join(ROOT, "templates")
GATES = os.path.join(ROOT, "scripts", "gates")


def load_template(name: str) -> dict:
    for ext in (".yaml", ".yml"):
        p = os.path.join(TEMPLATES, name + ext)
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    raise FileNotFoundError(f"templates/{name}.yaml 가 없다")


def gate_stages(tpl: dict) -> list[dict]:
    """객관 게이트를 선언한 stage 만."""
    out = []
    for st in tpl.get("stages", []) or []:
        objs = ((st.get("gate") or {}).get("objective")) or []
        if objs:
            out.append(st)
    return out


def scaffold(mid: str, tpl: dict) -> str:
    """텅 빈 미션 트리. **파일은 만들되 내용은 비운다** — 파일 부재와 내용 부재는 다르다.

    게이트가 '파일이 없어서' exit 2 를 내는 것과 '내용이 없어서' exit 1 을 내는 것은
    서로 다른 사건이다. 둘 다 non-zero 라 판정은 같지만, 우리가 알고 싶은 것은
    **내용이 비었을 때도 반려하는가** 이므로 파일은 존재하게 둔다.
    """
    d = tempfile.mkdtemp(prefix=f"preflight-{mid}-")
    root = os.path.join(d, "reports", mid)
    os.makedirs(os.path.join(root, "raw"), exist_ok=True)
    with open(os.path.join(root, "SCOPE.md"), "w", encoding="utf-8") as f:
        f.write("---\ntitle: preflight\n---\n\n# SCOPE\n")
    with open(os.path.join(root, "raw", "sources.yaml"), "w", encoding="utf-8") as f:
        f.write("sources: []\n")
    # 템플릿 policy 를 그대로 실은 pipeline.json — 게이트는 여기서 정책을 읽는다
    import json
    with open(os.path.join(root, "pipeline.json"), "w", encoding="utf-8") as f:
        json.dump({"mission": mid, "policy": tpl.get("policy") or {}, "stages": []}, f)
    return d


def draft_abs(base: str, mid: str, declared, root: str) -> str | None:
    """템플릿이 선언한 draft 경로를 프리플라이트 트리로 옮긴다(빈 파일/디렉터리로 생성)."""
    if not declared:
        return None
    rel = str(declared).replace("<MID>", mid)
    p = os.path.join(base, rel)
    # 확장자가 있으면 파일, 없으면 디렉터리로 본다
    if os.path.splitext(p)[1]:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if not os.path.exists(p):
            open(p, "w", encoding="utf-8").close()
    else:
        os.makedirs(p, exist_ok=True)
    return p


def check(name: str, verbose: bool = True) -> tuple[int, int, list[str]]:
    """(검사한 게이트 수, 통과시킨 게이트 수, 문제 목록)."""
    tpl = load_template(name)
    mid = "M-PREFLIGHT"
    base = scaffold(mid, tpl)
    root = os.path.join(base, "reports", mid)
    policy = os.path.join(root, "pipeline.json")
    sources = os.path.join(root, "raw", "sources.yaml")

    total, leaked, problems = 0, 0, []
    try:
        for st in gate_stages(tpl):
            gate = st.get("gate") or {}
            objs = gate["objective"]
            d = draft_abs(base, mid, gate.get("draft"), root)
            for g in objs:
                script = os.path.join(GATES, f"{g}.py")
                if not os.path.exists(script):
                    problems.append(f"stage {st.get('id')} · {g}: 게이트 스크립트가 없다")
                    continue
                cmd = ["python3", script, "--policy", policy, "--sources", sources]
                if d:
                    cmd += ["--draft", d]
                try:
                    rc = subprocess.run(cmd, capture_output=True, text=True,
                                        timeout=60).returncode
                except Exception as e:  # noqa: BLE001
                    rc = 2
                    problems.append(f"stage {st.get('id')} · {g}: 실행 오류 {e}")
                total += 1
                if rc == 0:
                    leaked += 1
                    problems.append(
                        f"stage {st.get('id')} · {g}: **빈 미션을 PASS 시켰다**"
                        f" (draft={gate.get('draft')})")
                if verbose:
                    mark = "‼️ PASS" if rc == 0 else ("reject" if rc == 1 else "reject(fail-closed)")
                    print(f"  stage {str(st.get('id')):>2} · {g:<26} exit={rc} {mark}")
    finally:
        shutil.rmtree(base, ignore_errors=True)
    return total, leaked, problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("template", nargs="?", help="템플릿 이름(확장자 없이)")
    ap.add_argument("mission", nargs="?", help="(무시됨 · 런북 호환용)")
    ap.add_argument("--all", action="store_true", help="templates/*.yaml 전부")
    args = ap.parse_args()

    if not args.template and not args.all:
        ap.error("템플릿 이름 또는 --all 이 필요하다")

    names = []
    if args.all:
        for fn in sorted(os.listdir(TEMPLATES)):
            if fn.endswith((".yaml", ".yml")) and not fn.startswith("_"):
                names.append(os.path.splitext(fn)[0])
    else:
        names = [args.template]

    rc = 0
    for n in names:
        print(f"── {n} ──")
        try:
            total, leaked, problems = check(n)
        except (OSError, ValueError, yaml.YAMLError) as e:
            print(f"  ERROR: {e}"); rc = max(rc, 2); continue
        if problems:
            print("  문제:")
            for p in problems:
                print(f"    - {p}")
        print(f"  {total - leaked}/{total} 게이트가 빈 입력을 반려"
              + (f"  ‼️ {leaked}건이 통과시켰다" if leaked else "  ✓"))
        if leaked or any("게이트 스크립트가 없다" in p for p in problems):
            rc = max(rc, 1)
    return rc


if __name__ == "__main__":
    sys.exit(main())
