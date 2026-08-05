#!/usr/bin/env python3
r"""
객관 게이트: 설치 테스트가 실제로 돌았다는 증거 + 미검증 항목 공시
==================================================================
재현 패키지가 **실행돼 봤는지**, 그리고 **검증하지 못한 경로를 숨기지 않았는지** LLM 없이
검사한다.
출처: reproforge 에는 이 검사가 **없다**(신설).

⚠️ **원본에서 이 자리가 통째로 비어 있다.** 하드게이트(`result_tolerance.py`)는 설치 테스트
   보고서의 `measurements:` 숫자만 읽는다. 실측: 보고서에
     `docker build: FAILED (base image not found)` · `smoke test: NOT RUN`
   이라고 적혀 있어도 그 아래 숫자만 있으면 **PASS · exit=0** 이다.
   재현 가능성을 증명하려고 만든 파이프라인이 **아무것도 재현되지 않았을 때 통과**한다.
   → 실행 사실 자체를 증거로 요구한다(방식·종료코드·소요·환경 지문·로그 발췌).

⚠️ **우리 환경에는 docker 데몬이 없다**(실측: `docker info` 실패 · `/var/run/docker.sock`
   부재). 컨테이너 안에서 `docker build` 를 돌릴 수 없고, **소켓을 붙이는 것은 호스트
   root 권한을 미션에 넘기는 일**이라 하지 않는다. 그래서 이 아키타입의 설치 테스트는
   `venv` 로 하고 Dockerfile 은 **정적 검토만** 한다.
   그런데 그것을 조용히 넘어가면 "Docker 로 재현된다"는 인상만 남는다 —
   **검증하지 못한 경로는 반드시 공시**하게 만든다(`docker_verified: false` 를 보고서와
   release-notes 양쪽에서 요구). 게이트가 못 하는 일을 못 했다고 말하게 하는 것이
   못 한 일을 한 척하는 것보다 낫다.

⚠️ **이 게이트는 아무것도 실행하지 않는다.** 게이트키퍼가 미션이 만든 코드를 돌리면 임의
   코드 실행 통로가 된다(`test_run`·`test_pass_rate`·`repro_determinism` 과 같은 규율 —
   docs/13 §7). 실행은 Tester 단계의 일이고 여기서는 그 **기록**을 검사한다.
   자기보고 신뢰 구간이 남지만, 기록이 없거나 실패로 적혀 있으면 **막는다**.

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.install_test_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : 미션 디렉터리

기대 형식 (install-test.md)
  method: venv
  build_status: success
  run_status: success
  exit_code: 0
  duration_sec: 143
  python_version: 3.13.5
  platform: linux-x86_64
  n_packages_installed: 27
  docker_verified: false

  ```log
  Successfully installed numpy-1.24.0 torch-2.1.0
  ...
  ```

정책 필드(install_test_policy)
  allowed_methods (기본 [venv, pip, conda]) · docker_available (기본 false)
  require_fields · min_duration_sec (기본 1) · min_log_lines (기본 3)
  disclose_in (기본 bundle/release-notes.md) — 미검증 경로를 공시할 파일

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
LOG_BLOCK_RE = re.compile(r"```log\s*\n(.*?)\n```", re.DOTALL)
MEAS_BLOCK_RE = re.compile(r"```measurements\s*\n(.*?)\n```", re.DOTALL)
SUCCESS_WORDS = ("success", "ok", "passed", "0")
DEFAULT_FIELDS = ["method", "build_status", "run_status", "exit_code", "duration_sec",
                  "python_version", "platform", "n_packages_installed"]
DEFAULT_METHODS = ["venv", "pip", "conda"]


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("install_test_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("install_test_policy", {}) or {}


def mission_root(draft: str) -> str:
    p = os.path.abspath(draft)
    return p if os.path.isdir(p) else os.path.dirname(p)


def field(text: str, key: str) -> str | None:
    m = re.search(rf"^\s*{re.escape(key)}\s*:\s*(\S.*?)\s*$", text, re.MULTILINE)
    return m.group(1).strip().strip('"\'') if m else None


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
    path = None
    for n in ("install-test.md", "06-install-test.md"):
        p = os.path.join(root, n)
        if os.path.isfile(p):
            path = p
            break
    if not path:
        print(f"FAIL(usage): install-test.md 를 찾지 못했다({root}) — 설치 테스트를 돌린 "
              f"기록이 없는 것은 재현된 것이 아니다. fail-closed", file=sys.stderr)
        return 2

    text = open(path, encoding="utf-8").read()
    fields = policy.get("require_fields") or DEFAULT_FIELDS
    methods = [str(m).lower() for m in (policy.get("allowed_methods") or DEFAULT_METHODS)]
    docker_available = bool(policy.get("docker_available", False))
    min_dur = float(policy.get("min_duration_sec", 1))
    min_log = int(policy.get("min_log_lines", 3))
    disclose_in = policy.get("disclose_in") or "bundle/release-notes.md"

    fail = False
    vals = {k: field(text, k) for k in fields}
    missing = [k for k, v in vals.items() if not v]
    print(f"설치 테스트 보고 {os.path.basename(path)} · 허용 방식 {methods} · "
          f"docker 사용가능={docker_available}")
    if missing:
        print(f"FAIL: 실행 증거 필드 누락 {missing} — **원본은 이 필드들을 요구하지 않아 "
              f"'build FAILED' 라고 적힌 보고서도 통과시켰다**(실측)")
        fail = True

    # ① 방식이 허용 목록 안인가
    method = (vals.get("method") or "").lower()
    if method and method not in methods:
        print(f"FAIL: 설치 방식 {method!r} 이 허용 목록 {methods} 밖이다 — 우리 컨테이너에는 "
              f"docker 데몬이 없다(소켓 부재). 붙이면 호스트 root 권한을 미션에 넘기는 일이다")
        fail = True

    # ② 실제로 성공했는가
    for key in ("build_status", "run_status"):
        v = (vals.get(key) or "").lower()
        if v and v not in SUCCESS_WORDS:
            print(f"FAIL: `{key}: {v}` — 실패한 실행은 재현의 증거가 아니다")
            fail = True
    ec = vals.get("exit_code")
    if ec is not None and str(ec).strip() not in ("0",):
        print(f"FAIL: `exit_code: {ec}` — 0 이 아니면 재현 스크립트가 끝까지 돌지 않았다")
        fail = True

    # ③ 소요 시간 — 0초는 돌지 않았다는 뜻이다
    dur = vals.get("duration_sec")
    if dur is not None:
        try:
            if float(dur) < min_dur:
                print(f"FAIL: `duration_sec: {dur}` < 하한 {min_dur} — 설치와 실행이 "
                      f"순식간에 끝났다면 실제로 돌지 않은 것이다")
                fail = True
        except ValueError:
            print(f"FAIL: `duration_sec: {dur!r}` 이 수가 아니다")
            fail = True

    npkg = vals.get("n_packages_installed")
    if npkg is not None:
        try:
            if int(npkg) <= 0:
                print(f"FAIL: 설치된 패키지가 {npkg}개 — 아무것도 설치하지 않았다")
                fail = True
        except ValueError:
            print(f"FAIL: `n_packages_installed: {npkg!r}` 이 수가 아니다")
            fail = True

    # ④ 로그 발췌 — 주장이 아니라 증거
    lm = LOG_BLOCK_RE.search(text)
    if not lm:
        print(f"FAIL: ```log``` 블록이 없다 — '성공했다'는 주장만으로는 증거가 아니다. "
              f"설치·실행 출력의 발췌를 남겨라")
        fail = True
    else:
        lines = [l for l in lm.group(1).splitlines() if l.strip()]
        if len(lines) < min_log:
            print(f"FAIL: 로그 발췌가 {len(lines)}줄 < 하한 {min_log}")
            fail = True

    mm = MEAS_BLOCK_RE.search(text)
    if not mm or not mm.group(1).strip():
        print(f"FAIL: ```measurements``` 블록이 없거나 비었다 — 무엇을 쟀는지 없이 "
              f"재현을 주장할 수 없다")
        fail = True

    # ⑤ **미검증 경로 공시** — 이 게이트만의 축
    dv = (field(text, "docker_verified") or "").lower()
    if dv not in ("true", "false"):
        print(f"FAIL: `docker_verified:` 선언이 없다(true|false) — Docker 경로를 실제로 "
              f"빌드해 봤는지 밝혀야 한다. 밝히지 않으면 읽는 사람은 검증됐다고 읽는다")
        fail = True
    elif dv == "true" and not docker_available:
        print(f"FAIL: `docker_verified: true` 인데 정책상 docker 를 쓸 수 없는 환경이다 — "
              f"실행하지 않은 검증을 했다고 적을 수 없다")
        fail = True
    elif dv == "false":
        disc = os.path.join(root, disclose_in)
        if not os.path.isfile(disc):
            print(f"FAIL: 미검증 공시 파일이 없다({disclose_in}) — Docker 경로가 검증되지 "
                  f"않았다는 사실을 배포물에 적어야 한다")
            fail = True
        else:
            dtext = open(disc, encoding="utf-8").read().lower()
            if "docker" not in dtext or not re.search(
                    r"검증되지\s*않|미검증|not\s+verified|unverified|빌드하지\s*않", dtext):
                print(f"FAIL: {disclose_in} 에 Docker 경로 미검증 사실이 적혀 있지 않다 — "
                      f"**게이트가 못 한 일을 못 했다고 말하게 하는 것이 이 검사의 목적**이다. "
                      f"'Docker 이미지는 이 환경에서 빌드 검증되지 않았다' 같은 문장을 넣어라")
                fail = True
            else:
                print(f"  ✓ Docker 경로 미검증 사실이 {disclose_in} 에 공시됨")

    if not fail:
        print(f"  ✓ {method} 방식으로 실제 실행됨(exit 0 · {dur}초 · 패키지 {npkg}개) · "
              f"로그 증거 있음 · 미검증 경로 공시됨")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
