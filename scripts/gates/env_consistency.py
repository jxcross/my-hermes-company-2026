#!/usr/bin/env python3
r"""
객관 게이트: 환경 파일 3종의 일치(이름 + **버전**)
==================================================
탐지한 패키지 목록이 Dockerfile · environment.yml · requirements.txt **셋 모두**에
같은 이름과 **같은 버전**으로 들어갔는지 LLM 없이 검사한다.
출처: other_projects/harness-templates/.../reproforge/scripts/env_diff.py

⚠️ **버전을 한 번도 비교하지 않는다** (docs/13 §5 · 실측). 원본은 이름 집합만 대조한다.
   그런데 원본 CLAUDE.md 는 "04-env 의 패키지 버전은 03-env 와 일치 — **임의 `latest`
   사용 금지**" 라고 선언한다. 실측: canonical 이 `numpy 1.24.0`·`torch 2.1.0` 인데
   requirements 에 `numpy`(핀 없음)·`torch>=99.0`(전혀 다른 버전)을 써도
   `in_all_three=2 · PASS · exit=0`. **재현 패키지에서 버전이 안 맞으면 그 패키지는
   재현되지 않는다** — 이 게이트의 존재 이유가 통째로 비어 있었다.

⚠️ **주석에 `requirements.txt` 라고 적기만 해도 전 패키지가 커버된 것으로 센다**(실측):
   ```python
   if DOCKER_REQS_REF_RE.search(text):   # 파일 전체에서 문자열 검색
       out |= requirements_packages
   ```
   `# TODO: requirements.txt 를 나중에 추가한다` 한 줄이 있는, **아무것도 설치하지 않는
   Dockerfile** 이 2/2 커버리지로 통과했다. secforge 의 "A01…A10 은 앞으로 점검할 예정"
   과 같은 계열 — **글자의 존재를 이행의 증거로 셌다.**
   → `COPY … requirements.txt` **와** `RUN pip install -r …` 가 모두 있어야 인정한다.

⚠️ **패키지 목록이 비면 PASS 였다**(실측). ```py_packages``` 블록이 없으면 canonical 이
   빈 집합이 되어 `partial == 0` → PASS. 공집합이 통과하는 계열의 다섯 번째 사례다.

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.env_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : 미션 디렉터리

기대 형식 (env.md)
  ```py_packages
  - name: numpy
    version: 1.24.0
  ```

정책 필드(env_policy)
  files (기본 {docker: bundle/Dockerfile, conda: bundle/environment.yml,
               pip: bundle/requirements.txt})
  require_pinned (기본 true) — 모든 패키지가 정확한 버전으로 핀 돼야 한다
  min_packages (기본 1) · allow_unpinned (기본 []) — 핀 예외 목록

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
PKG_BLOCK_RE = re.compile(r"```py_packages\s*\n(.*?)\n```", re.DOTALL)
PKG_ITEM_RE = re.compile(r"^\s*-\s*name:\s*(\S+)", re.MULTILINE)
VERSION_RE = re.compile(r"^\s+version:\s*(\S+)", re.MULTILINE)
# `COPY … requirements.txt` 와 `RUN … pip install -r …` 를 각각 요구한다
DOCKER_COPY_REQ_RE = re.compile(r"^\s*COPY\s+[^\n]*requirements\.txt", re.MULTILINE | re.IGNORECASE)
DOCKER_PIP_REQ_RE = re.compile(r"^\s*RUN\s+[^\n]*pip\s+install[^\n]*-r\s+\S*requirements\.txt",
                               re.MULTILINE | re.IGNORECASE)
DOCKER_PIP_INLINE_RE = re.compile(r"^\s*RUN\s+([^\n]*pip\s+install[^\n]*)$", re.MULTILINE | re.IGNORECASE)
DEFAULT_FILES = {"docker": "bundle/Dockerfile", "conda": "bundle/environment.yml",
                 "pip": "bundle/requirements.txt"}
PIN_SPLIT_RE = re.compile(r"(==|>=|<=|~=|!=|>|<|=)")


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("env_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("env_policy", {}) or {}


def mission_root(draft: str) -> str:
    p = os.path.abspath(draft)
    return p if os.path.isdir(p) else os.path.dirname(p)


def norm(name: str) -> str:
    """PyPI 이름 정규화 — `Scikit_Learn` 과 `scikit-learn` 은 같은 패키지다."""
    return re.sub(r"[-_.]+", "-", name.strip().lower())


def parse_canonical(path: str) -> dict[str, str | None]:
    """{패키지: 버전}. env.md 의 ```py_packages``` 블록."""
    m = PKG_BLOCK_RE.search(open(path, encoding="utf-8").read())
    if not m:
        return {}
    block = m.group(1)
    starts = list(PKG_ITEM_RE.finditer(block))
    out: dict[str, str | None] = {}
    for i, s in enumerate(starts):
        body = block[s.end():(starts[i + 1].start() if i + 1 < len(starts) else len(block))]
        v = VERSION_RE.search(body)
        out[norm(s.group(1))] = v.group(1).strip() if v else None
    return out


def split_spec(token: str) -> tuple[str, str | None]:
    """`numpy==1.24.0` → ('numpy', '1.24.0') · `numpy` → ('numpy', None)."""
    token = token.strip()
    m = PIN_SPLIT_RE.search(token)
    if not m:
        return norm(token), None
    name = token[:m.start()]
    rest = token[m.start():]
    exact = re.match(r"^(?:==|=)\s*([^\s,;]+)$", rest)
    return norm(name), (exact.group(1) if exact else None)


def parse_pip(path: str) -> dict[str, str | None]:
    if not os.path.isfile(path):
        return {}
    out: dict[str, str | None] = {}
    for raw in open(path, encoding="utf-8"):
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        n, v = split_spec(line)
        if n and n[0].isalpha():
            out[n] = v
    return out


def parse_conda(path: str) -> dict[str, str | None]:
    if not os.path.isfile(path):
        return {}
    out: dict[str, str | None] = {}
    in_deps = False
    for raw in open(path, encoding="utf-8"):
        s = raw.rstrip("\n")
        if re.match(r"^dependencies\s*:", s):
            in_deps = True
            continue
        if not in_deps:
            continue
        if s.strip() and not s.startswith((" ", "\t", "-")):
            break
        m = re.match(r"^\s*-\s*(.+?)\s*$", s)
        if not m:
            continue
        token = m.group(1)
        if token.rstrip(":") == "pip":
            continue
        n, v = split_spec(token)
        if n and n[0].isalpha():
            out.setdefault(n, v)
    return out


def parse_docker(path: str, pip_pkgs: dict[str, str | None]) -> tuple[dict[str, str | None], list[str]]:
    """(패키지, 진단 메모). requirements.txt 는 **실제로 복사하고 설치**해야 인정한다."""
    notes: list[str] = []
    if not os.path.isfile(path):
        return {}, ["Dockerfile 이 없다"]
    text = open(path, encoding="utf-8").read()
    out: dict[str, str | None] = {}
    has_copy = bool(DOCKER_COPY_REQ_RE.search(text))
    has_install = bool(DOCKER_PIP_REQ_RE.search(text))
    if has_copy and has_install:
        out.update(pip_pkgs)
    elif re.search(r"requirements\.txt", text):
        notes.append("`requirements.txt` 를 언급하지만 `COPY … requirements.txt` "
                     f"{'있음' if has_copy else '없음'} · `RUN pip install -r …` "
                     f"{'있음' if has_install else '없음'} — **언급만으로는 설치가 아니다**"
                     "(원본은 주석 한 줄에 전 패키지를 커버로 셌다)")
    for m in DOCKER_PIP_INLINE_RE.finditer(text):
        for tok in m.group(1).split():
            if tok.startswith("-") or tok in ("pip", "install", "RUN", "python3", "-m"):
                continue
            if tok.endswith(".txt"):
                continue
            n, v = split_spec(tok)
            if n and n[0].isalpha():
                out.setdefault(n, v)
    return out, notes


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
    files = {**DEFAULT_FILES, **(policy.get("files") or {})}
    require_pinned = bool(policy.get("require_pinned", True))
    min_pkgs = int(policy.get("min_packages", 1))
    allow_unpinned = {norm(x) for x in (policy.get("allow_unpinned") or [])}

    env_md = None
    for n in ("env.md", "03-env.md"):
        p = os.path.join(root, n)
        if os.path.isfile(p):
            env_md = p
            break
    if not env_md:
        print(f"FAIL(usage): env.md 를 찾지 못했다({root}) — fail-closed", file=sys.stderr)
        return 2

    canonical = parse_canonical(env_md)
    if len(canonical) < min_pkgs:
        print(f"FAIL(usage): ```py_packages``` 에 패키지가 {len(canonical)}건 < 하한 {min_pkgs} "
              f"— **원본은 블록이 없으면 canonical 이 빈 집합이 되어 PASS 였다.** "
              f"의존성을 하나도 못 찾은 것은 의존성이 없는 것과 다르다. fail-closed",
              file=sys.stderr)
        return 2

    pip_path = os.path.join(root, files["pip"])
    conda_path = os.path.join(root, files["conda"])
    docker_path = os.path.join(root, files["docker"])
    pip_pkgs = parse_pip(pip_path)
    conda_pkgs = parse_conda(conda_path)
    docker_pkgs, docker_notes = parse_docker(docker_path, pip_pkgs)

    fail = False
    print(f"탐지 패키지 {len(canonical)}종 · pip {len(pip_pkgs)} · conda {len(conda_pkgs)} · "
          f"docker {len(docker_pkgs)}")
    for n in docker_notes:
        print(f"  ⚠ {n}")

    for label, path in (("Dockerfile", docker_path), ("environment.yml", conda_path),
                        ("requirements.txt", pip_path)):
        if not os.path.isfile(path):
            print(f"FAIL: {label} 이 없다({os.path.relpath(path, root)}) — 3종 중 하나라도 "
                  f"없으면 그 경로로는 재현할 수 없다(병렬 워커 하나가 죽은 경우)")
            fail = True

    # 이름 커버리지 + **버전 일치**
    for pkg in sorted(canonical):
        want = canonical[pkg]
        present = {"D": pkg in docker_pkgs, "C": pkg in conda_pkgs, "P": pkg in pip_pkgs}
        flags = "".join(k if v else "." for k, v in present.items())
        if not all(present.values()):
            print(f"FAIL: [{flags}] {pkg} 가 3종 전부에 있지 않다")
            fail = True
            continue
        got = {"D": docker_pkgs.get(pkg), "C": conda_pkgs.get(pkg), "P": pip_pkgs.get(pkg)}
        if require_pinned and pkg not in allow_unpinned:
            unpinned = [k for k, v in got.items() if v is None]
            if unpinned:
                print(f"FAIL: [{flags}] {pkg} 가 {unpinned} 에서 정확한 버전으로 핀 되지 "
                      f"않았다 — **원본은 버전을 한 번도 비교하지 않았다.** 핀 없는 의존성은 "
                      f"내일 다른 것을 설치한다")
                fail = True
                continue
        if want:
            mismatch = {k: v for k, v in got.items() if v is not None and v != want}
            if mismatch:
                print(f"FAIL: [{flags}] {pkg} 버전 불일치 — 탐지 {want} vs {mismatch}")
                fail = True
                continue
        else:
            print(f"참고: {pkg} 는 env.md 에 version 이 없다 — 탐지 단계에서 버전을 적어라")
        print(f"  ✓ [{flags}] {pkg}=={want or got['P']}")

    extras = sorted((set(pip_pkgs) | set(conda_pkgs)) - set(canonical))
    if extras:
        print(f"참고: 탐지 목록에 없는 패키지 {extras[:8]} — env.md 에 반영하거나 제거하라")

    if not fail:
        print(f"  ✓ 패키지 {len(canonical)}종이 Dockerfile·environment.yml·requirements.txt "
              f"3종에 같은 이름·같은 버전으로 들어갔다")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
