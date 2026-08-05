#!/usr/bin/env python3
r"""
객관 게이트: 핵심 결과 재현 허용오차
=====================================
선언한 **모든** 핵심 결과가 실제로 측정됐고, 측정값이 `expected ± tolerance` 안인지
LLM 없이 검사한다.
출처: other_projects/harness-templates/.../reproforge/scripts/result_tolerance.py (HARD GATE)

⚠️ **`expected:` 를 빼면 그 지표는 검사에서 조용히 사라진다** (docs/13 §5 · 실측).
   원본 `parse_targets` 는 `expected` 가 없는 항목을 `continue` 로 건너뛴다. 그래서
   `- metric:` 을 3개 선언하고 그중 2개에서 `expected:` 만 지우면:
     `targets: 1, measured: 1, within: 1 · overall: PASS · exit=0`
   **검사 대상이 자기 검사 범위를 정한다.** 게다가 보고서에는 "targets: 1" 로 찍혀
   원래 3개였다는 사실조차 남지 않는다. → 선언된 `- metric:` **개수**와 파싱된 항목 수를
   대조해 어긋나면 FAIL 한다.

⚠️ **항목이 하나도 없으면 PASS 였다**(실측). `key_results:` 블록이 비어 있으면
   `targets=[]` → `n_missing == 0 and n_out == 0 and n_within == len(targets)` 가 모두 참 →
   **overall PASS**. 공집합이 통과하는 계열이 이번이 다섯 번째다(secforge 빈 블록 ·
   agentforge 0 runs · datasetforge 라이선스 선언 전무 · env_diff 패키지 0개).

⚠️ **빌드가 실패해도 통과한다**(실측). 원본 게이트는 `measurements:` 블록만 읽는다.
   설치 테스트 보고서에 `docker build: FAILED` · `smoke test: NOT RUN` 이라고 적혀 있어도
   그 아래 숫자만 있으면 PASS 다. **재현되지 않았음을 재현됐다고 판정한다** —
   이 파이프라인의 존재 이유와 정면으로 어긋난다.
   → 같은 보고서의 `run_status:` 를 함께 읽어 성공이 아니면 반려한다(`install_evidence`
     게이트와 겹치지만, 하나만 켜도 이 구멍이 막히도록 **의도적으로 이중화**했다).

⚠️ **허용오차 미선언 시 원본은 FAIL 한다.** 원본 CLAUDE.md 는 "Tolerance | abs: 0.02
   (사용자 미지정 시)" 를 기본값으로 선언하는데 코드에는 없어 `within()` 이 곧바로 False 를
   돌려준다(선언과 코드의 어긋남 · legalforge 계열의 거짓 FAIL). → 정책 기본값을 적용하고
   **적용했다는 사실을 출력**한다. 명시를 강제하고 싶으면 `require_explicit_tolerance: true`.

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.tolerance_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : 미션 디렉터리

기대 형식
  target.md      : ```key_results``` 블록(항목마다 metric·expected·tolerance)
  install-test.md: `run_status: success` 줄 + ```measurements``` 블록

정책 필드(tolerance_policy)
  default_abs (기본 0.02) · require_explicit_tolerance (기본 false)
  require_run_success (기본 true) · min_key_results (기본 1)

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
KR_BLOCK_RE = re.compile(r"```key_results\s*\n(.*?)\n```", re.DOTALL)
MEAS_BLOCK_RE = re.compile(r"```measurements\s*\n(.*?)\n```", re.DOTALL)
METRIC_START_RE = re.compile(r"^\s*-\s*metric:\s*(\S.*)$", re.MULTILINE)
FIELD_RE = re.compile(r"^\s+(\w+):\s*(.*)$")
NUM_RE = re.compile(r"^-?\d+(?:\.\d+)?$")
TOL_ABS_RE = re.compile(r"abs:\s*(-?\d+(?:\.\d+)?)")
TOL_REL_RE = re.compile(r"rel:\s*(-?\d+(?:\.\d+)?)")
MEAS_LINE_RE = re.compile(r"^\s*(\S+)\s*:\s*(-?\d+(?:\.\d+)?)\s*$", re.MULTILINE)
STATUS_RE = re.compile(r"^\s*run_status\s*:\s*(\S+)", re.MULTILINE)


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("tolerance_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("tolerance_policy", {}) or {}


def mission_root(draft: str) -> str:
    p = os.path.abspath(draft)
    return p if os.path.isdir(p) else os.path.dirname(p)


def find(root: str, *names: str) -> str | None:
    for n in names:
        p = os.path.join(root, n)
        if os.path.isfile(p):
            return p
    return None


def parse_key_results(block: str) -> tuple[list[dict], int]:
    """(파싱된 항목, 선언된 `- metric:` 개수). 둘이 다르면 조용히 빠진 항목이 있다."""
    starts = list(METRIC_START_RE.finditer(block))
    items = []
    for i, m in enumerate(starts):
        body = block[m.end():(starts[i + 1].start() if i + 1 < len(starts) else len(block))]
        item = {"metric": m.group(1).strip().rstrip(":,").strip(), "raw": body}
        for line in body.splitlines():
            mf = FIELD_RE.match(line)
            if mf:
                item[mf.group(1)] = mf.group(2).strip()
        items.append(item)
    return items, len(starts)


def main() -> int:  # noqa: C901
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", default=None, help="미사용(gate_keeper 규약상 전달됨)")
    ap.add_argument("--draft", default=None, help="미션 디렉터리")
    args = ap.parse_args()

    if not args.draft:
        print("FAIL(usage): --draft 필수 — fail-closed", file=sys.stderr); return 2
    try:
        policy = load_policy(args.policy)
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e} — fail-closed", file=sys.stderr); return 2

    root = mission_root(args.draft)
    tpath = find(root, "target.md", "01-target.md")
    mpath = find(root, "install-test.md", "06-install-test.md")
    if not tpath:
        print(f"FAIL(usage): target.md 를 찾지 못했다({root}) — 무엇을 재현하기로 했는지 "
              f"모르면 재현 여부도 알 수 없다. fail-closed", file=sys.stderr)
        return 2
    if not mpath:
        print(f"FAIL(usage): install-test.md 를 찾지 못했다({root}) — 설치 테스트 보고가 "
              f"없는 것을 '재현됨'으로 읽으면 안 된다. fail-closed", file=sys.stderr)
        return 2

    ttext = open(tpath, encoding="utf-8").read()
    mtext = open(mpath, encoding="utf-8").read()
    tb = KR_BLOCK_RE.search(ttext)
    if not tb:
        print(f"FAIL(usage): target.md 에 ```key_results``` 블록이 없다 — fail-closed",
              file=sys.stderr)
        return 2
    items, n_declared = parse_key_results(tb.group(1))

    default_abs = float(policy.get("default_abs", 0.02))
    require_explicit = bool(policy.get("require_explicit_tolerance", False))
    require_success = bool(policy.get("require_run_success", True))
    min_kr = int(policy.get("min_key_results", 1))

    fail = False

    # ① 빈 집합 방어 — 원본은 항목 0개를 PASS 로 읽었다
    if len(items) < min_kr:
        print(f"FAIL: 선언된 핵심 결과가 {len(items)}건 < 하한 {min_kr} — **원본은 항목이 "
              f"하나도 없으면 PASS 였다.** 검증할 것이 없는 재현 패키지는 재현을 주장할 수 없다")
        print("VERDICT: FAIL")
        return 1

    # ② 실행이 실제로 성공했는가 — 원본은 measurements 숫자만 봤다
    mstat = STATUS_RE.search(mtext)
    if require_success:
        if not mstat:
            print(f"FAIL: install-test.md 에 `run_status:` 선언이 없다 — **원본은 "
                  f"'docker build: FAILED · smoke test: NOT RUN' 이라고 적힌 보고서의 "
                  f"숫자만 읽고 PASS 했다**(실측)")
            fail = True
        elif mstat.group(1).lower() not in ("success", "ok", "passed"):
            print(f"FAIL: `run_status: {mstat.group(1)}` — 실행이 성공하지 않았는데 측정값이 "
                  f"적혀 있다. 재현되지 않은 것을 재현됐다고 판정할 수 없다")
            fail = True

    # ③ 선언 ↔ 파싱 대조 — `expected:` 를 빼서 검사를 지우는 것을 막는다
    missing_expected = [it["metric"] for it in items if not NUM_RE.match(str(it.get("expected", "")))]
    print(f"핵심 결과 선언 {n_declared}건 · 파싱 {len(items)}건 · "
          f"기본 허용오차 abs±{default_abs}")
    if missing_expected:
        print(f"FAIL: `expected:` 가 없거나 수가 아닌 항목 {missing_expected} — **원본은 이런 "
              f"항목을 조용히 건너뛰어 3개 중 1개만 검사하고 PASS 했다**(실측). "
              f"검사 대상이 자기 검사 범위를 정하게 된다")
        fail = True

    mb = MEAS_BLOCK_RE.search(mtext)
    if not mb:
        print(f"FAIL: install-test.md 에 ```measurements``` 블록이 없다 — 측정 없이 "
              f"재현을 주장할 수 없다")
        print("VERDICT: FAIL")
        return 1
    measured = {m.group(1): float(m.group(2)) for m in MEAS_LINE_RE.finditer(mb.group(1))}

    # ④ 커버리지 + 허용오차
    for it in items:
        metric = it["metric"]
        if not NUM_RE.match(str(it.get("expected", ""))):
            continue
        expected = float(it["expected"])
        raw = it.get("raw", "") + " " + str(it.get("tolerance", ""))
        ta = TOL_ABS_RE.search(raw)
        tr = TOL_REL_RE.search(raw)
        tol_abs = float(ta.group(1)) if ta else None
        tol_rel = float(tr.group(1)) if tr else None
        if tol_abs is None and tol_rel is None:
            if require_explicit:
                print(f"FAIL: {metric} 에 허용오차 선언이 없다(정책상 명시 필수)")
                fail = True
                continue
            tol_abs = default_abs
            note = f" (허용오차 미선언 → 정책 기본값 abs±{default_abs} 적용)"
        else:
            note = ""

        if metric not in measured:
            print(f"FAIL: {metric} 이 측정되지 않았다 — 선언한 핵심 결과는 전건 측정해야 한다")
            fail = True
            continue
        val = measured[metric]
        diff = abs(val - expected)
        ok = (tol_abs is not None and diff <= tol_abs) or \
             (tol_rel is not None and abs(expected) > 0 and diff / abs(expected) <= tol_rel)
        tol_s = ", ".join(x for x in (f"abs±{tol_abs}" if tol_abs is not None else "",
                                      f"rel±{tol_rel}" if tol_rel is not None else "") if x)
        print(f"  {'✓' if ok else '✗'} {metric:22s} 기대 {expected:<10} 측정 {val:<10} "
              f"차이 {diff:.6g} ({tol_s}){note}")
        if not ok:
            print(f"FAIL: {metric} 측정값이 허용오차를 벗어났다 — 재현되지 않았다. "
                  f"**허용오차를 넓히지 말고** 원인을 찾아라")
            fail = True

    extra = sorted(set(measured) - {it["metric"] for it in items})
    if extra:
        print(f"참고: 선언에 없는 측정값 {extra[:6]} — 나쁘지 않으나 핵심 결과로 볼 것이면 "
              f"target.md 에 선언하라")

    if not fail:
        print(f"  ✓ 선언한 핵심 결과 {len(items)}건이 전부 측정됐고 허용오차 안이다"
              f"(실행 성공 확인됨)")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
