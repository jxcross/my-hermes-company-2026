#!/usr/bin/env python3
"""
객관 게이트: 코멘트 응답 커버리지
==================================
파싱된 리뷰어 코멘트 **전건**에 응답이 있는지, 그리고 그 응답이 **실체가 있는지**
LLM 없이 검사한다.
출처: rebuttalforge 의 Gate 1(`coverage_check.py`) — 이식하며 결함 2건을 고쳤다.

⚠️ **원본은 파일의 존재를 응답으로 셌다**(실측 · docs/13 §5):
   프론트매터만 있고 본문이 **한 글자도 없는** 응답 파일 2건에

       expected comments: 2 · response files: 2 · matched IDs: 2 · verdict: PASS · exit=0

   재심사에서 편집자가 보는 것은 파일의 존재가 아니라 **답변의 내용**이다.
   → 응답 본문의 분량 하한을 둔다(아키타입 Q 의 '빈 제안서' 와 같은 자리 — 상한만 재거나
     존재만 재는 게이트는 빈 산출물을 가장 안전하게 통과시킨다).

⚠️ **코멘트가 0건이면 커버리지가 100% 였다**(실측): ```comments``` 블록을 비우면
   `expected comments: 0 · PASS`. 공집합 통과 아홉 번째.
   → 하한을 두고, **분모는 `comment_fidelity` 가 리뷰어 원문과 대조한다**. 이 게이트는
     `comment_fidelity` 와 **짝으로만 의미가 있다**(`api_coverage`↔`symbol_truth` 와 같다).

이식하며 유지한 것: orphan(코멘트에 없는 응답) · duplicate(같은 id 를 주장하는 두 파일) ·
untagged(id 를 알 수 없는 파일) 검사는 원본이 이미 양방향으로 하고 있었다. 좋은 게이트다.

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.coverage_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : 미션 디렉터리(reports/<MID>)

정책 필드(coverage_policy)
  comments_file (기본 _private/comments.md) · responses_dir (기본 _private/responses)
  min_comments (기본 1) · min_response_words (기본 30)
  require_declared_count (기본 true)

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
COMMENTS_BLOCK_RE = re.compile(r"```comments\s*\n(.*?)\n```", re.DOTALL)
ID_LINE_RE = re.compile(r"^\s*-\s*id:\s*(\S+)", re.MULTILINE)
DECLARED_N_RE = re.compile(r"^\s*n_comments\s*:\s*(\d+)\s*$", re.MULTILINE)
COMMENT_ID_RE = re.compile(r"^R\d+\.\d+$")


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("coverage_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("coverage_policy", {}) or {}


def mission_root(draft: str) -> str:
    p = os.path.abspath(draft)
    return p if os.path.isdir(p) else os.path.dirname(p)


def response_id(path: str) -> str | None:
    """프론트매터의 `comment_id:` 우선, 없으면 파일명. 원본과 같은 규칙."""
    text = open(path, encoding="utf-8").read()
    m = FRONTMATTER_RE.match(text)
    if m:
        for line in m.group(1).splitlines():
            if line.startswith("comment_id:"):
                return line.split(":", 1)[1].strip()
    stem = os.path.splitext(os.path.basename(path))[0]
    return stem if COMMENT_ID_RE.match(stem) else None


def body_words(path: str) -> int:
    """프론트매터를 제외한 본문 어절 수 — **파일이 있는 것과 답한 것은 다르다**."""
    text = open(path, encoding="utf-8").read()
    body = FRONTMATTER_RE.sub("", text, count=1)
    body = re.sub(r"```.*?```", " ", body, flags=re.DOTALL)   # changes 블록은 답변이 아니다
    body = re.sub(r"[#*_>`\[\]()|-]", " ", body)
    return len([w for w in body.split() if w.strip()])


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
    comments_p = os.path.join(root, policy.get("comments_file") or "_private/comments.md")
    resp_dir = os.path.join(root, policy.get("responses_dir") or "_private/responses")

    if not os.path.isfile(comments_p):
        print(f"FAIL(usage): {comments_p} 없음 — fail-closed", file=sys.stderr); return 2
    if not os.path.isdir(resp_dir):
        print(f"FAIL(usage): 응답 디렉터리 없음({resp_dir}) — fail-closed", file=sys.stderr)
        return 2

    ctext = open(comments_p, encoding="utf-8").read()
    mb = COMMENTS_BLOCK_RE.search(ctext)
    if not mb:
        print(f"FAIL(usage): ```comments``` 블록이 없다 — fail-closed", file=sys.stderr)
        return 2
    ids = ID_LINE_RE.findall(mb.group(1))

    min_comments = int(policy.get("min_comments", 1))
    min_words = int(policy.get("min_response_words", 30))

    fail = False
    print(f"코멘트 {len(ids)}건 (하한 {min_comments}) · 응답 본문 하한 {min_words} 어절")

    if len(ids) < min_comments:
        print(f"FAIL: 코멘트 {len(ids)}건 < 하한 {min_comments} — **원본은 코멘트 0건에 "
              f"커버리지 100% PASS 를 줬다**(공집합)")
        fail = True
    if bool(policy.get("require_declared_count", True)):
        md = DECLARED_N_RE.search(ctext)
        if md and int(md.group(1)) != len(ids):
            print(f"FAIL: `n_comments: {md.group(1)}` ≠ 블록 {len(ids)}건")
            fail = True

    files = sorted(os.path.join(resp_dir, n) for n in os.listdir(resp_dir)
                   if n.endswith(".md") and not n.startswith("."))
    id_to_files: dict[str, list[str]] = {}
    untagged: list[str] = []
    for p in files:
        rid = response_id(p)
        if rid is None:
            untagged.append(os.path.basename(p))
        else:
            id_to_files.setdefault(rid, []).append(p)

    expected = set(ids)
    found = set(id_to_files)
    missing = sorted(expected - found)
    orphan = sorted(found - expected)
    dup = sorted(k for k, v in id_to_files.items() if len(v) > 1)

    if missing:
        print(f"FAIL: 응답이 없는 코멘트 {missing} — 답하지 않은 지적은 재심사에서 "
              f"가장 먼저 지적된다")
        fail = True
    if orphan:
        print(f"FAIL: 코멘트에 없는 응답 {orphan} — id 가 틀렸거나 없는 코멘트에 답했다")
        fail = True
    if dup:
        print(f"FAIL: 같은 코멘트에 응답 파일이 둘 이상 {dup}")
        fail = True
    if untagged:
        print(f"FAIL: comment_id 를 알 수 없는 응답 파일 {untagged}")
        fail = True

    # 응답의 실체 — 원본은 빈 파일도 통과시켰다
    thin = []
    for cid in sorted(expected & found):
        n = body_words(id_to_files[cid][0])
        if n < min_words:
            thin.append((cid, n))
    if thin:
        for cid, n in thin:
            print(f"FAIL: 응답 '{cid}' 의 본문이 {n} 어절 — 하한 {min_words}. "
                  f"**원본은 프론트매터만 있는 빈 파일에 '커버리지 PASS'** 를 줬다")
        fail = True

    if not fail:
        print(f"  ✓ 코멘트 {len(ids)}건 전건에 실체 있는 응답")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
