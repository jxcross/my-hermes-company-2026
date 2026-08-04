#!/usr/bin/env python3
"""
객관 게이트: 청구항 정합성 (특허 명세서)
========================================
청구항에 등장하는 구성요소가 **명세서 본문에 실제로 설명돼 있는지**, 종속항이 **실재하는
청구항을 참조하는지** LLM 없이 검사한다. 출원 실무에서 이 둘은 기재불비(記載不備) 거절이유의
대표 사유이므로 하드 게이트다.
출처: other_projects/harness-templates/.../patentforge/scripts/claim_consistency.py
      (우리 gate_keeper CLI 규약으로 이식)

검사 항목
  1. 각 청구항의 구성요소(…모듈/부/장치/시스템/유닛 등)가 본문
     【과제의 해결 수단】+【발명을 실시하기 위한 구체적인 내용】에 등장하는가
  2. 종속항의 `제N항` 참조가 실재 청구항 번호인가 (자기 참조·순환·미존재 차단)
  3. 청구항이 1개 이상 있고 독립항이 존재하는가

명세서(spec.md)가 따라야 할 구조
    ## 【청구범위】
    ### 청구항 1
    … 제1 모듈과 제2 부를 포함하는 …
    ### 청구항 2
    제1항에 있어서, …
    ## 【과제의 해결 수단】
    ## 【발명을 실시하기 위한 구체적인 내용】

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.patent_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : spec.md (한국어 canonical 명세서)

정책 필드(patent_policy)
  min_element_coverage (기본 1.0) : 본문에 설명돼야 하는 구성요소 비율 하한

exit: 0 PASS · 1 FAIL · 2 usage/입력없음(fail-closed)
"""
from __future__ import annotations
import argparse
import json
import re
import sys

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML 필요", file=sys.stderr); sys.exit(2)

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
# ⚠️ 절 종료 조건은 `^##[^#]` 이어야 한다 — 원본의 `(?=^##|\Z)` 는 하위 제목인
#    `### 청구항 1` 에도 걸려 【청구범위】 절이 **즉시 잘렸다**(청구항을 하나도 못 읽는다).
#    이식 중 픽스처로 발견. docs/13 §5.
_END = r"(?=^##[^#]|\Z)"
CLAIMS_SECTION_RE = re.compile(r"##\s*【청구범위】(.*?)" + _END, re.DOTALL | re.M)
SOLUTION_RE = re.compile(r"##\s*【과제의 해결 수단】(.*?)" + _END, re.DOTALL | re.M)
EMBODIMENT_RE = re.compile(r"##\s*【발명을 실시하기 위한 구체적인 내용】(.*?)" + _END, re.DOTALL | re.M)
CLAIM_HEADER_RE = re.compile(r"###\s*청구항\s*(\d+)", re.M)
DEPENDENT_REF_RE = re.compile(r"제\s*(\d+)\s*항")
# 한국 특허 청구항의 구성요소는 "수식어 + 핵심명사"(예: 프로파일링 모듈, 캐시 부) 꼴이다.
#
# ⚠️ 원본의 `\S+\s*(?:모듈|…)\b` 패턴은 한국어에서 사실상 작동하지 않았다:
#    ① 조사가 붙은 `모듈과`·`부를` 은 `\b` 가 성립하지 않아 **놓치고**
#    ② 대신 동사구 `포함하는 시스템` 을 요소로 잡아 **엉뚱한 것을 검사**했다.
#    결과적으로 게이트가 커버리지 2/2 PASS 를 내면서 실제로는 아무것도 측정하지 못했다
#    (이식 중 픽스처로 발견 — 본문에서 '캐시 부'를 지웠는데 통과했다). docs/13 §5.
#
# 그래서 (수식어, 핵심명사)를 분리해 잡고, 뒤따르는 조사를 lookahead 로 허용한다.
# `기`는 제외했다 — 기록·기술 등 흔한 어휘에 걸려 오탐이 너무 많다.
HEAD_NOUNS = "모듈|시스템|장치|회로|유닛|블록|소자|엔진|컴포넌트|부"
JOSA = r"[을를과와은는이가에의로써서및,\.\)\]]|$|\s"
ELEMENT_RE = re.compile(
    rf"(?P<mod>[가-힣A-Za-z0-9]+)\s*(?P<head>{HEAD_NOUNS})(?={JOSA})")
ELEMENT_RE_EN = re.compile(
    r"(?P<mod>[A-Za-z0-9]+)\s+(?P<head>profiler|module|unit|component|system|circuit|engine)\b",
    re.IGNORECASE)
# 수식어 자리에 온 동사·연결어미는 구성요소가 아니다(포함하는 시스템 ≠ 구성요소).
VERBAL_TAIL_RE = re.compile(r"(?:하는|되는|있는|없는|지는|시키는|받는|주는|이는|같은|위한)$")


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("patent_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("patent_policy", {}) or {}


def claims_section(text: str) -> str:
    m = CLAIMS_SECTION_RE.search(text)
    return m.group(1) if m else ""


def spec_body(text: str) -> str:
    out = ""
    for rx in (SOLUTION_RE, EMBODIMENT_RE):
        m = rx.search(text)
        if m:
            out += m.group(1) + "\n"
    return out


def claim_blocks(claims_text: str) -> list[tuple[int, str]]:
    marks = list(CLAIM_HEADER_RE.finditer(claims_text))
    out = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(claims_text)
        out.append((int(m.group(1)), claims_text[m.end():end]))
    return out


def elements_of(body: str) -> list[tuple[str, str]]:
    """(수식어, 핵심명사) 목록. 수식어가 구성요소를 식별하는 부분이다."""
    seen, out = set(), []
    for rx in (ELEMENT_RE, ELEMENT_RE_EN):
        for m in rx.finditer(body):
            mod, head = m.group("mod").strip(), m.group("head").strip()
            if VERBAL_TAIL_RE.search(mod):     # '포함하는 시스템' 같은 동사구 제외
                continue
            if len(mod) < 2:                   # '제1 부' 처럼 식별력 없는 수식어 제외
                continue
            key = (mod.lower(), head.lower())
            if key not in seen:
                seen.add(key)
                out.append((mod, head))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", default=None, help="미사용(gate_keeper 규약상 전달됨)")
    ap.add_argument("--draft", default=None, help="spec.md")
    args = ap.parse_args()

    if not args.draft:
        print("FAIL(usage): --draft(spec.md) 필수 — fail-closed", file=sys.stderr); return 2
    try:
        policy = load_policy(args.policy)
        text = open(args.draft, encoding="utf-8").read()
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e} — fail-closed", file=sys.stderr); return 2

    claims_text = claims_section(text)
    if not claims_text.strip():
        print("FAIL: 【청구범위】 절을 찾지 못했다 — 명세서 구조를 지켜라(fail-closed).",
              file=sys.stderr)
        return 1
    body = spec_body(text)
    if not body.strip():
        print("FAIL: 【과제의 해결 수단】·【발명을 실시하기 위한 구체적인 내용】이 없다 — "
              "청구항을 뒷받침할 본문이 없다.", file=sys.stderr)
        return 1

    blocks = claim_blocks(claims_text)
    if not blocks:
        print("FAIL: 청구항(### 청구항 N)이 하나도 없다.", file=sys.stderr); return 1
    nums = [n for n, _ in blocks]

    min_cov = float(policy.get("min_element_coverage", 1.0) or 1.0)
    body_norm = re.sub(r"\s+", " ", body)

    print(f"청구항 {len(blocks)}개(번호 {nums}) · 본문 {len(body_norm)}자 · "
          f"요소 커버리지 하한 {min_cov}")

    fail = False

    # ① 종속항 참조 실재성
    independent = []
    for n, b in blocks:
        refs = {int(r) for r in DEPENDENT_REF_RE.findall(b)}
        if not refs:
            independent.append(n)
            continue
        bad = sorted(r for r in refs if r not in nums)
        self_ref = n in refs
        later = sorted(r for r in refs if r >= n)
        if bad:
            print(f"FAIL: 청구항 {n} 이 존재하지 않는 제{bad}항을 참조한다")
            fail = True
        if self_ref:
            print(f"FAIL: 청구항 {n} 이 자기 자신을 참조한다")
            fail = True
        elif later and not bad:
            print(f"FAIL: 청구항 {n} 이 뒤 번호 제{later}항을 참조한다(종속 방향 위반)")
            fail = True
    if not independent:
        print("FAIL: 독립항이 없다 — 모든 청구항이 다른 항을 참조한다")
        fail = True
    else:
        print(f"독립항: {independent}")

    # ② 구성요소가 본문에 설명되는가
    total = missing = 0
    body_lower = body_norm.lower()
    for n, b in blocks:
        for mod, head in elements_of(b):
            total += 1
            # 조사·어순이 달라도 되도록 **수식어**(식별 부분)가 본문에 있는지로 본다.
            if mod.lower() not in body_lower:
                missing += 1
                print(f"  - 청구항 {n} 요소 '{mod} {head}' 가 본문에 설명되지 않았다")
    if total:
        cov = round((total - missing) / total, 3)
        print(f"요소 커버리지: {total - missing}/{total} = {cov}")
        if cov < min_cov:
            print(f"FAIL: 커버리지 {cov} < 하한 {min_cov} — 기재불비 위험")
            fail = True
    else:
        print("WARNING: 청구항에서 구성요소를 추출하지 못했다(표현이 특이하거나 청구항이 짧다) "
              "— LLM 검증자가 판단하라")

    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
