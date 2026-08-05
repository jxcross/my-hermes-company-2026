#!/usr/bin/env python3
"""
객관 게이트: 다이어그램 무결성 — 선언↔산출↔슬라이드 삼각 대조 + Mermaid 문법
================================================================================
목차가 선언한 다이어그램이 **전부 만들어졌고**, 문법이 성립하며, **슬라이드에서 실제로
쓰이고**, 근거가 원자료에 있는지 LLM 없이 검사한다.
출처: slideforge 의 `mermaid_lint.py`(하드게이트가 호출) — 이식하며 세 군데 고쳤다.

⚠️ **다이어그램이 하나도 없으면 PASS 였다**(실측 · 공집합 통과 열한 번째):

       mmd_files = sorted(mermaid_dir.glob("*.mmd"))
       if not mmd_files:
           return {"status": "PASS", "detail": "no .mmd files (skipped)"}

   목차가 다이어그램 3개를 선언했는데 워커가 전부 죽어 0개여도 하드게이트가 통과한다.
   슬라이드에는 `{{mermaid:d1}}` 이 남고, `marp_export` 가 그것을 **주석**으로 바꾸므로
   발표장에서 빈 슬라이드가 뜬다. → **선언 목록 대비 존재**(policy-brief 의 패턴)로 뒤집었다.

⚠️ **괄호 균형을 파일 총계로 셌다**(실측):

       n_open = sum(l.count(opener) for l in lines)
       n_close = sum(l.count(closer) for l in lines)

   `flowchart LR` + `A[Input) --> B(Encoder]` 은 `[`1·`]`1·`(`1·`)`1 로 **총계가 맞아
   `PASS`** 다(실측). 깨진 다이어그램이 통과한다. → **스택 대응**(여는 순서와 닫는 순서가
   맞는지)으로 바꿨다.

⚠️ **사이드카와 근거를 검사하지 않는다.** 원본 템플릿은 "모든 노드 라벨은 02-source 에
   실제 존재 — 환각 금지" 와 "사이드카 .meta.yml 은 traceability 필수" 를 **선언만** 한다
   (docforge 의 '환각 금지 선언' 과 같은 자리 · docs/13 §5). → `source_basis` 가 원자료의
   claim/figure id 를 가리키는지 대조하고, 사이드카 부재를 FAIL 로 만들었다.

⚠️ **양방향으로 본다** — 슬라이드의 `{{mermaid:dN}}` 이 선언 밖을 가리키는 것(환각 참조)과,
   만들어 놓고 **아무 슬라이드도 쓰지 않는 것**(고아 다이어그램) 둘 다 잡는다.

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.diagram_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : 미션 디렉터리(reports/<MID>) 또는 그 하위

기대 형식 (_private/outline.md)
  ---
  n_diagrams: 2          # ⚠️ 명시 선언(0 도 명시한다) — 블록 길이와 대조한다
  ---
  ```diagrams
  - id: d1
    type: flowchart
    used_in_slide: 5
    source_basis: [e2, f1]
  ```

정책 필드(diagram_policy)
  outline_file · mermaid_dir (기본 _private/mermaid) · slides_dir · source_file
  valid_types · max_nodes (기본 8) · require_meta (기본 true)
  require_source_basis (기본 true) · min_body_lines (기본 2)

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
DIAGRAM_BLOCK_RE = re.compile(r"```diagrams\s*\n(.*?)\n```", re.DOTALL)
EV_BLOCK_RE = re.compile(r"```(?:evidence|figures)\s*\n(.*?)\n```", re.DOTALL)
ID_RE = re.compile(r"^\s*-\s*id:\s*(\S+)", re.MULTILINE)
FIELD_RE = re.compile(r"^\s+(\w+):\s*(.*)$")
MERMAID_PH_RE = re.compile(r"\{\{mermaid:([A-Za-z]?\d+)\}\}")
SLIDE_FILE_RE = re.compile(r"^slide-(\d+)\.md$")
MMD_FILE_RE = re.compile(r"^diagram-(\d+)\.mmd$")
QUOTED_RE = re.compile(r'"[^"]*"|\'[^\']*\'')
# erDiagram 의 카디널리티 토큰(`||--o{`)은 괄호가 아니다 — 스택 대응에서 제외한다.
ER_CARD_RE = re.compile(r"[|}o]{1,2}(?:--|\.\.)[|{o]{1,2}")
NODE_DEF_RE = re.compile(r"(?:^|[\s;])([A-Za-z_][\w-]*)\s*[\[\(\{]")
ARROW_RE = re.compile(r"([A-Za-z_][\w-]*)\s*(?:-{2,3}>|={2,3}>|-\.->|--[ox]|<-{2,3})\s*"
                      r"(?:\|[^|]*\|\s*)?([A-Za-z_][\w-]*)")
KEYWORDS = {"subgraph", "end", "direction", "style", "classDef", "class", "click",
            "linkStyle", "flowchart", "graph", "participant", "actor", "note", "loop",
            "alt", "opt", "par", "rect", "activate", "deactivate", "autonumber"}

DEFAULT_TYPES = ["flowchart", "graph", "sequenceDiagram", "classDiagram", "stateDiagram",
                 "stateDiagram-v2", "erDiagram", "gantt", "pie", "mindmap", "timeline",
                 "journey", "gitGraph", "quadrantChart", "xychart-beta",
                 "requirementDiagram", "sankey-beta", "C4Context", "block-beta"]
PAIRS = {")": "(", "]": "[", "}": "{"}


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("diagram_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("diagram_policy", {}) or {}


def mission_root(draft: str) -> str:
    """draft 가 하위 디렉터리여도 위로 올라가 `SCOPE.md` 가 있는 곳을 찾는다(docs/13 §5)."""
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


def parse_block(text: str, block_re: re.Pattern) -> list[dict] | None:
    m = block_re.search(text)
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


def known_source_ids(path: str) -> set[str]:
    """원자료의 claim·figure id — `source_basis` 가 여기 있는 것만 가리켜야 한다."""
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return set()
    out: set[str] = set()
    for m in EV_BLOCK_RE.finditer(text):
        out |= {x.group(1).strip() for x in ID_RE.finditer(m.group(1))}
    return out


def content_lines(text: str) -> list[str]:
    return [ln for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("%%")]


def bracket_issue(lines: list[str]) -> str | None:
    """⚠️ **스택 대응** — 원본은 문자 총계를 셌다. `A[Input) --> B(Encoder]` 는 총계가
    맞아 통과했다(실측)."""
    stack: list[tuple[str, int]] = []
    for i, raw in enumerate(lines, start=1):
        ln = ER_CARD_RE.sub(" ", QUOTED_RE.sub(" ", raw))
        for ch in ln:
            if ch in "([{":
                stack.append((ch, i))
            elif ch in ")]}":
                if not stack:
                    return f"line {i}: 여는 괄호 없이 '{ch}' 가 닫힌다"
                op, _ln = stack.pop()
                if op != PAIRS[ch]:
                    return f"line {i}: '{op}' 를 '{ch}' 로 닫았다 — 짝이 맞지 않는다"
    if stack:
        op, ln = stack[-1]
        return f"line {ln}: '{op}' 가 닫히지 않았다"
    return None


def count_nodes(dtype: str, lines: list[str]) -> int:
    """flowchart·graph 만 센다(다른 타입은 노드 개념이 다르다)."""
    if dtype not in ("flowchart", "graph"):
        return 0
    ids: set[str] = set()
    for raw in lines[1:]:
        ln = QUOTED_RE.sub(" ", raw)
        for m in NODE_DEF_RE.finditer(ln):
            ids.add(m.group(1))
        for m in ARROW_RE.finditer(ln):
            ids.add(m.group(1)); ids.add(m.group(2))
    return len(ids - KEYWORDS)


def lint_mermaid(text: str, valid: list[str], max_nodes: int, min_lines: int) -> list[str]:
    issues: list[str] = []
    lines = content_lines(text)
    if not lines:
        return ["빈 파일(다이어그램 내용이 없다)"]
    first = lines[0].strip()
    dtype = first.split()[0] if first else ""
    if dtype not in valid:
        issues.append(f"알 수 없는 다이어그램 타입 '{dtype}' (첫 줄: '{first[:50]}')")
    if len(lines) < min_lines:
        issues.append(f"본문이 {len(lines)}줄 — 타입 선언만 있고 내용이 없다")
    b = bracket_issue(lines)
    if b:
        issues.append(b)
    for i, ln in enumerate(lines, start=1):
        if "-->>>" in ln or "==>>>" in ln:
            issues.append(f"line {i}: 잘못된 화살표")
    n = count_nodes(dtype, lines)
    if max_nodes and n > max_nodes:
        issues.append(f"노드 {n}개 > 상한 {max_nodes} — 한 슬라이드에서 읽히지 않는다")
    return issues


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
    outline_p = os.path.join(root, policy.get("outline_file") or "_private/outline.md")
    mmd_d = os.path.join(root, policy.get("mermaid_dir") or "_private/mermaid")
    slides_d = os.path.join(root, policy.get("slides_dir") or "_private/slides")
    source_p = os.path.join(root, policy.get("source_file") or "_private/source.md")
    valid = [str(x) for x in (policy.get("valid_types") or DEFAULT_TYPES)]
    max_nodes = int(policy.get("max_nodes", 8))
    min_lines = int(policy.get("min_body_lines", 2))
    need_meta = bool(policy.get("require_meta", True))
    need_basis = bool(policy.get("require_source_basis", True))

    try:
        otext = open(outline_p, encoding="utf-8").read()
    except OSError:
        print(f"FAIL(usage): 목차를 찾지 못했다({os.path.relpath(outline_p, root)}) — "
              f"fail-closed", file=sys.stderr)
        return 2
    declared = parse_block(otext, DIAGRAM_BLOCK_RE) or []
    fm = FRONTMATTER_RE.match(otext)
    fmd = (yaml.safe_load(fm.group(1)) or {}) if fm else {}

    produced = sorted(n for n in (os.listdir(mmd_d) if os.path.isdir(mmd_d) else [])
                      if MMD_FILE_RE.match(n))
    print(f"선언 {len(declared)}개 · 산출 {len(produced)}개 · 노드 상한 {max_nodes}")
    fail = False

    # ── ① 분모 고정: n_diagrams 명시(0 도 명시한다) ──────────────────────────
    if "n_diagrams" not in fmd:
        print("FAIL: 목차 frontmatter 에 `n_diagrams:` 선언이 없다 — 0 이면 0 이라고 적어라. "
              "**선언이 없으면 '만들지 않은 것' 과 '만들 것이 없는 것' 을 구별할 수 없다**"
              "(원본은 파일이 0개면 통과시켰다)")
        fail = True
    else:
        try:
            n_declared = int(fmd.get("n_diagrams"))
        except (TypeError, ValueError):
            print(f"FAIL: `n_diagrams: {fmd.get('n_diagrams')}` 가 정수가 아니다")
            fail = True
            n_declared = None
        if n_declared is not None and n_declared != len(declared):
            print(f"FAIL: `n_diagrams: {n_declared}` 인데 ```diagrams``` 블록은 "
                  f"{len(declared)}개다")
            fail = True

    known = known_source_ids(source_p)
    meta_used: dict[str, str] = {}   # 사이드카가 선언한 사용처 — ④ 에서 실제 참조와 대조한다
    by_id: dict[str, dict] = {}
    for d in declared:
        did = str(d["id"]).strip()
        if did in by_id:
            print(f"FAIL: 다이어그램 id 중복 '{did}'")
            fail = True
        by_id[did] = d

    # ── ② 선언 목록 대비 존재 (원본은 파일이 없으면 PASS) ────────────────────
    def mmd_name(did: str) -> str:
        m = re.search(r"(\d+)", did)
        return f"diagram-{m.group(1)}.mmd" if m else f"diagram-{did}.mmd"

    for did, d in by_id.items():
        name = mmd_name(did)
        p = os.path.join(mmd_d, name)
        if not os.path.isfile(p):
            print(f"FAIL: 선언한 다이어그램 '{did}' 의 파일이 없다({name}) — **원본은 .mmd 가 "
                  f"하나도 없으면 '스킵' 으로 PASS 였다.** 슬라이드에는 placeholder 가 남고 "
                  f"발표장에서 빈 슬라이드가 된다")
            fail = True
            continue
        text = open(p, encoding="utf-8").read()
        for issue in lint_mermaid(text, valid, max_nodes, min_lines):
            print(f"FAIL: {name} — {issue}")
            fail = True
        # 사이드카
        meta_p = p + ".meta.yml"
        if need_meta:
            if not os.path.isfile(meta_p):
                print(f"FAIL: {name} 의 사이드카(.meta.yml)가 없다 — 원본 템플릿은 "
                      f"'traceability 필수' 라고 선언만 한다")
                fail = True
            else:
                try:
                    meta = yaml.safe_load(open(meta_p, encoding="utf-8").read()) or {}
                except yaml.YAMLError as e:
                    print(f"FAIL: {name}.meta.yml 파싱 실패 ({e})")
                    fail = True
                    meta = {}
                meta_used[did] = str(meta.get("used_in_slide", "")).strip()
                if str(meta.get("diagram_id", "")).strip() != did:
                    print(f"FAIL: {name}.meta.yml 의 diagram_id "
                          f"'{meta.get('diagram_id')}' 가 선언 '{did}' 과 다르다")
                    fail = True
                mtype = str(meta.get("type", "")).strip()
                ftype = (content_lines(text) or [""])[0].strip().split()[0] \
                    if content_lines(text) else ""
                if mtype and ftype and mtype != ftype:
                    print(f"FAIL: {name}.meta.yml 의 type '{mtype}' 이 실제 다이어그램 "
                          f"'{ftype}' 과 다르다")
                    fail = True
                if need_basis:
                    basis = str(meta.get("source_basis", "")).strip()
                    refs = re.findall(r"[A-Za-z]\d+", basis)
                    if not refs:
                        print(f"FAIL: {name}.meta.yml 의 `source_basis` 가 비었다 — 무엇을 "
                              f"근거로 그린 그림인지 없으면 환각을 막을 수 없다")
                        fail = True
                    elif known:
                        bad = [r for r in refs if r not in known]
                        if bad:
                            print(f"FAIL: {name}.meta.yml 의 source_basis 가 원자료에 없는 "
                                  f"id {bad} 를 가리킨다(환각 근거)")
                            fail = True
                    else:
                        print(f"FAIL: 원자료({os.path.relpath(source_p, root)})에서 claim/figure "
                              f"id 를 읽지 못했다 — source_basis 를 대조할 수 없다")
                        fail = True

    # ── ③ 선언 밖 산출물 ─────────────────────────────────────────────────────
    want_files = {mmd_name(d) for d in by_id}
    for name in produced:
        if name not in want_files:
            print(f"FAIL: 목차에 없는 다이어그램 파일 {name} 가 있다")
            fail = True

    # ── ④ 슬라이드와의 양방향 대조 ───────────────────────────────────────────
    used: dict[str, list[int]] = {}
    slide_names = sorted(n for n in (os.listdir(slides_d) if os.path.isdir(slides_d) else [])
                         if SLIDE_FILE_RE.match(n))
    for name in slide_names:
        num = int(SLIDE_FILE_RE.match(name).group(1))
        text = open(os.path.join(slides_d, name), encoding="utf-8").read()
        for m in MERMAID_PH_RE.finditer(text):
            ref = m.group(1)
            used.setdefault(ref, []).append(num)
            if ref not in by_id:
                print(f"FAIL: {name} 가 선언되지 않은 다이어그램 '{{{{mermaid:{ref}}}}}' 을 "
                      f"참조한다 — 치환할 것이 없어 발표장에서 빈 자리가 된다")
                fail = True
    if slide_names:
        for did, d in by_id.items():
            if did not in used:
                print(f"FAIL: 다이어그램 '{did}' 를 참조하는 슬라이드가 없다(고아) — 만들어 "
                      f"놓고 쓰지 않았다")
                fail = True
                continue
            # 목차와 사이드카 **양쪽의** 선언을 실제 참조와 대조한다. 한쪽만 보면 나머지
            # 한쪽은 아무도 읽지 않는 필드가 된다(죽은 변수 · docs/13 §5).
            for src, want in (("목차", str(d.get("used_in_slide", "")).strip()),
                              ("사이드카", meta_used.get(did, ""))):
                if not want:
                    continue
                try:
                    wnum = int(re.sub(r"[^\d]", "", want))
                except ValueError:
                    continue
                if wnum not in used[did]:
                    print(f"FAIL: '{did}' 는 {src} 선언상 슬라이드 {wnum} 에 쓰이는데 실제 "
                          f"참조는 {used[did]} 다")
                    fail = True

    if not fail:
        if not declared:
            print("  ✓ 다이어그램 0개를 명시적으로 선언했고 슬라이드에도 참조가 없다")
        else:
            print(f"  ✓ 다이어그램 {len(by_id)}개 전부 선언·산출·슬라이드 참조가 일치하고 "
                  f"문법이 성립한다")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
