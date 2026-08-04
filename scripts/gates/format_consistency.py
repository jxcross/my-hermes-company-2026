#!/usr/bin/env python3
"""
객관 게이트: 포맷 간 정합성 + 분량
====================================
같은 정책안을 4개 포맷(브리프·보고서·메모·인포그래픽)으로 **병렬 집필**하면, 워커마다
다른 옵션을 권고하거나 분량 규격을 벗어나는 사고가 조용히 일어난다. 이것을 LLM 없이 잡는다.
출처: other_projects/harness-templates/.../policyforge/scripts/format_consistency_check.py

⚠️ 이식하며 고친 것 (docs/13 §5):
  1. **분량 기준이 영어 계산이었다** — 원본은 `brief: 1200~2400 words = 2~4쪽`인데, 이는
     영문 기준이다. 국문 A4 1쪽은 대략 **500~700 어절**(≈1,600자)이라 같은 2~4쪽 문서가
     700~2,800 어절로 나온다. 원본 하한(1200)을 그대로 쓰면 규격에 맞는 국문 브리프가
     **분량 미달로 반려**된다. → 기준을 정책(template)으로 옮기고 국문으로 재보정.
  2. **옵션 토큰이 한국어에서 안 잡혔다** — `\\bO\\d+\\b` 는 `O2를`·`O3안` 에서 무너진다
     (숫자↔한글 사이에 \\b 가 없다). → lookaround 로 교체.
  3. **선언된 포맷의 부재를 못 잡았다** — glob 으로 있는 파일만 검사하므로 워커가
     통째로 실패해 memo.md 가 없으면 **검사할 것이 없어 통과**했다. → SCOPE.md 의
     `formats:` 선언(없으면 정책값)과 대조해 부재를 FAIL 로.

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.format_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : formats/ 디렉터리

권고 옵션은 미션 루트의 `options.md` 에서 읽는다 — frontmatter 또는 본문의
`recommended_option: O2` 줄.

정책 필드(format_policy)
  options_file (기본 options.md) · formats (기본 [brief, report, memo, infographic])
  word_ranges: {brief: [700, 2800], ...}   # 국문 어절 기준. 0 은 하한 없음
  require_recommended_in_all (기본 true)

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
RECOMMENDED_RE = re.compile(r"^\s*recommended_option:\s*(\S+)", re.MULTILINE)
# ⚠️ \b 금지 — `O2를`·`O3안` 처럼 한글이 붙으면 경계가 성립하지 않는다.
OPTION_RE_TMPL = r"(?<![0-9A-Za-z]){}(?![0-9A-Za-z])"

# 국문 어절 기준(A4 1쪽 ≈ 500~700 어절). 원본의 영문 word 기준을 재보정한 것.
DEFAULT_FORMATS = ["brief", "report", "memo", "infographic"]
DEFAULT_WORD_RANGES = {
    "brief": [700, 2800],        # 2~4쪽
    "report": [5000, 21000],     # 15~30쪽
    "memo": [350, 900],          # 1쪽
    "infographic": [0, 1200],    # 시각 서사 — 상한만
}


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("format_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("format_policy", {}) or {}


def scope_formats(root: str) -> list[str]:
    """SCOPE.md frontmatter 의 `formats:` — 선언이 정책 기본값보다 우선한다."""
    try:
        m = FRONTMATTER_RE.match(open(os.path.join(root, "SCOPE.md"), encoding="utf-8").read())
    except OSError:
        return []
    if not m:
        return []
    d = yaml.safe_load(m.group(1)) or {}
    v = d.get("formats")
    if isinstance(v, str):
        v = [x.strip() for x in v.split(",")]
    return [str(x).strip().lower() for x in (v or [])]


def count_words(text: str) -> int:
    """국문 어절 수. frontmatter·코드블록·표 구분선·마크다운 기호를 걷어낸 뒤 공백 분할."""
    body = FRONTMATTER_RE.sub("", text, count=1)
    body = re.sub(r"```.*?```", " ", body, flags=re.DOTALL)
    body = re.sub(r"^\s*\|[\s\-:|]+\|\s*$", " ", body, flags=re.MULTILINE)  # 표 구분선
    body = re.sub(r"[#*_>`\[\]()|-]", " ", body)
    return len([w for w in body.split() if w.strip()])


def recommended_option(options_path: str) -> str | None:
    try:
        text = open(options_path, encoding="utf-8").read()
    except OSError:
        return None
    m = RECOMMENDED_RE.search(text)
    return m.group(1).strip().strip('"\',') if m else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", default=None, help="미사용(gate_keeper 규약상 전달됨)")
    ap.add_argument("--draft", default=None, help="formats/ 디렉터리")
    args = ap.parse_args()

    if not args.draft:
        print("FAIL(usage): --draft(formats/) 필수 — fail-closed", file=sys.stderr); return 2
    try:
        policy = load_policy(args.policy)
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e} — fail-closed", file=sys.stderr); return 2
    if not os.path.isdir(args.draft):
        print(f"FAIL(usage): formats 디렉터리가 아니다({args.draft}) — fail-closed", file=sys.stderr)
        return 2

    root = os.path.dirname(os.path.abspath(args.draft))
    options_path = os.path.join(root, policy.get("options_file") or "options.md")
    recommended = recommended_option(options_path)
    if not recommended:
        print(f"FAIL(usage): 권고 옵션을 읽지 못했다({options_path}) — "
              f"`recommended_option: O2` 줄이 필요하다. fail-closed", file=sys.stderr)
        return 2

    expected = scope_formats(root) or [str(f).lower() for f in (policy.get("formats") or DEFAULT_FORMATS)]
    ranges = {k.lower(): v for k, v in (policy.get("word_ranges") or DEFAULT_WORD_RANGES).items()}
    require_all = bool(policy.get("require_recommended_in_all", True))
    opt_re = re.compile(OPTION_RE_TMPL.format(re.escape(recommended)))

    present = {os.path.basename(f).rsplit(".md", 1)[0].lower(): os.path.join(args.draft, f)
               for f in sorted(os.listdir(args.draft)) if f.endswith(".md")}

    print(f"권고 옵션 {recommended} · 선언 포맷 {expected} · 존재 {sorted(present)}")

    fail = False
    absent = [f for f in expected if f not in present]
    if absent:
        print(f"FAIL: 선언된 포맷 문서가 없다: {absent} — 병렬 집필 워커가 실패했을 수 있다")
        fail = True

    for stem in sorted(present):
        try:
            text = open(present[stem], encoding="utf-8").read()
        except OSError as e:
            print(f"FAIL: {stem} 읽기 실패 ({e})"); fail = True; continue
        words = count_words(text)
        rng = ranges.get(stem)
        marks = []
        if rng:
            lo, hi = int(rng[0]), int(rng[1])
            if not (lo <= words <= hi):
                print(f"FAIL: {stem} 분량 {words} 어절이 규격 {lo}~{hi} 밖이다(국문 어절 기준)")
                fail = True
            else:
                marks.append(f"분량 {words}({lo}~{hi}) ✓")
        else:
            marks.append(f"분량 {words}(규격 미선언)")
        if require_all and not opt_re.search(text):
            print(f"FAIL: {stem} 에 권고 옵션 {recommended} 이(가) 없다 — 포맷 간 권고가 "
                  f"엇갈리면 정책 자료로서 신뢰를 잃는다")
            fail = True
        else:
            marks.append(f"권고 {recommended} ✓")
        if marks:
            print(f"  {stem:12s} " + " · ".join(marks))

    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
