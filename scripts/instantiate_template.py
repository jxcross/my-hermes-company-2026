#!/usr/bin/env python3
"""
템플릿 → Kanban 그래프 번역기
==============================
선언적 미션 템플릿(templates/<name>.yaml)을 읽어 Hermes Kanban task 그래프로
인스턴스화한다. 하드코딩 build_pipeline.sh 를 대체한다. 설계: docs/11 §3.B·§3.F.

기능
  - 인스턴스화: stage→`hermes kanban create`, upstream→`link`, Sam게이트/검증자 downstream→block.
  - `--dry-run`         : 카드 생성 없이 계획만 출력(비파괴).
  - `--render mermaid`  : DAG 를 mermaid 로 출력(Scoping 협상 미리보기). `--render ascii` 도 지원.
  - reports/<MID>/pipeline.json 기록 → gate_keeper 가 stage별 객관 게이트 설정을 읽는다.

사용
  scripts/instantiate_template.py trend-report M-2026-003 --topic "온디바이스 LLM 추론 최적화 동향"
  scripts/instantiate_template.py trend-report M-2026-003 --dry-run --render mermaid   # 협상용 미리보기
"""
from __future__ import annotations
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML 필요 (pip install pyyaml). 컨테이너 내부에서 실행하라.", file=sys.stderr)
    sys.exit(2)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # scripts/ 의 부모
CONTAINER_REPO = "/work/company"   # 컨테이너 내 repo 마운트 경로(kanban workspace 기준)

# delegation 배치 1회당 최대 subagent 수. Hermes `delegate_task` 는 한 배치가
# `delegation.max_concurrent_children`(기본 3)을 넘으면 큐잉하지 않고
# "Too many tasks: N provided, but max_concurrent_children is M" tool_error 로 **거절**한다.
# 모델의 자체 분할 추측에 맡기지 않도록 템플릿이 명시(`parallel.batch_size`)하고,
# 미선언 시 이 기본값을 주입 문구에 박아 넣는다.
DEFAULT_BATCH_SIZE = 3


def log(m: str) -> None:
    print(m, flush=True)


# ── 보드 스코프 ─────────────────────────────────────────────────────────
# 미션마다 Kanban 보드를 새로 만든다(Sam 지시 2026-08-05 — 여러 미션이 한 보드에
# 섞여 복잡했다). Hermes 게이트웨이 디스패처는 **이미 다중 보드**라(매 틱 보드를
# 열거하고 새 보드를 재시작 없이 집는다) 런타임 쪽 변경은 필요 없다.
#
# ⚠️ `--board` 는 **전역 플래그다 — 서브커맨드 앞에 와야 한다.**
#      hermes kanban --board <slug> create …   ✓
#      hermes kanban create … --board <slug>   ✗ (인자 파싱 실패)
#    그래서 주입 지점은 `hermes_prefix()` 한 곳이다.
# ⚠️ `kan()` 의 `args` 에 넣으면 안 된다 — 테스트가 `args[0]`·`args[1]` 위치로
#    서브커맨드를 어설션한다(test_instantiate_template.py `_capture_instantiate`).
BOARD: str | None = None

# Hermes 의 슬러그 규칙(`kanban_db.py` `_normalize_board_slug`). 소문자로 정규화된다.
BOARD_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9\-_]{0,63}$")


# ── Hermes CLI ──────────────────────────────────────────────────────────
def hermes_prefix() -> list[str]:
    base = ["hermes", "kanban"] if shutil.which("hermes") \
        else ["docker", "exec", "hermes-solomon", "hermes", "kanban"]
    if BOARD:
        base += ["--board", BOARD]      # ★ 반드시 서브커맨드 **앞**
    return base


def ensure_board(slug: str, mission: str, dry: bool = False) -> None:
    """보드가 없으면 만든다. 있으면 그대로 쓴다(재실행 안전).

    ⚠️ `--switch` 를 쓰지 않는다 — 그것은 `<root>/kanban/current` 를 바꿔 **이후 모든
       CLI 호출의 기본 보드**가 된다. 사람이 무심코 친 `hermes kanban list` 도,
       게이트키퍼의 폴백 경로도 따라 움직인다. `default` 를 영구 기본값으로 두고
       보드 지정은 **항상 명시적으로** 한다 — 그래야 버그가 나도 "default 에서 돌았다"
       라는 **보이는 실패**가 되지 사라지지 않는다.
    """
    # 조회는 보드 스코프 밖이다(보드 목록 자체는 특정 보드의 것이 아니다).
    prefix = ["hermes", "kanban"] if shutil.which("hermes") \
        else ["docker", "exec", "hermes-solomon", "hermes", "kanban"]
    proc = subprocess.run(prefix + ["boards", "list", "--json"],
                          capture_output=True, text=True)
    existing = set()
    if proc.returncode == 0:
        try:
            existing = {b.get("slug") for b in json.loads(proc.stdout or "[]")}
        except json.JSONDecodeError:
            pass
    if slug in existing:
        log(f"  보드 {slug} 이미 있음 — 재사용")
        return
    if dry:
        log(f"  (dry-run) boards create {slug}")
        return
    proc = subprocess.run(
        prefix + ["boards", "create", slug, "--name", mission, "--icon", "🧭",
                  "--description", f"미션 {mission} 전용 보드"],
        capture_output=True, text=True)
    if proc.returncode != 0:
        raise InstantiateError(
            f"boards create {slug} 실패(rc={proc.returncode}): {proc.stderr.strip()[:200]}")
    log(f"  보드 {slug} 생성")


def kan(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    proc = subprocess.run(hermes_prefix() + args, capture_output=True, text=True)
    if check and proc.returncode != 0:
        log(f"WARN kanban {' '.join(args)} → {proc.returncode}: {proc.stderr.strip()[:200]}")
    return proc


class InstantiateError(RuntimeError):
    """인스턴스화 중단 — 반쪽짜리 그래프를 남기지 않기 위해 호출부가 롤백한다."""


def kan_or_abort(args: list[str], what: str) -> subprocess.CompletedProcess:
    """실패하면 1회 재시도하고, 그래도 실패하면 **중단**한다.

    ⚠️ 예전에는 `kan()` 이 WARN 만 찍고 넘어갔다. 실측(2026-08-05 · M-2026-005 첫 시도):
       `block ... --kind needs_input` 이 `rc=-7` 로 죽었는데 번역기가 그대로 진행해
       **검증 게이트가 빠진 파이프라인**이 만들어졌다. 게이트가 하나 빠진 그래프는
       없는 것보다 나쁘다 — 있는 줄 알고 돌리기 때문이다."""
    proc = kan(args, check=False)
    if proc.returncode != 0:
        log(f"  ↻ 재시도: {what} (rc={proc.returncode})")
        proc = kan(args, check=False)
    if proc.returncode != 0:
        raise InstantiateError(f"{what} 실패(rc={proc.returncode}): {proc.stderr.strip()[:200]}")
    return proc


def create_task(title: str, assignee: str, workspace: str, body: str,
                parents: list[str] | None = None) -> str:
    args = ["create", title, "--assignee", assignee, "--workspace", workspace, "--body", body]
    for p in parents or []:
        args += ["--parent", p]
    args += ["--json"]
    proc = kan(args, check=False)
    try:
        d = json.loads(proc.stdout)
        tid = d.get("id") or d.get("task", {}).get("id")
    except json.JSONDecodeError:
        tid = None
    if not tid:
        raise InstantiateError(f"create 실패: {title} :: {proc.stderr.strip()[:200]}")
    return tid


# ── 템플릿 로드 · 불변식 ──────────────────────────────────────────────────
def load_template(name_or_path: str) -> dict:
    path = name_or_path
    if not os.path.isfile(path):
        path = os.path.join(REPO_ROOT, "templates", f"{name_or_path}.yaml")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def stage_by_id(stages: list[dict], sid: int) -> dict | None:
    return next((s for s in stages if s.get("id") == sid), None)


# ── profile 등록 확인 ────────────────────────────────────────────────────
def registered_profiles() -> set[str]:
    """현재 보유한 profile 집합. profiles-src/<name>/ (git 기준 진실) + default(Solomon).
    고정 목록을 박지 않는다 — profile 수는 미션이 요구하면 늘어난다(docs/12 §2⑤)."""
    src = os.path.join(REPO_ROOT, "profiles-src")
    names = {"default"}
    if os.path.isdir(src):
        names |= {d for d in os.listdir(src) if os.path.isdir(os.path.join(src, d))}
    return names


def missing_profiles(tpl: dict) -> list[str]:
    """템플릿이 쓰는 profile 중 아직 없는 것. 순서 보존·중복 제거."""
    have = registered_profiles()
    out: list[str] = []
    for s in tpl.get("stages", []):
        p = s.get("profile")
        if p and p not in have and p not in out:
            out.append(p)
    return out


def check_invariants(tpl: dict) -> list[str]:
    """선언된 Layer0 불변식을 구조적으로 검사. 위반 목록 반환(비면 통과)."""
    stages = tpl.get("stages", [])
    inv = set(tpl.get("invariants", []))
    errs: list[str] = []
    if not stages:
        return ["stages 비어있음"]
    first, last = stages[0], stages[-1]
    if "scoping_gate" in inv and not first.get("sam_gate"):
        errs.append("scoping_gate: 첫 단계에 sam_gate 없음")
    if "deliver_gate" in inv and not last.get("sam_gate"):
        errs.append("deliver_gate: 마지막 단계에 sam_gate 없음")
    verifiers = [s for s in stages if s.get("verifier")]
    if "revision_loop" in inv and not verifiers:
        errs.append("revision_loop: 검증자 단계 없음")
    # 작성자≠검증자: 각 검증자의 직전 producer(첫 upstream) profile 이 검증자 profile 과 달라야
    for v in verifiers:
        ups = v.get("upstream") or []
        prod = stage_by_id(stages, ups[0]) if ups else None
        if prod and prod.get("profile") == v.get("profile"):
            errs.append(f"작성자≠검증자 위반: stage {v['id']}({v['profile']}) == producer {prod['id']}")
    # 게이트 겹침: 한 stage 에 sam_gate 와 검증자 downstream 이 동시에 걸리면 안 된다.
    # 번역기는 카드당 block 을 하나만 걸고 sam_gate 가 우선하므로(instantiate 2절), 검증 게이트가
    # 조용히 사라져 검증 FAIL 이어도 Sam 승인만으로 진행된다(불변식 우회). 승인 지점을 인접
    # stage 로 옮겨 분리하라. [발견: academic-paper 변환, docs/13 §5]
    for s in stages:
        if s.get("sam_gate") and is_gated_downstream(s, stages):
            errs.append(f"게이트 겹침: stage {s['id']}({s['name']})에 sam_gate 와 검증 게이트가 동시 — "
                        f"승인 지점을 인접 stage 로 분리하라")
    return errs


def resolve(tpl: dict, mid: str) -> dict:
    """<MID> 치환 등 미션별 해석."""
    def sub(x):
        return x.replace("<MID>", mid) if isinstance(x, str) else x
    stages = []
    for s in tpl.get("stages", []):
        s2 = dict(s)
        # ⚠️ **`body` 를 빠뜨리고 있었다 (2026-08-06 발견 · 20/20 템플릿 · 47개 stage).**
        #    카드 본문이 워커에게 `reports/<MID>/SCOPE.md` 를 **문자 그대로** 갔다.
        #    강한 모델은 문맥에서 미션 id 를 해석해 버려서 codex 시절 내내 드러나지 않았다
        #    (`trend-report` 는 이 상태로 두 번 완주했다 — proven 딱지가 결함을 덮었다).
        #    `<MID>` 를 쓰는 필드는 셋뿐이다: gate.draft · approval_artifact · **body**.
        if s.get("body"):
            s2["body"] = sub(s["body"])
        g = s.get("gate")
        if g:
            g2 = dict(g)
            g2["draft"] = sub(g.get("draft"))
            s2["gate"] = g2
        if s.get("approval_artifact"):
            s2["approval_artifact"] = sub(s["approval_artifact"])
        stages.append(s2)
    return {**tpl, "stages": stages}


def is_gated_downstream(stage: dict, stages: list[dict]) -> bool:
    """upstream 중 검증자가 있으면 downstream 게이트(초기 blocked)."""
    for uid in stage.get("upstream") or []:
        up = stage_by_id(stages, uid)
        if up and up.get("verifier"):
            return True
    return False


# ── 병렬 팬아웃 본문 주입 ──────────────────────────────────────────────────
def parallel_spec(stage: dict) -> dict | None:
    """스테이지의 병렬 선언을 dict 로 정규화. 구식 `parallel: true`(+workers) 호환."""
    p = stage.get("parallel")
    if not p:
        return None
    if p is True:  # 구식 선언 호환
        p = {"mode": "workers", "workers": stage.get("workers") or []}
    if not isinstance(p, dict):
        return None
    p.setdefault("mode", "workers" if p.get("workers") else "per_item")
    p["batch_size"] = normalize_batch_size(p.get("batch_size"))
    return p


def normalize_batch_size(v) -> int:
    """batch_size 를 정수로 정규화. 미선언·불량값이면 DEFAULT_BATCH_SIZE(하한 1)."""
    try:
        n = int(v)
    except (TypeError, ValueError):
        return DEFAULT_BATCH_SIZE
    return max(1, n)


def batch_plan(count: int, batch_size: int) -> list[int]:
    """count 개를 batch_size 씩 나눈 라운드별 크기(예: 5,3 → [3, 2])."""
    if count <= 0:
        return []
    return [min(batch_size, count - i) for i in range(0, count, batch_size)]


def fanout_label(stage: dict) -> str:
    """렌더용 팬아웃 요약(예: '⇉5워커/배치3' · '⇉동적/배치3')."""
    p = parallel_spec(stage)
    if not p:
        return ""
    bs = p["batch_size"]
    if p["mode"] == "workers":
        n = len(p.get("workers") or [])
        rounds = len(batch_plan(n, bs))
        return f"⇉{n}워커/배치{bs}" + (f"×{rounds}R" if rounds > 1 else "")
    return f"⇉동적/배치{bs}"


def batch_lines(p: dict) -> list[str]:
    """배치 크기 지시문. Hermes 는 배치 초과를 큐잉하지 않고 거절하므로
    '몇 개씩 몇 라운드로 나눌지'를 모델 추측에 맡기지 않고 본문에 못박는다."""
    bs = p["batch_size"]
    out = [f"· **배치 크기: 1회 위임당 최대 {bs}개.** 대상이 {bs}개를 넘으면 {bs}개씩 나눠 "
           f"여러 라운드로 위임하라(한 라운드의 subagent 가 모두 반환한 뒤 다음 라운드). "
           f"한 배치에 {bs}개를 초과해 넣으면 Hermes 가 "
           f"`Too many tasks: N provided, but max_concurrent_children is {bs}` tool_error 로 "
           f"거절한다 — 대기열에 넣어주지 않는다."]
    if p["mode"] == "workers":
        n = len(p.get("workers") or [])
        plan = batch_plan(n, bs)
        if len(plan) > 1:
            out.append(f"  → 이 단계: 워커 {n}개 = {' + '.join(str(x) for x in plan)}, "
                       f"총 {len(plan)}라운드.")
        elif n:
            out.append(f"  → 이 단계: 워커 {n}개 ≤ {bs} 이므로 한 배치로 위임.")
    else:
        out.append(f"  → 이 단계: 항목 수가 동적이다. 항목 수를 먼저 세고 {bs}개씩 "
                   f"올림 나눗셈으로 라운드를 계산해 순서대로 위임하라.")
    return out


def fanout_body(stage: dict, base_body: str) -> str:
    """병렬 스테이지의 task 본문 = 기본 목표 + subagent 팬아웃 프로토콜.
    번역기는 subagent 를 실행하지 않는다 — 실행 profile 이 이 지시를 읽어 delegation
    도구의 배치(parallel) 위임으로 worker 를 동시 디스패치한다(단계 내 병렬=subagent)."""
    p = parallel_spec(stage)
    if not p:
        return base_body
    merge_to = p.get("merge_to", "")
    bs = p["batch_size"]
    lines = [
        base_body,
        "",
        "── 병렬 팬아웃 (delegation 배치 위임) ──",
        "이 단계는 순차 처리하지 마라. 아래 작업들을 delegation 도구의 배치(parallel) "
        "기능으로 위임해 subagent 들이 동시에 실행되게 하라(각자 격리 세션).",
        "⛔ **Kanban task 를 새로 만들지 마라.** `kanban create`·`kanban decompose` 로 "
        "하위 카드를 만드는 것은 위임이 **아니다** — 파이프라인 카드는 이미 다 생성돼 있고, "
        "새 카드는 존재하지 않는 profile 에 배정되어 **아무도 실행하지 않는다.** "
        "쓸 도구는 오직 **delegation(subagent)** 하나다.",
        "⛔ **subagent 에게 넘겼다는 것은 네 일이 끝났다는 뜻이 아니다.** 위임 → 전원 반환 → "
        "네가 병합, 이 세 가지를 **네 세션 안에서** 끝내야 이 task 가 완료다. "
        "위임만 하고 완료를 선언하면 다음 단계가 **빈 입력으로 돌아간다.**",
    ]
    if p["mode"] == "workers":
        workers = p.get("workers") or []
        shard = p.get("shard", "raw/<worker>.yaml")
        lines.append(f"· 워커({len(workers)}개): {', '.join(workers)} — 워커마다 subagent 1개.")
        lines.append(f"· 각 워커는 자기 몫만 수집하고 source_type=<worker> 로 태깅해 "
                     f"'{shard}'(<worker> 치환)에 기록. 공유 파일 동시쓰기 금지(경합 방지).")
    else:  # per_item
        over = p.get("over", "각 항목")
        shard = p.get("shard", "shards/<id>.md")
        lines.append(f"· 분할 기준: {over} — 항목마다 subagent 1개.")
        lines.append(f"· 각 subagent 는 자기 항목만 처리해 '{shard}'(항목 식별자 치환)에 기록. "
                     f"공유 파일 동시쓰기 금지(경합 방지).")
    lines.extend(batch_lines(p))
    if merge_to:
        lines.append(f"· 모든 subagent 반환 후 **오케스트레이터(너)가** 산출 shard 들을 "
                     f"'{merge_to}'로 병합·dedup(필드 누락·형식 불량 항목 폐기). 이 병합 파일이 "
                     f"다음 단계·게이트의 입력이다.")
        lines.append(f"· ✅ **완료 조건: '{merge_to}' 가 디스크에 실재하고 내용이 비어 있지 않을 것.** "
                     f"그 파일을 만들지 못했다면 이 task 는 완료가 아니다 — 완료로 처리하지 말고 "
                     f"무엇이 막혔는지 남겨라. 완료 보고는 산출물을 대신하지 못한다.")
    return "\n".join(lines)


# ── 렌더(협상 미리보기) ────────────────────────────────────────────────────
def render_mermaid(tpl: dict, mid: str) -> str:
    stages = tpl["stages"]
    out = ["```mermaid", "graph TD"]
    for s in stages:
        # 표식은 **누적**한다 — 한 stage 가 Sam 게이트이면서 팬아웃일 수 있다
        # (policy-brief stage 9: 집필 개시 승인 + 포맷 4워커). elif 로 묶으면 협상 중
        # Sam 이 보는 DAG 에서 병렬이 사라진다.
        marks = []
        if s.get("sam_gate"):
            marks.append("🚦Sam")
        if s.get("verifier"):
            marks.append("🔍검증")
        if s.get("parallel"):
            marks.append(fanout_label(s))
        mark = (" " + " ".join(m for m in marks if m)) if marks else ""
        out.append(f'  s{s["id"]}["{s["id"]} {s["name"]}{mark}<br/>{s.get("profile","")}"]')
    for s in stages:
        for uid in s.get("upstream") or []:
            up = stage_by_id(stages, uid)
            edge = "-. 게이트 .->" if (up and up.get("verifier")) else "-->"
            out.append(f"  s{uid} {edge} s{s['id']}")
    out.append("```")
    return "\n".join(out)


def render_ascii(tpl: dict, mid: str) -> str:
    lines = [f"# {mid} — {tpl.get('display_name', tpl['name'])}"]
    for s in tpl["stages"]:
        flags = ["🚦Sam" if s.get("sam_gate") else ("🔍검증" if s.get("verifier") else "")]
        if s.get("parallel"):
            flags.append(fanout_label(s))   # 누적 — Sam 게이트 + 팬아웃 동시 가능
        flag = " ".join(f for f in flags if f)
        ups = ",".join(str(u) for u in (s.get("upstream") or [])) or "-"
        gate = ""
        if s.get("gate"):
            gate = f"  [gate: {'+'.join(s['gate'].get('objective', []))} +LLM]"
        lines.append(f"  {s['id']:>2} {s['name']:<18} @{s.get('profile',''):<12} ←{ups:<6} {flag}{gate}")
    return "\n".join(lines)


# ── 인스턴스화 ─────────────────────────────────────────────────────────────
def instantiate(tpl: dict, mid: str, topic: str, dry: bool,
                ids: dict[int, str] | None = None) -> dict:
    """`ids` 를 넘기면 실패 시 호출부가 **이미 만든 카드를 롤백**할 수 있다."""
    stages = tpl["stages"]
    ws = f"dir:{CONTAINER_REPO}/reports/{mid}"
    ids = {} if ids is None else ids

    log(f"▶ 미션 {mid} 인스턴스화: {topic}  (template={tpl['name']})")

    # ── stage 마다 생성→(게이트)→링크를 **한 번에** 끝낸다 ────────────────────
    # ⚠️ **디스패처와의 경합**(실측 2026-08-05 · M-2026-005 첫 시도에서 실제로 터졌다):
    #    예전에는 11장을 모두 만든 뒤 → 전부 block → 전부 link 했다. 그 사이 카드들은
    #    **부모 없는 `ready`** 라 게이트웨이 디스패처가 집어간다. 실제로 상류 산출물이
    #    하나도 없는 상태에서 워커 6개(2·3·5·6·9·10)가 동시에 돌기 시작했다.
    #
    # Hermes CLI 의 제약을 실측으로 확인하고 그에 맞춰 배치했다:
    #    · `create --parent <미완료 부모>` → **`todo` 로 태어난다** = 디스패처가 못 집는다(창 0)
    #    · `block` 은 **`ready` 에서만** 걸린다 — `todo` 면 "cannot block" 으로 거부된다
    #    · `--initial-status blocked` 는 **실제로 blocked 를 만들지 않는다**(ready 로 태어난다)
    #    · 한 번 걸린 needs_input block 은 **부모가 완료돼도 생존한다**
    #  → 게이트 있는 stage: 부모 없이 만들고(ready) **즉시** block 한 뒤 link (창 = CLI 1회)
    #    게이트 없는 stage: 부모와 함께 만든다(todo) = 창 0
    for s in stages:
        title = f"{mid} · {s['id']} {s['name']}"
        body = fanout_body(s, s.get("body", "")) if s.get("parallel") else s.get("body", "")
        ups = [ids[u] for u in (s.get("upstream") or [])]
        if s.get("sam_gate"):
            reason = f"Sam 승인 대기: {s['name']}"
        elif is_gated_downstream(s, stages):
            reason = f"검증 게이트 대기: {s['name']} (게이트키퍼가 PASS시 unblock)"
        else:
            reason = None

        if dry:
            fo = f"  {fanout_label(s)}" if s.get("parallel") else ""
            tid = f"<t{s['id']}>"
            ids[s["id"]] = tid
            if reason:
                log(f"  [dry] create '{title}' @{s['profile']}{fo}  (부모 없이 → 즉시 block)")
                log(f"  [dry] block {tid} --kind needs_input ({reason})")
                for u in ups:
                    log(f"  [dry] link {u} → {tid}")
            else:
                pl = f" --parent {' --parent '.join(ups)}" if ups else ""
                log(f"  [dry] create '{title}' @{s['profile']}{pl}{fo}")
            continue

        if reason:
            tid = create_task(title, s["profile"], ws, body)      # ready 로 태어난다
            ids[s["id"]] = tid
            kan_or_abort(["block", tid, reason, "--kind", "needs_input"],
                         f"block {tid}({s['name']})")             # ★즉시★ — 창을 최소화
            for u in ups:
                kan_or_abort(["link", u, tid], f"link {u}→{tid}")
            log(f"  create {tid}  '{title}' @{s['profile']}  🚦{reason}")
        else:
            tid = create_task(title, s["profile"], ws, body, parents=ups)  # 부모와 함께(todo)
            ids[s["id"]] = tid
            log(f"  create {tid}  '{title}' @{s['profile']}"
                + (f"  ←{','.join(ups)}" if ups else "  (상류 없음 — 즉시 실행 대상)"))

    # pipeline.json (게이트키퍼가 읽는 게이트 설정)
    pipeline = build_pipeline_json(tpl, mid, topic, ids)
    if dry:
        log("  [dry] pipeline.json (미기록):")
        log(json.dumps(pipeline, ensure_ascii=False, indent=2))
    else:
        write_pipeline_json(mid, pipeline)
    return pipeline


def build_pipeline_json(tpl: dict, mid: str, topic: str, ids: dict[int, str]) -> dict:
    stages = tpl["stages"]
    out_stages = []
    for s in stages:
        entry = {
            "id": s["id"], "name": s["name"], "task_id": ids.get(s["id"]),
            "profile": s.get("profile"), "verifier": bool(s.get("verifier")),
            "sam_gate": bool(s.get("sam_gate")),
            "upstream_task_ids": [ids.get(u) for u in (s.get("upstream") or [])],
        }
        if s.get("gate"):
            entry["gate"] = s["gate"]
        if s.get("approval_artifact"):
            # 중간 Sam 게이트가 '무엇을 보고 승인할지' — gate_keeper.gate_summary 가 읽는다.
            entry["approval_artifact"] = s["approval_artifact"]
        ps = parallel_spec(s)
        if ps:
            entry["parallel"] = {
                "mode": ps["mode"],
                **({"workers": ps.get("workers")} if ps["mode"] == "workers" else {"over": ps.get("over")}),
                "batch_size": ps["batch_size"],
                "merge_to": ps.get("merge_to"),
            }
        out_stages.append(entry)
    return {
        "mission": mid, "template": tpl["name"], "topic": topic,
        # ⚠️ 보드 슬러그를 **여기에** 남긴다. 보드 메타데이터는 `hermes-home/kanban/boards/`
        #    아래라 gitignore 되고, task JSON 에는 board 필드가 아예 없다. 커밋되는
        #    pipeline.json 이 "이 미션이 어느 보드에서 돌았는가" 의 유일한 영속 기록이다.
        #    gate_keeper 도 여기서 읽는다.
        "board": BOARD or "default",
        "policy_file": f"reports/{mid}/SCOPE.md",
        "sources_file": f"reports/{mid}/raw/sources.yaml",
        "policy": tpl.get("policy", {}),
        "stages": out_stages,
    }


def write_pipeline_json(mid: str, pipeline: dict) -> None:
    d = os.path.join(REPO_ROOT, "reports", mid)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, "pipeline.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(pipeline, f, ensure_ascii=False, indent=2)
    log(f"  pipeline.json → {path}")


def main() -> int:
    ap = argparse.ArgumentParser(description="템플릿 → Kanban 그래프 번역기")
    ap.add_argument("template", help="템플릿 이름(templates/<name>.yaml) 또는 경로")
    ap.add_argument("mission", help="미션 id (예: M-2026-003)")
    ap.add_argument("--topic", default="", help="미션 주제")
    ap.add_argument("--dry-run", action="store_true", help="카드 생성 없이 계획만 출력")
    ap.add_argument("--render", choices=["mermaid", "ascii", "none"], default="none",
                    help="DAG 미리보기 출력(협상용)")
    ap.add_argument("--board", default=None,
                    help="Kanban 보드 슬러그(기본: 미션 id 소문자). 'default' 를 주면 "
                         "기존 공용 보드를 쓴다.")
    args = ap.parse_args()

    # ── 보드 결정 ──────────────────────────────────────────────────────
    # 슬러그를 **먼저** 검증한다. Hermes 쪽에서 거절당하면 이미 카드를 몇 장 만든
    # 뒤가 되고, 그러면 반쪽짜리 그래프를 롤백해야 한다.
    global BOARD
    slug = (args.board or args.mission).strip().lower()
    if not BOARD_SLUG_RE.match(slug):
        log(f"✗ 보드 슬러그 형식 오류: {slug!r} "
            "— ^[a-z0-9][a-z0-9\\-_]{0,63}$ 이어야 한다")
        return 2
    BOARD = None if slug == "default" else slug

    tpl = resolve(load_template(args.template), args.mission)

    errs = check_invariants(tpl)
    if errs:
        log("✗ 불변식 위반 — 인스턴스화 중단:")
        for e in errs:
            log(f"  - {e}")
        return 1

    # 미등록 profile: 협상·미리보기 단계에선 경고만(docs/12 §2⑤ — 거부가 아니라 "생성할까요?"),
    # 실제 인스턴스화는 중단한다(존재하지 않는 assignee 로 카드가 생성되면 아무도 못 집는다).
    missing = missing_profiles(tpl)
    if missing:
        log(f"⚠ 미등록 profile {len(missing)}종: {', '.join(missing)}")
        log(f"  → 생성 필요: profiles-src/<name>/(SOUL·config) + hermes profile create. "
            f"Sam 승인 사항이다(docs/12 §2⑤).")
        if not args.dry_run:
            log("✗ 인스턴스화 중단 — profile 생성 후 다시 실행하라.")
            return 1

    if args.render != "none":
        r = render_mermaid(tpl, args.mission) if args.render == "mermaid" else render_ascii(tpl, args.mission)
        log(r)
        if args.dry_run:   # 미리보기 전용
            return 0

    log(f"보드: {BOARD or 'default'}"
        + ("  (미션 전용)" if BOARD else "  (공용 — 여러 미션이 섞인다)"))

    created: dict[int, str] = {}
    try:
        # ⚠️ 카드보다 **보드를 먼저** 만든다. 반대로 하면 카드가 default 로 새고,
        #    보드는 별도 DB 라 나중에 옮길 수 없다(이관 명령이 없다).
        if BOARD:
            ensure_board(BOARD, args.mission, args.dry_run)
        instantiate(tpl, args.mission, args.topic or f"{args.mission} 미션", args.dry_run,
                    created)
    except InstantiateError as e:
        # 반쪽짜리 그래프는 없는 것보다 나쁘다 — 게이트가 빠진 채로 돌게 된다.
        log(f"✗ 인스턴스화 실패: {e}")
        made = [t for t in created.values() if t]
        if made:
            log(f"  ↩ 롤백: 이미 만든 카드 {len(made)}장을 archive 한다 — {', '.join(made)}")
            for tid in reversed(made):
                kan(["archive", tid], check=False)
        return 1
    if not args.dry_run:
        log("✔ 인스턴스화 완료. Scoping 승인 후 게이트키퍼가 검증 게이트를 관리한다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
