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
import contextlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request

# ── 설정 ────────────────────────────────────────────────────────────────
VERIFIERS = {"fact-checker", "reviewer"}         # 검증자 profile(폴백 — 진실은 pipeline.json)
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

# ── Sam 승인 게이트(Slack Web API) 설정 ─────────────────────────────────────
# Socket Mode(인바운드)가 network 성으로 flapping 하므로, 승인 흐름은 Web API 폴링으로
# 처리해 의존을 끊는다(gate_keeper 와 동일한 결정적 오케스트레이션 레이어).
APPROVALS_CHANNEL = os.environ.get("GATE_KEEPER_APPROVALS_CHANNEL", "C0BN936JUM6")  # #approvals
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
# 승인 권한자(Sam) member id 목록. 이 사용자들의 메시지만 승인으로 인정(보안 앵커).
SLACK_ALLOWED_USERS = {u.strip() for u in os.environ.get("SLACK_ALLOWED_USERS", "").split(",") if u.strip()}
APPROVAL_ENABLED = os.environ.get("GATE_KEEPER_APPROVALS", "1") != "0"
APPROVAL_WORDS = ("승인", "approve", "approved", "go ahead")
DENY_WORDS = ("반려", "거부", "보류", "reject", "hold")   # 승인 오탐 방지(부정형 스킵)
TASK_ID_RE = re.compile(r"\b(t_[0-9a-f]{6,})\b")          # 명시 task id 토큰
HISTORY_LIMIT = int(os.environ.get("GATE_KEEPER_APPROVALS_LIMIT", "25"))


def log(msg: str) -> None:
    print(f"[gate-keeper] {msg}", flush=True)


# ── 보드 스코프 ─────────────────────────────────────────────────────────
# 미션마다 Kanban 보드를 새로 만든다(Sam 지시 2026-08-05). 게이트키퍼는 원래
# **단일 보드 가정**이었고, 그대로 두면 다른 보드의 미션은 `poll_once` 의 목록에
# 아예 안 잡혀 **검증 게이트가 영영 안 돌고 downstream 이 blocked 로 남는다 —
# 그리고 로그 한 줄도 안 남는다**(`VERIFIERS` 하드코딩 결함과 같은 모양 · docs/11 §7).
#
# ⚠️ `--board` 는 **전역 플래그 — 서브커맨드 앞**이다.
#      hermes kanban --board <slug> list --json   ✓
#      hermes kanban list --board <slug>          ✗
#    그래서 주입 지점은 argv 를 만드는 `run()` 한 곳뿐이다.
# ⚠️ kwarg 가 아니라 **모듈 전역 + contextmanager** 를 쓴다. 호출이 3단계까지 중첩되고
#    (`poll_once → handle_fail → revision_round_count → kanban_json`), 그중 둘은 함수를
#    **참조로** 넘긴다(`classify_children(children, task_status)`). kwarg 로 하면 그 자리에
#    partial/lambda 를 끼워야 하는데, `classify_children` 의 2인자 계약은 테스트 4종이
#    어설션한다. Hermes 자신도 같은 모양을 쓴다(`kanban_db.py` `_CURRENT_BOARD_OVERRIDE`).
# ⚠️ 이 모듈은 단일 스레드다(main → tick 순차). 스레드가 생기면 ContextVar 로 바꿔라.
_BOARD: str | None = None


@contextlib.contextmanager
def board_scope(slug: str | None):
    """이 블록 안의 모든 kanban 호출을 <slug> 보드로 보낸다. None/'default' = 기본 보드."""
    global _BOARD
    prev = _BOARD
    _BOARD = None if (slug in (None, "", "default")) else slug
    try:
        yield
    finally:
        _BOARD = prev


def current_board() -> str:
    return _BOARD or "default"


# ── Hermes CLI 래퍼 ─────────────────────────────────────────────────────
def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """hermes kanban [--board <slug>] <args> 실행."""
    argv = list(HERMES)
    if _BOARD:
        argv += ["--board", _BOARD]      # ★ 반드시 서브커맨드 **앞**
    proc = subprocess.run(argv + args, capture_output=True, text=True)
    if check and proc.returncode != 0:
        log(f"WARN cmd failed ({proc.returncode}) [board={current_board()}]: "
            f"kanban {' '.join(args)} :: {proc.stderr.strip()[:200]}")
    return proc


def kanban_json(args: list[str]):
    proc = run(args, check=False)
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None


def active_boards() -> list[str]:
    """폴 대상 보드. 권위는 `boards list --json` 이다.

    ⚠️ `pipeline.json` 의 board 필드만으로 열거하면 **밖에서 만든 보드를 못 본다.**
       가장 현실적인 경로가 인스턴스화 자체다 — 번역기는 카드를 먼저 만들고
       `pipeline.json` 을 **마지막에** 쓴다. 그 사이에 죽으면 카드는 있는데
       pipeline.json 이 없는 보드가 남고, 그 미션은 게이트키퍼에게 **영원히 보이지
       않는다**(로그도 안 남는다 — 이 파일이 고치려는 그 결함과 같은 모양).

    ⚠️ 조회 실패 시 조용히 `default` 로 축소하지 않는다 — 그것이 fail-open 이다.
       pipeline.json 합집합으로 내려가되 **반드시 로그를 남긴다.**
    """
    with board_scope(None):   # 보드 목록 자체는 특정 보드의 것이 아니다
        boards = kanban_json(["boards", "list", "--json"])
    if isinstance(boards, list):
        slugs = [b.get("slug") for b in boards
                 if isinstance(b, dict) and b.get("slug") and not b.get("archived")]
        if slugs:
            return slugs
    known = {"default"} | {(pl.get("board") or "default") for pl in load_all_pipelines()}
    log(f"WARN boards list 조회 실패 — pipeline.json 기준으로 축약 열거: {sorted(known)}")
    return sorted(known)


def board_of(mission: str) -> str:
    """미션이 도는 보드. 구 미션의 pipeline.json 에는 board 키가 없다 → default."""
    pl = load_pipeline(mission)
    return (pl or {}).get("board") or "default"


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


# ── 상태 영속화 ────────────────────────────────────────────────────────────
# 단일 JSON 파일에 세 처리셋을 보관(멱등·재시작 안전):
#   processed        : 검증자 게이트 처리 키(vid:completed_at)
#   approval_posted  : #approvals 에 승인요청을 이미 게시한 Sam-게이트 task id
#   approval_seen    : 이미 처리한 승인 메시지 ts(중복 unblock 방지)
def load_state() -> dict:
    try:
        with open(STATE_PATH, encoding="utf-8") as f:
            d = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        d = {}
    return {
        "processed": set(d.get("processed", [])),
        "approval_posted": set(d.get("approval_posted", [])),
        "approval_seen": set(d.get("approval_seen", [])),
    }


def save_state(state: dict) -> None:
    try:
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump({k: sorted(state.get(k, set())) for k in
                       ("processed", "approval_posted", "approval_seen")}, f)
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


def verifier_profiles() -> set[str]:
    """검증자 profile 집합 — **템플릿이 선언한 것을 진실로 삼는다.**

    ⚠️ 하드코딩(`VERIFIERS`)만 쓰면 템플릿이 새 검증자 profile 을 선언했을 때 게이트키퍼가
       그 stage 를 **아예 쳐다보지 않는다.** downstream 은 `blocked` 인 채 영구 정지하고,
       리비전 루프도 생성되지 않으며, **로그도 남지 않아** 원인 파악이 어렵다.
       실측(2026-08-05): 템플릿 20종의 `verifier: true` stage 는 fact-checker 29 · reviewer 24 ·
       **`tester` 1**(`webapp-build` stage 8 `Test & Verify`) — 그 미션은 stage 9 에서 조용히 멎는다.

    `pipeline.json` 이 stage 마다 `verifier`·`profile` 을 기록하므로 그것을 읽는다.
    리비전 재검증 카드는 pipeline.json 에 없지만 **검증자와 같은 profile 로 생성**되므로
    profile 단위 집합이면 함께 잡힌다(task_id 단위로 보면 놓친다).
    하드코딩은 pipeline.json 이 없는 구 미션을 위한 폴백으로만 남긴다.
    """
    out = set(VERIFIERS)
    for pl in load_all_pipelines():
        for s in pl.get("stages", []):
            if s.get("verifier") and s.get("profile"):
                out.add(str(s["profile"]).strip())
    return out


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
    """활성 보드를 **전부** 돈다.

    ⚠️ 예전에는 여기서 `kanban list --json` 을 한 번만 불렀고, 그것은 기본 보드만
       본다는 뜻이었다. 미션마다 보드를 새로 만들면 그 미션들은 **아예 목록에 안 잡히고,
       검증 게이트가 영영 안 돌고, downstream 이 blocked 로 남고, 로그도 안 남는다.**
    """
    for slug in active_boards():
        with board_scope(slug):
            _poll_board(slug, processed, dry)


def _poll_board(slug: str, processed: set, dry: bool) -> None:
    tasks = kanban_json(["list", "--json"]) or []
    verifiers = verifier_profiles()   # 템플릿 선언 기준(폴백=VERIFIERS) — 위 함수의 ⚠️ 참조
    for t in tasks:
        if t.get("assignee") not in verifiers:
            continue
        if t.get("status") != "done":
            continue
        vid = t.get("id")
        # ⚠️ 키에 보드를 넣는다. task id 는 보드마다 독립적으로 발급되므로
        #    보드가 다르면 같은 id 가 존재할 수 있다.
        key = f"{slug}:{vid}:{t.get('completed_at')}"
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


# ── Sam 승인 게이트: Slack Web API 폴링(#4 요청 게시 + #3 승인→unblock) ─────────
def slack_api(method: str, params: dict, post: bool = False) -> dict | None:
    """Slack Web API 호출(stdlib urllib). 실패 시 None(루프는 죽지 않음)."""
    if not SLACK_BOT_TOKEN:
        return None
    try:
        headers = {"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}
        if post:
            data = urllib.parse.urlencode(params).encode()
            req = urllib.request.Request(f"https://slack.com/api/{method}", data=data, headers=headers)
        else:
            url = f"https://slack.com/api/{method}?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.load(r)
    except Exception as e:  # noqa: BLE001 — 승인 폴링은 게이트 로직을 막지 않는다
        log(f"WARN slack_api {method} 실패: {e}")
        return None


def parse_approval(text: str) -> tuple[bool, str | None]:
    """메시지 텍스트 → (승인 여부, 명시 task_id|None).
    부정형(반려/거부/보류)이 있으면 승인 아님(오탐 방지). 승인 키워드가 있어야 True."""
    if not text:
        return False, None
    low = text.lower()
    if any(w in text or w in low for w in DENY_WORDS):
        return False, None
    if not any(w in text or w in low for w in APPROVAL_WORDS):
        return False, None
    m = TASK_ID_RE.search(text)
    return True, (m.group(1) if m else None)


def pending_sam_gates(pipelines: list[dict]) -> list[dict]:
    """현재 blocked 인 Sam-게이트 stage 목록(task_id·mission·name). pipeline.json 기반."""
    out = []
    for pl in pipelines:
        for s in pl.get("stages", []):
            if not s.get("sam_gate"):
                continue
            tid = s.get("task_id")
            if not tid:
                continue
            # ⚠️ 미션마다 보드가 다르다. 기본 보드에서 조회하면 다른 보드의 게이트는
            #    상태가 None 으로 나와 **#approvals 에 영영 안 올라간다.**
            board = pl.get("board") or "default"
            with board_scope(board):
                st = task_status(tid)
            if st == "blocked":
                out.append({"task_id": tid, "mission": pl.get("mission"), "name": s.get("name"),
                            "board": board,
                            "upstream": s.get("upstream_task_ids") or []})
    return out


def all_upstream_done(upstream: list[str], board: str | None = None) -> bool:
    """상위(upstream) task 가 모두 done/archived 여야 이 게이트가 '활성'(승인 차례).

    ⚠️ upstream 은 같은 보드에 있다. board 를 안 주면 기본 보드를 조회해 **전부 None** 이
       나오고, 그러면 이 게이트는 영원히 '활성 아님' 으로 판정된다(조용한 정지).
    """
    if not upstream:
        return True
    with board_scope(board):
        return all(task_status(u) in ("done", "archived") for u in upstream)


def load_all_pipelines() -> list[dict]:
    """reports/*/pipeline.json 전부 로드(활성 미션 게이트 조회용)."""
    base = os.path.join(COMPANY_ROOT, "reports")
    out = []
    try:
        for mid in os.listdir(base):
            pl = load_pipeline(mid)
            if pl:
                out.append(pl)
    except OSError:
        pass
    return out


def _read_head(path: str, n: int) -> str:
    """파일 앞부분 n자(없으면 '')."""
    try:
        with open(path, encoding="utf-8") as f:
            t = f.read(n + 1)
        return (t[:n] + "…") if len(t) > n else t
    except OSError:
        return ""


def _extract_section(md: str, needle: str, n: int) -> str:
    """마크다운에서 heading 에 needle 포함된 섹션 본문(다음 heading 전까지) 발췌."""
    out, cap = [], False
    for ln in md.splitlines():
        if ln.lstrip().startswith("#"):
            if cap:
                break
            cap = needle in ln
            continue
        if cap:
            out.append(ln)
    text = "\n".join(out).strip()
    return (text[:n] + "…") if len(text) > n else text


def _compact_policy(pol: dict) -> str:
    parts = []
    rp = pol.get("recency_policy") or {}
    if rp.get("recent_ratio") is not None:
        parts.append(f"recency(recent≥{rp.get('recent_ratio')})")
    mp = (pol.get("source_balance_policy") or {}).get("min_per_category") or {}
    hit = "·".join(f"{k}≥{v}" for k, v in mp.items() if v)
    if hit:
        parts.append("source_balance(min " + hit + ")")
    return ", ".join(parts)


def _compact_completion(pol: dict) -> str:
    cp = pol.get("completion_policy") or {}
    on = [k.replace("require_", "") for k, v in cp.items() if v]
    return ("완료조건(" + "·".join(on) + ")") if on else ""


def approval_artifact_of(g: dict, pl: dict) -> str | None:
    """중간 Sam 게이트가 '무엇을 보고 승인할지'. 템플릿이 stage.approval_artifact 로 선언한다."""
    st = next((s for s in pl.get("stages", []) if s.get("task_id") == g.get("task_id")), None)
    return (st or {}).get("approval_artifact")


def gate_summary(g: dict, pl: dict) -> str:
    """승인요청에 담을 게이트 핵심 내용. 세 경우로 갈린다:
    진입(upstream 없음)=계획·정책 · 중간(approval_artifact 선언)=그 산출물 발췌 · 산출=보고서 요약."""
    mission = g["mission"]
    root = os.path.join(COMPANY_ROOT, "reports", mission)
    L = []
    topic = pl.get("topic")
    if topic:
        L.append(f"• 주제: {topic}")
    artifact = approval_artifact_of(g, pl)
    if artifact and g["upstream"]:
        # 중간 게이트(예: 목차 승인·실행계획 승인) — 진입도 산출도 아니다.
        # 기존 코드는 이 경우 report.md 를 찾다 실패해 산출물 목록만 나열했다.
        body = _read_head(os.path.join(COMPANY_ROOT, artifact), 1200)
        L.append(f"• 승인 대상: {artifact}")
        if body:
            L.append("• 내용 발췌:\n" + body)
        else:
            L.append("⚠ 승인 대상 파일을 읽지 못했다 — 산출 여부를 확인하라.")
        L.append("• 승인 시: 이 산출물을 확정하고 다음 단계(구현·집필)로 진행한다. "
                 "되돌리려면 이후 작업을 폐기해야 하므로 지금 검토하라.")
    elif not g["upstream"]:
        # 진입 게이트(예: Scoping) — 무엇을 실행할지(계획·정책)
        stages = pl.get("stages", [])
        if stages:
            L.append("• 파이프라인: " + " → ".join(f"{s['id']}·{s['name']}" for s in stages))
        pol = ", ".join(x for x in (_compact_policy(pl.get("policy") or {}),
                                    _compact_completion(pl.get("policy") or {})) if x)
        if pol:
            L.append("• 정책: " + pol)
        scope = _read_head(os.path.join(root, "SCOPE.md"), 700)
        if scope:
            L.append("• SCOPE 발췌:\n" + scope)
    else:
        # 산출 게이트(예: Deliver) — 무엇을 공개할지. 아키타입마다 최종 산출 파일명이 다르다
        # (A=report.md · B=draft.md · D=spec/·test/). 있는 것을 찾아 요약한다.
        md, name = "", ""
        for cand in ("report.md", "draft.md", "paper.md", "README.md"):
            md = _read_head(os.path.join(root, cand), 20000)
            if md:
                name = cand
                break
        summ = _extract_section(md, "요약", 900) if md else ""
        if summ:
            L.append(f"• 산출 요약({name}):\n" + summ)
        elif md:
            L.append(f"• 산출 발췌({name}):\n" + md[:700] + "…")
        L.append("• 공개 대상: git 커밋(reports/) + Slack 게시 — 승인 시 실행.")
    try:
        arts = [f for f in sorted(os.listdir(root)) if os.path.isfile(os.path.join(root, f))]
        if arts:
            L.append("• 산출물: " + ", ".join(arts[:12]))
    except OSError:
        pass
    insp = artifact_inspection(root)
    if insp:
        L.append(insp)
    return "\n".join(L) or "(요약 없음 — reports/ 산출물 직접 확인 요망)"


# ⚠️⚠️ 왜 이게 있는가 (2026-08-05 · docs/11 §7 ⑧)
#   M-2026-005 stage 8 승인 요청이 Sam 에게 이렇게 갔다: "검증 통과했으니 집필 시작할까요."
#   그 시점에 stage 5 분석 11편 중 8편은 원문을 읽지 않고 작성된 껍데기였다. 승인 요청문은
#   **검증자의 판정을 그대로 옮기는데, 그 판정이 틀렸기 때문이다.**
#   사람이 최종 방어선인데 **그 사람에게 가는 정보가 이미 오염돼 있었다.**
#   → 승인문에 판정만이 아니라 **산출물의 실측치**를 함께 싣는다. 게이트가 못 본 것을
#     사람이 볼 기회를 준다. 판정과 실측이 어긋나면 그 자체가 신호다.
SUSPECT_RE = re.compile(
    r"\[[^\]\n]{0,120}?(?:simulat|synthesi[sz]ed\s+from|placeholder|\bTBD\b|\bTODO\b|추정|가상)"
    r"[^\]\n]{0,120}?\]|simulated\s+(?:deep\s+)?analysis",
    re.IGNORECASE,
)


def artifact_inspection(root: str, max_files: int = 400) -> str:
    """산출물 실사 — 파일 수·크기 분포·의심 문구. LLM 을 부르지 않는다.

    ⚠️ 이것은 게이트가 아니다(판정하지 않는다). **사람에게 보여줄 숫자**다.
       게이트는 `scripts/gates/analysis_substance.py` 가 한다.
    """
    rows: list[tuple[str, int]] = []
    suspects: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in (".git", "raw", "_private", "_personal")]
        for fn in filenames:
            if not fn.endswith((".md", ".txt", ".json", ".yaml", ".yml")):
                continue
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, root)
            try:
                size = os.path.getsize(p)
            except OSError:
                continue
            rows.append((rel, size))
            if len(rows) > max_files:
                break
            if fn.endswith(".md"):
                try:
                    with open(p, encoding="utf-8", errors="replace") as f:
                        hit = SUSPECT_RE.search(f.read())
                    if hit:
                        suspects.append(f"{rel}: {hit.group(0)[:70]}")
                except OSError:
                    pass
    if not rows:
        return ""
    sizes = sorted(s for _r, s in rows)
    tiny = [r for r, s in rows if s < 2048 and r.endswith(".md")]
    out = [f"• 산출물 실사: 파일 {len(rows)}개 · 크기 중앙값 {sizes[len(sizes)//2]:,}B "
           f"(최소 {sizes[0]:,}B · 최대 {sizes[-1]:,}B)"]
    if tiny:
        out.append(f"  ⚠ 2KB 미만 .md {len(tiny)}개: " + ", ".join(sorted(tiny)[:8])
                   + ("…" if len(tiny) > 8 else ""))
    if suspects:
        out.append(f"  ‼️ **의심 문구 {len(suspects)}건** — 승인 전에 직접 열어보라:")
        out += [f"    - {s}" for s in suspects[:6]]
        if len(suspects) > 6:
            out.append(f"    - (외 {len(suspects) - 6}건)")
    return "\n".join(out)


def resolve_approval_target(explicit_id: str | None, gates: list[dict]) -> tuple[str | None, str]:
    """승인 메시지 → unblock 대상 task. (target|None, 사유).
    - 명시 id: 그 id 가 현재 대기 Sam-게이트면 채택.
    - 바레('승인'만): 대기 게이트가 정확히 1개면 그것. 0개=대상없음. 2+개=모호(특정 요구)."""
    ids = {g["task_id"] for g in gates}
    if explicit_id:
        return (explicit_id, "명시 id") if explicit_id in ids else (None, f"명시 id {explicit_id} 는 현재 대기 게이트 아님")
    if len(gates) == 1:
        return gates[0]["task_id"], "단일 대기 게이트"
    if not gates:
        return None, "대기 게이트 없음"
    return None, f"대기 게이트 {len(gates)}개 — 모호(‘승인 <task_id>’ 로 특정 필요)"


def seed_approval_baseline(state: dict) -> None:
    """최초 기동 시(approval_seen 비어있음) 현재 #approvals 이력 ts 를 모두 seen 처리.
    → '지금부터' 도착하는 승인만 반영(과거 승인 메시지를 새 게이트에 소급 적용 방지)."""
    if not (APPROVAL_ENABLED and SLACK_BOT_TOKEN) or state["approval_seen"]:
        return
    hist = slack_api("conversations.history", {"channel": APPROVALS_CHANNEL, "limit": 100})
    if hist and hist.get("ok"):
        for msg in hist.get("messages", []):
            if msg.get("ts"):
                state["approval_seen"].add(msg["ts"])
        log(f"승인 baseline 설정: 기존 {len(state['approval_seen'])}개 메시지 seen 처리(지금부터 감시)")


def approval_poll(state: dict, dry: bool) -> None:
    """Sam 승인 게이트 자동화. #4 활성 게이트 요청 게시 + #3 승인 감지→unblock."""
    if not (APPROVAL_ENABLED and SLACK_BOT_TOKEN):
        return
    pipelines = load_all_pipelines()
    gates = [g for g in pending_sam_gates(pipelines)
             if all_upstream_done(g["upstream"], g.get("board"))]

    # ── #4: 활성(상위 done) 대기 Sam-게이트를 #approvals 에 1회 게시(내용 포함) ──
    posted = state["approval_posted"]
    pl_by_mission = {pl.get("mission"): pl for pl in pipelines}
    for g in gates:
        if g["task_id"] in posted:
            continue
        summary = gate_summary(g, pl_by_mission.get(g["mission"]) or {})
        board_note = f" · board `{g.get('board') or 'default'}`"
        text = (f":large_yellow_circle: *[승인 요청]* {g['mission']} · {g['name']}  "
                f"(`{g['task_id']}`{board_note})\n"
                f"{summary}\n"
                f"— 승인: `승인` (또는 `승인 {g['task_id']}`) · 반려/보완은 여기서 논의(게이트 대기 유지). 권한: Sam.")
        if dry:
            log(f"[dry] 승인요청 게시: {g['task_id']} {g['mission']}·{g['name']}")
            posted.add(g["task_id"])
            continue
        r = slack_api("chat.postMessage", {"channel": APPROVALS_CHANNEL, "text": text}, post=True)
        if r and r.get("ok"):
            posted.add(g["task_id"])
            log(f"승인요청 게시: {g['task_id']} {g['mission']}·{g['name']} → #approvals")
        else:
            log(f"WARN 승인요청 게시 실패: {g['task_id']} ({(r or {}).get('error')})")

    # ── #3: #approvals 최근 메시지에서 Sam 승인 감지 → 해당 게이트 unblock ──
    hist = slack_api("conversations.history", {"channel": APPROVALS_CHANNEL, "limit": HISTORY_LIMIT})
    if not hist or not hist.get("ok"):
        return
    seen = state["approval_seen"]
    # 오래된→최신 순으로 처리(여러 승인 누적 대비)
    for msg in reversed(hist.get("messages", [])):
        ts = msg.get("ts")
        if not ts or ts in seen:
            continue
        if msg.get("user") not in SLACK_ALLOWED_USERS:   # 보안: Sam 만
            continue
        ok, explicit = parse_approval(msg.get("text", ""))
        if not ok:
            continue
        # 현재 대기 게이트를 재조회(같은 폴에서 앞선 승인이 이미 unblock 했을 수 있음).
        cur = [g for g in pending_sam_gates(load_all_pipelines())
               if all_upstream_done(g["upstream"], g.get("board"))]
        target, why = resolve_approval_target(explicit, cur)
        if not target:
            # 모호(2+개)만 재시도 여지 남김(Sam 이 곧 id 특정) — seen 미기록.
            # 그 외(대상 없음·명시 id 불일치)는 재시도 무의미 → 소비.
            if "모호" not in why and not dry:
                seen.add(ts)
            log(f"승인 메시지(ts={ts}) 보류: {why}")
            continue
        if dry:
            log(f"[dry] Sam 승인(ts={ts}) → unblock {target} ({why})")
            seen.add(ts)
            continue
        # ⚠️ unblock 은 **그 게이트가 사는 보드**에서 해야 한다. 기본 보드에서 부르면
        #    "그런 task 없다" 로 조용히 실패하고, Sam 은 승인했는데 아무 일도 안 일어난다.
        tgt_board = next((g.get("board") for g in cur if g["task_id"] == target), None)
        with board_scope(tgt_board):
            run(["unblock", target, "--reason", f"Sam Slack 승인(ts={ts}, {why})"])
        log(f"Sam 승인 감지(ts={ts}) → unblock {target} [board={tgt_board or 'default'}] ({why})")
        notify(f"✅ Sam 승인 반영 — {target} unblock ({why}).", dry)
        seen.add(ts)


def main() -> int:
    ap = argparse.ArgumentParser(description="반려 게이트 자동화 (Solomon 게이트키퍼)")
    ap.add_argument("--once", action="store_true", help="1회 폴 후 종료")
    ap.add_argument("--dry-run", action="store_true", help="실제 변경 없이 판단만 로그")
    ap.add_argument("--interval", type=float, default=10.0, help="폴 간격(초, 기본 10)")
    args = ap.parse_args()

    log(f"start (once={args.once} dry_run={args.dry_run} interval={args.interval}s state={STATE_PATH} "
        f"approvals={'on' if (APPROVAL_ENABLED and SLACK_BOT_TOKEN) else 'off'})")
    state = load_state()
    if not args.dry_run:
        seed_approval_baseline(state)   # 과거 승인 소급 방지(지금부터 감시)

    def tick() -> None:
        poll_once(state["processed"], args.dry_run)      # 검증자 게이트
        approval_poll(state, args.dry_run)               # Sam 승인 게이트
        if not args.dry_run:
            save_state(state)

    if args.once:
        tick()
        return 0
    while True:
        try:
            tick()
        except Exception as e:  # noqa: BLE001 — 루프는 죽지 않는다
            log(f"ERROR poll: {e}")
        time.sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())
