#!/usr/bin/env python3
"""
객관 게이트: 다이제스트 형식·완결성
===================================
주기 실행 아키타입(E)의 산출물이 **읽을 수 있는 형태**인지 LLM 없이 검사한다.
주간 다이제스트는 매주 같은 형식이어야 비교·누적이 되므로 형식 자체가 계약이다.

검사 항목
  1. 논문 항목 수가 정책 범위(top_n) 안인가
  2. 각 항목의 id 가 후보 목록(sources.yaml)에 실재하는가 (지어낸 논문 차단)
  3. 각 항목 요약의 분량이 정책 범위 안인가 (한 줄짜리·논문 통째 붙여넣기 차단)
  4. 각 항목에 **행동 제안**이 있고 허용 라벨인가 (cite|rebut|monitor|skip|handoff)

다이제스트가 따라야 할 형식(항목마다)
    ### [arxiv:2505.01234] 논문 제목
    요약 본문 …
    **행동**: monitor — 근거 한 줄

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.monitor_policy)
  --sources <path>  : raw/sources.yaml (id 실재 확인)
  --draft   <path>  : digest.md

정책 필드(monitor_policy)
  top_n              : 항목 수 상한(기본 5). 하한은 min_items
  min_items          : 항목 수 하한(기본 1)
  summary_min_words  : 요약 최소 어절(기본 60)   ← 공백 기준이라 국문/영문 모두 적용
  summary_max_words  : 요약 최대 어절(기본 220)
  actions            : 허용 행동 라벨 목록

exit: 0 PASS · 1 FAIL · 2 usage/입력없음(fail-closed)
"""
from __future__ import annotations
import argparse
import json
import re
import sys

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML 필요", file=sys.stderr); sys.exit(2)

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
ITEM_RE = re.compile(r"^###\s+\[([^\]]+)\]\s*(.*)$", re.M)
# 라벨을 영문으로 한정하지 않고 첫 토큰을 잡는다 — 그래야 "행동 줄이 없다"와
# "행동 줄은 있는데 라벨이 틀렸다"를 구분해 집필자에게 정확히 알려줄 수 있다.
ACTION_RE = re.compile(r"\*\*행동\*\*\s*[:：]\s*(\S+)")
DEFAULT_ACTIONS = ["cite", "rebut", "monitor", "skip", "handoff"]


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("monitor_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("monitor_policy", {}) or {}


def load_ids(path: str | None) -> set[str]:
    if not path:
        return set()
    try:
        data = yaml.safe_load(open(path, encoding="utf-8").read())
    except (OSError, yaml.YAMLError):
        return set()
    if isinstance(data, dict):
        data = data.get("sources", data.get("candidates", []))
    return {str(c.get("id")) for c in (data or []) if isinstance(c, dict) and c.get("id")}


def split_items(text: str) -> list[tuple[str, str]]:
    """(id, 본문) 목록. 본문 = 다음 ### 직전까지."""
    marks = list(ITEM_RE.finditer(text))
    out = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        out.append((m.group(1).strip(), text[m.end():end]))
    return out


def word_count(body: str) -> int:
    """행동 줄을 **통째로** 뺀 요약 본문의 어절 수(공백 기준 — 국문·영문 공통).

    ⚠️ 라벨만 지우면 뒤에 붙은 근거("— 우리 보고서의 근거로 쓸 수 있다")가 요약 분량에
    합산돼, 한 줄짜리 요약도 근거를 길게 쓰면 하한을 통과한다. 행동 줄은 메타데이터이지
    요약이 아니므로 줄 단위로 제거한다."""
    lines = [l for l in body.splitlines() if "**행동**" not in l]
    text = re.sub(r"^\s*[-*>]\s*", " ", "\n".join(lines), flags=re.M)
    return len([w for w in text.split() if w.strip()])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", default=None)
    ap.add_argument("--draft", default=None, help="digest.md")
    args = ap.parse_args()

    if not args.draft:
        print("FAIL(usage): --draft(digest.md) 필수 — fail-closed", file=sys.stderr); return 2
    try:
        policy = load_policy(args.policy)
        text = open(args.draft, encoding="utf-8").read()
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e} — fail-closed", file=sys.stderr); return 2

    top_n = int(policy.get("top_n", 5) or 5)
    min_items = int(policy.get("min_items", 1) or 0)
    wmin = int(policy.get("summary_min_words", 60) or 0)
    wmax = int(policy.get("summary_max_words", 220) or 10**9)
    actions = [a.lower() for a in (policy.get("actions") or DEFAULT_ACTIONS)]
    known = load_ids(args.sources)

    items = split_items(text)
    print(f"policy: top_n={top_n} min_items={min_items} 요약 어절 {wmin}~{wmax} "
          f"actions={actions}")
    print(f"digest 항목: {len(items)}건 · 후보 id 대조군 {len(known)}건")

    fail = False
    if len(items) < min_items:
        print(f"FAIL: 항목 {len(items)}건 < 최소 {min_items}건 — 형식(`### [id] 제목`)을 "
              f"지키지 않았거나 내용이 비었다", file=sys.stderr)
        return 1
    if len(items) > top_n:
        print(f"FAIL: 항목 {len(items)}건 > top_n {top_n}")
        fail = True

    for pid, body in items:
        probs = []
        if known and pid not in known:
            probs.append(f"후보 목록에 없는 id(지어냈거나 오타)")
        wc = word_count(body)
        if wc < wmin:
            probs.append(f"요약 {wc}어절 < {wmin}")
        elif wc > wmax:
            probs.append(f"요약 {wc}어절 > {wmax}")
        m = ACTION_RE.search(body)
        if not m:
            probs.append("행동 제안 없음(`**행동**: <라벨>`)")
        elif m.group(1).lower() not in actions:
            probs.append(f"허용되지 않은 행동 라벨 '{m.group(1)}'")
        if probs:
            print(f"  - [{pid}] " + " · ".join(probs))
            fail = True

    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
