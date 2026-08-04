#!/usr/bin/env python3
"""
객관 게이트: 재현성(결정성 + 재실행 증거)
=========================================
평가 run 이 **다시 돌렸을 때 같은 수를 낼 수 있게 기록됐는지** LLM 없이 검사한다 —
seed·모델 버전·temperature 기록 · 예측 산출물의 실재와 분량 · 재실행 증거의 표류.
출처: other_projects/harness-templates/.../agentforge/scripts/repro_check.py (GATE 3)

⚠️ **원본은 세 곳에서 fail-open 이다** (docs/13 §5 — secforge 게이트 3종과 같은 계열).
   실측:
     · `runs/` 가 **비어 있으면** `scanned 0 runs · no determinism issues · PASS · exit=0`.
       **평가를 한 번도 돌리지 않은 것이 "재현 가능"으로 판정된다.**
     · `raw.jsonl` 이 없으면 `if raw_path.is_file():` 로 **검사를 건너뛴다** → PASS.
     · `metrics.json` 이 없어도 마찬가지로 통과한다.
   → 전부 fail-closed 로 뒤집었다. 보안 도메인에서 배운 것과 같다 —
     **"데이터가 없다"는 "문제가 없다"가 아니다.**

⚠️ **docstring 이 말한 gold set 대조가 코드에 없다** (behavior_diff 의 죽은 변수와 같은 계열).
   원본 docstring: "raw.jsonl row count matches **gold set count**".
   그런데 코드는 `metrics.n_items` 와 비교한다 — **그 run 이 스스로 적어 낸 숫자**다.
   50문항 중 2문항만 돌리고 `n_items: 2` 라고 적으면 통과한다. `repro_check.py` 전체에서
   'gold' 는 **docstring 12행에만 있고 코드에는 한 번도 등장하지 않는다**(실측).
   → 평가셋 `eval-set.jsonl` 을 실제로 읽어 대조한다.

⚠️ **버전 핀 휴리스틱이 정상 입력을 반려한다**(반대 방향의 고장 — legalforge 와 같은 계열).
   원본은 모델명에 숫자가 2개 미만이면 FAIL 인데, **agentforge 자신의 CLAUDE.md 가 기본값으로
   못박은 `text-embedding-3-small` 이 숫자 1개**라 FAIL 한다(실측 `exit=1`).
   → 숫자 세기를 버리고 **핀 되지 않은 별칭**(`latest`·`stable` 및 정책의 `vague_models`)을
     반려한다. `text-embedding-3-small` 은 그 API 의 정식 모델명이므로 통과한다.

⚠️ **재실행(replay)을 이 게이트가 직접 하지 않는다.** 원본은 `subprocess` 로 `run.sh` 를
   실행한다. 게이트키퍼가 미션이 만든 코드를 임의 실행하면 **임의 코드 실행 통로**가 되고
   API 비용도 발생한다(`test_run`·`test_pass_rate` 와 같은 규율 — docs/13 §7).
   → Tester 가 남긴 **재실행 증거**(`runs/<id>/replay.json`)를 검사한다. 자기보고 신뢰
     구간이 남지만, 증거가 아예 없으면 FAIL 이므로 원본처럼 조용히 넘어가지는 않는다.

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.repro_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : 미션 디렉터리(runs/ · eval-set.jsonl 을 담은 곳)

정책 필드(repro_policy)
  require_fields (기본 [seed, llm, embedding, temperature])
  vague_models (기본 gpt-4·gpt-4o·claude-sonnet·claude-opus·gemini-pro …)
  determinism_required (기본 true) · max_temperature (기본 0.0)
  require_replay (기본 true) · min_replays (기본 1) · replay_tolerance (기본 0.01)

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
DEFAULT_FIELDS = ["seed", "llm", "embedding", "temperature"]
# 버전이 핀 되지 않은 **별칭**들. 같은 이름이 시점에 따라 다른 모델을 가리킨다.
DEFAULT_VAGUE = [
    "gpt-4", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo",
    "claude-sonnet", "claude-opus", "claude-haiku",
    "gemini-pro", "gemini-flash", "llama-3", "mistral",
]
UNPINNED_TOKENS = ("latest", "stable", "preview", "dev", "nightly")


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


def gold_count(root: str) -> int | None:
    p = os.path.join(root, "eval-set.jsonl")
    if not os.path.isfile(p):
        return None
    return sum(1 for line in open(p, encoding="utf-8") if line.strip())


def raw_path_for(root: str, run_id: str) -> str | None:
    """예측 원본은 corpus 발췌를 담아 `_private/` 에 둔다. 구 위치도 받는다."""
    for rel in (os.path.join("_private", "runs", run_id, "raw.jsonl"),
                os.path.join("runs", run_id, "raw.jsonl")):
        p = os.path.join(root, rel)
        if os.path.isfile(p):
            return p
    return None


def count_lines(path: str) -> int:
    return sum(1 for line in open(path, encoding="utf-8") if line.strip())


def scalars(d: dict, prefix: str = "") -> dict[str, float]:
    out: dict[str, float] = {}
    for k, v in (d or {}).items():
        key = f"{prefix}.{k}" if prefix else str(k)
        if isinstance(v, dict):
            out.update(scalars(v, key))
        elif isinstance(v, bool):
            continue
        elif isinstance(v, (int, float)):
            out[key] = float(v)
    return out


def check_model_pin(value, field: str, run_id: str, vague: list[str]) -> list[str]:
    issues = []
    v = str(value or "").strip()
    low = v.lower()
    if not v:
        issues.append(f"{run_id}: config.{field} 가 비었다")
        return issues
    if any(t in low for t in UNPINNED_TOKENS):
        issues.append(f"{run_id}: config.{field}={v!r} 는 핀 되지 않은 별칭이다 "
                      f"({'/'.join(UNPINNED_TOKENS[:3])} …) — 같은 이름이 시점에 따라 "
                      f"다른 모델을 가리킨다")
    elif low in [str(x).lower() for x in vague]:
        issues.append(f"{run_id}: config.{field}={v!r} 는 버전이 핀 되지 않은 별칭이다 "
                      f"— 날짜/버전 접미사를 붙여라(`gpt-4o-2024-08-06`·`claude-sonnet-4-6`)")
    return issues


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
    run_ids = sorted(n for n in os.listdir(runs_dir) if os.path.isdir(os.path.join(runs_dir, n)))
    if not run_ids:
        print(f"FAIL(usage): run 이 하나도 없다({runs_dir}) — **원본은 이 경우 "
              f"'scanned 0 runs · PASS' 였다.** 평가를 돌리지 않은 것은 재현 가능한 것이 "
              f"아니다. fail-closed", file=sys.stderr)
        return 2

    fields = policy.get("require_fields") or DEFAULT_FIELDS
    vague = policy.get("vague_models") or DEFAULT_VAGUE
    det_required = bool(policy.get("determinism_required", True))
    max_temp = policy.get("max_temperature", 0.0)
    require_replay = bool(policy.get("require_replay", True))
    min_replays = int(policy.get("min_replays", 1))
    tol = float(policy.get("replay_tolerance", 0.01))

    gold = gold_count(root)
    if gold is None:
        print(f"FAIL(usage): eval-set.jsonl 이 없어 gold set 대조를 할 수 없다 — "
              f"원본은 이 대조를 docstring 에만 적어 두고 코드에서는 run 이 스스로 적어 낸 "
              f"`n_items` 와 비교했다. fail-closed", file=sys.stderr)
        return 2

    print(f"run {len(run_ids)}건 · gold set {gold}문항 · 결정성 필수={det_required} · "
          f"재실행 증거 필수={require_replay}")

    issues: list[str] = []
    n_replays = 0
    for run_id in run_ids:
        rd = os.path.join(runs_dir, run_id)
        cfg_path = os.path.join(rd, "config.json")
        met_path = os.path.join(rd, "metrics.json")

        if not os.path.isfile(cfg_path):
            issues.append(f"{run_id}: config.json 이 없다")
            continue
        try:
            cfg = json.loads(open(cfg_path, encoding="utf-8").read())
        except (OSError, json.JSONDecodeError) as e:
            issues.append(f"{run_id}: config.json 을 읽을 수 없다 ({e})")
            continue

        status = str(cfg.get("status", "complete")).lower()
        if status == "failed":
            # 실패 run 은 결정성 검사 대상이 아니다(집계 대상에서 빠진다 — run_completeness 가 본다)
            print(f"  · {run_id}: status=failed — 결정성 검사 제외(집계 포함 여부는 "
                  f"run_completeness 게이트가 본다)")
            continue

        for f in fields:
            if f not in cfg or cfg[f] in (None, ""):
                issues.append(f"{run_id}: config 에 {f!r} 가 없다")
        for f in ("llm", "embedding"):
            if f in fields and cfg.get(f) not in (None, ""):
                issues.extend(check_model_pin(cfg.get(f), f, run_id, vague))

        if "temperature" in fields:
            temp = cfg.get("temperature")
            if temp is not None:
                try:
                    tval = float(temp)
                except (TypeError, ValueError):
                    issues.append(f"{run_id}: temperature={temp!r} 가 수가 아니다 "
                                  f"(원본은 여기서 예외로 죽었다)")
                else:
                    if det_required and tval > float(max_temp) and \
                            not cfg.get("non_determinism_justification"):
                        issues.append(
                            f"{run_id}: temperature={tval} > {max_temp} 인데 "
                            f"`non_determinism_justification` 이 없다")

        # 예측 산출물 — 원본은 없으면 건너뛰어 PASS 였다
        raw = raw_path_for(root, run_id)
        if raw is None:
            issues.append(f"{run_id}: raw.jsonl 이 없다 — **원본은 파일이 없으면 검사를 "
                          f"건너뛰어 통과시켰다.** 예측 없이 지표만 있는 run 은 재현할 수 없다")
        else:
            rows = count_lines(raw)
            if rows != gold:
                issues.append(f"{run_id}: raw.jsonl {rows}행 ≠ gold set {gold}문항 — "
                              f"조용히 건너뛴 문항이 있다(원본은 run 이 스스로 적은 "
                              f"`n_items` 와만 비교했다)")

        if not os.path.isfile(met_path):
            issues.append(f"{run_id}: metrics.json 이 없다 — 원본은 이 경우도 통과시켰다")
        else:
            try:
                met = json.loads(open(met_path, encoding="utf-8").read())
            except (OSError, json.JSONDecodeError) as e:
                issues.append(f"{run_id}: metrics.json 을 읽을 수 없다 ({e})")
                met = None
            if met is not None:
                n_items = met.get("n_items")
                if n_items is None:
                    issues.append(f"{run_id}: metrics.n_items 가 없다")
                elif int(n_items) != gold:
                    issues.append(f"{run_id}: metrics.n_items={n_items} ≠ gold set {gold}문항")
                # 재실행 증거
                rep_path = os.path.join(rd, "replay.json")
                if os.path.isfile(rep_path):
                    try:
                        rep = json.loads(open(rep_path, encoding="utf-8").read())
                    except (OSError, json.JSONDecodeError) as e:
                        issues.append(f"{run_id}: replay.json 을 읽을 수 없다 ({e})")
                    else:
                        a = scalars(met.get("aggregate") or {})
                        b = scalars((rep.get("aggregate") or rep.get("metrics") or {}))
                        shared = sorted(set(a) & set(b))
                        if not shared:
                            issues.append(f"{run_id}: replay.json 에 대조 가능한 지표가 없다 "
                                          f"— 재실행했다는 기록만으로는 증거가 아니다")
                        else:
                            drift = [(k, a[k], b[k]) for k in shared if abs(a[k] - b[k]) > tol]
                            if drift:
                                for k, x, y in drift[:5]:
                                    issues.append(f"{run_id}: 재실행 표류 {k}: {x} → {y} "
                                                  f"(허용 {tol})")
                            else:
                                n_replays += 1

    if require_replay and n_replays < min_replays:
        issues.append(f"허용 오차 안에서 재현된 run 이 {n_replays}건 < 하한 {min_replays} — "
                      f"`runs/<id>/replay.json` 에 재실행 지표를 남겨라. "
                      f"⚠️ 이 게이트는 run.sh 를 직접 실행하지 않는다(임의 코드 실행 통로가 "
                      f"되기 때문 — docs/13 §7). 재실행은 Tester 단계의 일이다")

    if issues:
        print(f"FAIL: 재현성 문제 {len(issues)}건")
        for i in issues[:20]:
            print(f"       · {i}")
        if len(issues) > 20:
            print(f"       … 외 {len(issues) - 20}건")
    else:
        print(f"  ✓ 전 run 이 seed·모델버전·temperature 를 기록했고, 예측 {gold}행이 "
              f"gold set 과 일치하며, 재실행이 허용 오차 안에서 재현됐다({n_replays}건)")
    print("VERDICT:", "FAIL" if issues else "PASS")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
