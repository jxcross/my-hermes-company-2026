#!/usr/bin/env python3
"""
객관 게이트: 채널 규격 (X 스레드 · 블로그 · README)
=====================================================
발신 채널마다 플랫폼의 하드 제약(글자 수·개수·구조)을 지켰는지 LLM 없이 검사한다.
출처: outreachforge 의 `channel_format_check.py` — 이식하며 결함 2건을 고쳤다.
**둘 다 정상 산출물을 반려하는 쪽**이다(legalforge 계열).

⚠️ **채널 목록이 하드코딩돼 있었다**(실측):

       for stem, checker in (("twitter", ...), ("medium", ...), ("readme", ...)):
           if not path.is_file(): n_violations += 1

   스킬의 stage 1 은 `channels` 를 **미션마다 선언**하게 해 놓고(기본값이 '모두'일 뿐),
   게이트는 셋을 무조건 요구한다. X 스레드만 만들기로 한 미션이 medium·readme 부재로
   **반려된다**(실측 `exit=1`). → 선언 목록(SCOPE.md `channels:`)을 읽고 **선언한 것만**
   검사하되, **선언한 것의 부재는 FAIL**(병렬 산출물 부재 — docs/13 §5).

⚠️ **분량 규격이 영문 word 기준인데 본문은 국문이다**(실측):
   원본은 Medium 을 "한국어 blog, 1500~3000 words" 라 규정하고 공백 토큰(= 국문 어절)을
   센다. 영문 1,700 단어에 해당하는 **정상 국문 글(1,164 어절)이 '미달'로 반려**된다.
   policy-brief(어절)·research-proposal(글자)에 이은 **세 번째 한국어 재보정**이다.
   → 국문 어절 기준으로 다시 잡고 정책으로 뺐다(영문 ÷ 1.45).

이식하며 유지한 것: URL 을 23자로 세는 X 규칙 · `1/N` 번호 연속성 · 마지막 트윗 CTA.
원본이 이미 정확히 하고 있었다.

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.channel_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : 미션 디렉터리(reports/<MID>)

정책 필드(channel_policy)
  channels_dir (기본 _private/channels) · channels — SCOPE.md frontmatter 의 `channels:` 우선
  specs: {twitter: {...}, medium: {...}, readme: {...}}

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
URL_RE = re.compile(r"https?://\S+")
POST_NO_RE = re.compile(r"^#{1,3}\s*(\d+)\s*/\s*(\d+)\s*$", re.MULTILINE)
HEADING_RE = re.compile(r"^##\s+\S", re.MULTILINE)
HERO_RE = re.compile(r"^>\s*(?:Hero image hint|대표 이미지)\s*:", re.MULTILINE | re.IGNORECASE)
DIFF_RE = re.compile(r"^\+", re.MULTILINE)
KOREAN_RE = re.compile(r"[가-힣]")
BIBTEX_RE = re.compile(r"@\w+\s*\{[^}]+,", re.DOTALL)

DEFAULT_SPECS = {
    "twitter": {"min_posts": 5, "max_posts": 8, "max_chars": 280,
                "require_numbering": True, "require_cta": True},
    # ⚠️ 국문 어절 기준(영문 1500~3000 words ÷ 1.45). 원본 수치를 그대로 쓰면 정상 글이 반려된다
    "medium": {"word_range": [900, 2100], "min_headings": 3, "max_headings": 6,
               "require_hero": True},
    "readme": {"min_diff_lines": 5, "require_bilingual": True, "require_bibtex": True},
}


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("channel_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("channel_policy", {}) or {}


def mission_root(draft: str) -> str:
    p = os.path.abspath(draft)
    return p if os.path.isdir(p) else os.path.dirname(p)


def scope_value(root: str, key: str):
    try:
        m = FRONTMATTER_RE.match(open(os.path.join(root, "SCOPE.md"), encoding="utf-8").read())
    except OSError:
        return None
    return (yaml.safe_load(m.group(1)) or {}).get(key) if m else None


def chars_with_url_rule(text: str) -> int:
    """X 는 URL 을 길이와 무관하게 23자로 센다."""
    n_url = len(URL_RE.findall(text))
    return len(URL_RE.sub("", text)) + n_url * 23


def count_words(text: str) -> int:
    body = FRONTMATTER_RE.sub("", text, count=1)
    body = re.sub(r"```.*?```", " ", body, flags=re.DOTALL)
    body = re.sub(r"[#*_>`\[\]()|-]", " ", body)
    return len([w for w in body.split() if w.strip()])


def check_twitter(text: str, spec: dict) -> list[str]:
    errs = []
    marks = list(POST_NO_RE.finditer(text))
    n = len(marks)
    lo, hi = int(spec.get("min_posts", 5)), int(spec.get("max_posts", 8))
    if not (lo <= n <= hi):
        errs.append(f"트윗 {n}개가 규격 {lo}~{hi} 밖이다"
                    + (" (`## 1/N` 형식의 번호 제목이 있어야 트윗으로 센다)" if n == 0 else ""))
    bodies = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        bodies.append(text[m.end():end].strip())
    limit = int(spec.get("max_chars", 280))
    for i, b in enumerate(bodies, start=1):
        c = chars_with_url_rule(b)
        if c > limit:
            errs.append(f"{i}번 트윗이 {c}자 — 상한 {limit}(URL 은 23자로 계산)")
    if spec.get("require_numbering", True) and marks:
        total = marks[0].group(2)
        for i, m in enumerate(marks, start=1):
            if int(m.group(1)) != i or m.group(2) != total:
                errs.append(f"번호가 어긋난다 — {i}번째가 `{m.group(1)}/{m.group(2)}`")
                break
    if spec.get("require_cta", True):
        if not bodies:
            errs.append("CTA 를 확인할 트윗이 없다")
        elif not (URL_RE.search(bodies[-1]) or "#" in bodies[-1]):
            errs.append("마지막 트윗에 CTA(링크 또는 해시태그)가 없다")
    return errs


def check_medium(text: str, spec: dict) -> list[str]:
    errs = []
    rng = spec.get("word_range") or [900, 2100]
    n = count_words(text)
    if not (int(rng[0]) <= n <= int(rng[1])):
        errs.append(f"분량 {n} 어절이 규격 {rng[0]}~{rng[1]} 밖이다"
                    f"(**국문 어절 기준** — 원본의 영문 word 수치를 그대로 쓰면 정상 글이 반려된다)")
    h = len(HEADING_RE.findall(FRONTMATTER_RE.sub("", text, count=1)))
    lo, hi = int(spec.get("min_headings", 3)), int(spec.get("max_headings", 6))
    if not (lo <= h <= hi):
        errs.append(f"소제목 {h}개가 규격 {lo}~{hi} 밖이다")
    if spec.get("require_hero", True) and not HERO_RE.search(text):
        errs.append("대표 이미지 힌트(`> Hero image hint:`)가 없다")
    return errs


def check_readme(text: str, spec: dict) -> list[str]:
    errs = []
    n = len(DIFF_RE.findall(text))
    if n < int(spec.get("min_diff_lines", 5)):
        errs.append(f"추가 줄(`+`)이 {n}개 — 하한 {spec.get('min_diff_lines', 5)}"
                    f"(README 갱신은 PR diff 형식으로 낸다)")
    if spec.get("require_bilingual", True):
        if not KOREAN_RE.search(text) or not re.search(r"\b[A-Za-z]{4,}\b", text):
            errs.append("국·영문 병기가 아니다")
    if spec.get("require_bibtex", True) and not BIBTEX_RE.search(text):
        errs.append("BibTeX 인용 블록이 없다")
    return errs


CHECKERS = {"twitter": check_twitter, "medium": check_medium, "readme": check_readme}


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
    ch_dir = os.path.join(root, policy.get("channels_dir") or "_private/channels")
    declared = scope_value(root, "channels") or policy.get("channels")
    if not declared:
        print("FAIL(usage): 발신 채널 선언이 없다 — SCOPE.md frontmatter 의 `channels:` "
              "또는 정책에 선언하라. **원본은 셋을 하드코딩해 X 스레드만 만드는 미션도 "
              "반려했다.** fail-closed", file=sys.stderr)
        return 2
    if not os.path.isdir(ch_dir):
        print(f"FAIL(usage): 채널 디렉터리가 없다({ch_dir}) — fail-closed", file=sys.stderr)
        return 2

    specs = {**DEFAULT_SPECS, **(policy.get("specs") or {})}
    print(f"선언 채널 {list(declared)} · 규격 {sorted(specs)}")
    fail = False

    for ch in declared:
        p = os.path.join(ch_dir, f"{ch}.md")
        if not os.path.isfile(p):
            print(f"FAIL: 선언한 채널 '{ch}' 의 산출물이 없다 — 병렬 워커가 죽으면 파일이 "
                  f"통째로 빠지므로 **선언 목록 대비 존재**를 본다")
            fail = True
            continue
        checker = CHECKERS.get(ch)
        if not checker:
            print(f"FAIL: 채널 '{ch}' 의 규격 검사기가 없다 — 검사할 수 없는 채널을 "
                  f"선언했다(정책 specs 에 추가하거나 선언에서 빼라)")
            fail = True
            continue
        errs = checker(open(p, encoding="utf-8").read(), specs.get(ch) or {})
        for e in errs:
            print(f"FAIL: [{ch}] {e}")
        if errs:
            fail = True
        else:
            print(f"  ✓ [{ch}] 규격 충족")

    # 선언하지 않은 채널이 산출됐는가 — 발신 범위를 파이프라인이 늘리면 안 된다
    extra = [n[:-3] for n in sorted(os.listdir(ch_dir))
             if n.endswith(".md") and n[:-3] not in declared]
    if extra:
        print(f"FAIL: 선언하지 않은 채널 산출물 {extra} — 어디에 발신할지는 Scoping 에서 "
              f"정한다(승인 범위 밖의 공개다)")
        fail = True

    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
