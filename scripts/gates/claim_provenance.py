#!/usr/bin/env python3
r"""
객관 게이트: 발신 콘텐츠의 주장 출처 (수치·최상급 → claim id → 원자료)
=========================================================================
공개 발신물의 **모든 수치와 최상급 표현**이 선언된 claim 에 매여 있고, 그 값이 claim 과
**일치**하며, claim 자체가 **원자료에 실재**하는지 LLM 없이 검사한다.
출처: outreachforge 의 HARD GATE(`fact_check.py`) — 이식하며 판정 방식을 바꿨다.

⚠️ **원본은 숫자를 문자열로 찾았다**(실측 · docs/13 §5):

       nums = re.findall(r"\d+(?:\.\d+)?", claim)
       return all(n in haystack for n in nums)      # haystack = source + cite-pack 전문

   지어낸 "**8배** 빠르다" 가 원자료의 `0.873` 안에 있는 `8` 로 통과한다(실측 `PASS`).
   docforge 의 '부분 문자열 검사로 커버리지 100%' 와 같은 계열이되, 여기서는 **공개되는
   수치**라 되돌릴 수 없다. → 채널의 수치는 **claim id 를 인용**해야 하고, 게이트는 그
   claim 이 말하는 **값과 같은지** 대조한다.

⚠️ **비교·최상급 주장은 단어 하나만 겹치면 통과했다**(실측):

       return any(comp.lower() in (source+cite).lower()
                  for comp in re.findall(r"\b\w+\b", claim) if len(comp) > 4)

   "Our method is the **first ever to beat human experts**" 가 원자료에 `method` 라는
   단어가 있다는 이유로 통과한다(실측 `PASS`). 최상급은 발신물에서 가장 위험한 주장인데
   가장 헐거운 검사를 받고 있었다. → 최상급 표현도 claim id 인용을 요구한다.

⚠️ **채널이 하나도 없으면 PASS** 였다(실측 — 공집합 통과 열 번째).

두 모드 (아키타입 K·P·Q·R 과 같은 방식 — 판정 첫 줄에 출력한다)
  · source — 채널이 아직 없다(수집 검증 단계). claim 이 **원자료에 실재**하는지만 본다.
  · full   — 채널까지 있다. 채널의 수치·최상급이 claim 에 매이는지까지 본다.

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.claim_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : 미션 디렉터리(reports/<MID>)

기대 형식 (source.md)
  ```evidence
  - id: e1
    grade: verified            # evidence_grade(아키타입 G 재사용)가 읽는 필드
    value: 0.873               # 채널에 쓸 수 있는 수치(게이트가 대조한다)
    locator: source/results.md
    statement: 국내 데이터에서 정확도 0.873 을 얻었다
  ```
  채널 본문에서는 `[e1]` 로 인용한다(아키타입 G 의 `evidence_grade` 와 같은 id 형식).

정책 필드(claim_policy)
  source_file (기본 _private/source.md) · channels_dir (기본 _private/channels)
  source_dir (기본 _private/source) · min_claims (기본 3)
  require_locator (기본 true) · require_value_in_source (기본 true)
  superlative_patterns · number_patterns
  citation_scope (기본 paragraph · 다른 값: file)
  ※ 인용은 **수치가 있는 문단 안**에 있어야 한다(창 방식은 옆 트윗의 인용을 끌어온다)
  ※ `citation_scope: file` — **파일 하나가 곧 의미 단위**인 산출물용(아키타입 T 의 슬라이드).
    슬라이드는 제목의 수치와 불릿의 인용이 빈 줄로 갈리지만 청중에게는 **한 화면**이다.
    문단을 단위로 삼은 이유(구조 단위로 묶는다)가 여기서는 파일을 가리킨다. 기본값은
    그대로라 아키타입 S 의 동작은 바뀌지 않는다.

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
EV_BLOCK_RE = re.compile(r"```evidence\s*\n(.*?)\n```", re.DOTALL)
ID_RE = re.compile(r"^\s*-\s*id:\s*(\S+)", re.MULTILINE)
FIELD_RE = re.compile(r"^\s+(\w+):\s*(.*)$")

# 수치 표현: 12% · 3배 · 2.4x · 1,200명 · $30K
DEFAULT_NUMBER = [
    r"\d+(?:\.\d+)?\s*(?:%|%p|퍼센트)",
    r"\d+(?:\.\d+)?\s*(?:배|x|×|fold|times)\b",
    r"[$₩]\s?\d[\d,]*(?:\.\d+)?[KMBT]?",
    r"\d+(?:\.\d+)?\s*(?:ms|s|초|분|시간|GB|MB|TB)\b",
    # ⚠️ **단위 없는 소수**(정확도 0.873 · F1 0.91)를 빠뜨리면 발신물에서 가장 흔한 수치를
    #    통째로 놓친다. 픽스처가 잡았다 — 처음에는 단위가 붙은 것만 셌다.
    r"(?<![\d.])\d+\.\d+(?![\d.])",
]
# 최상급·비교 표현 — 발신물에서 가장 위험한 주장이다
DEFAULT_SUPERLATIVE = [
    r"\b(?:first|best|fastest|smallest|largest|cheapest|only)\b",
    r"\b(?:SOTA|state-of-the-art|outperform(?:s|ed)?|beat(?:s)?)\b",
    r"최초|최고|최초로|가장\s+빠르|가장\s+정확|유일한|능가",
]


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("claim_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("claim_policy", {}) or {}


def mission_root(draft: str) -> str:
    """미션 루트 — draft 가 하위 디렉터리여도 위로 올라가 `SCOPE.md` 가 있는 곳을 찾는다.

    ⚠️ 처음에는 `draft` 가 곧 미션 루트라고 가정했다. 그런데 **한 stage 의 객관 게이트는
       `--draft` 를 하나만 공유한다**(gate_keeper). 아키타입 S 의 stage 7·8 은 같은 stage 에
       콘텐츠 기준 게이트(evidence_grade)와 미션루트 기준 게이트를 함께 뒀고 draft 가
       `_private/channels` 였다 — **실측: 이 게이트가 exit 2 로 fail-closed 되어 실미션이
       그 자리에서 막힌다**(legalforge 의 '항상 FAIL' 과 같은 계열 · docs/13 §5).
       `legal_safety` 가 쓰던 walk-up 관용구로 두 규약 모두를 받는다."""
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


def parse_claims(path: str) -> list[dict] | None:
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return None
    m = EV_BLOCK_RE.search(text)
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


def source_text(root: str, rel: str) -> str:
    """원자료 전문 — claim 의 값·위치를 대조할 대상."""
    d = os.path.join(root, rel)
    if os.path.isfile(d):
        return open(d, encoding="utf-8").read()
    if not os.path.isdir(d):
        return ""
    buf = []
    for dp, _dirs, names in os.walk(d):
        for n in sorted(names):
            if n.lower().endswith((".md", ".txt", ".csv", ".json", ".bib", ".yaml", ".yml")):
                try:
                    buf.append(open(os.path.join(dp, n), encoding="utf-8").read())
                except OSError:
                    pass
    return "\n".join(buf)


# `[e1]` 인용. 대괄호 안이라 한국어 조사에 영향받지 않는다.
# ⚠️ **아는 id 만 걸러 내면 환각 인용을 영영 못 잡는다** — 모양이 맞는 것은 전부 거둬서
#    known 과 대조해야 `[e9]` 같은 지어낸 인용이 드러난다(내가 처음 그렇게 썼고 픽스처가 잡았다).
CITE_RE = re.compile(r"\[([A-Za-z]\d+)\]")


def cited_ids(text: str) -> set[str]:
    return {m.group(1) for m in CITE_RE.finditer(text)}


def segments(text: str) -> list[tuple[int, int, set[str]]]:
    """문단(빈 줄 구분) 단위로 자르고 각 문단의 인용을 모은다.

    ⚠️ 처음에는 '수치 주변 N자' 창으로 인용을 찾았는데, X 스레드처럼 짧은 글이 이어지면
    **옆 트윗의 인용까지 창에 들어와** 출처 없는 수치가 통과했다(픽스처가 잡았다).
    인용은 **그 수치가 있는 문단 안에** 있어야 한다."""
    out = []
    pos = 0
    for part in re.split(r"\n\s*\n", text):
        start = text.find(part, pos)
        if start < 0:
            start = pos
        end = start + len(part)
        out.append((start, end, cited_ids(part)))
        pos = end
    return out


def citations_at(segs: list[tuple[int, int, set[str]]], pos: int) -> set[str]:
    for start, end, cites in segs:
        if start <= pos < end:
            return cites
    return set()


def norm_num(s: str) -> str:
    return re.sub(r"[^\d.]", "", s).rstrip(".")


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
    src_p = os.path.join(root, policy.get("source_file") or "_private/source.md")
    ch_dir = os.path.join(root, policy.get("channels_dir") or "_private/channels")
    claims = parse_claims(src_p)
    if claims is None:
        print(f"FAIL(usage): {os.path.relpath(src_p, root)} 의 ```evidence``` 블록이 없다 — "
              f"무엇을 주장으로 삼았는지 모르면 발신물의 수치를 대조할 수 없다. fail-closed",
              file=sys.stderr)
        return 2

    mode = "full" if os.path.isdir(ch_dir) else "source"
    raw = source_text(root, policy.get("source_dir") or "_private/source")
    min_claims = int(policy.get("min_claims", 3))
    num_pats = policy.get("number_patterns") or DEFAULT_NUMBER
    sup_pats = policy.get("superlative_patterns") or DEFAULT_SUPERLATIVE
    scope_unit = str(policy.get("citation_scope") or "paragraph").strip().lower()
    if scope_unit not in ("paragraph", "file"):
        print(f"FAIL(usage): 알 수 없는 citation_scope '{scope_unit}' — fail-closed",
              file=sys.stderr)
        return 2

    print(f"모드={mode} · claim {len(claims)}건 (하한 {min_claims}) · 원자료 {len(raw)}자")
    fail = False

    if len(claims) < min_claims:
        print(f"FAIL: claim {len(claims)}건 < 하한 {min_claims} — 발신할 것이 없다"
              f"(공집합 통과 방지)")
        fail = True
    ids = [c["id"] for c in claims]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        print(f"FAIL: claim id 중복 {dup}")
        fail = True

    # ① claim 이 원자료에 실재하는가 — 환각 수치 차단
    if bool(policy.get("require_locator", True)):
        if not raw:
            print(f"FAIL: 원자료를 찾지 못했다({policy.get('source_dir')}) — claim 이 실제 "
                  f"결과에서 나왔는지 대조할 수 없다")
            fail = True
        else:
            for c in claims:
                loc = str(c.get("locator", "")).strip()
                if not loc:
                    print(f"FAIL: claim '{c['id']}' 에 `locator:` 가 없다 — 어디서 나온 "
                          f"수치인지 밝히지 않은 주장이다")
                    fail = True
                    continue
                fpath = os.path.join(root, loc.split("#", 1)[0])
                if not os.path.exists(fpath):
                    print(f"FAIL: claim '{c['id']}' 의 locator '{loc}' 가 실재하지 않는다")
                    fail = True
                val = str(c.get("value", "")).strip()
                if val and bool(policy.get("require_value_in_source", True)):
                    if norm_num(val) and norm_num(val) not in re.sub(r"[,\s]", "", raw):
                        print(f"FAIL: claim '{c['id']}' 의 값 {val} 이 원자료에 없다 — "
                              f"**지어낸 수치다**(원본은 숫자 한 글자만 걸쳐도 통과시켰다)")
                        fail = True

    if mode == "source":
        if not fail:
            print(f"  ✓ claim {len(claims)}건이 전부 원자료에 실재한다"
                  f"(채널 대조는 full 모드에서 본다)")
        print("VERDICT:", "FAIL" if fail else "PASS")
        return 1 if fail else 0

    # ② 채널의 수치·최상급이 claim 에 매이는가
    files = sorted(os.path.join(ch_dir, n) for n in os.listdir(ch_dir)
                   if n.endswith(".md") and not n.startswith("."))
    if not files:
        print(f"FAIL: 채널 산출물이 하나도 없다({ch_dir}) — **원본은 이때 PASS 였다**")
        print("VERDICT: FAIL")
        return 1

    known = set(ids)
    by_id = {c["id"]: c for c in claims}
    for p in files:
        name = os.path.basename(p)
        text = re.sub(r"```.*?```", " ", open(p, encoding="utf-8").read(), flags=re.DOTALL)
        # URL 안의 숫자(arxiv id·버전)는 주장이 아니다 — 자릿수를 유지해 위치를 보존한다
        text = re.sub(r"https?://\S+", lambda m: "_" * len(m.group(0)), text)
        # 의미 단위 — 문단(기본) 또는 파일 전체(슬라이드처럼 파일 하나가 한 화면인 산출물)
        segs = ([(0, len(text), cited_ids(text))] if scope_unit == "file"
                else segments(text))
        # 환각 인용
        for cid in cited_ids(text):
            if cid not in known:
                print(f"FAIL: {name} 이 존재하지 않는 claim [{cid}] 을 인용한다")
                fail = True
        # 수치
        for pat in num_pats:
            for m in re.finditer(pat, text, re.IGNORECASE):
                near = citations_at(segs, m.start()) & known
                if not near:
                    print(f"FAIL: {name} 의 수치 '{m.group(0).strip()}' 에 claim 인용이 없다 "
                          f"— 공개되는 수치는 출처가 있어야 한다")
                    fail = True
                    continue
                want = {norm_num(str(by_id[c].get("value", ""))) for c in near}
                want.discard("")
                got = norm_num(m.group(0))
                if want and got and got not in want:
                    print(f"FAIL: {name} 의 수치 '{m.group(0).strip()}' 이 인용한 claim "
                          f"{sorted(near)} 의 값 {sorted(want)} 과 다르다 — **원본은 숫자가 "
                          f"원자료 어딘가에 문자열로 있기만 하면 통과시켰다**")
                    fail = True
        # 최상급
        for pat in sup_pats:
            for m in re.finditer(pat, text, re.IGNORECASE):
                if not (citations_at(segs, m.start()) & known):
                    print(f"FAIL: {name} 의 최상급 표현 '{m.group(0).strip()}' 에 claim "
                          f"인용이 없다 — 원본은 단어 하나만 겹쳐도 통과시켰다")
                    fail = True

    if not fail:
        print(f"  ✓ 채널 {len(files)}건의 수치·최상급이 전부 claim 에 매이고 값이 일치한다")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
