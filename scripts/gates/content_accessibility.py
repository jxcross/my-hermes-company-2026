#!/usr/bin/env python3
"""
객관 게이트: 강의 콘텐츠 접근성
=================================
이미지에 대체 텍스트가 있는지, 문장이 지나치게 길지 않은지 LLM 없이 검사한다.
출처: other_projects/harness-templates/.../lectureforge/scripts/accessibility_check.py (GATE 3)

이식하며 고친 것 (docs/13 §5)
  · **불릿을 한 문장으로 뭉쳤다** — 원본은 `[.!?]\\s+|\\n\\n` 로만 문장을 나눈다. 슬라이드는
    대부분 불릿이고 마침표가 없어 **불릿 블록 전체가 문장 1개**로 잡혔다. 문장당 어절이
    부풀어 슬라이드가 부당하게 위반으로 몰린다. → **불릿·표 줄은 각각 하나의 단위**로 센다.
  · **임계가 영어 word 기준이었다** — 국문 어절은 영어 word 보다 문장당 개수가 적다.
    임계를 정책으로 옮기고 국문 기준으로 재보정했다(policy-brief 의 분량 재보정과 같은 계열).
  · **가독성 위반이 곧 하드 FAIL 이었다** — 문장 길이는 **거친 대리지표**다. 기본은 WARNING
    으로 두고, 정책 `readability_is_fail` 로 올릴 수 있게 했다. 대체 텍스트 부재만 기본 FAIL.

⚠️ 정직하게 적어 둔다: 문장당 어절 수는 가독성의 **약한 대리지표**다. 이 게이트가 PASS 라는
   것은 "명백히 긴 문장이 없다"는 뜻이지 "읽기 쉽다"는 뜻이 아니다. 실제 판단은 LLM 검증자
   (reviewer)의 몫이고, 이 게이트는 그 앞의 바닥을 받칠 뿐이다.

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.a11y_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : content/ 디렉터리(하위 폴더 포함) 또는 단일 문서

정책 필드(a11y_policy)
  require_alt_text (기본 true)
  max_words_per_sentence (기본 {undergraduate: 22, graduate: 26, adult: 18, mooc: 18})
  readability_is_fail (기본 false) · max_violation_ratio (기본 0.3)
  require_speaker_notes_in (기본 [slides]) — 발표자 노트가 있어야 할 산출물

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
CODE_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
MD_IMAGE_RE = re.compile(r"!\[(.*?)\]\([^)]*\)")
HINT_RE = re.compile(r"^\s*>\s*(?:이미지|그림|도표|Image hint|Figure)\s*[:：]\s*(.+)$",
                     re.MULTILINE | re.IGNORECASE)
ALT_RE = re.compile(r"(?:alt[-_ ]?text|대체\s*텍스트)\s*[:：]\s*(.+)", re.IGNORECASE)
BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
NOTES_RE = re.compile(r"(?:발표자\s*노트|speaker\s*notes?|<!--\s*note)", re.IGNORECASE)

DEFAULT_MAX_WORDS = {"undergraduate": 22, "graduate": 26, "adult": 18, "mooc": 18}


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("a11y_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("a11y_policy", {}) or {}


def scope_level(root: str) -> str | None:
    try:
        m = FRONTMATTER_RE.match(open(os.path.join(root, "SCOPE.md"), encoding="utf-8").read())
    except OSError:
        return None
    v = (yaml.safe_load(m.group(1)) or {}).get("education_level") if m else None
    return str(v).strip().lower() if v else None


def images(text: str) -> list[tuple[str, bool]]:
    """(설명, 대체텍스트 있음) 목록. 마크다운 이미지와 '이미지:' 힌트 둘 다 본다."""
    out = []
    for m in MD_IMAGE_RE.finditer(text):
        alt = m.group(1).strip()
        out.append((m.group(0)[:60], bool(alt) and alt.lower() not in ("image", "그림", "img")))
    for m in HINT_RE.finditer(text):
        hint = m.group(1)
        out.append((hint[:60], bool(ALT_RE.search(hint))))
    return out


def sentences(text: str) -> list[str]:
    """문장 단위. ⚠️ **불릿·표 줄은 각각 하나의 단위**로 본다 — 원본처럼 빈 줄로만 나누면
    마침표 없는 슬라이드 불릿 블록이 통째로 문장 1개가 되어 어절 수가 부풀려진다."""
    body = FRONTMATTER_RE.sub("", text, count=1)
    body = CODE_FENCE_RE.sub(" ", body)
    units: list[str] = []
    for line in body.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or set(s) <= set("|-: "):
            continue
        if BULLET_RE.match(s) or s.startswith("|"):
            units.append(BULLET_RE.sub("", s).strip(" |"))
        else:
            units += [x.strip() for x in re.split(r"(?<=[.!?。！？])\s+", s) if x.strip()]
    return [u for u in units if len(u.split()) >= 2]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", default=None, help="미사용(gate_keeper 규약상 전달됨)")
    ap.add_argument("--draft", default=None, help="content/ 디렉터리 또는 단일 문서")
    args = ap.parse_args()

    if not args.draft:
        print("FAIL(usage): --draft(content/) 필수 — fail-closed", file=sys.stderr); return 2
    try:
        policy = load_policy(args.policy)
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e} — fail-closed", file=sys.stderr); return 2

    files: list[str] = []
    if os.path.isdir(args.draft):
        for dirpath, _d, names in os.walk(args.draft):
            files += [os.path.join(dirpath, n) for n in sorted(names) if n.endswith(".md")]
        files.sort()
        root = os.path.dirname(os.path.abspath(args.draft))
    elif os.path.isfile(args.draft):
        files = [args.draft]
        root = os.path.dirname(os.path.dirname(os.path.abspath(args.draft)))
    if not files:
        print(f"FAIL(usage): 콘텐츠를 찾지 못했다({args.draft}) — fail-closed", file=sys.stderr)
        return 2

    level = scope_level(root) or "undergraduate"
    maxw_cfg = policy.get("max_words_per_sentence") or DEFAULT_MAX_WORDS
    max_words = int(maxw_cfg.get(level, DEFAULT_MAX_WORDS.get(level, 22))) \
        if isinstance(maxw_cfg, dict) else int(maxw_cfg)
    require_alt = bool(policy.get("require_alt_text", True))
    read_is_fail = bool(policy.get("readability_is_fail", False))
    max_ratio = float(policy.get("max_violation_ratio", 0.3))
    notes_in = [str(x).lower() for x in (policy.get("require_speaker_notes_in") or ["slides"])]

    print(f"교육 수준 {level} · 문서 {len(files)}건 · 문장당 어절 상한 {max_words} "
          f"(가독성 {'FAIL' if read_is_fail else 'WARNING'})")

    fail = False
    n_img = n_noalt = 0
    long_total = sent_total = 0
    for path in files:
        rel = os.path.relpath(path, args.draft if os.path.isdir(args.draft) else root)
        try:
            text = open(path, encoding="utf-8").read()
        except OSError as e:
            print(f"FAIL: {rel} 읽기 실패 ({e})"); fail = True; continue

        imgs = images(text)
        noalt = [d for d, ok in imgs if not ok]
        n_img += len(imgs); n_noalt += len(noalt)
        if require_alt and noalt:
            print(f"FAIL: {rel} — 대체 텍스트 없는 이미지 {len(noalt)}건: {noalt[:3]}")
            print(f"      (`![설명](경로)` 의 설명을 채우거나 `> 이미지: … (대체 텍스트: …)`)")
            fail = True

        sents = sentences(text)
        long_ones = [s for s in sents if len(s.split()) > max_words]
        sent_total += len(sents); long_total += len(long_ones)
        if long_ones:
            ratio = len(long_ones) / len(sents)
            tag = "FAIL" if (read_is_fail and ratio > max_ratio) else "WARNING"
            print(f"{tag}: {rel} — 긴 문장 {len(long_ones)}/{len(sents)} ({ratio:.0%}) "
                  f"· 최장 {max(len(s.split()) for s in long_ones)}어절")
            if tag == "FAIL":
                fail = True

        if any(k in rel.lower() for k in notes_in) and not NOTES_RE.search(text):
            print(f"WARNING: {rel} — 발표자 노트가 없다(시각 자료만으로는 전달되지 않는 "
                  f"맥락을 노트로 남겨라)")

    print(f"이미지 {n_img}건(대체 텍스트 누락 {n_noalt}) · 문장 {sent_total}개"
          f"(상한 초과 {long_total})")
    if not fail:
        print("  ✓ 접근성 기준 충족")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
