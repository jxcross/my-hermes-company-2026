#!/usr/bin/env python3
"""agent-eval(아키타입 M) 게이트를 '일부러 깨뜨린 픽스처'로 검증한다 (docs/13 §5).

원본 agentforge 의 게이트 2종에서 실측으로 확인한 결함 5건에 **회귀 방어**를 건다:
  · 통계 게이트가 **방향을 보지 않아** 제안이 30%p 퇴보해도 PASS  → ⑤-1
  · 잘한 문항만 채점해 내면 그 문항들로만 판정(분모 자기결정)      → ⑤-2
  · 균일한 개선은 표준편차 0 → Cohen's d = +inf 로 통과            → ⑤-3
  · `runs/` 가 비어도 "scanned 0 runs · PASS"                      → ⑥-1
  · `raw.jsonl`·`metrics.json` 이 없으면 검사를 건너뛰어 PASS       → ⑥-2·3
  · docstring 이 말한 gold set 대조가 코드에 없음                   → ⑥-4
  · 버전 핀 휴리스틱이 자기 기본값(`text-embedding-3-small`)을 반려 → ⑨-1
"""
import json, os, shutil, subprocess, sys
import yaml

ROOT = "/work/company"
FIX = "/tmp/af"
GATES = os.path.join(ROOT, "scripts", "gates")

SYSTEMS = [("baseline", "baseline"), ("proposed", "proposed"), ("abl-no-rerank", "ablation")]
SEEDS = [11, 22, 33]
N_ITEMS = 50
CATS = ["설치", "설정", "문제해결", "개념"]


def item_scores(system: str, i: int) -> float:
    """결정적 점수. proposed 는 baseline 보다 평균 +0.10, 편차가 있어 표준편차 > 0."""
    base = 0.60 + (i % 5) * 0.02
    if system == "baseline":
        return round(base, 4)
    if system == "proposed":
        return round(base + 0.08 + (i % 3) * 0.02, 4)
    return round(base + 0.03, 4)                      # ablation


def w(rel, s):
    p = os.path.join(FIX, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(s)


def build():
    shutil.rmtree(FIX, ignore_errors=True)
    os.makedirs(FIX)

    tpl = yaml.safe_load(open(os.path.join(ROOT, "templates", "agent-eval.yaml"), encoding="utf-8"))
    pol = tpl["policy"]
    pol["stat_policy"]["bootstrap_samples"] = 2000     # 픽스처 속도(판정 로직은 동일)
    json.dump({"policy": pol}, open(os.path.join(FIX, "pipeline.json"), "w"), ensure_ascii=False)

    # ── 코퍼스 ────────────────────────────────────────────────────────────
    chunks = "\n".join(json.dumps(
        {"id": f"chunk-{i:04d}", "source": f"doc{i % 4 + 1}", "text": f"본문 {i}", "tokens": 400},
        ensure_ascii=False) for i in range(N_ITEMS + 10))
    w("_private/corpus/chunks.jsonl", chunks + "\n")
    w("raw/sources.yaml", yaml.safe_dump([
        {"id": "doc1", "title": "사용자 매뉴얼", "published_year": 2025,
         "source_type": "primary_doc", "license": "CC-BY-4.0", "status": "selected"},
        {"id": "doc2", "title": "설치 가이드", "published_year": 2025,
         "source_type": "primary_doc", "license": "CC-BY-4.0", "status": "selected"},
        {"id": "doc3", "title": "API 레퍼런스", "published_year": 2024,
         "source_type": "reference", "license": "Apache-2.0", "status": "selected"},
        {"id": "doc4", "title": "FAQ", "published_year": 2025,
         "source_type": "faq", "license": "CC-BY-4.0", "status": "selected"},
    ], allow_unicode=True))
    w("corpus.md", "# 코퍼스\n문서 4건 · 청크 60개 · 중복 제거 3건\n")

    # ── 평가셋: 15 easy / 20 medium / 15 hard = 30/40/30 ─────────────────
    diffs = ["easy"] * 15 + ["medium"] * 20 + ["hard"] * 15
    lines = []
    for i in range(N_ITEMS):
        lines.append(json.dumps({
            "id": f"q{i:03d}",
            "question": f"{CATS[i % 4]} 관련 질문 {i} 은 무엇인가?",
            "gold_answer": f"답 {i} 이다",
            "gold_context": [f"chunk-{i:04d}"],
            "difficulty": diffs[i],
            "category": CATS[i % 4],
        }, ensure_ascii=False))
    w("eval-set.jsonl", "\n".join(lines) + "\n")
    w("eval-set.md", "# 평가셋\n50문항 · easy 15 / medium 20 / hard 15 · 카테고리 4종\n")

    # ── 설계 ──────────────────────────────────────────────────────────────
    w("design.md", """# 인덱스·시스템 설계

임베딩 `text-embedding-3-small` · 벡터스토어 faiss-1.8.0 · top-k 5

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
""")

    # ── 구현물 ────────────────────────────────────────────────────────────
    for sid, _role in SYSTEMS:
        w(f"src/{sid}/agent.py", "import os\napi_key = os.environ['OPENAI_API_KEY']\n")
        w(f"src/{sid}/config.yaml", "llm: gpt-4o-2024-08-06\ntemperature: 0\n")
        w(f"src/{sid}/run.sh", "#!/bin/sh\npython3 agent.py \"$@\"\n")

    # ── run 매트릭스: 3 시스템 × 3 seed ──────────────────────────────────
    for sid, _role in SYSTEMS:
        for seed in SEEDS:
            rid = f"{sid}__seed{seed}"
            per = [{"id": f"q{i:03d}", "answer_correctness": item_scores(sid, i),
                    "recall_at_k": {"5": 1.0}} for i in range(N_ITEMS)]
            agg = round(sum(p["answer_correctness"] for p in per) / N_ITEMS, 4)
            w(f"runs/{rid}/config.json", json.dumps({
                "run_id": rid, "system": sid, "seed": seed,
                "llm": "gpt-4o-2024-08-06", "embedding": "text-embedding-3-small",
                "temperature": 0, "status": "complete"}, ensure_ascii=False, indent=2))
            w(f"runs/{rid}/metrics.json", json.dumps({
                "run_id": rid, "system": sid, "seed": seed, "n_items": N_ITEMS,
                "per_item": per, "aggregate": {"answer_correctness": agg}},
                ensure_ascii=False))
            w(f"_private/runs/{rid}/raw.jsonl",
              "".join(json.dumps({"id": f"q{i:03d}", "prediction": f"예측 {i}"},
                                 ensure_ascii=False) + "\n" for i in range(N_ITEMS)))
    # 재실행 증거 1건(허용 오차 안)
    m = json.load(open(os.path.join(FIX, "runs/proposed__seed11/metrics.json"), encoding="utf-8"))
    w("runs/proposed__seed11/replay.json", json.dumps({
        "replayed": "proposed__seed11",
        "aggregate": {"answer_correctness": round(m["aggregate"]["answer_correctness"] + 0.002, 4)}},
        ensure_ascii=False))
    w("runs-summary.md", "# 실행 요약\nrun 9건 · 실패 0건\n")
    w("run-plan.md", "# 실행 계획\n3 시스템 × 3 seed = 9 run · 예상 호출 450회\n")

    # ── 보고서(커밋 대상) ─────────────────────────────────────────────────
    w("report/report.md", """# 평가 보고서

본 결과는 단일 환경에서 수행된 평가이며 재현을 보장하지 않습니다.

## 주요 결과
proposed 가 baseline 대비 answer_correctness +0.10 (95% CI [+0.09, +0.11]).
""")
    w("report/usage-disclaimer.md", """# 고지

본 결과는 단일 환경에서 수행된 평가이며 재현을 보장하지 않습니다.
동료 심사를 거치지 않았습니다.
""")
    w("report/paper-artifacts/main_results.csv", "system,answer_correctness\nbaseline,0.64\n")
    # _private 에는 진짜 키가 있어도 된다(커밋되지 않으므로 검사 대상 아님)
    w("_private/corpus/notes.md", "내부 메모: sk-abcdefghijklmnopqrstuvwxyz012345\n")


def run(gate, draft):
    r = subprocess.run(["python3", os.path.join(GATES, f"{gate}.py"),
                        "--policy", os.path.join(FIX, "pipeline.json"),
                        "--sources", os.path.join(FIX, "raw", "sources.yaml"),
                        "--draft", os.path.join(FIX, draft)],
                       capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


DRAFTS = {"eval_set_quality": "eval-set.jsonl", "source_balance": "eval-set.jsonl",
          "stat_significance": ".", "repro_determinism": ".", "run_completeness": ".",
          "secret_redaction": "."}


def expect(label, gate, want, show=False, draft=None):
    rc, out = run(gate, draft or DRAFTS[gate])
    print(f"{'OK ' if rc == want else '‼️ '}{label:58s} exit={rc} (기대 {want})")
    if rc != want or show:
        print("      " + "\n      ".join(out.splitlines()[-8:]))
    return rc == want


def patch(path, old, new):
    p = os.path.join(FIX, path)
    t = open(p, encoding="utf-8").read()
    assert old in t, f"픽스처 치환 실패: {old!r} not in {path}"
    open(p, "w", encoding="utf-8").write(t.replace(old, new, 1))


def rewrite_metrics(rid, fn):
    """runs/<rid>/metrics.json 의 per_item 을 fn(i, value) 로 다시 쓴다."""
    p = os.path.join(FIX, "runs", rid, "metrics.json")
    m = json.load(open(p, encoding="utf-8"))
    m["per_item"] = fn(m["per_item"])
    m["n_items"] = len(m["per_item"])
    if m["per_item"]:
        m["aggregate"] = {"answer_correctness":
                          round(sum(x["answer_correctness"] for x in m["per_item"])
                                / len(m["per_item"]), 4)}
    json.dump(m, open(p, "w", encoding="utf-8"), ensure_ascii=False)


results = []
print("── ① 정상 픽스처: 6게이트 모두 PASS ──")
build()
results.append(expect("정상 · eval_set_quality", "eval_set_quality", 0, show=True))
results.append(expect("정상 · source_balance", "source_balance", 0))
results.append(expect("정상 · stat_significance", "stat_significance", 0, show=True))
results.append(expect("정상 · repro_determinism", "repro_determinism", 0, show=True))
results.append(expect("정상 · run_completeness", "run_completeness", 0, show=True))
results.append(expect("정상 · secret_redaction(코드·설정까지)", "secret_redaction", 0))

print("\n── ② eval_set_quality: 평가셋을 깨뜨린다 ──")
build(); patch("eval-set.jsonl", '{"id": "q049"', '{"id": "q049_dropped_marker"')
lines = open(os.path.join(FIX, "eval-set.jsonl"), encoding="utf-8").read().splitlines()
open(os.path.join(FIX, "eval-set.jsonl"), "w", encoding="utf-8").write("\n".join(lines[:-1]) + "\n")
results.append(expect("문항 49건(하한 50 미달)", "eval_set_quality", 1))

build(); patch("eval-set.jsonl", '"gold_context": ["chunk-0007"]', '"gold_context": ["chunk-9999"]')
results.append(expect("**환각 gold_context — 원본은 지시로만 금지**", "eval_set_quality", 1, show=True))

build()
ep = os.path.join(FIX, "eval-set.jsonl")
skewed = open(ep, encoding="utf-8").read().replace('"difficulty": "hard"', '"difficulty": "easy"')
open(ep, "w", encoding="utf-8").write(skewed)
results.append(expect("난이도 전부 easy 로 쏠림", "eval_set_quality", 1))

build(); os.remove(os.path.join(FIX, "_private/corpus/chunks.jsonl"))
results.append(expect("chunk 목록 부재 → fail-closed(대조 불가)", "eval_set_quality", 2))

build(); patch("eval-set.jsonl", '"question": "설정 관련 질문 1 은 무엇인가?"',
               '"question": "설치 관련 질문 0 은 무엇인가?"')
results.append(expect("사실상 같은 질문으로 문항 수 채우기", "eval_set_quality", 1))

build(); patch("eval-set.jsonl", '"gold_answer": "답 3 이다"', '"gold_answer": ""')
results.append(expect("gold_answer 가 비었다(채점 불가)", "eval_set_quality", 1))

build(); patch("eval-set.jsonl", '"difficulty": "easy", "category": "설정"',
               '"difficulty": "easy", "category": ""')
results.append(expect("category 누락(커버리지 분모 흔들림)", "eval_set_quality", 1))

print("\n── ③ stat_significance: **원본 결함 3건의 회귀 방어** ──")
build(); rewrite_metrics("proposed__seed11", lambda ps: [{**p, "answer_correctness": round(p["answer_correctness"] - 0.30, 4)} for p in ps])
rewrite_metrics("proposed__seed22", lambda ps: [{**p, "answer_correctness": round(p["answer_correctness"] - 0.30, 4)} for p in ps])
rewrite_metrics("proposed__seed33", lambda ps: [{**p, "answer_correctness": round(p["answer_correctness"] - 0.30, 4)} for p in ps])
results.append(expect("**제안이 30%p 퇴보 — 원본 실측 PASS 였다**", "stat_significance", 1, show=True))

build()
for s in SEEDS:
    rewrite_metrics(f"proposed__seed{s}", lambda ps: ps[:6])
results.append(expect("**잘한 6문항만 채점(분모 자기결정) — 원본 실측 PASS**", "stat_significance", 1, show=True))

build()
for s in SEEDS:
    rewrite_metrics(f"proposed__seed{s}",
                    lambda ps: [{**p, "answer_correctness": round(item_scores("baseline", i) + 0.001, 4)}
                                for i, p in enumerate(ps)])
results.append(expect("**균일 +0.001(표준편차 0 → d=inf) — 원본 실측 PASS**", "stat_significance", 1, show=True))

build(); patch("design.md", "```systems", "```systemz")
results.append(expect("systems 블록 없음 → fail-closed", "stat_significance", 2))

build(); shutil.rmtree(os.path.join(FIX, "runs"))
os.makedirs(os.path.join(FIX, "runs"))
results.append(expect("run 이 하나도 없음 → fail-closed", "stat_significance", 2))

print("\n── ④ repro_determinism: **fail-open 이던 지점** ──")
build(); shutil.rmtree(os.path.join(FIX, "runs")); os.makedirs(os.path.join(FIX, "runs"))
results.append(expect("**runs/ 비어 있음 — 원본은 '0 runs · PASS'**", "repro_determinism", 2, show=True))

build(); shutil.rmtree(os.path.join(FIX, "_private/runs/baseline__seed11"))
results.append(expect("**raw.jsonl 없음 — 원본은 건너뛰어 PASS**", "repro_determinism", 1))

build(); os.remove(os.path.join(FIX, "runs/baseline__seed22/metrics.json"))
results.append(expect("**metrics.json 없음 — 원본은 건너뛰어 PASS**", "repro_determinism", 1))

build()
p = os.path.join(FIX, "_private/runs/baseline__seed33/raw.jsonl")
kept = open(p, encoding="utf-8").readlines()[:48]      # 먼저 읽는다 — open(w) 가 먼저 평가되면 0행이 된다
open(p, "w", encoding="utf-8").write("".join(kept))
results.append(expect("**raw 48행 ≠ gold 50문항(원본은 자기신고와만 비교)**", "repro_determinism", 1, show=True))

build(); patch("runs/proposed__seed22/config.json", '"temperature": 0', '"temperature": 0.7')
results.append(expect("temperature 0.7 인데 사유 없음", "repro_determinism", 1))

build(); patch("runs/proposed__seed33/config.json", '"llm": "gpt-4o-2024-08-06"', '"llm": "gpt-4o"')
results.append(expect("핀 되지 않은 모델 별칭 `gpt-4o`", "repro_determinism", 1))

build(); patch("runs/proposed__seed33/config.json", '"llm": "gpt-4o-2024-08-06"', '"llm": "claude-sonnet-latest"')
results.append(expect("`latest` 별칭(시점마다 다른 모델)", "repro_determinism", 1))

build(); patch("runs/proposed__seed11/replay.json", '"answer_correctness"', '"answer_correctness_x"')
results.append(expect("replay 에 대조 가능한 지표 없음", "repro_determinism", 1))

build(); os.remove(os.path.join(FIX, "runs/proposed__seed11/replay.json"))
results.append(expect("재실행 증거가 아예 없음", "repro_determinism", 1))

build()
m = json.load(open(os.path.join(FIX, "runs/proposed__seed11/metrics.json"), encoding="utf-8"))
w("runs/proposed__seed11/replay.json", json.dumps(
    {"aggregate": {"answer_correctness": round(m["aggregate"]["answer_correctness"] + 0.05, 4)}}))
results.append(expect("재실행 표류 0.05 > 허용 0.01", "repro_determinism", 1))

print("\n── ⑤ run_completeness: 선언 ↔ 실재 ──")
build(); shutil.rmtree(os.path.join(FIX, "runs/proposed__seed22"))
results.append(expect("선언한 run 하나가 없다(병렬 워커 사망)", "run_completeness", 1, show=True))

build(); shutil.rmtree(os.path.join(FIX, "src/proposed"))
results.append(expect("선언만 하고 구현하지 않은 시스템", "run_completeness", 1))

build(); patch("runs/proposed__seed33/config.json", '"status": "complete"', '"status": "failed"')
results.append(expect("**proposed 의 run 이 실패 — 원본은 빼고 진행**", "run_completeness", 1, show=True))

build(); patch("runs/proposed__seed11/config.json", '"system": "proposed"', '"system": "baseline"')
results.append(expect("디렉터리 이름 ≠ config.system(짝이 뒤바뀐다)", "run_completeness", 1))

build(); patch("design.md", "- id: abl-no-rerank\n  role: ablation\n  change: 리랭커 제거\n", "")
shutil.rmtree(os.path.join(FIX, "src/abl-no-rerank"))
for s in SEEDS:
    shutil.rmtree(os.path.join(FIX, f"runs/abl-no-rerank__seed{s}"))
results.append(expect("ablation 이 하나도 없다", "run_completeness", 1))

build(); patch("design.md", "  change: 리랭커 제거", "  note: 리랭커 제거")
results.append(expect("ablation 에 `change:` 가 없다(해석 불가)", "run_completeness", 1))

build(); patch("design.md", "- id: proposed\n  role: proposed", "- id: proposed\n  role: baseline")
results.append(expect("baseline 이 2개(비교가 성립하지 않는다)", "run_completeness", 1))

build(); patch("design.md", "seeds: [11, 22, 33]", "seeds: [11]")
results.append(expect("seed 1개(운과 개선을 구별 못한다)", "run_completeness", 1))

print("\n── ⑥ secret_redaction: **코드·설정까지 훑는다**(M 에서 확장) ──")
build(); patch("src/proposed/config.yaml", "llm: gpt-4o-2024-08-06",
               "api_key: sk-abcdefghijklmnopqrstuvwxyz012345\nllm: gpt-4o-2024-08-06")
results.append(expect("커밋될 config.yaml 에 API 키 평문", "secret_redaction", 1, show=True))

build(); patch("runs/baseline__seed11/config.json", '"status": "complete"',
               '"status": "complete", "token": "ghp_abcdefghijklmnopqrstuvwxyz0123"')
results.append(expect("커밋될 run config.json 에 GitHub 토큰", "secret_redaction", 1))

build(); os.remove(os.path.join(FIX, "report/usage-disclaimer.md"))
results.append(expect("고지 파일 자체가 없다(검사가 건너뛰어지면 안 된다)", "secret_redaction", 1))

build(); patch("report/report.md", "본 결과는 단일 환경에서 수행된 평가이며 재현을 보장하지 않습니다.\n", "")
results.append(expect("report.md 의 고지 문구 누락", "secret_redaction", 1))

print("\n── ⑦ 설계 판단의 회귀 방어 ──")
build()
results.append(expect("`text-embedding-3-small` 은 PASS — **원본은 자기 기본값을 반려했다**",
                      "repro_determinism", 0))
build()
results.append(expect("`_private/` 의 진짜 키는 검사 대상이 아니다(커밋 안 됨)", "secret_redaction", 0))
build(); patch("runs/abl-no-rerank__seed11/config.json", '"status": "complete"', '"status": "failed"')
results.append(expect("ablation 실패는 막지 않는다(strict_roles 밖)", "run_completeness", 0))

print(f"\n{sum(results)}/{len(results)} 통과")
sys.exit(0 if all(results) else 1)
