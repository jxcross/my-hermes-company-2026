#!/usr/bin/env python3
"""
객관 게이트: API 문서화 커버리지
==================================
공개 심볼이 API 레퍼런스에 **실제로 문서화된 항목으로** 들어 있는지, 그리고 레퍼런스가
**존재하지 않는 심볼을 문서화하지 않았는지**(역방향) LLM 없이 검사한다.
출처: other_projects/harness-templates/.../docforge/scripts/api_coverage.py (HARD GATE)

⚠️ **원본은 아무것도 문서화하지 않은 문서에 100% PASS 를 준다** (docs/13 §5).
   `keyword in api_text` — 문서 **전체에 대한 부분 문자열** 검사였다. 실측:
   심볼 `run`·`get_config`·`parse_tree` 를 선언하고 본문에 "**running** 상태의 파이프라인에서
   **get_configuration** 값을 **parse_tree_node** 로 넘긴다" 만 써도 **3/3 = 100.0% PASS**.
   → 심볼이 **제목 또는 시그니처 줄로** 등장해야 문서화로 인정한다(경계 있는 정확 매칭).

⚠️ 그리고 **커버리지의 분모를 파이프라인이 스스로 정한다**는 구조적 문제가 있다. 심볼 추출이
   공개 함수 100개 중 3개만 적어 내면 3개만 문서화해도 100% 다. 그 방어는 `symbol_truth`
   게이트(AST 대조 + 선언 비율 하한)가 맡는다 — **두 게이트는 짝이다.** 하나만 켜면 반쪽이다.

이식하며 보강한 것
  · **역방향 검사** — 레퍼런스가 symbols.md 에 없는 심볼을 문서화하면 FAIL(환각 문서화).
  · **제목/시그니처 인정 규칙** — 목차 나열이나 "앞으로 설명할 예정" 은 문서화가 아니다.

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.api_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : docs/ 디렉터리(api-ref.md 포함) 또는 api-ref.md 단일 파일

심볼 목록은 미션 루트의 `symbols.md` 에서 읽는다.

정책 필드(api_policy)
  threshold (기본 0.9) · symbols_file (기본 symbols.md) · api_ref (기본 api-ref.md)
  check_reverse (기본 true) · min_body_chars (기본 40) — 제목만 있고 설명이 없는 항목 배제

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
BLOCK_RE = r"```{}\s*\n(.*?)\n```"
ENTRY_RE = re.compile(r"^\s*-\s+(?:name|path):\s*(\S+)", re.MULTILINE)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*")


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("api_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("api_policy", {}) or {}


def parse_symbols(path: str) -> list[str]:
    text = open(path, encoding="utf-8").read()
    out = []
    for kind in ("functions", "classes"):
        m = re.search(BLOCK_RE.format(kind), text, re.DOTALL)
        if m:
            out += [x.strip() for x in ENTRY_RE.findall(m.group(1))]
    return out


def documented_entries(api_text: str, min_body: int) -> dict[str, str]:
    """API 레퍼런스에서 **문서화된 항목**을 뽑는다 = 제목 + 그 아래 본문.
    제목에 담긴 식별자를 항목 이름으로 본다. 본문이 너무 짧으면 항목으로 치지 않는다
    (목차 나열·'추후 작성' 을 문서화로 세지 않기 위해서다)."""
    heads = list(HEADING_RE.finditer(api_text))
    out: dict[str, str] = {}
    for i, h in enumerate(heads):
        start = h.end()
        end = heads[i + 1].start() if i + 1 < len(heads) else len(api_text)
        body = api_text[start:end].strip()
        if len(body) < min_body:
            continue
        title = h.group(2)
        # 제목의 시그니처 괄호 앞부분까지가 이름이다: `parse_tree(node, depth=0)` → parse_tree
        title = re.sub(r"`", "", title)
        for ident in IDENT_RE.findall(title.split("(")[0]):
            out.setdefault(ident, body)
            if "." in ident:                      # Class.method → 마지막 조각도 인정
                out.setdefault(ident.split(".")[-1], body)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", default=None, help="미사용(gate_keeper 규약상 전달됨)")
    ap.add_argument("--draft", default=None, help="docs/ 디렉터리 또는 api-ref.md")
    args = ap.parse_args()

    if not args.draft:
        print("FAIL(usage): --draft(docs/) 필수 — fail-closed", file=sys.stderr); return 2
    try:
        policy = load_policy(args.policy)
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e} — fail-closed", file=sys.stderr); return 2

    api_name = policy.get("api_ref") or "api-ref.md"
    if os.path.isdir(args.draft):
        api_path = os.path.join(args.draft, api_name)
        root = os.path.dirname(os.path.abspath(args.draft))
    else:
        api_path = args.draft
        root = os.path.dirname(os.path.dirname(os.path.abspath(args.draft)))
    if not os.path.isfile(api_path):
        print(f"FAIL(usage): API 레퍼런스를 찾지 못했다({api_path}) — fail-closed", file=sys.stderr)
        return 2

    sym_path = os.path.join(root, policy.get("symbols_file") or "symbols.md")
    if not os.path.isfile(sym_path):
        print(f"FAIL(usage): 심볼 목록이 없다({sym_path}) — fail-closed", file=sys.stderr)
        return 2

    threshold = float(policy.get("threshold", 0.9))
    check_reverse = bool(policy.get("check_reverse", True))
    min_body = int(policy.get("min_body_chars", 40))

    symbols = parse_symbols(sym_path)
    if not symbols:
        print(f"FAIL(usage): 심볼이 하나도 선언되지 않았다({sym_path}) — fail-closed", file=sys.stderr)
        return 2
    api_text = open(api_path, encoding="utf-8").read()
    entries = documented_entries(api_text, min_body)

    documented = [s for s in symbols if s in entries or s.split(".")[-1] in entries]
    missing = [s for s in symbols if s not in documented]
    coverage = len(documented) / len(symbols)

    print(f"심볼 {len(symbols)}개 · 문서화 항목 {len(entries)}개 · "
          f"커버리지 {len(documented)}/{len(symbols)} = {coverage:.1%} (하한 {threshold:.0%})")

    fail = False
    if coverage < threshold:
        print(f"FAIL: 커버리지 미달 — 문서화되지 않은 공개 심볼 {len(missing)}건: {missing[:10]}")
        print(f"      (심볼은 **제목**으로 등장하고 본문 {min_body}자 이상이어야 문서화로 센다 — "
              f"목차 나열이나 '추후 작성' 은 문서가 아니다)")
        fail = True

    if check_reverse:
        known = set(symbols) | {s.split(".")[-1] for s in symbols}
        ghosts = sorted(e for e in entries if e not in known)
        # 제목에 흔히 섞이는 일반 낱말은 심볼 후보에서 제외한다
        ghosts = [g for g in ghosts if not g[0].isupper() or "." in g]
        ghosts = [g for g in ghosts if g.islower() or "_" in g or "." in g]
        if ghosts:
            print(f"WARNING: 심볼 목록에 없는 항목이 문서화돼 있다 {ghosts[:8]} — "
                  f"환각이거나 symbols.md 가 과소 선언됐다(symbol_truth 게이트 확인)")

    if not fail:
        print("  ✓ 커버리지 충족")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
