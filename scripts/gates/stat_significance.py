#!/usr/bin/env python3
"""
객관 게이트: 통계적 유의성(baseline vs proposed)
================================================
제안 시스템이 기준 시스템보다 **실제로 더 나은지** paired bootstrap 신뢰구간 + 효과크기로
검사한다. 표준 라이브러리만 쓴다.
출처: other_projects/harness-templates/.../agentforge/scripts/statistical_test.py (GATE 2)

⚠️ **원본은 '더 나은가'가 아니라 '다른가'를 쟀다 — 방향을 보지 않는다** (docs/13 §5).
   `ci_excludes_zero = (ci_lo > 0) or (ci_hi < 0)` 이고 `effect_ok = abs(d) >= min_effect`
   라, **제안 시스템이 기준보다 나쁠수록 오히려 확실하게 PASS** 한다.
   실측(픽스처 50문항, 제안이 30%p 하락): `mean diff -0.2951 · Cohen's d -11.157 ·
   CI [-0.3023, -0.2882] · verdict: PASS · exit=0`.
   개선을 주장하는 논문 산출물이 **성능 퇴보를 통계적으로 입증하고 통과**한다.
   → `higher_is_better` 정책에 맞는 방향의 개선만 인정한다.

⚠️ **두 번째 결함: 분모를 채점 대상이 스스로 정한다** (code-docs 의 '분모 자기결정'과 같은 계열).
   원본은 두 run 에 **공통으로 존재하는 항목**만 짝지어 비교하고, 5건 이상이면 통과시킨다.
   제안 시스템이 50문항 중 잘한 6문항만 채점해 내면 그 6문항으로 판정된다.
   실측(6문항만 제출, 전부 +0.1): `paired n: 6 · Cohen's d +inf · CI [+0.1, +0.1] · PASS`.
   → 평가셋 대비 **짝지어진 항목의 커버리지 하한**(min_paired_coverage)을 요구한다.

⚠️ **세 번째 결함: 축퇴(degenerate) 케이스에서 효과크기가 무한대**가 된다.
   차이가 모든 항목에서 똑같으면 표준편차가 0 이라 원본은 `float("inf")` 를 돌려주고,
   bootstrap CI 도 한 점으로 수렴해 0 을 제외한다. **+0.001 의 균일한 개선이 "무한대 효과"**
   로 통과한다. → 표준편차 0 이면 효과크기를 판정 근거로 쓰지 않고, 대신 **실질 유의성**
   (min_mean_diff)을 요구한다.

⚠️ 원본은 **run 하나 대 run 하나**를 비교한다. 그런데 파이프라인은 시스템 × seed 로 run 을
   만든다(재현성 목적). seed 하나만 골라 비교하면 **seed 운으로 결과가 갈린다.**
   → 시스템의 전 seed run 을 항목별로 평균낸 뒤 비교한다(seed 를 통제한다).

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.stat_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : 미션 디렉터리(runs/ · design.md · eval-set.jsonl 을 담은 곳)

정책 필드(stat_policy)
  primary_metric (기본 answer_correctness) · higher_is_better (기본 true)
  alpha (기본 0.05) · bootstrap_samples (기본 10000) · bootstrap_seed (기본 42)
  min_effect_size (기본 0.2) · min_mean_diff (기본 0.02)
  min_paired_items (기본 30) · min_paired_coverage (기본 0.9)

exit: 0 PASS · 1 FAIL · 2 usage/입력없음(fail-closed)
"""
from __future__ import annotations
import argparse
import json
import os
import random
import re
import statistics
import sys

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML 필요", file=sys.stderr); sys.exit(2)

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
SYSTEMS_BLOCK_RE = re.compile(r"```systems\s*\n(.*?)\n```", re.DOTALL)

# 원본 metrics.json 의 per-item 키 표기 흔들림을 흡수한다.
METRIC_ALIASES = {
    "answer_correctness": ("answer_correctness", "answer_correctness_score"),
    "faithfulness": ("faithfulness", "faithfulness_score"),
}


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("stat_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("stat_policy", {}) or {}


def mission_root(draft: str) -> str:
    p = os.path.abspath(draft)
    return p if os.path.isdir(p) else os.path.dirname(p)


def parse_systems(root: str) -> dict[str, str]:
    """design.md 의 ```systems``` 블록 → {system_id: role}."""
    out: dict[str, str] = {}
    for name in ("design.md", "04-agent-design.md"):
        path = os.path.join(root, name)
        if not os.path.isfile(path):
            continue
        m = SYSTEMS_BLOCK_RE.search(open(path, encoding="utf-8").read())
        if not m:
            continue
        cur = None
        for line in m.group(1).splitlines():
            mi = re.match(r"^\s*-\s+id:\s*(\S+)", line)
            if mi:
                cur = mi.group(1).strip()
                out.setdefault(cur, "")
                continue
            mr = re.match(r"^\s+role:\s*(\S+)", line)
            if mr and cur:
                out[cur] = mr.group(1).strip().lower()
        break
    return out


def per_item_values(metrics: dict, metric: str) -> dict[str, float]:
    """metrics.json 의 per_item → {item_id: value}. recall@5 형태도 받는다."""
    keys = METRIC_ALIASES.get(metric, (metric,))
    at_k = re.match(r"^(recall|ndcg)(?:_at_k|@)[._@]?(\d+)$", metric.replace(" ", ""))
    out: dict[str, float] = {}
    for it in metrics.get("per_item", []) or []:
        iid = it.get("id")
        if iid is None:
            continue
        v = None
        if at_k:
            d = it.get(f"{at_k.group(1)}_at_k") or {}
            if isinstance(d, dict):
                v = d.get(at_k.group(2))
        else:
            for k in keys:
                if k in it:
                    v = it[k]
                    break
        if v is None:
            continue
        try:
            out[str(iid)] = float(v)
        except (TypeError, ValueError):
            continue
    return out


def system_item_means(root: str, system: str, metric: str) -> tuple[dict[str, float], list[str]]:
    """시스템의 전 seed run 을 항목별로 평균. (값, 쓰인 run 목록)."""
    runs_dir = os.path.join(root, "runs")
    acc: dict[str, list[float]] = {}
    used: list[str] = []
    if not os.path.isdir(runs_dir):
        return {}, []
    for name in sorted(os.listdir(runs_dir)):
        rd = os.path.join(runs_dir, name)
        mp = os.path.join(rd, "metrics.json")
        if not os.path.isdir(rd) or not os.path.isfile(mp):
            continue
        try:
            m = json.loads(open(mp, encoding="utf-8").read())
        except (OSError, json.JSONDecodeError):
            continue
        sysid = m.get("system") or name.split("__")[0]
        if sysid != system:
            continue
        vals = per_item_values(m, metric)
        if not vals:
            continue
        used.append(name)
        for k, v in vals.items():
            acc.setdefault(k, []).append(v)
    return {k: statistics.mean(v) for k, v in acc.items()}, used


def eval_set_size(root: str) -> int | None:
    p = os.path.join(root, "eval-set.jsonl")
    if not os.path.isfile(p):
        return None
    return sum(1 for line in open(p, encoding="utf-8") if line.strip())


def cohens_d_paired(diffs: list[float]) -> float | None:
    """표준편차 0 이면 None — 원본의 float('inf') 는 축퇴를 '무한대 효과'로 둔갑시킨다."""
    if len(diffs) < 2:
        return None
    sd = statistics.stdev(diffs)
    return None if sd == 0 else statistics.mean(diffs) / sd


def paired_bootstrap_ci(diffs: list[float], n_samples: int, alpha: float,
                        seed: int) -> tuple[float, float]:
    rng = random.Random(seed)
    n = len(diffs)
    means = []
    for _ in range(n_samples):
        means.append(sum(diffs[rng.randrange(n)] for _ in range(n)) / n)
    means.sort()
    lo = means[int((alpha / 2) * n_samples)]
    hi = means[max(0, int((1 - alpha / 2) * n_samples) - 1)]
    return lo, hi


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
    metric = str(policy.get("primary_metric", "answer_correctness"))
    higher_better = bool(policy.get("higher_is_better", True))
    alpha = float(policy.get("alpha", 0.05))
    nboot = int(policy.get("bootstrap_samples", 10000))
    bseed = int(policy.get("bootstrap_seed", 42))
    min_d = float(policy.get("min_effect_size", 0.2))
    min_diff = float(policy.get("min_mean_diff", 0.02))
    min_paired = int(policy.get("min_paired_items", 30))
    min_cov = float(policy.get("min_paired_coverage", 0.9))

    systems = parse_systems(root)
    if not systems:
        print(f"FAIL(usage): design.md 의 ```systems``` 블록을 찾지 못했다({root}) — "
              f"어느 것이 baseline 이고 어느 것이 proposed 인지 알 수 없다. fail-closed",
              file=sys.stderr)
        return 2
    base = [s for s, r in systems.items() if r == "baseline"]
    prop = [s for s, r in systems.items() if r == "proposed"]
    if len(base) != 1 or len(prop) != 1:
        print(f"FAIL(usage): baseline {base} · proposed {prop} — 각각 정확히 1개여야 한다. "
              f"fail-closed", file=sys.stderr)
        return 2
    base, prop = base[0], prop[0]

    base_vals, base_runs = system_item_means(root, base, metric)
    prop_vals, prop_runs = system_item_means(root, prop, metric)
    if not base_runs or not prop_runs:
        print(f"FAIL(usage): metric '{metric}' 를 담은 run 이 없다 "
              f"(baseline={base_runs} · proposed={prop_runs}) — 평가를 돌리지 않은 것을 "
              f"'차이 없음'으로 읽으면 안 된다. fail-closed", file=sys.stderr)
        return 2

    common = sorted(set(base_vals) & set(prop_vals))
    n_eval = eval_set_size(root)
    print(f"metric={metric} (higher_is_better={higher_better}) · "
          f"baseline={base}({len(base_runs)} run) · proposed={prop}({len(prop_runs)} run)")
    print(f"짝지어진 항목 {len(common)}건 "
          f"(baseline {len(base_vals)} · proposed {len(prop_vals)} · "
          f"평가셋 {n_eval if n_eval is not None else '?'})")

    fail = False
    # ① 분모 통제 — 잘한 문항만 채점해 내는 것을 막는다(원본 결함 2)
    if len(common) < min_paired:
        print(f"FAIL: 짝지어진 항목 {len(common)}건 < 하한 {min_paired} — 표본이 작으면 "
              f"bootstrap CI 가 무엇이든 통과시킨다")
        fail = True
    if n_eval:
        cov = len(common) / n_eval
        print(f"  평가셋 대비 커버리지 {cov:.1%} (하한 {min_cov:.0%})")
        if cov < min_cov:
            print(f"FAIL: 평가셋 {n_eval}문항 중 {len(common)}문항만 짝지어졌다 — "
                  f"**채점 대상이 분모를 스스로 정한 것**이다. 누락 문항의 사유를 밝히고 "
                  f"전건을 채점하라(원본은 5건만 있어도 통과시켰다)")
            fail = True
    else:
        print(f"FAIL(usage): eval-set.jsonl 이 없어 커버리지 분모를 확인할 수 없다 — "
              f"fail-closed", file=sys.stderr)
        return 2

    if not common:
        print("VERDICT: FAIL")
        return 1

    diffs = [prop_vals[i] - base_vals[i] for i in common]
    if not higher_better:
        diffs = [-d for d in diffs]     # 항상 "개선이 양수"가 되도록 부호를 맞춘다
    mean_diff = statistics.mean(diffs)
    d = cohens_d_paired(diffs)
    ci_lo, ci_hi = paired_bootstrap_ci(diffs, nboot, alpha, bseed)

    raw_mean = statistics.mean([prop_vals[i] - base_vals[i] for i in common])
    print(f"  평균 차이(proposed - baseline): {raw_mean:+.4f} "
          f"→ 개선 방향 기준 {mean_diff:+.4f}")
    print(f"  Cohen's d: {'(표준편차 0 — 판정 근거로 쓰지 않음)' if d is None else f'{d:+.3f}'}"
          f"  (하한 {min_d})")
    print(f"  bootstrap CI ({1 - alpha:.0%}, n={nboot}): [{ci_lo:+.4f}, {ci_hi:+.4f}]")

    # ② 방향 — 이 게이트의 본체(원본 결함 1)
    if mean_diff <= 0:
        print(f"FAIL: 제안 시스템이 기준보다 나아지지 않았다(개선 방향 평균 차이 "
              f"{mean_diff:+.4f}). **원본은 방향을 보지 않아 30%p 퇴보도 PASS 였다** — "
              f"'다른가'가 아니라 '더 나은가'를 묻는 게이트다")
        fail = True
    elif ci_lo <= 0:
        print(f"FAIL: 개선 방향 신뢰구간 하한이 {ci_lo:+.4f} 로 0 을 포함한다 — 개선이 "
              f"우연과 구별되지 않는다")
        fail = True

    # ③ 실질 유의성 — 축퇴 케이스 방어(원본 결함 3)
    if mean_diff > 0 and mean_diff < min_diff:
        print(f"FAIL: 개선폭 {mean_diff:+.4f} < 실질 유의성 하한 {min_diff} — 통계적으로 "
              f"유의해도 의미 없는 크기다(원본은 균일한 +0.001 을 '무한대 효과'로 통과시켰다)")
        fail = True

    # ④ 효과크기 — 표준편차가 0 이면 판정 근거가 아니다
    if d is None:
        print(f"  참고: 전 항목의 차이가 동일해 표준편차가 0 이다 — 효과크기 대신 실질 "
              f"유의성(min_mean_diff)으로 판정했다. 채점이 상수를 더한 것은 아닌지 확인하라")
    elif abs(d) < min_d:
        print(f"FAIL: 효과크기 |d|={abs(d):.3f} < 하한 {min_d}")
        fail = True

    if not fail:
        print(f"  ✓ 제안 시스템이 기준 대비 유의하게 개선됐다(방향·CI·효과크기·실질 크기)")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
