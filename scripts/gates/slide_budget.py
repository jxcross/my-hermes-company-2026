#!/usr/bin/env python3
"""
객관 게이트: 발표 분량 예산 — 슬라이드 수·시간 배분·노트 실체
==================================================================
발표 시간에 맞는 슬라이드 수인지(**양방향**), 목차가 선언한 슬라이드가 **전부 만들어졌는지**,
모든 슬라이드에 **실체 있는 발표자 노트**가 붙었는지 LLM 없이 검사한다.
출처: slideforge 의 HARD GATE(`timing_check.py`) — 이식하며 판정을 네 군데 고쳤다.

⚠️ **원본은 상한만 잰다**(실측 · docs/13 §5):

       estimated = n * ctx["min_per_slide"]
       ok = estimated <= ctx["talk_time_minutes"]

   → **20분 발표에 슬라이드 2장이 `PASS`**(실측 `2 slides × 1.0 = 2.0 min vs cap 20.0`).
   "한도 이하"는 0 에서 가장 잘 만족된다 — research-proposal 의 '빈 제안서가 가장 안전하게
   통과한다' 와 같은 자리다. → **하한을 짝으로** 뒀다(`max_per_slide` 로 하한을 만든다).

⚠️ **분모를 검사 대상이 정한다**(실측): `min_per_slide` 를 미션 산출물(`01-context.md`)에서
   읽는다. **15분 발표에 60장을 만들고 `min_per_slide: 0.1` 이라 적으면 `PASS`** 다
   (실측 `60 slides × 0.1 = 6.0 min vs cap 15.0`). → 장당 시간은 **템플릿 정책**이 갖고,
   발표 시간은 **SCOPE.md**(stage 1 · Sam 이 승인한 값)에서 읽는다. 산출물이 고칠 수 없다.

⚠️ **`--notes` 는 죽은 인자였다**(실측): argparse 가 `required=True` 로 받아 놓고 코드가
   **한 번도 참조하지 않는다**(`check_notes_coverage(slides_dir)`). 존재하지 않는 경로를 줘도
   `PASS` 다 — 통합 노트 문서가 아예 없어도 '노트 커버리지 통과' 가 나온다.
   simforge 의 `--doe`(`--help` 에까지 광고하고 코드에서 미참조)와 같은 계열. → 실제로 읽는다.

⚠️ **플레이스홀더 필터가 한국어에서 무력했다**(실측): `body.lower() in ("tbd","todo","...")`
   는 완전 일치라 **`TBD.`(마침표 하나)도, `작성 예정` 도 통과**한다. patent-spec 이후 반복되는
   한국어 함정이다. → 금칙어 부분일치 + **국문 어절 하한**으로 실체를 요구한다.

⚠️ **선언 목록 대비 존재를 보지 않는다**: 섹션 워커 5개 중 하나가 죽어 method 슬라이드가
   통째로 없어도, 남은 슬라이드가 시간 상한 아래이므로 통과한다. policy-brief 에서 배운
   '병렬 산출물은 선언 목록 대비 존재를 확인하라' 를 여기에 적용했다.

두 모드 (아키타입 K·P·Q·R·S 와 같은 방식 — 판정 첫 줄에 출력한다)
  · plan  — 슬라이드가 아직 없다(설계 검증 단계). 목차의 슬라이드 수·시간 배분만 본다.
  · final — 슬라이드·노트까지 있다. 선언 대비 존재와 노트 실체까지 본다.
  집필 **전에** 설계를 검증하는 배치다 — 16주치를 다 쓴 뒤 반려하던 lectureforge 의 반대(§5).

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.slide_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : 미션 디렉터리(reports/<MID>) 또는 그 하위(위로 올라가 SCOPE.md 를 찾는다)

SCOPE.md frontmatter 선언 (**분모** — stage 1 에서 Sam 이 승인한 값)
  talk_time_minutes: 15
  sections: [intro, method, result, discussion, closing]   # 없으면 정책값

기대 형식 (_private/outline.md)
  ---
  n_slides: 14            # ⚠️ 명시 선언 — 블록 길이와 대조한다(나중에 조용히 줄일 수 없게)
  ---
  ```slides
  - id: 1
    section: intro
    title: 문제와 배경
    time_min: 0.8
    claims: [e1]
  ```

정책 필드(slide_policy)
  outline_file (기본 _private/outline.md) · slides_dir (기본 _private/slides)
  notes_file (기본 _private/notes.md)
  min_per_slide (기본 0.75) · max_per_slide (기본 1.5) · time_sum_tolerance (기본 0.2)
  sections · require_all_sections (기본 true)
  min_note_words (기본 8 · 국문 어절) · placeholder_terms

exit: 0 PASS · 1 FAIL · 2 usage/입력없음(fail-closed)
"""
from __future__ import annotations
import argparse
import json
import math
import os
import re
import sys

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML 필요", file=sys.stderr); sys.exit(2)

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
SLIDE_BLOCK_RE = re.compile(r"```slides\s*\n(.*?)\n```", re.DOTALL)
ID_RE = re.compile(r"^\s*-\s*id:\s*(\S+)", re.MULTILINE)
FIELD_RE = re.compile(r"^\s+(\w+):\s*(.*)$")
# `<!-- speaker: … -->` 블록. 원본과 같은 형식을 읽되 판정만 바꾼다.
SPEAKER_RE = re.compile(r"<!--\s*speaker\s*:?\s*\n?(.*?)-->", re.DOTALL)
SLIDE_FILE_RE = re.compile(r"^slide-(\d+)\.md$")
# 통합 노트의 슬라이드 항목: `## Slide 3: …` · `## 슬라이드 3 …` · `## 3. …`
NOTE_ITEM_RE = re.compile(r"^#{2,3}\s*(?:slide|슬라이드)?\s*[:\s]*(\d+)\b", re.MULTILINE | re.IGNORECASE)

DEFAULT_SECTIONS = ["intro", "method", "result", "discussion", "closing"]
DEFAULT_PLACEHOLDERS = ["TBD", "TODO", "FIXME", "작성 예정", "미정", "채워", "여기에",
                        "1~3 sentences", "what to say", "..."]


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("slide_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("slide_policy", {}) or {}


def mission_root(draft: str) -> str:
    """draft 가 하위 디렉터리여도 위로 올라가 `SCOPE.md` 가 있는 곳을 미션 루트로 삼는다.

    ⚠️ **한 stage 의 객관 게이트는 `--draft` 를 하나만 공유한다**(gate_keeper). 게이트마다
       기대하는 draft 가 다르면 그 조합은 성립하지 않는다 — 아키타입 S 에서 실제로 그랬다
       (docs/13 §5). `legal_safety` 의 관용구를 따른다."""
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


def scope(root: str) -> dict:
    try:
        m = FRONTMATTER_RE.match(open(os.path.join(root, "SCOPE.md"), encoding="utf-8").read())
    except OSError:
        return {}
    return (yaml.safe_load(m.group(1)) or {}) if m else {}


def parse_block(text: str, block_re: re.Pattern) -> list[dict] | None:
    m = block_re.search(text)
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


def words(s: str) -> int:
    """국문 어절 = 공백 토큰. 영문 word 와 달리 조사가 붙어 개수가 적다(§5 재보정)."""
    return len([w for w in re.split(r"\s+", s.strip()) if w])


def note_body(text: str) -> str | None:
    m = SPEAKER_RE.search(text)
    return m.group(1).strip() if m else None


def is_placeholder(s: str, terms: list[str]) -> str | None:
    low = s.lower()
    for t in terms:
        if t.lower() in low:
            return t
    return None


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
    sc = scope(root)
    outline_p = os.path.join(root, policy.get("outline_file") or "_private/outline.md")
    slides_d = os.path.join(root, policy.get("slides_dir") or "_private/slides")
    notes_p = os.path.join(root, policy.get("notes_file") or "_private/notes.md")

    # ── 분모: 발표 시간은 SCOPE(Sam 승인) · 장당 시간은 정책(템플릿). 산출물이 못 고친다 ──
    try:
        talk = float(sc.get("talk_time_minutes"))
    except (TypeError, ValueError):
        print("FAIL(usage): SCOPE.md 에 `talk_time_minutes:` 선언이 없다 — 발표 시간을 모르면 "
              "분량을 잴 수 없다. **원본은 이 값을 미션 산출물에서 읽어 산출물이 스스로 분모를 "
              "정했다**. fail-closed", file=sys.stderr)
        return 2
    lo_min = float(policy.get("min_per_slide", 0.75))
    hi_min = float(policy.get("max_per_slide", 1.5))
    if lo_min <= 0 or hi_min < lo_min:
        print(f"FAIL(usage): 장당 시간 정책이 이상하다(min={lo_min} max={hi_min}) — fail-closed",
              file=sys.stderr)
        return 2
    tol = float(policy.get("time_sum_tolerance", 0.2))
    sections = [str(x).strip().lower() for x in
                (sc.get("sections") or policy.get("sections") or DEFAULT_SECTIONS)]
    terms = policy.get("placeholder_terms") or DEFAULT_PLACEHOLDERS
    min_note_w = int(policy.get("min_note_words", 8))

    try:
        otext = open(outline_p, encoding="utf-8").read()
    except OSError:
        print(f"FAIL(usage): 목차를 찾지 못했다({os.path.relpath(outline_p, root)}) — 무엇을 "
              f"만들기로 했는지 모르면 만들어진 것을 대조할 수 없다. fail-closed", file=sys.stderr)
        return 2
    declared = parse_block(otext, SLIDE_BLOCK_RE)
    if declared is None:
        print(f"FAIL(usage): {os.path.relpath(outline_p, root)} 에 ```slides``` 블록이 없다 — "
              f"fail-closed", file=sys.stderr)
        return 2

    files = sorted(n for n in (os.listdir(slides_d) if os.path.isdir(slides_d) else [])
                   if SLIDE_FILE_RE.match(n))
    mode = "final" if files else "plan"
    n_min = math.ceil(talk / hi_min - 1e-9)
    n_max = math.floor(talk / lo_min + 1e-9)
    print(f"모드={mode} · 발표 {talk:g}분 · 선언 슬라이드 {len(declared)}장 "
          f"(허용 {n_min}~{n_max}장 = {talk:g}분 ÷ {hi_min:g}~{lo_min:g}분/장) · "
          f"산출 파일 {len(files)}개")
    fail = False

    # ── ① 분모 고정: n_slides 선언과 블록 길이 대조 ──────────────────────────
    fm = FRONTMATTER_RE.match(otext)
    fmd = (yaml.safe_load(fm.group(1)) or {}) if fm else {}
    try:
        n_declared = int(fmd.get("n_slides"))
    except (TypeError, ValueError):
        print("FAIL: 목차 frontmatter 에 `n_slides:` 선언이 없다 — 선언을 따로 두지 않으면 "
              "블록에서 슬라이드를 지워도 '내부적으로 일관' 해져 통과한다(sim-experiment 의 "
              "설계점 함정과 같은 자리)")
        fail = True
        n_declared = None
    if n_declared is not None and n_declared != len(declared):
        print(f"FAIL: `n_slides: {n_declared}` 인데 ```slides``` 블록은 {len(declared)}장이다")
        fail = True

    # ── ② 슬라이드 수 — 양방향(원본은 상한만 잰다) ───────────────────────────
    n = len(declared)
    if n == 0:
        print("FAIL: 목차에 슬라이드가 한 장도 없다(공집합 통과 방지)")
        fail = True
    elif n < n_min:
        print(f"FAIL: 슬라이드 {n}장 < 하한 {n_min}장 — {talk:g}분을 채우려면 장당 "
              f"{talk / n:.1f}분을 말해야 한다(상한 {hi_min:g}분/장). **원본은 이때 PASS 였다** "
              f"— 20분 발표에 2장이 통과한다")
        fail = True
    elif n > n_max:
        print(f"FAIL: 슬라이드 {n}장 > 상한 {n_max}장 — 장당 {talk / n:.2f}분(하한 "
              f"{lo_min:g}분/장)이라 넘길 시간도 없다")
        fail = True

    # ── ③ 슬라이드 선언의 충실도 ─────────────────────────────────────────────
    ids: list[int] = []
    tsum = 0.0
    seen_sections: set[str] = set()
    by_id: dict[int, dict] = {}
    for d in declared:
        try:
            sid = int(str(d["id"]).strip())
        except ValueError:
            print(f"FAIL: 슬라이드 id '{d['id']}' 가 정수가 아니다")
            fail = True
            continue
        ids.append(sid)
        by_id[sid] = d
        sec = str(d.get("section", "")).strip().lower()
        if sec not in sections:
            print(f"FAIL: 슬라이드 {sid} 의 section '{sec or '(없음)'}' 이 선언 목록 "
                  f"{sections} 밖이다")
            fail = True
        else:
            seen_sections.add(sec)
        if not str(d.get("title", "")).strip():
            print(f"FAIL: 슬라이드 {sid} 에 title 이 없다")
            fail = True
        try:
            t = float(str(d.get("time_min", "")).strip())
        except ValueError:
            t = -1.0
        if t <= 0:
            print(f"FAIL: 슬라이드 {sid} 의 `time_min` 이 없거나 0 이하다 — 시간 배분을 적지 "
                  f"않으면 합계를 잴 수 없다")
            fail = True
        else:
            tsum += t
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        print(f"FAIL: 슬라이드 id 중복 {dup}")
        fail = True
    if ids and sorted(set(ids)) != list(range(1, max(ids) + 1)):
        print(f"FAIL: 슬라이드 id 가 1..{max(ids)} 로 연속되지 않는다(빠진 번호: "
              f"{sorted(set(range(1, max(ids) + 1)) - set(ids))})")
        fail = True

    # ── ④ 시간 배분 합계 ↔ 발표 시간 ─────────────────────────────────────────
    if tsum > 0 and abs(tsum - talk) > talk * tol:
        print(f"FAIL: 시간 배분 합계 {tsum:.1f}분이 발표 시간 {talk:g}분과 "
              f"{abs(tsum - talk) / talk:.0%} 차이다(허용 {tol:.0%}) — 배분을 적어 놓고 "
              f"합이 맞지 않으면 리허설에서 무너진다")
        fail = True

    # ── ⑤ 섹션 커버리지 — 병렬 워커 하나가 죽은 것을 여기서 잡는다 ───────────
    if bool(policy.get("require_all_sections", True)):
        missing = [s for s in sections if s not in seen_sections]
        if missing:
            print(f"FAIL: 선언한 섹션 중 목차에 없는 것 {missing} — 섹션 워커가 하나 죽으면 "
                  f"그 섹션이 통째로 비고, 원본은 남은 슬라이드가 시간 상한 아래라 통과시킨다")
            fail = True

    if mode == "plan":
        if not fail:
            print(f"  ✓ 목차 {n}장 · 시간 배분 {tsum:.1f}분 · 섹션 {sorted(seen_sections)} "
                  f"(집필 후 final 모드에서 산출물을 대조한다)")
        print("VERDICT:", "FAIL" if fail else "PASS")
        return 1 if fail else 0

    # ── ⑥ 선언 목록 대비 존재 ────────────────────────────────────────────────
    produced = {int(SLIDE_FILE_RE.match(n_).group(1)): n_ for n_ in files}
    for sid in sorted(by_id):
        if sid not in produced:
            print(f"FAIL: 슬라이드 {sid}({by_id[sid].get('section')}/"
                  f"{by_id[sid].get('title')}) 의 파일이 없다 — 선언했는데 만들어지지 않았다")
            fail = True
    for sid in sorted(produced):
        if sid not in by_id:
            print(f"FAIL: 목차에 없는 슬라이드 파일 {produced[sid]} 가 있다 — 승인된 목차 "
                  f"밖의 슬라이드다")
            fail = True

    # ── ⑦ 노트 실체 — 원본은 'TBD.' 와 '작성 예정' 을 통과시켰다 ─────────────
    n_with = 0
    for sid in sorted(produced):
        p = os.path.join(slides_d, produced[sid])
        text = open(p, encoding="utf-8").read()
        body = note_body(text)
        if body is None:
            print(f"FAIL: {produced[sid]} 에 `<!-- speaker: … -->` 블록이 없다")
            fail = True
            continue
        hit = is_placeholder(body, terms)
        if not body or hit:
            print(f"FAIL: {produced[sid]} 의 발표자 노트가 플레이스홀더다"
                  f"{f'({hit})' if hit else ''} — **원본은 `TBD.` 와 `작성 예정` 을 "
                  f"통과시켰다**(완전 일치 비교였다)")
            fail = True
            continue
        if words(body) < min_note_w:
            print(f"FAIL: {produced[sid]} 의 노트가 {words(body)}어절 — 하한 {min_note_w}어절. "
                  f"'할 말' 이 한 마디도 아니면 노트가 아니다")
            fail = True
            continue
        n_with += 1
        sec = str(by_id.get(sid, {}).get("section", "")).strip().lower()
        fm2 = FRONTMATTER_RE.match(text)
        fsec = str(((yaml.safe_load(fm2.group(1)) or {}) if fm2 else {})
                   .get("section", "")).strip().lower()
        if sec and fsec and sec != fsec:
            print(f"FAIL: {produced[sid]} 의 section '{fsec}' 이 목차 선언 '{sec}' 과 다르다")
            fail = True

    # ── ⑧ 통합 노트 — 원본이 인자로 받기만 하고 읽지 않던 파일이다 ───────────
    if not os.path.isfile(notes_p):
        print(f"FAIL: 통합 노트가 없다({os.path.relpath(notes_p, root)}) — **원본은 이 파일을 "
              f"`--notes` 로 받아 놓고 코드에서 한 번도 읽지 않는다**(존재하지 않는 경로를 줘도 "
              f"PASS 였다)")
        fail = True
    else:
        ntext = open(notes_p, encoding="utf-8").read()
        listed = {int(m.group(1)) for m in NOTE_ITEM_RE.finditer(ntext)}
        missing = sorted(set(by_id) - listed)
        if missing:
            print(f"FAIL: 통합 노트에 슬라이드 {missing[:5]} 항목이 없다 "
                  f"({len(listed)}/{len(by_id)}장) — 슬라이드 안의 노트와 통합 노트가 "
                  f"어긋나면 리허설에서 쓰는 쪽이 비어 있게 된다")
            fail = True
        extra = sorted(listed - set(by_id))
        if extra:
            print(f"FAIL: 통합 노트에 존재하지 않는 슬라이드 {extra[:5]} 항목이 있다")
            fail = True

    if not fail:
        print(f"  ✓ 슬라이드 {len(produced)}장 전부 선언과 일치 · 노트 {n_with}/{len(produced)}장 "
              f"실체 확인 · 통합 노트 대조 완료")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
