#!/usr/bin/env python3
r"""
객관 게이트: 판정 ↔ 변경기록 ↔ 원고 정합
==========================================
응답의 `verdict` 가 약속한 원고 변경이 **변경기록과 원고에 실제로 있는지**, 그리고
변경하지 않기로 한 것이 **몰래 바뀌지 않았는지** LLM 없이 검사한다.
출처: rebuttalforge 의 Gate 2(`change_consistency.py`) — 원본이 이미 양방향으로 검사하던
좋은 게이트다. 이식하며 결함 3건을 고치고 **원본 원고 대조**를 더했다.

⚠️ **"변경했다"가 태그 문자열의 존재로만 증명됐다**(실측 · docs/13 §5):
   인자 목록이 `--responses --revised --change-log` 뿐이다 — **원본 원고를 받는 통로가 없다.**
   그래서 원고를 **한 글자도 고치지 않고** `[CHANGE-R1.1: 실험 추가]` 태그만 붙여 넣으면

       change-log entries: 2 · revised-manuscript change tags: 2 · verdict: PASS

   agentforge 의 죽은 gold-set 대조와 같은 계열이다("A 를 B 와 대조한다"고 하면 **B 를 받을
   통로가 있는지 인자 목록부터 보라"). → 원본 원고를 읽어 **태그가 붙은 자리가 실제로
   달라졌는지** 대조한다. 파일 읽기는 코드 실행이 아니므로 게이트가 해도 안전하다.

⚠️ **정상 산출물을 반려하는 결함 2건**(둘 다 실측 — legalforge 계열):
   1. 변경기록을 **마크다운 목록**으로 쓰면(`- R1.1: 3.2절에 실험 추가`) 정규식
      `^\s*(R\d+\.\d+):\s` 가 `-` 를 넘지 못해 **항목 0건**으로 읽고 전건 FAIL 한다.
   2. 원본 CLAUDE.md 가 문서화한 태그 형식은 `[CHANGE-r1: ...]` 인데 게이트가 찾는 것은
      `[CHANGE-R1.1:` 이다. **문서를 따르면 게이트가 막는다**(실측: 태그 0건 · FAIL).
   → 목록 기호를 허용하고, 태그 형식을 정책으로 못박아 템플릿 본문과 한 곳에서 관리한다.

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.change_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : 미션 디렉터리(reports/<MID>)

기대 형식
  responses/<id>.md   frontmatter: comment_id · verdict
  change-log.md       `- R1.1: 3.2절에 검증 실험을 추가했다` (목록 기호 있어도 없어도 된다)
  revised-ms.md       변경 지점마다 `[CHANGE-R1.1: 무엇을 바꿨는지]`

정책 필드(change_policy)
  responses_dir (기본 _private/responses) · revised_file (기본 _private/revised-ms.md)
  change_log (기본 _private/change-log.md) · original_file (기본 _private/original-ms.md)
  verdicts_change (기본 [accept, partially-accept])
  verdicts_nochange (기본 [rebut, clarification-only])
  require_original_diff (기본 true) — 태그 자리가 실제로 달라졌는지 원본과 대조

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
# ⚠️ 목록 기호(`- `·`* `·`1. `)를 허용한다 — 원본은 이것 때문에 정상 변경기록을 0건으로 읽었다
LOG_LINE_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)?(R\d+\.\d+)\s*[:：]\s*(\S.*)$")


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("change_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("change_policy", {}) or {}


def mission_root(draft: str) -> str:
    p = os.path.abspath(draft)
    return p if os.path.isdir(p) else os.path.dirname(p)


def frontmatter(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    out: dict = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.lstrip().partition(":")
            out[k.strip()] = v.strip()
    return out


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def strip_tags(text: str, tag_re: re.Pattern) -> str:
    return tag_re.sub("", text)


def paragraphs(text: str) -> list[str]:
    return [p for p in re.split(r"\n\s*\n", text) if p.strip()]


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
    revised_p = os.path.join(root, policy.get("revised_file") or "_private/revised-ms.md")
    log_p = os.path.join(root, policy.get("change_log") or "_private/change-log.md")
    orig_p = os.path.join(root, policy.get("original_file") or "_private/original-ms.md")

    for p, label in ((resp_dir, "응답 디렉터리"), (revised_p, "수정 원고"), (log_p, "변경기록")):
        if not os.path.exists(p):
            print(f"FAIL(usage): {label}가 없다({p}) — fail-closed", file=sys.stderr)
            return 2

    verdicts_change = set(policy.get("verdicts_change") or ["accept", "partially-accept"])
    verdicts_nochange = set(policy.get("verdicts_nochange") or ["rebut", "clarification-only"])
    tag_re = re.compile(r"\[CHANGE-(R\d+\.\d+)\s*:[^\]]*\]")

    files = sorted(os.path.join(resp_dir, n) for n in os.listdir(resp_dir)
                   if n.endswith(".md") and not n.startswith("."))
    if not files:
        print(f"FAIL(usage): 응답이 한 건도 없다({resp_dir}) — 검사할 것이 없다는 것은 "
              f"통과가 아니다. fail-closed", file=sys.stderr)
        return 2

    verdicts: dict[str, str] = {}
    fail = False
    for p in files:
        fm = frontmatter(p)
        stem = os.path.splitext(os.path.basename(p))[0]
        cid = fm.get("comment_id") or (stem if COMMENT_ID_RE.match(stem) else None)
        if not cid:
            print(f"FAIL: {os.path.basename(p)} 의 comment_id 를 알 수 없다 — 원본은 "
                  f"경고만 하고 **집계에서 뺐다**(빠진 것은 검사되지 않는다)")
            fail = True
            continue
        verdicts[cid] = fm.get("verdict", "").strip()

    log_text = open(log_p, encoding="utf-8").read()
    log_ids: set[str] = set()
    for line in log_text.splitlines():
        m = LOG_LINE_RE.match(line)
        if m:
            log_ids.add(m.group(1))

    revised_text = open(revised_p, encoding="utf-8").read()
    tag_ids = set(tag_re.findall(revised_text))

    print(f"응답 {len(verdicts)}건 · 변경기록 {len(log_ids)}건 · 원고 태그 {len(tag_ids)}종")

    for cid, verdict in sorted(verdicts.items()):
        if verdict in verdicts_change:
            if cid not in log_ids:
                print(f"FAIL: {cid} 의 판정이 '{verdict}' 인데 변경기록에 항목이 없다")
                fail = True
            if cid not in tag_ids:
                print(f"FAIL: {cid} 의 판정이 '{verdict}' 인데 원고에 "
                      f"`[CHANGE-{cid}: …]` 표시가 없다")
                fail = True
        elif verdict in verdicts_nochange:
            if cid in log_ids:
                print(f"FAIL: {cid} 의 판정이 '{verdict}'(변경 없음)인데 변경기록에 항목이 "
                      f"있다 — 반박한다고 해 놓고 조용히 고쳤다")
                fail = True
            if cid in tag_ids:
                print(f"FAIL: {cid} 의 판정이 '{verdict}' 인데 원고에 변경 표시가 있다")
                fail = True
        elif verdict:
            print(f"FAIL: {cid} 의 판정 '{verdict}' 이 허용값 "
                  f"{sorted(verdicts_change | verdicts_nochange)} 밖이다")
            fail = True
        else:
            print(f"FAIL: {cid} 에 `verdict:` 가 없다")
            fail = True

    for cid in sorted(log_ids - set(verdicts)):
        print(f"FAIL: 변경기록에 {cid} 항목이 있는데 대응하는 응답이 없다 — "
              f"**모든 변경은 리뷰어 코멘트로 소급돼야 한다**")
        fail = True
    for cid in sorted(tag_ids - set(verdicts)):
        print(f"FAIL: 원고에 `[CHANGE-{cid}: …]` 가 있는데 대응하는 응답이 없다")
        fail = True

    # ── 원본 대조: 태그가 붙은 자리가 **실제로** 달라졌는가 ──────────────────
    if bool(policy.get("require_original_diff", True)):
        if not os.path.isfile(orig_p):
            print(f"FAIL: 원본 원고가 없다({os.path.relpath(orig_p, root)}) — 원본이 없으면 "
                  f"'바꿨다'는 주장을 **태그 문자열의 존재로만** 확인하게 된다"
                  f"(원본 게이트가 정확히 그랬다)")
            fail = True
        else:
            orig_text = open(orig_p, encoding="utf-8").read()
            orig_norm = normalize(orig_text)
            if normalize(strip_tags(revised_text, tag_re)) == orig_norm:
                print("FAIL: 수정 원고가 원본과 **글자 하나 다르지 않다** — 태그만 붙었다. "
                      "실측으로 확인한 원본 게이트의 구멍이 바로 이 경우다")
                fail = True
            else:
                unchanged = []
                for cid, verdict in sorted(verdicts.items()):
                    if verdict not in verdicts_change or cid not in tag_ids:
                        continue
                    sites = [para for para in paragraphs(revised_text)
                             if re.search(rf"\[CHANGE-{re.escape(cid)}\s*:", para)]
                    changed_here = False
                    for para in sites:
                        body = normalize(strip_tags(para, tag_re))
                        if not body or body not in orig_norm:
                            changed_here = True
                            break
                    if sites and not changed_here:
                        unchanged.append(cid)
                if unchanged:
                    print(f"FAIL: {unchanged} 의 변경 표시가 붙은 문단이 원본과 동일하다 — "
                          f"표시만 달고 내용을 바꾸지 않았다(변경 지점에 표시를 붙이는 것이 "
                          f"규약이다)")
                    fail = True

    if not fail:
        print(f"  ✓ 판정 {len(verdicts)}건이 변경기록·원고 표시와 정합하고 "
              f"표시 지점이 원본과 실제로 다르다")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
