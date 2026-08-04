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
                 "lit-monitor", "patent-spec", "policy-brief", "legal-draft", "code-docs", "lecture-course", "code-migration"):
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
