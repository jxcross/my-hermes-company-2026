#!/usr/bin/env python3
r"""
객관 게이트: 솔버·환경 고정 (계획 모드 / 실행 모드)
====================================================
실험에 쓴 솔버와 환경이 **다시 세울 수 있을 만큼 고정**됐는지, 그리고 **선언한 솔버로
실제로 돌았는지** LLM 없이 검사한다.
출처: simforge 의 Gate 1(environment-audit) — **스크립트가 없다**(LLM 크리틱뿐). 신설.

두 모드로 돈다(아키타입 K 의 `atomic_commit` 과 같은 방식):
  · **계획 모드** — `runs/` 가 아직 없으면 `solver.md` 의 고정 선언만 본다(실행 전 검증).
  · **실행 모드** — `runs/` 가 있으면 **모든 `runs/<id>/config.json` 이 선언과 같은
    솔버·버전인지** 대조한다.

⚠️ **원본 CLAUDE.md 가 선언한 규약이 아무 데서도 강제되지 않는다**(docs/13 §5 계열):
     · "Every `runs/<id>/config.json` MUST include `solver_version`, `solver_commit`
       (or container hash), and `seed`"
     · "**02-solver.md is the source of truth** for what version was used;
       downstream cannot change solver mid-pipeline"
   Gate 1 의 판정자는 LLM 크리틱 하나이고 검사 코드는 없다. 그래서 run 마다 다른 솔버
   버전이 적혀 있어도, 파이프라인 중간에 솔버가 바뀌어도 아무도 모른다.
   → 선언 ↔ 전 run 대조를 코드로 옮겼다.

⚠️ **핀 되지 않은 태그를 막는다**(아키타입 O 에서 배운 것). `latest`·`main`·`HEAD`·
   `stable` 은 시점마다 다른 것을 가리키므로 고정이 아니다. 원격 솔버(EDISON 등)는
   **사람이 읽는 태그가 아니라 실제 배포 이미지 해시**를 요구한다(원본 CLAUDE.md 도
   "the actual deployed image hash, not just the human-readable tag" 라고 적었다).

⚠️ **인증 토큰은 이름만 적는다.** `auth.env_var: EDISON_API_TOKEN` 은 되고 값은 안 된다 —
   이 저장소는 PUBLIC 이다(`secret_redaction` 이 커밋 대상을 따로 훑지만, 여기서도 막는다).

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.solver_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : 미션 디렉터리

기대 형식 (solver.md · frontmatter 또는 본문 `키: 값`)
  solver_name: openfoam
  solver_version: 11.0
  solver_commit: 3f2a91c        # 또는 image_hash: sha256:...
  deps_lock: env/requirements.txt
  hardware: 16-core x86_64 / OpenMPI 4.1.5
  solver_type: local            # local | remote
  # remote 인 경우
  endpoint: https://.../api
  app_version: v2.3
  auth_env_var: EDISON_API_TOKEN

정책 필드(solver_policy)
  require_fields (기본 [solver_name, solver_version, deps_lock, hardware])
  unpinned_tags (기본 [latest, main, head, stable, dev, nightly])
  require_remote_fields (기본 [endpoint, app_version, image_hash, auth_env_var])
  require_deps_lock_exists (기본 true) · cross_check_runs (기본 true)

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
DEFAULT_FIELDS = ["solver_name", "solver_version", "deps_lock", "hardware"]
DEFAULT_UNPINNED = ["latest", "main", "head", "stable", "dev", "nightly"]
DEFAULT_REMOTE = ["endpoint", "app_version", "image_hash", "auth_env_var"]
# 토큰처럼 보이는 값(이름이 아니라 값이 적힌 경우)
TOKEN_VALUE_RE = re.compile(r"(?i)\b(?:token|secret|api[_-]?key|password)\s*:\s*"
                            r"[\"']?([A-Za-z0-9/+_\-]{20,})[\"']?")


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("solver_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("solver_policy", {}) or {}


def mission_root(draft: str) -> str:
    p = os.path.abspath(draft)
    return p if os.path.isdir(p) else os.path.dirname(p)


def field(text: str, key: str) -> str | None:
    m = re.search(rf"^\s*{re.escape(key)}\s*:\s*(\S.*?)\s*$", text, re.MULTILINE)
    return m.group(1).strip().strip('"\'') if m else None


def is_unpinned(value: str, unpinned: list[str]) -> bool:
    v = str(value).strip().lower().lstrip("v")
    return v in [u.lower() for u in unpinned] or any(
        v.endswith(f"-{u.lower()}") or v.endswith(f":{u.lower()}") for u in unpinned)


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
    spath = None
    for n in ("solver.md", "02-solver.md"):
        p = os.path.join(root, n)
        if os.path.isfile(p):
            spath = p
            break
    if not spath:
        print(f"FAIL(usage): solver.md 를 찾지 못했다({root}) — 무엇으로 돌리는지 고정하지 "
              f"않으면 재현할 수 없다. fail-closed", file=sys.stderr)
        return 2

    text = open(spath, encoding="utf-8").read()
    fields = policy.get("require_fields") or DEFAULT_FIELDS
    unpinned = policy.get("unpinned_tags") or DEFAULT_UNPINNED
    remote_fields = policy.get("require_remote_fields") or DEFAULT_REMOTE
    require_lock = bool(policy.get("require_deps_lock_exists", True))
    cross_check = bool(policy.get("cross_check_runs", True))

    runs_dir = os.path.join(root, "runs")
    run_ids = sorted(n for n in os.listdir(runs_dir)) if os.path.isdir(runs_dir) else []
    run_ids = [r for r in run_ids if os.path.isdir(os.path.join(runs_dir, r))]
    mode = "실행" if run_ids else "계획"
    print(f"솔버 고정 검사 [{mode} 모드] · {os.path.basename(spath)} · run {len(run_ids)}건")

    fail = False
    vals = {k: field(text, k) for k in fields}
    missing = [k for k, v in vals.items() if not v]
    if missing:
        print(f"FAIL: 고정 선언 누락 {missing} — **원본 Gate 1 의 판정자는 LLM 크리틱 하나이고 "
              f"검사 코드가 없다**")
        fail = True

    commit = field(text, "solver_commit")
    image = field(text, "image_hash")
    if not commit and not image:
        print("FAIL: `solver_commit` 도 `image_hash` 도 없다 — 버전 문자열만으로는 같은 "
              "빌드를 다시 세울 수 없다")
        fail = True

    for key in ("solver_version", "solver_commit", "image_hash", "app_version"):
        v = field(text, key)
        if v and is_unpinned(v, unpinned):
            print(f"FAIL: `{key}: {v}` 는 핀 되지 않은 태그다 — 같은 이름이 시점마다 다른 "
                  f"것을 가리킨다({unpinned[:3]}…)")
            fail = True

    if require_lock:
        lock = field(text, "deps_lock")
        if lock:
            lp = lock if os.path.isabs(lock) else os.path.join(root, lock)
            if not os.path.isfile(lp):
                print(f"FAIL: `deps_lock: {lock}` 파일이 실재하지 않는다 — 선언만 하고 "
                      f"의존성을 고정하지 않았다")
                fail = True

    stype = (field(text, "solver_type") or "local").lower()
    if stype == "remote":
        rmissing = [k for k in remote_fields if not field(text, k)]
        if rmissing:
            print(f"FAIL: 원격 솔버인데 {rmissing} 가 없다 — 원본도 '**the actual deployed "
                  f"image hash, not just the human-readable tag**' 를 요구한다")
            fail = True

    hits = TOKEN_VALUE_RE.findall(text)
    if hits:
        print(f"FAIL: 인증 토큰 값이 적혀 있다({len(hits)}건) — 이 저장소는 PUBLIC 이다. "
              f"`auth_env_var: EDISON_API_TOKEN` 처럼 **이름만** 적어라")
        fail = True

    # 실행 모드 — 선언 ↔ 전 run 대조
    if cross_check and run_ids:
        want_ver = field(text, "solver_version")
        want_id = commit or image
        bad_ver, bad_id, no_cfg = [], [], []
        for rid in run_ids:
            cp = os.path.join(runs_dir, rid, "config.json")
            if not os.path.isfile(cp):
                no_cfg.append(rid)
                continue
            try:
                cfg = json.loads(open(cp, encoding="utf-8").read())
            except (OSError, json.JSONDecodeError):
                no_cfg.append(rid)
                continue
            if str(cfg.get("status", "done")).lower() == "failed":
                continue
            if want_ver and str(cfg.get("solver_version", "")).strip() != want_ver:
                bad_ver.append((rid, cfg.get("solver_version")))
            got_id = str(cfg.get("solver_commit") or cfg.get("image_hash") or "").strip()
            if want_id and got_id != want_id:
                bad_id.append((rid, got_id or "없음"))
        if no_cfg:
            print(f"FAIL: config.json 이 없거나 깨진 run {no_cfg[:6]}")
            fail = True
        if bad_ver:
            print(f"FAIL: 선언 `solver_version: {want_ver}` 과 다른 run {bad_ver[:6]} — "
                  f"**파이프라인 중간에 솔버가 바뀌었다.** 원본은 'solver.md 가 source of "
                  f"truth' 라고 선언만 하고 대조하지 않았다")
            fail = True
        if bad_id:
            print(f"FAIL: 선언 커밋/이미지({want_id[:16]}…)와 다른 run {bad_id[:4]}")
            fail = True
        if not (bad_ver or bad_id or no_cfg):
            print(f"  ✓ run {len(run_ids)}건 전부가 선언한 솔버 {want_ver}"
                  f"({(want_id or '')[:12]}…)로 돌았다")

    if not fail:
        print(f"  ✓ 솔버·버전·커밋/이미지·의존성 lock·하드웨어가 고정됐고 핀 되지 않은 "
              f"태그가 없다")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
