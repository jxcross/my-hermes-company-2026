#!/usr/bin/env python3
"""
match_template 회귀 테스트
==========================
매처가 틀리는 두 방향을 모두 막는다:
  · **억지로 고른다** — 관계없는 요청에 아무 아키타입이나 '높음' 을 준다
  · **못 고른다**     — 명백한 요청(예: "마이그레이션")을 '낮음' 으로 떨어뜨린다

실행: python3 scripts/tests/test_match_template.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import match_template as mt  # noqa: E402

TPLS = mt.load_templates()


def top(query: str):
    r = mt.rank(query, TPLS)[0]
    return r["name"], r["score"], mt.verdict(r["score"])


def test_templates_load():
    assert len(TPLS) >= 20, len(TPLS)
    assert all(t["name"] and t["maturity"] for t in TPLS)


def test_clear_requests_pick_the_right_archetype():
    cases = {
        "온디바이스 LLM 추론 최적화 동향 조사": "trend-report",
        "이 논문으로 학회 발표 슬라이드 만들어줘": "conference-slides",
        "리뷰어 코멘트에 응답서를 써야 한다": "reviewer-response",
        "특허 출원할 발명 명세서": "patent-spec",
        "우리 코드베이스 API 문서를 만들어줘": "code-docs",
        "보안 취약점 감사를 해줘": "security-audit",
        "데이터셋을 정리해서 배포하고 싶다": "dataset-release",
        "코드를 파이썬 3.13으로 마이그레이션": "code-migration",
        "RAG 시스템 평가 실험": "agent-eval",
        "연구비 제안서 작성": "research-proposal",
    }
    bad = []
    for q, want in cases.items():
        name, sc, v = top(q)
        if name != want or v == "낮음":
            bad.append(f"{q!r} → {name}({sc}, {v}), 기대 {want}")
    assert not bad, "\n".join(bad)


def test_unrelated_request_is_not_forced():
    """★ '낮음' 이 실제로 나와야 한다 — 억지로 고르면 매처가 해로워진다(docs/12 §5)."""
    for q in ("저녁 메뉴 추천해줘", "그냥 뭔가 좀 해줘", "안녕하세요"):
        name, sc, v = top(q)
        assert v == "낮음", f"{q!r} 가 {name}({sc}, {v}) 로 잡혔다"


def test_single_specific_keyword_is_enough_signal():
    """★ 개수 기준이면 '마이그레이션' 한 낱말이 0.16(낮음)으로 떨어졌다 — 가중치 합으로 잰다."""
    name, sc, v = top("마이그레이션")
    assert name == "code-migration" and v != "낮음", (name, sc, v)


def test_maturity_is_weighted_and_missing_defaults_to_draft():
    proven = {"name": "x", "display_name": "동향 보고서", "goal_kr": "", "keywords": ["동향"],
              "maturity": "proven"}
    draft = {**proven, "name": "y", "maturity": "draft"}
    unknown = {**proven, "name": "z", "maturity": ""}
    sp, _ = mt.score("동향", proven)
    sd, _ = mt.score("동향", draft)
    su, _ = mt.score("동향", unknown)
    assert sp > sd, (sp, sd)
    assert abs(su - sd) < 1e-6, "maturity 미선언을 draft 로 보지 않았다"


def test_korean_particles_do_not_break_matching():
    """조사가 붙어도 맞아야 한다 — `\\b` 토큰 경계를 쓰지 않는 이유(docs/13 §5)."""
    t = {"name": "x", "display_name": "", "goal_kr": "", "keywords": ["동향"],
         "maturity": "proven"}
    for q in ("동향을", "동향은", "동향이라", "기술동향"):
        s, m = mt.score(q, t)
        assert m == ["동향"], (q, m)


def test_evidence_is_returned_with_the_score():
    """점수만 주면 Sam 이 판단할 수 없다 — 맞은 낱말을 함께 낸다(docs/12 §5)."""
    r = mt.rank("특허 출원할 발명 명세서", TPLS)[0]
    assert r["matched"], r


def test_manifest_rebuild_is_derived_not_handwritten():
    import json
    import tempfile
    orig = mt.MANIFEST
    mt.MANIFEST = os.path.join(tempfile.mkdtemp(), "manifest.json")
    try:
        mt.rebuild_manifest(TPLS)
        d = json.load(open(mt.MANIFEST, encoding="utf-8"))
        assert d["count"] == len(TPLS)
        assert {t["name"] for t in d["templates"]} == {t["name"] for t in TPLS}
    finally:
        mt.MANIFEST = orig


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
