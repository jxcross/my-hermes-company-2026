#!/usr/bin/env python3
"""
객관 게이트: 실험 매트릭스의 완결성(선언 ↔ 실재)
=================================================
`design.md` 가 **선언한** 시스템 × seed 조합이 실제로 **전부 돌았는지**, 구현물이 있는지,
run 이 자기 라벨과 일치하는지 LLM 없이 검사한다.
출처: agentforge 에는 이 검사가 **없다**(신설).

⚠️ **원본은 실패한 run 을 조용히 빼고 진행한다.** SKILL.md Stage 7:
   "Runs returning `failed` … are excluded from synthesis (**gates may still pass with
   remaining runs if min N met**)". 즉 proposed 의 seed 3개 중 2개가 실패해도 남은 1개로
   통계 게이트를 통과할 수 있다. **재현성 목적으로 seed 를 여러 개 돌려 놓고, 잘 나온
   seed 만 남기면** 그 목적이 사라진다.
   → baseline·proposed 는 선언한 seed 전건이 성공해야 한다(`max_failed_ratio` 기본 0).

⚠️ **병렬 산출물은 "선언 목록 대비 존재"를 항상 확인한다** (docs/13 §5 — policy-brief 의
   `formats/*.md` glob 함정, patent_format 의 `jurisdictions` 검사와 같은 패턴).
   stage 7·8 은 시스템마다·run 마다 subagent 를 띄운다. 워커 하나가 통째로 죽으면
   `runs/*` 를 glob 하는 검사는 **검사할 것이 없어 통과**한다.

⚠️ **run 디렉터리 이름과 config 내용을 대조한다.** `proposed__seed11/config.json` 안에
   `"system": "baseline"` 이 들어 있으면 통계 게이트가 엉뚱한 짝을 비교한다. 라벨은
   두 곳에 있으므로 어긋날 수 있고, 어긋난 채로도 각각은 잘 파싱된다.

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.run_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : 미션 디렉터리(design.md · runs/ · src/ 를 담은 곳)

기대 형식 (design.md)
  seeds: [11, 22, 33]

  ```systems
  - id: baseline
    role: baseline
    description: 단순 top-k 검색 + 생성
  - id: proposed
    role: proposed
    description: 하이브리드 검색 + 리랭커
  - id: abl-no-rerank
    role: ablation
    change: 리랭커 제거
  ```

run 디렉터리 이름 규약: `runs/<system_id>__seed<seed>/`

정책 필드(run_policy)
  seeds (design.md 선언이 없을 때의 기본) · min_seeds (기본 3) · min_ablations (기본 1)
  max_failed_ratio (기본 0.0) · strict_roles (기본 [baseline, proposed])
  require_src (기본 true) · allow_undeclared_runs (기본 false)

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
SYSTEMS_BLOCK_RE = re.compile(r"```systems\s*\n(.*?)\n```", re.DOTALL)
SEEDS_RE = re.compile(r"^\s*seeds\s*:\s*\[([^\]]*)\]", re.MULTILINE)
RUN_NAME_RE = re.compile(r"^(?P<sys>.+?)__seed(?P<seed>-?\d+)$")


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("run_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("run_policy", {}) or {}


def mission_root(draft: str) -> str:
    p = os.path.abspath(draft)
    return p if os.path.isdir(p) else os.path.dirname(p)


def find_design(root: str) -> str | None:
    for name in ("design.md", "04-agent-design.md"):
        p = os.path.join(root, name)
        if os.path.isfile(p):
            return p
    return None


def parse_systems(block: str) -> list[dict]:
    items, cur = [], None
    for line in block.splitlines():
        mi = re.match(r"^\s*-\s+id:\s*(\S+)", line)
        if mi:
            if cur:
                items.append(cur)
            cur = {"id": mi.group(1).strip()}
            continue
        if cur is None:
            continue
        mf = re.match(r"^\s+(\w+):\s*(.*)$", line)
        if mf:
            cur[mf.group(1)] = mf.group(2).strip().strip('"\'')
    if cur:
        items.append(cur)
    return items


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
    design = find_design(root)
    if not design:
        print(f"FAIL(usage): design.md 를 찾지 못했다({root}) — 무엇을 돌리기로 했는지 "
              f"모르면 다 돌았는지도 알 수 없다. fail-closed", file=sys.stderr)
        return 2
    text = open(design, encoding="utf-8").read()
    mb = SYSTEMS_BLOCK_RE.search(text)
    if not mb:
        print(f"FAIL(usage): design.md 에 ```systems``` 블록이 없다 — fail-closed",
              file=sys.stderr)
        return 2
    systems = parse_systems(mb.group(1))
    if not systems:
        print("FAIL(usage): ```systems``` 블록이 비었다 — fail-closed", file=sys.stderr)
        return 2

    ms = SEEDS_RE.search(text)
    if ms:
        seeds = [s.strip() for s in ms.group(1).split(",") if s.strip()]
    else:
        seeds = [str(s) for s in (policy.get("seeds") or [])]
    min_seeds = int(policy.get("min_seeds", 3))
    min_abl = int(policy.get("min_ablations", 1))
    max_failed = float(policy.get("max_failed_ratio", 0.0))
    strict_roles = [str(r).lower() for r in (policy.get("strict_roles") or ["baseline", "proposed"])]
    require_src = bool(policy.get("require_src", True))
    allow_undeclared = bool(policy.get("allow_undeclared_runs", False))

    fail = False
    roles: dict[str, list[str]] = {}
    for s in systems:
        roles.setdefault(str(s.get("role", "")).lower(), []).append(s["id"])
    print(f"선언 시스템 {len(systems)}종 · seed {seeds or '(없음)'} · "
          f"역할 {[(k or '없음', len(v)) for k, v in sorted(roles.items())]}")

    # ① 비교 설계의 형태
    for role in ("baseline", "proposed"):
        if len(roles.get(role, [])) != 1:
            print(f"FAIL: role={role} 인 시스템이 {len(roles.get(role, []))}개 — 정확히 1개여야 "
                  f"비교가 성립한다")
            fail = True
    n_abl = len(roles.get("ablation", []))
    if n_abl < min_abl:
        print(f"FAIL: ablation {n_abl}종 < 하한 {min_abl} — 무엇이 개선을 만들었는지 "
              f"가릴 수 없다")
        fail = True
    for s in systems:
        if str(s.get("role", "")).lower() == "ablation" and not str(s.get("change", "")).strip():
            print(f"FAIL: ablation {s['id']} 에 `change:` 가 없다 — 무엇 하나를 뺐는지 "
                  f"적히지 않은 ablation 은 해석할 수 없다")
            fail = True
    dup = sorted({s["id"] for s in systems if [x["id"] for x in systems].count(s["id"]) > 1})
    if dup:
        print(f"FAIL: 중복 system_id {dup}")
        fail = True
    unknown_role = [s["id"] for s in systems
                    if str(s.get("role", "")).lower() not in ("baseline", "proposed", "ablation")]
    if unknown_role:
        print(f"FAIL: role 이 없거나 알 수 없는 시스템 {unknown_role} "
              f"(baseline|proposed|ablation)")
        fail = True

    # ② seed
    if not seeds:
        print(f"FAIL: seed 선언이 없다 — design.md 에 `seeds: [11, 22, 33]` 를 적거나 "
              f"정책에 두어라. seed 없는 실험은 재현성을 주장할 수 없다")
        fail = True
    elif len(set(seeds)) < min_seeds:
        print(f"FAIL: seed {len(set(seeds))}개 < 하한 {min_seeds} — seed 1개는 "
              f"운과 개선을 구별하지 못한다")
        fail = True

    # ③ 구현물
    if require_src:
        for s in systems:
            d = os.path.join(root, "src", s["id"])
            if not os.path.isdir(d):
                print(f"FAIL: src/{s['id']}/ 가 없다 — 선언만 하고 구현하지 않은 시스템이다 "
                      f"(stage 7 의 병렬 워커 하나가 죽으면 이렇게 된다)")
                fail = True

    # ④ 실험 매트릭스: 선언 ↔ 실재
    runs_dir = os.path.join(root, "runs")
    actual: dict[str, dict] = {}
    if os.path.isdir(runs_dir):
        for name in sorted(os.listdir(runs_dir)):
            rd = os.path.join(runs_dir, name)
            if not os.path.isdir(rd):
                continue
            cfg = {}
            cp = os.path.join(rd, "config.json")
            if os.path.isfile(cp):
                try:
                    cfg = json.loads(open(cp, encoding="utf-8").read())
                except (OSError, json.JSONDecodeError):
                    cfg = {}
            actual[name] = cfg

    expected = [f"{s['id']}__seed{seed}" for s in systems for seed in seeds]
    missing = [r for r in expected if r not in actual]
    if missing:
        print(f"FAIL: 선언했지만 실행되지 않은 run {len(missing)}건 {missing[:6]} — "
              f"**glob 만 하는 검사는 '검사할 것이 없어' 통과한다**")
        fail = True

    undeclared = [r for r in actual if r not in expected]
    if undeclared:
        msg = (f"선언에 없는 run {len(undeclared)}건 {undeclared[:6]} — 매트릭스 밖의 run 은 "
               f"결과 선택의 여지를 만든다")
        if allow_undeclared:
            print(f"참고: {msg}")
        else:
            print(f"FAIL: {msg}")
            fail = True

    # ⑤ 라벨 일치 · 실패율
    failed_by_sys: dict[str, int] = {}
    total_by_sys: dict[str, int] = {}
    for name, cfg in sorted(actual.items()):
        m = RUN_NAME_RE.match(name)
        if not m:
            print(f"FAIL: run 이름 {name!r} 이 `<system_id>__seed<seed>` 규약에 맞지 않는다")
            fail = True
            continue
        sysid, seed = m.group("sys"), m.group("seed")
        if not cfg:
            print(f"FAIL: {name}: config.json 이 없거나 깨졌다")
            fail = True
            continue
        if str(cfg.get("system", sysid)) != sysid:
            print(f"FAIL: {name}: config.system={cfg.get('system')!r} 이 디렉터리 이름의 "
                  f"{sysid!r} 와 다르다 — 통계 게이트가 엉뚱한 짝을 비교하게 된다")
            fail = True
        if str(cfg.get("seed", seed)) != seed:
            print(f"FAIL: {name}: config.seed={cfg.get('seed')!r} 이 디렉터리 이름의 "
                  f"{seed!r} 와 다르다")
            fail = True
        total_by_sys[sysid] = total_by_sys.get(sysid, 0) + 1
        if str(cfg.get("status", "complete")).lower() == "failed":
            failed_by_sys[sysid] = failed_by_sys.get(sysid, 0) + 1

    for s in systems:
        sid, role = s["id"], str(s.get("role", "")).lower()
        tot = total_by_sys.get(sid, 0)
        bad = failed_by_sys.get(sid, 0)
        if not tot:
            continue
        ratio = bad / tot
        mark = "✓" if not bad else "✗"
        print(f"  {sid:22s} role={role:9s} run {tot}건 · 실패 {bad}건 ({ratio:.0%}) {mark}")
        if role in strict_roles and ratio > max_failed:
            print(f"FAIL: {sid}({role}) 의 실패 run 비율 {ratio:.0%} > 허용 {max_failed:.0%} — "
                  f"**원본은 실패 run 을 집계에서 빼고 남은 것으로 게이트를 통과시켰다.** "
                  f"seed 를 여러 개 돌리는 이유가 사라진다")
            fail = True

    if not fail:
        print(f"  ✓ 선언한 {len(systems)}시스템 × seed {len(seeds)}개 = {len(expected)}건이 "
              f"전부 실행됐고 라벨이 일치한다")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
