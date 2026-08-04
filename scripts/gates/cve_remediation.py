#!/usr/bin/env python3
"""
객관 게이트: 의존성 CVE 조치 명시
===================================
알려진 고위험 CVE 마다 **조치 방법이 적혀 있는지**, 그리고 **스캔이 실제로 돌았는지**
LLM 없이 검사한다.
출처: other_projects/harness-templates/.../secforge/scripts/cve_check.py (GATE 3)

⚠️ 이식하며 고친 것 — **원본은 fail-open 이다** (docs/13 §5):
  1. **CVE 블록이 없으면 통과했다** — `block = m.group(1) if m else ""` → 항목 0건 →
     고위험 0건 → 조치 누락 0건 → **PASS**. 스캔을 아예 안 돌려도 합격이다.
     보안 게이트에서 "데이터가 없다"는 "문제가 없다"가 아니다.
  2. **severity 를 안 적으면 검사에서 빠졌다** — `c.get("severity","").upper() in (HIGH, CRITICAL)`
     이라 등급을 비워 두면 고위험 목록에서 제외되고 조치 요구도 사라진다.
  3. **스캔이 돌았다는 증거가 없다** — 매니페스트를 몇 개, 패키지를 몇 개 대조했는지 모른 채
     "CVE 0건" 을 그대로 받는다. → `scanned_manifests`·`scanned_packages` 를 요구한다.

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.cve_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : cve.md(```cves``` 블록) 또는 그 문서를 담은 디렉터리

기대 형식
  scanned_manifests: 2
  scanned_packages: 137

  ```cves
  - cve_id: CVE-2024-12345
    package: requests
    installed: 2.25.1
    severity: high            # critical | high | medium | low  (필수)
    fixed_in: 2.32.0
    remediation: 2.32.0 이상으로 올린다(호환성 영향 없음)
  ```

정책 필드(cve_policy)
  require_remediation_for (기본 [critical, high]) · require_scan_evidence (기본 true)
  min_remediation_chars (기본 10) · allowed_severities

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
CVES_BLOCK_RE = re.compile(r"```cves\s*\n(.*?)\n```", re.DOTALL)
ALLOWED_SEVERITIES = ["critical", "high", "medium", "low", "none"]


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("cve_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("cve_policy", {}) or {}


def parse_cves(block: str) -> list[dict]:
    items, current = [], None
    for line in block.splitlines():
        mi = re.match(r"^\s*-\s+(?:cve_id|package):\s*(\S+)", line)
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
            if n.endswith(".md") and CVES_BLOCK_RE.search(open(p, encoding="utf-8").read()):
                return p
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", default=None, help="미사용(gate_keeper 규약상 전달됨)")
    ap.add_argument("--draft", default=None, help="cve.md 또는 디렉터리")
    args = ap.parse_args()

    if not args.draft:
        print("FAIL(usage): --draft 필수 — fail-closed", file=sys.stderr); return 2
    try:
        policy = load_policy(args.policy)
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e} — fail-closed", file=sys.stderr); return 2

    path = find_draft(args.draft)
    if not path:
        print(f"FAIL(usage): ```cves``` 블록을 담은 문서를 찾지 못했다({args.draft}) — "
              f"**스캔 결과가 없다는 것은 '문제 없음'이 아니다.** fail-closed", file=sys.stderr)
        return 2

    text = open(path, encoding="utf-8").read()
    m = CVES_BLOCK_RE.search(text)
    if not m:
        print(f"FAIL(usage): {os.path.basename(path)} 에 ```cves``` 블록이 없다 — "
              f"**스캔 결과가 없다는 것은 '문제 없음'이 아니다**(원본은 이때 PASS 했다). "
              f"fail-closed", file=sys.stderr)
        return 2
    items = parse_cves(m.group(1))

    need = [str(s).lower() for s in (policy.get("require_remediation_for") or ["critical", "high"])]
    require_scan = bool(policy.get("require_scan_evidence", True))
    min_rem = int(policy.get("min_remediation_chars", 10))
    allowed = [str(s).lower() for s in (policy.get("allowed_severities") or ALLOWED_SEVERITIES)]

    fail = False

    # ① 스캔 실행 증거 — 원본에는 없던 검사
    if require_scan:
        n_man = int_field(text, "scanned_manifests")
        n_pkg = int_field(text, "scanned_packages")
        if n_man is None or n_pkg is None:
            print("FAIL: 스캔 실행 증거가 없다 — `scanned_manifests: N` · `scanned_packages: N` "
                  "줄이 필요하다. 몇 개를 대조했는지 모른 채 'CVE 0건'을 받을 수 없다")
            fail = True
        elif n_man == 0 or n_pkg == 0:
            print(f"FAIL: 스캔 대상이 0이다(매니페스트 {n_man} · 패키지 {n_pkg}) "
                  f"— 대조한 것이 없으면 결과도 없다")
            fail = True
        else:
            print(f"스캔 증거: 매니페스트 {n_man}개 · 패키지 {n_pkg}개 대조")

    # ② 항목별 검사
    print(f"CVE 항목 {len(items)}건 · 조치 필수 등급 {need}")
    no_sev, no_rem = [], []
    counts: dict[str, int] = {}
    for c in items:
        cid = c.get("id", "?")
        sev = str(c.get("severity", "")).lower()
        if sev not in allowed or not sev:
            no_sev.append(cid)
            continue
        counts[sev] = counts.get(sev, 0) + 1
        if sev in need and len(str(c.get("remediation", ""))) < min_rem:
            no_rem.append((cid, sev))
    if no_sev:
        print(f"FAIL: severity 가 없거나 허용값이 아닌 CVE {no_sev[:8]} — 원본은 등급을 비우면 "
              f"**고위험 목록에서 빠져** 조치 요구도 사라졌다")
        fail = True
    if no_rem:
        print(f"FAIL: 조치 방법이 없는 고위험 CVE {len(no_rem)}건: {no_rem[:6]}")
        fail = True
    if counts:
        print("등급 분포: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))

    if not fail:
        print("  ✓ 스캔 증거 있음 · 고위험 CVE 전건 조치 명시")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
