#!/usr/bin/env python3
"""
객관 게이트: 심볼 실재성(코드 AST 대조)
=========================================
문서가 선언한 심볼(함수·클래스·모듈)이 **실제 코드에 존재하는지**, 시그니처가 맞는지,
그리고 **공개 API 를 빠뜨리지 않았는지** LLM 없이 검사한다. Python 은 `ast` 로 실제 파싱한다.

⚠️ **원본에는 이 게이트가 없다.** docforge 의 CLAUDE.md 는 "03-symbols 의 모든 entry 는
   실제 AST 분석 결과(**환각 금지**)" 라고 **선언만** 하고, 이를 검사하는 코드는 없다.
   지시로 남겨 두면 모델이 그럴듯한 심볼을 지어내도 파이프라인이 알아채지 못한다.

⚠️ 더 중요한 것은 **과소 선언(under-declaration)** 이다(docs/13 §5).
   원본의 하드게이트(`api_coverage.py`)는 커버리지를 **파이프라인이 스스로 만든 심볼 목록**
   대비로 잰다. 심볼 추출 단계가 공개 함수 100개 중 3개만 적어 내면 그 3개만 문서화해도
   **커버리지 100%** 다. 측정의 분모를 측정 대상이 정하는 구조라 게이트가 무력하다.
   → 여기서 **AST 가 찾은 공개 심볼 대비 선언 비율**(`min_declared_ratio`)을 강제한다.

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.symbol_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : symbols.md (```functions|classes|modules``` 블록)

코드베이스 경로는 미션 루트 `SCOPE.md` frontmatter 의 `codebase:` 에서 읽는다.

정책 필드(symbol_policy)
  ast_languages (기본 [python])   : 실제 파싱해 대조할 언어. 그 외는 WARNING(검증 불가)
  min_declared_ratio (기본 0.8)   : AST 공개 심볼 대비 선언 비율 하한(과소 선언 방지)
  check_signatures (기본 true)    : 선언된 signature 의 파라미터 이름 대조
  exclude_dirs (기본 아래 목록)    : 탐색 제외 디렉터리

exit: 0 PASS · 1 FAIL · 2 usage/입력없음(fail-closed)
"""
from __future__ import annotations
import argparse
import ast
import json
import os
import re
import sys

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML 필요", file=sys.stderr); sys.exit(2)

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
BLOCK_RE = r"```{}\s*\n(.*?)\n```"
ENTRY_RE = re.compile(r"^\s*-\s+(?:name|path):\s*(\S+)", re.MULTILINE)
SIG_RE = re.compile(r"^\s+signature:\s*(.+?)\s*$", re.MULTILINE)
DEFAULT_EXCLUDE = [".git", "__pycache__", "node_modules", ".venv", "venv", "build", "dist",
                   ".mypy_cache", ".pytest_cache", "site-packages"]


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("symbol_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("symbol_policy", {}) or {}


def scope_field(root: str, key: str):
    try:
        m = FRONTMATTER_RE.match(open(os.path.join(root, "SCOPE.md"), encoding="utf-8").read())
    except OSError:
        return None
    return (yaml.safe_load(m.group(1)) or {}).get(key) if m else None


def parse_declared(path: str) -> list[dict]:
    """symbols.md 의 블록에서 선언된 심볼 목록. 항목 = {name, kind, signature?}."""
    text = open(path, encoding="utf-8").read()
    out: list[dict] = []
    for kind in ("functions", "classes", "modules"):
        m = re.search(BLOCK_RE.format(kind), text, re.DOTALL)
        if not m:
            continue
        # 항목 단위로 쪼개 signature 를 같은 항목에 붙인다
        chunks = re.split(r"\n(?=\s*-\s+(?:name|path):)", m.group(1))
        for ch in chunks:
            em = ENTRY_RE.search(ch)
            if not em:
                continue
            sm = SIG_RE.search(ch)
            out.append({"name": em.group(1).strip(), "kind": kind,
                        "signature": sm.group(1).strip() if sm else None})
    return out


def py_files(root: str, exclude: list[str]) -> list[str]:
    out = []
    for dirpath, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d not in exclude and not d.startswith(".")]
        out += [os.path.join(dirpath, n) for n in sorted(names) if n.endswith(".py")]
    return sorted(out)


def is_public(name: str) -> bool:
    return not name.startswith("_")


def extract_python(root: str, exclude: list[str]) -> tuple[dict[str, list[str]], set[str]]:
    """(공개 심볼 → 파라미터 이름 목록, 모듈 경로 집합). 실패한 파일은 건너뛴다."""
    symbols: dict[str, list[str]] = {}
    modules: set[str] = set()
    for path in py_files(root, exclude):
        rel = os.path.relpath(path, root)
        modules.add(rel)
        modules.add(os.path.splitext(rel)[0].replace(os.sep, "."))
        try:
            tree = ast.parse(open(path, encoding="utf-8").read(), filename=path)
        except (SyntaxError, UnicodeDecodeError, OSError):
            continue
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and is_public(node.name):
                symbols[node.name] = [a.arg for a in node.args.args] + \
                                     [a.arg for a in node.args.kwonlyargs]
            elif isinstance(node, ast.ClassDef) and is_public(node.name):
                symbols[node.name] = []
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)) and is_public(sub.name):
                        args = [a.arg for a in sub.args.args if a.arg != "self"]
                        symbols[f"{node.name}.{sub.name}"] = args
    return symbols, modules


def sig_params(signature: str) -> list[str] | None:
    """선언된 시그니처에서 파라미터 **이름**만 뽑는다(기본값·타입힌트는 무시).
    형식이 자유로우므로 괄호가 없으면 None(대조 생략)."""
    m = re.search(r"\((.*)\)", signature, re.DOTALL)
    if not m:
        return None
    inner = m.group(1)
    if not inner.strip():
        return []
    params, depth, cur = [], 0, ""
    for ch in inner:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == "," and depth == 0:
            params.append(cur); cur = ""
        else:
            cur += ch
    params.append(cur)
    out = []
    for p in params:
        p = p.split("=")[0].split(":")[0].strip().lstrip("*")
        if p and p not in ("self", "cls", "/"):
            out.append(p)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", default=None, help="미사용(gate_keeper 규약상 전달됨)")
    ap.add_argument("--draft", default=None, help="symbols.md")
    args = ap.parse_args()

    if not args.draft or not os.path.isfile(args.draft):
        print(f"FAIL(usage): --draft(symbols.md) 필요 — fail-closed", file=sys.stderr); return 2
    try:
        policy = load_policy(args.policy)
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e} — fail-closed", file=sys.stderr); return 2

    root = os.path.dirname(os.path.abspath(args.draft))
    codebase = scope_field(root, "codebase")
    if not codebase:
        print("FAIL(usage): SCOPE.md frontmatter 에 `codebase:` 가 없다 — 무엇과 대조할지 "
              "알 수 없다. fail-closed", file=sys.stderr)
        return 2
    if not os.path.isabs(codebase):
        codebase = os.path.abspath(os.path.join(root, codebase))
    if not os.path.isdir(codebase):
        print(f"FAIL(usage): 코드베이스 경로가 없다({codebase}) — fail-closed", file=sys.stderr)
        return 2

    langs = [str(x).lower() for x in (policy.get("ast_languages") or ["python"])]
    min_ratio = float(policy.get("min_declared_ratio", 0.8))
    check_sig = bool(policy.get("check_signatures", True))
    exclude = policy.get("exclude_dirs") or DEFAULT_EXCLUDE

    declared = parse_declared(args.draft)
    if not declared:
        print(f"FAIL(usage): 선언된 심볼이 없다({args.draft}) — ```functions``` 블록에 "
              f"`- name:` 이 필요하다. fail-closed", file=sys.stderr)
        return 2

    if "python" not in langs:
        print(f"WARNING: ast_languages={langs} 에 python 이 없어 실제 대조를 건너뛴다 — "
              f"이 게이트는 현재 Python 만 파싱한다(다른 언어는 검증자가 읽어야 한다)")
        print("VERDICT: PASS")
        return 0

    truth, modules = extract_python(codebase, exclude)
    print(f"코드베이스 {codebase} · AST 공개 심볼 {len(truth)}개 · 모듈 {len(modules)//2}개 "
          f"· 선언 {len(declared)}개")

    fail = False

    # ① 환각 — 선언했는데 코드에 없는 심볼
    ghosts, sig_bad = [], []
    for d in declared:
        name = d["name"]
        if d["kind"] == "modules":
            if name not in modules and os.path.basename(name) not in \
                    {os.path.basename(m) for m in modules}:
                ghosts.append(name)
            continue
        if name not in truth:
            ghosts.append(name)
            continue
        if check_sig and d["signature"]:
            want = sig_params(d["signature"])
            if want is not None and want != truth[name]:
                sig_bad.append((name, d["signature"], truth[name]))
    if ghosts:
        print(f"FAIL: 코드에 없는 심볼을 선언했다(환각) {len(ghosts)}건: {ghosts[:8]}")
        fail = True
    if sig_bad:
        print(f"FAIL: 시그니처 불일치 {len(sig_bad)}건")
        for n, got, want in sig_bad[:5]:
            print(f"       · {n}: 문서 `{got}` ≠ 코드 파라미터 {want}")
        fail = True

    # ② 과소 선언 — 커버리지 게이트의 분모를 스스로 줄이는 것을 막는다
    declared_names = {d["name"] for d in declared if d["kind"] != "modules"}
    covered = [s for s in truth if s in declared_names]
    ratio = len(covered) / len(truth) if truth else 1.0
    print(f"선언 비율 {len(covered)}/{len(truth)} = {ratio:.1%} (하한 {min_ratio:.0%})")
    if ratio < min_ratio:
        undeclared = sorted(set(truth) - declared_names)
        print(f"FAIL: 공개 심볼을 과소 선언했다 — 누락 {len(undeclared)}건: {undeclared[:10]}")
        print(f"      (커버리지 게이트는 이 목록을 분모로 쓴다. 여기서 빠뜨리면 "
              f"문서화율이 실제보다 높게 나온다)")
        fail = True

    if not fail:
        print(f"  ✓ 환각 0건 · 시그니처 일치 · 선언 비율 충족")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
