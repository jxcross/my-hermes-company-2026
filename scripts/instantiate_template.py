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


def log(m: str) -> None:
    print(m, flush=True)


# ── Hermes CLI ──────────────────────────────────────────────────────────
def hermes_prefix() -> list[str]:
    if shutil.which("hermes"):
        return ["hermes", "kanban"]
    return ["docker", "exec", "hermes-solomon", "hermes", "kanban"]


def kan(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    proc = subprocess.run(hermes_prefix() + args, capture_output=True, text=True)
    if check and proc.returncode != 0:
        log(f"WARN kanban {' '.join(args)} → {proc.returncode}: {proc.stderr.strip()[:200]}")
    return proc


def create_task(title: str, assignee: str, workspace: str, body: str) -> str:
    args = ["create", title, "--assignee", assignee, "--workspace", workspace, "--body", body, "--json"]
    proc = kan(args, check=False)
    try:
        d = json.loads(proc.stdout)
        return d.get("id") or d.get("task", {}).get("id")
    except json.JSONDecodeError:
        log(f"ERROR create 실패: {title} :: {proc.stderr.strip()[:200]}")
        return ""


# ── 템플릿 로드 · 불변식 ──────────────────────────────────────────────────
def load_template(name_or_path: str) -> dict:
    path = name_or_path
    if not os.path.isfile(path):
        path = os.path.join(REPO_ROOT, "templates", f"{name_or_path}.yaml")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def stage_by_id(stages: list[dict], sid: int) -> dict | None:
    return next((s for s in stages if s.get("id") == sid), None)


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
    return errs


def resolve(tpl: dict, mid: str) -> dict:
    """<MID> 치환 등 미션별 해석."""
    def sub(x):
        return x.replace("<MID>", mid) if isinstance(x, str) else x
    stages = []
    for s in tpl.get("stages", []):
        s2 = dict(s)
        g = s.get("gate")
        if g:
            g2 = dict(g)
            g2["draft"] = sub(g.get("draft"))
            s2["gate"] = g2
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
    return p


def fanout_label(stage: dict) -> str:
    """렌더용 팬아웃 요약(예: '⇉5워커' · '⇉동적')."""
    p = parallel_spec(stage)
    if not p:
        return ""
    if p["mode"] == "workers":
        return f"⇉{len(p.get('workers') or [])}워커"
    return "⇉동적"


def fanout_body(stage: dict, base_body: str) -> str:
    """병렬 스테이지의 task 본문 = 기본 목표 + subagent 팬아웃 프로토콜.
    번역기는 subagent 를 실행하지 않는다 — 실행 profile 이 이 지시를 읽어 delegation
    도구의 배치(parallel) 위임으로 worker 를 동시 디스패치한다(단계 내 병렬=subagent)."""
    p = parallel_spec(stage)
    if not p:
        return base_body
    merge_to = p.get("merge_to", "")
    lines = [
        base_body,
        "",
        "── 병렬 팬아웃 (delegation 배치 위임) ──",
        "이 단계는 순차 처리하지 마라. 아래 작업들을 delegation 도구의 배치(parallel) "
        "기능으로 **한 번에** 위임해 subagent 들이 동시에 실행되게 하라(각자 격리 세션).",
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
    if merge_to:
        lines.append(f"· 모든 subagent 반환 후 **오케스트레이터(너)가** 산출 shard 들을 "
                     f"'{merge_to}'로 병합·dedup(필드 누락·형식 불량 항목 폐기). 이 병합 파일이 "
                     f"다음 단계·게이트의 입력이다.")
    return "\n".join(lines)


# ── 렌더(협상 미리보기) ────────────────────────────────────────────────────
def render_mermaid(tpl: dict, mid: str) -> str:
    stages = tpl["stages"]
    out = ["```mermaid", "graph TD"]
    for s in stages:
        mark = ""
        if s.get("sam_gate"):
            mark = " 🚦Sam"
        elif s.get("verifier"):
            mark = " 🔍검증"
        elif s.get("parallel"):
            mark = f" {fanout_label(s)}"
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
        flag = "🚦Sam" if s.get("sam_gate") else ("🔍검증" if s.get("verifier") else "")
        if not flag and s.get("parallel"):
            flag = fanout_label(s)
        ups = ",".join(str(u) for u in (s.get("upstream") or [])) or "-"
        gate = ""
        if s.get("gate"):
            gate = f"  [gate: {'+'.join(s['gate'].get('objective', []))} +LLM]"
        lines.append(f"  {s['id']:>2} {s['name']:<18} @{s.get('profile',''):<12} ←{ups:<6} {flag}{gate}")
    return "\n".join(lines)


# ── 인스턴스화 ─────────────────────────────────────────────────────────────
def instantiate(tpl: dict, mid: str, topic: str, dry: bool) -> dict:
    stages = tpl["stages"]
    ws = f"dir:{CONTAINER_REPO}/reports/{mid}"
    ids: dict[int, str] = {}

    log(f"▶ 미션 {mid} 인스턴스화: {topic}  (template={tpl['name']})")
    # 1) 생성(모두 일반 생성 — 게이트는 아래서 block)
    for s in stages:
        title = f"{mid} · {s['id']} {s['name']}"
        body = fanout_body(s, s.get("body", "")) if s.get("parallel") else s.get("body", "")
        if dry:
            fo = f"  {fanout_label(s)}" if s.get("parallel") else ""
            log(f"  [dry] create '{title}' @{s['profile']}{fo}")
            ids[s["id"]] = f"<t{s['id']}>"
        else:
            tid = create_task(title, s["profile"], ws, body)
            ids[s["id"]] = tid
            log(f"  create {tid}  '{title}' @{s['profile']}")

    # 2) 게이트 block — ★링크 전(ready 상태)에★ needs_input 로 건다.
    #    링크 후엔 상위 대기(todo)라 block 이 거부되고, generic --initial-status blocked 는
    #    부모 완료 시 auto-promote 되어 불안정. 링크 전 needs_input 는 부모 완료 후에도
    #    blocked 가 생존한다(실측). 두 종류의 게이트:
    #      - sam_gate           : Sam 이 #approvals 에서 unblock (Scoping·Deliver)
    #      - 검증자 downstream   : 게이트키퍼가 검증 PASS 시 unblock (Synthesis·Wiki)
    for s in stages:
        if s.get("sam_gate"):
            reason = f"Sam 승인 대기: {s['name']}"
        elif is_gated_downstream(s, stages):
            reason = f"검증 게이트 대기: {s['name']} (게이트키퍼가 PASS시 unblock)"
        else:
            continue
        if dry:
            log(f"  [dry] block {ids[s['id']]} --kind needs_input ({reason})")
        else:
            kan(["block", ids[s["id"]], reason, "--kind", "needs_input"])

    # 3) 링크(upstream→stage)
    for s in stages:
        for uid in s.get("upstream") or []:
            if dry:
                log(f"  [dry] link {ids[uid]} → {ids[s['id']]}")
            else:
                kan(["link", ids[uid], ids[s["id"]]])

    # 4) pipeline.json (게이트키퍼가 읽는 게이트 설정)
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
        ps = parallel_spec(s)
        if ps:
            entry["parallel"] = {
                "mode": ps["mode"],
                **({"workers": ps.get("workers")} if ps["mode"] == "workers" else {"over": ps.get("over")}),
                "merge_to": ps.get("merge_to"),
            }
        out_stages.append(entry)
    return {
        "mission": mid, "template": tpl["name"], "topic": topic,
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
    args = ap.parse_args()

    tpl = resolve(load_template(args.template), args.mission)

    errs = check_invariants(tpl)
    if errs:
        log("✗ 불변식 위반 — 인스턴스화 중단:")
        for e in errs:
            log(f"  - {e}")
        return 1

    if args.render != "none":
        r = render_mermaid(tpl, args.mission) if args.render == "mermaid" else render_ascii(tpl, args.mission)
        log(r)
        if args.dry_run:   # 미리보기 전용
            return 0

    instantiate(tpl, args.mission, args.topic or f"{args.mission} 미션", args.dry_run)
    if not args.dry_run:
        log("✔ 인스턴스화 완료. Scoping 승인 후 게이트키퍼가 검증 게이트를 관리한다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
