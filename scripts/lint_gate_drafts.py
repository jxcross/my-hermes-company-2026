#!/usr/bin/env python3
"""
하네스 ↔ 템플릿 `--draft` 정합 린터
====================================
E2E 픽스처가 각 게이트에 주는 `--draft` 가 **템플릿이 선언한 stage draft 와 같은지** 본다.

왜 필요한가 (docs/13 §5 · 아키타입 S 의 실미션 결함)
----------------------------------------------------
실미션에서 한 stage 의 객관 게이트는 `--draft` 를 **하나만 공유한다**
(`gate_keeper.py:239-247` — stage 의 `gate.draft` 하나를 그 stage 의 모든 게이트에 준다).
그런데 하네스는 **게이트마다** `DRAFTS` dict 로 편한 경로를 골라 준다. 그래서:

  · 하네스는 게이트마다 자기한테 맞는 draft 를 받아 **53/53 통과**
  · 실미션은 stage 하나의 draft 를 공유해서 **3종이 exit 2 로 fail-closed**

**하네스가 실미션보다 관대한 입력을 준 것**이고, 그 조합은 실미션에서만 드러났다.
이 린터는 그 간극을 커밋 전에 잡는다.

무엇을 보는가
  ① 하네스 draft ≠ 템플릿 stage draft                    → FAIL
  ② 한 stage 의 게이트들에 **서로 다른 draft** 를 준다     → FAIL (실미션에서 불가능한 조합)
  ③ 템플릿이 선언했는데 하네스가 한 번도 안 돌린 게이트    → WARN

⚠️ `ast` 로 읽는다 — 픽스처를 import·실행하지 않는다(빌드가 파일시스템을 건드린다).

사용
  python3 scripts/lint_gate_drafts.py            # 전체
  python3 scripts/lint_gate_drafts.py code-docs  # 템플릿 하나

exit: 0 정합 · 1 불일치 · 2 usage/error
"""
from __future__ import annotations
import argparse
import ast
import os
import sys

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML 필요 — 컨테이너 내부에서 실행하라", file=sys.stderr); sys.exit(2)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES = os.path.join(ROOT, "templates")
FIXTURES = os.path.join(ROOT, "scripts", "tests", "fixtures")

# 하네스 파일명 → 템플릿 이름. `run_all.py` 의 HARNESSES 와 짝이다.
# ⚠️ 여기 없는 템플릿은 **하네스가 없다**(아키타입 A~F). 그쪽은 `preflight_gates.py` 가 맡는다.
HARNESS_TO_TEMPLATE = {
    "policy": "policy-brief",
    "legal": "legal-draft",
    "docs": "code-docs",
    "lecture": "lecture-course",
    "migrate": "code-migration",
    "sec": "security-audit",
    "agent": "agent-eval",
    "dataset": "dataset-release",
    "repro": "repro-package",
    "sim": "sim-experiment",
    "proposal": "research-proposal",
    "rebuttal": "reviewer-response",
    "outreach": "outreach-content",
    "slide": "conference-slides",
}


def norm(draft, mid_token: str = "<MID>") -> str | None:
    """템플릿 draft 를 픽스처 기준(미션 루트 상대)으로 정규화.

    템플릿: `reports/<MID>/docs`  ·  픽스처: `docs`  →  둘 다 `docs`
    미션 루트 자신은 `.` 로 통일한다(`reports/<MID>` ↔ `.`).
    """
    if draft is None:
        return None
    s = str(draft).strip().strip('"').strip("'")
    if s in ("", "null", "None"):
        return None
    for pre in (f"reports/{mid_token}/", f"reports/{mid_token}"):
        if s.startswith(pre):
            s = s[len(pre):]
            break
    s = s.strip("/")
    return s or "."


def template_stage_drafts(name: str) -> dict[int, tuple[str | None, list[str]]]:
    for ext in (".yaml", ".yml"):
        p = os.path.join(TEMPLATES, name + ext)
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                tpl = yaml.safe_load(f) or {}
            break
    else:
        raise FileNotFoundError(f"templates/{name}.yaml 가 없다")
    out = {}
    for st in tpl.get("stages", []) or []:
        gate = st.get("gate") or {}
        objs = gate.get("objective") or []
        if objs:
            out[int(st.get("id"))] = (norm(gate.get("draft")), list(objs))
    return out


def _sig(fn: ast.FunctionDef) -> tuple[list[str], dict[str, object]]:
    """(파라미터 이름 순서, 기본값 map). 기본값은 상수만 담는다."""
    names = [a.arg for a in fn.args.args]
    defaults: dict[str, object] = {}
    for a, d in zip(fn.args.args[len(fn.args.args) - len(fn.args.defaults):], fn.args.defaults):
        if isinstance(d, ast.Constant):
            defaults[a.arg] = d.value
    return names, defaults


def fixture_drafts(harness: str) -> dict[str, set[str]]:
    """게이트 → 하네스가 그 게이트에 준 draft 들의 **집합**.

    ⚠️ 픽스처마다 `expect` 시그니처가 다르다 — 처음에 `run()` 의 기본값과 `draft=` 키워드만
       봤다가 4개 하네스를 통째로 "한 번도 안 돌린다" 로 오탐했다. 실제로는:
         · `docs.py`     : `expect(label, gate, want)` + 모듈 `DRAFTS[gate]`
         · `policy.py`   : `run(gate, draft="formats")` — run 쪽 기본값
         · `migrate.py`  : `expect(label, gate, draft, want)` — **draft 가 3번째 위치인자**
         · `repro/sim/dataset.py` : `expect(label, gate, want, show=False, draft=".")`
       **린터가 대상을 덜 읽으면 조용히 통과시킨다** — 게이트가 검사 대상이 아닌 파일을
       보고 있던 것(docs/11 §7 ⑧)과 같은 계열의 실수다. 그래서 시그니처를 읽어 해석한다.
    """
    path = os.path.join(FIXTURES, f"{harness}.py")
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    tree = ast.parse(open(path, encoding="utf-8").read(), filename=path)

    static: dict[str, str] = {}          # 모듈 DRAFTS
    sigs: dict[str, tuple[list[str], dict]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "DRAFTS" and isinstance(node.value, ast.Dict):
                    for k, v in zip(node.value.keys, node.value.values):
                        if isinstance(k, ast.Constant) and isinstance(v, ast.Constant):
                            static[str(k.value)] = norm(v.value) or "."
        if isinstance(node, ast.FunctionDef) and node.name in ("expect", "run"):
            sigs[node.name] = _sig(node)

    out: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fname = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
        if fname not in ("expect", "run") or fname not in sigs:
            continue
        names, defaults = sigs[fname]
        bound: dict[str, object] = {}
        for i, a in enumerate(node.args):
            if i < len(names) and isinstance(a, ast.Constant):
                bound[names[i]] = a.value
        for k in node.keywords:
            if k.arg and isinstance(k.value, ast.Constant):
                bound[k.arg] = k.value.value

        gate = bound.get("gate")
        if not isinstance(gate, str):
            continue
        if "draft" in bound:
            d = norm(bound["draft"]) or "."
        elif "draft" in defaults:
            d = norm(defaults["draft"]) or "."
        elif gate in static:
            d = static[gate]
        elif "run" in sigs and "draft" in sigs["run"][1]:
            d = norm(sigs["run"][1]["draft"]) or "."
        else:
            continue
        out.setdefault(gate, set()).add(d)
    # DRAFTS 에만 있고 호출에서 못 읽은 게이트도 반영
    for g, d in static.items():
        out.setdefault(g, set()).add(d)
    return out


def check(harness: str, tpl_name: str) -> list[str]:
    problems: list[str] = []
    stages = template_stage_drafts(tpl_name)
    fx = fixture_drafts(harness)
    declared_gates = {g for _d, objs in stages.values() for g in objs}

    for sid, (want, objs) in sorted(stages.items()):
        used: dict[str, set[str]] = {g: fx.get(g, set()) for g in objs}

        for g, ds in used.items():
            if not ds:
                problems.append(f"WARN stage {sid} · {g}: 하네스가 한 번도 안 돌린다")
                continue
            # ① 템플릿이 선언한 draft 로 **한 번이라도** 돌렸는가
            target = want if want is not None else "."
            if target not in ds:
                problems.append(
                    f"FAIL stage {sid} · {g}: 하네스가 템플릿 draft {target!r} 로 한 번도 안 돌린다"
                    f" (쓴 값: {sorted(ds)})")

        # ② 실미션 조합 — stage 의 모든 게이트가 **하나의 draft 를 공유**해서 돌아간 적이 있는가
        exercised = [ds for ds in used.values() if ds]
        if len(exercised) > 1:
            common = set.intersection(*exercised)
            if not common:
                problems.append(
                    f"FAIL stage {sid}: 게이트들이 공유하는 draft 가 없다 "
                    f"{ {g: sorted(d) for g, d in used.items()} } "
                    "— 실미션은 stage 당 하나를 공유하므로 이 조합은 한 번도 검증되지 않았다")

    for g in sorted(set(fx) - declared_gates):
        problems.append(f"WARN 하네스가 {g} 를 돌리는데 템플릿 stage 선언에 없다")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("template", nargs="?", help="템플릿 이름(생략하면 전체)")
    args = ap.parse_args()

    pairs = sorted(HARNESS_TO_TEMPLATE.items(), key=lambda kv: kv[1])
    if args.template:
        pairs = [(h, t) for h, t in pairs if t == args.template]
        if not pairs:
            print(f"{args.template}: 대응하는 E2E 하네스가 없다 "
                  "(아키타입 A~F — `preflight_gates.py` 로 확인하라)")
            return 0

    rc = 0
    for harness, tpl in pairs:
        try:
            problems = check(harness, tpl)
        except (OSError, ValueError, yaml.YAMLError, SyntaxError) as e:
            print(f"── {tpl} ({harness}.py) ──\n  ERROR: {e}")
            rc = max(rc, 2); continue
        fails = [p for p in problems if p.startswith("FAIL")]
        warns = [p for p in problems if p.startswith("WARN")]
        mark = "✗" if fails else ("△" if warns else "✓")
        print(f"{mark} {tpl:<20} ({harness}.py)"
              + (f"  FAIL {len(fails)} · WARN {len(warns)}" if problems else "  정합"))
        for p in problems:
            print(f"    {p}")
        if fails:
            rc = max(rc, 1)
    return rc


if __name__ == "__main__":
    sys.exit(main())
