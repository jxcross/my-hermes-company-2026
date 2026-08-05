#!/usr/bin/env python3
"""
객관 게이트: 덱 규격 — 슬라이드 과적재·Marp 구조·번들 조립
=============================================================
슬라이드가 **한 장에 담을 만큼만** 담았는지, 번들이 **실제로 조립됐는지**(미치환 placeholder·
누락 파일) LLM 없이 검사한다.
출처: slideforge — **이 검사가 통째로 없다.** 신설.

⚠️ **원본은 슬라이드 규율을 CLAUDE.md 에 지시로만 적어 둔다**:

       - 슬라이드당 본문 ≤ 5 bullets 또는 1 figure (정보 과적재 금지)
       - Marp 표준 — `---` 슬라이드 구분, frontmatter `marp: true`

   그리고 **이를 검사하는 코드는 없다**(하드게이트는 시간·노트·mermaid 만 본다).
   patentforge 의 고지 승격 · docforge 의 '환각 금지 선언' 과 같은 계열이다 —
   **도메인의 규율은 지시가 아니라 게이트로 올린다**(docs/13 §5).

⚠️ **미치환 placeholder 가 조용히 남는다.** `marp_export.py` 는 `{{mermaid:dN}}` 을 찾지
   못하면 그 자리에 `<!-- missing mermaid: dN -->` 를 **주석으로** 써 넣는다. Marp 는 주석을
   렌더하지 않으므로 **발표장에서 빈 슬라이드가 뜬다** — 아무도 모른 채 finalize 된다.
   → 번들 모드에서 미치환 표식을 FAIL 로 잡는다.

⚠️ **상한만 재면 빈 슬라이드가 가장 안전하다**(research-proposal 의 교훈 · 아홉 번째).
   불릿 5개 상한만 두면 **불릿 0개짜리 슬라이드가 가장 잘 통과한다.** → 본문 어절의
   **하한**을 짝으로 뒀다.

⚠️ **문장 길이는 이 게이트가 재지 않는다** — `content_accessibility`(아키타입 J 재사용)의
   일이다. 같은 것을 두 게이트가 재면 어느 쪽이 규칙인지 흐려진다(docs/13 §2④).
   여기서는 **구조**(불릿 개수·제목·frontmatter·번들)만 본다.

두 모드 (판정 첫 줄에 출력한다)
  · deck   — 슬라이드만 있다(전달 검토 단계).
  · bundle — 번들까지 조립됐다(Deliver 직전). 조립 산출물의 실체까지 본다.

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.deck_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : 슬라이드 디렉터리 또는 미션 디렉터리(위로 올라가 SCOPE.md 를 찾는다)

정책 필드(deck_policy)
  slides_dir (기본 _private/slides) · bundle_dir (기본 _private/slide-bundle)
  bundle_files (기본 [slides.md, speaker-notes.md, handout.md])
  max_bullets (기본 5) · max_bullets_with_visual (기본 2) · max_visuals (기본 1)
  min_body_words (기본 4) · max_body_words (기본 60)   # 국문 어절
  require_title (기본 true) · required_fields (기본 [slide_number, section, title])
  handout_words (기본 [150, 900]) · unresolved_markers

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
SPEAKER_RE = re.compile(r"<!--\s*speaker\s*:?\s*\n?(.*?)-->", re.DOTALL)
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
CODE_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\S")
HEADING_RE = re.compile(r"^(#{1,6})\s+(\S.*)$", re.MULTILINE)
IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
MERMAID_PH_RE = re.compile(r"\{\{mermaid:([A-Za-z]?\d+)\}\}")
SLIDE_FILE_RE = re.compile(r"^slide-(\d+)\.md$")
NOTE_ITEM_RE = re.compile(r"^#{2,3}\s*(?:slide|슬라이드)?\s*[:\s]*(\d+)\b",
                          re.MULTILINE | re.IGNORECASE)

DEFAULT_FIELDS = ["slide_number", "section", "title"]
DEFAULT_BUNDLE = ["slides.md", "speaker-notes.md", "handout.md"]
DEFAULT_MARKERS = ["{{mermaid:", "missing mermaid", "TODO", "TBD", "작성 예정"]


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("deck_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("deck_policy", {}) or {}


def mission_root(draft: str) -> str:
    """draft 가 슬라이드 디렉터리여도 위로 올라가 `SCOPE.md` 가 있는 곳을 찾는다
    (한 stage 의 게이트들이 draft 하나를 공유하기 때문 · docs/13 §5)."""
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


def words(s: str) -> int:
    return len([w for w in re.split(r"\s+", s.strip()) if w])


def body_of(text: str) -> str:
    """frontmatter·발표자 노트·주석·코드펜스를 걷어낸 **청중이 보는 본문**."""
    t = FRONTMATTER_RE.sub("", text, count=1)
    t = SPEAKER_RE.sub(" ", t)
    t = COMMENT_RE.sub(" ", t)
    return CODE_FENCE_RE.sub(" ", t)


def count_bullets(body: str) -> int:
    return sum(1 for line in body.splitlines() if BULLET_RE.match(line))


def count_visuals(body: str) -> int:
    return len(IMAGE_RE.findall(body)) + len(MERMAID_PH_RE.findall(body))


def deck_slide_chunks(text: str) -> list[str]:
    """Marp 단일 파일의 슬라이드 조각. 덱 frontmatter 는 제외한다."""
    t = text
    m = FRONTMATTER_RE.match(t)
    if m:
        t = t[m.end():]
    return [c for c in re.split(r"^---\s*$", t, flags=re.MULTILINE) if c.strip()]


def main() -> int:  # noqa: C901
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", default=None, help="미사용(gate_keeper 규약상 전달됨)")
    ap.add_argument("--draft", default=None, help="슬라이드 디렉터리 또는 미션 디렉터리")
    args = ap.parse_args()

    if not args.draft:
        print("FAIL(usage): --draft 필수 — fail-closed", file=sys.stderr); return 2
    try:
        policy = load_policy(args.policy)
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e} — fail-closed", file=sys.stderr); return 2

    root = mission_root(args.draft)
    slides_d = os.path.join(root, policy.get("slides_dir") or "_private/slides")
    bundle_d = os.path.join(root, policy.get("bundle_dir") or "_private/slide-bundle")
    max_b = int(policy.get("max_bullets", 5))
    max_bv = int(policy.get("max_bullets_with_visual", 2))
    max_v = int(policy.get("max_visuals", 1))
    min_w = int(policy.get("min_body_words", 4))
    max_w = int(policy.get("max_body_words", 60))
    fields = [str(x) for x in (policy.get("required_fields") or DEFAULT_FIELDS)]
    need_title = bool(policy.get("require_title", True))
    bundle_files = [str(x) for x in (policy.get("bundle_files") or DEFAULT_BUNDLE)]
    markers = [str(x) for x in (policy.get("unresolved_markers") or DEFAULT_MARKERS)]
    hand_lo, hand_hi = (policy.get("handout_words") or [150, 900])[:2]

    names = sorted(n for n in (os.listdir(slides_d) if os.path.isdir(slides_d) else [])
                   if SLIDE_FILE_RE.match(n))
    if not names:
        print(f"FAIL(usage): 슬라이드를 찾지 못했다({os.path.relpath(slides_d, root)}) — "
              f"fail-closed", file=sys.stderr)
        return 2

    mode = "bundle" if os.path.isdir(bundle_d) else "deck"
    print(f"모드={mode} · 슬라이드 {len(names)}장 · 불릿 상한 {max_b}"
          f"(시각자료 있으면 {max_bv}) · 본문 어절 {min_w}~{max_w}")
    fail = False

    for name in names:
        num = int(SLIDE_FILE_RE.match(name).group(1))
        text = open(os.path.join(slides_d, name), encoding="utf-8").read()
        fm = FRONTMATTER_RE.match(text)
        if not fm:
            print(f"FAIL: {name} 에 frontmatter 가 없다 — Marp 슬라이드 규약을 벗어난다")
            fail = True
            continue
        try:
            meta = yaml.safe_load(fm.group(1)) or {}
        except yaml.YAMLError as e:
            print(f"FAIL: {name} frontmatter 파싱 실패 ({e})")
            fail = True
            continue
        for f in fields:
            if not str(meta.get(f, "")).strip():
                print(f"FAIL: {name} frontmatter 에 `{f}` 가 없다")
                fail = True
        try:
            if int(meta.get("slide_number")) != num:
                print(f"FAIL: {name} 의 `slide_number: {meta.get('slide_number')}` 가 "
                      f"파일명({num})과 다르다 — 병합 순서가 어긋난다")
                fail = True
        except (TypeError, ValueError):
            pass  # 위에서 필수 필드 부재로 이미 잡았다

        body = body_of(text)
        if need_title and not HEADING_RE.search(body):
            print(f"FAIL: {name} 본문에 제목(`## …`)이 없다 — frontmatter 의 title 은 "
                  f"메타데이터일 뿐 청중에게 보이지 않는다")
            fail = True
        n_v = count_visuals(body)
        n_b = count_bullets(body)
        cap = max_bv if n_v else max_b
        if n_b > cap:
            print(f"FAIL: {name} 의 불릿 {n_b}개 > 상한 {cap}"
                  f"{'(시각자료 있음)' if n_v else ''} — 정보 과적재. **원본은 이 규율을 "
                  f"지시로만 적어 두고 검사하지 않는다**")
            fail = True
        if n_v > max_v:
            print(f"FAIL: {name} 에 시각자료 {n_v}개 > 상한 {max_v} — 한 장에 그림 하나다")
            fail = True
        # 제목 줄을 뺀 본문 어절. 상한만 재면 빈 슬라이드가 가장 안전하다(§5).
        text_wo_head = HEADING_RE.sub(" ", body)
        bw = words(text_wo_head)
        if bw < min_w and n_v == 0:
            print(f"FAIL: {name} 의 본문이 {bw}어절 — 하한 {min_w}. 제목만 있고 내용이 없는 "
                  f"슬라이드다(상한만 재는 게이트는 빈 것을 가장 잘 통과시킨다)")
            fail = True
        if bw > max_w:
            print(f"FAIL: {name} 의 본문이 {bw}어절 > 상한 {max_w} — 슬라이드가 문서가 됐다")
            fail = True

    if mode == "deck":
        if not fail:
            print(f"  ✓ 슬라이드 {len(names)}장이 규격 안이다(번들 조립 후 bundle 모드에서 "
                  f"조립 산출물을 본다)")
        print("VERDICT:", "FAIL" if fail else "PASS")
        return 1 if fail else 0

    # ── 번들 모드 ────────────────────────────────────────────────────────────
    for f in bundle_files:
        p = os.path.join(bundle_d, f)
        if not os.path.isfile(p):
            print(f"FAIL: 번들에 {f} 가 없다({os.path.relpath(bundle_d, root)})")
            fail = True

    deck_p = os.path.join(bundle_d, "slides.md")
    if os.path.isfile(deck_p):
        dtext = open(deck_p, encoding="utf-8").read()
        dfm = FRONTMATTER_RE.match(dtext)
        dmeta = {}
        if dfm:
            try:
                dmeta = yaml.safe_load(dfm.group(1)) or {}
            except yaml.YAMLError:
                dmeta = {}
        if dmeta.get("marp") is not True:
            print("FAIL: slides.md frontmatter 에 `marp: true` 가 없다 — Marp 가 이 파일을 "
                  "덱으로 읽지 않는다")
            fail = True
        if not str(dmeta.get("theme", "")).strip():
            print("FAIL: slides.md frontmatter 에 `theme:` 가 없다")
            fail = True
        chunks = deck_slide_chunks(dtext)
        if len(chunks) != len(names):
            print(f"FAIL: slides.md 의 슬라이드 조각이 {len(chunks)}개인데 원본 슬라이드는 "
                  f"{len(names)}장이다 — 병합에서 빠지거나 잘렸다")
            fail = True
        for mk in markers:
            if mk.lower() in dtext.lower():
                print(f"FAIL: slides.md 에 미치환 표식 '{mk}' 이 남았다 — `marp_export` 는 "
                      f"다이어그램을 못 찾으면 `<!-- missing mermaid: dN -->` **주석**을 넣는다. "
                      f"Marp 는 주석을 렌더하지 않으므로 **발표장에서 빈 슬라이드가 뜬다**")
                fail = True
                break

    notes_p = os.path.join(bundle_d, "speaker-notes.md")
    if os.path.isfile(notes_p):
        ntext = open(notes_p, encoding="utf-8").read()
        listed = {int(m.group(1)) for m in NOTE_ITEM_RE.finditer(ntext)}
        want = {int(SLIDE_FILE_RE.match(n).group(1)) for n in names}
        if listed != want:
            print(f"FAIL: 번들 speaker-notes.md 의 슬라이드 항목이 어긋난다"
                  f"(누락 {sorted(want - listed)[:5]} · 초과 {sorted(listed - want)[:5]})")
            fail = True

    hand_p = os.path.join(bundle_d, "handout.md")
    if os.path.isfile(hand_p):
        hw = words(body_of(open(hand_p, encoding="utf-8").read()))
        if hw < int(hand_lo):
            print(f"FAIL: handout.md 가 {hw}어절 — 하한 {hand_lo}. 배포용 1쪽 요약이 "
                  f"제목만 있으면 배포할 것이 없다")
            fail = True
        elif hw > int(hand_hi):
            print(f"FAIL: handout.md 가 {hw}어절 > 상한 {hand_hi} — 1쪽 요약이 아니다")
            fail = True

    if not fail:
        print(f"  ✓ 슬라이드 {len(names)}장 규격 · 번들 {bundle_files} 조립 · 미치환 표식 없음")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
