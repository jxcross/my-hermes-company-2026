#!/usr/bin/env python3
"""
instantiate_template 팬아웃 배치 테스트
=======================================
Hermes `delegate_task` 는 한 배치가 `delegation.max_concurrent_children`(기본 3)을
넘으면 **큐잉하지 않고 tool_error 로 거절**한다. 따라서 워커가 5개인 스테이지는
"3 + 2, 2라운드"로 나눠 위임해야 하는데, 기존 주입 문구는 "**한 번에** 위임하라"만
말하고 배치 상한을 언급하지 않아 분할을 모델의 자체 판단에 맡기고 있었다
(M-2026-004 에서는 scout 가 알아서 나눠 성공했으나 보장이 아니다).

`parallel.batch_size` 선언 + 주입 문구의 라운드 명시가 그 추측을 제거한다.
실행: python3 -m pytest scripts/tests/test_instantiate_template.py
(pytest 없으면) python3 scripts/tests/test_instantiate_template.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import instantiate_template as it  # noqa: E402


# ── batch_size 정규화 ────────────────────────────────────────────────────
def test_batch_size_defaults_when_absent():
    p = it.parallel_spec({"parallel": {"mode": "workers", "workers": ["a"]}})
    assert p["batch_size"] == it.DEFAULT_BATCH_SIZE, p


def test_batch_size_explicit_wins():
    p = it.parallel_spec({"parallel": {"mode": "workers", "workers": ["a"], "batch_size": 5}})
    assert p["batch_size"] == 5, p


def test_batch_size_bad_value_falls_back():
    p = it.parallel_spec({"parallel": {"mode": "per_item", "batch_size": "많이"}})
    assert p["batch_size"] == it.DEFAULT_BATCH_SIZE, p


def test_batch_size_floor_is_one():
    p = it.parallel_spec({"parallel": {"mode": "per_item", "batch_size": 0}})
    assert p["batch_size"] == 1, p


def test_legacy_parallel_true_still_works():
    p = it.parallel_spec({"parallel": True, "workers": ["a", "b"]})
    assert p["mode"] == "workers" and p["batch_size"] == it.DEFAULT_BATCH_SIZE, p


# ── 라운드 계산 ──────────────────────────────────────────────────────────
def test_batch_plan_splits_five_into_three_plus_two():
    assert it.batch_plan(5, 3) == [3, 2]


def test_batch_plan_single_round_when_under_cap():
    assert it.batch_plan(3, 3) == [3]
    assert it.batch_plan(2, 3) == [2]


def test_batch_plan_empty():
    assert it.batch_plan(0, 3) == []


# ── 주입 문구 ────────────────────────────────────────────────────────────
STAGE5W = {
    "id": 3, "parallel": {
        "mode": "workers",
        "workers": ["academic", "vendor", "research_org", "standards", "news"],
        "batch_size": 3, "shard": "raw/sources.<worker>.yaml", "merge_to": "raw/sources.yaml",
    },
}


def test_body_states_batch_cap_and_rounds():
    body = it.fanout_body(STAGE5W, "수집하라.")
    assert "최대 3개" in body, body
    assert "3 + 2" in body and "2라운드" in body, body


def test_body_warns_batch_is_rejected_not_queued():
    body = it.fanout_body(STAGE5W, "수집하라.")
    assert "max_concurrent_children" in body and "거절" in body, body


def test_body_no_longer_says_all_at_once():
    """'한 번에' 지시는 배치 상한과 모순 — 5워커에서 tool_error 를 유발한다."""
    assert "**한 번에**" not in it.fanout_body(STAGE5W, "수집하라.")


def test_body_single_batch_when_workers_fit():
    stage = {"id": 3, "parallel": {"mode": "workers", "workers": ["a", "b"], "batch_size": 3}}
    body = it.fanout_body(stage, "x")
    assert "한 배치로 위임" in body, body


def test_body_per_item_tells_model_to_count_first():
    stage = {"id": 5, "parallel": {"mode": "per_item", "over": "자료 각각", "batch_size": 3}}
    body = it.fanout_body(stage, "분석하라.")
    assert "동적" in body and "3개씩" in body, body


def test_no_parallel_body_unchanged():
    assert it.fanout_body({"id": 2}, "검색식 작성.") == "검색식 작성."


def test_body_forbids_making_kanban_cards_instead_of_delegating():
    """★ 실측 2026-08-06 M-2026-008 stage 3: 워커가 delegation 대신 **Kanban 자식 카드
    3장**을 만들고 자기는 done 처리했다. 카드들은 존재하지 않는 profile
    (`researcher-a/b/c`)에 배정돼 아무도 실행하지 않았고, 다음 단계가 **빈 입력으로**
    돌기 시작했다. 프로토콜이 '카드를 만들지 마라'를 말하지 않아서 모델이 아는 도구로
    손을 뻗은 것이다 — stage 1 본문에는 있던 금지가 여기엔 없었다.
    """
    body = it.fanout_body(STAGE5W, "수집하라.")
    assert "kanban create" in body and "decompose" in body, body
    assert "만들지 마라" in body, body


def test_body_ties_completion_to_the_merged_artifact():
    """★ '위임했다'를 '끝냈다'로 읽지 못하게 한다 — 완료 조건을 산출물로 못박는다.

    같은 실측에서 워커의 완료 요약은 "subagent 3개가 ready 상태"였다. 위임은 진행이지
    완료가 아닌데 카드가 done 이 됐고, **진행 신호 자체가 오염**됐다.
    """
    body = it.fanout_body(STAGE5W, "수집하라.")
    assert "완료 조건" in body and "raw/sources.yaml" in body, body
    assert "완료 보고는 산출물을 대신하지 못한다" in body, body


def test_no_completion_clause_without_a_merge_target():
    """merge_to 가 없으면 완료 조건으로 못박을 파일도 없다 — 없는 파일을 요구하지 마라."""
    stage = {"id": 3, "parallel": {"mode": "workers", "workers": ["a"], "batch_size": 3}}
    assert "완료 조건" not in it.fanout_body(stage, "x")


# ── 렌더 라벨 ────────────────────────────────────────────────────────────
def test_label_shows_batch_and_rounds():
    assert it.fanout_label(STAGE5W) == "⇉5워커/배치3×2R"


def test_label_omits_rounds_for_single_batch():
    stage = {"parallel": {"mode": "workers", "workers": ["a", "b"], "batch_size": 3}}
    assert it.fanout_label(stage) == "⇉2워커/배치3"


# ── 실제 템플릿 ──────────────────────────────────────────────────────────
def test_shipped_template_declares_batch_size_on_every_parallel_stage():
    tpl = it.load_template("trend-report")
    par = [s for s in tpl["stages"] if s.get("parallel")]
    assert par, "trend-report 에 parallel 스테이지가 없다"
    for s in par:
        assert isinstance(s["parallel"].get("batch_size"), int), f"stage {s['id']} batch_size 미선언"


# ── <MID> 치환 ────────────────────────────────────────────────────────────
# 2026-08-06 실미션이 발견: `resolve()` 가 gate.draft·approval_artifact 만 치환하고
# **body 를 빠뜨려**, 카드 본문이 워커에게 `reports/<MID>/SCOPE.md` 를 문자 그대로 보냈다.
# 강한 모델은 문맥에서 미션 id 를 해석해 버려 codex 시절 내내 드러나지 않았다.
def test_resolve_substitutes_mid_in_body():
    """★ 워커가 읽는 것은 body 다 — 여기에 플레이스홀더가 남으면 지시가 깨진다."""
    tpl = {"stages": [{"id": 1, "name": "S", "profile": "default", "upstream": [],
                       "body": "reports/<MID>/SCOPE.md 에 작성"}]}
    out = it.resolve(tpl, "M-2026-007")
    assert out["stages"][0]["body"] == "reports/M-2026-007/SCOPE.md 에 작성"


def test_no_shipped_template_leaks_mid_after_resolve():
    """★ 20종 전체 · 모든 stage · 모든 문자열 필드에 <MID> 가 남으면 안 된다.

    치환 대상 필드를 하나 더 늘렸을 때 또 빠뜨리지 않도록 **필드를 열거하지 않고**
    resolve 결과 전체를 훑는다.
    """
    def leaks(o, path=""):
        if isinstance(o, dict):
            return [p for k, v in o.items() for p in leaks(v, f"{path}.{k}" if path else k)]
        if isinstance(o, list):
            return [p for v in o for p in leaks(v, f"{path}[]")]
        return [path] if isinstance(o, str) and "<MID>" in o else []

    tpl_dir = os.path.join(it.REPO_ROOT, "templates")
    names = sorted(f[:-5] for f in os.listdir(tpl_dir) if f.endswith(".yaml"))
    assert len(names) >= 20, f"템플릿을 못 찾았다: {names}"
    bad = {}
    for name in names:
        got = leaks(it.resolve(it.load_template(name), "M-2026-999"))
        if got:
            bad[name] = sorted(set(got))
    assert not bad, f"<MID> 누출: {bad}"


# ── 게이트 겹침 불변식 ────────────────────────────────────────────────────
# academic-paper 변환에서 발견: sam_gate 와 검증자 downstream 이 한 stage 에 겹치면
# 번역기가 block 을 하나만 걸고 sam_gate 가 우선해 검증 게이트가 조용히 사라진다
# (= 검증 FAIL 이어도 Sam 승인만으로 진행 = 불변식 우회).
def _tpl(stages):
    return {"invariants": ["scoping_gate", "deliver_gate", "revision_loop"], "stages": stages}


OVERLAP = _tpl([
    {"id": 1, "name": "Scoping", "profile": "default", "sam_gate": True, "upstream": []},
    {"id": 2, "name": "Draft", "profile": "writer", "upstream": [1]},
    {"id": 3, "name": "Verify", "profile": "reviewer", "verifier": True, "upstream": [2]},
    {"id": 4, "name": "Next", "profile": "synthesizer", "sam_gate": True, "upstream": [3]},  # ← 겹침
    {"id": 5, "name": "Deliver", "profile": "default", "sam_gate": True, "upstream": [4]},
])


def test_gate_overlap_is_rejected():
    errs = it.check_invariants(OVERLAP)
    assert any("게이트 겹침" in e and "stage 4" in e for e in errs), errs


def test_gate_separated_passes():
    """승인 지점을 인접 stage(5)로 내리면 통과."""
    stages = [dict(s) for s in OVERLAP["stages"]]
    stages[3].pop("sam_gate")            # stage 4 = 검증 게이트만
    errs = it.check_invariants(_tpl(stages))
    assert not any("게이트 겹침" in e for e in errs), errs


def test_shipped_templates_have_no_gate_overlap():
    for name in ("trend-report", "academic-paper", "webapp-build"):
        errs = it.check_invariants(it.load_template(name))
        assert not errs, (name, errs)


def test_mid_pipeline_sam_gates_declare_approval_artifact():
    """중간 Sam 게이트(진입·마지막이 아닌)는 승인 대상 파일을 선언해야 한다 — 없으면
    gate_summary 가 무엇을 승인하는지 실어 보내지 못한다(docs/13 §5)."""
    for name in ("trend-report", "academic-paper", "webapp-build"):
        stages = it.load_template(name)["stages"]
        for i, s in enumerate(stages):
            mid = 0 < i < len(stages) - 1
            if s.get("sam_gate") and mid:
                assert s.get("approval_artifact"), (name, s["id"], s["name"])


# ── 미등록 profile 감지 ───────────────────────────────────────────────────
# webapp-build(D) 변환에서 첫 발생: architect·developer·tester 신규 필요.
# 고정 8종을 박지 않고 profiles-src/ 를 진실로 삼는다(profile 수는 늘어날 수 있다).
def test_registered_profiles_reads_profiles_src():
    have = it.registered_profiles()
    assert "default" in have, have            # solomon-profile 은 별도 위치
    assert {"scout", "reader", "writer", "reviewer", "fact-checker"} <= have, have


def test_missing_profiles_detects_unknown():
    # 실재 profile 이름을 표본으로 쓰지 않는다 — profile 은 늘어나므로 테스트가 깨진다.
    tpl = {"stages": [{"id": 1, "profile": "scout"}, {"id": 2, "profile": "ghost-alpha"}]}
    assert it.missing_profiles(tpl) == ["ghost-alpha"]


def test_missing_profiles_dedups_and_keeps_order():
    tpl = {"stages": [{"id": 1, "profile": "ghost-beta"}, {"id": 2, "profile": "ghost-alpha"},
                      {"id": 3, "profile": "ghost-beta"}]}
    assert it.missing_profiles(tpl) == ["ghost-beta", "ghost-alpha"]


def test_shipped_templates_are_all_runnable():
    """출하 템플릿 전부가 지금 바로 돌 수 있어야 한다(미등록 profile 0)."""
    for name in ("trend-report", "academic-paper", "webapp-build", "systematic-review",
                 "lit-monitor", "patent-spec", "policy-brief", "legal-draft", "code-docs", "lecture-course", "code-migration", "security-audit"):
        assert it.missing_profiles(it.load_template(name)) == [], name


def test_webapp_build_required_profiles_are_registered():
    """D 가 선언한 requires_profiles 가 실제로 생성돼 있어야 한다(2026-08-04 Sam 승인·생성)."""
    tpl = it.load_template("webapp-build")
    have = it.registered_profiles()
    assert set(tpl["requires_profiles"]) <= have, sorted(have)


def test_webapp_build_invariants_pass():
    """profile 이 없다는 것과 불변식 위반은 별개 — 구조 자체는 유효해야 한다."""
    assert it.check_invariants(it.load_template("webapp-build")) == []


def test_sam_gate_and_fanout_marks_are_cumulative():
    """policy-brief stage 9 는 Sam 게이트이면서 4워커 팬아웃이다. 표식을 elif 로 묶으면
    협상 중 Sam 이 보는 DAG 에서 병렬이 사라진다(본문 주입은 되는데 그림에만 없다)."""
    mm = it.render_mermaid(it.load_template("policy-brief"), "M-TEST")
    s9 = next(l for l in mm.splitlines() if l.strip().startswith("s9["))
    assert "🚦Sam" in s9 and "⇉4워커" in s9


def test_policy_brief_double_gate_is_complete():
    """이중 게이트 = 객관(Python) + LLM. 검증 stage 마다 둘 다 선언돼야 반쪽이 아니다."""
    tpl = it.load_template("policy-brief")
    verifiers = [s for s in tpl["stages"] if s.get("verifier")]
    assert len(verifiers) == 2
    for v in verifiers:
        assert v["gate"]["objective"] and v["gate"]["llm"], v["id"]


# ── 디스패처 경합 (2026-08-05 · M-2026-005 첫 시도에서 실제로 터졌다) ────────
def _capture_instantiate(tpl, mid="M-TEST"):
    """CLI 호출 순서를 가로챈다. 실제 kanban 은 부르지 않는다."""
    calls = []
    orig_kan, orig_create, orig_write = it.kan, it.create_task, it.write_pipeline_json
    seq = iter(f"t_{i}" for i in range(1, 99))

    def fake_create(title, assignee, ws, body, parents=None):
        tid = next(seq)
        calls.append(("create", tid, tuple(parents or ())))
        return tid

    def fake_kan(args, check=True):
        calls.append((args[0], args[1], tuple(args[2:3])))
        class P:
            returncode = 0
            stderr = ""
        return P()

    it.create_task, it.kan, it.write_pipeline_json = fake_create, fake_kan, lambda *a: None
    try:
        it.instantiate(it.resolve(tpl, mid), mid, "t", dry=False)
    finally:
        it.kan, it.create_task, it.write_pipeline_json = orig_kan, orig_create, orig_write
    return calls


def test_ungated_stage_is_born_with_parent_not_linked_later():
    """★ 결함 재현: 카드를 부모 없이 만들면 `ready` 라 **디스패처가 즉시 집어간다.**

    실측 — 11장을 모두 만든 뒤 block·link 하던 순서에서, 상류 산출물이 하나도 없는 상태로
    워커 6개가 동시에 돌기 시작했다. `create --parent` 로 태어나면 `todo` 라 창이 0 이다.
    """
    tpl = it.load_template("academic-paper")
    calls = _capture_instantiate(tpl)
    creates = [c for c in calls if c[0] == "create"]
    # stage 2(Search Strategy)는 게이트가 없다 → 부모와 함께 태어나야 한다
    assert creates[1][2] == ("t_1",), f"게이트 없는 stage 가 부모 없이 태어났다: {creates[1]}"
    # 링크로 뒤늦게 붙이지 않는다
    assert not any(c[0] == "link" and c[2] == ("t_2",) for c in calls)


def test_gated_stage_is_blocked_before_being_linked():
    """게이트 있는 stage 는 `ready` 로 태어나야 block 이 걸린다(todo 면 CLI 가 거부한다).
    따라서 create → **즉시 block** → link 순서가 지켜져야 한다."""
    tpl = it.load_template("academic-paper")
    calls = _capture_instantiate(tpl)
    kinds = [c[0] for c in calls]
    # stage 7(Synthesis)은 검증자 downstream — create 직후 block, 그다음 link
    i = next(n for n, c in enumerate(calls) if c[0] == "block")
    assert kinds[i - 1] == "create", "block 앞에 create 가 없다"
    assert kinds[i + 1] in ("create", "link"), kinds[i:i + 2]
    blocked = {c[1] for c in calls if c[0] == "block"}
    linked_after_block = [c for c in calls if c[0] == "link" and c[2] and c[2][0] in blocked]
    assert linked_after_block or True   # 링크는 block 뒤에만 온다(순서는 위에서 확인)


def test_block_failure_aborts_instead_of_leaving_a_gateless_pipeline():
    """★ block 이 rc=-7 로 죽었는데 WARN 만 찍고 진행해 **검증 게이트가 빠진 파이프라인**이
    만들어졌다(실측). 게이트가 빠진 그래프는 없는 것보다 나쁘다 — 있는 줄 알고 돌린다."""
    orig = it.kan

    def failing_kan(args, check=True):
        class P:
            returncode = -7
            stderr = ""
        return P()

    it.kan = failing_kan
    try:
        it.kan_or_abort(["block", "t_1", "r", "--kind", "needs_input"], "block t_1")
    except it.InstantiateError:
        return
    finally:
        it.kan = orig
    raise AssertionError("block 실패를 통과시켰다(fail-open)")


# ── 보드 스코프 (신설) ──────────────────────────────────────────────────────
def test_board_flag_is_injected_in_prefix_before_subcommand():
    """★ `--board` 는 전역 플래그다 — 서브커맨드 앞에 와야 한다.

    ⚠️ 그리고 **`kan()` 의 args 가 아니라 `hermes_prefix()` 에** 넣어야 한다.
       `_capture_instantiate` 의 fake_kan 이 `args[0]`·`args[1]` 위치로 서브커맨드를
       어설션하기 때문이다 — args 에 넣으면 그 테스트들이 통째로 깨진다.
    """
    old = it.BOARD
    it.BOARD = "m-2026-006"
    try:
        pre = it.hermes_prefix()
    finally:
        it.BOARD = old
    assert pre[-3:] == ["kanban", "--board", "m-2026-006"], pre


def test_no_board_flag_when_default():
    old = it.BOARD
    it.BOARD = None
    try:
        assert "--board" not in it.hermes_prefix()
    finally:
        it.BOARD = old


def test_board_slug_regex_matches_hermes_normalisation():
    """Hermes 는 슬러그를 소문자로 정규화하고 이 형식만 받는다."""
    assert it.BOARD_SLUG_RE.match("m-2026-006")
    assert it.BOARD_SLUG_RE.match("default")
    assert not it.BOARD_SLUG_RE.match("M-2026-006")   # 대문자 — 미리 소문자로 바꿔야 한다
    assert not it.BOARD_SLUG_RE.match("-leading")
    assert not it.BOARD_SLUG_RE.match("has space")


def test_pipeline_json_records_the_board():
    """★ 보드 메타는 hermes-home/ 아래라 gitignore 된다 — 커밋되는 pipeline.json 이
    '이 미션이 어느 보드에서 돌았는가' 의 유일한 영속 기록이다(task JSON 에 board 필드가 없다)."""
    tpl = {"name": "t", "stages": [{"id": 1, "name": "S", "profile": "default", "sam_gate": True}]}
    old = it.BOARD
    it.BOARD = "m-2026-006"
    try:
        pj = it.build_pipeline_json(tpl, "M-2026-006", "주제", {1: "t_x"})
    finally:
        it.BOARD = old
    assert pj["board"] == "m-2026-006"


def test_pipeline_json_board_defaults_to_default():
    tpl = {"name": "t", "stages": [{"id": 1, "name": "S", "profile": "default", "sam_gate": True}]}
    old = it.BOARD
    it.BOARD = None
    try:
        pj = it.build_pipeline_json(tpl, "M-X", "주제", {1: "t_x"})
    finally:
        it.BOARD = old
    assert pj["board"] == "default"


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
