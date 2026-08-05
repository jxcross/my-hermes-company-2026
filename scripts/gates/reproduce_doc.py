#!/usr/bin/env python3
r"""
객관 게이트: REPRODUCE.md 의 실행 가능성
========================================
재현 안내서가 **다른 사람이 따라할 수 있는 형태인지** LLM 없이 검사한다 —
필수 절 · 실제 명령 블록 · **번들에 실재하는 파일만 가리키는가** · 플레이스홀더.
출처: reproforge 의 `doc-clarity-check` critic — **스크립트가 없다**(LLM 서술뿐). 신설.

⚠️ 이 아키타입에서 REPRODUCE.md 는 부수 문서가 아니라 **산출물 그 자체**다. 환경 파일이
   아무리 정확해도 안내서가 따라할 수 없으면 재현 패키지가 아니다. 그런데 원본의 판정
   기준은 "clarity" 라는 **서술**뿐이라 무엇이 통과인지가 매번 달라진다.

⚠️ **명령이 가리키는 파일이 실제로 번들에 있는지 본다.** 안내서에 `bash reproduce.sh` 라고
   적혀 있는데 번들에 그 파일이 없는 것이 이 계열에서 가장 흔한 사고다 —
   `doc_links`(아키타입 I)가 링크에 대해 하던 일을 **명령의 인자**에 대해 한다.

⚠️ **분량은 어절이 아니라 글자로 잰다**(국문 대응 · docs/13 §5).

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.doc_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : 미션 디렉터리 또는 REPRODUCE.md

정책 필드(doc_policy)
  sections — {키: [인정 제목 별칭]} (기본: 전제조건·설치·데이터·실행·검증·문제해결)
  min_section_chars (기본 40) · min_command_blocks (기본 2)
  placeholder_terms (기본 TBD·TODO·미정·<PATH>·xxx)
  bundle_dir (기본 bundle) — 명령이 가리키는 파일이 실재해야 하는 곳
  require_expected_runtime (기본 true) — 예상 소요를 밝혀야 한다

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
HEADING_RE = re.compile(r"^(#{1,4})\s+(.+?)\s*$", re.MULTILINE)
FENCE_RE = re.compile(r"```(?:bash|sh|shell|console)?\s*\n(.*?)\n```", re.DOTALL)
DEFAULT_SECTIONS = {
    "prerequisites": ["prerequisite", "requirement", "전제", "사전", "준비물", "요구 사항", "요구사항"],
    "install": ["install", "setup", "설치", "환경 구성", "환경구성"],
    "data": ["data", "dataset", "데이터", "자료 준비"],
    "run": ["run", "execute", "실행", "재현 절차", "reproduce"],
    "verify": ["verify", "expected", "검증", "확인", "기대 결과", "예상 결과"],
    "troubleshooting": ["troubleshoot", "faq", "문제 해결", "문제해결", "알려진 문제"],
}
DEFAULT_PLACEHOLDERS = ["TBD", "TODO", "미정", "<PATH>", "<YOUR", "xxx", "FIXME", "작성 예정"]
# 명령에서 파일처럼 보이는 토큰
FILE_TOKEN_RE = re.compile(r"(?<![\w/.-])([\w./-]+\.(?:sh|yml|yaml|txt|json|py|md|cfg|toml))")
RUNTIME_RE = re.compile(r"(\d+\s*(?:분|시간|초|min|minutes?|hours?|sec|seconds?))", re.IGNORECASE)


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("doc_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("doc_policy", {}) or {}


def mission_root(draft: str) -> str:
    p = os.path.abspath(draft)
    return p if os.path.isdir(p) else os.path.dirname(p)


def find_doc(draft: str, bundle_dir: str) -> tuple[str | None, str]:
    p = os.path.abspath(draft)
    if os.path.isfile(p):
        return p, os.path.dirname(p)
    for rel in (os.path.join(bundle_dir, "REPRODUCE.md"), "REPRODUCE.md"):
        c = os.path.join(p, rel)
        if os.path.isfile(c):
            return c, p
    return None, p


def sections_of(text: str) -> dict[str, tuple[int, str]]:
    """제목 → (heading level, 본문). **level 이 필요하다** — 문서 제목(H1)이 절 별칭과
    겹쳐 진짜 절을 가리는 일이 있다(픽스처가 잡은 자체 결함: `# 재현 절차` 라는 H1 이
    'run' 절로 매칭돼 `## 실행` 을 덮었다)."""
    out: dict[str, tuple[int, str]] = {}
    marks = list(HEADING_RE.finditer(text))
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        out[m.group(2).strip()] = (len(m.group(1)), text[m.end():end].strip())
    return out


def body_chars(body: str) -> int:
    """장식과 공백을 뺀 실질 글자 수. 코드 블록 안은 설명이 아니므로 제외한다."""
    stripped = FENCE_RE.sub(" ", body)
    return len(re.sub(r"[\s`*_>#\-|\[\]()]+", "", stripped))


def match_section(secs: dict[str, tuple[int, str]], aliases: list[str]) -> tuple[str, str] | None:
    """별칭에 맞는 절. **문서 제목(H1)보다 하위 제목을 우선**한다 — REPRODUCE.md 의 제목이
    `# 재현 절차` 인 것은 정상인데, 그것이 'run' 절로 잡히면 진짜 `## 실행` 절을 가린다."""
    hits = [(lvl, title, body) for title, (lvl, body) in secs.items()
            if any(a.lower() in title.lower() for a in aliases)]
    if not hits:
        return None
    deeper = [h for h in hits if h[0] > 1]
    lvl, title, body = (deeper or hits)[0]
    return title, body


def main() -> int:  # noqa: C901
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", default=None, help="미사용(gate_keeper 규약상 전달됨)")
    ap.add_argument("--draft", default=None, help="미션 디렉터리 또는 REPRODUCE.md")
    args = ap.parse_args()

    if not args.draft:
        print("FAIL(usage): --draft 필수 — fail-closed", file=sys.stderr); return 2
    try:
        policy = load_policy(args.policy)
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e} — fail-closed", file=sys.stderr); return 2

    bundle_dir = policy.get("bundle_dir") or "bundle"
    path, root = find_doc(args.draft, bundle_dir)
    if not path:
        print(f"FAIL(usage): REPRODUCE.md 를 찾지 못했다({args.draft}) — 재현 안내서 없는 "
              f"재현 패키지는 재현 패키지가 아니다. fail-closed", file=sys.stderr)
        return 2

    spec = policy.get("sections") or DEFAULT_SECTIONS
    min_chars = int(policy.get("min_section_chars", 40))
    min_cmds = int(policy.get("min_command_blocks", 2))
    placeholders = policy.get("placeholder_terms") or DEFAULT_PLACEHOLDERS
    require_runtime = bool(policy.get("require_expected_runtime", True))

    text = open(path, encoding="utf-8").read()
    secs = sections_of(text)
    fences = FENCE_RE.findall(text)
    bundle = os.path.join(root, bundle_dir)
    if not os.path.isdir(bundle):
        bundle = os.path.dirname(path)

    fail = False
    print(f"{os.path.relpath(path, root)} · 절 {len(secs)}개 · 명령 블록 {len(fences)}개 · "
          f"번들 {os.path.relpath(bundle, root)}/")

    # ① 필수 절
    for key, aliases in spec.items():
        aliases = aliases if isinstance(aliases, list) else [aliases]
        hit = match_section(secs, aliases)
        if hit is None:
            print(f"FAIL: '{key}' 절이 없다 (인정 표기: {aliases[:3]}) — 따라할 수 없는 안내서다")
            fail = True
            continue
        title, body = hit
        n = body_chars(body)
        bad = [t for t in placeholders if t.lower() in body.lower()]
        if n < min_chars:
            print(f"FAIL: '{title}' 절의 설명이 {n}자 — 명령만 있고 설명이 없다"
                  f"(하한 {min_chars}자, 코드 블록 제외)")
            fail = True
        if bad:
            print(f"FAIL: '{title}' 절에 플레이스홀더 {bad[:3]} — 채우지 않은 안내서는 "
                  f"따라할 수 없다")
            fail = True

    # ② 실제 명령이 있는가
    if len(fences) < min_cmds:
        print(f"FAIL: 실행 가능한 명령 블록이 {len(fences)}개 < 하한 {min_cmds} — 산문만으로는 "
              f"재현할 수 없다")
        fail = True

    # ③ 명령이 가리키는 파일이 번들에 실재하는가
    referenced: set[str] = set()
    for f in fences:
        for tok in FILE_TOKEN_RE.findall(f):
            base = os.path.basename(tok)
            if base and not tok.startswith(("http", "-")):
                referenced.add(base)
    have = set()
    for dirpath, dirs, names in os.walk(bundle):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        have |= set(names)
    ghosts = sorted(n for n in referenced if n not in have)
    if referenced:
        print(f"  명령이 가리키는 파일 {len(referenced)}건 · 번들에 실재 "
              f"{len(referenced) - len(ghosts)}건")
    if ghosts:
        print(f"FAIL: 번들에 없는 파일을 실행하라고 적었다 {ghosts[:6]} — 안내서대로 하면 "
              f"바로 막힌다(`doc_links` 가 링크에 대해 하는 일을 명령의 인자에 대해 한다)")
        fail = True

    # ④ 예상 소요 — 없으면 사용자는 멈춘 것인지 도는 중인지 모른다
    if require_runtime and not RUNTIME_RE.search(text):
        print(f"FAIL: 예상 소요 시간이 적혀 있지 않다 — 재현자가 '멈춘 것인지 도는 중인지' "
              f"판단할 수 없다('약 20분' 같은 표기)")
        fail = True

    if not fail:
        print(f"  ✓ 필수 절 {len(spec)}종 · 명령 {len(fences)}블록이 번들의 실재 파일을 "
              f"가리킴 · 예상 소요 명시")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
