#!/usr/bin/env python3
"""
객관 게이트: 공개 준비 — 지금 이것을 발신해도 되는가
========================================================
발신물이 **공개돼도 되는 자료**에서 나왔는지(공개 근거·엠바고·특허), **그대로 게시해도
되는 상태**인지(플레이스홀더·그림 저작권), 그리고 **우리가 게시하지 않는다는 고지**가
붙었는지 LLM 없이 검사한다.
출처: outreachforge — **이 검사가 통째로 없다.** 신설.

⚠️ **원본은 '무엇을 공개해도 되는가'를 한 번도 묻지 않는다.** 하드게이트는 사실 일치와
   과장만 본다. 그런데 이 아키타입의 입력은 **논문·데이터셋·시스템**이고, 그중에는

     · 심사 중이라 결과를 공개할 수 없는 원고(아키타입 R 의 입력이 바로 그것이다)
     · **출원 전 발명** — 공개하면 신규성을 잃는다(아키타입 F 와 정면으로 충돌한다)
     · 엠바고가 걸린 공동연구 결과 · 라이선스가 재배포를 막는 데이터

   가 섞인다. 발신은 **되돌릴 수 없는 행위**이고, 우리 파이프라인의 다른 아키타입들이
   `local_only` 로 지키던 것을 이 아키타입은 **공개하는 것이 목적**이라 더 위험하다.
   → 공개 근거를 **선언하게 하고**(fail-closed) 엠바고·특허 상태와 발신일을 대조한다.

⚠️ **엠바고 비교에 시계를 쓰지 않는다.** `embargo_until` 과 `launch_date` 를 **둘 다
   선언에서 읽어** 비교한다(sim-experiment 에서 배운 것 — 시각에 의존하는 판정은 픽스처가
   시간이 지나면 깨진다).

⚠️ **아키타입 Q·R 의 `legal_safety` 를 재사용하지 않았다.** 이름은 겹치지 않지만 하는 일이
   겹쳐 보인다 — 둘 다 '무엇이 커밋되는가'를 본다. 그러나 여기서는 **커밋 여부가 공개
   근거에 종속**된다(원자료가 이미 공개됐으면 커밋해도 되고 아니면 안 된다). 두 게이트가
   같은 질문에 서로 다른 정책으로 답하면 어느 쪽이 규칙인지 흐려지므로 하나로 뒀다
   (docs/13 §2④ — 재사용은 '하는 일'이 같을 때이고, 여기서는 **하나로 합치는 것**이
   같은 원칙의 다른 얼굴이다).

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.release_policy · policy.publication_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : 미션 디렉터리(reports/<MID>)

SCOPE.md frontmatter 선언
  release_basis: arxiv | doi | github_release | public_dataset | owner_approval
  release_ref: 2601.01234            # 근거의 실체(id·URL·태그)
  patent_status: none | filed | planned
  launch_date: 2026-09-01
  embargo_until: 2026-08-15          # 없으면 엠바고 없음

정책 필드(release_policy)
  allowed_basis · public_basis (커밋을 허용하는 근거) · require_launch_date (기본 true)
  checklist_file (기본 _private/launch-checklist.md) · visuals_file (기본 _private/visuals.md)
  placeholder_terms · require_visual_rights (기본 true)
  disclaimer_terms · scan_dirs (기본 [_private/channels])

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
BRIEF_ID_RE = re.compile(r"^\s*-\s*id:\s*(\S+)", re.MULTILINE)
FIELD_RE = re.compile(r"^\s+(\w+):\s*(.*)$")
VIS_BLOCK_RE = re.compile(r"```visuals\s*\n(.*?)\n```", re.DOTALL)

DEFAULT_PLACEHOLDERS = ["TBD", "TODO", "FIXME", "<URL>", "<링크>", "@handle", "@yourhandle",
                        "example.com", "xxx", "lorem ipsum", "작성 예정", "미정"]
DEFAULT_DISCLAIMER = ["게시는 저자", "직접 게시하지 않", "사람이 최종 확인",
                      "이 파이프라인은 게시하지"]


def load_policy(path: str, key: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get(key, {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get(key, {}) or {}


def mission_root(draft: str) -> str:
    p = os.path.abspath(draft)
    return p if os.path.isdir(p) else os.path.dirname(p)


def scope(root: str) -> dict:
    try:
        m = FRONTMATTER_RE.match(open(os.path.join(root, "SCOPE.md"), encoding="utf-8").read())
    except OSError:
        return {}
    return (yaml.safe_load(m.group(1)) or {}) if m else {}


def parse_visuals(path: str) -> list[dict] | None:
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return None
    m = VIS_BLOCK_RE.search(text)
    if not m:
        return None
    block = m.group(1)
    starts = list(BRIEF_ID_RE.finditer(block))
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


def md_files(root: str, rels: list[str]) -> list[str]:
    out = []
    for rel in rels:
        p = os.path.join(root, rel)
        if os.path.isfile(p):
            out.append(p)
        elif os.path.isdir(p):
            for dp, _d, names in os.walk(p):
                out += [os.path.join(dp, n) for n in sorted(names) if n.endswith(".md")]
    return out


def main() -> int:  # noqa: C901
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", default=None, help="미사용(gate_keeper 규약상 전달됨)")
    ap.add_argument("--draft", default=None, help="미션 디렉터리(reports/<MID>)")
    args = ap.parse_args()

    if not args.draft:
        print("FAIL(usage): --draft 필수 — fail-closed", file=sys.stderr); return 2
    try:
        policy = load_policy(args.policy, "release_policy")
        pub = load_policy(args.policy, "publication_policy")
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e} — fail-closed", file=sys.stderr); return 2

    root = mission_root(args.draft)
    sc = scope(root)
    allowed = policy.get("allowed_basis") or ["arxiv", "doi", "github_release",
                                              "public_dataset", "owner_approval"]
    public_basis = policy.get("public_basis") or ["arxiv", "doi", "github_release",
                                                  "public_dataset"]
    basis = str(sc.get("release_basis") or "").strip()
    ref = str(sc.get("release_ref") or "").strip()
    patent = str(sc.get("patent_status") or "").strip()
    launch = str(sc.get("launch_date") or "").strip()
    embargo = str(sc.get("embargo_until") or "").strip()

    print(f"공개 근거={basis or '(없음)'} · 근거 실체={ref or '(없음)'} · "
          f"특허={patent or '(없음)'} · 발신일={launch or '(없음)'} · "
          f"엠바고={embargo or '없음'}")
    fail = False

    # ① 공개 근거 — 선언이 없으면 검사가 성립하지 않는다(fail-closed)
    if not basis:
        print("FAIL: SCOPE.md 에 `release_basis:` 선언이 없다 — **무엇을 근거로 공개하는지 "
              "모르는 채 발신할 수 없다.** 발신은 되돌릴 수 없다")
        fail = True
    elif basis not in allowed:
        print(f"FAIL: 공개 근거 '{basis}' 가 허용값 {allowed} 밖이다")
        fail = True
    elif not ref:
        print(f"FAIL: 공개 근거가 '{basis}' 인데 `release_ref:`(id·URL·태그)가 없다 — "
              f"근거의 실체가 없으면 선언일 뿐이다")
        fail = True

    # ② 특허 — 출원 전 공개는 신규성을 잃는다(아키타입 F 와 충돌한다)
    if patent == "planned":
        print("FAIL: `patent_status: planned`(출원 예정) — **공개하면 신규성을 잃는다.** "
              "출원 후(`filed`)로 바꾸거나 발신을 미뤄라")
        fail = True
    elif patent not in ("none", "filed", "planned", ""):
        print(f"FAIL: 알 수 없는 `patent_status: {patent}`")
        fail = True
    elif not patent:
        print("FAIL: `patent_status:` 선언이 없다 — 출원 예정인 발명을 모르고 공개하는 것을 "
              "막는 선언이다(none 이면 none 이라고 적어라)")
        fail = True

    # ③ 엠바고 ↔ 발신일 — 둘 다 선언에서 읽는다(시계를 쓰지 않는다)
    if bool(policy.get("require_launch_date", True)) and not launch:
        print("FAIL: `launch_date:` 선언이 없다")
        fail = True
    if embargo and launch and embargo > launch:
        print(f"FAIL: 엠바고 해제일({embargo})이 발신일({launch})보다 늦다 — "
              f"엠바고 중에 공개하게 된다")
        fail = True

    # ④ 커밋 범위 — 공개된 자료일 때만 저장소에 올린다
    mode = str(pub.get("mode") or "local_only")
    if mode == "repo_commit" and basis and basis not in public_basis:
        print(f"FAIL: 공개 범위가 `repo_commit` 인데 공개 근거가 '{basis}' 다 — 이 저장소는 "
              f"PUBLIC 이므로 커밋 자체가 공개다. 원자료가 이미 공개된 경우"
              f"({public_basis})에만 허용한다")
        fail = True

    # ⑤ 플레이스홀더 — 그대로 게시되면 사고다
    terms = policy.get("placeholder_terms") or DEFAULT_PLACEHOLDERS
    scan = md_files(root, policy.get("scan_dirs") or ["_private/channels"])
    checklist_p = os.path.join(root, policy.get("checklist_file")
                               or "_private/launch-checklist.md")
    if os.path.isfile(checklist_p):
        scan.append(checklist_p)
    if not scan:
        print("FAIL(usage): 검사할 발신물이 없다 — fail-closed", file=sys.stderr)
        return 2
    for p in scan:
        text = open(p, encoding="utf-8").read()
        hits = [t for t in terms if t.lower() in text.lower()]
        if hits:
            print(f"FAIL: {os.path.basename(p)} 에 미완성 표시 {hits} — 그대로 게시되면 "
                  f"되돌릴 수 없다")
            fail = True

    # ⑥ 발신 체크리스트 + 우리가 게시하지 않는다는 고지
    if not os.path.isfile(checklist_p):
        print(f"FAIL: 발신 체크리스트가 없다({os.path.relpath(checklist_p, root)})")
        fail = True
    else:
        ctext = open(checklist_p, encoding="utf-8").read()
        if launch and launch not in ctext:
            print(f"FAIL: 체크리스트에 발신일 {launch} 이 없다 — 언제 무엇을 올릴지가 "
                  f"체크리스트의 전부다")
            fail = True
        dterms = policy.get("disclaimer_terms") or DEFAULT_DISCLAIMER
        if not any(t.lower() in ctext.lower() for t in dterms):
            print(f"FAIL: 체크리스트에 고지가 없다 — **이 파이프라인은 게시하지 않는다.** "
                  f"사람이 최종 확인 후 직접 올린다는 것을 명시하라(인정 문구: {dterms[:2]}…)")
            fail = True

    # ⑦ 그림 저작권 — 남의 그림을 무단으로 쓰지 않는다
    if bool(policy.get("require_visual_rights", True)):
        vpath = os.path.join(root, policy.get("visuals_file") or "_private/visuals.md")
        briefs = parse_visuals(vpath)
        if briefs is None:
            print(f"FAIL: {os.path.basename(vpath)} 의 ```visuals``` 블록이 없다 — 발신물에 "
                  f"쓰는 그림의 출처를 적지 않으면 남의 그림을 무단으로 쓰게 된다")
            fail = True
        else:
            for b in briefs:
                if not str(b.get("source", "")).strip():
                    print(f"FAIL: 그림 '{b['id']}' 에 `source:` 가 없다")
                    fail = True
                if not str(b.get("license", "")).strip():
                    print(f"FAIL: 그림 '{b['id']}' 에 `license:` 가 없다 — 자작이면 own, "
                          f"인용이면 그 라이선스를 적어라")
                    fail = True

    if not fail:
        print(f"  ✓ 공개 근거 {basis}({ref}) · 특허 {patent} · 발신일 {launch} · "
              f"플레이스홀더 없음 · 그림 권리 확인")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
