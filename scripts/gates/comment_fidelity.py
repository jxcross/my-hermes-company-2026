#!/usr/bin/env python3
"""
객관 게이트: 코멘트 파싱 충실도 (리뷰어 원문 ↔ 파싱 목록)
==========================================================
파싱한 리뷰어 코멘트가 **원문에 실제로 있는 말인지**, 그리고 **빠뜨린 것이 없는지**를
LLM 없이 검사한다.
출처: rebuttalforge — **이 검사가 통째로 없다.** 신설.

⚠️ **커버리지 게이트의 분모를 파이프라인 자신이 정하고 있었다**(docs/13 §5 · code-docs 의
   '분모 자기결정' 과 같은 계열이되 더 위험하다):

       coverage_check.py --comments 02-comments.md --responses 04-responses/

   **인자 목록에 리뷰어 원문이 없다.** 분모(코멘트 목록)는 같은 파이프라인의 stage 2 가
   만든 것이고, 그것을 stage 4 의 응답과 대조한다. 리뷰어가 지적한 8건 중 5건만 파싱하면
   **커버리지 5/5 = 100% PASS** 다. 재심사에서 "답하지 않은 지적"이 나오는 가장 흔한 경로가
   바로 여기인데 게이트가 그 자리를 보지 않는다.

   실측: ```comments``` 블록을 비우면 `expected comments: 0 · verdict: PASS · exit=0` —
   **코멘트를 하나도 파싱하지 않으면 커버리지가 100%다**(공집합 통과 아홉 번째).

   → 원문을 직접 읽어 ① 파싱한 verbatim 이 **원문에 있는 말인가**(환각·왜곡) ② 원문의
     얼마나 많은 부분이 코멘트로 포착됐는가(**누락**) ③ 선언한 리뷰어가 전부 등장하는가를
     본다. `api_coverage` 옆에 `symbol_truth` 를 세운 것과 같은 배치다 — **둘은 짝으로만
     의미가 있다.**

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.fidelity_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : 미션 디렉터리(reports/<MID>)

기대 형식 (comments.md)
  n_comments: 6                 # 블록 길이와 대조된다(조용한 축소 방지)
  reviewers: [R1, R2]

  ```comments
  - id: R1.1
    category: major
  ```

  ## R1.1
  (리뷰어 원문 그대로)

정책 필드(fidelity_policy)
  reviews_dir (기본 _private/reviews) · comments_file (기본 _private/comments.md)
  min_comments (기본 1) · min_coverage_ratio (기본 0.4)
  require_declared_count (기본 true) · id_regex (기본 ^R\\d+\\.\\d+$)

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
DECLARED_REVIEWERS_RE = re.compile(r"^\s*reviewers\s*:\s*\[(.*?)\]\s*$", re.MULTILINE)


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("fidelity_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("fidelity_policy", {}) or {}


def mission_root(draft: str) -> str:
    p = os.path.abspath(draft)
    return p if os.path.isdir(p) else os.path.dirname(p)


def normalize(text: str) -> str:
    """대조용 정규화 — 줄바꿈·목록기호·인용부호·제목표시를 걷어내고 공백을 하나로.

    파싱하며 목록 기호를 떼는 것은 **정상**이므로 양쪽에서 똑같이 떼야 한다. 그러지 않으면
    정상 산출물을 반려하게 된다(legalforge 교훈)."""
    t = FRONTMATTER_RE.sub("", text, count=1)
    t = re.sub(r"^\s*(?:[-*>+]|\d+[.)])\s+", " ", t, flags=re.MULTILINE)
    t = re.sub(r"^#{1,6}\s*", " ", t, flags=re.MULTILINE)
    t = re.sub(r"[`*_\"'“”‘’]", "", t)
    return re.sub(r"\s+", " ", t).strip()


def verbatim_sections(text: str) -> dict[str, str]:
    """`## R1.1` 절 → 본문. 코멘트 id 마다 원문 인용을 요구한다."""
    out: dict[str, str] = {}
    parts = re.split(r"^##\s+(\S+)\s*$", text, flags=re.MULTILINE)
    for i in range(1, len(parts) - 1, 2):
        out[parts[i].strip()] = parts[i + 1]
    return out


def review_files(d: str) -> list[str]:
    if not os.path.isdir(d):
        return []
    return sorted(os.path.join(d, n) for n in os.listdir(d)
                  if n.lower().endswith((".md", ".txt")) and not n.startswith("."))


def numbered_items(text: str) -> int:
    """리뷰어 원문에서 **번호 매긴 지적**의 수. 대부분의 리뷰가 `1.` `2.` 로 항목을 나눈다.

    글자 비율(포착률)만으로는 지적 하나를 빠뜨린 것을 잡기 어렵다 — 짧은 지적을 빼면
    비율이 거의 안 움직인다. 번호가 있으면 **개수를 직접 셀 수 있다**(구조가 있는 곳에서는
    구조를 쓰고, 없으면 비율로 돌아간다)."""
    nums = [int(m.group(1)) for m in
            re.finditer(r"^\s*(\d{1,2})[.)]\s+\S", text, re.MULTILINE)]
    if not nums:
        return 0
    # `1. 2. 3.` 처럼 이어지는 것만 항목으로 본다(연도·수치 나열을 항목으로 세지 않는다)
    n = 0
    for i, v in enumerate(nums, start=1):
        if v == i:
            n = i
        else:
            break
    return n


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
    reviews_dir = os.path.join(root, policy.get("reviews_dir") or "_private/reviews")
    comments_p = os.path.join(root, policy.get("comments_file") or "_private/comments.md")

    files = review_files(reviews_dir)
    if not files:
        print(f"FAIL(usage): 리뷰어 원문을 찾지 못했다({reviews_dir}) — **원문이 없으면 "
              f"파싱이 충실한지도 무엇을 빠뜨렸는지도 알 수 없다.** fail-closed",
              file=sys.stderr)
        return 2
    try:
        ctext = open(comments_p, encoding="utf-8").read()
    except OSError:
        print(f"FAIL(usage): {comments_p} 를 읽을 수 없다 — fail-closed", file=sys.stderr)
        return 2

    mb = COMMENTS_BLOCK_RE.search(ctext)
    ids = ID_LINE_RE.findall(mb.group(1)) if mb else []
    min_comments = int(policy.get("min_comments", 1))
    if not mb:
        print("FAIL: comments.md 에 ```comments``` 블록이 없다")
        print("VERDICT: FAIL")
        return 1

    fail = False
    id_re = re.compile(policy.get("id_regex") or r"^R\d+\.\d+$")
    print(f"리뷰어 원문 {len(files)}건 · 파싱 코멘트 {len(ids)}건 (하한 {min_comments})")

    # ① 공집합 — 원본은 코멘트 0건에 커버리지 100% 를 줬다
    if len(ids) < min_comments:
        print(f"FAIL: 파싱된 코멘트 {len(ids)}건 < 하한 {min_comments} — 리뷰어 보고서가 "
              f"{len(files)}건 있는데 코멘트가 없다. **원본은 이때 '커버리지 100% PASS'** 였다")
        fail = True
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        print(f"FAIL: 코멘트 id 중복 {dup}")
        fail = True
    bad = [i for i in ids if not id_re.match(i)]
    if bad:
        print(f"FAIL: id 형식 위반 {bad} — 원본은 경고만 하고 넘어갔다(id 는 응답·"
              f"change-log·커버레터가 전부 참조하는 키다)")
        fail = True

    # ② 선언한 개수 ↔ 블록 길이 — 분모를 고정한다
    if bool(policy.get("require_declared_count", True)):
        md = DECLARED_N_RE.search(ctext)
        if not md:
            print("FAIL: comments.md 에 `n_comments:` 선언이 없다 — 블록에서 코멘트를 지우면 "
                  "회계가 내부적으로 일관해져 아무도 모른다(분모를 따로 고정하라)")
            fail = True
        elif int(md.group(1)) != len(ids):
            print(f"FAIL: `n_comments: {md.group(1)}` 인데 블록은 {len(ids)}건 — "
                  f"코멘트가 조용히 {'줄었다' if int(md.group(1)) > len(ids) else '늘었다'}")
            fail = True

    # ③ verbatim 이 원문에 실재하는가 — 환각·왜곡 차단
    raw = " ".join(normalize(open(p, encoding="utf-8").read()) for p in files)
    sections = verbatim_sections(ctext)
    matched_chars = 0
    for cid in ids:
        body = sections.get(cid)
        if body is None:
            print(f"FAIL: 코멘트 '{cid}' 의 원문 인용 절(`## {cid}`)이 없다 — 원문 없이는 "
                  f"응답이 무엇에 답하는지 검증할 수 없다")
            fail = True
            continue
        norm = normalize(body)
        if not norm:
            print(f"FAIL: 코멘트 '{cid}' 의 인용 절이 비었다")
            fail = True
            continue
        if norm in raw:
            matched_chars += len(norm)
        else:
            print(f"FAIL: 코멘트 '{cid}' 의 인용이 리뷰어 원문에 없다 — **지어냈거나 "
                  f"고쳐 적었다.** 그대로 옮겨라")
            print(f"       · 인용: {norm[:60]}…")
            fail = True

    # ④ 누락 — 원문의 얼마나 많은 부분이 코멘트로 포착됐는가
    ratio = matched_chars / len(raw) if raw else 0.0
    min_ratio = float(policy.get("min_coverage_ratio", 0.4))
    print(f"  원문 포착률 {ratio:.0%} (하한 {min_ratio:.0%}) · 원문 {len(raw)}자 중 "
          f"{matched_chars}자")
    if ratio < min_ratio:
        print(f"FAIL: 원문 포착률 {ratio:.0%} < {min_ratio:.0%} — 리뷰어가 쓴 것의 대부분이 "
              f"코멘트 목록에 들어오지 않았다. **답하지 않은 지적**이 남는다")
        fail = True

    # ⑤ 번호 매긴 지적의 수 ↔ 그 리뷰어의 코멘트 수 — 비율이 못 잡는 누락을 잡는다
    for p in files:
        stem = os.path.splitext(os.path.basename(p))[0]
        want = numbered_items(open(p, encoding="utf-8").read())
        if not want:
            continue          # 번호를 매기지 않은 리뷰는 포착률로만 본다
        got = len([i for i in ids if i.startswith(stem + ".")])
        if got < want:
            print(f"FAIL: {stem} 원문에 번호 매긴 지적이 {want}건인데 코멘트는 {got}건 — "
                  f"**빠뜨린 지적이 있다**(포착률만으로는 짧은 지적의 누락이 드러나지 않는다)")
            fail = True

    # ⑥ 선언한 리뷰어가 전부 등장하는가 — 한 명을 통째로 빠뜨리는 것을 막는다
    mr = DECLARED_REVIEWERS_RE.search(ctext)
    if mr:
        declared = [t.strip() for t in mr.group(1).split(",") if t.strip()]
        for rv in declared:
            if not any(i.startswith(rv + ".") for i in ids):
                print(f"FAIL: 리뷰어 '{rv}' 의 코멘트가 하나도 없다 — 선언 목록 대비 부재")
                fail = True
    elif len(files) > 1:
        print(f"FAIL: 리뷰어 보고서가 {len(files)}건인데 comments.md 에 `reviewers:` 선언이 "
              f"없다 — 한 명을 통째로 빠뜨려도 드러나지 않는다")
        fail = True

    if not fail:
        print(f"  ✓ 코멘트 {len(ids)}건이 전부 원문에 실재하고 포착률 {ratio:.0%}")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
