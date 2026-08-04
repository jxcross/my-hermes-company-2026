#!/usr/bin/env python3
"""
객관 게이트: 보안 발견의 완결성
=================================
발견된 취약점마다 **위치·근거·영향·조치**가 적혀 있는지, 그리고 **신고한 건수가 실제 목록과
맞는지** LLM 없이 검사한다.
출처: other_projects/harness-templates/.../secforge/scripts/severity_check.py (GATE 1) —
      **판정 방향을 뒤집어 이식했다.** 아래 이유 참조.

⚠️ **원본의 하드게이트는 "Critical/High = 0 건" 이다. 이것은 감사 도구에서 거꾸로다**
   (docs/13 §5). secforge 는 스스로 report-only(자동 수정 없음)라고 선언한다. 그런데
   **취약점을 찾을수록 게이트가 FAIL 이 되어 보고서가 finalize 되지 않는다.**
   심각한 취약점을 발견했을 때야말로 보고서가 가장 빨리 사람에게 가야 하는데, 바로 그때
   파이프라인이 막힌다. 게이트가 **발견을 벌한다.**

   → 우리는 "몇 건이냐"가 아니라 **"보고가 조치 가능한가"** 를 잡는다. Critical/High 발견마다
     위치·근거·영향·조치가 있어야 한다. 몇 건이 나왔는지에 대한 판단은 Sam 의 몫이다
     (릴리스 게이트로 쓰고 싶은 팀을 위해 `max_critical`·`max_high` 를 정책으로 남겨 뒀지만
     **기본값은 무제한**이다).

⚠️ 원본의 두 번째 결함: **자기 신고 숫자만 봤다.** `n_critical:` / `n_high:` 줄만 읽으므로
   목록에 Critical 5건을 적어 놓고 `n_critical: 0` 이라고 쓰면 통과한다. 게다가 `parse_int` 는
   키가 없으면 0 을 돌려주므로 **보고서가 깨져 있어도 PASS**(fail-open)다.
   → 선언 수치와 실제 목록을 **대조**하고, 목록이 없으면 fail-closed 한다.

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.finding_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : findings.md(```findings``` 블록) 또는 그 문서를 담은 디렉터리

기대 형식
  n_critical: 0
  n_high: 1

  ```findings
  - id: f1
    title: SQL 인젝션 가능성
    severity: high
    category: A03
    location: src/db/query.py:88
    evidence: 사용자 입력을 문자열 포매팅으로 쿼리에 결합
    impact: 인증 우회 및 전체 테이블 유출 가능
    remediation: 파라미터 바인딩으로 교체
  ```

정책 필드(finding_policy)
  require_fields (기본 [location, evidence, impact, remediation])
  strict_severities (기본 [critical, high]) — 위 필드를 강제할 등급
  max_critical · max_high (기본 null = 무제한 · 릴리스 게이트로 쓸 때만 설정)
  min_field_chars (기본 5)

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
FINDINGS_BLOCK_RE = re.compile(r"```findings\s*\n(.*?)\n```", re.DOTALL)
DEFAULT_FIELDS = ["location", "evidence", "impact", "remediation"]
DEFAULT_STRICT = ["critical", "high"]
SEVERITIES = ["critical", "high", "medium", "low", "info"]


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("finding_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("finding_policy", {}) or {}


def parse_findings(block: str) -> list[dict]:
    items, current = [], None
    for line in block.splitlines():
        mi = re.match(r"^\s*-\s+id:\s*(\S+)", line)
        if mi:
            if current:
                items.append(current)
            current = {"id": mi.group(1).strip()}
            continue
        if current is None:
            continue
        mf = re.match(r"^\s+(\w+):\s*(.*)$", line)
        if mf:
            current[mf.group(1)] = mf.group(2).strip().strip('"\'')
    if current:
        items.append(current)
    return items


def int_field(text: str, key: str) -> int | None:
    m = re.search(rf"^\s*{re.escape(key)}\s*:\s*(\d+)\s*$", text, re.MULTILINE)
    return int(m.group(1)) if m else None


def find_draft(draft: str) -> str | None:
    if os.path.isfile(draft):
        return draft
    if os.path.isdir(draft):
        for n in sorted(os.listdir(draft)):
            p = os.path.join(draft, n)
            if n.endswith(".md") and FINDINGS_BLOCK_RE.search(open(p, encoding="utf-8").read()):
                return p
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", default=None, help="미사용(gate_keeper 규약상 전달됨)")
    ap.add_argument("--draft", default=None, help="findings.md 또는 디렉터리")
    args = ap.parse_args()

    if not args.draft:
        print("FAIL(usage): --draft 필수 — fail-closed", file=sys.stderr); return 2
    try:
        policy = load_policy(args.policy)
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e} — fail-closed", file=sys.stderr); return 2

    path = find_draft(args.draft)
    if not path:
        print(f"FAIL(usage): ```findings``` 블록을 담은 문서를 찾지 못했다({args.draft}) — "
              f"원본은 보고서가 깨져 있어도 '0건'으로 읽어 PASS 했다. fail-closed",
              file=sys.stderr)
        return 2

    text = open(path, encoding="utf-8").read()
    m = FINDINGS_BLOCK_RE.search(text)
    if not m:
        print(f"FAIL(usage): {os.path.basename(path)} 에 ```findings``` 블록이 없다 — "
              f"보고서 형식이 깨진 것을 '발견 0건'으로 읽으면 안 된다(원본의 fail-open). "
              f"fail-closed", file=sys.stderr)
        return 2
    items = parse_findings(m.group(1))

    fields = policy.get("require_fields") or DEFAULT_FIELDS
    strict = [str(s).lower() for s in (policy.get("strict_severities") or DEFAULT_STRICT)]
    min_chars = int(policy.get("min_field_chars", 5))
    max_crit = policy.get("max_critical")
    max_high = policy.get("max_high")

    counts = {s: 0 for s in SEVERITIES}
    fail = False
    bad_sev = []
    for f in items:
        sev = str(f.get("severity", "")).lower()
        if sev not in counts:
            bad_sev.append((f.get("id", "?"), sev or "없음"))
            continue
        counts[sev] += 1
    if bad_sev:
        print(f"FAIL: severity 가 없거나 알 수 없는 발견 {bad_sev[:6]} — 등급 없는 발견은 "
              f"분류되지 않아 검사에서 빠진다")
        fail = True

    print(f"발견 {len(items)}건 · " + ", ".join(f"{s}={counts[s]}" for s in SEVERITIES))

    # ① 선언 수치 ↔ 실제 목록 대조 (원본은 선언 수치만 봤다)
    for key, sev in (("n_critical", "critical"), ("n_high", "high")):
        declared = int_field(text, key)
        if declared is None:
            print(f"FAIL: `{key}:` 선언이 없다 — 요약 수치와 목록을 대조할 수 없다")
            fail = True
        elif declared != counts[sev]:
            print(f"FAIL: `{key}: {declared}` 인데 목록의 {sev} 는 {counts[sev]}건이다 "
                  f"— **자기 신고 숫자만 보던 원본은 이 불일치를 통과시켰다**")
            fail = True

    # ② 조치 가능성 — 이 게이트의 본체
    for f in items:
        sev = str(f.get("severity", "")).lower()
        if sev not in strict:
            continue
        missing = [k for k in fields if len(str(f.get(k, ""))) < min_chars]
        if missing:
            print(f"FAIL: {f.get('id', '?')}({sev}) 에 {missing} 가 없다 — 위치·근거·영향·조치 "
                  f"없는 발견은 고칠 수 없다")
            fail = True

    # ③ 릴리스 게이트로 쓸 때만(기본 무제한) — 감사 자체를 막지 않는다
    for label, cap, n in (("critical", max_crit, counts["critical"]),
                          ("high", max_high, counts["high"])):
        if cap is not None and n > int(cap):
            print(f"FAIL: {label} {n}건 > 정책 상한 {cap} (릴리스 게이트 모드)")
            fail = True
    if max_crit is None and max_high is None and (counts["critical"] or counts["high"]):
        print(f"참고: Critical {counts['critical']}건 · High {counts['high']}건이 발견됐다. "
              f"**이 게이트는 건수로 막지 않는다** — 보고가 조치 가능한지만 본다. "
              f"조치 여부 판단은 Sam 의 몫이다")

    if not fail:
        print("  ✓ 모든 고위험 발견이 위치·근거·영향·조치를 갖췄고 요약 수치가 목록과 일치")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
