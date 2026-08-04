#!/usr/bin/env python3
"""
객관 게이트: 평가셋(gold set) 품질
====================================
평가셋 `eval-set.jsonl` 이 **측정 도구로서 쓸 만한지** LLM 없이 검사한다 —
항목 수 · 난이도 분포 · 카테고리 커버리지 · 정답 충실도 · **gold_context 의 실재**.

⚠️ **원본에는 이 게이트의 스크립트가 없다. 신설이다** (docs/13 §5).
   agentforge 의 GATE 1(eval set quality)은 `agentforge-eval-quality-check` 라는
   **LLM 크리틱 하나**가 전부다. 나머지 두 게이트(통계·재현성)는 파이썬 스크립트로
   만들어 두고 **가장 앞단의, 모든 수치의 분모가 되는 평가셋만 LLM 판단에 맡겼다.**
   평가셋이 부실하면 뒤의 통계·재현성 게이트는 **부실한 측정을 정밀하게 재는 일**이 된다.
   우리 규약은 이중 게이트(객관 Python + LLM 검증자)이므로 객관 쪽을 만들었다.

⚠️ **환각 gold_context 를 실제로 막는다.** 원본 CLAUDE.md 는
   "Every bibkey in eval items MUST trace to a chunk in `corpus/processed/`" ·
   "Never invent a gold context" 라고 **선언**하지만 이를 검사하는 코드는 없다
   (docforge 의 '환각 금지' 선언과 같은 계열 — docs/13 §5). 여기서는
   `_private/corpus/chunks.jsonl` 의 실제 chunk id 와 대조한다. 대조할 파일이 없으면
   **fail-closed** 다 — "확인할 데이터가 없다"는 "문제가 없다"가 아니다.

⚠️ **분량은 어절이 아니라 글자로 잰다.** 국문 정답 "설정 파일을 고친다"는 4어절이지만
   영문 기준 단어 하한(예 5 words)에 걸려 반려된다(policy-brief 에서 겪은 한국어 함정의
   같은 얼굴 — docs/13 §5).

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.eval_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : eval-set.jsonl 또는 그것을 담은 미션 디렉터리

정책 필드(eval_policy)
  min_items (기본 50) · difficulty_targets (기본 easy .30 / medium .40 / hard .30)
  difficulty_tolerance (기본 0.10) · min_categories (기본 3) · min_items_per_category (기본 3)
  min_question_chars (기본 6) · min_answer_chars (기본 4)
  require_grounding (기본 true) — gold_context 를 corpus chunk 와 대조
  chunks_file (기본 _private/corpus/chunks.jsonl)

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

DEFAULT_TARGETS = {"easy": 0.30, "medium": 0.40, "hard": 0.30}
# 국문 표기도 받는다 — 라벨이 한국어라고 분포 검사가 무력해지면 안 된다.
DIFFICULTY_ALIASES = {
    "easy": "easy", "쉬움": "easy", "하": "easy", "low": "easy",
    "medium": "medium", "med": "medium", "보통": "medium", "중": "medium", "mid": "medium",
    "hard": "hard", "어려움": "hard", "상": "hard", "high": "hard", "difficult": "hard",
}
DEFAULT_CHUNKS = os.path.join("_private", "corpus", "chunks.jsonl")


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("eval_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("eval_policy", {}) or {}


def find_eval_set(draft: str) -> tuple[str | None, str | None]:
    """(eval-set.jsonl 경로, 미션 루트) 반환."""
    if os.path.isfile(draft):
        return draft, os.path.dirname(os.path.abspath(draft))
    if os.path.isdir(draft):
        for name in ("eval-set.jsonl", "05-eval-set.jsonl"):
            p = os.path.join(draft, name)
            if os.path.isfile(p):
                return p, os.path.abspath(draft)
    return None, None


def load_items(path: str) -> tuple[list[dict], list[str]]:
    """(항목, 파싱오류) — 깨진 줄을 조용히 건너뛰면 분모가 줄어든다."""
    items, errs = [], []
    for i, line in enumerate(open(path, encoding="utf-8"), 1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            errs.append(f"{i}행 JSON 파싱 실패: {e}")
            continue
        if not isinstance(obj, dict):
            errs.append(f"{i}행이 객체가 아니다")
            continue
        items.append(obj)
    return items, errs


def load_chunk_ids(path: str) -> set[str] | None:
    if not os.path.isfile(path):
        return None
    ids: set[str] = set()
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        cid = obj.get("id") or obj.get("chunk_id")
        if cid:
            ids.add(str(cid))
    return ids


def norm_difficulty(v) -> str | None:
    return DIFFICULTY_ALIASES.get(str(v).strip().lower()) if v is not None else None


def norm_question(q: str) -> str:
    """중복 판정용 정규화 — 공백·문장부호 차이는 다른 질문이 아니다."""
    return re.sub(r"[\s\W_]+", "", str(q)).lower()


def gold_contexts(item: dict) -> list[str]:
    v = item.get("gold_context", item.get("gold_contexts"))
    if v is None:
        return []
    if isinstance(v, str):
        return [v]
    return [str(x) for x in v] if isinstance(v, list) else []


def main() -> int:  # noqa: C901  검사 항목이 많아 분기가 길다
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", default=None, help="미사용(gate_keeper 규약상 전달됨)")
    ap.add_argument("--draft", default=None, help="eval-set.jsonl 또는 미션 디렉터리")
    args = ap.parse_args()

    if not args.draft:
        print("FAIL(usage): --draft 필수 — fail-closed", file=sys.stderr); return 2
    try:
        policy = load_policy(args.policy)
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e} — fail-closed", file=sys.stderr); return 2

    path, root = find_eval_set(args.draft)
    if not path:
        print(f"FAIL(usage): eval-set.jsonl 을 찾지 못했다({args.draft}) — 평가셋 없이 "
              f"평가 결과를 논할 수 없다. fail-closed", file=sys.stderr)
        return 2

    items, parse_errs = load_items(path)
    min_items = int(policy.get("min_items", 50))
    targets = policy.get("difficulty_targets") or DEFAULT_TARGETS
    tol = float(policy.get("difficulty_tolerance", 0.10))
    min_cats = int(policy.get("min_categories", 3))
    min_per_cat = int(policy.get("min_items_per_category", 3))
    min_q = int(policy.get("min_question_chars", 6))
    min_a = int(policy.get("min_answer_chars", 4))
    require_grounding = bool(policy.get("require_grounding", True))
    chunks_rel = policy.get("chunks_file") or DEFAULT_CHUNKS

    fail = False
    print(f"평가셋 {os.path.basename(path)} · 항목 {len(items)}건 (하한 {min_items})")

    if parse_errs:
        print(f"FAIL: 깨진 줄 {len(parse_errs)}건 — 조용히 건너뛰면 분모가 줄어 모든 비율이 "
              f"부풀려진다")
        for e in parse_errs[:5]:
            print(f"       · {e}")
        fail = True

    # ① 규모
    if len(items) < min_items:
        print(f"FAIL: 항목 {len(items)}건 < 하한 {min_items} — 표본이 작으면 뒤의 통계 게이트가 "
              f"무엇을 재든 신뢰구간이 무의미해진다")
        fail = True

    # ② id 유일성 — 중복 id 는 paired 비교에서 조용히 덮어쓴다
    ids = [str(it.get("id", "")).strip() for it in items]
    missing_id = [i for i, v in enumerate(ids, 1) if not v]
    if missing_id:
        print(f"FAIL: id 없는 항목 {len(missing_id)}건(행 {missing_id[:5]}) — "
              f"paired 통계는 id 로 짝을 맞춘다")
        fail = True
    dup_ids = sorted({v for v in ids if v and ids.count(v) > 1})
    if dup_ids:
        print(f"FAIL: 중복 id {dup_ids[:5]} — 채점 시 뒤 항목이 앞 항목을 덮어쓴다")
        fail = True

    # ③ 질문·정답 충실도 (글자 기준 — 국문 어절 기준이 아니다)
    thin_q, thin_a = [], []
    for it in items:
        if len(str(it.get("question", "")).strip()) < min_q:
            thin_q.append(it.get("id", "?"))
        if len(str(it.get("gold_answer", it.get("answer", ""))).strip()) < min_a:
            thin_a.append(it.get("id", "?"))
    if thin_q:
        print(f"FAIL: 질문이 비었거나 {min_q}자 미만인 항목 {len(thin_q)}건 {thin_q[:5]}")
        fail = True
    if thin_a:
        print(f"FAIL: gold_answer 가 비었거나 {min_a}자 미만인 항목 {len(thin_a)}건 "
              f"{thin_a[:5]} — 정답 없는 문항은 채점할 수 없다")
        fail = True

    # ④ 질문 중복 — 같은 질문을 여러 번 넣어 항목 수 하한을 채우는 것을 막는다
    seen: dict[str, str] = {}
    dup_q = []
    for it in items:
        k = norm_question(it.get("question", ""))
        if not k:
            continue
        if k in seen:
            dup_q.append((seen[k], it.get("id", "?")))
        else:
            seen[k] = str(it.get("id", "?"))
    if dup_q:
        print(f"FAIL: 사실상 같은 질문 {len(dup_q)}쌍 {dup_q[:3]} — 중복으로 항목 수를 채우면 "
              f"규모 하한이 아무것도 보장하지 않는다")
        fail = True

    # ⑤ 난이도 분포
    counts: dict[str, int] = {}
    unknown = []
    for it in items:
        d = norm_difficulty(it.get("difficulty"))
        if d is None:
            unknown.append(it.get("id", "?"))
        else:
            counts[d] = counts.get(d, 0) + 1
    if unknown:
        print(f"FAIL: difficulty 가 없거나 알 수 없는 항목 {len(unknown)}건 {unknown[:5]} "
              f"— 분류되지 않은 항목은 분포 검사에서 빠진다(인정 표기: easy/medium/hard·쉬움/보통/어려움)")
        fail = True
    n = len(items)
    if n:
        for label, target in targets.items():
            lab = norm_difficulty(label) or label
            ratio = counts.get(lab, 0) / n
            lo, hi = float(target) - tol, float(target) + tol
            mark = "✓" if lo <= ratio <= hi else "✗"
            print(f"  난이도 {lab:6s}: {counts.get(lab, 0):3d}건 {ratio:5.1%} "
                  f"(목표 {float(target):.0%} ±{tol:.0%}) {mark}")
            if not (lo <= ratio <= hi):
                print(f"FAIL: 난이도 {lab} 비율 {ratio:.1%} 이 목표 범위 밖 — 쉬운 문항만 모으면 "
                      f"어떤 시스템도 잘해 보이고, 어려운 문항만 모으면 개선이 묻힌다")
                fail = True

    # ⑥ 카테고리 커버리지
    cats: dict[str, int] = {}
    for it in items:
        c = str(it.get("category", "")).strip()
        if c:
            cats[c] = cats.get(c, 0) + 1
    no_cat = sum(1 for it in items if not str(it.get("category", "")).strip())
    if no_cat:
        print(f"FAIL: category 없는 항목 {no_cat}건 — 커버리지의 분모가 흔들린다")
        fail = True
    print(f"  카테고리 {len(cats)}종 (하한 {min_cats}): "
          f"{', '.join(f'{k}={v}' for k, v in sorted(cats.items())[:8])}")
    if len(cats) < min_cats:
        print(f"FAIL: 카테고리 {len(cats)}종 < 하한 {min_cats} — 한 종류의 질문만으로는 "
              f"시스템의 어느 축이 좋아졌는지 말할 수 없다")
        fail = True
    thin_cats = {k: v for k, v in cats.items() if v < min_per_cat}
    if thin_cats:
        print(f"FAIL: 항목 {min_per_cat}건 미만인 카테고리 {thin_cats} — 카테고리 수만 채운 것이다")
        fail = True

    # ⑦ gold_context 실재 대조 — 원본이 '선언'만 하고 검사하지 않던 것
    if require_grounding:
        chunks_path = chunks_rel if os.path.isabs(chunks_rel) else os.path.join(root or "", chunks_rel)
        chunk_ids = load_chunk_ids(chunks_path)
        if chunk_ids is None:
            print(f"FAIL(usage): corpus chunk 목록을 찾지 못했다({chunks_path}) — gold_context 의 "
                  f"실재를 확인할 수 없다. 확인할 데이터가 없는 것은 문제가 없는 것이 아니다. "
                  f"fail-closed", file=sys.stderr)
            return 2
        no_ctx, halluc = [], []
        for it in items:
            gc = gold_contexts(it)
            if not gc:
                no_ctx.append(it.get("id", "?"))
                continue
            bad = [c for c in gc if c not in chunk_ids]
            if bad:
                halluc.append((it.get("id", "?"), bad[:2]))
        print(f"  corpus chunk {len(chunk_ids)}개와 대조 · gold_context 미기재 {len(no_ctx)} · "
              f"실재하지 않는 참조 {len(halluc)}")
        if no_ctx:
            print(f"FAIL: gold_context 가 없는 항목 {len(no_ctx)}건 {no_ctx[:5]} — 근거 없는 "
                  f"정답은 검색 성능을 재지 못한다")
            fail = True
        if halluc:
            print(f"FAIL: corpus 에 없는 chunk 를 가리키는 항목 {len(halluc)}건 {halluc[:3]} — "
                  f"**환각 gold_context**. 원본은 이것을 지시로만 금지하고 검사하지 않았다")
            fail = True

    if not fail:
        print("  ✓ 규모·분포·커버리지·정답 충실도·근거 실재 모두 충족")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
