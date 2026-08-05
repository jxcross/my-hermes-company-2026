#!/usr/bin/env python3
"""
객관 게이트: 산출물 실체성(Analysis Substance)
==============================================
**병렬 샤드 산출물이 원문을 실제로 다뤘는지**를 LLM 없이 검사한다.

왜 만들었나 (docs/11 §7 ⑧ · 2026-08-05 M-2026-005)
--------------------------------------------------
stage 5 분석 11편 중 **7편이 날조**였다. `raw/` 에 원문(35KB~384KB)이 다 있는데 읽지 않고
`curated.md` 의 관련성 메모를 재서술한 뒤 본문에 이렇게 적었다:

    ### Claim 1: [Synthesized from relevance note]
    - **Evidence:** [Simulated deep analysis based on relevance impacts.]

그런데 **그 stage 의 객관 게이트 2종이 전부 통과시켰다** — `recency_check`·`source_balance`
는 `raw/sources.yaml` **메타데이터만** 읽고 산출물을 아예 열지 않기 때문이다.
LLM 검증자도 11편 중 5편만 대조하고 `VERDICT: PASS` 를 냈다.

> **객관 게이트가 검사 대상이 아닌 파일을 보고 있으면 그 stage 에는 사실상 게이트가 없다.**

이 게이트는 그 빈자리를 메운다. 두 층으로 막는다:
  ① **자가선언 탐지** — 이번 사건을 정확히 잡는다. 다만 문구는 모델마다 다르므로 이것만으로는
     부족하다(다음 모델은 다른 말로 지어낼 것이다).
  ② **구조 검사** — 개수 항등 · 분량 상하한 · 근거 불릿 하한. **문구에 의존하지 않으므로**
     모델이 바뀌어도 남는다. 이쪽이 본체다.

⚠️ **`--draft` 를 쓰지 않는다 — 의도적이다.**
   한 stage 의 객관 게이트는 `--draft` 를 **하나만 공유한다**(`gate_keeper.py:239-247`).
   이 게이트가 `analysis/` 를 요구하면 stage 의 공유 draft 가 바뀌고, 같은 stage 의
   `recency_check`·`source_balance` 가 그 경로에서 동작해야 한다 — 아키타입 S 의 stage 7·8 을
   실미션에서 `exit 2` 로 막은 것이 정확히 이 조합이다(docs/13 §5).
   `--policy` 는 항상 `reports/<MID>/pipeline.json` 이므로 그 **dirname 이 미션 루트**다.
   여기서 샤드 디렉터리를 찾으면 draft 충돌이 원천적으로 없다.

입력
  --policy  <path> : pipeline.json (정책 + 미션 루트 기준점) 또는 frontmatter .md/.yaml
  --sources <path> : sources.yaml (status=selected 개수 = 기대 샤드 수)
  --draft   <path> : 받되 **무시한다**(stage 공유 인자라 거부하면 exit 2 가 된다)

정책 필드 (`analysis_substance_policy`)
  shard_dir: analysis                 # 미션 루트 기준 상대경로
  shard_glob: "*.md"
  exclude: ["_index.md", "_*.md"]     # 병합/색인 파일은 샤드가 아니다
  min_words: 150                      # 샤드당 하한
  max_words: 20000                    # ★ 상한도 둔다(하한만 두면 폭주를 못 잡는다)
  min_evidence_bullets: 3
  require_shard_per_selected: true    # 샤드 수 == selected 수 항등
  extra_markers: []                   # 프로젝트별 추가 자가선언 문구

exit: 0 PASS · 1 FAIL · 2 usage/error(fail-closed)
"""
from __future__ import annotations
import argparse
import glob
import json
import os
import re
import sys

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML 필요", file=sys.stderr); sys.exit(2)

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)

# ── ① 자가선언 탐지 ─────────────────────────────────────────────────────────
# ⚠️ **정밀도를 위해 '괄호 안 메타 주석' 으로 좁힌다.** 맨 단어 "simulation" 을 잡으면
#    시뮬레이션 논문을 분석한 정상 산출물이 걸린다(아키타입 P 는 주제 자체가 시뮬레이션이다).
#    `[...]` 안에 들어간 것은 산문이 아니라 **작성자가 남긴 자백**이다.
BRACKET_MARKER_RE = re.compile(
    r"\[[^\]\n]{0,120}?"
    r"(?:simulat|synthesi[sz]ed\s+from|placeholder|to\s+be\s+(?:filled|determined)|"
    r"\bTBD\b|\bTODO\b|추정|가상|미확인|내용\s*없음)"
    r"[^\]\n]{0,120}?\]",
    re.IGNORECASE,
)
# 괄호 밖이어도 이 표현들은 자백이다(관용구가 아니다).
BARE_MARKER_RE = re.compile(
    r"(?:simulated\s+(?:deep\s+)?analysis|"
    r"based\s+on\s+relevance\s+(?:note|impact)|"
    r"원문을?\s*읽지\s*(?:않|못)|"
    r"관련성\s*메모\s*(?:를)?\s*(?:기반|바탕))",
    re.IGNORECASE,
)

# ── ②-d 위치 지정 인용 ──────────────────────────────────────────────────────
# ★ **이 게이트에서 가장 잘 드는 검사다.** 아키타입 B 템플릿은 stage 5 본문에서
#   *"인용 가능한 문장은 페이지/섹션까지 특정"* 하라고 요구한다. 원문을 실제로 읽으면
#   표·절·그림 번호가 자연히 따라오고, 읽지 않고 지어내면 **하나도 안 나온다.**
#
#   M-2026-005 실측(2026-08-05) — 겹치는 구간이 없다:
#     실물 3편  dhuliawala 11 · gao 71 · min 55
#     날조 8편  전부 **0**
#   ⚠️ 그중 `madaan2023` 은 **자가선언 문구가 없었다** — 분량(211w)도 하한을 넘겼다.
#      문구 탐지와 분량만 뒀으면 이 한 건은 통과했을 것이다. 지어낸 티가 안 나는 산출물을
#      가르는 것은 **템플릿이 실제로 요구한 것을 재는 검사**지 길이가 아니다.
LOCATOR_RE = re.compile(
    r"(?:Table|Figure|Fig\.|Section|Sec\.|Appendix|Eq\.|Equation)\s*\d"
    r"|§\s*\d"
    r"|\bp{1,2}\.\s*\d"
    r"|\b(?:표|그림|절|장|식)\s*\d",
    re.IGNORECASE,
)

# `source_balance.py` 와 같은 어휘를 쓴다 — 두 게이트가 다른 집합을 세면 정책이 갈라진다.
DEFAULT_EXCLUDED_STATUS = ("failed", "excluded", "rejected", "dropped", "duplicate", "skipped")

DEFAULTS = {
    "shard_dir": "analysis",
    "shard_glob": "*.md",
    "exclude": ["_index.md"],
    "min_words": 150,
    "max_words": 20000,
    "min_evidence_bullets": 3,
    # ⚠️ 기본값을 **켜 둔다**(0 이 아니다). 이 게이트를 다는 stage 는 원문 분석이 목적이고,
    #    해당 없는 아키타입은 `min_locator_citations: 0` 으로 **명시적으로** 끈다.
    #    암묵적 opt-out 은 보이지 않지만 명시적 opt-out 은 리뷰에서 보인다.
    "min_locator_citations": 2,
    "require_shard_per_selected": True,
    "extra_markers": [],
}


def load_policy(path: str) -> tuple[dict, str]:
    """(정책, 미션 루트). 미션 루트는 --policy 파일이 있는 디렉터리다."""
    text = open(path, encoding="utf-8").read()
    root = os.path.dirname(os.path.abspath(path))
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
    else:
        m = FRONTMATTER_RE.match(text)
        pol = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
        pol = pol or {}
    return (pol.get("analysis_substance_policy") or {}), root


def load_sources(path: str) -> list[dict]:
    data = yaml.safe_load(open(path, encoding="utf-8").read())
    if isinstance(data, dict):
        data = data.get("sources", [])
    return [s for s in (data or []) if isinstance(s, dict)]


def selected_ids(sources: list[dict]) -> list[str]:
    pref = DEFAULT_EXCLUDED_STATUS
    out = []
    for s in sources:
        if str(s.get("status", "selected")).strip().lower().startswith(pref):
            continue
        sid = s.get("id")
        if sid:
            out.append(str(sid))
    return out


def strip_frontmatter(text: str) -> str:
    m = FRONTMATTER_RE.match(text)
    return text[m.end():] if m else text


def word_count(text: str) -> int:
    """한국어/영어 혼용이라 공백 토큰만 세면 한국어를 과소평가한다.

    영문 토큰 + 한글 음절/2 를 더해 대략 맞춘다. 정밀할 필요는 없다 —
    1KB 짜리 껍데기와 8KB 짜리 실물을 가르는 것이 목적이다.
    """
    body = strip_frontmatter(text)
    latin = len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'\-]*", body))
    hangul = len(re.findall(r"[가-힣]", body))
    return latin + hangul // 2


def evidence_bullets(text: str, min_chars: int = 40) -> int:
    """실질 내용이 있는 불릿 수.

    ⚠️ '불릿이 있다' 가 아니라 **'불릿에 내용이 있다'** 를 센다. 날조 샤드도 불릿은
       있었다 — 다만 한 줄이 `[Simulated ...]` 였다.
    """
    n = 0
    for line in strip_frontmatter(text).splitlines():
        m = re.match(r"\s*(?:[-*+]|\d+\.)\s+(.*)$", line)
        if not m:
            continue
        content = re.sub(r"[*_`\[\]()#>]", "", m.group(1)).strip()
        if len(content) >= min_chars:
            n += 1
    return n


def find_markers(text: str, extra: list[str]) -> list[str]:
    hits = [m.group(0).strip() for m in BRACKET_MARKER_RE.finditer(text)]
    hits += [m.group(0).strip() for m in BARE_MARKER_RE.finditer(text)]
    for pat in extra:
        try:
            hits += [m.group(0).strip() for m in re.finditer(pat, text, re.IGNORECASE)]
        except re.error:
            pass
    # 중복 제거(순서 유지)
    seen, out = set(), []
    for h in hits:
        if h.lower() not in seen:
            seen.add(h.lower()); out.append(h)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", required=True)
    ap.add_argument("--draft", default=None,
                    help="stage 공유 인자 — 받되 무시한다(모듈 docstring 참조)")
    args = ap.parse_args()

    try:
        policy, root = load_policy(args.policy)
        sources = load_sources(args.sources)
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e}", file=sys.stderr); return 2

    cfg = {**DEFAULTS, **{k: v for k, v in policy.items() if v is not None}}
    shard_dir = os.path.join(root, str(cfg["shard_dir"]))
    excl = {str(x) for x in (cfg["exclude"] or [])}

    paths = sorted(
        p for p in glob.glob(os.path.join(shard_dir, str(cfg["shard_glob"])))
        if os.path.basename(p) not in excl
        and not any(re.fullmatch(e.replace("*", ".*"), os.path.basename(p)) for e in excl if "*" in e)
    )

    expected = selected_ids(sources)
    print(f"shard_dir: {os.path.relpath(shard_dir, root)}  (미션 루트 {root})")
    print(f"selected sources: {len(expected)} · shards found: {len(paths)}")

    # ⚠️ **공집합에서 PASS 하지 않는다.** `all(...)`·`not any(...)` 는 빈 목록에서 참이다 —
    #    이 저장소에서 같은 버그가 11회 반복됐다. 검사 대상이 0건이면 그 자체가 FAIL 이다.
    if not paths:
        # ⚠️ **공집합 예외를 두지 않는다 — 한 번 만들었다가 지웠다.**
        #    주기 모니터의 '조용한 회차' 를 위해 `allow_empty_when_no_sources` 를 뒀는데,
        #    `preflight_gates.py` 가 그걸 "빈 미션을 PASS 시킨다" 로 잡아냈다. 다시 보니
        #    같은 stage 의 `seen_dedup`·`recency_check` 도 빈 입력을 반려하므로 그 예외로
        #    구제되는 경우가 실제로는 없었다 — **얻는 것 없이 게이트만 약해졌다.**
        #    쓰지 않는 탈출구는 나중에 생각 없이 쓰인다.
        print(f"\n‼️ 샤드가 0건이다 ({shard_dir}) — 검사할 산출물이 없다"
              + (f" (선별 자료는 {len(expected)}건)" if expected else ""))
        print("\nverdict: FAIL")
        return 1

    failures: list[str] = []

    # ②-a 개수 항등 — "11건 선언, 4건 실물" 을 잡는다
    if cfg["require_shard_per_selected"] and expected:
        have = {os.path.splitext(os.path.basename(p))[0] for p in paths}
        missing = [i for i in expected if i not in have]
        if missing:
            failures.append(f"샤드 누락 {len(missing)}건: {missing}")

    for p in paths:
        name = os.path.basename(p)
        try:
            text = open(p, encoding="utf-8").read()
        except OSError as e:
            failures.append(f"{name}: 읽기 실패 {e}")
            continue

        # ① 자가선언
        marks = find_markers(text, list(cfg["extra_markers"] or []))
        if marks:
            failures.append(f"{name}: 자가선언 문구 {marks[:3]}")

        # ②-b 분량 — 하한과 **상한을 짝으로**
        wc = word_count(text)
        if wc < int(cfg["min_words"]):
            failures.append(f"{name}: 분량 {wc} < 하한 {cfg['min_words']}")
        elif wc > int(cfg["max_words"]):
            failures.append(f"{name}: 분량 {wc} > 상한 {cfg['max_words']} (폭주 의심)")

        # ②-c 근거 불릿
        eb = evidence_bullets(text)
        if eb < int(cfg["min_evidence_bullets"]):
            failures.append(f"{name}: 실질 불릿 {eb} < 하한 {cfg['min_evidence_bullets']}")

        # ②-d 위치 지정 인용 — 원문을 읽었는지의 가장 강한 신호
        loc_min = int(cfg["min_locator_citations"])
        loc = len(LOCATOR_RE.findall(strip_frontmatter(text)))
        if loc < loc_min:
            failures.append(
                f"{name}: 위치 지정 인용 {loc} < 하한 {loc_min} "
                "(표·절·그림·페이지 번호가 없다 = 원문 미독 신호)")

        flag = "FAIL" if any(f.startswith(name + ":") for f in failures) else "ok"
        print(f"  {name:<28} words={wc:<6} bullets={eb:<3} locators={loc:<4} {flag}")

    if failures:
        print("\nviolations:")
        for f in failures:
            print(f"  - {f}")
    print(f"\nverdict: {'PASS' if not failures else 'FAIL'}")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
