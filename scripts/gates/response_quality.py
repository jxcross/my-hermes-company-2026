#!/usr/bin/env python3
"""
객관 게이트: 응답 품질 — 판정별 필수 요소 + 금지 표현
=======================================================
응답이 **판정에 걸맞은 내용**을 갖췄는지(반박은 근거를, 수용은 원고 위치를, 부분수용은
차이 설명을), 그리고 **리뷰어를 자극하는 표현**이 없는지 LLM 없이 검사한다.
출처: rebuttalforge 의 stage 7 크리틱 2종(`argument-strength`·`tone-polish`) —
**둘 다 스크립트가 없다**(LLM 서술뿐). 신설.

⚠️ **규칙이 이미 기계적으로 쓰여 있는데 코드가 없었다.** agent 정의와 CLAUDE.md 를 그대로
   옮기면 다음과 같다 — 판정할 수 있는 문장들이다:

     · `rebut` 은 근거를 **반드시** 인용한다(원고 절·표·수치·문헌 중 하나).
       "A `rebut` response without ANY cited evidence = HIGH automatically."
     · `partially-accept` 는 제안과 **어떻게 달라졌는지** 설명한다.
     · `accept` 는 원고의 **어디에** 반영됐는지 가리킨다("We have made the change" 만 쓰면 안 된다).
     · `clarification-only` 는 최소 3문장의 실질 답변이어야 한다.
     · 금지 표현: "리뷰어가 오해했다" · "이미 서술했다" · "명백히" · "리뷰어가 틀렸다".
       "Each banned phrase occurrence = HIGH (no exceptions; reviewers notice)."

   판정자를 LLM 하나로 두면 이 규칙들은 **매번 다시 판단**된다. 게이트로 올리면 매번 같다.
   (아키타입 M 의 `eval_set_quality`·N 의 `schema_conformance` 와 같은 자리 — 원본이
   '하드게이트' 라 부르면서 스크립트를 두지 않은 것을 코드로 옮긴다.)

⚠️ **금지 표현 목록은 정책 소유다.** 도메인·언어·저널 문화마다 다르고, 지나치게 넓히면
   정상 문서를 반려한다(legalforge 교훈). 기본값은 **리뷰어를 향한 표현**으로 좁혔다.

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.response_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : 미션 디렉터리(reports/<MID>)

정책 필드(response_policy)
  responses_dir (기본 _private/responses) · cover_letter (기본 _private/cover-letter.md)
  banned_phrases · min_response_words (기본 30)
  evidence_verdicts (기본 [rebut]) · evidence_markers
  pointer_verdicts (기본 [accept, partially-accept]) · pointer_markers
  divergence_verdicts (기본 [partially-accept]) · divergence_markers
  ※ evidence_markers·pointer_markers 는 **정규식** 목록이다(숫자를 요구해 위치를 가리키게 한다)
  min_sentences (기본 {clarification-only: 3})
  cover_letter_words (기본 [250, 500])

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
COMMENT_ID_RE = re.compile(r"^R\d+\.\d+$")
CHANGES_BLOCK_RE = re.compile(r"```changes\s*\n(.*?)\n```", re.DOTALL)
ACTION_RE = re.compile(r"^\s*-\s*(?:action|type)\s*:\s*(\S+)", re.MULTILINE)

DEFAULT_BANNED = [
    "리뷰어가 오해", "리뷰어는 오해", "리뷰어의 오해", "리뷰어가 틀렸", "리뷰어는 틀렸",
    "잘못 이해하", "이미 서술했", "이미 기술했", "이미 밝혔",
    "the reviewer misunderstood", "the reviewer is incorrect", "as we already wrote",
    "obviously",
]
# 근거·위치 표시는 **정규식**이다. 한국어에서 부분 문자열로 하면 무너진다 —
# `적절히` 안에 `절` 이 들어 있어 "적절히 수정했습니다" 가 '3.2절 인용' 으로 통과한다
# (docs/13 §5 의 한국어 함정). **숫자를 요구**하면 그 표시가 실제 위치를 가리킨다.
DEFAULT_EVIDENCE = [
    r"\d+(?:\.\d+)*\s*절", r"(?:Section|Sec\.)\s*\d", r"(?:Table|표)\s*\d",
    r"(?:Figure|Fig\.|그림)\s*\d", r"(?:Eq\.|식)\s*\(?\d", r"p\s*[<=]\s*0?\.\d",
    r"et\s+al", r"\[[A-Za-z][A-Za-z0-9_+-]*\d{2,4}[a-z]?\]", r"\d+\.\d+",
]
DEFAULT_POINTER = [
    r"\d+(?:\.\d+)*\s*절", r"(?:Section|Sec\.)\s*\d", r"(?:Table|표)\s*\d",
    r"(?:Figure|Fig\.|그림)\s*\d", r"(?:Appendix|부록)\s*[A-Z0-9]", r"\d+\s*(?:쪽|행)",
    r"(?:line|p\.)\s*\d",
]
DEFAULT_DIVERGENCE = ["대신", "다만", "그러나", "차이", "일부", "instead", "however",
                      "rather than", "partially"]


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("response_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("response_policy", {}) or {}


def mission_root(draft: str) -> str:
    p = os.path.abspath(draft)
    return p if os.path.isdir(p) else os.path.dirname(p)


def split_doc(path: str) -> tuple[dict, str]:
    text = open(path, encoding="utf-8").read()
    m = FRONTMATTER_RE.match(text)
    fm: dict = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, _, v = line.lstrip().partition(":")
                fm[k.strip()] = v.strip()
    return fm, FRONTMATTER_RE.sub("", text, count=1)


def prose(body: str) -> str:
    """코드블록(```changes``` 등)을 뺀 서술 본문 — 답변은 산문이다."""
    return re.sub(r"```.*?```", " ", body, flags=re.DOTALL)


def words(text: str) -> int:
    t = re.sub(r"[#*_>`\[\]()|-]", " ", text)
    return len([w for w in t.split() if w.strip()])


def sentences(text: str) -> int:
    return len([s for s in re.split(r"[.!?。]\s|\n다\.\s|다\.", text) if len(s.strip()) > 5])


def has_any(text: str, markers: list[str]) -> bool:
    """부분 문자열이 아니라 **정규식**으로 본다(한국어 부분 일치 오탐 방지)."""
    return any(re.search(m, text, re.IGNORECASE) for m in markers)


def has_phrase(text: str, phrases: list[str]) -> list[str]:
    """금지 표현은 문구 그대로 찾는다(정규식이 아니라 문자열)."""
    low = text.lower()
    return [p for p in phrases if p.lower() in low]


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
    resp_dir = os.path.join(root, policy.get("responses_dir") or "_private/responses")
    cover_p = os.path.join(root, policy.get("cover_letter") or "_private/cover-letter.md")
    if not os.path.isdir(resp_dir):
        print(f"FAIL(usage): 응답 디렉터리 없음({resp_dir}) — fail-closed", file=sys.stderr)
        return 2
    files = sorted(os.path.join(resp_dir, n) for n in os.listdir(resp_dir)
                   if n.endswith(".md") and not n.startswith("."))
    if not files:
        print(f"FAIL(usage): 응답이 한 건도 없다 — fail-closed", file=sys.stderr); return 2

    banned = policy.get("banned_phrases") or DEFAULT_BANNED
    min_words = int(policy.get("min_response_words", 30))
    ev_verdicts = set(policy.get("evidence_verdicts") or ["rebut"])
    ev_markers = policy.get("evidence_markers") or DEFAULT_EVIDENCE
    pt_verdicts = set(policy.get("pointer_verdicts") or ["accept", "partially-accept"])
    pt_markers = policy.get("pointer_markers") or DEFAULT_POINTER
    dv_verdicts = set(policy.get("divergence_verdicts") or ["partially-accept"])
    dv_markers = policy.get("divergence_markers") or DEFAULT_DIVERGENCE
    min_sent = policy.get("min_sentences") or {"clarification-only": 3}

    print(f"응답 {len(files)}건 · 금지 표현 {len(banned)}종 · 본문 하한 {min_words} 어절")
    fail = False

    for p in files:
        name = os.path.basename(p)
        fm, body = split_doc(p)
        stem = os.path.splitext(name)[0]
        cid = fm.get("comment_id") or (stem if COMMENT_ID_RE.match(stem) else name)
        verdict = fm.get("verdict", "").strip()
        text = prose(body)

        if words(text) < min_words:
            print(f"FAIL: {cid} 의 답변이 {words(text)} 어절 — 하한 {min_words}")
            fail = True

        hits = has_phrase(text, banned)
        if hits:
            print(f"FAIL: {cid} 에 금지 표현 {hits} — 리뷰어를 향한 표현은 재심사에서 "
                  f"그대로 읽힌다. '말씀하신 …에 대해 저희는 …근거로 달리 봅니다' 로 바꿔라")
            fail = True

        if verdict in ev_verdicts and not has_any(text, ev_markers):
            print(f"FAIL: {cid} 는 '{verdict}'(반박)인데 근거 인용이 없다 — 원고 절·표·그림·"
                  f"수치·문헌 중 하나를 대야 한다(원본 규칙: 근거 없는 반박 = HIGH)")
            fail = True

        if verdict in pt_verdicts:
            mb = CHANGES_BLOCK_RE.search(body)
            n_actions = len(ACTION_RE.findall(mb.group(1))) if mb else 0
            if n_actions < 1:
                print(f"FAIL: {cid} 는 '{verdict}' 인데 ```changes``` 블록에 액션이 없다 "
                      f"— 바꾸겠다고 하고 무엇을 바꿀지 적지 않았다")
                fail = True
            if not has_any(text, pt_markers):
                print(f"FAIL: {cid} 는 '{verdict}' 인데 원고의 **어디에** 반영됐는지 "
                      f"가리키지 않는다('수정했습니다' 만으로는 심사자가 찾을 수 없다)")
                fail = True

        if verdict in dv_verdicts and not has_any(text, dv_markers):
            print(f"FAIL: {cid} 는 '{verdict}'(부분 수용)인데 제안과 **어떻게 달라졌는지** "
                  f"설명이 없다")
            fail = True

        need = min_sent.get(verdict)
        if need and sentences(text) < int(need):
            print(f"FAIL: {cid} 는 '{verdict}' 인데 답변이 {sentences(text)}문장 — "
                  f"하한 {need}('질문 감사합니다' 로 끝나는 답변을 막는다)")
            fail = True

    # 커버레터 — 금지 표현 + 분량
    if os.path.isfile(cover_p):
        _fm, cbody = split_doc(cover_p)
        ctext = prose(cbody)
        hits = has_phrase(ctext, banned)
        if hits:
            print(f"FAIL: 커버레터에 금지 표현 {hits} — 편집자가 가장 먼저 읽는 문서다")
            fail = True
        rng = policy.get("cover_letter_words") or [250, 500]
        n = words(ctext)
        if not (int(rng[0]) <= n <= int(rng[1])):
            print(f"FAIL: 커버레터 분량 {n} 어절이 규격 {rng[0]}~{rng[1]} 밖이다")
            fail = True
        else:
            print(f"  ✓ 커버레터 {n} 어절")
    else:
        print(f"FAIL: 커버레터가 없다({os.path.relpath(cover_p, root)})")
        fail = True

    if not fail:
        print(f"  ✓ 응답 {len(files)}건이 판정별 필수 요소를 갖추고 금지 표현이 없다")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
