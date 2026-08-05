#!/usr/bin/env python3
"""repro-package(아키타입 O) 게이트를 '일부러 깨뜨린 픽스처'로 검증한다 (docs/13 §5).

원본 reproforge 게이트 2종에서 실측으로 확인한 결함 6건에 **회귀 방어**를 건다:
  · 빌드가 FAILED 라고 적혀 있어도 measurements 숫자만 보고 PASS      → ②-1
  · `expected:` 를 빼면 그 지표가 검사에서 조용히 사라진다(3→1개)      → ②-2
  · key_results 항목이 0건이면 PASS(공집합 통과)                      → ②-3
  · py_packages 블록이 없으면 canonical 공집합 → PASS                 → ④-1
  · Dockerfile 이 requirements.txt 를 **주석에서만** 언급해도 전 커버   → ④-2
  · 버전을 한 번도 비교하지 않는다(`latest`·미핀·전혀 다른 버전 통과)  → ④-3
"""
import json, os, shutil, subprocess, sys
import yaml

ROOT = "/work/company"
FIX = "/tmp/rpf"
GATES = os.path.join(ROOT, "scripts", "gates")

MIT = """MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files.
"""

REPRODUCE_MD = """---
license: MIT
---

# 재현 절차

이 패키지는 논문의 핵심 수치를 다시 계산하기 위한 것이다. 전체 소요는 **약 20분**이다.

## 전제조건

리눅스 또는 macOS 와 Python 3.11 이상이 필요하다. 디스크 여유 공간은 2GB 이상을
권장하며 네트워크 접속이 필요하다. GPU 는 필요하지 않다.

## 설치

저장소를 내려받은 뒤 번들 디렉터리에서 아래를 실행한다. 가상환경을 먼저 만들면
시스템 파이썬을 건드리지 않는다.

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## 데이터 준비

데이터는 스크립트가 자동으로 내려받고 sha256 으로 검증한다. 인증이 필요한 자료는
포함되어 있지 않으므로 별도 계정 없이 진행할 수 있다.

## 실행

아래 한 줄이 설치·데이터 확보·실행·측정을 모두 수행한다. 중간 출력으로 진행
상황을 확인할 수 있다.

```bash
bash reproduce.sh
```

## 검증

실행이 끝나면 `key-results.json` 이 생성된다. `accuracy` 가 0.873 ± 0.005 범위,
`f1` 이 0.819 ± 0.005 범위이면 재현에 성공한 것이다. 범위를 벗어나면 문제 해결
절을 보라.

## 문제 해결

설치가 실패하면 파이썬 버전을 먼저 확인하라. 데이터 다운로드가 막히면 사내
프록시 설정이 원인인 경우가 많다. 그래도 안 되면 릴리스 노트의 연락처로 알려 달라.
"""

RELEASE_NOTES = """---
license: MIT
---

# 릴리스 노트

- 소스 라이선스: MIT → 배포 MIT
- 검증 환경: Linux x86_64 · Python 3.13.5 · venv 방식으로 실측
- **Docker 이미지는 이 환경에서 빌드 검증되지 않았다**(컨테이너에 docker 데몬이 없다).
  Dockerfile 은 정적 검토만 거쳤으므로 사용 전 직접 빌드해 확인하라.
- 본 패키지는 단일 환경에서 수행된 검증이며 모든 환경에서의 재현을 보장하지 않습니다.
"""


def w(rel, s):
    p = os.path.join(FIX, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(s)


def build():
    shutil.rmtree(FIX, ignore_errors=True)
    os.makedirs(FIX)

    tpl = yaml.safe_load(open(os.path.join(ROOT, "templates", "repro-package.yaml"), encoding="utf-8"))
    json.dump({"policy": tpl["policy"]}, open(os.path.join(FIX, "pipeline.json"), "w"),
              ensure_ascii=False)

    w("_private/source/LICENSE", MIT)
    w("_private/source/train.py", "import numpy\nimport torch\n")
    w("ingest.md", "# 인벤토리\n코드 2건 · 진입점 train.py\n")

    w("env.md", """# 환경

Python 3.11 · 시스템 의존성 없음

```py_packages
- name: numpy
  version: 1.24.0
- name: torch
  version: 2.1.0
- name: scikit-learn
  version: 1.3.2
```
""")

    w("target.md", """---
source_type: local_dir
---

# 재현 대상

```key_results
- metric: accuracy
  expected: 0.873
  tolerance: {abs: 0.005}
  measurement_command: python eval.py --metric accuracy
- metric: f1
  expected: 0.819
  tolerance: {abs: 0.005}
  measurement_command: python eval.py --metric f1
```
""")

    w("bundle/Dockerfile", """FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["bash", "reproduce.sh"]
""")
    w("bundle/environment.yml", """name: repro
channels:
  - conda-forge
dependencies:
  - python=3.11
  - numpy=1.24.0
  - torch=2.1.0
  - scikit-learn=1.3.2
""")
    w("bundle/requirements.txt", "numpy==1.24.0\ntorch==2.1.0\nscikit-learn==1.3.2\n")
    w("bundle/reproduce.sh", """#!/usr/bin/env bash
set -euo pipefail
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python3 eval.py --all > measurements.json
""")
    w("bundle/REPRODUCE.md", REPRODUCE_MD)
    w("bundle/release-notes.md", RELEASE_NOTES)
    w("bundle/key-results.json", json.dumps(
        {"accuracy": {"expected": 0.873, "measured": 0.871, "tolerance_abs": 0.005},
         "f1": {"expected": 0.819, "measured": 0.821, "tolerance_abs": 0.005}},
        ensure_ascii=False, indent=2))
    w("bundle/install-test-report.md", "# 설치 테스트 요약\nvenv 방식 · 성공 · 143초\n")

    w("install-test.md", """# 설치 테스트

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
Collecting numpy==1.24.0
Successfully installed numpy-1.24.0 torch-2.1.0 scikit-learn-1.3.2
running eval.py --all
measurements written to measurements.json
```

```measurements
accuracy: 0.871
f1: 0.821
```
""")


def run(gate, draft):
    r = subprocess.run(["python3", os.path.join(GATES, f"{gate}.py"),
                        "--policy", os.path.join(FIX, "pipeline.json"),
                        "--sources", os.path.join(FIX, "raw", "sources.yaml"),
                        "--draft", os.path.join(FIX, draft)],
                       capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def expect(label, gate, want, show=False, draft="."):
    rc, out = run(gate, draft)
    print(f"{'OK ' if rc == want else '‼️ '}{label:60s} exit={rc} (기대 {want})")
    if rc != want or show:
        print("      " + "\n      ".join(out.splitlines()[-8:]))
    return rc == want


def patch(path, old, new):
    p = os.path.join(FIX, path)
    t = open(p, encoding="utf-8").read()
    assert old in t, f"픽스처 치환 실패: {old!r} not in {path}"
    open(p, "w", encoding="utf-8").write(t.replace(old, new, 1))


results = []
print("── ① 정상 픽스처: 5게이트 모두 PASS ──")
build()
results.append(expect("정상 · install_evidence", "install_evidence", 0, show=True))
results.append(expect("정상 · result_tolerance", "result_tolerance", 0, show=True))
results.append(expect("정상 · env_consistency", "env_consistency", 0, show=True))
results.append(expect("정상 · reproduce_doc", "reproduce_doc", 0, show=True))
results.append(expect("정상 · license_compat(N 에서 재사용)", "license_compat", 0))
results.append(expect("정상 · secret_redaction(L 에서 재사용)", "secret_redaction", 0,
                      draft="bundle"))

print("\n── ② result_tolerance: **원본 결함 3건의 회귀 방어** ──")
build(); patch("install-test.md", "run_status: success", "run_status: failed")
patch("install-test.md", "build_status: success", "build_status: failed")
results.append(expect("**빌드 실패인데 측정값만 적었다 — 원본 실측 PASS**",
                      "result_tolerance", 1, show=True))

build(); patch("target.md", "  expected: 0.819\n", "")
results.append(expect("**`expected:` 를 빼서 검사를 지운다 — 원본 실측 PASS**",
                      "result_tolerance", 1, show=True))

build(); patch("target.md", """- metric: accuracy
  expected: 0.873
  tolerance: {abs: 0.005}
  measurement_command: python eval.py --metric accuracy
- metric: f1
  expected: 0.819
  tolerance: {abs: 0.005}
  measurement_command: python eval.py --metric f1
""", "\n")   # 블록은 남기고 항목만 비운다 — '블록 형식이 깨졌다'가 아니라 '항목이 0건'을 검사한다
results.append(expect("**key_results 항목 0건 — 원본 실측 PASS**", "result_tolerance", 1, show=True))

build(); patch("install-test.md", "accuracy: 0.871", "accuracy: 0.950")
results.append(expect("측정값이 허용오차를 벗어남", "result_tolerance", 1, show=True))

build(); patch("install-test.md", "f1: 0.821", "recall: 0.821")
results.append(expect("선언한 지표가 측정되지 않음", "result_tolerance", 1))

build(); patch("install-test.md", "```measurements\naccuracy: 0.871\nf1: 0.821\n```", "")
results.append(expect("measurements 블록 자체가 없다", "result_tolerance", 1))

build(); patch("install-test.md", "run_status: success\n", "")
results.append(expect("run_status 선언 없음(성공했다는 근거가 없다)", "result_tolerance", 1))

build(); os.remove(os.path.join(FIX, "target.md"))
results.append(expect("target.md 부재 → fail-closed", "result_tolerance", 2))

print("\n── ③ 허용오차 미선언 시 정책 기본값(원본은 곧바로 FAIL 했다) ──")
build(); patch("target.md", "  tolerance: {abs: 0.005}\n  measurement_command: python eval.py --metric accuracy",
               "  measurement_command: python eval.py --metric accuracy")
results.append(expect("허용오차 미선언 → 정책 기본값 abs±0.02 적용 후 통과",
                      "result_tolerance", 0, show=True))

print("\n── ④ env_consistency: **원본 결함 3건의 회귀 방어** ──")
build(); patch("env.md", "```py_packages", "```packages")
results.append(expect("**py_packages 블록 없음 — 원본 실측 PASS**", "env_consistency", 2, show=True))

build(); patch("bundle/Dockerfile", "COPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\n",
               "# TODO: requirements.txt 를 나중에 추가한다\n")
results.append(expect("**주석에만 requirements.txt — 원본 실측 PASS**",
                      "env_consistency", 1, show=True))

build(); patch("bundle/requirements.txt", "numpy==1.24.0", "numpy")
results.append(expect("**핀 없는 패키지 — 원본은 버전을 안 봤다**", "env_consistency", 1, show=True))

build(); patch("bundle/requirements.txt", "torch==2.1.0", "torch>=99.0")
results.append(expect("**전혀 다른 버전 — 원본 실측 PASS**", "env_consistency", 1, show=True))

build(); patch("bundle/environment.yml", "  - torch=2.1.0\n", "")
results.append(expect("conda 에만 패키지가 빠졌다", "env_consistency", 1))

build(); os.remove(os.path.join(FIX, "bundle/environment.yml"))
results.append(expect("환경 파일 3종 중 하나가 없다(병렬 워커 사망)", "env_consistency", 1))

build(); patch("bundle/environment.yml", "  - scikit-learn=1.3.2", "  - scikit_learn=1.3.2")
results.append(expect("`scikit_learn` 과 `scikit-learn` 은 같은 패키지다(정규화)",
                      "env_consistency", 0))

print("\n── ⑤ install_evidence: 실행 증거(원본에 없던 검사) ──")
build(); patch("install-test.md", "duration_sec: 143", "duration_sec: 0")
results.append(expect("소요 0초(실제로 돌지 않았다)", "install_evidence", 1, show=True))

build(); patch("install-test.md", "exit_code: 0", "exit_code: 1")
results.append(expect("종료 코드가 0 이 아니다", "install_evidence", 1))

build(); patch("install-test.md", "n_packages_installed: 27", "n_packages_installed: 0")
results.append(expect("설치된 패키지 0개", "install_evidence", 1))

build(); patch("install-test.md", "method: venv", "method: docker")
results.append(expect("허용되지 않은 방식(데몬 없는 환경에서 docker 주장)", "install_evidence", 1, show=True))

build(); patch("install-test.md", "docker_verified: false", "docker_verified: true")
results.append(expect("**빌드하지 않은 검증을 했다고 적었다**", "install_evidence", 1, show=True))

build(); patch("install-test.md", "docker_verified: false\n", "")
results.append(expect("미검증 여부를 아예 밝히지 않았다", "install_evidence", 1))

build(); patch("bundle/release-notes.md",
               "- **Docker 이미지는 이 환경에서 빌드 검증되지 않았다**(컨테이너에 docker 데몬이 없다).\n  Dockerfile 은 정적 검토만 거쳤으므로 사용 전 직접 빌드해 확인하라.\n", "")
results.append(expect("**미검증 사실을 release-notes 에서 지웠다**", "install_evidence", 1, show=True))

build(); patch("install-test.md", """```log
Collecting numpy==1.24.0
Successfully installed numpy-1.24.0 torch-2.1.0 scikit-learn-1.3.2
running eval.py --all
measurements written to measurements.json
```

""", "")
results.append(expect("로그 증거 없음('성공했다'는 주장만)", "install_evidence", 1))

build(); os.remove(os.path.join(FIX, "install-test.md"))
results.append(expect("설치 테스트 보고 자체가 없음 → fail-closed", "install_evidence", 2))

print("\n── ⑥ reproduce_doc: 따라할 수 있는가 ──")
build(); patch("bundle/REPRODUCE.md", "## 문제 해결", "## 잡담")
results.append(expect("필수 절 누락(문제 해결)", "reproduce_doc", 1, show=True))

build(); patch("bundle/REPRODUCE.md", "bash reproduce.sh", "bash run_experiment.sh")
results.append(expect("**번들에 없는 파일을 실행하라고 적었다**", "reproduce_doc", 1, show=True))

build(); patch("bundle/REPRODUCE.md", "전체 소요는 **약 20분**이다.", "전체 소요는 상황에 따라 다르다.")
results.append(expect("예상 소요가 없다(멈춘 것인지 도는 중인지 모른다)", "reproduce_doc", 1))

build(); patch("bundle/REPRODUCE.md",
               "데이터는 스크립트가 자동으로 내려받고 sha256 으로 검증한다. 인증이 필요한 자료는\n포함되어 있지 않으므로 별도 계정 없이 진행할 수 있다.",
               "TBD")
results.append(expect("절이 플레이스홀더", "reproduce_doc", 1))

build(); patch("bundle/REPRODUCE.md", """```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```""", "가상환경을 만들고 의존성을 설치하면 된다.")
patch("bundle/REPRODUCE.md", """```bash
bash reproduce.sh
```""", "스크립트를 실행한다.")
results.append(expect("실행 가능한 명령 블록이 없다(산문뿐)", "reproduce_doc", 1))

build(); os.remove(os.path.join(FIX, "bundle/REPRODUCE.md"))
results.append(expect("REPRODUCE.md 부재 → fail-closed", "reproduce_doc", 2))

print("\n── ⑦ 재사용 게이트 · 설계 판단의 회귀 방어 ──")
build(); patch("bundle/reproduce.sh", "pip install -r requirements.txt",
               "pip install -r requirements.txt --index-url https://user:ghp_abcdefghijklmnopqrstuvwxyz0123@pkg.internal/simple")
results.append(expect("번들 스크립트에 토큰이 박힌 데이터/패키지 URL", "secret_redaction", 1,
                      show=True, draft="bundle"))

build(); patch("bundle/release-notes.md", "- 본 패키지는 단일 환경에서 수행된 검증이며 모든 환경에서의 재현을 보장하지 않습니다.\n", "")
patch("bundle/release-notes.md", "- **Docker 이미지는 이 환경에서 빌드 검증되지 않았다**(컨테이너에 docker 데몬이 없다).\n  Dockerfile 은 정적 검토만 거쳤으므로 사용 전 직접 빌드해 확인하라.\n", "")
results.append(expect("release-notes 의 고지 문구 누락", "secret_redaction", 1, draft="bundle"))

build(); w("_private/source/LICENSE", "All Rights Reserved. Proprietary.")
results.append(expect("재배포 불가 소스로 재현 패키지를 만들 수 없다", "license_compat", 1))

build()
results.append(expect("`_private/source/` 는 커밋 대상이 아니다(번들만 검사)",
                      "secret_redaction", 0, draft="bundle"))

print(f"\n{sum(results)}/{len(results)} 통과")
sys.exit(0 if all(results) else 1)
