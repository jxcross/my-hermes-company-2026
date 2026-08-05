#!/usr/bin/env python3
"""sim-experiment(아키타입 P) 게이트를 '일부러 깨뜨린 픽스처'로 검증한다 (docs/13 §5).

원본 simforge 에서 실측으로 확인한 결함에 **회귀 방어**를 건다:
  · `output.hash` 를 **존재만** 확인 — 0 을 64자 적어도 PASS            → ③-1
  · `--doe` 인자를 광고만 하고 한 번도 쓰지 않음(입력 드리프트 미검사)   → ③-2
  · run 이 0건이면 PASS(공집합 통과, 여섯 번째)                         → ③-3
  · Gate 1(환경 감사)·Gate 3(출력 완결성)은 **스크립트가 없다**         → ②·④ 전체
"""
import hashlib, json, os, shutil, subprocess, sys
import yaml

ROOT = "/work/company"
FIX = "/tmp/smf"
GATES = os.path.join(ROOT, "scripts", "gates")

DESIGN = [("run-01", 0.05, 100), ("run-02", 0.05, 200),
          ("run-03", 0.10, 100), ("run-04", 0.10, 200),
          ("run-05", 0.20, 100), ("run-06", 0.20, 200)]
SOLVER_VER = "11.0"
SOLVER_COMMIT = "3f2a91c8d4"
EXCLUDE = ["*.log", "*.tmp", "timestamp.txt", "*.pyc"]


def w(rel, s):
    p = os.path.join(FIX, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(s)


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_dir(root):
    """게이트와 **같은 알고리즘** — 다르면 정상 픽스처가 통과하지 않는다."""
    import fnmatch
    files = []
    for dp, _d, names in os.walk(root):
        for n in names:
            p = os.path.join(dp, n)
            rel = os.path.relpath(p, root).replace(os.sep, "/")
            if any(fnmatch.fnmatch(rel, x) or fnmatch.fnmatch(n, x) for x in EXCLUDE):
                continue
            files.append((rel, p))
    files.sort(key=lambda t: t[0])
    agg = hashlib.sha256()
    for rel, p in files:
        agg.update(rel.encode()); agg.update(b"\0")
        agg.update(file_sha256(p).encode("ascii")); agg.update(b"\n")
    return agg.hexdigest()


def build():
    shutil.rmtree(FIX, ignore_errors=True)
    os.makedirs(FIX)
    tpl = yaml.safe_load(open(os.path.join(ROOT, "templates", "sim-experiment.yaml"), encoding="utf-8"))
    json.dump({"policy": tpl["policy"]}, open(os.path.join(FIX, "pipeline.json"), "w"),
              ensure_ascii=False)

    w("hypothesis.md", """# 가설

```independent_vars
- name: mesh
  range: [0.05, 0.2]
- name: reynolds
  range: [100, 200]
```
응답변수: drag
""")
    w("env/requirements.txt", "numpy==1.24.0\n")
    w("solver.md", f"""# 솔버 고정

solver_name: openfoam
solver_version: {SOLVER_VER}
solver_commit: {SOLVER_COMMIT}
deps_lock: env/requirements.txt
hardware: 16-core x86_64 / OpenMPI 4.1.5
solver_type: local
""")

    runs_block = "\n".join(
        f"- id: {rid}\n  inputs: runs/{rid}/inputs.json\n"
        f"  design_point: {{mesh: {mesh}, reynolds: {re_}}}\n  status: done"
        for rid, mesh, re_ in DESIGN)
    w("doe.md", f"# 실험계획\n\n방법: 완전요인(3×2)\n\nn_design_points: {len(DESIGN)}\n\n```runs\n{runs_block}\n```\n")
    w("run-plan.md", "# 실행 계획\n설계점 6건 · 1회 약 12분 · 재현 검증 대상 run-03\n")

    for rid, mesh, re_ in DESIGN:
        w(f"runs/{rid}/inputs.json", json.dumps({"mesh": mesh, "reynolds": re_},
                                                ensure_ascii=False))
        w(f"runs/{rid}/config.json", json.dumps({
            "solver_version": SOLVER_VER, "solver_commit": SOLVER_COMMIT,
            "seed": 42, "design_point": {"mesh": mesh, "reynolds": re_},
            "status": "done"}, ensure_ascii=False, indent=2))
        w(f"runs/{rid}/outputs/field.json", json.dumps(
            {"drag": round(0.5 + mesh * 2 + re_ * 0.001, 6),
             "lift": round(1.0 - mesh, 6)}, ensure_ascii=False))
        w(f"runs/{rid}/outputs/solver.log", "converged in 412 iterations\n")
        w(f"runs/{rid}/outputs.json", json.dumps(
            {"drag": round(0.5 + mesh * 2 + re_ * 0.001, 6),
             "lift": round(1.0 - mesh, 6)}, ensure_ascii=False))
        h = hash_dir(os.path.join(FIX, "runs", rid, "outputs"))
        w(f"runs/{rid}/output.hash", h + "\n")
    # 재현 검증 증거 1건
    h3 = hash_dir(os.path.join(FIX, "runs", "run-03", "outputs"))
    w("runs/run-03/output.replay.hash", h3 + "\n")
    w("runs-summary.md", "# 실행 요약\n설계점 6건 · 성공 6 · 실패 0\n")

    w("data/drag.csv", "mesh,reynolds,drag\n"
      + "".join(f"{m},{r},{round(0.5 + m*2 + r*0.001, 6)}\n" for _i, m, r in DESIGN))
    w("analysis.md", """# 분석

n_samples: 6

주요 결과는 `data/drag.csv` 에 있다.

```sensitivity
{"response": "drag", "n_samples": 24,
 "variables": [{"name": "mesh", "S_i": 0.62, "S_Ti": 0.71, "pearson": 0.81, "beta": 0.73},
               {"name": "reynolds", "S_i": 0.21, "S_Ti": 0.29, "pearson": 0.44, "beta": 0.38}],
 "notes": "S_i 와 S_Ti 는 표본 분산 기반 근사치다(S_Ti 는 proxy)"}
```
""")
    w("figures.md", """# 그림

figures_generated: false

이 환경에는 matplotlib 이 설치되어 있지 않아 그림을 생성하지 못했다.
`figures/plot.py` 와 `data/*.csv` 로 재현할 수 있다.

- fig1: mesh 대비 drag 주결과 그림
- fig2: 응답변수 drag 의 민감도 막대그림
""")
    w("figures/plot.py", "# matplotlib 필요\nimport csv\n")

    w("report/report.md", """# 실험 보고서

본 결과는 단일 환경에서 수행된 실험이며 민감도 지수는 근사치입니다.
그림은 생성되지 않았고 `plot.py` 로 재현합니다.

## 결과
mesh 가 drag 를 지배한다(S_i 0.62).
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


def rehash(rid):
    w(f"runs/{rid}/output.hash", hash_dir(os.path.join(FIX, "runs", rid, "outputs")) + "\n")


results = []
print("── ① 정상 픽스처: 5게이트 모두 PASS ──")
build()
results.append(expect("정상 · solver_pin(실행 모드)", "solver_pin", 0, show=True))
results.append(expect("정상 · doe_completeness", "doe_completeness", 0, show=True))
results.append(expect("정상 · bit_exact", "bit_exact", 0, show=True))
results.append(expect("정상 · analysis_integrity", "analysis_integrity", 0, show=True))
results.append(expect("정상 · secret_redaction(L 재사용)", "secret_redaction", 0, draft="report"))

print("\n── ② solver_pin: 원본에 스크립트가 없던 Gate 1 ──")
build(); shutil.rmtree(os.path.join(FIX, "runs"))
results.append(expect("계획 모드(run 이 아직 없다) → 선언만 검사", "solver_pin", 0, show=True))

build(); patch("solver.md", f"solver_version: {SOLVER_VER}", "solver_version: latest")
results.append(expect("핀 되지 않은 태그 `latest`", "solver_pin", 1, show=True))

build(); patch("solver.md", f"solver_commit: {SOLVER_COMMIT}\n", "")
results.append(expect("커밋도 이미지 해시도 없다", "solver_pin", 1))

build(); patch("solver.md", "deps_lock: env/requirements.txt", "deps_lock: env/missing.txt")
results.append(expect("deps_lock 파일이 실재하지 않는다", "solver_pin", 1))

build(); patch("solver.md", "hardware: 16-core x86_64 / OpenMPI 4.1.5\n", "")
results.append(expect("하드웨어 지문 없음", "solver_pin", 1))

build(); patch("runs/run-04/config.json", f'"solver_version": "{SOLVER_VER}"',
               '"solver_version": "10.2"')
results.append(expect("**파이프라인 중간에 솔버가 바뀌었다 — 원본은 대조 안 함**",
                      "solver_pin", 1, show=True))

build(); patch("solver.md", "solver_type: local",
               "solver_type: remote\nendpoint: https://x/api\napp_version: v2.3")
results.append(expect("원격인데 image_hash·auth_env_var 없음", "solver_pin", 1))

build(); patch("solver.md", "solver_type: local",
               "solver_type: local\napi_key: abcdefghijklmnopqrstuvwxyz0123")
results.append(expect("토큰 **값**을 적었다(PUBLIC 저장소)", "solver_pin", 1))

print("\n── ③ bit_exact: **원본 결함 3건의 회귀 방어** ──")
build(); w("runs/run-02/output.hash", "0" * 64 + "\n")
results.append(expect("**해시가 실제 출력과 무관 — 원본 실측 PASS**", "bit_exact", 1, show=True))

build(); patch("runs/run-05/inputs.json", '"mesh": 0.2', '"mesh": 0.25')
results.append(expect("**입력 드리프트 — 원본은 `--doe` 를 쓰지 않았다**", "bit_exact", 1, show=True))

build(); shutil.rmtree(os.path.join(FIX, "runs"))
os.makedirs(os.path.join(FIX, "runs"))
results.append(expect("**run 0건 — 원본 실측 PASS**", "bit_exact", 2, show=True))

build()
patch("runs/run-03/outputs/field.json", '"drag"', '"drag_modified"')
results.append(expect("출력이 바뀌었는데 해시를 갱신하지 않았다", "bit_exact", 1))

build(); os.remove(os.path.join(FIX, "runs/run-03/output.replay.hash"))
results.append(expect("재현 검증 증거가 없다", "bit_exact", 1))

build(); w("runs/run-03/output.replay.hash", "f" * 64 + "\n")
results.append(expect("재실행 해시 불일치(bit-exact)", "bit_exact", 1))

build(); patch("runs/run-01/config.json", '"seed": 42,\n  ', "")
results.append(expect("config 에 seed 가 없다", "bit_exact", 1))

build(); os.remove(os.path.join(FIX, "runs/run-06/inputs.json"))
results.append(expect("inputs.json 이 없다(무엇을 넣었는지 모른다)", "bit_exact", 1))

print("\n── ④ doe_completeness: 원본에 스크립트가 없던 Gate 3 ──")
build(); shutil.rmtree(os.path.join(FIX, "runs/run-04"))
patch("doe.md", "- id: run-04\n  inputs: runs/run-04/inputs.json\n"
                "  design_point: {mesh: 0.1, reynolds: 200}\n  status: done\n", "")
results.append(expect("**설계점을 DOE 표에서도 지웠다(6→5) — 회계는 일관해진다**",
                      "doe_completeness", 1, show=True))

build(); patch("doe.md", f"n_design_points: {len(DESIGN)}\n\n", "")
results.append(expect("`n_design_points:` 선언이 없다(분모를 고정하지 않았다)",
                      "doe_completeness", 1))

build(); shutil.rmtree(os.path.join(FIX, "runs/run-05"))
results.append(expect("**조용한 누락 — 설계했는데 run 이 없다**", "doe_completeness", 1, show=True))

build(); patch("doe.md", "  design_point: {mesh: 0.2, reynolds: 100}\n  status: done",
               "  design_point: {mesh: 0.2, reynolds: 100}\n  status: failed")
results.append(expect("실패인데 `failure_reason:` 이 없다", "doe_completeness", 1, show=True))

build(); patch("doe.md", "  design_point: {mesh: 0.2, reynolds: 100}\n  status: done",
               "  design_point: {mesh: 0.2, reynolds: 100}\n  status: failed\n"
               "  failure_reason: 격자가 너무 성겨 발산했다")
results.append(expect("사유를 적은 실패는 통과(실패를 벌하지 않는다)", "doe_completeness", 0, show=True))

build(); patch("runs/run-02/outputs.json", '"lift"', '"moment"')
results.append(expect("출력 스키마가 run 마다 다르다", "doe_completeness", 1, show=True))

build(); os.remove(os.path.join(FIX, "runs/run-02/outputs.json"))
results.append(expect("성공이라는데 outputs.json 이 없다", "doe_completeness", 1))

build(); patch("doe.md", "  status: done", "  status: pending")
results.append(expect("끝나지 않은 실험(pending)을 결과로", "doe_completeness", 1))

build(); w("runs/run-99/config.json", "{}")
results.append(expect("DOE 에 없는 run(설계 밖의 실행)", "doe_completeness", 1))

print("\n── ⑤ analysis_integrity: 지수 불변식 · 커버리지 · 공시 ──")
build(); patch("analysis.md", '"S_i": 0.62, "S_Ti": 0.71', '"S_i": 0.91, "S_Ti": 0.71')
results.append(expect("**S_i > S_Ti (참 Sobol 이면 불가능)**", "analysis_integrity", 1, show=True))

build(); patch("analysis.md", '"S_i": 0.21, "S_Ti": 0.29', '"S_i": 1.8, "S_Ti": 2.1')
results.append(expect("지수가 [0,1] 밖", "analysis_integrity", 1))

build(); patch("analysis.md",
               '{"name": "reynolds", "S_i": 0.21, "S_Ti": 0.29, "pearson": 0.44, "beta": 0.38}',
               '{"name": "unrelated", "S_i": 0.21, "S_Ti": 0.29, "pearson": 0.44, "beta": 0.38}')
results.append(expect("선언한 독립변수가 분석에서 빠졌다", "analysis_integrity", 1, show=True))

build(); patch("analysis.md", '"n_samples": 24', '"n_samples": 5')
results.append(expect("표본이 하한 미만(지수가 잡음)", "analysis_integrity", 1))

build(); patch("analysis.md", '"notes": "S_i 와 S_Ti 는 표본 분산 기반 근사치다(S_Ti 는 proxy)"',
               '"notes": "mesh 가 지배적이다"')
results.append(expect("**근사 한계를 공시하지 않았다**", "analysis_integrity", 1, show=True))

build(); os.remove(os.path.join(FIX, "data/drag.csv"))
results.append(expect("본문이 인용한 CSV 가 없다", "analysis_integrity", 1, show=True))

build(); patch("figures.md", "figures_generated: false", "figures_generated: true")
results.append(expect("**만들지 않은 그림을 만들었다고 적었다**", "analysis_integrity", 1, show=True))

build(); os.remove(os.path.join(FIX, "figures/plot.py"))
results.append(expect("그림도 없고 plot.py 도 없다(남이 그릴 수 없다)", "analysis_integrity", 1))

build(); patch("figures.md",
               "이 환경에는 matplotlib 이 설치되어 있지 않아 그림을 생성하지 못했다.\n"
               "`figures/plot.py` 와 `data/*.csv` 로 재현할 수 있다.\n", "")
results.append(expect("미생성 사유를 지웠다(공시 없음)", "analysis_integrity", 1))

build(); patch("analysis.md", "```sensitivity", "```sens")
results.append(expect("sensitivity 블록 없음 → fail-closed", "analysis_integrity", 2))

print("\n── ⑥ 설계 판단의 회귀 방어 ──")
build(); patch("analysis.md", '"S_i": 0.62, "S_Ti": 0.71', '"S_i": 0.7150, "S_Ti": 0.71')
results.append(expect("proxy 잡음 수준(0.005)은 통과 — 근사임을 알고 있다",
                      "analysis_integrity", 0))

build(); patch("runs/run-01/outputs/solver.log", "converged in 412 iterations",
               "converged in 999 iterations")
results.append(expect("`*.log` 는 해시 제외 대상(로그가 바뀌어도 통과)", "bit_exact", 0, show=True))

build(); patch("report/report.md", "본 결과는 단일 환경에서 수행된 실험이며 민감도 지수는 근사치입니다.\n"
               "그림은 생성되지 않았고 `plot.py` 로 재현합니다.\n", "")
results.append(expect("보고서 고지 문구 누락", "secret_redaction", 1, draft="report"))

print(f"\n{sum(results)}/{len(results)} 통과")
sys.exit(0 if all(results) else 1)
