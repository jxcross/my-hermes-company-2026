#!/usr/bin/env python3
"""
객관 게이트: 원자 커밋(계획 · 실행)
=====================================
마이그레이션의 각 변환이 **되돌릴 수 있는 단위**로 나뉘어 있는지 LLM 없이 검사한다.
두 지점에서 쓰인다 — `--draft plan.md`(계획 검증) · `--draft transforms/`(실행 검증).
출처: other_projects/harness-templates/.../migrateforge/scripts/atomic_commit_check.py (GATE 3)

⚠️ 이식하며 고친 것 (docs/13 §5):
  1. **커밋 메시지가 비어 있으면 검사를 건너뛰었다** — `if msg and not COMMIT_MSG_RE.match(msg)`.
     `commit_message` 를 아예 안 적으면 형식 검사를 통과한다. → 누락 자체를 FAIL 로.
  2. **자기 신고를 그대로 믿었다** — 원본은 `05-transforms/*.md` 가 적어 낸 SHA 를 셀 뿐
     실제 저장소를 보지 않는다(주석은 "CI/sandbox 를 위해" 라고 설명한다). 우리는 대상
     저장소가 로컬에 있고 `git log` 읽기는 **읽기 전용이라 안전**하므로 실제로 대조한다
     (테스트 실행과 달리 임의 코드 실행 통로가 아니다 — docs/13 §7 의 test_run 주석 참조).
     존재하지 않는 SHA · 선언과 다른 파일을 건드린 커밋을 잡는다.
  3. **혼합 커밋을 실제로는 검사하지 않았다** — docstring 은 "No mixed commits
     (transformation + unrelated changes)" 라고 하지만, 코드는 **같은 SHA 가 두 step 에
     쓰였는지**만 본다. 한 커밋이 무관한 파일을 함께 건드려도 알 수 없다.
     → git 으로 커밋의 실제 변경 파일을 읽어 step 이 선언한 `files:` 와 대조한다.

계획 모드에서 추가로 보는 것 (원본에 없음)
  · 모든 step 에 `files:` 와 `rollback:` 이 선언됐는가(되돌릴 수 없는 계획은 계획이 아니다)
  · step 간 **파일 겹침**이 없는가 — 겹치면 원자성이 깨지고 개별 revert 가 불가능해진다

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.migration_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : plan.md(계획 모드) 또는 transforms/ 디렉터리(실행 모드)

대상 저장소는 미션 루트 `SCOPE.md` frontmatter 의 `codebase:` 에서 읽는다.

기대 형식
  plan.md:        ```steps\n- id: s1\n  type: syntax\n  files: [a.py, b.py]\n
                  commit_message: "migrate(syntax): print 문 변환"\n  rollback: git revert\n```
  transforms/*.md ```executed\n- step_id: s1\n  commit_sha: abc1234\n
                  commit_message: "migrate(syntax): print 문 변환"\n```

정책 필드(migration_policy)
  commit_prefix (기본 migrate) · require_git_verify (기본 true)
  require_rollback (기본 true) · allow_file_overlap (기본 false)

exit: 0 PASS · 1 FAIL · 2 usage/입력없음(fail-closed)
"""
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
import sys

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML 필요", file=sys.stderr); sys.exit(2)

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
STEPS_RE = re.compile(r"```steps\s*\n(.*?)\n```", re.DOTALL)
EXECUTED_RE = re.compile(r"```executed\s*\n(.*?)\n```", re.DOTALL)


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("migration_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("migration_policy", {}) or {}


def scope_field(root: str, key: str):
    try:
        m = FRONTMATTER_RE.match(open(os.path.join(root, "SCOPE.md"), encoding="utf-8").read())
    except OSError:
        return None
    return (yaml.safe_load(m.group(1)) or {}).get(key) if m else None


def parse_items(block: str, id_field: str) -> list[dict]:
    items, current = [], None
    for line in block.splitlines():
        m = re.match(rf"^\s*-\s+{re.escape(id_field)}:\s*(.+)$", line)
        if m:
            if current:
                items.append(current)
            current = {id_field: m.group(1).strip().strip('"\'')}
            continue
        if current is None:
            continue
        mf = re.match(r"^\s+(\w+):\s*(.*)$", line)
        if mf:
            current[mf.group(1)] = mf.group(2).strip().strip('"\'')
    if current:
        items.append(current)
    return items


def as_list(v: str | None) -> list[str]:
    if not v:
        return []
    return [x.strip().strip('"\'') for x in v.strip().strip("[]").split(",") if x.strip()]


def git(repo: str, *args: str) -> tuple[int, str]:
    try:
        r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, timeout=30)
        return r.returncode, r.stdout
    except (OSError, subprocess.SubprocessError) as e:
        return 1, str(e)


def check_plan(steps: list[dict], prefix: str, require_rollback: bool,
               allow_overlap: bool) -> bool:
    fail = False
    msg_re = re.compile(rf"^{re.escape(prefix)}\([\w.\-]+\):\s+\S+")
    seen_files: dict[str, str] = {}
    for s in steps:
        sid = s.get("id", "?")
        msg = s.get("commit_message", "")
        if not msg:
            print(f"FAIL: step {sid} 에 commit_message 가 없다 — 원본은 비어 있으면 형식 "
                  f"검사를 **건너뛰었다**")
            fail = True
        elif not msg_re.match(msg):
            print(f"FAIL: step {sid} 커밋 메시지 형식 위반: {msg[:60]} "
                  f"(기대: `{prefix}(<type>): <설명>`)")
            fail = True
        files = as_list(s.get("files"))
        if not files:
            print(f"FAIL: step {sid} 에 `files:` 선언이 없다 — 무엇을 바꾸는지 모르면 "
                  f"혼합 커밋을 검사할 수 없다")
            fail = True
        if require_rollback and not s.get("rollback"):
            print(f"FAIL: step {sid} 에 `rollback:` 이 없다 — 되돌릴 수 없는 단계는 "
                  f"원자 커밋이 아니다")
            fail = True
        if not allow_overlap:
            for f in files:
                if f in seen_files and seen_files[f] != sid:
                    print(f"FAIL: 파일 겹침 — {f} 를 step {seen_files[f]} 와 {sid} 가 함께 "
                          f"건드린다. 개별 revert 가 불가능해진다(원자성 위반)")
                    fail = True
                seen_files[f] = sid
    return fail


def check_executed(steps: list[dict], executed: list[dict], repo: str | None,
                   prefix: str, verify_git: bool) -> bool:
    fail = False
    msg_re = re.compile(rf"^{re.escape(prefix)}\([\w.\-]+\):\s+\S+")
    planned_ids = {s.get("id") for s in steps}
    exec_ids = {e.get("step_id") for e in executed if e.get("step_id")}

    missing = sorted(planned_ids - exec_ids)
    extra = sorted(exec_ids - planned_ids)
    if missing:
        print(f"FAIL: 계획됐으나 실행되지 않은 step {missing}")
        fail = True
    if extra:
        print(f"FAIL: 계획에 없는 step 이 실행됐다 {extra} — 범위 이탈이다")
        fail = True

    sha_owner: dict[str, str] = {}
    for e in executed:
        sid = e.get("step_id", "?")
        msg = e.get("commit_message", "")
        sha = e.get("commit_sha", "")
        if not msg:
            print(f"FAIL: step {sid} 실행 기록에 commit_message 가 없다")
            fail = True
        elif not msg_re.match(msg):
            print(f"FAIL: step {sid} 커밋 메시지 형식 위반: {msg[:60]}")
            fail = True
        if not sha:
            print(f"FAIL: step {sid} 에 commit_sha 가 없다 — 되돌릴 수 없다")
            fail = True
            continue
        if sha in sha_owner and sha_owner[sha] != sid:
            print(f"FAIL: 커밋 {sha[:8]} 를 step {sha_owner[sha]} 와 {sid} 가 공유한다 "
                  f"(혼합 커밋)")
            fail = True
        sha_owner[sha] = sid

    if verify_git and repo and os.path.isdir(os.path.join(repo, ".git")):
        plan_files = {s.get("id"): set(as_list(s.get("files"))) for s in steps}
        for e in executed:
            sid, sha = e.get("step_id", "?"), e.get("commit_sha", "")
            if not sha:
                continue
            rc, _out = git(repo, "cat-file", "-e", f"{sha}^{{commit}}")
            if rc != 0:
                print(f"FAIL: 커밋 {sha[:8]}(step {sid})가 저장소에 없다 — **자기 신고를 "
                      f"그대로 믿으면 잡을 수 없는 결함이다**")
                fail = True
                continue
            rc, out = git(repo, "show", "--name-only", "--format=", sha)
            touched = {l.strip() for l in out.splitlines() if l.strip()}
            declared = plan_files.get(sid) or set()
            if declared:
                extra_files = sorted(f for f in touched
                                     if not any(f == d or f.endswith("/" + d)
                                                or d.endswith("/" + f) for d in declared))
                if extra_files:
                    print(f"FAIL: 커밋 {sha[:8]}(step {sid})가 선언되지 않은 파일을 함께 "
                          f"바꿨다 {extra_files[:5]} — 혼합 커밋(원본은 이것을 검사한다고 "
                          f"선언만 했다)")
                    fail = True
    elif verify_git:
        print(f"WARNING: 대상 저장소를 찾지 못해 git 대조를 건너뛴다({repo}) — "
              f"자기 신고만 검사했다")
    return fail


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", default=None, help="미사용(gate_keeper 규약상 전달됨)")
    ap.add_argument("--draft", default=None, help="plan.md 또는 transforms/")
    args = ap.parse_args()

    if not args.draft or not os.path.exists(args.draft):
        print("FAIL(usage): --draft(plan.md 또는 transforms/) 필요 — fail-closed", file=sys.stderr)
        return 2
    try:
        policy = load_policy(args.policy)
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e} — fail-closed", file=sys.stderr); return 2

    is_dir = os.path.isdir(args.draft)
    root = os.path.abspath(args.draft) if is_dir else os.path.dirname(os.path.abspath(args.draft))
    if is_dir:
        root = os.path.dirname(root)
    plan_path = os.path.join(root, policy.get("plan_file") or "plan.md")
    if not os.path.isfile(plan_path):
        print(f"FAIL(usage): 계획 문서가 없다({plan_path}) — fail-closed", file=sys.stderr)
        return 2

    m = STEPS_RE.search(open(plan_path, encoding="utf-8").read())
    if not m:
        print(f"FAIL(usage): {os.path.basename(plan_path)} 에 ```steps``` 블록이 없다 "
              f"— fail-closed", file=sys.stderr)
        return 2
    steps = parse_items(m.group(1), "id")
    if not steps:
        print("FAIL(usage): 계획된 변환 step 이 없다 — fail-closed", file=sys.stderr); return 2

    prefix = str(policy.get("commit_prefix") or "migrate")
    require_rollback = bool(policy.get("require_rollback", True))
    allow_overlap = bool(policy.get("allow_file_overlap", False))
    verify_git = bool(policy.get("require_git_verify", True))

    codebase = scope_field(root, "codebase")
    repo = None
    if codebase:
        repo = codebase if os.path.isabs(codebase) else os.path.abspath(os.path.join(root, codebase))

    if not is_dir:
        print(f"[계획 모드] 변환 step {len(steps)}개 · 커밋 접두 `{prefix}` "
              f"· 롤백 필수={require_rollback}")
        fail = check_plan(steps, prefix, require_rollback, allow_overlap)
    else:
        executed = []
        for f in sorted(os.listdir(args.draft)):
            if not f.endswith(".md"):
                continue
            em = EXECUTED_RE.search(open(os.path.join(args.draft, f), encoding="utf-8").read())
            if em:
                executed += parse_items(em.group(1), "step_id")
        print(f"[실행 모드] 계획 {len(steps)}개 · 실행 기록 {len(executed)}개 "
              f"· git 대조={verify_git} · 저장소={repo}")
        if not executed:
            print("FAIL: 실행 기록이 하나도 없다 — ```executed``` 블록이 필요하다")
            fail = True
        else:
            fail = check_executed(steps, executed, repo, prefix, verify_git)

    if not fail:
        print("  ✓ 원자 커밋 규율 충족")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
