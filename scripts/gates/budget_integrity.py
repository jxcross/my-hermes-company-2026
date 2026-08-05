#!/usr/bin/env python3
"""
객관 게이트: 예산 회계 정합 + 연차 상한
=========================================
예산표(CSV)가 **산술적으로 맞고**, **연차별 상한을 지키고**, **계획에 근거**하는지
LLM 없이 검사한다.
출처: proposalforge 의 Gate 1 중 예산 부분(`format_check.py`) — 이식하며 결함 3건을 고쳤다.

⚠️ **원본의 cap 검사는 세 가지 방법으로 빠져나갈 수 있었다**(전부 실측 · docs/13 §5):

  1. **Sum 열을 빼면 산술 검사가 통째로 사라진다.** `if sum_col >= 0` 이라 열이 없으면
     아무 행도 대조하지 않고 `budget_arithmetic PASS — ok` 를 찍는다. 검사할 것이 없다는
     사실이 통과로 보고된다(§5 '필드 하나를 빼면 그 항목이 검사에서 사라진다').
  2. **짧은 행은 통째로 증발한다.** `except (ValueError, IndexError): continue` 라
     열이 모자란 행은 합계에서 빠진다. 실측: `대형장비,900000000` 한 줄(연차 열 부족)을
     넣으면 9억이 **연차 총계에 잡히지 않고** cap 을 통과한다. 건너뛴 것을 세는 코드가 없다.
  3. **음수 행으로 상한을 깎는다.** 숫자 정규화가 `[^\\d-]` 라 `-` 를 남기므로
     `조정,-160000000,-160000000` 한 줄이면 연 3억짜리 예산이 1.4억으로 보고된다.

⚠️ **회계는 표 안에서 닫히면 안 된다.** 이 표는 `scripts/tools/budget_build.py` 가 만든다.
   도구가 만든 합계를 도구의 규칙으로 검사하면 **언제나 맞는다**(docs/13 §5 '표가 스스로를
   선언하고 스스로를 만족시킨다'). 그래서 분모를 표 밖에 고정한다:
     · 연차 수·상한·간접비율 → **SCOPE.md**(stage 1, Sam 승인 대상)
     · 인력·장비 근거      → **plan.md**(stage 9, 예산보다 먼저 쓰인다)
   연차 열을 줄여 상한을 피하는 것도 이것으로 막힌다.

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.budget_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : 미션 디렉터리(reports/<MID>)

기대 형식
  budget.csv:  비목,Year 1,…,Year N,Sum   (tools/budget_build.py 산출 형식)
  plan.md:
    ```resources
    - id: r1
      kind: personnel        # personnel | equipment | material | travel | etc
      item: 박사후연구원 1인
      year: 1
      ```

정책 필드(budget_policy)
  csv (기본 _private/bundle/budget.csv) · plan_file (기본 _private/plan.md)
  cap_per_year_krw · n_years · indirect_rate  — **SCOPE.md frontmatter 우선**
  require_sum_column (기본 true) · sum_aliases · total_row_prefix (기본 연차_총계)
  subtotal_row_prefix (기본 직접비_소계) · indirect_row_prefix (기본 간접비)
  allow_negative (기본 false) · min_total_krw (기본 1)
  categories : 필수 비목(행) 목록 · indirect_tolerance (기본 0.01)
  require_plan_basis (기본 true) — plan.md 선언과 예산 항목의 상호 근거

exit: 0 PASS · 1 FAIL · 2 usage/입력없음(fail-closed)
"""
from __future__ import annotations
import argparse
import csv
import json
import os
import re
import sys

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML 필요", file=sys.stderr); sys.exit(2)

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
YEAR_COL_RE = re.compile(r"^\s*Year\s*(\d+)\s*$", re.I)
RES_BLOCK_RE = re.compile(r"```resources\s*\n(.*?)\n```", re.DOTALL)
RES_ID_RE = re.compile(r"^\s*-\s*id:\s*(\S+)", re.MULTILINE)
FIELD_RE = re.compile(r"^\s+(\w+):\s*(.*)$")

# 자원 종류 → 예산 비목. plan.md 에 선언된 것이 예산에 계상됐는지 대조한다.
KIND_TO_CATEGORY = {
    "personnel": ["인건비", "학생인건비"],
    "equipment": ["장비비"],
    "material": ["재료비"],
    "travel": ["출장비"],
    "meeting": ["회의비"],
    "etc": ["기타"],
}


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("budget_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("budget_policy", {}) or {}


def mission_root(draft: str) -> str:
    p = os.path.abspath(draft)
    return p if os.path.isdir(p) else os.path.dirname(p)


def scope_value(root: str, key: str):
    try:
        m = FRONTMATTER_RE.match(open(os.path.join(root, "SCOPE.md"), encoding="utf-8").read())
    except OSError:
        return None
    if not m:
        return None
    return (yaml.safe_load(m.group(1)) or {}).get(key)


def parse_amount(cell: str) -> int | None:
    """금액 셀 → 정수. **파싱 실패는 None 이고 None 은 FAIL 이다**(원본은 조용히 0/건너뜀).
    천단위 콤마·원 표기·공백은 허용한다."""
    s = (cell or "").strip().replace(",", "").replace("원", "").replace(" ", "")
    if s in ("", "-", "—"):
        return 0
    if not re.fullmatch(r"[+-]?\d+", s):
        return None
    return int(s)


def parse_resources(path: str) -> list[dict] | None:
    """plan.md 의 ```resources``` 블록. 예산의 근거 선언 — 예산보다 먼저 쓰인다."""
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return None
    m = RES_BLOCK_RE.search(text)
    if not m:
        return None
    block = m.group(1)
    starts = list(RES_ID_RE.finditer(block))
    items = []
    for i, s in enumerate(starts):
        body = block[s.end():(starts[i + 1].start() if i + 1 < len(starts) else len(block))]
        it = {"id": s.group(1).strip()}
        for line in body.splitlines():
            mf = FIELD_RE.match(line)
            if mf:
                it[mf.group(1)] = mf.group(2).strip()
        items.append(it)
    return items


def main() -> int:  # noqa: C901
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", default=None, help="미사용(gate_keeper 규약상 전달됨)")
    ap.add_argument("--draft", default=None, help="미션 디렉터리(reports/<MID>)")
    args = ap.parse_args()

    if not args.draft:
        print("FAIL(usage): --draft 필수 — fail-closed", file=sys.stderr); return 2
    try:
        policy = load_policy(args.policy)
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e} — fail-closed", file=sys.stderr); return 2

    root = mission_root(args.draft)
    csv_path = os.path.join(root, policy.get("csv") or "_private/bundle/budget.csv")
    if not os.path.isfile(csv_path):
        print(f"FAIL(usage): 예산표가 없다({csv_path}) — fail-closed", file=sys.stderr)
        return 2

    cap = scope_value(root, "budget_cap_per_year_krw") or policy.get("cap_per_year_krw")
    n_years = scope_value(root, "n_years") or policy.get("n_years")
    rate = scope_value(root, "indirect_rate")
    rate = float(rate if rate is not None else policy.get("indirect_rate", 0.17))
    if not cap or not n_years:
        print("FAIL(usage): SCOPE.md 에 `budget_cap_per_year_krw`·`n_years` 선언이 없다 — "
              "**분모를 표 밖에 고정**해야 연차 열을 줄여 상한을 피하는 것을 막는다. "
              "fail-closed", file=sys.stderr)
        return 2
    cap, n_years = int(cap), int(n_years)

    try:
        with open(csv_path, encoding="utf-8", newline="") as f:
            rows = [r for r in csv.reader(f) if r and any(c.strip() for c in r)]
    except OSError as e:
        print(f"FAIL(usage): 예산표를 읽을 수 없다({e}) — fail-closed", file=sys.stderr)
        return 2
    if len(rows) < 2:
        print("FAIL(usage): 예산표에 데이터 행이 없다 — fail-closed", file=sys.stderr)
        return 2

    header = rows[0]
    year_cols = [(i, m.group(0).strip()) for i, h in enumerate(header)
                 if (m := YEAR_COL_RE.match(h))]
    sum_aliases = [s.lower() for s in (policy.get("sum_aliases") or ["sum", "합계", "총계"])]
    sum_col = next((i for i, h in enumerate(header) if h.strip().lower() in sum_aliases), -1)

    fail = False
    print(f"예산표 {os.path.relpath(csv_path, root)} · 연차 {len(year_cols)}열 "
          f"(선언 {n_years}) · 상한 {cap:,}/년 · 간접비율 {rate * 100:g}%")

    # ① 연차 열 수 = SCOPE 선언 — 열을 줄여 상한을 피하는 통로를 막는다
    if len(year_cols) != n_years:
        print(f"FAIL: 연차 열이 {len(year_cols)}개인데 SCOPE.md 선언은 {n_years}년 — "
              f"연차를 줄이면 연차별 상한 검사가 그만큼 헐거워진다")
        fail = True
    if not year_cols:
        print("FAIL: `Year N` 열이 없다 — 연차별 상한을 검사할 수 없다")
        print("VERDICT: FAIL")
        return 1

    # ② Sum 열 필수 — 없으면 산술 검사가 통째로 사라진다(원본 결함 #1)
    if bool(policy.get("require_sum_column", True)) and sum_col < 0:
        print(f"FAIL: 합계 열({policy.get('sum_aliases') or ['Sum', '합계', '총계']})이 없다 — "
              f"원본은 이때 **아무 행도 대조하지 않고 '산술 ok'** 를 찍었다")
        fail = True

    subtotal_pre = policy.get("subtotal_row_prefix") or "직접비_소계"
    indirect_pre = policy.get("indirect_row_prefix") or "간접비"
    total_pre = policy.get("total_row_prefix") or "연차_총계"
    allow_neg = bool(policy.get("allow_negative", False))

    item_totals = [0] * len(year_cols)        # 비목 행(소계·간접비·총계 제외)의 연차 합
    indirect_row: list[int] | None = None
    subtotal_row: list[int] | None = None
    total_row: list[int] | None = None
    cat_totals: dict[str, int] = {}           # 비목 → 전 연차 합계(계획 근거 대조용)

    for r in rows[1:]:
        label = (r[0] or "").strip()
        if not label or label.startswith("#"):
            continue
        # ③ 모든 행이 파싱돼야 한다 — 짧은 행·비수치 셀은 FAIL(원본 결함 #2)
        if len(r) <= max(i for i, _ in year_cols):
            print(f"FAIL: 행 '{label}' 의 열이 모자라다({len(r)}열) — 원본은 이런 행을 "
                  f"`continue` 로 건너뛰어 **금액이 합계에서 증발**했다(실측: 9억 누락)")
            fail = True
            continue
        vals = [parse_amount(r[i]) for i, _ in year_cols]
        if any(v is None for v in vals):
            bad = [year_cols[k][1] for k, v in enumerate(vals) if v is None]
            print(f"FAIL: 행 '{label}' 의 {bad} 셀이 숫자가 아니다 — 원본은 숫자가 아닌 셀을 "
                  f"0 으로 읽었다(금액을 적어 놓고 0 으로 계상되는 것이 더 위험하다)")
            fail = True
            continue
        # ④ 음수 금지 — 조정 행으로 상한을 깎는 통로(원본 결함 #3)
        if not allow_neg and any(v < 0 for v in vals):
            print(f"FAIL: 행 '{label}' 에 음수가 있다 — 원본은 음수 조정 행 하나로 연 3억짜리 "
                  f"예산을 1.4억으로 보고했다")
            fail = True

        # ⑤ 행 합계 = 연차 합
        if sum_col >= 0 and sum_col < len(r):
            got = parse_amount(r[sum_col])
            if got is None:
                print(f"FAIL: 행 '{label}' 의 합계 셀이 숫자가 아니다")
                fail = True
            elif got != sum(vals):
                print(f"FAIL: 행 '{label}' 합계 {got:,} ≠ 연차 합 {sum(vals):,}")
                fail = True

        if label.startswith(indirect_pre):
            indirect_row = vals
        elif label.startswith(subtotal_pre):
            subtotal_row = vals
        elif label.startswith(total_pre):
            total_row = vals
        else:
            cat_totals[label] = cat_totals.get(label, 0) + sum(vals)
            for k, v in enumerate(vals):
                item_totals[k] += v

    # ⑥ 필수 비목
    for c in list(policy.get("categories") or []):
        if c not in cat_totals:
            print(f"FAIL: 필수 비목 '{c}' 행이 없다")
            fail = True

    # ⑦ 소계·간접비·총계 정합
    if subtotal_row is not None and subtotal_row != item_totals:
        print(f"FAIL: 직접비 소계 {subtotal_row} ≠ 비목 합 {item_totals}")
        fail = True
    if indirect_row is None:
        print(f"FAIL: 간접비 행('{indirect_pre}…')이 없다 — NRF 예산은 간접비를 별도 계상한다")
        fail = True
    else:
        tol = float(policy.get("indirect_tolerance", 0.01))
        for k, (d, ind) in enumerate(zip(item_totals, indirect_row), start=1):
            want = d * rate
            if abs(ind - want) > max(1.0, abs(want) * tol):
                print(f"FAIL: Year {k} 간접비 {ind:,} ≠ 직접비 {d:,} × {rate * 100:g}% "
                      f"= {want:,.0f} — 간접비율은 SCOPE.md 선언이 기준이다(원본은 "
                      f"CLAUDE.md 에 17% 를 적어 두고 **검사하지 않았다**)")
                fail = True

    # ⑧ 연차별 상한 — 총계 행이 있으면 그것도 대조
    totals = total_row if total_row is not None else \
        [d + (indirect_row[k] if indirect_row else 0) for k, d in enumerate(item_totals)]
    if total_row is not None and indirect_row is not None:
        want = [d + i for d, i in zip(item_totals, indirect_row)]
        if total_row != want:
            print(f"FAIL: 연차 총계 {total_row} ≠ 직접비+간접비 {want}")
            fail = True
    for k, t in enumerate(totals, start=1):
        if t > cap:
            print(f"FAIL: Year {k} 총계 {t:,} > 상한 {cap:,} (초과 {t - cap:,})")
            fail = True
    grand = sum(totals)
    if grand < int(policy.get("min_total_krw", 1)):
        print(f"FAIL: 총액 {grand:,} — 예산이 없는 제안서다(공집합 통과 방지)")
        fail = True
    print(f"  연차 총계 {[f'{t:,}' for t in totals]} · 총액 {grand:,}")

    # ⑨ 계획 근거 — plan.md 의 자원 선언과 예산 비목의 상호 근거
    if bool(policy.get("require_plan_basis", True)):
        plan_path = os.path.join(root, policy.get("plan_file") or "_private/plan.md")
        res = parse_resources(plan_path)
        if res is None:
            print(f"FAIL: {os.path.basename(plan_path)} 의 ```resources``` 블록이 없다 — "
                  f"예산의 근거는 **예산보다 먼저 쓰인 계획**이어야 한다(도구가 만든 표를 "
                  f"도구의 규칙으로 검사하면 언제나 맞는다)")
            fail = True
        elif not res:
            print(f"FAIL: {os.path.basename(plan_path)} 의 ```resources``` 블록이 비었다 — "
                  f"자원 선언 0건이면 '계획에 없는 예산' 검사가 통째로 무력해진다"
                  f"(공집합이 통과하는 자리)")
            fail = True
        else:
            # 계획이 요구하는 비목 집합. 한 자원 종류가 두 비목에 걸치면(인건비·학생인건비)
            # 둘 중 **하나 이상**이 계상되면 충족으로 본다.
            groups = [KIND_TO_CATEGORY.get(str(r_.get("kind", "")).lower(), [])
                      for r_ in res]
            unknown = [r_["id"] for r_, g in zip(res, groups) if not g]
            if unknown:
                print(f"FAIL: 자원 {unknown} 의 `kind:` 가 알 수 없는 값이다 "
                      f"(허용: {sorted(KIND_TO_CATEGORY)}) — 분류할 수 없는 선언은 "
                      f"어느 비목도 근거하지 못한다")
                fail = True
            funded = {c for c, v in cat_totals.items() if v > 0}
            for r_, g in zip(res, groups):
                if g and not (set(g) & funded):
                    print(f"FAIL: 계획 자원 '{r_['id']}'({r_.get('item', '')}) 의 비목 {g} 에 "
                          f"예산이 0 이다 — 계획한 것을 계상하지 않았다")
                    fail = True
            planned = {c for g in groups for c in g}
            for label in sorted(funded - planned):
                print(f"FAIL: 비목 '{label}' 에 {cat_totals[label]:,} 원이 잡혔는데 "
                      f"plan.md 의 ```resources``` 에 근거 선언이 없다 — 근거 없는 예산이다")
                fail = True
            print(f"  계획 자원 {len(res)}건 → 요구 비목 {sorted(planned)} · "
                  f"계상 비목 {sorted(funded)}")

    if not fail:
        print(f"  ✓ {len(year_cols)}개년 회계 정합 · 상한 준수 · 간접비율 {rate * 100:g}% 일치 "
              f"· 계획 근거 확인")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
