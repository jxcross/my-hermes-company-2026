#!/usr/bin/env python3
"""
객관 게이트: 공고 정합 — 신청자격 + 평가지표 대응
====================================================
① 신청자 **자격**이 사업 요건을 만족하는지 ② 공고 **평가지표**마다 제안서의 어느 절이
어떻게 대응하는지가 **선언되고 실재하는지** LLM 없이 검사한다.
출처: proposalforge 의 Gate 2(`call_alignment_check.py`) — 이식하며 판정 방식을 바꿨다.

⚠️ **원본은 키워드를 셌다** — 그리고 그것은 검사가 아니다(실측 · docs/13 §5):
   5개 섹션에 아래 **한 줄씩**만 넣으면 전 지표가 통과한다.

       창의 창의 창의 novel 우수 우수 구체 구체 구체 정량 지표 추진 전략 기대 효과 활용 기여
       → 창의성 20/3 · 우수성 10/2 · 구체성 25/5 · 추진전략 10/2 · 기대효과 20/3 · PASS

   secforge 의 OWASP 게이트가 "A01…A10 은 앞으로 점검할 예정" 한 줄에 커버리지 10/10 을
   준 것과 같은 자리다 — **글자의 존재를 대응의 증거로 센다.**
   → 지표마다 **구조화된 대응 선언**(어느 절 · 무엇으로 · 최소 길이)을 요구하고, 선언한
     절이 실재하며 분량을 갖는지 대조한다. 키워드 빈도는 세지 않는다.

⚠️ **미상 사업명이면 자격 검사가 통째로 꺼졌다**(fail-open · 실측):
   `else: ok = True  # unknown program — eligibility not auto-checked`.
   사업명에 `기본연구` 라고 쓰면 박사 30년차도 신진 사업에 **PASS · exit=0** 이다.
   → 정책에 없는 사업명은 **FAIL**(fail-closed). 새 사업이면 정책에 자격창을 추가하라.

⚠️ **대표논문을 남의 인용에서 셌다**(실측): `- bibkey:` 를 파일 전체에서 찾으므로
   참고문헌 5건이면 리더연구자의 '대표논문 5편 이상' 이 충족된다.
   → `representative:` 블록 **안**의 항목만 센다.

두 모드 (아키타입 K 의 `atomic_commit`, P 의 `solver_pin` 과 같은 방식)
  · plan  — 섹션이 아직 없다(설계 검증 단계). 자격 + 대응 **선언**을 본다.
  · final — 섹션이 있다. 선언한 절의 **실재와 분량**까지 본다.
  모드는 섹션 디렉터리의 존재로 자동 판별하고 **판정 첫 줄에 출력**한다.

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.call_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : 미션 디렉터리(reports/<MID>)

기대 형식 (outline.md)
  ```criteria
  - id: 창의성
    section: aims
    evidence: 기존 X 계열은 …에 그쳤다. 본 연구는 Y 를 도입해 …를 처음으로 가능하게 한다.
  ```

정책 필드(call_policy)
  program                : SCOPE.md frontmatter 의 `nrf_program` 우선
  eligibility            : {신진: {max_years_post_phd: 7}, 리더: {min_years_post_phd: 10,
                            min_representative_pubs: 5}, ...}
  criteria               : 평가지표 목록(전건 대응 선언 필수)
  min_evidence_chars (기본 60) · outline_file (기본 _private/outline.md)
  context_file (기본 _private/context.md) · sections_dir (기본 _private/bundle/sections)
  min_section_words (기본 120)

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
CRIT_BLOCK_RE = re.compile(r"```criteria\s*\n(.*?)\n```", re.DOTALL)
CRIT_ID_RE = re.compile(r"^\s*-\s*id:\s*(.+)$", re.MULTILINE)
FIELD_RE = re.compile(r"^\s+(\w+):\s*(.*)$")
REPR_BLOCK_RE = re.compile(r"```representative\s*\n(.*?)\n```", re.DOTALL)
BIBKEY_RE = re.compile(r"^\s*-\s*bibkey:\s*(\S+)", re.MULTILINE)
YEARS_RE = re.compile(r"^\s*career_years_post_phd\s*:\s*(\d+)\s*$", re.MULTILINE)


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("call_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("call_policy", {}) or {}


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


def count_words(text: str) -> int:
    body = FRONTMATTER_RE.sub("", text, count=1)
    body = re.sub(r"```.*?```", " ", body, flags=re.DOTALL)
    body = re.sub(r"[#*_>`\[\]()|-]", " ", body)
    return len([w for w in body.split() if w.strip()])


def parse_criteria(path: str) -> list[dict] | None:
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return None
    m = CRIT_BLOCK_RE.search(text)
    if not m:
        return None
    block = m.group(1)
    starts = list(CRIT_ID_RE.finditer(block))
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


def match_program(program: str, rules: dict) -> tuple[str | None, dict]:
    """사업명 → 자격 규칙. 부분 일치를 허용하되 **못 찾으면 None**(fail-closed).
    `신진연구자사업(2026)` 처럼 접미가 붙는 것이 정상이라 부분 일치는 필요하다."""
    if not program:
        return None, {}
    for key, rule in rules.items():
        if key in program:
            return key, (rule or {})
    return None, {}


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
    outline_p = os.path.join(root, policy.get("outline_file") or "_private/outline.md")
    context_p = os.path.join(root, policy.get("context_file") or "_private/context.md")
    sec_dir = os.path.join(root, policy.get("sections_dir") or "_private/bundle/sections")
    mode = "final" if os.path.isdir(sec_dir) else "plan"

    program = scope_value(root, "nrf_program") or policy.get("program") or ""
    rules = policy.get("eligibility") or {}
    criteria = [str(c) for c in (policy.get("criteria") or [])]
    if not criteria or not rules:
        print("FAIL(usage): call_policy 에 `criteria`·`eligibility` 선언이 없다 — "
              "무엇에 맞춰야 하는지 모르면 정합을 잴 수 없다. fail-closed", file=sys.stderr)
        return 2

    print(f"모드={mode} · 사업 '{program}' · 평가지표 {len(criteria)}종")

    fail = False

    # ① 신청자격 — 미상 사업명은 FAIL(원본은 여기서 검사를 껐다)
    key, rule = match_program(program, rules)
    elig_fail = False
    if key is None:
        print(f"FAIL: 사업명 '{program or '(없음)'}' 에 대한 자격 규칙이 정책에 없다 — "
              f"원본은 이때 '자동 검사하지 않음'으로 **PASS** 를 줬다(박사 30년차도 신진 사업에 "
              f"통과했다). 새 사업이면 call_policy.eligibility 에 자격창을 추가하라")
        fail = True; elig_fail = True
    else:
        ctx = None
        try:
            ctx = open(context_p, encoding="utf-8").read()
        except OSError:
            print(f"FAIL: PI 정보 파일이 없다({os.path.relpath(context_p, root)}) — "
                  f"자격을 확인할 근거가 없다")
            fail = True; elig_fail = True
        if ctx is not None:
            my = YEARS_RE.search(ctx)
            if not my:
                print("FAIL: context.md 에 `career_years_post_phd:` 선언이 없다 — "
                      "자격창 판정의 유일한 입력이다")
                fail = True; elig_fail = True
            else:
                yrs = int(my.group(1))
                lo = rule.get("min_years_post_phd")
                hi = rule.get("max_years_post_phd")
                if lo is not None and yrs < int(lo):
                    print(f"FAIL: 자격 미달 — 박사 후 {yrs}년 < {key} 요건 {lo}년")
                    fail = True; elig_fail = True
                if hi is not None and yrs > int(hi):
                    print(f"FAIL: 자격 초과 — 박사 후 {yrs}년 > {key} 요건 {hi}년 "
                          f"(다른 사업으로 신청해야 한다)")
                    fail = True; elig_fail = True
                need_pubs = rule.get("min_representative_pubs")
                if need_pubs:
                    # **`representative` 블록 안**만 센다 — 원본은 파일 전체의 bibkey 를 셌다
                    mb = REPR_BLOCK_RE.search(ctx)
                    n = len(BIBKEY_RE.findall(mb.group(1))) if mb else 0
                    if not mb:
                        print("FAIL: context.md 에 ```representative``` 블록이 없다 — "
                              "원본은 참고문헌의 bibkey 까지 대표논문으로 셌다(남의 논문 5건이면 "
                              "리더연구자 자격이 충족됐다)")
                        fail = True; elig_fail = True
                    elif n < int(need_pubs):
                        print(f"FAIL: 대표논문 {n}편 < {key} 요건 {need_pubs}편")
                        fail = True; elig_fail = True
                    else:
                        print(f"  ✓ 대표논문 {n}편 (요건 {need_pubs})")
                if not elig_fail:
                    print(f"  ✓ 자격 — {key} · 박사 후 {yrs}년")

    # ② 평가지표 대응 선언
    decl = parse_criteria(outline_p)
    if decl is None:
        print(f"FAIL: {os.path.relpath(outline_p, root)} 에 ```criteria``` 블록이 없다 — "
              f"지표별 대응을 **선언**하지 않으면 남는 검사는 키워드 세기뿐이다")
        print("VERDICT: FAIL")
        return 1

    min_chars = int(policy.get("min_evidence_chars", 60))
    min_words = int(policy.get("min_section_words", 120))
    by_id = {d["id"]: d for d in decl}
    ids = [d["id"] for d in decl]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        print(f"FAIL: 평가지표 대응 선언이 중복됐다 {dup}")
        fail = True

    for c in criteria:
        d = by_id.get(c)
        if not d:
            print(f"FAIL: 평가지표 '{c}' 에 대한 대응 선언이 없다 — 공고의 지표는 "
                  f"전건 대응해야 한다")
            fail = True
            continue
        ev = str(d.get("evidence", "")).strip()
        sec = str(d.get("section", "")).strip()
        if len(ev) < min_chars:
            print(f"FAIL: '{c}' 의 evidence 가 {len(ev)}자 — 하한 {min_chars}자. "
                  f"'창의적이다' 같은 한 마디는 대응이 아니다")
            fail = True
        if not sec:
            print(f"FAIL: '{c}' 에 `section:` 선언이 없다 — 어느 절이 이 지표를 받는지 "
                  f"지정해야 심사자가 찾을 수 있다")
            fail = True
            continue
        if mode == "final":
            p = os.path.join(sec_dir, f"{sec}.md")
            if not os.path.isfile(p):
                print(f"FAIL: '{c}' 이 가리키는 절 '{sec}' 이 실재하지 않는다({sec}.md)")
                fail = True
            else:
                n = count_words(open(p, encoding="utf-8").read())
                if n < min_words:
                    print(f"FAIL: '{c}' 이 가리키는 절 '{sec}' 이 {n} 어절 — 하한 {min_words}. "
                          f"빈 절을 가리키는 대응 선언은 대응이 아니다")
                    fail = True

    # 선언했지만 공고에 없는 지표 — 오탈자·구식 지표를 잡는다
    extra = [d["id"] for d in decl if d["id"] not in criteria]
    if extra:
        print(f"FAIL: 공고 지표에 없는 대응 선언 {extra} — 지표명이 정확해야 한다"
              f"(공고 지표: {criteria})")
        fail = True

    if not fail:
        print(f"  ✓ 평가지표 {len(criteria)}종 전건 대응 선언 · "
              f"{'절 실재·분량 확인' if mode == 'final' else '선언 검사(설계 단계)'}")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
