#!/usr/bin/env python3
"""
객관 게이트: 발신 톤 — 과장 억제
==================================
공개 발신물에 **과장 표현**이 얼마나 들어갔는지, 채널별 톤 규칙(이모지·해시태그·전부
대문자)을 지켰는지 LLM 없이 검사한다.
출처: outreachforge 의 stage 7 크리틱 `tone-style-check` — **스크립트가 없다**(LLM 서술뿐).
과장 임계만 HARD GATE(`fact_check.py`) 안에 섞여 있었다. 신설.

⚠️ **원본의 과장 임계는 채널당 5건이었다**(실측 · docs/13 §5):

       획기적이고 혁명적인 놀라운 breakthrough 이며 전례없는 성과다.
       → hype=5 · overall: PASS · exit=0

   **한 문장에 다섯 개를 넣어도 통과한다.** 게다가 `HYPE_WARN = 2` 는 보고서 dict 에만
   나오고 판정에 쓰이지 않는 **죽은 상수**다(lectureforge 의 `pass` 본문, simforge 의
   `--doe` 와 같은 계열). → 기본 임계를 **채널당 1**로 낮추고 정책으로 뺐다.
   과장은 세는 것이 목적이 아니라 **줄이는 것**이 목적이다.

⚠️ **과장을 0 으로 강제하지는 않는다.** 발신물은 읽히라고 쓰는 것이고 '놀라운' 한 마디가
   늘 거짓은 아니다. 막는 것은 **누적**이다(secforge 에서 배운 것 — 게이트가 목적과
   싸우면 안 된다). 임계는 정책 소유이고 미션마다 조정한다.

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.tone_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : 미션 디렉터리(reports/<MID>)

정책 필드(tone_policy)
  channels_dir (기본 _private/channels)
  hype_patterns · max_hype_per_channel (기본 1)
  banned_phrases (경쟁 비하·클릭베이트) · max_emoji_per_post (기본 2, twitter)
  max_hashtags_per_post (기본 3) · max_allcaps_words (기본 2)

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
POST_NO_RE = re.compile(r"^#{1,3}\s*(\d+)\s*/\s*(\d+)\s*$", re.MULTILINE)
EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF⬀-⯿]")

DEFAULT_HYPE = [
    r"\brevolutionary\b", r"\bbreakthrough\b", r"\bgame[- ]?chang(?:ing|er)\b",
    r"\bworld[- ]first\b", r"\bunprecedented\b", r"\bgroundbreaking\b",
    r"\bmind[- ]blowing\b", r"\binsane(?:ly)?\b",
    r"획기적", r"전례\s*없", r"세계\s*최초", r"혁명적", r"놀라운", r"경이적", r"압도적",
]
# 경쟁 비하·클릭베이트 — 학술 발신에서 신뢰를 가장 빨리 깎는 표현들
DEFAULT_BANNED = [
    "기존 연구는 쓸모없", "아무도 못 했던", "논문 안 읽어도",
    "everyone else failed", "nobody has done", "you won't believe",
    "forget everything you know",
]


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("tone_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("tone_policy", {}) or {}


def mission_root(draft: str) -> str:
    """미션 루트 — draft 가 하위 디렉터리여도 위로 올라가 `SCOPE.md` 가 있는 곳을 찾는다.

    ⚠️ 처음에는 `draft` 가 곧 미션 루트라고 가정했다. 그런데 **한 stage 의 객관 게이트는
       `--draft` 를 하나만 공유한다**(gate_keeper). 아키타입 S 의 stage 7·8 은 같은 stage 에
       콘텐츠 기준 게이트(evidence_grade)와 미션루트 기준 게이트를 함께 뒀고 draft 가
       `_private/channels` 였다 — **실측: 이 게이트가 exit 2 로 fail-closed 되어 실미션이
       그 자리에서 막힌다**(legalforge 의 '항상 FAIL' 과 같은 계열 · docs/13 §5).
       `legal_safety` 가 쓰던 walk-up 관용구로 두 규약 모두를 받는다."""
    p = os.path.abspath(draft)
    if not os.path.isdir(p):
        p = os.path.dirname(p)
    cur = p
    for _ in range(4):
        if os.path.isfile(os.path.join(cur, "SCOPE.md")):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return p


def body_of(text: str) -> str:
    b = FRONTMATTER_RE.sub("", text, count=1)
    return re.sub(r"```.*?```", " ", b, flags=re.DOTALL)


def count_hype(text: str, pats: list[str]) -> list[str]:
    hits = []
    for p in pats:
        hits += [m.group(0) for m in re.finditer(p, text, re.IGNORECASE)]
    return hits


def posts_of(text: str) -> list[str]:
    marks = list(POST_NO_RE.finditer(text))
    out = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        out.append(text[m.end():end])
    return out or [text]


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
    if not os.path.isdir(ch_dir):
        print(f"FAIL(usage): 채널 디렉터리가 없다({ch_dir}) — fail-closed", file=sys.stderr)
        return 2
    files = sorted(os.path.join(ch_dir, n) for n in os.listdir(ch_dir)
                   if n.endswith(".md") and not n.startswith("."))
    if not files:
        print(f"FAIL(usage): 채널 산출물이 없다 — 검사할 것이 없다는 것은 통과가 아니다. "
              f"fail-closed", file=sys.stderr)
        return 2

    hype_pats = policy.get("hype_patterns") or DEFAULT_HYPE
    max_hype = int(policy.get("max_hype_per_channel", 1))
    banned = policy.get("banned_phrases") or DEFAULT_BANNED
    max_emoji = int(policy.get("max_emoji_per_post", 2))
    max_tags = int(policy.get("max_hashtags_per_post", 3))
    max_caps = int(policy.get("max_allcaps_words", 2))

    print(f"채널 {len(files)}건 · 과장 임계 {max_hype}/채널 (원본은 5였다) · "
          f"금지 표현 {len(banned)}종")
    fail = False

    for p in files:
        name = os.path.basename(p)[:-3]
        text = body_of(open(p, encoding="utf-8").read())

        hits = count_hype(text, hype_pats)
        if len(hits) > max_hype:
            print(f"FAIL: [{name}] 과장 표현 {len(hits)}건 > 임계 {max_hype} — "
                  f"{sorted(set(hits))[:6]}. **원본은 한 문장에 다섯 개를 넣어도 통과시켰다**")
            fail = True

        bad = [b for b in banned if b.lower() in text.lower()]
        if bad:
            print(f"FAIL: [{name}] 금지 표현 {bad} — 학술 발신에서 신뢰를 가장 빨리 깎는다")
            fail = True

        caps = re.findall(r"\b[A-Z]{4,}\b", text)
        caps = [c for c in caps if c not in ("SOTA", "GPU", "CPU", "JSON", "HTTP", "API")]
        if len(caps) > max_caps:
            print(f"FAIL: [{name}] 전부 대문자 낱말 {len(caps)}건 > 임계 {max_caps} "
                  f"— {caps[:5]}")
            fail = True

        for i, post in enumerate(posts_of(text), start=1):
            n_emoji = len(EMOJI_RE.findall(post))
            if n_emoji > max_emoji:
                print(f"FAIL: [{name}] {i}번 글의 이모지 {n_emoji}개 > 임계 {max_emoji}")
                fail = True
            n_tags = len(re.findall(r"(?<!\w)#\w+", post))
            if n_tags > max_tags:
                print(f"FAIL: [{name}] {i}번 글의 해시태그 {n_tags}개 > 임계 {max_tags}")
                fail = True

        if not any(x for x in (hits[max_hype:], bad)):
            print(f"  ✓ [{name}] 과장 {len(hits)}건(임계 {max_hype}) · 금지 표현 없음")

    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
