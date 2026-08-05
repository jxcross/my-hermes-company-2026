#!/usr/bin/env python3
r"""
객관 게이트: 제안서 추적성 사슬 (공백 → 세부목표 → 활동 → 일정 · 방법)
=========================================================================
연구 공백(gap)이 세부목표를 낳고, 세부목표가 활동을 낳고, 활동이 **일정표와 방법 절에
실제로 배치**됐는지 — 그 사슬을 LLM 없이 검사한다.
출처: proposalforge — **스크립트가 없다.** 신설.

⚠️ **원본은 이 사슬을 규약으로만 선언한다.** CLAUDE.md 에 "Gantt 는 methods 섹션의 연차별
   활동과 **1:1 매칭**" 이라고 적어 두고, 검사하는 코드는 `format_check.py` 의

       if not GANTT_RE.search(text): FAIL          # mermaid gantt 블록이 있는가

   한 줄뿐이다. 실측: ````mermaid\ngantt\n```` 만 있는 **빈 도표**가 "timeline_format PASS"
   다. 1:1 매칭은 어디에서도 대조되지 않는다(docs/13 §5 'docstring 은 검사한다는데 코드는
   안 하는 게이트' 의 상위 문서판).

   제안서에서 이 사슬이 끊기는 것은 심사에서 가장 자주 지적되는 결함이다 — 목표는 거창한데
   활동이 없거나, 일정표에 목표와 무관한 작업이 들어 있거나, 방법 절이 계획과 다른 것을
   서술한다. **각 단계를 사람이 읽어야 아는 것이 아니라 id 로 대조할 수 있다.**

⚠️ **환각 공백을 막는다.** gap 은 landscape 조사에서 나와야 한다 — 각 gap 이 인용한 출처 id 가
   `sources.yaml` 에 실재하는지 본다(policyforge 의 환각 인용 교훈과 같은 자리).

⚠️ **역방향도 본다.** 모든 세부목표가 최소 1개 활동을 가져야 하고(활동 없는 목표는 선언일
   뿐이다), 일정표에 활동 아닌 task 가 있으면 안 된다(lecture-course 의 '빈 주차' 교훈).

⚠️ **한국어 조사**(docs/13 §5): 본문에서 활동 id 는 `a1을`·`a3의` 처럼 조사가 붙는다.
   `\ba1\b` 는 `1`↔`을` 사이에 경계가 없어 **한 건도 못 읽는다.** lookaround 로 잡는다.

두 모드 (아키타입 K·P 와 같은 방식 — 판정 첫 줄에 출력한다)
  · plan  — 일정표·섹션이 아직 없다. gap↔목표↔활동까지 본다(설계 검증 단계).
  · final — 일정표·방법 절까지 배치됐는지 본다.

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.trace_policy)
  --sources <path>  : sources.yaml (gap 이 인용한 출처의 실재 확인)
  --draft   <path>  : 미션 디렉터리(reports/<MID>)

기대 형식
  landscape.md:  ```gaps
                 - id: g1
                   sources: [acad_kim_2024, ntis_2023_001]
                   statement: 국내 데이터에 대한 검증이 없다
                 ```
  outline.md:    ```objectives
                 - id: s1
                   gaps: [g1]
                   statement: 국내 데이터 기반 검증 체계를 만든다
                 ```
                 ```activities
                 - id: a1
                   objective: s1
                   year: 1
                   title: 데이터 수집 프로토콜 설계
                 ```
  bundle/timeline.md:  mermaid gantt 의 각 task 가 활동 id 를 담는다
                       `데이터 수집 프로토콜 설계 :a1, 2026-03-01, 120d`

정책 필드(trace_policy)
  landscape_file (기본 _private/landscape.md) · outline_file (기본 _private/outline.md)
  timeline_file (기본 _private/bundle/timeline.md)
  methods_file (기본 _private/bundle/sections/methods.md)
  min_objectives (기본 2) · max_objectives (기본 5) · min_gaps (기본 2)
  min_activities_per_objective (기본 1) · require_gap_sources (기본 true)
  n_years — SCOPE.md frontmatter 우선. 활동의 `year:` 가 이 범위 안이어야 한다

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
ID_RE = re.compile(r"^\s*-\s*id:\s*(\S+)", re.MULTILINE)
FIELD_RE = re.compile(r"^\s+(\w+):\s*(.*)$")
GANTT_DIRECTIVE = ("gantt", "title", "dateformat", "axisformat", "section",
                   "excludes", "todaymarker", "tickinterval", "weekday")


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("trace_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("trace_policy", {}) or {}


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


def parse_block(path: str, name: str) -> list[dict] | None:
    """```<name>``` 블록의 `- id:` 항목들. 파일·블록이 없으면 None."""
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return None
    m = re.search(rf"```{name}\s*\n(.*?)\n```", text, re.DOTALL)
    if not m:
        return None
    block = m.group(1)
    starts = list(ID_RE.finditer(block))
    out = []
    for i, s in enumerate(starts):
        body = block[s.end():(starts[i + 1].start() if i + 1 < len(starts) else len(block))]
        it = {"id": s.group(1).strip()}
        for line in body.splitlines():
            mf = FIELD_RE.match(line)
            if mf:
                it[mf.group(1)] = mf.group(2).strip()
        out.append(it)
    return out


def id_list(raw: str) -> list[str]:
    """`[g1, g2]` 또는 `g1, g2` 또는 `g1` → ['g1','g2']."""
    return [t for t in re.split(r"[,\s]+", (raw or "").strip().strip("[]")) if t]


def mentions(text: str, token: str) -> bool:
    """조사가 붙어도 잡는다 — `a1을`·`a1의`·`(a1)`. `\\b` 는 국문에서 무너진다."""
    return re.search(rf"(?<![0-9A-Za-z_]){re.escape(token)}(?![0-9A-Za-z_])", text) is not None


def gantt_tasks(text: str) -> list[str] | None:
    m = re.search(r"```mermaid\s*\n(.*?)```", text, re.DOTALL)
    if not m or not re.search(r"^\s*gantt\b", m.group(1), re.MULTILINE):
        return None
    tasks = []
    for line in m.group(1).splitlines():
        s = line.strip()
        if not s or s.startswith("%%"):
            continue
        head = s.split(":", 1)[0].strip().lower()
        if head in GANTT_DIRECTIVE or s.lower().startswith(GANTT_DIRECTIVE):
            continue
        if ":" in s:
            tasks.append(s)
    return tasks


def source_ids(path: str | None) -> set[str]:
    if not path or not os.path.isfile(path):
        return set()
    try:
        data = yaml.safe_load(open(path, encoding="utf-8").read())
    except (OSError, yaml.YAMLError):
        return set()
    items = data.get("sources") if isinstance(data, dict) else data
    if not isinstance(items, list):
        return set()
    return {str(it.get("id")) for it in items if isinstance(it, dict) and it.get("id")}


def main() -> int:  # noqa: C901
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", default=None, help="sources.yaml — gap 인용의 실재 확인")
    ap.add_argument("--draft", default=None, help="미션 디렉터리(reports/<MID>)")
    args = ap.parse_args()

    if not args.draft:
        print("FAIL(usage): --draft 필수 — fail-closed", file=sys.stderr); return 2
    try:
        policy = load_policy(args.policy)
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e} — fail-closed", file=sys.stderr); return 2

    root = mission_root(args.draft)
    land_p = os.path.join(root, policy.get("landscape_file") or "_private/landscape.md")
    out_p = os.path.join(root, policy.get("outline_file") or "_private/outline.md")
    tl_p = os.path.join(root, policy.get("timeline_file") or "_private/bundle/timeline.md")
    me_p = os.path.join(root, policy.get("methods_file") or "_private/bundle/sections/methods.md")
    mode = "final" if os.path.isfile(tl_p) else "plan"

    gaps = parse_block(land_p, "gaps")
    objs = parse_block(out_p, "objectives")
    acts = parse_block(out_p, "activities")
    if gaps is None or objs is None or acts is None:
        miss = [n for n, v in (("landscape.md ```gaps```", gaps),
                               ("outline.md ```objectives```", objs),
                               ("outline.md ```activities```", acts)) if v is None]
        print(f"FAIL(usage): {miss} 블록을 찾지 못했다 — 사슬의 마디가 없으면 사슬을 잴 수 "
              f"없다. fail-closed", file=sys.stderr)
        return 2

    min_gaps = int(policy.get("min_gaps", 2))
    min_objs = int(policy.get("min_objectives", 2))
    max_objs = int(policy.get("max_objectives", 5))
    min_acts = int(policy.get("min_activities_per_objective", 1))
    n_years = scope_value(root, "n_years") or policy.get("n_years")

    print(f"모드={mode} · 공백 {len(gaps)} · 세부목표 {len(objs)} · 활동 {len(acts)}")
    fail = False

    # ① 공백 — 개수 하한 + 인용 출처의 실재(환각 gap 차단)
    if len(gaps) < min_gaps:
        print(f"FAIL: 연구 공백 {len(gaps)}건 < 하한 {min_gaps} — 공백이 없으면 세부목표의 "
              f"근거가 없다(공집합이 통과하는 자리)")
        fail = True
    known = source_ids(args.sources)
    gap_ids = [g["id"] for g in gaps]
    if bool(policy.get("require_gap_sources", True)):
        if not known:
            print(f"FAIL: sources.yaml 에서 출처 id 를 읽지 못했다({args.sources}) — "
                  f"공백의 근거를 대조할 수 없다")
            fail = True
        else:
            for g in gaps:
                cited = id_list(g.get("sources", ""))
                if not cited:
                    print(f"FAIL: 공백 '{g['id']}' 에 `sources:` 인용이 없다 — "
                          f"조사에서 나오지 않은 공백은 지어낸 공백이다")
                    fail = True
                    continue
                ghost = [c for c in cited if c not in known]
                if ghost:
                    print(f"FAIL: 공백 '{g['id']}' 이 sources.yaml 에 없는 출처 {ghost} 를 "
                          f"인용한다 — 환각 인용")
                    fail = True

    # ② 세부목표 — 개수 범위(분모 자기결정 차단) + gap 참조 실재
    if not (min_objs <= len(objs) <= max_objs):
        print(f"FAIL: 세부목표 {len(objs)}개가 범위 {min_objs}~{max_objs} 밖이다 — "
              f"1개로 줄이면 커버리지가 저절로 쉬워진다(code-docs 의 분모 자기결정과 같은 계열)")
        fail = True
    obj_ids = [o["id"] for o in objs]
    dup = sorted({i for i in obj_ids if obj_ids.count(i) > 1})
    if dup:
        print(f"FAIL: 세부목표 id 중복 {dup}")
        fail = True
    for o in objs:
        cited = id_list(o.get("gaps", ""))
        if not cited:
            print(f"FAIL: 세부목표 '{o['id']}' 에 `gaps:` 참조가 없다 — 어느 공백을 메우는지 "
                  f"밝히지 않은 목표다")
            fail = True
            continue
        ghost = [c for c in cited if c not in gap_ids]
        if ghost:
            print(f"FAIL: 세부목표 '{o['id']}' 이 실재하지 않는 공백 {ghost} 를 참조한다")
            fail = True
    # 역방향: 어느 목표도 메우지 않는 공백은 조사 낭비이거나 목표 누락이다
    covered_gaps = {c for o in objs for c in id_list(o.get("gaps", ""))}
    orphan_gaps = [g for g in gap_ids if g not in covered_gaps]
    if orphan_gaps:
        print(f"FAIL: 어떤 세부목표도 다루지 않는 공백 {orphan_gaps} — 공백을 찾아 놓고 "
              f"대응하지 않으면 심사자가 먼저 묻는다")
        fail = True

    # ③ 활동 — 목표 참조 실재 + 모든 목표가 활동을 가짐 + 연차 범위
    act_ids = [a["id"] for a in acts]
    dupa = sorted({i for i in act_ids if act_ids.count(i) > 1})
    if dupa:
        print(f"FAIL: 활동 id 중복 {dupa}")
        fail = True
    per_obj: dict[str, int] = {o["id"]: 0 for o in objs}
    for a in acts:
        ref = str(a.get("objective", "")).strip()
        if not ref:
            print(f"FAIL: 활동 '{a['id']}' 에 `objective:` 가 없다 — 목표에 매이지 않은 "
                  f"활동은 예산·일정의 근거가 되지 못한다")
            fail = True
        elif ref not in per_obj:
            print(f"FAIL: 활동 '{a['id']}' 이 실재하지 않는 세부목표 '{ref}' 를 참조한다")
            fail = True
        else:
            per_obj[ref] += 1
        if n_years:
            yr = str(a.get("year", "")).strip()
            if not yr.isdigit() or not (1 <= int(yr) <= int(n_years)):
                print(f"FAIL: 활동 '{a['id']}' 의 `year: {yr or '없음'}` 이 연구기간 "
                      f"1~{n_years}년 밖이다")
                fail = True
    for oid, n in per_obj.items():
        if n < min_acts:
            print(f"FAIL: 세부목표 '{oid}' 에 활동이 {n}건 — 하한 {min_acts}. "
                  f"활동 없는 목표는 선언일 뿐이다(역방향 검사)")
            fail = True

    if mode == "plan":
        if not fail:
            print(f"  ✓ 공백 {len(gaps)} → 세부목표 {len(objs)} → 활동 {len(acts)} 사슬 정합 "
                  f"(일정·방법 배치는 final 모드에서 본다)")
        print("VERDICT:", "FAIL" if fail else "PASS")
        return 1 if fail else 0

    # ④ 일정 배치 — 원본이 "1:1 매칭"이라 선언만 하던 것
    tl_text = open(tl_p, encoding="utf-8").read()
    tasks = gantt_tasks(tl_text)
    if tasks is None:
        print(f"FAIL: {os.path.basename(tl_p)} 에 mermaid gantt 블록이 없다")
        fail = True
        tasks = []
    unplaced = [aid for aid in act_ids if not any(mentions(t, aid) for t in tasks)]
    if unplaced:
        print(f"FAIL: 일정표에 배치되지 않은 활동 {unplaced} — CLAUDE.md 가 'Gantt 는 methods "
              f"활동과 1:1 매칭' 이라 선언하지만 원본은 **블록의 존재만** 확인했다")
        fail = True
    orphan_tasks = [t for t in tasks if not any(mentions(t, aid) for aid in act_ids)]
    if orphan_tasks:
        print(f"FAIL: 활동에 없는 일정 task {len(orphan_tasks)}건 — 계획 밖의 일정이다")
        for t in orphan_tasks[:3]:
            print(f"       · {t[:70]}")
        fail = True

    # ⑤ 방법 절 서술 — 활동이 본문에 실제로 등장하는가
    try:
        me_text = open(me_p, encoding="utf-8").read()
    except OSError:
        print(f"FAIL: 방법 절이 없다({os.path.relpath(me_p, root)})")
        fail = True
        me_text = ""
    undescribed = [aid for aid in act_ids if not mentions(me_text, aid)]
    if undescribed:
        print(f"FAIL: 방법 절이 서술하지 않은 활동 {undescribed} — 일정표에만 있고 본문에 "
              f"없는 활동은 심사자가 검증할 수 없다(활동 id 를 본문에 명시하라)")
        fail = True

    if not fail:
        print(f"  ✓ 공백 {len(gaps)} → 세부목표 {len(objs)} → 활동 {len(acts)} → "
              f"일정 task {len(tasks)} · 방법 절 서술까지 사슬 정합")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
