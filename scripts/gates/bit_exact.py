#!/usr/bin/env python3
r"""
객관 게이트: 출력 해시 무결성 + 입력 드리프트
==============================================
각 run 의 `output.hash` 가 **실제 outputs/ 의 해시와 맞는지**, 그리고 각 run 의 입력이
**DOE 가 지시한 설계점과 같은지** LLM 없이 검사한다.
출처: other_projects/harness-templates/.../simforge/scripts/{bit_exact_check,hash_outputs}.py (Gate 2)

⚠️ **원본은 `output.hash` 의 존재만 확인한다** (docs/13 §5 · 실측). 파일 안의 값이 실제
   출력과 맞는지는 보지 않는다. 실측: `outputs/out.json` 에 실제 데이터가 있고
   `output.hash` 에 **0 을 64자 적어 넣어도** `no hash-mode issues · PASS · exit=0`.
   재현성 게이트의 해시가 **아무것도 가리키지 않는 장식**이다.
   → 우리는 `outputs/` 를 실제로 읽어 **같은 알고리즘으로 다시 계산해 대조**한다.
     파일을 읽는 것은 코드 실행이 아니므로 게이트가 해도 안전하다(솔버 재실행과 다르다).

⚠️ **`--doe` 는 선언만 되고 한 번도 쓰이지 않는다**(실측). docstring 은
   "run_inputs hash matches the input recorded in 03-doe.md (**no input drift**)" 라 하고
   argparse 에도 `--doe` 가 `help="optional: 03-doe.md for input drift check"` 로 들어 있는데,
   **`args.doe` 를 참조하는 코드가 없다.** 존재하지 않는 경로를 줘도 아무 말이 없다.
   migrateforge 의 죽은 변수 · agentforge 의 죽은 gold-set 대조와 같은 계열이되,
   **CLI 옵션으로 광고까지 한다**는 점에서 가장 그럴듯하다.
   → `design_point` ↔ `inputs.json` 을 실제로 대조한다.

⚠️ **run 이 하나도 없으면 PASS 였다**(실측 · `scanned 0 runs · PASS`). 공집합이 통과하는
   계열의 여섯 번째 사례다.

⚠️ **이 게이트는 솔버를 재실행하지 않는다.** 원본 `replay_check` 는 `run.sh` 를 실행하고
   **원본 outputs/ 를 덮어쓴다**(실패하면 원본이 손상된다). 게이트키퍼가 미션 코드를 돌리면
   임의 코드 실행 통로가 된다(docs/13 §7). 재실행은 Tester 의 일이고 여기서는
   `output.replay.hash` 기록을 검사한다.

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.repro_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : 미션 디렉터리

정책 필드(repro_policy)
  exclude (기본 *.log,*.tmp,timestamp.txt,*.pyc) — 해시에서 제외할 glob
  require_replay (기본 true) · min_replays (기본 1)
  tolerance (기본 bit-exact) — bit-exact 이면 해시 문자열 일치를 요구
  require_config_fields (기본 [solver_version, seed])

exit: 0 PASS · 1 FAIL · 2 usage/입력없음(fail-closed)
"""
from __future__ import annotations
import argparse
import fnmatch
import hashlib
import json
import os
import re
import sys

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML 필요", file=sys.stderr); sys.exit(2)

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
RUNS_BLOCK_RE = re.compile(r"```runs\s*\n(.*?)\n```", re.DOTALL)
RUN_ID_RE = re.compile(r"^\s*-\s*id:\s*(\S+)", re.MULTILINE)
DESIGN_POINT_RE = re.compile(r"^\s+design_point:\s*\{(.*?)\}\s*$", re.MULTILINE)
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
DEFAULT_EXCLUDE = ["*.log", "*.tmp", "timestamp.txt", "*.pyc"]


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("repro_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("repro_policy", {}) or {}


def mission_root(draft: str) -> str:
    p = os.path.abspath(draft)
    return p if os.path.isdir(p) else os.path.dirname(p)


def file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_directory(root: str, exclude: list[str]) -> str:
    """원본 `hash_outputs.py` 와 **같은 알고리즘** — 상대경로 정렬 후 (path\\0digest\\n) 누적."""
    files = []
    for dirpath, _dirs, names in os.walk(root):
        for n in names:
            p = os.path.join(dirpath, n)
            rel = os.path.relpath(p, root).replace(os.sep, "/")
            if any(fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(n, pat) for pat in exclude):
                continue
            files.append((rel, p))
    files.sort(key=lambda t: t[0])
    agg = hashlib.sha256()
    for rel, p in files:
        agg.update(rel.encode("utf-8")); agg.update(b"\0")
        agg.update(file_sha256(p).encode("ascii")); agg.update(b"\n")
    return agg.hexdigest()


def parse_doe(root: str) -> dict[str, dict]:
    """{run_id: {파라미터: 값}} — DOE 의 ```runs``` 블록."""
    for name in ("doe.md", "03-doe.md"):
        p = os.path.join(root, name)
        if not os.path.isfile(p):
            continue
        m = RUNS_BLOCK_RE.search(open(p, encoding="utf-8").read())
        if not m:
            return {}
        block = m.group(1)
        starts = list(RUN_ID_RE.finditer(block))
        out = {}
        for i, s in enumerate(starts):
            body = block[s.end():(starts[i + 1].start() if i + 1 < len(starts) else len(block))]
            dp = {}
            dm = DESIGN_POINT_RE.search(body)
            if dm:
                for pair in dm.group(1).split(","):
                    if ":" in pair:
                        k, v = pair.split(":", 1)
                        dp[k.strip()] = v.strip()
            out[s.group(1).strip()] = dp
        return out
    return {}


def num_eq(a, b) -> bool:
    try:
        return abs(float(a) - float(b)) <= 1e-12 * max(1.0, abs(float(a)))
    except (TypeError, ValueError):
        return str(a).strip() == str(b).strip()


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
    runs_dir = os.path.join(root, "runs")
    if not os.path.isdir(runs_dir):
        print(f"FAIL(usage): runs/ 가 없다({runs_dir}) — fail-closed", file=sys.stderr)
        return 2
    run_ids = sorted(n for n in os.listdir(runs_dir)
                     if os.path.isdir(os.path.join(runs_dir, n)))
    if not run_ids:
        print(f"FAIL(usage): run 이 하나도 없다 — **원본은 `scanned 0 runs · PASS` 였다**. "
              f"시뮬레이션을 돌리지 않은 것은 재현 가능한 것이 아니다. fail-closed",
              file=sys.stderr)
        return 2

    exclude = policy.get("exclude") or DEFAULT_EXCLUDE
    require_replay = bool(policy.get("require_replay", True))
    min_replays = int(policy.get("min_replays", 1))
    tolerance = str(policy.get("tolerance", "bit-exact"))
    req_fields = policy.get("require_config_fields") or ["solver_version", "seed"]

    doe = parse_doe(root)
    if not doe:
        print(f"FAIL(usage): doe.md 의 ```runs``` 블록을 찾지 못했다 — 입력 드리프트를 "
              f"대조할 기준이 없다(**원본은 `--doe` 를 받기만 하고 쓰지 않았다**). "
              f"fail-closed", file=sys.stderr)
        return 2

    print(f"run {len(run_ids)}건 · DOE 설계점 {len(doe)}건 · 허용오차 {tolerance} · "
          f"해시 제외 {exclude}")
    issues: list[str] = []
    n_replays = 0

    for rid in run_ids:
        rd = os.path.join(runs_dir, rid)
        cfg_p = os.path.join(rd, "config.json")
        if not os.path.isfile(cfg_p):
            issues.append(f"{rid}: config.json 이 없다")
            continue
        try:
            cfg = json.loads(open(cfg_p, encoding="utf-8").read())
        except (OSError, json.JSONDecodeError) as e:
            issues.append(f"{rid}: config.json 을 읽을 수 없다 ({e})")
            continue
        if str(cfg.get("status", "done")).lower() == "failed":
            print(f"  · {rid}: status=failed — 해시 검사 제외(회계는 doe_completeness 가 본다)")
            continue

        for f in req_fields:
            if f not in cfg or cfg[f] in (None, ""):
                issues.append(f"{rid}: config 에 {f!r} 가 없다")
        if not (cfg.get("solver_commit") or cfg.get("image_hash")):
            issues.append(f"{rid}: `solver_commit` 도 `image_hash` 도 없다 — 무엇으로 돌렸는지 "
                          f"알 수 없다")

        # ① 출력 해시를 **다시 계산해 대조**(원본은 존재만 확인했다)
        out_dir = os.path.join(rd, "outputs")
        hash_p = os.path.join(rd, "output.hash")
        if not os.path.isdir(out_dir):
            issues.append(f"{rid}: outputs/ 가 없다")
        elif not os.path.isfile(hash_p):
            issues.append(f"{rid}: output.hash 가 없다")
        else:
            recorded = open(hash_p, encoding="utf-8").read().strip().split()[0] \
                if open(hash_p, encoding="utf-8").read().strip() else ""
            actual = hash_directory(out_dir, exclude)
            if not HEX64_RE.match(recorded):
                issues.append(f"{rid}: output.hash 가 sha256 형식이 아니다({recorded[:16]}…)")
            elif recorded != actual:
                issues.append(f"{rid}: output.hash 가 실제 출력과 다르다 — "
                              f"기록 {recorded[:16]}… vs 실제 {actual[:16]}… "
                              f"**원본은 파일 존재만 보고 값을 대조하지 않았다**(0 을 64자 "
                              f"적어 넣어도 통과했다)")
            else:
                # ② 재실행 증거(있으면) — 게이트가 직접 돌리지는 않는다
                rp = os.path.join(rd, "output.replay.hash")
                if os.path.isfile(rp):
                    replay = open(rp, encoding="utf-8").read().strip().split()[0]
                    if tolerance == "bit-exact" and replay != recorded:
                        issues.append(f"{rid}: 재실행 해시 불일치(bit-exact) — "
                                      f"{recorded[:16]}… vs {replay[:16]}…")
                    elif not HEX64_RE.match(replay):
                        issues.append(f"{rid}: output.replay.hash 가 sha256 형식이 아니다")
                    else:
                        n_replays += 1

        # ③ 입력 드리프트 — 원본이 광고만 하던 검사
        inp_p = os.path.join(rd, "inputs.json")
        dp = doe.get(rid)
        if dp is None:
            issues.append(f"{rid}: DOE 에 없는 run 이다(설계 밖의 실행)")
        elif not os.path.isfile(inp_p):
            issues.append(f"{rid}: inputs.json 이 없다 — 무엇을 넣었는지 알 수 없다")
        elif dp:
            try:
                inp = json.loads(open(inp_p, encoding="utf-8").read())
            except (OSError, json.JSONDecodeError) as e:
                issues.append(f"{rid}: inputs.json 을 읽을 수 없다 ({e})")
            else:
                for k, v in dp.items():
                    if k not in inp:
                        issues.append(f"{rid}: DOE 설계점의 {k!r} 가 inputs.json 에 없다")
                    elif not num_eq(inp[k], v):
                        issues.append(f"{rid}: **입력 드리프트** {k}: DOE {v} vs 실제 {inp[k]} "
                                      f"— 설계와 다른 값으로 돌린 결과다")

    if require_replay and n_replays < min_replays:
        issues.append(f"허용오차 안에서 재현된 run 이 {n_replays}건 < 하한 {min_replays} — "
                      f"`runs/<id>/output.replay.hash` 에 재실행 해시를 남겨라. "
                      f"⚠️ 이 게이트는 솔버를 직접 실행하지 않는다(임의 코드 실행 통로가 "
                      f"되고, 원본은 재실행 중 원본 outputs/ 를 덮어썼다)")

    if issues:
        print(f"FAIL: 재현성 문제 {len(issues)}건")
        for i in issues[:20]:
            print(f"       · {i}")
        if len(issues) > 20:
            print(f"       … 외 {len(issues) - 20}건")
    else:
        print(f"  ✓ 전 run 의 output.hash 가 실제 출력과 일치하고, 입력이 DOE 설계점과 "
              f"같으며, 재실행이 재현됐다({n_replays}건)")
    print("VERDICT:", "FAIL" if issues else "PASS")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
