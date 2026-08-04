#!/usr/bin/env python3
"""
반려 게이트 자동화 (Solomon 게이트키퍼)
========================================
full 11단계 파이프라인의 검증 게이트를 강제한다.

문제: 검증자(fact-checker=6, reviewer=9)는 '수정요청'이어도 Kanban task를 정상
`completed`로 끝낸다. 판정은 outcome이 아니라 산출물/코멘트의 *텍스트*로만 존재하고,
다음 단계(7·10)로의 링크가 무조건 걸려 있어 반려가 무시된 채 진행된다.

해결: 이 게이트키퍼가 검증자 완료를 감지 → 판정(VERDICT)을 파싱 →
  - PASS  : downstream(children) unblock → 다음 단계 진행 허용
  - FAIL  : downstream을 blocked로 유지 + 리비전 루프 카드 자동 생성
            (producer 재작업 → 재검증 → downstream). 재검증 카드는 다시 검증자
            task 이므로 다음 폴에서 재평가된다(재귀).

핵심 원칙
  - Fail-closed: VERDICT 신호가 없거나 애매하면 FAIL로 간주(조용한 통과 금지).
  - 작성자≠검증자 유지: 게이트 *강제*는 오케스트레이션 레이어(=Solomon)인 이 스크립트가
    수행. 검증자는 판정 코멘트만 남긴다.
  - 그래프 기반 매핑: 검증자 task 의 parents=producer, children=downstream 로 직접 매핑
    (제목 파싱에 의존하지 않음).
  - 멱등: 리비전 카드는 --idempotency-key(검증자 task id 기준)로 중복 생성 방지.

사용:
  python3 gate_keeper.py               # 상시 루프(기본 10초 폴)
  python3 gate_keeper.py --once        # 1회 폴 후 종료(테스트/cron)
  python3 gate_keeper.py --dry-run     # 실제 변경 없이 판단만 로그
  python3 gate_keeper.py --interval 15 # 폴 간격(초)
"""
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
import sys
import time

# ── 설정 ────────────────────────────────────────────────────────────────
VERIFIERS = {"fact-checker", "reviewer"}         # 검증자 profile
STATE_PATH = os.environ.get("GATE_KEEPER_STATE", "/opt/data/gate_keeper_state.json")
SLACK_TARGET = os.environ.get("GATE_KEEPER_SLACK", "slack")  # bare = home(#mission-log)
COMPANY_ROOT = os.environ.get("GATE_KEEPER_COMPANY_ROOT", "/work/company")  # repo 마운트 경로
MAX_REVISION_ROUNDS = int(os.environ.get("GATE_KEEPER_MAX_ROUNDS", "2"))  # 게이트별 자동 리비전 상한
NOTIFY_TIMEOUT = int(os.environ.get("GATE_KEEPER_NOTIFY_TIMEOUT", "60"))  # Slack 통지 타임아웃(초)
MAX_DEFER = int(os.environ.get("GATE_KEEPER_MAX_DEFER", "6"))  # 판정 신호 미확정 시 재시도 횟수(race 방지)
_DEFER_COUNTS: dict = {}  # key -> 재시도 횟수(검증자 done 직후 VERDICT 코멘트 in-flight 대비)
_CHILD_DEFER_COUNTS: dict = {}  # key -> 자식 상태 조회 실패(None) 재시도 횟수(fail-open 방지)
HERMES = ["hermes", "kanban"]
VERDICT_RE = re.compile(r"VERDICT:\s*(PASS|FAIL)", re.IGNORECASE)
# fail-closed 폴백 키워드(표준 토큰이 없는 구 미션·누락 대비)
FAIL_WORDS = ("수정요청", "changes-requested", "보완요청", "반려")
PASS_WORDS = ("승인", "approve", "합격")


def log(msg: str) -> None:
    print(f"[gate-keeper] {msg}", flush=True)


# ── Hermes CLI 래퍼 ─────────────────────────────────────────────────────
def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """hermes kanban <args> 실행."""
    proc = subprocess.run(HERMES + args, capture_output=True, text=True)
    if check and proc.returncode != 0:
        log(f"WARN cmd failed ({proc.returncode}): kanban {' '.join(args)} :: {proc.stderr.strip()[:200]}")
    return proc


def kanban_json(args: list[str]):
    proc = run(args, check=False)
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None


def notify(text: str, dry: bool) -> None:
    """Slack #mission-log 통지(best-effort). GATE_KEEPER_NOTIFY=0 이면 비활성(테스트용)."""
    if dry:
        log(f"[dry] notify: {text}")
        return
    if os.environ.get("GATE_KEEPER_NOTIFY", "1") == "0":
        log(f"notify(off): {text}")
        return
    try:
        subprocess.run(["hermes", "send", "--to", SLACK_TARGET, text],
                       capture_output=True, text=True, timeout=NOTIFY_TIMEOUT)
    except Exception as e:  # noqa: BLE001 — 통지는 게이트 로직을 막지 않는다
        log(f"WARN notify failed: {e}")


# ── 상태(처리셋) 영속화 ──────────────────────────────────────────────────
def load_state() -> set:
    try:
        with open(STATE_PATH, encoding="utf-8") as f:
            return set(json.load(f).get("processed", []))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def save_state(processed: set) -> None:
    try:
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump({"processed": sorted(processed)}, f)
    except OSError as e:
        log(f"WARN state save failed: {e}")


# ── 판정 파싱 ────────────────────────────────────────────────────────────
def verdict_texts(show: dict) -> list[str]:
    """판정 신호 후보 텍스트(코멘트 전체 + latest_summary), 시간순."""
    texts = [c["body"] for c in (show.get("comments") or []) if c.get("body")]
    if show.get("latest_summary"):
        texts.append(show["latest_summary"])
    return texts


def verdict_signal_present(show: dict) -> bool:
    """명시 VERDICT 토큰 또는 pass/fail 키워드가 하나라도 있으면 True.
    검증자가 done 됐지만 아직 아무 신호가 없으면(코멘트 in-flight) False → 재시도."""
    for body in verdict_texts(show):
        if VERDICT_RE.search(body):
            return True
        if any(w in body for w in FAIL_WORDS) or any(w in body for w in PASS_WORDS):
            return True
    return False


def parse_verdict(show: dict, assignee: str) -> str:
    """PASS/FAIL 판정. VERDICT 토큰은 예약어이므로 author-무관 스캔. fail-closed.

    (assignee 인자는 호환성 위해 유지 — 토큰은 우리가 통제하는 신호라 저자 무관.)"""
    texts = verdict_texts(show)
    for body in reversed(texts):          # 최신 신호 우선
        m = VERDICT_RE.search(body)
        if m:
            return m.group(1).upper()
    # 폴백 키워드(구 미션·토큰 누락). fail 우선(fail-closed).
    blob = "\n".join(texts)
    if any(w in blob for w in FAIL_WORDS):
        return "FAIL"
    if any(w in blob for w in PASS_WORDS):
        return "PASS"
    return "FAIL"                          # 신호 없음 → fail-closed


def mission_of(title: str) -> str:
    m = re.search(r"(M-\d{4}-\d{3}|TEST-[A-Z0-9\-]+)", title or "")
    return m.group(1) if m else (title or "UNKNOWN").split("·")[0].strip()


def stage_tag(title: str) -> str:
    """게이트 단계 태그. '· 9 Independent Review'·'· G9R Re-Verify' 모두 'G9'."""
    m = re.search(r"·\s*G?(\d+)", title or "")
    return f"G{m.group(1)}" if m else "G"


def load_pipeline(mission: str) -> dict | None:
    """reports/<MID>/pipeline.json — 템플릿 번역기가 기록한 게이트 설정."""
    path = os.path.join(COMPANY_ROOT, "reports", mission, "pipeline.json")
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def objective_verdict(vid: str, title: str) -> tuple[str, str]:
    """검증자 task 의 객관(Python) 게이트 실행. 반환 (status, detail).
    status: PASS(모두 exit0) · FAIL(하나라도 실패; usage/missing 도 fail-closed) · SKIP(선언 없음/구 미션)."""
    mission = mission_of(title)
    pl = load_pipeline(mission)
    if not pl:
        return "SKIP", "pipeline.json 없음"
    stages = pl.get("stages", [])
    stage = next((s for s in stages if s.get("task_id") == vid), None)
    if not stage:
        # 리비전 재검증 카드(pipeline.json 미등록) → 제목의 단계번호(예 'G9R')로 원 stage 매칭
        m = re.search(r"(?:·\s*|G)(\d+)", title)
        if m:
            sid = int(m.group(1))
            stage = next((s for s in stages if s.get("id") == sid), None)
    gate = (stage or {}).get("gate") or {}
    objs = gate.get("objective") or []
    if not objs:
        return "SKIP", "객관 게이트 선언 없음"
    policy = os.path.join(COMPANY_ROOT, "reports", mission, "pipeline.json")  # 정책은 pipeline.json 안
    sources = os.path.join(COMPANY_ROOT, pl.get("sources_file") or f"reports/{mission}/raw/sources.yaml")
    draft = gate.get("draft")
    draft_abs = os.path.join(COMPANY_ROOT, draft) if draft else None
    results = []
    for g in objs:
        script = os.path.join(COMPANY_ROOT, "scripts", "gates", f"{g}.py")
        cmd = ["python3", script, "--policy", policy, "--sources", sources]
        if draft_abs:
            cmd += ["--draft", draft_abs]
        try:
            rc = subprocess.run(cmd, capture_output=True, text=True, timeout=60).returncode
        except Exception as e:  # noqa: BLE001
            log(f"  객관게이트 {g}: 실행오류 {e} → fail-closed")
            rc = 2
        ok = rc == 0
        note = "PASS" if ok else ("FAIL(입력없음·fail-closed)" if rc == 2 else "FAIL")
        log(f"  객관게이트 {g}: exit={rc} {note}")
        results.append(ok)
    return ("PASS" if all(results) else "FAIL"), f"gates={objs}"


def task_assignee(task_id: str) -> str | None:
    show = kanban_json(["show", task_id, "--json"])
    return (show or {}).get("task", {}).get("assignee") if show else None


def task_status(task_id: str) -> str | None:
    show = kanban_json(["show", task_id, "--json"])
    return (show or {}).get("task", {}).get("status") if show else None


# ── 게이트 처리 ──────────────────────────────────────────────────────────
def revision_round_count(mission: str, tag: str) -> int:
    """해당 미션·게이트(tag)에서 이미 생성된 리비전 라운드 수(archive 제외)."""
    tasks = kanban_json(["list", "--json"]) or []
    prefix = f"{mission} · {tag}R"
    return sum(1 for t in tasks
               if (t.get("title") or "").startswith(prefix) and "Revision" in (t.get("title") or ""))


def handle_pass(vid: str, title: str, children: list[str], dry: bool) -> None:
    if not children:
        log(f"PASS {vid} ({title}) — downstream 없음(종단). no-op")
        return
    for ds in children:
        st = task_status(ds)
        if st in ("blocked", "todo"):
            if dry:
                log(f"[dry] PASS → unblock downstream {ds}")
            else:
                run(["unblock", ds, "--reason", f"게이트 통과: {title} VERDICT=PASS"])
                log(f"PASS {vid} → downstream {ds} unblocked")
        else:
            log(f"PASS {vid} → downstream {ds} status={st} (unblock 불필요)")
    notify(f"✅ 게이트 통과 — {title} (VERDICT=PASS). 다음 단계 진행.", dry)


def handle_fail(vid: str, title: str, assignee: str, parents: list[str],
                children: list[str], instr: str, dry: bool) -> None:
    mission = mission_of(title)
    # downstream 을 blocked 로 유지(이미 ready/todo 면 게이트로 차단)
    for ds in children:
        st = task_status(ds)
        if st in ("ready", "todo", "running"):
            if dry:
                log(f"[dry] FAIL → hold downstream {ds} (block needs_input)")
            else:
                run(["block", ds, f"게이트 미통과 대기: {title}", "--kind", "needs_input"])
                log(f"FAIL {vid} → downstream {ds} held (blocked)")

    if not parents:
        log(f"FAIL {vid} — producer(parent) 없음. 리비전 생성 불가, downstream만 보류.")
        notify(f"⛔ 게이트 반려 — {title} (VERDICT=FAIL). producer 미상 → 수동 확인 필요.", dry)
        return
    producer = parents[0]
    prod_profile = task_assignee(producer) or "writer"
    tag = stage_tag(title)

    # ── 루프 상한: 같은 게이트에서 이미 MAX회 리비전했으면 자동 반복 중단하고 Sam 에스컬레이션 ──
    #   무한 반려 루프(예: 본질적 미검증 주장으로 검증자가 계속 FAIL) 방지. harness 의 'max 2회'와 정렬.
    prior = revision_round_count(mission, tag)
    if prior >= MAX_REVISION_ROUNDS:
        if dry:
            log(f"[dry] FAIL {vid} — 루프 상한({MAX_REVISION_ROUNDS}) 도달 → Sam 에스컬레이션")
            return
        run(["block", producer, f"자동 리비전 {prior}회 후에도 게이트 미통과({tag}) — Sam 판단 필요",
             "--kind", "needs_input"])
        log(f"FAIL {vid} → 루프 상한({MAX_REVISION_ROUNDS}) 도달. producer {producer} 에스컬레이션(blocked). 자동 리비전 중단.")
        notify(f"🟠 게이트 루프 상한 — {title} ({tag}) 자동 리비전 {prior}회 후에도 미통과.\n"
               f"검증자 판정이 수렴하지 않음(예: 본질적 미검증). Sam 검토·판단 요망.\n마지막 지시: {instr[:300]}", dry)
        return

    # 리비전 루프 카드(--parent 없음: producer 재작업은 즉시 ready).
    #   producer_rev ─link→ reverify ─link→ downstream. downstream 은 blocked 유지,
    #   승격은 게이트키퍼가 재검증 PASS 시에만 수행(FAIL 시 re-block 안전망).
    ws = ["--workspace", f"dir:/work/company/reports/{mission}"]
    rev_key = f"rev-{vid}"
    reverify_key = f"reverify-{vid}"
    rev_title = f"{mission} · {tag}R Revision"
    reverify_title = f"{mission} · {tag}R Re-Verify"
    body = (f"검증자 {assignee} 반려(VERDICT=FAIL). 아래 수정 지시를 반영하라.\n\n{instr}").strip()

    if dry:
        log(f"[dry] FAIL → create revision '{rev_title}'({prod_profile}) → "
            f"re-verify '{reverify_title}'({assignee}) → link→downstream {children}")
        notify(f"⛔ 게이트 반려 — {title} (VERDICT=FAIL). 리비전 루프 생성(dry).", dry)
        return

    rev = kanban_json(["create", rev_title, "--assignee", prod_profile, "--body", body,
                       "--idempotency-key", rev_key, *ws, "--json"])
    rev_id = (rev or {}).get("id") or (rev or {}).get("task", {}).get("id")
    rv = kanban_json(["create", reverify_title, "--assignee", assignee,
                      "--body", f"{rev_title} 수정본을 재검증하고 VERDICT: PASS|FAIL 판정.",
                      "--idempotency-key", reverify_key, *ws, "--json"])
    rv_id = (rv or {}).get("id") or (rv or {}).get("task", {}).get("id")

    if rev_id and rv_id:
        run(["link", rev_id, rv_id])                       # 재작업 → 재검증
        for ds in children:
            run(["link", rv_id, ds])                        # 재검증 → downstream(매핑용)
        log(f"FAIL {vid} → 리비전 루프 생성: {rev_id}({prod_profile}) → {rv_id}({assignee}) → {children}")
        notify(f"⛔ 게이트 반려 — {title} (VERDICT=FAIL)\n"
               f"→ 자동 리비전: {rev_title} → 재검증 → 다음 단계 보류.\n"
               f"수정지시: {instr[:300]}", dry)
    else:
        log(f"ERROR {vid} — 리비전 카드 생성 실패(rev={rev_id}, reverify={rv_id})")
        notify(f"⚠️ 게이트 반려 처리 중 카드 생성 실패 — {title}. 수동 확인 필요.", dry)


def verifier_instruction(show: dict, assignee: str) -> str:
    """판정 토큰이 담긴 마지막 텍스트에서 VERDICT 줄을 뺀 수정지시."""
    texts = verdict_texts(show)
    chosen = ""
    for body in reversed(texts):
        if VERDICT_RE.search(body):
            chosen = body
            break
    if not chosen and texts:
        chosen = texts[-1]
    instr = VERDICT_RE.sub("", chosen).strip() if chosen else ""
    return instr or "수정 지시는 검증 산출물(review/·verify/)을 참조."


# ── 자식 상태 분류 ─────────────────────────────────────────────────────────
def classify_children(children: list, status_of) -> tuple[list, list]:
    """downstream 자식을 (actionable, unknown) 으로 분류.
    - actionable : 아직 진행 대기(done/archived 아님)로 *확인된* 자식(게이트 대상).
    - unknown    : 상태 조회가 실패(None)해 *확정 불가*한 자식.

    핵심: None(조회 실패)을 종단(done/archived)과 섞지 않는다. 예전엔 둘을 함께
    actionable 에서 제거해, transient kanban 오류 한 번이 검증자를 processed 로 확정 →
    blocked downstream 을 영구 고아화(게이트 조용히 통과 = fail-open)했다. 이제 unknown 은
    별도로 돌려주고, 호출부가 fail-closed(보류·재시도)로 처리한다."""
    actionable, unknown = [], []
    for c in children:
        st = status_of(c)
        if st is None:
            unknown.append(c)
        elif st not in ("done", "archived"):
            actionable.append(c)
    return actionable, unknown


# ── 폴 1회 ───────────────────────────────────────────────────────────────
def poll_once(processed: set, dry: bool) -> None:
    tasks = kanban_json(["list", "--json"]) or []
    for t in tasks:
        if t.get("assignee") not in VERIFIERS:
            continue
        if t.get("status") != "done":
            continue
        vid = t.get("id")
        key = f"{vid}:{t.get('completed_at')}"
        if key in processed:
            continue
        show = kanban_json(["show", vid, "--json"])
        if not show:
            log(f"WARN {vid} show 실패 — skip")
            continue
        title = show.get("task", {}).get("title", "")
        assignee = t["assignee"]
        parents = show.get("parents") or []
        children = show.get("children") or []
        # 활성 게이트만 처리: downstream 중 아직 done/archived 아닌 것(=진행 대기)이 있어야 한다.
        # 완료된 미션(모든 downstream done)·종단 검증자(children 없음)는 건너뛴다 →
        # 과거 미션 재처리 방지, 사이드카 재시작에도 안전(상태파일 무관).
        actionable, unknown = classify_children(children, task_status)
        # fail-closed: 자식 상태를 하나라도 확정 못하면(kanban 조회 실패=None) 종단으로
        # 오인해 게이트를 조용히 통과시키지 않는다. 다음 폴에서 재시도(processed 미기록).
        # MAX_DEFER 초과 시에만 확인된 자식으로 진행(무한 보류 방지 — 삭제된 자식 등 대비).
        if unknown:
            n = _CHILD_DEFER_COUNTS.get(key, 0) + 1
            _CHILD_DEFER_COUNTS[key] = n
            if n <= MAX_DEFER:
                log(f"자식 상태 미확정: {vid} '{title}' children={unknown} — 재시도 {n}/{MAX_DEFER}(조회실패 대비)")
                continue
            log(f"자식 상태 미확정: {vid} — {MAX_DEFER}회 후 확인된 자식만으로 진행")
        if not actionable:
            if not dry:
                processed.add(key)
            continue
        # race 방지: 검증자가 done 이지만 VERDICT 신호가 아직 없으면(코멘트 in-flight)
        # 이번 폴은 건너뛰고(처리셋 미기록) 다음 폴에서 재시도. MAX_DEFER 후에도 없으면 fail-closed.
        if not verdict_signal_present(show):
            n = _DEFER_COUNTS.get(key, 0) + 1
            _DEFER_COUNTS[key] = n
            if n <= MAX_DEFER:
                log(f"판정 신호 미확정: {vid} '{title}' — 재시도 {n}/{MAX_DEFER}(코멘트 in-flight 대비)")
                continue
            log(f"판정 신호 없음: {vid} — {MAX_DEFER}회 후 fail-closed(FAIL)")
        llm_verdict = parse_verdict(show, assignee)
        obj_status, obj_detail = objective_verdict(vid, title)
        # 이중 게이트 결합: 객관 FAIL 이면 LLM 무관 FAIL(fail-closed). 그 외 LLM 판정 채택.
        verdict = "FAIL" if obj_status == "FAIL" else llm_verdict
        log(f"검증자 완료 감지: {vid} '{title}' assignee={assignee} → "
            f"객관={obj_status} · LLM={llm_verdict} ⇒ VERDICT={verdict} (downstream {actionable})")
        if verdict == "PASS":
            handle_pass(vid, title, actionable, dry)
        else:
            instr = verifier_instruction(show, assignee)
            if obj_status == "FAIL":
                instr = f"[객관 게이트 실패 {obj_detail}] " + instr
            handle_fail(vid, title, assignee, parents, actionable, instr, dry)
        if not dry:
            processed.add(key)
    if not dry:
        save_state(processed)


def main() -> int:
    ap = argparse.ArgumentParser(description="반려 게이트 자동화 (Solomon 게이트키퍼)")
    ap.add_argument("--once", action="store_true", help="1회 폴 후 종료")
    ap.add_argument("--dry-run", action="store_true", help="실제 변경 없이 판단만 로그")
    ap.add_argument("--interval", type=float, default=10.0, help="폴 간격(초, 기본 10)")
    args = ap.parse_args()

    log(f"start (once={args.once} dry_run={args.dry_run} interval={args.interval}s state={STATE_PATH})")
    processed = load_state()
    if args.once:
        poll_once(processed, args.dry_run)
        return 0
    while True:
        try:
            poll_once(processed, args.dry_run)
        except Exception as e:  # noqa: BLE001 — 루프는 죽지 않는다
            log(f"ERROR poll: {e}")
        time.sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())
