# 10. Stage 1 착수 계획 — 얇은 수직 슬라이스로 1호 미션 파이프라인 증명

> 작성일: 2026-08-02 · 상태: 실행 계획(승인됨)
> 관련: [`03_mission_pipeline_and_workflow.md`](./03_mission_pipeline_and_workflow.md) · [`04_mvp_research_trend_report_spec.md`](./04_mvp_research_trend_report_spec.md) · [`05_stage0_setup_guide.md`](./05_stage0_setup_guide.md)

## 0. 왜 이렇게 하나 (목표)
Stage 0 인프라(컨테이너 `hermes-solomon`, `default`=Solomon 프로필 gpt-5.5, Kanban DB, 대시보드 `:9129`, Slack, llm-wiki repo)는 가동 중이다.
Stage 1의 최종 목표는 `docs/04`의 **11단계 파이프라인 완주**지만, 한 번에 다 짓지 않고
**최소 profile로 축소 파이프라인(Scout→Reader→Writer + Solomon 게이트)을 실제 미션 1건에 돌려 "시스템이 실제로 돈다"를 먼저 증명**한다.
증명 후 검증자 분리(Fact-Checker·Reviewer)·Synthesizer·Curator·wiki 게이트를 붙여 full 11단계로 확장한다.

**전제 확인(완료):** Solomon = `default` 프로필(별도 named 프로필 없음). `hermes-home/SOUL.md`·`memories/USER.md` 배포됨 → 역할 정의 정상 로드. Kanban 비어 있음.

## 1. 축소 슬라이스 범위 (5노드)

| # | 단계 | 소유 profile | 산출물 | 게이트 |
|---|------|--------------|--------|--------|
| 1 | Scoping | Solomon(`default`) | 미션 스펙(목표·완료조건·제약·N) | **Sam 승인** = block(needs_input) |
| 2 | Search + Collection | `scout` | `raw/`에 원자료 + 메타(URL·수집일·발행일) | Solomon |
| 3 | Deep Analysis | `reader` | 자료별 주장/근거 분리 분석 | Solomon |
| 4 | Report Draft | `writer` | 출처 포함 Markdown 초안 | Solomon |
| 5 | Deliver | Solomon(`default`) | Slack 요약 + Git 커밋 링크 | **Sam 승인** = block(needs_input) |

> 이 슬라이스는 full 11단계의 부분집합이다. **6 Cross-Verify / 9 Independent Review(작성자≠검증자)** 는 확장 단계에서 추가한다.
> 축소본에서도 **Solomon은 산출물을 직접 생산하지 않고 게이트만** 수행한다(핵심 불변식).

## 2. 실제 Hermes 명령 매핑 (컨테이너 내부에서 실행)

### 2.1 전문 profile 생성 (named)
`--description`은 Kanban decomposer의 역할 기반 라우팅에 쓰이므로 반드시 채운다.
```bash
docker compose exec hermes-solomon hermes profile create scout  \
  --description "웹 검색·자료 수집 전문. 검색식으로 공개 자료를 모아 raw/에 원문+메타(URL·수집일·발행일)로 저장."
docker compose exec hermes-solomon hermes profile create reader \
  --description "논문·문서 심층 분석 전문. 자료별 핵심 주장과 근거를 분리하고 수치·정의를 추출."
docker compose exec hermes-solomon hermes profile create writer \
  --description "보고서 집필 전문. 분석 결과를 출처 링크 포함 Markdown 보고서로 구조화."
```
- 생성 후 배포(둘 다 필요):
  - `cp profiles-src/<name>/SOUL.md   hermes-home/profiles/<name>/SOUL.md` (좁은 역할)
  - `cp profiles-src/<name>/config.yaml hermes-home/profiles/<name>/config.yaml`
- ⚠️ **핵심 함정(검증됨):** named 프로필은 **루트(default) config의 model 블록을 상속하지 않는다.** config.yaml 없이 실행하면 `No inference provider configured` 오류. 각 프로필에 `provider: openai-codex` / `default: gpt-5.5`를 명시해야 한다. 인증(OAuth)은 `hermes auth` pooled 자격으로 계정 단위 공유됨.
- SOUL/config **버전관리 소스**는 repo `profiles-src/<name>/`에 둔다(`solomon-profile/` 관례 따름).
- 도구 스코프는 profile config로 좁힌다(scout=웹/브라우저, reader=파일/PDF/브라우저, writer=파일). 상세는 확장 시 강화.
- **검증(완료):** `scout/reader/writer -z "역할?"` → 각자 gpt-5.5로 응답 + 역할 경계 준수(reader=집필 거부, writer=무출처 주장 거부).

### 2.2 축소 Kanban 파이프라인 (미션=부모, 단계=자식, link=게이트)
```bash
# 미션 부모 카드
docker compose exec hermes-solomon hermes kanban create "M-2026-001 research-trend-report" \
  --body "1호 미션: 지정 주제의 최신 연구·기술 동향 보고서" --created-by default   # → <MID>

# 5개 단계 카드 (assignee = 소유 profile, --parent <MID>)
hermes kanban create "1 Scoping"            --assignee default --parent <MID> --initial-status blocked
hermes kanban create "2 Search+Collection"  --assignee scout   --parent <MID>
hermes kanban create "3 Deep Analysis"      --assignee reader  --parent <MID>
hermes kanban create "4 Report Draft"       --assignee writer  --parent <MID>
hermes kanban create "5 Deliver"            --assignee default --parent <MID>

# 순서·게이트: 부모 done → 자식 ready
hermes kanban link <t1> <t2>; hermes kanban link <t2> <t3>
hermes kanban link <t3> <t4>; hermes kanban link <t4> <t5>

# Sam 승인 게이트(1·5): 사람 입력 대기 → 승인 시 unblock
hermes kanban block <t1> --kind needs_input "Sam 승인 대기: 미션 스펙"
# 승인 후: hermes kanban unblock <t1>
```
- 실행: 디스패처는 gateway에 포함(`hermes gateway start`). 단발 진행은 `hermes kanban dispatch`.
- 상태 알림 → Slack `#mission-log`(gateway watcher). 진행 열람 → 대시보드 `:9129`.

### 2.3 (확장 시) 검증자 분리 = `kanban swarm`
full 11단계의 6·9단계는 네이티브 스웜으로 구현 가능:
```bash
hermes kanban swarm "핵심 주장 교차검증" \
  --worker "fact-checker:주장별 독립출처 대조" \
  --verifier reviewer --synthesizer writer
```
> `swarm` = 병렬 워커 → **verifier** → **synthesizer**. 작성자≠검증자 패턴을 CLI가 직접 제공.

## 3. 미션 실행 (엔드투엔드)
1. Slack `#ceo-office`에서 Sam이 주제 제시(예: "최근 3개월 Agentic AI 동향").
2. Solomon이 1단계 Scoping 스펙 제안 → `#approvals`에서 Sam 승인 → `unblock <t1>`.
3. 파이프라인 구동(scout→reader→writer), 각 단계 산출물은 task_comment + 파일.
4. 산출: `reports/M-2026-001/report.md`(모든 주장에 출처) → Git 커밋 + Slack 요약.
5. Sam이 5단계 Deliver 승인 → 미션 done.

## 4. 완주 판정 (이 슬라이스가 성공이라 볼 조건)
- [ ] Slack 주제 투입 → Solomon이 스펙 제안 → 승인 게이트 2회(1·5) 정상 동작
- [ ] Kanban 5 task 전부 `done`, `#mission-log`에 단계 전이 알림 도착
- [ ] `reports/M-2026-001/report.md` 생성·**출처 포함**·Git 커밋
- [ ] Slack 요약 수신

## 5. full 11단계 확장 백로그 (슬라이스 완주 후)
- profile 추가: `fact-checker`(6, ≠reader) · `synthesizer`(7) · `reviewer`(9, ≠writer) · `curator`(4·10).
- Skill: **PRISMA식 체계적 문헌조사 + 근거등급** · **karpathy-llm-wiki**(ingest/query/lint).
- Kanban: 5노드 → 11노드로 확장, 6·9는 `kanban swarm`으로 검증자 분리.
- Wiki: llm-wiki repo에 raw→wiki→reflection 반영 + index/log + Lint 게이트.
- 성장 지표: 소요시간·재작업률·Wiki 재사용 비율(1호=0 기준선) 수집.
