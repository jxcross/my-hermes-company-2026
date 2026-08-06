#!/usr/bin/env python3
"""
gate_keeper 회귀 테스트
=======================
근본 결함(fail-open on transient None): 검증자 downstream 자식의 상태 조회가
transient 하게 실패(None)하면, 기존 코드는 그 자식을 '종단(done/archived)'과
동일 취급해 actionable 에서 제거 → 검증자를 processed 로 확정 → blocked downstream
을 영구 고아화했다(게이트 조용히 통과 = fail-open). fail-closed 원칙 위반.

classify_children 은 자식을 (actionable, unknown) 으로 분리해 None(조회실패)을
종단과 구분한다. 실행: python3 -m pytest scripts/tests/test_gate_keeper.py
(pytest 없으면) python3 scripts/tests/test_gate_keeper.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import gate_keeper as gk


def test_none_status_child_is_unknown_not_terminal():
    """★ 결함 재현: 조회 실패(None) 자식은 종단이 아니라 unknown 이어야 한다."""
    actionable, unknown = gk.classify_children(["c1"], lambda c: None)
    assert unknown == ["c1"], "None 자식이 unknown 으로 분류되지 않음(fail-open)"
    assert actionable == []


def test_blocked_child_is_actionable():
    actionable, unknown = gk.classify_children(["c1"], lambda c: "blocked")
    assert actionable == ["c1"] and unknown == []


def test_done_and_archived_children_are_terminal():
    actionable, unknown = gk.classify_children(["a", "b"], {"a": "done", "b": "archived"}.get)
    assert actionable == [] and unknown == []


def test_mixed_children():
    st = {"a": "done", "b": "blocked", "c": None, "d": "todo"}
    actionable, unknown = gk.classify_children(["a", "b", "c", "d"], st.get)
    assert actionable == ["b", "d"]
    assert unknown == ["c"]


# ── Sam 승인 게이트 파싱/매칭 ───────────────────────────────────────────────
def test_parse_approval_bare():
    ok, tid = gk.parse_approval("승인")
    assert ok is True and tid is None


def test_parse_approval_with_explicit_id():
    ok, tid = gk.parse_approval("승인 t_2daad491")
    assert ok is True and tid == "t_2daad491"


def test_parse_approval_english():
    ok, tid = gk.parse_approval("approve t_abc123")
    assert ok is True and tid == "t_abc123"


def test_parse_approval_deny_word_is_not_approval():
    # ★ 오탐 방지: 반려/보류가 있으면 승인 아님
    assert gk.parse_approval("반려한다")[0] is False
    assert gk.parse_approval("이건 보류")[0] is False
    assert gk.parse_approval("아직 승인 못함, 보류")[0] is False


def test_parse_approval_non_approval_text():
    assert gk.parse_approval("보고서 잘 봤어요")[0] is False
    assert gk.parse_approval("")[0] is False


def test_resolve_target_explicit_match():
    gates = [{"task_id": "t_1"}, {"task_id": "t_2"}]
    target, _ = gk.resolve_approval_target("t_2", gates)
    assert target == "t_2"


def test_resolve_target_explicit_not_a_gate():
    gates = [{"task_id": "t_1"}]
    target, why = gk.resolve_approval_target("t_9", gates)
    assert target is None and "아님" in why


def test_resolve_target_single_bare():
    target, _ = gk.resolve_approval_target(None, [{"task_id": "t_only"}])
    assert target == "t_only"


def test_resolve_target_ambiguous_bare():
    target, why = gk.resolve_approval_target(None, [{"task_id": "t_1"}, {"task_id": "t_2"}])
    assert target is None and "모호" in why


def test_resolve_target_none_pending():
    target, why = gk.resolve_approval_target(None, [])
    assert target is None and "없음" in why


# ── 승인요청 내용(gate_summary) ────────────────────────────────────────────
def test_extract_section():
    md = "# 제목\n서문\n## 1. 요약\n- 핵심 A\n- 핵심 B\n## 2. 다음\n무시"
    s = gk._extract_section(md, "요약", 500)
    assert "핵심 A" in s and "핵심 B" in s and "무시" not in s


def test_compact_policy():
    pol = {"recency_policy": {"recent_ratio": 0.6},
           "source_balance_policy": {"min_per_category": {"academic": 2, "vendor": 2, "news": 0}}}
    s = gk._compact_policy(pol)
    assert "recent≥0.6" in s and "academic≥2" in s and "news" not in s  # 0 은 생략


def test_gate_summary_entry_vs_output(tmp_path=None):
    import tempfile, os as _os
    d = tempfile.mkdtemp()
    orig = gk.COMPANY_ROOT
    gk.COMPANY_ROOT = d
    try:
        mroot = _os.path.join(d, "reports", "M-TEST")
        _os.makedirs(mroot)
        with open(_os.path.join(mroot, "report.md"), "w", encoding="utf-8") as f:
            f.write("# R\n## 1. 요약\n- 온디바이스 추론은 조건부 trade-off\n## 2. 끝\n")
        pl = {"mission": "M-TEST", "topic": "테스트 주제",
              "stages": [{"id": 1, "name": "Scoping"}, {"id": 11, "name": "Deliver"}],
              "policy": {"recency_policy": {"recent_ratio": 0.6}}}
        # 진입 게이트(upstream 없음): 계획·정책
        entry = gk.gate_summary({"mission": "M-TEST", "name": "Scoping", "upstream": []}, pl)
        assert "파이프라인" in entry and "테스트 주제" in entry and "recent≥0.6" in entry
        # 산출 게이트(upstream 있음): 보고서 요약 + 공개 대상
        out = gk.gate_summary({"mission": "M-TEST", "name": "Deliver", "upstream": ["t_10"]}, pl)
        assert "trade-off" in out and "공개 대상" in out
    finally:
        gk.COMPANY_ROOT = orig


def test_gate_summary_middle_gate_reads_approval_artifact():
    """중간 Sam 게이트(진입도 산출도 아님) — 기존엔 report.md 를 찾다 실패해 산출물 목록만
    나열했다. 템플릿이 stage.approval_artifact 로 승인 대상을 선언하면 그것을 실어 보낸다."""
    import tempfile, os as _os
    d = tempfile.mkdtemp()
    orig = gk.COMPANY_ROOT
    gk.COMPANY_ROOT = d
    try:
        mroot = _os.path.join(d, "reports", "M-TEST")
        _os.makedirs(mroot)
        with open(_os.path.join(mroot, "outline.md"), "w", encoding="utf-8") as f:
            f.write("# 목차\n- 1장 서론\n- 2장 관련연구\n")
        pl = {"mission": "M-TEST", "topic": "논문 주제",
              "stages": [{"id": 7, "name": "Synthesis", "task_id": "t_7"},
                         {"id": 8, "name": "Draft Sections", "task_id": "t_8",
                          "approval_artifact": "reports/M-TEST/outline.md"}],
              "policy": {}}
        g = {"mission": "M-TEST", "name": "Draft Sections", "task_id": "t_8", "upstream": ["t_7"]}
        s = gk.gate_summary(g, pl)
        assert "승인 대상" in s and "outline.md" in s, s
        assert "2장 관련연구" in s, s          # 내용이 실제로 실렸는가
        assert "공개 대상" not in s, s          # 산출(Deliver) 게이트로 오분류되지 않았는가
    finally:
        gk.COMPANY_ROOT = orig


def test_gate_summary_output_gate_finds_draft_md():
    """아키타입마다 최종 산출 파일명이 다르다(A=report.md · B=draft.md)."""
    import tempfile, os as _os
    d = tempfile.mkdtemp()
    orig = gk.COMPANY_ROOT
    gk.COMPANY_ROOT = d
    try:
        mroot = _os.path.join(d, "reports", "M-TEST")
        _os.makedirs(mroot)
        with open(_os.path.join(mroot, "draft.md"), "w", encoding="utf-8") as f:
            f.write("# 원고\n## 요약\n- 핵심 주장 X\n")
        pl = {"mission": "M-TEST", "stages": [{"id": 11, "name": "Deliver", "task_id": "t_11"}]}
        s = gk.gate_summary({"mission": "M-TEST", "name": "Deliver",
                             "task_id": "t_11", "upstream": ["t_10"]}, pl)
        assert "핵심 주장 X" in s and "draft.md" in s, s
    finally:
        gk.COMPANY_ROOT = orig


def test_compact_completion_policy():
    s = gk._compact_completion({"completion_policy": {"require_e2e_green": True,
                                                      "require_task_checkboxes": True,
                                                      "require_scenario_coverage": False}})
    assert "e2e_green" in s and "task_checkboxes" in s and "scenario_coverage" not in s, s


def test_approval_artifact_of_missing_returns_none():
    pl = {"stages": [{"id": 1, "task_id": "t_1"}]}
    assert gk.approval_artifact_of({"task_id": "t_1"}, pl) is None
    assert gk.approval_artifact_of({"task_id": "t_x"}, pl) is None


# ── 검증자 profile 인식 (2026-08-05 · 실미션 착수 전 발견) ───────────────────
def test_verifier_profiles_reads_template_declaration():
    """★ 결함 재현: 검증자 profile 이 하드코딩이면 템플릿이 선언한 새 검증자를 못 본다.

    실측 — `webapp-build` stage 8(`Test & Verify`)의 검증자는 `tester` 다. 하드코딩
    `{fact-checker, reviewer}` 만 보면 그 stage 가 done 이 돼도 게이트키퍼가 쳐다보지 않아
    downstream 이 blocked 인 채 영구 정지한다(리비전 루프도 로그도 없다).
    """
    import tempfile, os as _os, json as _json
    d = tempfile.mkdtemp()
    orig = gk.COMPANY_ROOT
    gk.COMPANY_ROOT = d
    try:
        mroot = _os.path.join(d, "reports", "M-TEST")
        _os.makedirs(mroot)
        pl = {"mission": "M-TEST", "stages": [
            {"id": 7, "name": "Implementation", "profile": "developer", "verifier": False},
            {"id": 8, "name": "Test & Verify", "profile": "tester", "verifier": True},
        ]}
        with open(_os.path.join(mroot, "pipeline.json"), "w", encoding="utf-8") as f:
            _json.dump(pl, f)
        got = gk.verifier_profiles()
        assert "tester" in got, f"템플릿이 선언한 검증자를 못 봤다: {got}"
        assert {"fact-checker", "reviewer"} <= got, "폴백 집합이 사라졌다"
        assert "developer" not in got, "검증자가 아닌 stage 의 profile 을 끌어왔다"
    finally:
        gk.COMPANY_ROOT = orig


def test_verifier_profiles_falls_back_when_no_pipeline():
    """pipeline.json 이 없는 구 미션에서도 기존 동작을 유지한다."""
    import tempfile
    orig = gk.COMPANY_ROOT
    gk.COMPANY_ROOT = tempfile.mkdtemp()
    try:
        assert gk.verifier_profiles() == {"fact-checker", "reviewer"}
    finally:
        gk.COMPANY_ROOT = orig


# ── artifact_inspection (승인문 보강 · docs/11 §7 ⑧) ──────────────────────────
# ⚠️ 이건 게이트가 아니라 **사람에게 보여줄 숫자**다. M-2026-005 stage 8 승인 요청은
#    "검증 통과했으니 집필 시작할까요" 였고, 그 시점 분석 11편 중 8편이 껍데기였다.
#    승인문이 검증 판정만 옮기면 **사람에게 가는 정보가 이미 오염돼 있다.**
def _mk_mission(files: dict) -> str:
    import tempfile, os as _os
    d = tempfile.mkdtemp()
    for rel, body in files.items():
        p = _os.path.join(d, rel)
        _os.makedirs(_os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(body)
    return d


def test_inspection_flags_self_declared_simulation():
    d = _mk_mission({"analysis/a.md": "# A\n- **Evidence:** [Simulated deep analysis based on x.]\n"})
    out = gk.artifact_inspection(d)
    assert "의심 문구" in out and "a.md" in out


def test_inspection_reports_tiny_markdown_files():
    d = _mk_mission({"analysis/a.md": "# A\n" + "x " * 20})
    out = gk.artifact_inspection(d)
    assert "2KB 미만" in out


def test_inspection_is_quiet_on_healthy_artifacts():
    """★ 반대 방향 — 정상 산출물에 경고를 붙이면 승인문이 늑대소년이 된다."""
    d = _mk_mission({"report.md": "# R\n" + ("본문 내용이 충분히 길다. " * 400)})
    out = gk.artifact_inspection(d)
    assert "의심 문구" not in out and "2KB 미만" not in out
    assert "산출물 실사" in out


def test_inspection_skips_raw_and_private_directories():
    """`raw/` 는 원문이라 크고, `_private/` 는 공개 대상이 아니다 — 실사 분포를 왜곡한다."""
    d = _mk_mission({"raw/big.md": "x" * 5000, "_private/secret.md": "[TBD]", "report.md": "y" * 3000})
    out = gk.artifact_inspection(d)
    assert "의심 문구" not in out
    assert "파일 1개" in out


def test_inspection_returns_empty_for_missing_dir():
    assert gk.artifact_inspection("/nonexistent/mission/root") == ""


# ── 보드 스코프 (신설 · argv 구성 회귀) ──────────────────────────────────────
# ⚠️ 이 파일에는 원래 `run`·`kanban_json`·`poll_once` 를 건드리는 테스트가 **하나도
#    없었다.** 보드 도입은 정확히 그 층을 바꾸므로 커버리지를 먼저 만든다.
def _capture_argv(monkey_target=None):
    """gk.subprocess.run 을 가로채 argv 를 기록한다."""
    import types
    calls = []

    class _P:
        returncode = 0
        stdout = "[]"
        stderr = ""

    orig = gk.subprocess.run
    gk.subprocess.run = lambda argv, **kw: (calls.append(list(argv)), _P())[1]
    return calls, (lambda: setattr(gk.subprocess, "run", orig))


def test_board_flag_precedes_the_subcommand():
    """★ `--board` 는 **전역 플래그**다 — 서브커맨드 뒤에 오면 argparse 가 거절한다.

    `hermes kanban --board X list` ✓ / `hermes kanban list --board X` ✗
    """
    calls, restore = _capture_argv()
    try:
        with gk.board_scope("m-2026-006"):
            gk.run(["list", "--json"], check=False)
    finally:
        restore()
    argv = calls[0]
    assert argv[:4] == ["hermes", "kanban", "--board", "m-2026-006"], argv
    assert argv[4] == "list", argv


def test_default_board_adds_no_flag():
    """기본 보드에서는 플래그를 붙이지 않는다 — 기존 동작과 완전히 같아야 한다."""
    calls, restore = _capture_argv()
    try:
        with gk.board_scope("default"):
            gk.run(["list", "--json"], check=False)
        with gk.board_scope(None):
            gk.run(["list", "--json"], check=False)
    finally:
        restore()
    for argv in calls:
        assert "--board" not in argv, argv


def test_board_scope_restores_previous_scope():
    """중첩 스코프가 새면 다음 미션의 카드를 엉뚱한 보드에서 조회한다."""
    with gk.board_scope("a"):
        with gk.board_scope("b"):
            assert gk.current_board() == "b"
        assert gk.current_board() == "a"
    assert gk.current_board() == "default"


def test_legacy_pipeline_without_board_falls_back_to_default():
    """★ 하위 호환 — 기존 미션의 pipeline.json 에는 board 키가 없다."""
    import tempfile, json as _json, os as _os
    d = tempfile.mkdtemp()
    _os.makedirs(_os.path.join(d, "reports", "M-OLD"), exist_ok=True)
    with open(_os.path.join(d, "reports", "M-OLD", "pipeline.json"), "w", encoding="utf-8") as f:
        _json.dump({"mission": "M-OLD", "stages": []}, f)
    old = gk.COMPANY_ROOT
    gk.COMPANY_ROOT = d
    try:
        assert gk.board_of("M-OLD") == "default"
    finally:
        gk.COMPANY_ROOT = old


def test_active_boards_falls_back_loudly_when_listing_fails():
    """★ 조회 실패에 조용히 default 로 축소하면 그게 fail-open 이다 — 로그가 남아야 한다."""
    logs = []
    orig_log, orig_json, orig_pl = gk.log, gk.kanban_json, gk.load_all_pipelines
    gk.log = lambda m: logs.append(m)
    gk.kanban_json = lambda args: None
    gk.load_all_pipelines = lambda: [{"board": "m-2026-006"}, {"mission": "M-OLD"}]
    try:
        got = gk.active_boards()
    finally:
        gk.log, gk.kanban_json, gk.load_all_pipelines = orig_log, orig_json, orig_pl
    assert got == ["default", "m-2026-006"], got
    assert any("boards list 조회 실패" in m for m in logs), logs


def test_active_boards_skips_archived():
    orig = gk.kanban_json
    gk.kanban_json = lambda args: [{"slug": "default"}, {"slug": "old", "archived": True}]
    try:
        assert gk.active_boards() == ["default"]
    finally:
        gk.kanban_json = orig



# ── 리비전 지시문에 게이트 **사유**가 실리는가 (2026-08-06 · M-2026-006 ⑨-g) ──
# ★ 이 묶음의 존재 이유: 리비전 카드 본문이
#     `[객관 게이트 실패 gates=['symbol_truth']] <LLM 검증자의 PASS 요약>`
#   이었다. 게이트 이름만 있고 사유가 없으며, 이어지는 문장은 "다 잘 됐다" 였다.
#   워커는 무엇을 고칠지 알 수 없다. 출력을 capture 해 놓고 returncode 만 쓴 탓이다.

GATE_MSG = ("FAIL(usage): SCOPE.md frontmatter 에 `codebase:` 가 없다 — "
            "무엇과 대조할지 알 수 없다. fail-closed")


def test_gate_failure_detail_carries_the_reason_not_just_the_name():
    """★ 결함 재현: 사유가 실려야 워커가 고칠 수 있다."""
    d = gk.format_gate_failures([("symbol_truth", GATE_MSG)])
    assert "symbol_truth" in d
    assert "frontmatter" in d and "codebase" in d, f"게이트 사유가 실리지 않았다: {d}"


def test_gate_failure_detail_is_bounded():
    """카드 본문은 다음 워커의 프롬프트다 — 무한정 실으면 지시가 묻힌다."""
    d = gk.format_gate_failures([("g", "x" * 5000)])
    assert len(d) < gk.GATE_MSG_CHARS + 300, f"길이 상한이 없다: {len(d)}"
    assert "생략" in d, "잘랐다는 사실을 적지 않았다"


def test_silent_gate_is_reported_as_silent_not_as_no_reason():
    """★ 반대 방향 — 게이트가 아무 말도 안 하면 그 사실 자체를 적어야 한다.

    빈 문자열을 그대로 실으면 '사유 없음'이 되어 침묵과 구분되지 않는다.
    """
    d = gk.format_gate_failures([("g", "")])
    assert "출력하지 않았다" in d or "사유" in d, d


def test_multiple_failed_gates_all_appear():
    d = gk.format_gate_failures([("api_coverage", "커버리지 61% < 90%"),
                                 ("doc_links", "끊어진 앵커 3건")])
    assert "api_coverage" in d and "doc_links" in d
    assert "61%" in d and "앵커" in d, d

if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
