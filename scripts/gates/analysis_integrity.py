#!/usr/bin/env python3
r"""
객관 게이트: 분석·시각화 산출물의 무결성
========================================
민감도 분석이 **수학적으로 말이 되는지**, 선언한 변수·응답을 **빠짐없이** 다뤘는지,
표가 인용한 CSV 와 그림이 **실재**하는지, 그리고 **생성하지 못한 산출물을 숨기지 않았는지**
LLM 없이 검사한다.
출처: simforge 의 analyze/visualize 단계 — 이 자리에 게이트가 **없다**(evidence-critic 은
      LLM 크리틱). 신설.

⚠️ **Sobol 지수는 불변식이 있다.** 참값이라면 `0 ≤ S_i ≤ S_Ti ≤ 1` 이다. 원본
   `sensitivity_analysis.py` 의 `S_Ti` 는 **proxy**(bin 조건부 분산 평균)라 표본에 따라
   이 관계가 미세하게 깨질 수 있고, 스크립트도 `notes` 에 "approximations from sample
   variance" 라고 적어 둔다. 실측에서는 부동소수 잡음 수준(2.2e-16)이었으므로 **결함으로
   단정하지 않는다.** 다만 **보고서에 그 근사 사실이 실리는지는 아무도 강제하지 않는다** —
   지수만 표에 실리면 읽는 쪽은 참 Sobol 지수로 읽는다.
   → 불변식 위반은 허용 오차(`invariant_epsilon`) 밖일 때만 FAIL 하고,
     **근사 한계의 공시를 요구**한다(아키타입 O 의 '미검증 경로 공시'와 같은 계열).

⚠️ **우리 환경에는 matplotlib·numpy 가 없다**(실측: 둘 다 `ModuleNotFoundError`).
   그림을 만들 수 없다. 그런데 조용히 넘어가면 논문 산출물이 그림을 포함한다고 읽힌다.
   → `figures.md` 가 `figures_generated: true|false` 를 선언하게 하고,
     `false` 면 **`plot.py` 와 데이터 CSV 가 있어야** 한다(남이 그릴 수 있어야 한다) +
     보고서에 공시. `true` 인데 파일이 없으면 FAIL.

⚠️ **표가 인용한 CSV 는 실재해야 한다.** 원본 CLAUDE.md 는 "All numeric tables in
   Methods/Results MUST cite a CSV file in `08-paper-artifacts/data/`" 라고 선언하지만
   검사하지 않는다(`doc_links`·`reproduce_doc` 이 링크·명령에 하던 일을 데이터 인용에 한다).

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.analysis_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : 미션 디렉터리

기대 형식 (analysis.md)
  n_samples: 27
  ```sensitivity
  {"response": "drag", "n_samples": 27,
   "variables": [{"name": "mesh", "S_i": 0.62, "S_Ti": 0.71, "pearson": -0.8, "beta": -0.7}],
   "notes": "S_i·S_Ti 는 표본 분산 기반 근사치다"}
  ```

정책 필드(analysis_policy)
  min_samples (기본 12) · invariant_epsilon (기본 0.05)
  require_caveat (기본 true) · caveat_terms (기본 근사·approximation·proxy)
  data_dir (기본 data) · figures_manifest (기본 figures.md)
  require_plot_script (기본 true)

exit: 0 PASS · 1 FAIL · 2 usage/입력없음(fail-closed)
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
    print("ERROR: PyYAML 필요", file=sys.stderr); sys.exit(2)

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
SENS_BLOCK_RE = re.compile(r"```sensitivity\s*\n(.*?)\n```", re.DOTALL)
CSV_REF_RE = re.compile(r"([\w./-]+\.csv)")
DEFAULT_CAVEATS = ["근사", "approxim", "proxy", "추정치", "표본 분산"]


def load_policy(path: str, key: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get(key, {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get(key, {}) or {}


def mission_root(draft: str) -> str:
    p = os.path.abspath(draft)
    return p if os.path.isdir(p) else os.path.dirname(p)


def find(root: str, *names: str) -> str | None:
    for n in names:
        p = os.path.join(root, n)
        if os.path.isfile(p):
            return p
    return None


def declared_vars(root: str) -> list[str]:
    """hypothesis.md 의 독립변수 선언 — 분석이 빠뜨린 변수를 잡기 위한 기준."""
    p = find(root, "hypothesis.md", "01-hypothesis.md")
    if not p:
        return []
    text = open(p, encoding="utf-8").read()
    m = re.search(r"```independent_vars\s*\n(.*?)\n```", text, re.DOTALL)
    block = m.group(1) if m else text
    return [x.group(1).strip() for x in re.finditer(r"^\s*-\s*name:\s*(\S+)", block, re.MULTILINE)]


def field(text: str, key: str) -> str | None:
    m = re.search(rf"^\s*{re.escape(key)}\s*:\s*(\S.*?)\s*$", text, re.MULTILINE)
    return m.group(1).strip().strip('"\'') if m else None


def main() -> int:  # noqa: C901
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", default=None, help="미사용(gate_keeper 규약상 전달됨)")
    ap.add_argument("--draft", default=None, help="미션 디렉터리")
    args = ap.parse_args()

    if not args.draft:
        print("FAIL(usage): --draft 필수 — fail-closed", file=sys.stderr); return 2
    try:
        policy = load_policy(args.policy, "analysis_policy")
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e} — fail-closed", file=sys.stderr); return 2

    root = mission_root(args.draft)
    apath = find(root, "analysis.md", "05-analysis.md")
    if not apath:
        print(f"FAIL(usage): analysis.md 를 찾지 못했다({root}) — fail-closed", file=sys.stderr)
        return 2

    text = open(apath, encoding="utf-8").read()
    blocks = SENS_BLOCK_RE.findall(text)
    if not blocks:
        print(f"FAIL(usage): ```sensitivity``` 블록이 없다 — 민감도 분석 없이 파라미터 스윕의 "
              f"결론을 낼 수 없다. fail-closed", file=sys.stderr)
        return 2

    min_samples = int(policy.get("min_samples", 12))
    eps = float(policy.get("invariant_epsilon", 0.05))
    require_caveat = bool(policy.get("require_caveat", True))
    caveats = policy.get("caveat_terms") or DEFAULT_CAVEATS
    data_dir = policy.get("data_dir") or "data"
    fig_manifest = policy.get("figures_manifest") or "figures.md"
    require_plot = bool(policy.get("require_plot_script", True))

    fail = False
    want_vars = declared_vars(root)
    print(f"민감도 블록 {len(blocks)}개 · 선언 독립변수 {want_vars or '(선언 없음)'} · "
          f"불변식 허용오차 ±{eps}")

    responses = []
    for i, b in enumerate(blocks, 1):
        try:
            d = json.loads(b)
        except (ValueError, json.JSONDecodeError) as e:
            print(f"FAIL: {i}번째 sensitivity 블록이 JSON 이 아니다 ({e})")
            fail = True
            continue
        resp = d.get("response")
        responses.append(resp)
        n = d.get("n_samples")
        if n is None:
            print(f"FAIL: {resp}: `n_samples` 가 없다 — 표본 수 없이 지수를 해석할 수 없다")
            fail = True
        elif int(n) < min_samples:
            print(f"FAIL: {resp}: 표본 {n} < 하한 {min_samples} — 표본이 적으면 분산 기반 "
                  f"지수는 잡음이다")
            fail = True

        vs = d.get("variables") or []
        names = [v.get("name") for v in vs]
        if want_vars:
            miss = [v for v in want_vars if v not in names]
            if miss:
                print(f"FAIL: {resp}: 선언한 독립변수 {miss} 가 분석에서 빠졌다 — 빠뜨린 "
                      f"변수는 '영향 없음'과 다르다")
                fail = True
        for v in vs:
            nm, si, sti = v.get("name"), v.get("S_i"), v.get("S_Ti")
            if si is None or sti is None:
                print(f"FAIL: {resp}/{nm}: S_i 또는 S_Ti 가 없다")
                fail = True
                continue
            try:
                si, sti = float(si), float(sti)
            except (TypeError, ValueError):
                print(f"FAIL: {resp}/{nm}: S_i·S_Ti 가 수가 아니다")
                fail = True
                continue
            if not (-eps <= si <= 1 + eps) or not (-eps <= sti <= 1 + eps):
                print(f"FAIL: {resp}/{nm}: 지수가 [0,1] 밖이다 (S_i={si}, S_Ti={sti})")
                fail = True
            elif si - sti > eps:
                print(f"FAIL: {resp}/{nm}: S_i({si}) > S_Ti({sti}) 가 허용오차 {eps} 를 "
                      f"넘는다 — 참 Sobol 지수라면 불가능하다. 표본을 늘리거나 계산을 "
                      f"확인하라")
                fail = True

        if require_caveat:
            note = str(d.get("notes", ""))
            if not any(c.lower() in note.lower() for c in caveats):
                print(f"FAIL: {resp}: `notes` 에 근사 한계가 적혀 있지 않다 — S_Ti 는 proxy 다. "
                      f"지수만 표에 실리면 읽는 쪽은 참 Sobol 지수로 읽는다"
                      f"(인정 표현: {caveats[:3]})")
                fail = True

    dup = sorted({r for r in responses if responses.count(r) > 1})
    if dup:
        print(f"FAIL: 응답변수 중복 블록 {dup}")
        fail = True

    # 표가 인용한 CSV 실재 — 원본이 선언만 하던 규칙
    refs = {os.path.basename(r) for r in CSV_REF_RE.findall(text)}
    ddir = os.path.join(root, data_dir)
    have = set(os.listdir(ddir)) if os.path.isdir(ddir) else set()
    ghosts = sorted(r for r in refs if r not in have)
    if refs:
        print(f"  인용 CSV {len(refs)}건 · {data_dir}/ 에 실재 {len(refs) - len(ghosts)}건")
    if ghosts:
        print(f"FAIL: 분석이 인용한 CSV 가 없다 {ghosts[:6]} — 수치의 출처를 따라갈 수 없다")
        fail = True

    # 그림 — 만들지 못했으면 공시하게 한다(matplotlib 이 없는 환경)
    fpath = os.path.join(root, fig_manifest)
    if not os.path.isfile(fpath):
        print(f"FAIL: {fig_manifest} 이 없다 — 그림을 만들었는지 못 만들었는지 알 수 없다")
        fail = True
    else:
        ftext = open(fpath, encoding="utf-8").read()
        gen = (field(ftext, "figures_generated") or "").lower()
        if gen not in ("true", "false"):
            print(f"FAIL: {fig_manifest} 에 `figures_generated: true|false` 선언이 없다")
            fail = True
        elif gen == "true":
            imgs = [n for n in (os.listdir(os.path.dirname(fpath)) if os.path.isdir(
                os.path.dirname(fpath)) else []) if n.lower().endswith((".png", ".pdf"))]
            figdir = os.path.join(root, "figures")
            if os.path.isdir(figdir):
                imgs += [n for n in os.listdir(figdir) if n.lower().endswith((".png", ".pdf"))]
            if not imgs:
                print(f"FAIL: `figures_generated: true` 인데 png/pdf 파일이 없다 — "
                      f"만들었다고 적었으면 있어야 한다")
                fail = True
        else:
            plot = find(root, "figures/plot.py", "plot.py")
            if require_plot and not plot:
                print(f"FAIL: 그림을 만들지 못했으면(`figures_generated: false`) 최소한 "
                      f"**`plot.py` 와 데이터가 있어야** 남이 그릴 수 있다 — 우리 환경에는 "
                      f"matplotlib·numpy 가 없다(실측)")
                fail = True
            elif not re.search(r"matplotlib|생성하지\s*못|not\s+generated|미생성", ftext, re.I):
                print(f"FAIL: 그림 미생성 사실과 사유가 {fig_manifest} 에 적혀 있지 않다 — "
                      f"조용히 넘어가면 논문 산출물이 그림을 포함한다고 읽힌다")
                fail = True
            else:
                print(f"  ✓ 그림 미생성 사실이 {fig_manifest} 에 공시되고 plot.py 가 있다")

    if not fail:
        print(f"  ✓ 민감도 지수가 불변식을 지키고 선언 변수를 모두 다뤘으며, 인용 CSV 가 "
              f"실재하고 그림 상태가 공시됐다")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
