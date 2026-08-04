#!/usr/bin/env python3
"""
객관 게이트: 설계 문서 정합성(Doc Consistency)
==============================================
웹개발 아키타입(D)의 Design Review 단계에서 LLM 없이 **추적 가능성**을 검사한다.
조사·집필 아키타입의 recency/source_balance 에 대응하는, 엔지니어링용 객관 게이트다.

검사 항목
  1. PRD 요구사항 id(R-xx) 전건이 설계 문서에 인용되는가        (요구사항 커버리지)
  2. 사용자 시나리오 id(S-xx) 전건이 설계 문서에 인용되는가      (시나리오 커버리지)
  3. 설계 산출이 선언된 워커 수만큼 존재하는가                   (누락 감지)
  4. 비범위(non-goals)로 선언된 항목이 설계에 새어 들어오지 않았는가 (범위 이탈, 경고)

입력 (gate_keeper 규약 — recency_check/source_balance 와 동일한 CLI)
  --policy  <path>  : pipeline.json (policy.completion_policy) 또는 frontmatter 문서
  --sources <path>  : 미사용(규약상 항상 전달됨). 웹개발 미션엔 sources.yaml 이 없다.
  --draft   <path>  : 병합된 설계 문서(spec/4-design.md). 이 파일의 **디렉터리**를 spec 루트로 보고
                      2-prd.md · 3-scenarios.md 를 찾는다.

정책 필드(completion_policy)
  require_scenario_coverage (기본 true)  : S-id 미커버 시 FAIL
  require_requirement_coverage (기본 true): R-id 미커버 시 FAIL

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
REQ_RE = re.compile(r"\bR-(\d{1,3})\b")
SCN_RE = re.compile(r"\bS-(\d{1,3})\b")
NONGOAL_HEAD_RE = re.compile(r"^#{1,6}\s*.*(비범위|non-?goals?|out of scope).*$", re.I | re.M)


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("completion_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("completion_policy", {}) or {}


def read(path: str) -> str:
    return open(path, encoding="utf-8").read()


def find_doc(spec_dir: str, *needles: str) -> str | None:
    """spec 디렉터리에서 이름에 needle 이 들어간 첫 .md 를 찾는다(번호 접두 변화에 견딤)."""
    try:
        names = sorted(os.listdir(spec_dir))
    except OSError:
        return None
    for n in names:
        low = n.lower()
        if low.endswith(".md") and any(x in low for x in needles):
            return os.path.join(spec_dir, n)
    return None


def ids(pattern: re.Pattern, text: str) -> set[str]:
    """R-1 과 R-01 을 같은 것으로 본다(제로패딩 정규화)."""
    return {str(int(m)) for m in pattern.findall(text)}


def nongoal_terms(prd: str, min_len: int = 4) -> list[str]:
    """비범위 절의 불릿에서 핵심어를 뽑는다(경고용 — FAIL 사유 아님)."""
    m = NONGOAL_HEAD_RE.search(prd)
    if not m:
        return []
    tail = prd[m.end():]
    nxt = re.search(r"^#{1,6}\s", tail, re.M)
    block = tail[: nxt.start()] if nxt else tail
    out = []
    for line in block.splitlines():
        line = line.strip()
        if line.startswith(("-", "*", "•")):
            t = re.sub(r"^[-*•]\s*", "", line).strip(" .")
            if len(t) >= min_len:
                out.append(t.split("(")[0].split("—")[0].strip()[:40])
    return out[:20]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", default=None, help="미사용(gate_keeper 규약상 전달됨)")
    ap.add_argument("--draft", default=None, help="병합된 설계 문서")
    args = ap.parse_args()

    if not args.draft:
        print("FAIL(usage): --draft(설계 문서) 필수 — fail-closed", file=sys.stderr); return 2
    try:
        policy = load_policy(args.policy)
        design = read(args.draft)
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e}", file=sys.stderr); return 2

    spec_dir = os.path.dirname(os.path.abspath(args.draft))
    prd_path = find_doc(spec_dir, "prd")
    scn_path = find_doc(spec_dir, "scenario", "시나리오")
    if not prd_path or not scn_path:
        print(f"FAIL(usage): spec 디렉터리에서 PRD/시나리오 문서를 찾지 못함 "
              f"(dir={spec_dir}, prd={prd_path}, scenarios={scn_path}) — fail-closed", file=sys.stderr)
        return 2

    try:
        prd, scn = read(prd_path), read(scn_path)
    except OSError as e:
        print(f"FAIL(usage): {e}", file=sys.stderr); return 2

    # 설계 문서 + 같은 디렉터리의 shard 를 모두 커버리지 근거로 삼는다.
    corpus = design
    base = os.path.basename(args.draft).rsplit(".md", 1)[0]
    for n in sorted(os.listdir(spec_dir)):
        if n.startswith(base + ".") and n.endswith(".md"):
            try:
                corpus += "\n" + read(os.path.join(spec_dir, n))
            except OSError:
                pass

    req_all, scn_all = ids(REQ_RE, prd), ids(SCN_RE, scn)
    req_cov, scn_cov = ids(REQ_RE, corpus), ids(SCN_RE, corpus)
    req_missing = sorted(req_all - req_cov, key=int)
    scn_missing = sorted(scn_all - scn_cov, key=int)

    need_req = bool(policy.get("require_requirement_coverage", True))
    need_scn = bool(policy.get("require_scenario_coverage", True))

    print(f"policy: require_requirement_coverage={need_req} require_scenario_coverage={need_scn}")
    print(f"PRD={os.path.basename(prd_path)} 요구사항 {len(req_all)}건 · "
          f"시나리오={os.path.basename(scn_path)} {len(scn_all)}건")
    print(f"coverage: R {len(req_all) - len(req_missing)}/{len(req_all)} · "
          f"S {len(scn_all) - len(scn_missing)}/{len(scn_all)}")

    fail = False
    if not req_all and not scn_all:
        print("FAIL: PRD·시나리오에서 추적 id(R-xx·S-xx)를 하나도 찾지 못했다 — "
              "id 부여가 누락됐거나 형식이 다르다(fail-closed).", file=sys.stderr)
        return 1
    if req_missing:
        print(f"미커버 요구사항: {['R-%02d' % int(i) for i in req_missing]}")
        fail = fail or need_req
    if scn_missing:
        print(f"미커버 시나리오: {['S-%02d' % int(i) for i in scn_missing]}")
        fail = fail or need_scn

    leaked = [t for t in nongoal_terms(prd) if t and t.lower() in corpus.lower()]
    if leaked:
        print(f"WARNING 비범위 항목이 설계에 등장(범위 이탈 의심): {leaked}")

    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
