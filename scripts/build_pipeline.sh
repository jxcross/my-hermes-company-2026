#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────
# ⚠️ DEPRECATED (2026-08-03) — scripts/instantiate_template.py 로 대체됨.
#   하드코딩 11단계 대신 templates/trend-report.yaml 을 읽는 결정적 번역기를 쓴다.
#   또한 이 스크립트는 잠재 결함(Deliver Sam 게이트가 todo 상태라 block 실패,
#   generic --initial-status blocked 의 auto-promote 불안정)을 갖고 있다.
#   신규 미션: python3 scripts/instantiate_template.py trend-report <MID> --topic "..."
#   협상 미리보기: ... --dry-run --render mermaid
# 아래는 참고용 원본. 새 미션에 사용하지 말 것.
# ─────────────────────────────────────────────────────────────────────────
# 게이트 내장 11단계 미션 파이프라인 인스턴스화
#
# docs/04 파이프라인 표를 그대로 카드로 만들되, "9→10 무조건 링크" 근본원인을
# 제거한다: 검증자(6·9)의 즉시 downstream(7·10)을 `blocked`로 시작해, 게이트키퍼
# (scripts/gate_keeper.py)가 검증 PASS 시에만 unblock 하도록 한다.
#   - 검증 게이트 : 6(fact-checker)→7(synthesizer) · 9(reviewer)→10(curator)
#   - Sam 게이트  : 1 Scoping · 11 Deliver (block --kind needs_input)
#
# 사용:
#   scripts/build_pipeline.sh <MISSION_ID> ["미션 제목/주제"]
#   예) scripts/build_pipeline.sh M-2026-003 "온디바이스 LLM 추론 최적화 동향"
#
# 컨테이너 내부의 hermes CLI 로 실행된다(호스트에서 호출 시 docker exec 래핑).
# ─────────────────────────────────────────────────────────────────────────
set -euo pipefail

MID="${1:?사용법: build_pipeline.sh <MISSION_ID> [\"주제\"]}"
TOPIC="${2:-$MID 미션}"
WS="dir:/work/company/reports/${MID}"

# 컨테이너 안이면 hermes 직접, 밖이면 docker exec 로.
if command -v hermes >/dev/null 2>&1; then
  K() { hermes kanban "$@"; }
else
  K() { docker exec hermes-solomon hermes kanban "$@"; }
fi

# create → task id 추출(--json)
mk() {  # mk "<title>" <assignee> [extra args...]
  local title="$1" assignee="$2"; shift 2
  K create "$title" --assignee "$assignee" --workspace "$WS" --json "$@" \
    | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('id') or d.get('task',{}).get('id'))"
}

echo "▶ 미션 ${MID} 파이프라인 생성: ${TOPIC}"

t1=$(mk "${MID} · 1 Scoping"            default     --body "${TOPIC} — 미션 스펙(목표·완료조건·제약·N)")
t2=$(mk "${MID} · 2 Search Strategy"    scout       --body "검색식·소스 목록·기간")
t3=$(mk "${MID} · 3 Collection"         scout       --body "raw/ 원자료+메타(URL·수집일·발행일)")
t4=$(mk "${MID} · 4 Dedup·Relevance"    curator     --body "중복 제거·관련성 선별")
t5=$(mk "${MID} · 5 Deep Analysis"      reader      --body "자료별 주장/근거 분리 분석")
t6=$(mk "${MID} · 6 Cross-Verify"       fact-checker --body "핵심 주장 독립출처 교차검증. 끝에 VERDICT: PASS|FAIL")
t7=$(mk "${MID} · 7 Synthesis"          synthesizer --body "기술 분류·성숙도·적용 후보" --initial-status blocked)
t8=$(mk "${MID} · 8 Report Draft"       writer      --body "출처 포함 Markdown 보고서")
t9=$(mk "${MID} · 9 Independent Review" reviewer    --body "완료조건 대비 독립 검토. 끝에 VERDICT: PASS|FAIL")
t10=$(mk "${MID} · 10 Wiki Update"      curator     --body "raw→wiki 반영 + reflection" --initial-status blocked)
t11=$(mk "${MID} · 11 Deliver"          default     --body "Slack 요약 + Git 커밋 링크")

echo "  카드: 1=$t1 2=$t2 3=$t3 4=$t4 5=$t5 6=$t6 7=$t7 8=$t8 9=$t9 10=$t10 11=$t11"

# 순차 링크(체인). 게이트 엣지(6→7, 9→10)도 링크는 유지하되 downstream 이 blocked 라
# 게이트키퍼 unblock 전까지 실행되지 않는다.
K link "$t1" "$t2";  K link "$t2" "$t3";  K link "$t3" "$t4";  K link "$t4" "$t5"
K link "$t5" "$t6";  K link "$t6" "$t7";  K link "$t7" "$t8";  K link "$t8" "$t9"
K link "$t9" "$t10"; K link "$t10" "$t11"

# Sam 승인 게이트(1·11)
K block "$t1"  "Sam 승인 대기: 미션 스펙"       --kind needs_input
K block "$t11" "Sam 승인 대기: 외부 공개(Deliver)" --kind needs_input

echo "✔ 완료. 검증 게이트: 6→7(blocked) · 9→10(blocked) = 게이트키퍼가 PASS 시 unblock."
echo "  Scoping 승인 후:  hermes kanban unblock $t1"
