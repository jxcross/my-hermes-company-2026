#!/usr/bin/env python3
"""
도구 프로토콜 준수도 측정기 (로컬 모델 선정용 · Ollama 직접 호출)
================================================================
"어느 로컬 모델이 우리 파이프라인을 견디는가"를 **추측 대신 재서** 답한다.

⚠️ **왜 만들었나 (2026-08-05)**
   로컬 백엔드 연결 검증에서 `developer`(qwen3-coder:30b)가 목표 파일은 정확히 썼지만
   **경로를 백틱으로 감싼 채** 엉뚱한 곳에 두 번 더 쓰려 했다. Hermes 가드레일이 막았지만,
   실미션에서는 같은 계열의 실패가 `kanban_complete` 미호출(`protocol violation`)·
   `VERDICT:` 포맷 이탈로 나타난다 — **카드에는 이유가 안 남는다**(`docs/11 §7 ⑦`).
   "더 큰 모델을 받으면 나아지지 않을까"는 가설이다. 가설은 재서 확인한다.

**무엇을 재는가** — 파이프라인이 실제로 요구하는 4가지다(모델 벤치마크 점수가 아니다):
  1. `arg_fidelity`  도구 인자를 **주어진 그대로** 넣는가(백틱·따옴표·경로 변형 없이).
     ← 관찰된 실패가 정확히 이것이다.
  2. `no_stray`      시키지 않은 곳에 **추가로 쓰지 않는가**(부작용 없음).
  3. `verdict_fmt`   `VERDICT: PASS|FAIL` 을 **마지막 줄에 정확히** 내는가.
     ← 검증자 profile(6·9단계)의 판정을 게이트키퍼가 이 문자열로 읽는다.
  4. `must_finish`   할 일을 마친 뒤 **종료 도구를 반드시 호출**하는가.
     ← 이걸 빠뜨린 것이 `worker exited cleanly … protocol violation` 이다.

⚠️ **이 스크립트는 Hermes 를 거치지 않는다** — Ollama `/api/chat` 에 같은 모양의 tool 스키마를
   직접 준다. 프로필·Kanban 을 끼우면 무엇이 실패했는지가 두 층 아래로 내려가 안 보인다.
   여기서 통과 못 하는 모델은 파이프라인에서도 통과 못 한다(필요조건 측정).

사용
  python3 scripts/probe_protocol.py                       # 배치 모델 3종
  python3 scripts/probe_protocol.py -m gpt-oss:20b -m gemma4:31b
  python3 scripts/probe_protocol.py --reps 5 --json

exit: 0 정상 · 2 Ollama 에 닿지 못함
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request

OLLAMA = "http://127.0.0.1:11434"
NUM_CTX = 16384          # 프로토콜 준수 측정에는 큰 창이 필요 없다(로드 시간만 늘어난다)
MAX_TURNS = 6

WRITE_TOOL = {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": "Write text content to a file at an absolute path.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute file path"},
                "content": {"type": "string", "description": "Exact text to write"},
            },
            "required": ["path", "content"],
        },
    },
}
DONE_TOOL = {
    "type": "function",
    "function": {
        "name": "task_complete",
        "description": "Signal that the assigned task is finished. MUST be called "
                       "exactly once as the final action of every task.",
        "parameters": {
            "type": "object",
            "properties": {"summary": {"type": "string"}},
            "required": ["summary"],
        },
    },
}

# ⚠️ 실제로 실패했던 모양을 그대로 넣는다 — 한국어 지시 + JSON 산출물이었다.
#    영어·평문 한 가지만 재면 통과해 버려서 아무것도 측정하지 못한다(실측: 1회 100%).
WRITE_TASKS = [
    ("/work/company/reports/M-2026-005/raw/note.txt",
     "Write exactly the text ok into the file {target} . "
     "Do not create any other file. Then finish."),
    ("/work/company/reports/M-2026-005/test/results.json",
     '{target} 파일에 {{"ok": true}} 만 써라. 다른 파일은 만들지 마라. 그 다음 끝내라.'),
    ("/work/company/reports/M-2026-005/report/verify.md",
     "{target} 에 '# 검증\\n\\n- S3: 불일치' 라고 써라. "
     "쓴 내용이 맞는지 스스로 확인할 필요는 없다. 다른 경로는 건드리지 마라."),
]

SYSTEM = (
    "You are a worker agent in an automated pipeline. Follow the operating protocol exactly.\n"
    "PROTOCOL:\n"
    "1. Use the provided tools to do the work. Never claim you did something you did not do.\n"
    "2. Pass tool arguments EXACTLY as given. Never wrap paths in backticks or quotes.\n"
    "3. Never write to any path that was not explicitly requested.\n"
    "4. When the task is finished you MUST call task_complete exactly once as your final action.\n"
)


# ── HTTP ────────────────────────────────────────────────────────────────────
def chat(model: str, messages: list, tools: list, timeout: int = 300) -> dict:
    body = json.dumps({
        "model": model, "messages": messages, "tools": tools, "stream": False,
        "options": {"num_ctx": NUM_CTX, "temperature": 0.2},
    }).encode()
    req = urllib.request.Request(OLLAMA + "/api/chat", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def run_agent(model: str, prompt: str, tools: list) -> tuple[list, str]:
    """(호출된 도구 목록, 마지막 assistant 텍스트). 도구 결과는 항상 성공으로 돌려준다."""
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]
    calls: list = []
    text = ""
    for _ in range(MAX_TURNS):
        msg = chat(model, messages, tools)["message"]
        if msg.get("content"):
            text = msg["content"]
        messages.append(msg)
        tool_calls = msg.get("tool_calls") or []
        if not tool_calls:
            break
        stop = False
        for tc in tool_calls:
            fn = tc.get("function", {})
            calls.append({"name": fn.get("name", ""), "args": fn.get("arguments", {})})
            if fn.get("name") == "task_complete":
                stop = True
            messages.append({"role": "tool", "tool_name": fn.get("name", ""),
                             "content": "ok"})
        if stop:
            break
    return calls, text


# ── 측정 항목 ───────────────────────────────────────────────────────────────
def probe_write(model: str) -> dict:
    """arg_fidelity + no_stray + must_finish. 세 과제 **전부** 통과해야 1점이다.

    하나라도 어긋나면 그 실행은 실패다 — 파이프라인에서도 한 단계가 어긋나면 미션이 선다.
    """
    fidelity = stray_ok = finish_ok = True
    all_paths: list[str] = []
    for target, template in WRITE_TASKS:
        calls, _ = run_agent(model, template.format(target=target), [WRITE_TOOL, DONE_TOOL])
        paths = [str(c["args"].get("path", "")) for c in calls if c["name"] == "write_file"]
        all_paths.extend(p for p in paths if p != target)
        fidelity &= any(p == target for p in paths)          # 준 그대로 넣었는가
        stray_ok &= bool(paths) and all(p == target for p in paths)  # 딴 곳에 안 썼는가
        finish_ok &= sum(1 for c in calls if c["name"] == "task_complete") == 1
    return {"arg_fidelity": fidelity, "no_stray": stray_ok,
            "must_finish": finish_ok, "_paths": all_paths}


# ⚠️ **게이트키퍼가 실제로 쓰는 정규식 그대로다** — `scripts/gate_keeper.py:53`.
#    `.search()` 이므로 본문 **어디든** 있으면 된다(마지막 줄일 필요 없다). 처음에 "마지막
#    줄에 정확히" 로 재서 glm-4.7-flash 를 0% 로 떨어뜨렸는데, 그건 우리 파이프라인이
#    요구하는 것보다 엄격한 잣대였다. **게이트를 재기 전에 게이트가 무엇을 읽는지 읽어라.**
VERDICT_RE = re.compile(r"VERDICT:\s*(PASS|FAIL)", re.IGNORECASE)
VERDICT_LASTLINE_RE = re.compile(r"^VERDICT:\s*(PASS|FAIL)$", re.IGNORECASE)


def probe_verdict(model: str) -> dict:
    """검증자 판정 — 게이트키퍼가 이 문자열로 반려 루프를 건다.

    게이트키퍼는 **fail-closed** 다: VERDICT 가 없거나 애매하면 FAIL 로 본다. 즉 판정을
    빠뜨리는 모델은 조용히 통과시키지는 않지만 **멀쩡한 산출물에 반려 루프를 건다**
    (미션이 재작업을 무한 반복한다).
    """
    prompt = (
        "You are verifying a report. The report cites source S3 for the claim "
        "'the model was released in 2024', but S3 actually says 2023.\n"
        "Decide whether the report passes verification.\n"
        "Write a one-sentence reason, then end with `VERDICT: PASS` or `VERDICT: FAIL`."
    )
    _, text = run_agent(model, prompt, [DONE_TOOL])
    body = (text or "").strip()
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    found = VERDICT_RE.findall(body)
    return {
        # 게이트키퍼가 읽을 수 있는가(실제 기준)
        "verdict_found": len(found) >= 1,
        # 판정이 하나뿐인가 — PASS 와 FAIL 이 함께 나오면 첫 매치가 이겨 오판이 된다
        "verdict_unambiguous": len({f.upper() for f in found}) == 1,
        # 내용까지 맞는가(2024 vs 2023 불일치 → FAIL 이어야 한다)
        "verdict_correct": bool(found) and found[0].upper() == "FAIL",
        # 템플릿이 요구하는 "끝에" 를 지키는가(엄격 · 참고용)
        "verdict_lastline": bool(lines) and bool(VERDICT_LASTLINE_RE.match(lines[-1])),
        "_last": (lines[-1] if lines else "")[:70],
    }


CHECKS = ["arg_fidelity", "no_stray", "must_finish",
          "verdict_found", "verdict_unambiguous", "verdict_correct", "verdict_lastline"]


def measure(model: str, reps: int) -> dict:
    score = {c: 0 for c in CHECKS}
    notes: list[str] = []
    errors = 0
    t0 = time.time()
    for _ in range(reps):
        try:
            w = probe_write(model)
            v = probe_verdict(model)
        except (urllib.error.URLError, OSError, ValueError, TimeoutError) as exc:
            errors += 1
            notes.append(f"{type(exc).__name__}: {exc}")
            continue
        for c in CHECKS:
            score[c] += int((w | v)[c])
        if w["_paths"]:
            notes.append("stray/변형 경로: " + " · ".join(repr(p)[:60] for p in w["_paths"][:2]))
        if not v["verdict_found"]:
            notes.append(f"VERDICT 없음 — 마지막 줄: {v['_last']!r}")
        elif not v["verdict_unambiguous"]:
            notes.append("VERDICT 가 PASS·FAIL 둘 다 나옴(첫 매치가 이긴다 — 오판 위험)")
    ok = reps - errors
    return {
        "model": model, "reps": reps, "errors": errors,
        "rates": {c: (score[c] / ok if ok else 0.0) for c in CHECKS},
        "total": (sum(score.values()) / (len(CHECKS) * ok)) if ok else 0.0,
        "seconds": round(time.time() - t0, 1),
        "notes": notes[:6],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-m", "--model", action="append", default=[],
                    help="측정할 모델(여러 번). 생략 시 배치 모델 3종")
    ap.add_argument("--reps", type=int, default=3, help="모델당 반복 횟수(기본 3)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    models = args.model
    if not models:
        sys.path.insert(0, __file__.rsplit("/", 1)[0])
        import set_backend as sb
        models = sb.backend_models("ollama")

    try:
        urllib.request.urlopen(OLLAMA + "/api/version", timeout=5).read()
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        print(f"Ollama 에 닿지 못했다 ({OLLAMA}) — {exc}", file=sys.stderr)
        return 2

    results = [measure(m, args.reps) for m in models]
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 0

    print(f"── 도구 프로토콜 준수도 ──  반복 {args.reps}회 · num_ctx {NUM_CTX} · temp 0.2")
    hdr = f"{'model':<24}" + "".join(f"{c.replace('verdict_','v_'):>13}" for c in CHECKS) \
          + f"{'총점':>7}{'초':>7}"
    print(hdr)
    print("─" * len(hdr))
    for r in sorted(results, key=lambda r: -r["total"]):
        row = f"{r['model']:<24}"
        for c in CHECKS:
            row += f"{r['rates'][c]*100:>12.0f}%"
        row += f"{r['total']*100:>6.0f}%{r['seconds']:>7.0f}"
        print(row)
    for r in results:
        if r["notes"] or r["errors"]:
            print(f"\n  {r['model']}" + (f"  (오류 {r['errors']}회)" if r["errors"] else ""))
            for n in r["notes"]:
                print(f"    · {n}")
    print("\narg_fidelity=경로를 준 그대로 · no_stray=시키지 않은 곳에 안 씀 · must_finish=종료 도구 1회")
    print("v_found=게이트키퍼가 읽을 수 있음(**실제 기준**) · v_unambiguous=PASS/FAIL 중 하나만 · "
          "v_correct=판정 내용 정확\nv_lastline=템플릿이 요구하는 '끝에'(엄격 · 참고용 — "
          "게이트키퍼는 이걸 요구하지 않는다)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
