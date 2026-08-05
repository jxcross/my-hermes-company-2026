#!/usr/bin/env python3
"""
객관 게이트: 라이선스 적합성 + 선언 일관성
==========================================
소스 데이터의 라이선스를 **실제 LICENSE 파일에서 다시 판정**하고, 의도한 배포 라이선스와
양립하는지, 그리고 그 라이선스가 **산출물 전체에 같은 값으로 선언**됐는지 검사한다.
출처: other_projects/harness-templates/.../datasetforge/scripts/{license_check,pii_license_check}.py

⚠️ **하드게이트가 라이선스를 다시 검사하지 않는다** (docs/13 §5). `pii_license_check.py` 의
   docstring 은 "Re-runs PII scan … AND **license check against the source**" 라고 선언하지만,
   코드는 `license_check.py` 를 **한 번도 호출하지 않는다** — 5단계 에이전트가 쓴 마크다운
   frontmatter 를 `re.search` 로 읽을 뿐이다. **검사 대상이 자기 성적표를 적어 낸다.**
   agentforge 의 죽은 gold-set 대조와 같은 계열이 두 하네스 연속으로 나왔다.
   → 우리는 소스 LICENSE 를 **직접 다시 읽어** 판정한다.

⚠️ **`# safe default` 주석이 달린 죽은 기본값**(실측). 하드게이트는 이렇게 읽는다:
   `license_severity = license_report.get("verdict", "red")  # safe default`
   그런데 `parse_license_report` 는 파일이 없을 때 `{"verdict": "missing"}` 를 돌려준다.
   키가 **있으므로 기본값 `red` 는 절대 쓰이지 않는다.** 실측: 보고서 파일이 아예 없으면
   `severity="missing"` → `missing != "red"` → **PASS**. 방어적으로 보이는 주석이 달린
   자리가 정확히 구멍이었다.

⚠️ **CLAUDE.md 가 선언한 정책이 코드에 없다**: "License 가 `unknown` 이면 `red` 로 취급
   (안전 기본값)" · "`yellow` 이면 WARN — release-notes 에 명시 + user 확인 필요".
   실측: `verdict: unknown` → `unknown != "red"` → **PASS**. yellow 도 경고 한 줄 없이 통과.
   → `unknown`/`missing` 을 red 로 접고, yellow 는 **release-notes 명시를 요구**한다.

⚠️ **"아무 데도 선언하지 않으면 일관됨"**(실측). 원본:
   `license_consistent = len(declared_set) <= 1  # all same or all missing`
   데이터시트 어디에도 라이선스가 없으면 집합이 비어 `len 0 <= 1` → PASS. 라이선스 전파를
   검증하는 게이트가 **라이선스가 전무할 때 통과**한다. → 선언 부재를 FAIL 로.

⚠️ **분류 순서가 뒤집혀 있다**(실측). 원본 `classify_text` 는 green → yellow → red 순서로
   본다. 그래서 `Apache License / Version 2.0 … All Rights Reserved. Proprietary and
   Confidential.` 은 **green(Apache-2.0)** 으로 분류된다. 독점 조건이 덧붙은 permissive 헤더가
   통과한다. → **제한 조항을 먼저** 본다(하나라도 있으면 red).

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.license_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : 미션 디렉터리

정책 필드(license_policy)
  intent_license (필수 — 배포하려는 라이선스)
  source_dirs (기본 [_private/raw]) · declare_in (기본 datasheets/·bundle 의 README·croissant)
  block_severities (기본 [red]) · require_notes_for (기본 [yellow])
  allow_unknown (기본 false — unknown/missing 은 red)
  extra_compatible: {소스: [허용 배포 라이선스]} — 아래 표를 미션별로 넓힌다

⚠️ **양립성 표는 코드 라이선스 기준이라 보수적이다.** 데이터셋에서는 판단이 다를 수 있고
   (예: Apache-2.0 데이터를 CC-BY-4.0 으로 재배포), 보수적인 표를 그대로 두면 legalforge
   에서 겪은 **'어떤 입력에도 FAIL'** 과 같은 자리에 이르게 된다(docs/13 §5). 그래서 표를
   하드코딩으로 닫지 않고 `extra_compatible` 로 **정책에서 넓힐 수 있게** 뒀다 —
   넓히는 것은 근거를 적어 Sam 이 결정할 일이지, 게이트가 대신 정할 일이 아니다.

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

# ⚠️ 제한 조항을 **가장 먼저** 본다 — 원본은 마지막에 봐서 독점 조건이 덧붙은 Apache 헤더를
#    green 으로 분류했다(실측).
RED_PATTERNS = {
    "CC-BY-NC": [r"NonCommercial", r"CC[-\s]?BY[-\s]?NC"],
    "all-rights-reserved": [r"All Rights Reserved", r"Proprietary", r"Confidential",
                            r"내부용", r"무단\s*전재"],
}
GREEN_LICENSES = {
    "MIT": [r"MIT License|Permission is hereby granted, free of charge"],
    "BSD-3-Clause": [r"BSD 3-Clause|Neither the name of .+ nor the names"],
    "BSD-2-Clause": [r"BSD 2-Clause"],
    "Apache-2.0": [r"Apache License", r"Version 2\.0"],
    "CC-BY-4.0": [r"Creative Commons Attribution 4\.0|CC[-\s]?BY[-\s]?4\.0"],
    "CC0-1.0": [r"CC0|public domain dedication"],
    "ISC": [r"ISC License"],
    "Unlicense": [r"This is free and unencumbered"],
}
YELLOW_LICENSES = {
    "AGPL-3.0": [r"GNU AFFERO GENERAL PUBLIC LICENSE"],
    "LGPL-3.0": [r"GNU LESSER GENERAL PUBLIC LICENSE", r"Version 3"],
    "LGPL-2.1": [r"GNU LESSER GENERAL PUBLIC LICENSE", r"Version 2\.1"],
    "GPL-3.0": [r"GNU GENERAL PUBLIC LICENSE", r"Version 3"],
    "GPL-2.0": [r"GNU GENERAL PUBLIC LICENSE", r"Version 2"],
    "CC-BY-SA-4.0": [r"Creative Commons Attribution[-\s]ShareAlike|CC[-\s]?BY[-\s]?SA"],
    "MPL-2.0": [r"Mozilla Public License"],
}
COMPATIBILITY = {
    "MIT": {"MIT", "Apache-2.0", "BSD-3-Clause", "BSD-2-Clause", "GPL-3.0", "GPL-2.0",
            "LGPL-3.0", "CC-BY-4.0"},
    "BSD-3-Clause": {"BSD-3-Clause", "MIT", "Apache-2.0", "GPL-3.0"},
    "BSD-2-Clause": {"BSD-2-Clause", "MIT", "Apache-2.0", "GPL-3.0"},
    "Apache-2.0": {"Apache-2.0", "GPL-3.0"},
    "CC-BY-4.0": {"CC-BY-4.0", "CC-BY-SA-4.0"},
    "CC0-1.0": {"CC0-1.0", "CC-BY-4.0", "MIT", "Apache-2.0", "CC-BY-SA-4.0"},
    "ISC": {"ISC", "MIT", "Apache-2.0"},
    "Unlicense": {"Unlicense", "MIT", "CC0-1.0", "Apache-2.0"},
    "GPL-3.0": {"GPL-3.0"},
    "GPL-2.0": {"GPL-2.0", "GPL-3.0"},
    "LGPL-3.0": {"LGPL-3.0", "GPL-3.0"},
    "LGPL-2.1": {"LGPL-2.1", "LGPL-3.0", "GPL-2.0", "GPL-3.0"},
    "AGPL-3.0": {"AGPL-3.0"},
    "CC-BY-SA-4.0": {"CC-BY-SA-4.0"},
    "MPL-2.0": {"MPL-2.0", "GPL-3.0"},
}
LICENSE_FILES = ["LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING", "COPYING.md", "NOTICE"]
DECLARE_FILES = ["datasheets/datasheet.md", "datasheets/data-statement.md",
                 "datasheets/croissant.json", "report/release-notes.md"]
DECLARE_RE = [re.compile(r"^license\s*:\s*([A-Za-z0-9.\-]+)", re.MULTILINE | re.IGNORECASE),
              re.compile(r'"license"\s*:\s*"([A-Za-z0-9.\-]+)"'),
              re.compile(r"라이선스\s*:\s*([A-Za-z0-9.\-]+)")]


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("license_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("license_policy", {}) or {}


def mission_root(draft: str) -> str:
    p = os.path.abspath(draft)
    return p if os.path.isdir(p) else os.path.dirname(p)


def classify_text(text: str) -> tuple[str, str]:
    """(등급, 라이선스 id). **제한 조항을 먼저** 본다."""
    head = text[:5000]
    for lid, pats in RED_PATTERNS.items():
        if any(re.search(p, head, re.IGNORECASE) for p in pats):
            return ("red", lid)
    for lid, pats in GREEN_LICENSES.items():
        if all(re.search(p, head, re.IGNORECASE) for p in pats):
            return ("green", lid)
    for lid, pats in YELLOW_LICENSES.items():
        if all(re.search(p, head, re.IGNORECASE) for p in pats):
            return ("yellow", lid)
    return ("red", "UNKNOWN")


def declared_in(path: str) -> str | None:
    if not os.path.isfile(path):
        return None
    text = open(path, encoding="utf-8", errors="replace").read()
    for rx in DECLARE_RE:
        m = rx.search(text)
        if m:
            return m.group(1).strip()
    return None


def compatibility(source: str, intent: str, extra: dict | None = None) -> str:
    if source == intent:
        return "COMPATIBLE"
    if source == "UNKNOWN" or intent in (None, "", "UNKNOWN"):
        return "UNKNOWN"
    allowed = set(COMPATIBILITY.get(source, set())) | set((extra or {}).get(source, []))
    return "COMPATIBLE" if intent in allowed else "INCOMPATIBLE"


def main() -> int:  # noqa: C901
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", default=None, help="미사용(gate_keeper 규약상 전달됨)")
    ap.add_argument("--draft", default=None, help="미션 디렉터리")
    args = ap.parse_args()

    if not args.draft:
        print("FAIL(usage): --draft 필수 — fail-closed", file=sys.stderr); return 2
    try:
        policy = load_policy(args.policy)
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e} — fail-closed", file=sys.stderr); return 2

    root = mission_root(args.draft)
    intent = str(policy.get("intent_license") or "").strip()
    src_dirs = policy.get("source_dirs") or [os.path.join("_private", "raw")]
    declare_files = policy.get("declare_in") or DECLARE_FILES
    block = [s.lower() for s in (policy.get("block_severities") or ["red"])]
    notes_for = [s.lower() for s in (policy.get("require_notes_for") or ["yellow"])]
    allow_unknown = bool(policy.get("allow_unknown", False))

    if not intent:
        print("FAIL(usage): `license_policy.intent_license` 선언이 없다 — 무엇으로 배포할지 "
              f"모르면 양립성을 볼 수 없다. fail-closed", file=sys.stderr)
        return 2

    # ① 소스 라이선스를 **직접 다시 읽는다**(원본 하드게이트는 보고서만 읽었다)
    detected = []
    for d in src_dirs:
        base = d if os.path.isabs(d) else os.path.join(root, d)
        if not os.path.isdir(base):
            continue
        for dirpath, dirs, names in os.walk(base):
            dirs[:] = [x for x in dirs if x != "__pycache__"]
            for n in sorted(names):
                if n in LICENSE_FILES:
                    p = os.path.join(dirpath, n)
                    sev, lid = classify_text(open(p, encoding="utf-8", errors="replace").read())
                    detected.append((sev, lid, os.path.relpath(p, root)))
    if not detected:
        detected = [("red", "UNKNOWN", "(LICENSE 파일 없음)")]

    rank = {"green": 0, "yellow": 1, "red": 2}
    sev, lid, where = max(detected, key=lambda t: rank[t[0]])
    print(f"소스 라이선스 {len(detected)}건 검출 · 최악 등급 = {sev}({lid}) @ {where}")
    for s, i, w in detected:
        print(f"  {s:6s} {i:20s} {w}")
    print(f"배포 의도 라이선스 = {intent}")

    fail = False
    if lid == "UNKNOWN" and not allow_unknown:
        print(f"FAIL: 소스 라이선스를 식별할 수 없다(UNKNOWN) — **원본 CLAUDE.md 는 "
              f"'unknown 은 red 로 취급'이라 선언했지만 코드에는 없었다.** 확인되지 않은 "
              f"라이선스의 데이터를 배포하면 되돌릴 수 없다")
        fail = True
    if sev in block:
        print(f"FAIL: 소스 라이선스 등급 {sev}({lid}) 는 배포 차단 대상이다")
        fail = True

    extra = policy.get("extra_compatible") or {}
    compat = compatibility(lid, intent, extra)
    print(f"양립성: {lid} → {intent} = {compat}"
          + (f" (정책 확장 적용)" if intent in set(extra.get(lid, [])) else ""))
    if compat == "INCOMPATIBLE":
        print(f"FAIL: {lid} 소스를 {intent} 로 재배포할 수 없다 — 판단이 다르다면 근거를 적어 "
              f"`license_policy.extra_compatible: {{{lid}: [{intent}]}}` 로 넓혀라(Sam 결정)")
        fail = True
    elif compat == "UNKNOWN" and not allow_unknown:
        print(f"FAIL: 양립성을 판정할 수 없다 — 원본은 UNKNOWN 을 통과시켰다"
              f"(`overall_pass` 가 INCOMPATIBLE 만 막는다)")
        fail = True

    # ② 선언 일관성 — 원본은 '전무해도 일관됨'이었다
    declared = {}
    for rel in declare_files:
        p = rel if os.path.isabs(rel) else os.path.join(root, rel)
        declared[rel] = declared_in(p)
    missing = [k for k, v in declared.items() if v is None]
    values = {v for v in declared.values() if v}
    print(f"산출물 라이선스 선언: " + ", ".join(f"{os.path.basename(k)}={v or '없음'}"
                                          for k, v in declared.items()))
    if missing:
        print(f"FAIL: 라이선스가 선언되지 않은 산출물 {missing} — **원본은 아무 데도 선언이 "
              f"없으면 `len(set) <= 1` 로 '일관됨' PASS 였다.** 라이선스 없는 데이터셋은 "
              f"쓰는 쪽이 쓸 수 없다")
        fail = True
    if len(values) > 1:
        print(f"FAIL: 산출물마다 라이선스 선언이 다르다 {sorted(values)}")
        fail = True
    elif values and next(iter(values)) != intent:
        print(f"FAIL: 산출물 선언 {next(iter(values))!r} 이 의도 라이선스 {intent!r} 와 다르다")
        fail = True

    # ③ yellow 는 release-notes 에 명시해야 한다(원본은 경고조차 없었다)
    if sev in notes_for:
        notes = os.path.join(root, "report", "release-notes.md")
        text = open(notes, encoding="utf-8", errors="replace").read() if os.path.isfile(notes) else ""
        if lid.lower() not in text.lower():
            print(f"FAIL: 카피레프트({sev}·{lid}) 소스인데 release-notes.md 에 그 사실이 "
                  f"명시되지 않았다 — 쓰는 쪽이 상속되는 의무를 모른 채 가져간다. "
                  f"**원본은 yellow 를 경고 한 줄 없이 통과시켰다**")
            fail = True
        else:
            print(f"  ✓ {sev} 등급({lid})이 release-notes 에 명시됨")

    if not fail:
        print(f"  ✓ 소스 {sev}({lid}) → {intent} 양립 · 산출물 전체가 같은 라이선스를 선언")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
