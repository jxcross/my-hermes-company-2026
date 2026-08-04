#!/usr/bin/env python3
"""code-migration 3게이트를 '일부러 깨뜨린 픽스처'로 검증한다 (docs/13 §5).
실제 git 저장소를 만들어 SHA 대조까지 확인한다."""
import json, os, shutil, subprocess, sys
import yaml

ROOT = "/work/company"
FIX = "/tmp/mg"
REPO = "/tmp/mg/repo"
GATES = os.path.join(ROOT, "scripts", "gates")


def sh(*args, cwd=None):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)


def build():
    shutil.rmtree(FIX, ignore_errors=True)
    os.makedirs(os.path.join(FIX, "verify"))
    os.makedirs(os.path.join(FIX, "transforms"))
    os.makedirs(os.path.join(REPO, "src"))

    tpl = yaml.safe_load(open(os.path.join(ROOT, "templates", "code-migration.yaml"), encoding="utf-8"))
    json.dump({"policy": tpl["policy"]}, open(os.path.join(FIX, "pipeline.json"), "w"), ensure_ascii=False)

    w = lambda p, s: open(os.path.join(FIX, p), "w", encoding="utf-8").write(s)

    # 실제 git 저장소 — 두 개의 원자 커밋
    sh("git", "init", "-q", REPO)
    sh("git", "config", "user.email", "t@t", cwd=REPO)
    sh("git", "config", "user.name", "t", cwd=REPO)
    open(os.path.join(REPO, "src", "a.py"), "w").write("print 'old'\n")
    open(os.path.join(REPO, "src", "b.py"), "w").write("x = 1/2\n")
    sh("git", "add", "-A", cwd=REPO); sh("git", "commit", "-qm", "init", cwd=REPO)

    open(os.path.join(REPO, "src", "a.py"), "w").write("print('new')\n")
    sh("git", "add", "src/a.py", cwd=REPO)
    sh("git", "commit", "-qm", "migrate(syntax): print 문을 함수 호출로 변환", cwd=REPO)
    sha1 = sh("git", "rev-parse", "HEAD", cwd=REPO).stdout.strip()

    open(os.path.join(REPO, "src", "b.py"), "w").write("x = 1//2\n")
    sh("git", "add", "src/b.py", cwd=REPO)
    sh("git", "commit", "-qm", "migrate(semantics): 정수 나눗셈 연산자 변경", cwd=REPO)
    sha2 = sh("git", "rev-parse", "HEAD", cwd=REPO).stdout.strip()

    w("SCOPE.md", "---\ncodebase: repo\nmigration_types: [version]\n"
                  "test_command: pytest\n---\n# 범위\n")
    w("plan.md", """# 마이그레이션 계획

```steps
- id: s1
  type: syntax
  files: [src/a.py]
  commit_message: "migrate(syntax): print 문을 함수 호출로 변환"
  rollback: git revert s1
  depends_on: []
- id: s2
  type: semantics
  files: [src/b.py]
  commit_message: "migrate(semantics): 정수 나눗셈 연산자 변경"
  rollback: git revert s2
  depends_on: [s1]
```

```intentional
- id: ic1
  change: 정수 나눗셈이 실수 나눗셈에서 바닥 나눗셈으로 바뀐다
  affected: [f2]
```
""")
    w("baseline.md", """# 기준선

n_tests_total: 20
n_passed: 19

```fingerprint
- case: f1
  input: greet()
  output: "hello"
  how: python -c "import src.a"
- case: f2
  input: 1/2
  output: "0.5"
  how: python -c "print(1/2)"
```
""")
    w("transforms/batch-01.md", f"""# 배치 1

```executed
- step_id: s1
  commit_sha: {sha1}
  commit_message: "migrate(syntax): print 문을 함수 호출로 변환"
  files_changed: [src/a.py]
- step_id: s2
  commit_sha: {sha2}
  commit_message: "migrate(semantics): 정수 나눗셈 연산자 변경"
  files_changed: [src/b.py]
```
""")
    w("verify/regression.md", """# 회귀 테스트

n_tests_total_after: 20
n_passed_after: 19
""")
    w("verify/new-test.md", """# 신규 테스트

n_new_tests_added: 3
n_passed: 3
""")
    w("verify/diff.md", """# 행동 차이

checked_cases: 2

```diffs
- entry: f2
  acceptable: yes
  intentional_id: ic1
  reason: 계획에 선언된 정수 나눗셈 변경
```
""")
    return sha1, sha2


def run(gate, draft):
    r = subprocess.run(["python3", os.path.join(GATES, f"{gate}.py"),
                        "--policy", os.path.join(FIX, "pipeline.json"),
                        "--sources", os.path.join(FIX, "raw", "sources.yaml"),
                        "--draft", os.path.join(FIX, draft)],
                       capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def expect(label, gate, draft, want, show=False):
    rc, out = run(gate, draft)
    print(f"{'OK ' if rc == want else '‼️ '}{label:54s} exit={rc} (기대 {want})")
    if rc != want or show:
        print("      " + "\n      ".join(out.splitlines()[-8:]))
    return rc == want


def patch(path, old, new):
    p = os.path.join(FIX, path)
    t = open(p, encoding="utf-8").read()
    assert old in t, f"픽스처 치환 실패: {old!r} not in {path}"
    open(p, "w", encoding="utf-8").write(t.replace(old, new))


results = []
print("── ① 정상 픽스처: 3게이트 모두 PASS ──")
build()
results.append(expect("정상 · atomic_commit(계획 모드)", "atomic_commit", "plan.md", 0, show=True))
results.append(expect("정상 · atomic_commit(실행 모드·git 대조)", "atomic_commit", "transforms", 0, show=True))
results.append(expect("정상 · test_pass_rate", "test_pass_rate", "verify", 0, show=True))
results.append(expect("정상 · behavior_diff", "behavior_diff", "verify", 0, show=True))

print("\n── ② atomic_commit 계획 모드를 깨뜨린다 ──")
build(); patch("plan.md", "  files: [src/b.py]", "  files: [src/a.py]")
results.append(expect("step 간 파일 겹침(개별 revert 불가)", "atomic_commit", "plan.md", 1))

build(); patch("plan.md", '  commit_message: "migrate(syntax): print 문을 함수 호출로 변환"\n', "")
results.append(expect("커밋 메시지 누락 — 원본은 건너뛰었다", "atomic_commit", "plan.md", 1))

build(); patch("plan.md", "  rollback: git revert s2\n", "")
results.append(expect("rollback 미선언", "atomic_commit", "plan.md", 1))

build(); patch("plan.md", '  commit_message: "migrate(semantics): 정수 나눗셈 연산자 변경"',
               '  commit_message: "정수 나눗셈 변경"')
results.append(expect("커밋 메시지 형식 위반", "atomic_commit", "plan.md", 1))

print("\n── ③ atomic_commit 실행 모드를 깨뜨린다(git 대조) ──")
import re as _re
sha1, sha2 = build()
patch("transforms/batch-01.md", sha2, "0" * 40)
results.append(expect("존재하지 않는 SHA — 자기 신고만 믿으면 못 잡는다", "atomic_commit", "transforms", 1))

sha1, sha2 = build()
# 혼합 커밋: 선언되지 않은 파일(src/c.py)을 함께 커밋
open(os.path.join(REPO, "src", "c.py"), "w").write("unrelated = 1\n")
open(os.path.join(REPO, "src", "a.py"), "a").write("# more\n")
sh("git", "add", "-A", cwd=REPO)
sh("git", "commit", "-qm", "migrate(syntax): print 문을 함수 호출로 변환", cwd=REPO)
mixed = sh("git", "rev-parse", "HEAD", cwd=REPO).stdout.strip()
patch("transforms/batch-01.md", sha1, mixed)
results.append(expect("혼합 커밋(선언 외 파일) — 원본은 선언만 했다", "atomic_commit", "transforms", 1))

build(); patch("transforms/batch-01.md", "- step_id: s2\n", "- step_id: s9\n")
results.append(expect("계획에 없는 step 실행(범위 이탈)", "atomic_commit", "transforms", 1))

print("\n── ④ test_pass_rate 를 깨뜨린다 ──")
build(); patch("verify/regression.md", "n_passed_after: 19", "n_passed_after: 18")
results.append(expect("회귀 19→18 — **원본은 임계 95%만 봐서 통과**", "test_pass_rate", "verify", 1))

build(); patch("verify/regression.md", "n_tests_total_after: 20\nn_passed_after: 19",
               "n_tests_total_after: 18\nn_passed_after: 18")
results.append(expect("깨진 테스트를 지워 100% — 분모 자기결정", "test_pass_rate", "verify", 1))

build(); patch("verify/regression.md", "n_passed_after: 19", "")
results.append(expect("필수 수치 누락은 usage 오류(0/0 판정 방지)", "test_pass_rate", "verify", 2))

print("\n── ⑤ behavior_diff 를 깨뜨린다 ──")
build(); patch("verify/diff.md", "  intentional_id: ic1\n", "")
results.append(expect("계획 참조 없는 '괜찮음' — 원본은 자기 신고만 봄", "behavior_diff", "verify", 1))

build(); patch("verify/diff.md", "  intentional_id: ic1", "  intentional_id: ic9")
results.append(expect("계획에 없는 intentional_id 참조", "behavior_diff", "verify", 1))

build(); patch("verify/diff.md", "  acceptable: yes", "  acceptable: no")
results.append(expect("설명되지 않은 행동 변화", "behavior_diff", "verify", 1))

build(); patch("verify/diff.md", "checked_cases: 2", "checked_cases: 1")
results.append(expect("지문 재실행 커버리지 미달(차이 0건 ≠ 통과)", "behavior_diff", "verify", 1))

print("\n── ⑥ 원본 결함의 회귀 방어 ──")
build(); patch("verify/diff.md", "  acceptable: yes", "  acceptable: not yes")
results.append(expect("'not yes' 를 yes 로 오인하지 않는다", "behavior_diff", "verify", 1))

print(f"\n{sum(results)}/{len(results)} 통과")
sys.exit(0 if all(results) else 1)
