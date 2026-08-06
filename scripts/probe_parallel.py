#!/usr/bin/env python3
"""
동시 요청 병렬성 측정기 (Ollama 직접 호출)
================================================================
"우리 파이프라인의 스테이지 내 병렬화가 로컬 백엔드에서 **실제로 병렬인가**"를
추측 대신 재서 답한다.

⚠️ **왜 만들었나 (2026-08-06)**
   `docs/11 §5` 의 Phase 2-① 병렬화는 스테이지 하나에서 subagent 3개를 동시에 띄운다
   (`delegation.max_concurrent_children` 기본 3 · 템플릿 `batch_size: 3`). 즉 **Ollama 에
   동시에 3개의 `/v1` 요청이 꽂힌다.** 그런데 Ollama 의 `OLLAMA_NUM_PARALLEL` 이 1이면
   서버가 요청을 **큐에 세워 하나씩 처리한다** — 클라이언트에서는 아무 오류도 안 보이고
   그냥 3배 느릴 뿐이다. 병렬화가 **조용히 사라진다.**

   병렬 파일럿 M-2026-004 는 codex 백엔드에서 돌아 이걸 볼 기회가 없었다.
   `docs/14` 도 `NUM_PARALLEL` 을 다루지 않는다(설정된 적이 없다 — 실측 확인).

**무엇을 재는가** — 같은 일을 하는 요청 N개를 **동시에 발사**하고 종료 시각을 본다.
  · 병렬이면 → N개가 **거의 같이** 끝난다(총 벽시계 ≈ 단일 × 1.0~1.6)
  · 직렬이면 → 종료 시각이 **계단처럼** 벌어진다(총 벽시계 ≈ 단일 × N)

  판정의 근거는 비율 하나가 아니라 **종료 시각 분포**다. 비율만 보면 모델 로드나
  프롬프트 캐시가 섞여 오판할 수 있어서, 요청별 종료 오프셋을 항상 함께 출력한다.

⚠️ **프롬프트를 요청마다 다르게 준다.** 같은 프롬프트를 N개 보내면 프롬프트 캐시가
   일을 줄여 버려서 "빨라졌다"가 병렬 때문인지 캐시 때문인지 구분할 수 없다.
   길이는 같게 두고 인덱스 토큰만 바꾼다.

⚠️ **`num_predict` 를 못박는다.** 생성 길이가 요청마다 다르면 종료 시각 분포가
   병렬성이 아니라 길이 차이를 반영한다.

사용
  python3 scripts/probe_parallel.py                      # 배치 모델(set_backend 표) · 동시 3
  python3 scripts/probe_parallel.py -m devstral-24b-96k -n 3
  python3 scripts/probe_parallel.py --json

exit: 0 병렬(또는 판정 보류) · 1 **직렬 검출**(병렬화 이득 없음) · 2 Ollama 에 닿지 못함
"""
from __future__ import annotations

import argparse
import json
import pathlib
import statistics
import sys
import threading
import time
import urllib.error
import urllib.request

OLLAMA = "http://127.0.0.1:11434"


def _default_model() -> str:
    """기본 모델은 **배치표에서 읽는다** — 문자열로 박아 두면 백엔드를 갈 때 여기만 남는다.

    ⚠️ 2026-08-06 실측: 이 파일만 `set_backend` 를 import 하지 않아 배치가
       `gemma4-26b-256k` 에서 바뀌어도 따라오지 않았다. `probe_protocol.py:239-243` 과
       `usage_report.py:174` 는 이미 표를 읽는다 — 같은 방식으로 맞춘다.
       import 이 실패해도 프로브 자체는 돌아야 하므로 폴백만 문자열로 둔다.
    """
    try:
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        import set_backend as sb  # noqa: PLC0415

        return sb.backend_models("ollama")[0]
    except Exception:
        return "gemma4-26b-256k"


DEFAULT_MODEL = _default_model()

# 생성 길이를 못박는다 — 요청마다 다르면 종료 분포가 병렬성이 아니라 길이를 반영한다.
NUM_PREDICT = 96

# ── 판정 신호 ────────────────────────────────────────────────────────────────
# ⚠️ **처음엔 총 벽시계 비율 하나로 판정했다가 틀렸다(실측 2026-08-06).**
#    NUM_PARALLEL=3 을 걸고 다시 재니 종료 오프셋이 [2.77, 2.77, 2.77] — 셋이 **정확히
#    동시에** 끝나는 완전한 병렬인데, 비율은 ×1.85 라 "부분 병렬"로 읽혔다.
#    GPU 는 동시 요청끼리 연산을 나눠 쓰므로 **병렬이어도 요청당 벽시계는 늘어난다.**
#    비율은 그 둘을 구분하지 못한다. 그래서 판정을 기계적으로 의미 있는 두 신호로 옮겼다:
#
#      ① **종료 오프셋 분산** — 큐에 서면 계단처럼 벌어진다. 병렬이면 몰린다.
#      ② **합산 처리량 이득** — 직렬이면 이득이 없다(오히려 음수: 실측 73.1 < 84.7).
#                              병렬이면 가중치를 한 번 읽어 여러 슬롯을 채우므로 는다.
#
#    실측 대조 (gemma4-26b-256k · 동시 3):
#      NUM_PARALLEL 미설정 → 분산 1.70 · 이득 ×0.84 → **직렬**
#      NUM_PARALLEL=3      → 분산 0.00 · 이득 ×1.27 → **병렬**
SPREAD_PARALLEL_MAX = 0.35    # 종료 오프셋 분산 / 단일 벽시계
SPREAD_SERIAL_FRAC = 0.60     # (n-1) × 이 값 이상이면 계단으로 본다
GAIN_PARALLEL_MIN = 1.05      # 합산 처리량 / 단일 처리량


def verdict_of(spread: float, gain: float, n: int, completed: int) -> str:
    """판정을 순수 함수로 떼어 둔다 — 서버 없이 검사할 수 있어야 한다.

    `spread` = (최대 종료 - 최소 종료) / 단일 벽시계 · `gain` = 합산 처리량 / 단일 처리량.
    **총 벽시계 비율은 쓰지 않는다** — 위 상수 주석의 오판 사례를 보라.

    ⚠️ 완료 수를 먼저 본다. 요청이 하나라도 떨어지면 남은 것끼리는 분산이 작아 보여
       **'병렬'로 거짓말한다**(3개 중 1개만 끝나면 분산 0이다).
    """
    if n < 2 or completed < n:
        return "불완전"
    if spread <= SPREAD_PARALLEL_MAX and gain >= GAIN_PARALLEL_MIN:
        return "병렬"
    if spread >= (n - 1) * SPREAD_SERIAL_FRAC or gain < 1.0:
        return "직렬"
    return "부분병렬"


def chat(model: str, prompt: str, num_predict: int, timeout: int) -> dict:
    """`/api/chat` 1회. 반환에 벽시계와 Ollama 자체 계측을 함께 담는다."""
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"num_predict": num_predict, "temperature": 0.2},
    }).encode()
    req = urllib.request.Request(
        OLLAMA + "/api/chat", data=body,
        headers={"Content-Type": "application/json"},
    )
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read())
    t1 = time.monotonic()
    return {
        "wall": t1 - t0,
        "start": t0,
        "end": t1,
        # Ollama 자체 계측(ns) — 벽시계와 어긋나면 큐 대기가 있었다는 뜻이다.
        "eval_count": data.get("eval_count", 0),
        "eval_ns": data.get("eval_duration", 0),
        "load_ns": data.get("load_duration", 0),
        "prompt_eval_ns": data.get("prompt_eval_duration", 0),
    }


def prompt_for(i: int) -> str:
    """길이는 같게, 내용만 다르게 — 프롬프트 캐시가 일을 줄이지 못하게 한다."""
    return (f"Topic {i:02d}: Write a short technical paragraph about distributed "
            f"systems variant {i:02d}. Be concise and concrete.")


def probe(model: str, n: int, reps: int, timeout: int) -> dict:
    # 0) 워밍업 — 모델 로드 비용을 측정에서 빼낸다(로드가 섞이면 첫 요청만 느려 보인다).
    warm = chat(model, "Reply with OK.", 4, timeout)

    # 1) 단일 요청 기준선 — reps 회의 중앙값(한 번만 재면 튄다)
    singles = [chat(model, prompt_for(90 + r), NUM_PREDICT, timeout) for r in range(reps)]
    t_single = statistics.median(s["wall"] for s in singles)

    # 2) 동시 N 요청 — 같은 순간에 발사한다
    results: list[dict | None] = [None] * n
    errors: list[str] = []
    barrier = threading.Barrier(n)

    def worker(idx: int) -> None:
        try:
            barrier.wait(timeout=timeout)          # 발사 시점을 맞춘다
            results[idx] = chat(model, prompt_for(idx), NUM_PREDICT, timeout)
        except Exception as exc:                    # noqa: BLE001 - 어떤 실패든 기록만
            errors.append(f"req{idx}: {type(exc).__name__}: {exc}")

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(n)]
    t0 = time.monotonic()
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    t_total = time.monotonic() - t0

    ok = [r for r in results if r]
    # 종료 시각을 t0 기준 오프셋으로 — 판정의 실제 근거다
    ends = sorted(round(r["end"] - t0, 2) for r in ok)

    ratio = t_total / t_single if t_single else 0.0
    single_tps = statistics.median(
        (s["eval_count"] / (s["eval_ns"] / 1e9)) if s["eval_ns"] else 0 for s in singles)
    agg_tps = (sum(r["eval_count"] for r in ok) / t_total) if t_total else 0.0
    spread = ((ends[-1] - ends[0]) / t_single) if (ends and t_single) else 0.0
    gain = (agg_tps / single_tps) if single_tps else 0.0
    verdict = verdict_of(spread, gain, n, len(ok))

    return {
        "model": model,
        "n": n,
        "reps": reps,
        "num_predict": NUM_PREDICT,
        "load_s": round(warm["load_ns"] / 1e9, 2),
        "single_s": round(t_single, 2),
        "concurrent_total_s": round(t_total, 2),
        "ratio": round(ratio, 2),
        "verdict": verdict,
        "end_offsets_s": ends,
        "end_spread": round(spread, 2),        # ← 판정 신호 ①
        "throughput_gain": round(gain, 2),     # ← 판정 신호 ②
        "per_req_wall_s": [round(r["wall"], 2) for r in ok],
        "single_tok_s": round(single_tps, 1),
        "aggregate_tok_s": round(agg_tps, 1),
        "errors": errors,
    }


def render(res: dict) -> None:
    n = res["n"]
    print(f"── 동시 요청 병렬성 ──  {res['model']}  ·  동시 {n}  ·  num_predict {res['num_predict']}")
    print(f"  단일 요청 벽시계(중앙값 {res['reps']}회) : {res['single_s']}초  ({res['single_tok_s']} tok/s)")
    print(f"  동시 {n}개 총 벽시계               : {res['concurrent_total_s']}초")
    print(f"  동시 {n}개 총 벽시계 비율          : ×{res['ratio']}  "
          f"(참고 — GPU 는 병렬이어도 요청당 느려진다. 판정에 쓰지 않는다)")
    print(f"  종료 오프셋(초)                   : {res['end_offsets_s']}")
    print(f"  ① 종료 분산                       : {res['end_spread']}  "
          f"(병렬 ≤{SPREAD_PARALLEL_MAX} · 직렬 ≥{round((n - 1) * SPREAD_SERIAL_FRAC, 2)})")
    print(f"  ② 합산 처리량 이득                : ×{res['throughput_gain']}  "
          f"({res['aggregate_tok_s']} / 단일 {res['single_tok_s']} tok/s · 병렬 ≥{GAIN_PARALLEL_MIN})")
    for e in res["errors"]:
        print(f"  ⚠️ {e}")

    v = res["verdict"]
    print()
    if v == "병렬":
        print(f"  ✅ **병렬** — 동시 {n}요청이 서버에서 함께 처리된다. 스테이지 내 팬아웃이 이득을 낸다.")
    elif v == "직렬":
        print(f"  ❌ **직렬** — 서버가 요청을 큐에 세운다. 스테이지 내 팬아웃 {n}개가 "
              f"이득 없이 {n}배 걸린다.")
        print(f"     → `launchctl setenv OLLAMA_NUM_PARALLEL \"{n}\"` 후 Ollama 재시작.")
        print(f"     ⚠️ KV 캐시가 슬롯 수만큼 늘어난다 — `OLLAMA_KV_CACHE_TYPE=q8_0` 과 짝으로 걸어라.")
    elif v == "부분병렬":
        print(f"  🟨 **부분 병렬** — 슬롯이 동시 요청 수보다 적다. NUM_PARALLEL 을 {n} 이상으로.")
    else:
        print(f"  ⚠️ **판정 보류** — 요청 {n}개 중 {len(res['per_req_wall_s'])}개만 완료했다.")


def main() -> int:
    ap = argparse.ArgumentParser(description="Ollama 동시 요청 병렬성 측정")
    ap.add_argument("-m", "--model", default=DEFAULT_MODEL, help=f"모델(기본 {DEFAULT_MODEL})")
    ap.add_argument("-n", type=int, default=3,
                    help="동시 요청 수(기본 3 = delegation.max_concurrent_children)")
    ap.add_argument("--reps", type=int, default=3, help="단일 기준선 반복(기본 3)")
    ap.add_argument("--timeout", type=int, default=600, help="요청 타임아웃 초(기본 600)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    try:
        with urllib.request.urlopen(OLLAMA + "/api/version", timeout=5):
            pass
    except Exception as exc:                        # noqa: BLE001
        print(f"⚠️ Ollama 에 닿지 못했다 ({OLLAMA}) — {exc}", file=sys.stderr)
        return 2

    res = probe(args.model, args.n, args.reps, args.timeout)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        render(res)
    return 1 if res["verdict"] == "직렬" else 0


if __name__ == "__main__":
    sys.exit(main())
