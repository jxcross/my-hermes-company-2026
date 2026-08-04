#!/usr/bin/env python3
"""
객관 게이트: 신규성(중복 미검출)
================================
주기 실행 아키타입(E — 문헌 모니터)의 수집 산출이 **이번 회차의 신규분만** 담고 있는지 검사한다.
같은 논문을 매주 다시 보고하면 모니터의 존재 이유가 사라지므로, 멱등성은 이 아키타입의
핵심 계약이고 따라서 객관 게이트 대상이다.

검사 항목
  1. 후보 중 이미 본 것(`monitors/<id>/_seen.tsv`)이 섞이지 않았는가
  2. 모든 후보에 `id`가 있고 형식이 `<source>:<key>` 인가 (seen 추적의 전제)
  3. 후보 수가 0이 아닌가 (수집 실패를 '신규 없음'으로 오인하지 않기 위해)
  4. 후보 id 가 중복되지 않는가 (워커 간 병합 실패 감지)

monitor_id 해석 순서
  ① 미션 SCOPE.md frontmatter 의 `monitor_id`  ② policy.monitor_policy.monitor_id  ③ 실패 시 fail-closed
  (미션 루트 = --draft 의 두 단계 상위. 예: reports/<MID>/raw/sources.yaml → reports/<MID>)

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.monitor_policy)
  --sources <path>  : 미사용(규약상 전달됨 — 판정 대상은 --draft 로 받는다)
  --draft   <path>  : 병합된 후보 목록(raw/sources.yaml)

정책 필드(monitor_policy)
  monitor_id            : 기본 monitor_id(SCOPE.md 가 우선)
  allow_seen_overlap    : true 면 중복을 경고로만(기본 false)
  min_candidates        : 최소 후보 수(기본 1). 0 이면 '신규 없음' 허용

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

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
ID_RE = re.compile(r"^[a-z][a-z0-9_\-]*:[A-Za-z0-9._\-/]+$")


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("monitor_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("monitor_policy", {}) or {}


def load_candidates(path: str) -> list[dict]:
    data = yaml.safe_load(open(path, encoding="utf-8").read())
    if isinstance(data, dict):
        data = data.get("sources", data.get("candidates", []))
    return [c for c in (data or []) if isinstance(c, dict)]


def scope_monitor_id(mission_root: str) -> str | None:
    p = os.path.join(mission_root, "SCOPE.md")
    try:
        m = FRONTMATTER_RE.match(open(p, encoding="utf-8").read())
    except OSError:
        return None
    if not m:
        return None
    d = yaml.safe_load(m.group(1)) or {}
    v = d.get("monitor_id")
    return str(v) if v else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", default=None, help="미사용(gate_keeper 규약상 전달됨)")
    ap.add_argument("--draft", default=None, help="병합된 후보 목록(raw/sources.yaml)")
    args = ap.parse_args()

    if not args.draft:
        print("FAIL(usage): --draft(후보 목록) 필수 — fail-closed", file=sys.stderr); return 2
    try:
        policy = load_policy(args.policy)
        cands = load_candidates(args.draft)
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e} — fail-closed", file=sys.stderr); return 2

    mission_root = os.path.dirname(os.path.dirname(os.path.abspath(args.draft)))
    monitor_id = scope_monitor_id(mission_root) or policy.get("monitor_id")
    if not monitor_id:
        print("FAIL(usage): monitor_id 를 찾지 못했다 — SCOPE.md frontmatter 나 "
              "policy.monitor_policy.monitor_id 에 선언하라(fail-closed).", file=sys.stderr)
        return 2

    from monitor_state import load_seen  # noqa: E402  (경로 주입 후 import)
    seen = load_seen(monitor_id)

    allow_overlap = bool(policy.get("allow_seen_overlap", False))
    min_c = int(policy.get("min_candidates", 1) or 0)

    print(f"monitor={monitor_id} · seen={len(seen)}건 · 후보={len(cands)}건 "
          f"(allow_overlap={allow_overlap} min_candidates={min_c})")

    fail = False
    if len(cands) < min_c:
        print(f"FAIL: 후보 {len(cands)}건 < 최소 {min_c}건 — 수집 실패를 '신규 없음'으로 "
              f"오인하지 않도록 fail 한다.", file=sys.stderr)
        fail = True

    ids = [str(c.get("id") or "") for c in cands]
    missing = [i for i, c in enumerate(cands) if not c.get("id")]
    if missing:
        print(f"FAIL: id 없는 후보 {len(missing)}건(인덱스 {missing[:10]}) — seen 추적 불가")
        fail = True

    malformed = [i for i in ids if i and not ID_RE.match(i)]
    if malformed:
        print(f"FAIL: id 형식 위반(<source>:<key> 이어야 함) {len(malformed)}건: {malformed[:5]}")
        fail = True

    dup = sorted({i for i in ids if i and ids.count(i) > 1})
    if dup:
        print(f"FAIL: 후보 내 중복 id {len(dup)}건: {dup[:5]} — 워커 산출 병합이 dedup 되지 않았다")
        fail = True

    overlap = sorted({i for i in ids if i in seen})
    if overlap:
        msg = (f"이미 본 논문 {len(overlap)}건이 후보에 섞였다: {overlap[:5]}"
               f"{' …' if len(overlap) > 5 else ''}")
        if allow_overlap:
            print(f"WARNING: {msg}")
        else:
            print(f"FAIL: {msg} — 수집 단계가 _seen.tsv 대비 dedup 해야 한다")
            fail = True

    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
