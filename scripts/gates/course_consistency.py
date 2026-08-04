#!/usr/bin/env python3
"""
객관 게이트: 강의 산출물 간 정합성
====================================
병렬로 쓴 강의계획서·슬라이드·과제·퀴즈가 **같은 강의를 말하는지** LLM 없이 검사한다 —
학습목표 id · 주차 번호 · 성적 반영 비율.
출처: other_projects/harness-templates/.../lectureforge/scripts/format_consistency_check.py

⚠️ 이식하며 고친 것 (docs/13 §5):
  1. **성적 비중 합계 검사가 죽은 코드였다** — docstring 은 "Total grade weights sum to
     100% (±0.1)" 라고 선언하는데, 해당 분기의 본문이 **문자 그대로 `pass`** 다(원본
     116~119행). 비중이 60%든 140%든 아무 일도 일어나지 않는다. → 실제로 합산해 판정한다.
  2. **한국어 주차 표기를 하나도 못 읽었다** — `\\b(?:week|주차)\\s*(\\d+)\\b` 는 숫자가
     **뒤에** 오는 영어식만 잡는다. 국문은 `3주차`(숫자가 앞)라 실측 결과 `[]` 였고,
     canonical_weeks 가 빈 집합이 되어 **"강의계획서가 전 주차를 담는가" 검사가 공회전**했다.
     → `3주차`·`제3주`·`Week 3` 를 모두 인식한다.
  3. **LO 참조가 한국어 조사에서 무너졌다** — `\\blo\\d+\\b` (§5 반복 함정). → lookaround.

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.course_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : content/ 디렉터리(syllabus.md · slides/ · assignments/ · quiz/)

정본은 미션 루트의 `objectives.md` · `structure.md` · `assessment.md` 에서 읽는다.

정책 필드(course_policy)
  weight_total (기본 100) · weight_tolerance (기본 0.1)
  require_syllabus_covers_all_weeks (기본 true) · outputs (선언된 산출물 — SCOPE.md 우선)

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
BLOCK_RE = r"```{}\s*\n(.*?)\n```"
LO_RE = re.compile(r"(?<![0-9A-Za-z])(lo\d+)(?![0-9A-Za-z])", re.IGNORECASE)
# 국문 `3주차`·`제3주`, 영문 `Week 3`, 그리고 units 블록의 필드 형식 `week: 3` 을 모두 잡는다.
# (원본은 영문 산문형만 잡아 국문 표기와 필드 표기를 통째로 놓쳤다.)
WEEK_RES = [
    re.compile(r"제\s*(\d{1,2})\s*주"),
    re.compile(r"(\d{1,2})\s*주차"),
    re.compile(r"week\s*[:：]?\s*(\d{1,2})", re.IGNORECASE),
]
WEIGHT_FIELD_RE = re.compile(r"^\s*weight:\s*([0-9]+(?:\.[0-9]+)?)\s*%?\s*$", re.MULTILINE)


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("course_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("course_policy", {}) or {}


def scope_field(root: str, key: str):
    try:
        m = FRONTMATTER_RE.match(open(os.path.join(root, "SCOPE.md"), encoding="utf-8").read())
    except OSError:
        return None
    return (yaml.safe_load(m.group(1)) or {}).get(key) if m else None


def block(text: str, name: str) -> str | None:
    m = re.search(BLOCK_RE.format(name), text, re.DOTALL)
    return m.group(1) if m else None


def weeks(text: str) -> set[int]:
    out: set[int] = set()
    for rx in WEEK_RES:
        out |= {int(x) for x in rx.findall(text)}
    return out


def los(text: str) -> set[str]:
    return {x.lower() for x in LO_RE.findall(text)}


def read_all(path: str) -> str:
    if os.path.isfile(path):
        return open(path, encoding="utf-8").read()
    if os.path.isdir(path):
        parts = []
        for dirpath, _d, names in os.walk(path):
            for n in sorted(names):
                if n.endswith(".md"):
                    parts.append(open(os.path.join(dirpath, n), encoding="utf-8").read())
        return "\n".join(parts)
    return ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", default=None, help="미사용(gate_keeper 규약상 전달됨)")
    ap.add_argument("--draft", default=None, help="content/ 디렉터리")
    args = ap.parse_args()

    if not args.draft or not os.path.isdir(args.draft):
        print("FAIL(usage): --draft(content/ 디렉터리) 필요 — fail-closed", file=sys.stderr); return 2
    try:
        policy = load_policy(args.policy)
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e} — fail-closed", file=sys.stderr); return 2

    root = os.path.dirname(os.path.abspath(args.draft))
    paths = {n: os.path.join(root, f"{n}.md") for n in ("objectives", "structure", "assessment")}
    for n, p in paths.items():
        if not os.path.isfile(p):
            print(f"FAIL(usage): 정본이 없다({p}) — fail-closed", file=sys.stderr); return 2

    obj_text = open(paths["objectives"], encoding="utf-8").read()
    st_text = open(paths["structure"], encoding="utf-8").read()
    as_text = open(paths["assessment"], encoding="utf-8").read()

    canonical_los = los(block(obj_text, "objectives") or obj_text)
    canonical_weeks = weeks(block(st_text, "units") or st_text)

    outputs = scope_field(root, "outputs") or policy.get("outputs") \
        or ["syllabus", "slides", "assignments", "quiz"]
    outputs = [str(x).strip().lower() for x in outputs]
    weight_total = float(policy.get("weight_total", 100))
    tol = float(policy.get("weight_tolerance", 0.1))
    require_weeks = bool(policy.get("require_syllabus_covers_all_weeks", True))

    print(f"정본 학습목표 {len(canonical_los)}개 · 주차 {sorted(canonical_weeks) or '없음'} "
          f"· 선언 산출물 {outputs}")

    fail = False
    if not canonical_weeks:
        print("FAIL: 주차 구조에서 주차 번호를 하나도 읽지 못했다 — `1주차`·`제1주`·`Week 1` "
              "중 한 형식으로 적어야 한다")
        fail = True

    # ① 선언된 산출물 존재 + LO 참조 정합
    present = {}
    for name in outputs:
        f = os.path.join(args.draft, f"{name}.md")
        d = os.path.join(args.draft, name)
        if os.path.isfile(f):
            present[name] = f
        elif os.path.isdir(d) and any(x.endswith(".md") for x in os.listdir(d)):
            present[name] = d
        else:
            print(f"FAIL: 선언된 산출물 {name} 이 없다 — 병렬 집필 워커가 실패했을 수 있다")
            fail = True
    for name, p in present.items():
        text = read_all(p)
        unknown = sorted(los(text) - canonical_los)
        if unknown:
            print(f"FAIL: {name} 이 정의되지 않은 학습목표를 참조한다 {unknown}")
            fail = True

    # ② 강의계획서의 주차 커버리지
    if require_weeks and "syllabus" in present and canonical_weeks:
        sw = weeks(read_all(present["syllabus"]))
        missing = sorted(canonical_weeks - sw)
        if missing:
            print(f"FAIL: 강의계획서에 빠진 주차 {missing} — 학생이 받는 문서가 실제 운영과 "
                  f"어긋난다")
            fail = True

    # ③ 성적 반영 비율 합계 — **원본에서 죽어 있던 검사**
    weights = [float(x) for x in WEIGHT_FIELD_RE.findall(as_text)]
    if not weights:
        print(f"FAIL: 평가 계획에 `weight:` 필드가 없다 — 성적 비중을 기계가 셀 수 없다"
              f"(각 평가 항목에 `weight: 20` 형식으로 적어라)")
        fail = True
    else:
        s = sum(weights)
        ok = abs(s - weight_total) <= tol
        print(f"성적 반영 비율 합계 {s:g}% (목표 {weight_total:g}±{tol:g}) {'✓' if ok else '✗'}")
        if not ok:
            print(f"FAIL: 성적 비중 합계가 {s:g}% 다 — 원본은 이 검사를 선언만 하고 "
                  f"본문이 `pass` 였다(죽은 코드)")
            fail = True

    if not fail:
        print("  ✓ 학습목표·주차·성적 비중이 산출물 간 일치")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
