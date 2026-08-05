#!/usr/bin/env python3
"""
객관 게이트: 제안서 제출 규격
==============================
연구제안서 번들이 **제출 규격**(필수 절 · 분량 · 필수 산출물 · 일정표 · 영문 초록)을
만족하는지 LLM 없이 검사한다.
출처: proposalforge 의 Gate 1(`format_check.py`) — 이식하며 결함 5건을 고쳤다.

⚠️ **원본은 빈 제안서를 통과시켰다**(실측 · docs/13 §5):
   섹션 파일 5개를 **전부 빈 파일**로 두고 gantt 블록을 ````mermaid\\ngantt\\n````
   한 줄로 두면

       page_count           PASS — 0.0 / 30 pages (0 words)
       section_completeness PASS — all present
       timeline_format      PASS — mermaid gantt block present
       overall              PASS   exit=0

   존재만 확인하고 **하한이 없다**. 페이지 한도는 상한만 재므로 아무것도 쓰지 않은 제안서가
   가장 안전하게 통과한다. 공집합이 통과하는 자리의 일곱 번째다(§5).
   → ① 절마다 실질 분량 하한 ② 총 분량 **하한과 상한** ③ gantt **task 개수**를 강제한다.

⚠️ **원본에 없는 검사 하나**: CLAUDE.md 는 "본문 언어는 한국어, abstract 는 **영문**"을
   규약으로 선언하지만 코드에 그 대조가 없다. 국문 초록을 `abstract-en.md` 로 내도 아무도
   모른다 → ASCII 비율로 실제 영문인지 본다(§5 '선언만 하고 코드에 없는 검사' 계열).

⚠️ **조립 누락**: `proposal.md` 는 섹션을 합친 것이다. 목차만 있고 본문이 비어도 파일은
   존재한다 → 섹션 어절 합 대비 비율(`min_assembly_ratio`)로 조립 여부를 본다.

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.format_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : 미션 디렉터리(reports/<MID>)

정책 필드(format_policy)
  bundle_dir (기본 _private/bundle) · sections_subdir (기본 sections)
  sections            : 필수 절 목록. 부재는 FAIL(선언 목록 대비 존재)
  section_aliases     : {aims: [연구목표], ...} — 파일명 별칭
  required_artifacts  : 번들에 있어야 할 산출물 목록
  page_limit / words_per_page (기본 600 · 국문 어절) — SCOPE.md frontmatter 우선
  min_page_ratio (기본 0.5) · min_section_words (기본 120)
  gantt_min_tasks (기본 3) · timeline_file (기본 timeline.md)
  abstract_file (기본 abstract-en.md) · abstract_words [150, 400] · abstract_min_ascii (기본 0.7)
  proposal_file (기본 proposal.md) · min_assembly_ratio (기본 0.8)

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
# gantt task 줄: `설계 :a1, 2026-03-01, 90d` 형태. section/title/dateFormat 등 지시어는 제외.
GANTT_DIRECTIVE = ("gantt", "title", "dateformat", "axisformat", "section",
                   "excludes", "todaymarker", "tickinterval", "weekday")


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("format_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("format_policy", {}) or {}


def mission_root(draft: str) -> str:
    p = os.path.abspath(draft)
    return p if os.path.isdir(p) else os.path.dirname(p)


def scope_value(root: str, key: str):
    """SCOPE.md frontmatter 값(정책 기본값보다 우선). 미션마다 한도가 다르다."""
    try:
        m = FRONTMATTER_RE.match(open(os.path.join(root, "SCOPE.md"), encoding="utf-8").read())
    except OSError:
        return None
    if not m:
        return None
    return (yaml.safe_load(m.group(1)) or {}).get(key)


def count_words(text: str) -> int:
    """국문 어절 수. frontmatter·코드블록·표 구분선·마크다운 기호를 걷어낸 뒤 공백 분할.
    (format_consistency 와 같은 셈법 — 아키타입이 달라도 분량의 단위는 같아야 한다.)"""
    body = FRONTMATTER_RE.sub("", text, count=1)
    body = re.sub(r"```.*?```", " ", body, flags=re.DOTALL)
    body = re.sub(r"^\s*\|[\s\-:|]+\|\s*$", " ", body, flags=re.MULTILINE)
    body = re.sub(r"[#*_>`\[\]()|-]", " ", body)
    return len([w for w in body.split() if w.strip()])


def read(path: str) -> str | None:
    try:
        return open(path, encoding="utf-8").read()
    except OSError:
        return None


def section_path(sec_dir: str, name: str, aliases: dict) -> str | None:
    """`aims.md` 또는 별칭(`연구목표.md`). 선언한 이름이 없으면 None."""
    for cand in [name] + list(aliases.get(name) or []):
        p = os.path.join(sec_dir, f"{cand}.md")
        if os.path.isfile(p):
            return p
    return None


def gantt_tasks(text: str) -> list[str] | None:
    """mermaid gantt 블록의 **실제 task 줄**. 블록이 없으면 None, 있고 비면 []."""
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
        if ":" in s:                      # `할일 :id, 시작, 기간`
            tasks.append(s)
    return tasks


def ascii_ratio(text: str) -> float:
    body = FRONTMATTER_RE.sub("", text, count=1)
    letters = [c for c in body if not c.isspace() and (c.isalnum() or ord(c) > 127)]
    if not letters:
        return 0.0
    return sum(1 for c in letters if ord(c) < 128) / len(letters)


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
    bundle = os.path.join(root, policy.get("bundle_dir") or "_private/bundle")
    sec_dir = os.path.join(bundle, policy.get("sections_subdir") or "sections")

    declared = list(policy.get("sections") or [])
    if not declared:
        print("FAIL(usage): format_policy.sections 선언이 없다 — 무엇이 있어야 하는지 모르면 "
              "부재를 검출할 수 없다. fail-closed", file=sys.stderr)
        return 2
    if not os.path.isdir(bundle):
        print(f"FAIL(usage): 번들 디렉터리가 없다({bundle}) — fail-closed", file=sys.stderr)
        return 2

    aliases = policy.get("section_aliases") or {}
    page_limit = scope_value(root, "page_limit") or policy.get("page_limit")
    wpp = int(policy.get("words_per_page", 600))
    min_ratio = float(policy.get("min_page_ratio", 0.5))
    min_sec_words = int(policy.get("min_section_words", 120))
    gantt_min = int(policy.get("gantt_min_tasks", 3))

    if not page_limit:
        print("FAIL(usage): page_limit 이 SCOPE.md 에도 정책에도 없다 — 상한을 모르면 "
              "규격 검사가 성립하지 않는다. fail-closed", file=sys.stderr)
        return 2
    page_limit = int(page_limit)

    print(f"번들 {os.path.relpath(bundle, root)} · 필수 절 {len(declared)}종 · "
          f"페이지 한도 {page_limit}쪽(1쪽={wpp} 어절 · 하한 {min_ratio:.0%})")

    fail = False

    # ① 필수 절 존재 + 실질 분량 — 원본은 `is_file()` 만 봤다(빈 파일도 '완비')
    total_words = 0
    per_sec: dict[str, int] = {}
    for name in declared:
        p = section_path(sec_dir, name, aliases)
        if not p:
            print(f"FAIL: 필수 절 '{name}' 이 없다({os.path.relpath(sec_dir, root)}/{name}.md) "
                  f"— 병렬 워커가 죽으면 파일이 통째로 비므로 **선언 목록 대비 존재**를 본다")
            fail = True
            continue
        n = count_words(read(p) or "")
        per_sec[name] = n
        total_words += n
        if n < min_sec_words:
            print(f"FAIL: 절 '{name}' 이 {n} 어절 — 하한 {min_sec_words}. **파일이 있는 것과 "
                  f"쓰인 것은 다르다**(원본은 빈 파일 5개에 '모두 존재 PASS' 를 줬다)")
            fail = True

    # ② 총 분량: 상한 + **하한**
    pages = round(total_words / wpp, 1)
    lo = round(page_limit * min_ratio, 1)
    print(f"  분량 {total_words} 어절 = {pages}쪽 (허용 {lo}~{page_limit}쪽) · "
          f"절별 {per_sec}")
    if pages > page_limit:
        print(f"FAIL: {pages}쪽 > 한도 {page_limit}쪽 — 초과분은 심사에서 잘린다")
        fail = True
    if pages < lo:
        print(f"FAIL: {pages}쪽 < 하한 {lo}쪽 — 한도의 {min_ratio:.0%} 도 채우지 못한 "
              f"제안서다(원본에는 하한이 없어 **빈 제안서가 가장 안전하게 통과**했다)")
        fail = True

    # ③ 필수 산출물 — 선언 목록 대비 존재
    for rel in list(policy.get("required_artifacts") or []):
        p = os.path.join(bundle, rel)
        if not os.path.exists(p):
            print(f"FAIL: 필수 산출물 '{rel}' 이 번들에 없다")
            fail = True

    # ④ 일정표: gantt 블록 존재 + **task 실체**
    tl_name = policy.get("timeline_file") or "timeline.md"
    tl = read(os.path.join(bundle, tl_name))
    if tl is None:
        print(f"FAIL: 일정표 {tl_name} 이 없다")
        fail = True
    else:
        tasks = gantt_tasks(tl)
        if tasks is None:
            print(f"FAIL: {tl_name} 에 mermaid gantt 블록이 없다")
            fail = True
        elif len(tasks) < gantt_min:
            print(f"FAIL: gantt task {len(tasks)}건 < 하한 {gantt_min} — 원본은 **블록의 존재만** "
                  f"봐서 `gantt` 한 줄짜리 빈 도표가 통과했다")
            fail = True
        else:
            print(f"  ✓ gantt task {len(tasks)}건")

    # ⑤ 영문 초록 — 원본에 없다(CLAUDE.md 의 "abstract 는 영문"은 선언뿐이었다)
    ab_name = policy.get("abstract_file") or "abstract-en.md"
    ab_rng = policy.get("abstract_words") or [150, 400]
    min_ascii = float(policy.get("abstract_min_ascii", 0.7))
    ab = read(os.path.join(bundle, ab_name))
    if ab is None:
        print(f"FAIL: 영문 초록 {ab_name} 이 없다")
        fail = True
    else:
        n = count_words(ab)
        ratio = ascii_ratio(ab)
        if not (int(ab_rng[0]) <= n <= int(ab_rng[1])):
            print(f"FAIL: {ab_name} 분량 {n} 단어가 규격 {ab_rng[0]}~{ab_rng[1]} 밖이다")
            fail = True
        if ratio < min_ascii:
            print(f"FAIL: {ab_name} 의 ASCII 비율 {ratio:.0%} < {min_ascii:.0%} — "
                  f"**영문 초록이 아니다**. NRF 는 본문 국문·초록 영문을 요구한다")
            fail = True
        if int(ab_rng[0]) <= n <= int(ab_rng[1]) and ratio >= min_ascii:
            print(f"  ✓ {ab_name} {n} 단어 · ASCII {ratio:.0%}")

    # ⑥ 조립 — proposal.md 가 섹션을 실제로 담고 있는가
    pr_name = policy.get("proposal_file") or "proposal.md"
    pr = read(os.path.join(bundle, pr_name))
    if pr is None:
        print(f"FAIL: 본문 {pr_name} 이 없다")
        fail = True
    elif total_words:
        need = total_words * float(policy.get("min_assembly_ratio", 0.8))
        got = count_words(pr)
        if got < need:
            print(f"FAIL: {pr_name} 이 {got} 어절인데 절 합계는 {total_words} 어절 "
                  f"— 조립이 누락됐다(목차만 있는 본문). 하한 {need:.0f}")
            fail = True
        else:
            print(f"  ✓ {pr_name} 조립 {got} 어절 (절 합계 {total_words})")

    if not fail:
        print(f"  ✓ 필수 절 {len(declared)}종 · {pages}쪽 · 필수 산출물 전건 존재")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
