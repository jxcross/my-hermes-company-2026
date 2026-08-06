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

# ── Discord 병렬 경로 (2026-08-07 · docs/16) ────────────────────────────────
# ⚠️ 이 묶음이 지키는 불변식은 하나다: **한 플랫폼의 실패가 다른 플랫폼을 막지 못한다.**
#    회사망에서 slack.com 이 차단됐고, 그래서 Discord 를 붙였다. Slack 실패가 Discord 를
#    막으면 이 작업 전체가 무효다.
GATE = {"mission": "M-2026-008", "name": "Scoping",
        "task_id": "t_abc123", "board": "m-2026-008"}

# ★ 리팩터 **이전** 코드(:894-897)가 만들던 문자열. 한 글자도 바뀌면 안 된다.
SLACK_GOLDEN = (
    ':large_yellow_circle: *[승인 요청]* M-2026-008 · Scoping  '
    '(`t_abc123` · board `m-2026-008`)\n요약본문\n'
    '— 승인: `승인` (또는 `승인 t_abc123`) · 반려/보완은 여기서 논의(게이트 대기 유지). 권한: Sam.')


def test_slack_approval_text_is_byte_identical_after_refactor():
    """★ 골든 — 리팩터가 Slack 표시를 바꾸지 않았다는 증거."""
    assert gk.render_approval_request(GATE, "요약본문", "slack") == SLACK_GOLDEN


def test_discord_render_uses_markdown_not_mrkdwn():
    """Discord 는 `*굵게*`(별 1개)가 **기울임**이고 `:shortcode:` 는 문자 그대로 보인다."""
    d = gk.render_approval_request(GATE, "요약본문", "discord")
    assert "**[승인 요청]**" in d, d
    assert ":large_yellow_circle:" not in d, "Slack 숏코드가 Discord 본문에 남았다"
    assert "t_abc123" in d and "board `m-2026-008`" in d


def test_chunk_message_never_exceeds_limit_and_loses_nothing():
    text = "\n".join(f"줄 {i} " + "가" * 40 for i in range(40))
    parts = gk.chunk_message(text, 200)
    assert all(gk.u16len(p) <= 200 for p in parts), [gk.u16len(p) for p in parts]
    assert "\n".join(parts) == text, "라운드트립 실패 — 글자를 잃거나 더했다"


def test_chunk_message_hard_splits_an_overlong_single_line():
    """줄 경계가 없으면 하드 분할 — 무한 루프도, 글자 손실도 없어야 한다."""
    parts = gk.chunk_message("가" * 500, 100)
    assert len(parts) >= 5 and all(gk.u16len(p) <= 100 for p in parts)
    assert "".join(parts) == "가" * 500


def test_chunk_message_measures_utf16_not_python_len():
    """★ Discord 의 2000 은 **UTF-16 코드유닛**이다. BMP 밖 이모지는 1자가 2유닛.
       len() 으로 재면 통과시켜 놓고 서버가 400 을 준다."""
    s = "𝕏" * 60          # len()=60 이지만 UTF-16 으로는 120
    assert len(s) == 60 and gk.u16len(s) == 120
    assert all(gk.u16len(p) <= 100 for p in gk.chunk_message(s, 100))


def test_chunk_message_empty_input_is_one_empty_chunk():
    """0개면 '게시할 것이 없다'와 구분이 안 된다."""
    assert gk.chunk_message("", 100) == [""]


def test_normalize_discord_history_reads_a_bare_array_oldest_first():
    payload = [{"id": "3", "author": {"id": "U1"}, "content": "셋"},
               {"id": "2", "author": {"id": "U1", "bot": True}, "content": "둘"},
               {"id": "1", "author": {"id": "U1"}, "content": "하나"}]
    out = gk.normalize_discord_history(payload)
    assert [m["id"] for m in out] == ["1", "2", "3"], "최신순→오래된순 변환 실패"
    assert out[1]["bot"] is True
    assert out[0]["text"] == "하나"


def test_normalize_discord_history_rejects_slack_shaped_payload():
    """★ Discord 응답에는 {"ok":...} 래퍼가 없다. Slack 모양을 넣으면 빈 결과여야 한다 —
       조용히 통과시키면 승인이 영영 감지되지 않는다."""
    assert gk.normalize_discord_history({"ok": True, "messages": [{"ts": "1"}]}) == []
    assert gk.normalize_discord_history(None) == []


def test_normalize_discord_history_skips_malformed_entries():
    payload = [{"id": "1"}, {"author": {"id": "U"}}, {"id": "2", "author": {"id": "U"}}]
    out = gk.normalize_discord_history(payload)
    assert [m["id"] for m in out] == ["2"]
    assert out[0]["text"] == "", "content 없음이 KeyError 가 됐다"


def test_normalize_slack_history_matches_the_old_reversed_order():
    payload = {"ok": True, "messages": [{"ts": "2", "user": "U", "text": "나중"},
                                        {"ts": "1", "user": "U", "text": "먼저"}]}
    assert [m["id"] for m in gk.normalize_slack_history(payload)] == ["1", "2"]
    assert gk.normalize_slack_history({"ok": False}) == []


def _state_file(tmp: dict):
    import json as _j
    import tempfile
    p = os.path.join(tempfile.mkdtemp(), "state.json")
    with open(p, "w", encoding="utf-8") as f:
        _j.dump(tmp, f)
    return p


def test_state_migration_promotes_bare_slack_entries():
    """★★ 마이그레이션이 없으면 **과거 승인이 소급 적용된다**(docs/16 §4).

    구 항목이 미확인이 되고 → 집합이 비어있지 않아 재시딩을 건너뛰고 →
    다음 틱에 history 가 통째로 새 메시지로 처리된다."""
    orig = gk.STATE_PATH
    gk.STATE_PATH = _state_file({"approval_seen": ["1754400000.000100"],
                                 "approval_posted": ["t_a"], "processed": ["x"]})
    try:
        st = gk.load_state()
        assert st["approval_seen"] == {"slack:1754400000.000100"}, st["approval_seen"]
        assert st["approval_posted"] == {"slack:t_a"}
        assert st["approval_seeded"] == {"slack"}, "구 상태를 미시딩으로 오인했다"
        assert st["processed"] == {"x"}, "processed 는 네임스페이싱 대상이 아니다"
    finally:
        gk.STATE_PATH = orig


def test_state_fresh_install_is_not_marked_seeded():
    """빈 상태에서 seeded 로 표시하면 baseline 없이 폴링해 소급 승인이 난다."""
    orig = gk.STATE_PATH
    gk.STATE_PATH = _state_file({})
    try:
        assert gk.load_state()["approval_seeded"] == set()
    finally:
        gk.STATE_PATH = orig


def test_state_roundtrip_preserves_namespacing():
    orig = gk.STATE_PATH
    gk.STATE_PATH = _state_file({})
    try:
        st = gk.load_state()
        st["approval_seen"] |= {"slack:1.1", "discord:1401234567890123456"}
        st["approval_seeded"].add("discord")
        gk.save_state(st)
        again = gk.load_state()
        assert again["approval_seen"] == st["approval_seen"]
        assert again["approval_seeded"] == {"discord"}
    finally:
        gk.STATE_PATH = orig


def _stub_platforms(monkey: dict):
    """플랫폼별 이력을 주입하고 unblock 호출을 기록한다."""
    saved = {k: getattr(gk, k) for k in
             ("fetch_history", "pending_sam_gates", "all_upstream_done",
              "load_all_pipelines", "run", "notify", "gate_summary",
              "post_approval_request", "enabled_platforms")}
    calls = []
    gk.fetch_history = lambda p, limit: monkey["hist"].get(p)
    gk.load_all_pipelines = lambda: []
    gk.all_upstream_done = lambda *a, **k: True
    gk.pending_sam_gates = monkey["gates"]
    gk.gate_summary = lambda *a, **k: "요약"
    gk.post_approval_request = lambda *a, **k: True
    gk.notify = lambda *a, **k: None
    gk.enabled_platforms = lambda: monkey.get("plats", ["slack", "discord"])
    gk.run = lambda args, check=True: calls.append(list(args))
    if monkey.get("gate_until_unblock"):
        gk.pending_sam_gates = _gates_until_unblock(monkey["gate_until_unblock"], calls)
    return calls, (lambda: [setattr(gk, k, v) for k, v in saved.items()])


def _msg(mid, author, text):
    return {"id": mid, "author": author, "text": text, "bot": False}


def _gates_until_unblock(g, calls):
    """실제 동작을 흉내낸다: unblock 이 성공하면 그 게이트는 blocked 가 아니게 되어
    `pending_sam_gates` 목록에서 사라진다.

    ⚠️ 고정 시퀀스(pop)로 쓰면 안 된다 — `approval_poll` 자신도 이 함수를 한 번 부르고,
       그 호출이 시퀀스를 소비해 버린다(첫 시도에서 실제로 겪은 오류)."""
    def _f(*a, **k):
        done = any(c[:2] == ["unblock", g["task_id"]] for c in calls)
        return [] if done else [g]
    return _f


def test_slack_failure_does_not_block_discord_approvals():
    """★★ 이 파일에서 가장 중요한 테스트.

    옛 코드는 Slack history 조회 실패 시 `return` 으로 함수를 빠져나갔다. 그대로 두면
    **Slack 이 죽어 있을 때 Discord 승인이 영영 처리되지 않는다** — 그런데 Slack 이
    죽은 것이 이 경로를 만든 이유다. 그 한 줄이 기능 전체를 무효화한다."""
    g = dict(GATE, upstream=[])
    calls, restore = _stub_platforms({
        "hist": {"slack": None,                       # ← Slack 은 죽어 있다
                 "discord": [_msg("140100", "SAM_D", "승인")]},
        "gates": lambda *a, **k: [g], "gate_until_unblock": g,
    })
    orig_allowed = gk.DISCORD_ALLOWED_USERS
    gk.DISCORD_ALLOWED_USERS = {"SAM_D"}
    try:
        st = {"processed": set(), "approval_posted": set(),
              "approval_seen": set(), "approval_seeded": {"slack", "discord"}}
        gk.approval_poll(st, dry=False)
        assert any(c[:2] == ["unblock", "t_abc123"] for c in calls), \
            f"Slack 실패가 Discord 승인을 막았다: {calls}"
    finally:
        gk.DISCORD_ALLOWED_USERS = orig_allowed
        restore()


def test_discord_failure_does_not_block_slack_approvals():
    """반대 방향도 같아야 한다(대칭 확인)."""
    g = dict(GATE, upstream=[])
    calls, restore = _stub_platforms({
        "hist": {"slack": [_msg("1754.1", "SAM_S", "승인")], "discord": None},
        "gates": lambda *a, **k: [g], "gate_until_unblock": g,
    })
    orig = gk.SLACK_ALLOWED_USERS
    gk.SLACK_ALLOWED_USERS = {"SAM_S"}
    try:
        st = {"processed": set(), "approval_posted": set(),
              "approval_seen": set(), "approval_seeded": {"slack", "discord"}}
        gk.approval_poll(st, dry=False)
        assert any(c[:2] == ["unblock", "t_abc123"] for c in calls), calls
    finally:
        gk.SLACK_ALLOWED_USERS = orig
        restore()


def test_one_platform_raising_does_not_stop_the_other():
    """예외도 마찬가지다 — 루프가 죽으면 안 된다."""
    g = dict(GATE, upstream=[])
    calls, restore = _stub_platforms({
        "hist": {"discord": [_msg("140100", "SAM_D", "승인")]},
        "gates": lambda *a, **k: [g], "gate_until_unblock": g,
    })
    boom = gk.fetch_history
    gk.fetch_history = lambda p, limit: (_ for _ in ()).throw(RuntimeError("boom")) \
        if p == "slack" else boom(p, limit)
    orig = gk.DISCORD_ALLOWED_USERS
    gk.DISCORD_ALLOWED_USERS = {"SAM_D"}
    try:
        st = {"processed": set(), "approval_posted": set(),
              "approval_seen": set(), "approval_seeded": {"slack", "discord"}}
        gk.approval_poll(st, dry=False)
        assert any(c[:2] == ["unblock", "t_abc123"] for c in calls), calls
    finally:
        gk.DISCORD_ALLOWED_USERS = orig
        restore()


def test_approval_on_both_platforms_unblocks_only_once():
    """★ 이중 unblock 불가 — 승인마다 대기 게이트를 **재조회**하기 때문이다."""
    g = dict(GATE, upstream=[])
    calls, restore = _stub_platforms({
        "hist": {"slack": [_msg("1754.1", "SAM_S", "승인")],
                 "discord": [_msg("140100", "SAM_D", "승인")]},
        "gates": lambda *a, **k: [g], "gate_until_unblock": g,
    })
    o1, o2 = gk.SLACK_ALLOWED_USERS, gk.DISCORD_ALLOWED_USERS
    gk.SLACK_ALLOWED_USERS, gk.DISCORD_ALLOWED_USERS = {"SAM_S"}, {"SAM_D"}
    try:
        st = {"processed": set(), "approval_posted": set(),
              "approval_seen": set(), "approval_seeded": {"slack", "discord"}}
        gk.approval_poll(st, dry=False)
        ub = [c for c in calls if c[:1] == ["unblock"]]
        assert len(ub) == 1, f"unblock 이 {len(ub)}회 — 이중 반영됐다: {calls}"
    finally:
        gk.SLACK_ALLOWED_USERS, gk.DISCORD_ALLOWED_USERS = o1, o2
        restore()


def test_second_approval_retries_when_the_first_unblock_failed():
    """★ 깨뜨린 픽스처 — 위 테스트가 '우연히 1회'가 아니라 **재조회 기제**를 재고 있음을
    증명한다. unblock 이 실패해 게이트가 blocked 로 남으면 두 번째 승인이 재시도해야 한다.
    (이건 버그가 아니라 Discord 를 붙이는 이유 그 자체다 — 한쪽이 죽어도 승인이 관철된다.)"""
    g = dict(GATE, upstream=[])
    calls, restore = _stub_platforms({
        "hist": {"slack": [_msg("1754.1", "SAM_S", "승인")],
                 "discord": [_msg("140100", "SAM_D", "승인")]},
        "gates": lambda *a, **k: [g],       # ← 계속 blocked (unblock 실패 시뮬레이션)
    })
    o1, o2 = gk.SLACK_ALLOWED_USERS, gk.DISCORD_ALLOWED_USERS
    gk.SLACK_ALLOWED_USERS, gk.DISCORD_ALLOWED_USERS = {"SAM_S"}, {"SAM_D"}
    try:
        st = {"processed": set(), "approval_posted": set(),
              "approval_seen": set(), "approval_seeded": {"slack", "discord"}}
        gk.approval_poll(st, dry=False)
        ub = [c for c in calls if c[:1] == ["unblock"]]
        assert len(ub) == 2, f"실패한 unblock 을 재시도하지 않았다: {calls}"
    finally:
        gk.SLACK_ALLOWED_USERS, gk.DISCORD_ALLOWED_USERS = o1, o2
        restore()


def test_approval_from_a_non_allowed_user_is_ignored():
    """★ 보안 앵커 — allowlist 밖의 `승인` 은 아무 일도 일으키지 않는다."""
    g = dict(GATE, upstream=[])
    calls, restore = _stub_platforms({
        "hist": {"discord": [_msg("140100", "STRANGER", "승인")]},
        "gates": lambda *a, **k: [g], "plats": ["discord"],
    })
    orig = gk.DISCORD_ALLOWED_USERS
    gk.DISCORD_ALLOWED_USERS = {"SAM_D"}
    try:
        st = {"processed": set(), "approval_posted": set(),
              "approval_seen": set(), "approval_seeded": {"discord"}}
        gk.approval_poll(st, dry=False)
        assert not [c for c in calls if c[:1] == ["unblock"]], f"보안 앵커 뚫림: {calls}"
    finally:
        gk.DISCORD_ALLOWED_USERS = orig
        restore()


def test_posted_keys_are_namespaced_so_both_platforms_get_the_request():
    """단일 키면 먼저 올린 쪽이 다른 쪽의 게시를 막는다."""
    g = dict(GATE, upstream=[])
    posted = []
    calls, restore = _stub_platforms({
        "hist": {"slack": [], "discord": []},
        "gates": lambda *a, **k: [g],
    })
    gk.post_approval_request = lambda plat, gg, text: (posted.append(plat), True)[1]
    try:
        st = {"processed": set(), "approval_posted": set(),
              "approval_seen": set(), "approval_seeded": {"slack", "discord"}}
        gk.approval_poll(st, dry=False)
        assert sorted(posted) == ["discord", "slack"], posted
        assert st["approval_posted"] == {"slack:t_abc123", "discord:t_abc123"}
    finally:
        restore()


def test_polling_is_skipped_until_that_platform_is_seeded():
    """★ 시딩 전에 폴링하면 그게 바로 소급 승인이다(fail-closed)."""
    g = dict(GATE, upstream=[])
    calls, restore = _stub_platforms({
        "hist": {"discord": [_msg("140100", "SAM_D", "승인")]},
        "gates": lambda *a, **k: [g], "plats": ["discord"],
    })
    orig = gk.DISCORD_ALLOWED_USERS
    gk.DISCORD_ALLOWED_USERS = {"SAM_D"}
    try:
        st = {"processed": set(), "approval_posted": set(),
              "approval_seen": set(), "approval_seeded": set()}   # ← 미시딩
        gk.approval_poll(st, dry=False)
        assert not [c for c in calls if c[:1] == ["unblock"]], "미시딩인데 승인을 처리했다"
    finally:
        gk.DISCORD_ALLOWED_USERS = orig
        restore()


def test_warn_throttle_suppresses_but_reports_the_count():
    """조용해지는 것과 나아지는 것은 다르다 — 억제 건수를 합산해 드러내야 한다."""
    gk._WARN_STATE.clear()
    lines = []
    orig, gk.log = gk.log, lambda m: lines.append(m)
    try:
        assert gk.warn_throttled("k", "실패", now=0.0) is True
        for i in range(5):
            assert gk.warn_throttled("k", "실패", now=1.0 + i) is False
        assert gk.warn_throttled("k", "실패", now=100.0) is True
        assert "5회 억제" in lines[-1], lines
    finally:
        gk.log = orig
        gk._WARN_STATE.clear()


def test_warn_throttle_is_per_key_so_a_new_failure_is_not_masked():
    """★ 전역 억제가 되면 진짜 실패가 묻힌다."""
    gk._WARN_STATE.clear()
    try:
        assert gk.warn_throttled("a", "x", now=0.0) is True
        assert gk.warn_throttled("b", "y", now=0.1) is True, "다른 key 가 억제됐다"
    finally:
        gk._WARN_STATE.clear()


def test_notify_sends_to_every_target_discord_first():
    calls = []

    class _P:
        returncode = 0
        stdout = stderr = ""
    orig_run, orig_d = gk.subprocess.run, gk.DISCORD_TARGET
    gk.subprocess.run = lambda argv, **kw: (calls.append(list(argv)), _P())[1]
    gk.DISCORD_TARGET = "discord:140199"
    gk._BREAKER.clear()
    try:
        gk.notify("본문", dry=False)
        tos = [c[c.index("--to") + 1] for c in calls]
        assert tos == ["discord:140199", gk.SLACK_TARGET], tos
    finally:
        gk.subprocess.run, gk.DISCORD_TARGET = orig_run, orig_d


def test_notify_continues_when_the_first_target_times_out():
    """★ 한 목적지 실패가 다른 목적지를 막으면 안 된다."""
    calls = []

    class _P:
        returncode = 0
        stdout = stderr = ""

    def _run(argv, **kw):
        calls.append(list(argv))
        if "discord:140199" in argv:
            raise gk.subprocess.TimeoutExpired(argv, 60)
        return _P()
    orig_run, orig_d = gk.subprocess.run, gk.DISCORD_TARGET
    gk.subprocess.run, gk.DISCORD_TARGET = _run, "discord:140199"
    gk._BREAKER.clear(); gk._WARN_STATE.clear()
    try:
        gk.notify("본문", dry=False)
        assert len(calls) == 2, f"첫 대상 실패 후 멈췄다: {calls}"
    finally:
        gk.subprocess.run, gk.DISCORD_TARGET = orig_run, orig_d
        gk._BREAKER.clear(); gk._WARN_STATE.clear()


def test_notify_targets_is_unchanged_when_discord_is_not_configured():
    """Discord 미설정이면 오늘과 **완전히 동일**해야 한다."""
    orig = gk.DISCORD_TARGET
    gk.DISCORD_TARGET = ""
    try:
        assert gk.notify_targets() == [gk.SLACK_TARGET]
    finally:
        gk.DISCORD_TARGET = orig


def test_enabled_platforms_is_fail_closed_on_missing_config():
    o = (gk.SLACK_BOT_TOKEN, gk.DISCORD_BOT_TOKEN, gk.DISCORD_APPROVALS_CHANNEL)
    try:
        gk.SLACK_BOT_TOKEN, gk.DISCORD_BOT_TOKEN, gk.DISCORD_APPROVALS_CHANNEL = "", "", ""
        assert gk.enabled_platforms() == []
        gk.DISCORD_BOT_TOKEN = "tok"
        assert gk.enabled_platforms() == [], "채널 없이 discord 가 켜졌다(fail-closed 위반)"
        gk.DISCORD_APPROVALS_CHANNEL = "140100"
        assert gk.enabled_platforms() == ["discord"]
        gk.SLACK_BOT_TOKEN = "xoxb-x"
        assert gk.enabled_platforms() == ["slack", "discord"]
    finally:
        gk.SLACK_BOT_TOKEN, gk.DISCORD_BOT_TOKEN, gk.DISCORD_APPROVALS_CHANNEL = o


def test_discord_api_retries_on_429_and_never_raises():
    """★ urllib 은 4xx 에서 HTTPError 를 raise 한다. blanket except 뒤에 두면
       429 가 네트워크 오류와 구분되지 않아 **재시도가 영영 안 돈다.**"""
    import io
    import urllib.error
    slept, seq = [], []

    def _open(req, timeout=None):
        seq.append(1)
        if len(seq) == 1:
            raise urllib.error.HTTPError(
                "u", 429, "rate", {}, io.BytesIO(b'{"retry_after": 0.5}'))

        class _R:
            def read(self, *a): return b'[]'
            def __enter__(self): return self
            def __exit__(self, *a): return False
        return _R()
    o_open, o_sleep, o_tok = gk.urllib.request.urlopen, gk.time.sleep, gk.DISCORD_BOT_TOKEN
    gk.urllib.request.urlopen = _open
    gk.time.sleep = lambda s: slept.append(s)
    gk.DISCORD_BOT_TOKEN = "tok"
    gk._WARN_STATE.clear()
    try:
        out = gk.discord_api("/channels/1/messages", {"limit": 1})
        assert slept == [0.5], f"retry_after 를 안 읽었다: {slept}"
        assert out == [], out
    finally:
        gk.urllib.request.urlopen, gk.time.sleep = o_open, o_sleep
        gk.DISCORD_BOT_TOKEN = o_tok
        gk._WARN_STATE.clear()


def test_discord_api_returns_none_on_auth_error_without_retrying():
    import io
    import urllib.error
    seq = []

    def _open(req, timeout=None):
        seq.append(1)
        raise urllib.error.HTTPError("u", 403, "forbidden", {}, io.BytesIO(b"{}"))
    o_open, o_tok = gk.urllib.request.urlopen, gk.DISCORD_BOT_TOKEN
    gk.urllib.request.urlopen, gk.DISCORD_BOT_TOKEN = _open, "tok"
    gk._WARN_STATE.clear()
    try:
        assert gk.discord_api("/channels/1/messages") is None
        assert len(seq) == 1, "권한 오류를 재시도했다(무의미하다)"
    finally:
        gk.urllib.request.urlopen, gk.DISCORD_BOT_TOKEN = o_open, o_tok
        gk._WARN_STATE.clear()


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
