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

## 4.1 실행에서 발견한 인프라 제약 (검증됨 · 재현 시 필독)
1호 미션(M-2026-001) 실제 실행에서 드러난 제약과 대응:
- **워커 파일 쓰기는 `HERMES_WRITE_SAFE_ROOT`(=`/opt/data`) 내부로만 허용.** repo 마운트(`/work/company`)에 직접 쓰면 `Write denied`. → 공유 워크스페이스를 `dir:/opt/data/workspace/<mission>`로 두고, **Deliver(Solomon)가 repo `reports/`로 복사·커밋**(설계 정합).
- **네이티브 `web`/`browser` 도구 미프로비저닝**(검색 API 키 없음·Chrome 없음). 단 **네트워크·egress는 정상**(HTTPS `curl` 200). → scout 브리프에서 `terminal`+`curl`(HTTPS: arXiv API·공식 블로그) 사용을 명시. full 버전은 web-search API 키(비용, Sam 승인) 검토.
- **Deliver 카드를 `default`(Solomon)에 할당 + ready 상태로 두면 자율 실행되어 rerun 카드를 만들 수 있음.** → Deliver는 writer 완료 전까지 **`block --kind needs_input` 유지**. (Solomon이 중복을 스스로 SUPERSEDED 처리해 무해했으나, 게이트 유지가 정석.)
- **결과:** scout 13편 수집 → reader 13 분석 → writer `report.md`(출처13·불확실성/상충 명시) 완주. 산출물 `reports/M-2026-001/`.

## 4.2 프로덕션화 개선 (2026-08-02, §4.1 제약 해소)
슬라이스 완주 후 Sam 지시로 인프라를 정비. `docker-compose.yml` + force-recreate로 배치:
- **write-safe-root = 마운트 볼륨과 일치**: `HERMES_WRITE_SAFE_ROOT=/opt/data:/work/company:/work/llm-wiki`. 다중경로 지원(`file_safety.py`). → 워커가 회사 repo(모든 미션 유형·디렉터리)·llm-wiki에 **직접쓰기**, **복사 근본 제거**. 안전망=git+Solomon 게이트+태스크 워크스페이스 스코핑. 미션 워크스페이스는 `dir:/work/company/reports/<mission>` 관례.
- **Tavily 웹 검색 적용**: `web.backend=tavily` 자동, `check_web_api_key=True`. **검증**: Tavily API 직접호출 + default·scout 프로필이 **컷오프 이후 쿼리를 web_search로 실검색**(curl/browser 금지 상태에서 실제 결과 반환) ✅.
  - ⚠️ **핵심 함정(해결됨, 재현 필독)**: `check_web_api_key`→`get_provider_env`는 `os.environ` → **프로필 홈 `.env`** 순으로 키를 찾는다. `TAVILY_API_KEY`를 `hermes-home/.env`에만 두면 **default 프로필만** web 활성; named 프로필(scout/reader/writer)은 자기 `.env`(빈 값)를 봐서 web 도구가 꺼진다. → **키를 프로세스 env에 노출**해야 모든 프로필이 사용: repo `.env`(compose `env_file`, gitignore)에 `TAVILY_API_KEY` 추가 → force-recreate. (초기 "scout가 web 못 씀"은 luna 탓이 아니라 이 스코프 문제였음.)
- **모델 배치(품질우선, GPT-5.6, 전부 openai-codex OAuth 서빙 확인)**:
  | 프로필 | 모델 | 근거 |
  |---|---|---|
  | **scout** | `gpt-5.6-terra` | 도구(web_search·fetch·write) 집약 → 신뢰성 위해 Terra (Sam 결정). 근본원인은 키 스코프였으므로 비용 원하면 Luna 복귀도 가능. |
  | reader·writer·**Solomon(default)**·(추후)synthesizer·curator | `gpt-5.6-terra` | GPT-5.5급·절반가·프로덕션 표준 |
  | (추후)fact-checker·reviewer | `gpt-5.6-sol` | 최심층 추론=독립검증 |
  - 설정: `hermes-home/config.yaml`(Solomon) + `profiles/<name>/config.yaml`. 버전관리 소스=`profiles-src/`.

## 4.3 full 11단계 실행 결과 (M-2026-002, 2026-08-02~03)
2호 미션 "AI 에이전트 평가·신뢰성·안전성 동향"으로 full 11단계를 완주하며 두 핵심 원리를 실증.
- **프로필 8종**: default(Solomon)·scout·reader·writer·synthesizer·curator=terra, fact-checker·reviewer=sol.
- **작성자≠검증자 (실증)**: Reviewer(≠Writer)가 report를 `수정요청`으로 반려 → 8R Writer 수정 → 9R 반려(검증표 불일치 지적) → **6R Fact-Checker가 verify 표 근본수정**(S11 재인용→미검증, S14 정정) → 9R2 **승인**. 표면이 아닌 ground-truth 정합까지 강제됨.
- **복리 (실증)**: llm-wiki 재사용 **7/17 = 41.2%**(M-2026-001 대비 0→41%). wiki 자동갱신(concepts +2, reflections/m-2026-002, index 재사용률 추적).
- **정직성**: 검증 32건 = 확인9·상충1·**미검증22**(주제가 제공자 자기보고 다수 — 숨기지 않음).
- 산출물: `reports/M-2026-002/`(report + raw/analysis/verify/synthesis/review 감사추적), llm-wiki repo.

### 발견한 개선점 (다음 반영)
1. **반려 게이트 미강제**: 9→10 링크를 무조건 걸어, Reviewer `수정요청`인데도 stage 10(wiki)이 진행됨. → 검증 task 판정이 fail이면 산출물 task를 자동 `block`으로 되돌리는 게이팅 필요(수동 revision 카드로 우회함).
2. **Scoping 자율분해 충돌**: `default`(Solomon) Scoping 워커가 스스로 파이프라인을 분해해 수동 11카드와 충돌 → 중복 archive. → Scoping은 Solomon 분해에 맡기거나, Scoping 완료 후 하위 생성.
3. ~~**Slack 아웃바운드 실패**: 다중 force-recreate 후 `hermes send`가 빈 오류로 실패(status는 configured).~~ → **[해소 2026-08-03] 오진 정정**: 실제 근본원인은 force-recreate가 아니라 **호스트 네트워크가 slack.com에 도달 못함**(DNS는 해석되나 TCP443 타임아웃, 컨테이너·호스트 모두 HTTPS 000). 와이파이 변경으로 slack.com 200 회복 → 게이트웨이 Socket Mode 자가 재연결(신규 세션 수립, disconnect 루프 소멸) → 아웃바운드 정상. 토큰(봇 `auth.test` ok·앱 `apps.connections.open` ok)·홈채널ID(`C0BM8FK3RTM`)는 모두 정상이었음.

#### Slack 이상 진단 runbook (재발 시)
증상: `hermes send` 빈/실패 오류 또는 로그의 `Socket Mode unhealthy (transport disconnected); reconnecting`(빈 세션 `()` 반복). `hermes status`의 `Slack ✓ configured`는 **토큰 존재만** 뜻하므로 정상 판정으로 오해 금지.
1. **네트워크 도달성부터(1순위)**: `docker exec hermes-solomon curl -sS --max-time 8 https://slack.com/api/auth.test` — 타임아웃/000이면 **네트워크 문제**(와이파이/기관망/방화벽). 호스트에서도 `curl https://slack.com` 확인. 기관망(KISTI 등)이 Slack egress를 막을 수 있음.
2. **토큰·Socket Mode 실측**(네트워크 OK인데도 실패 시): 봇=`auth.test`(Authorization: Bearer $SLACK_BOT_TOKEN), 앱=`POST apps.connections.open`(Bearer $SLACK_APP_TOKEN). `ok:false`면 해당 토큰 재발급/스코프(`connections:write`) 또는 Slack 앱 Socket Mode 토글 확인.
3. **중복 Socket 연결**: 같은 App-Level Token을 쓰는 인스턴스가 둘 이상이면 disconnect 루프. `docker ps -a`로 확인(현 시점 타 프로젝트 `ainc-hermes`·`hermes`는 Slack 토큰 없어 무관).
4. **복구는 down→up**: 네트워크 회복 후 게이트웨이가 15초 주기로 자가 재연결하나, 즉시 원하면 `docker compose down && docker compose up -d`(force-recreate 반복 대신 소켓 완전 정리).
5. 스코프: 봇토큰이 `channels:read` 미보유면 `conversations.info`/`conversations.list`가 `missing_scope`로 실패(조회만 막힘, 전송 `chat:write`엔 무관). **[2026-08-03 해소]** Slack 앱 OAuth 페이지에 스코프를 추가만 하면 기존 토큰엔 반영 안 됨 — **Reinstall to Workspace**를 눌러야 토큰에 반영(이 앱은 재설치 시 토큰 값 불변·스코프만 확장돼 `.env` 교체 불필요했음). 현 봇토큰 스코프에 `channels:read` 등 포함. 봇 소속 채널: `C0BM8FK3RTM`=**#mission-log**(=`SLACK_HOME_CHANNEL`, bare 전송 목적지)·`C0BN935M0MN`=#ceo-office·`C0BN936JUM6`=#approvals.

## 5. full 11단계 확장 백로그 (슬라이스 완주 후)
- profile 추가: `fact-checker`(6, ≠reader) · `synthesizer`(7) · `reviewer`(9, ≠writer) · `curator`(4·10).
- Skill: **PRISMA식 체계적 문헌조사 + 근거등급** · **karpathy-llm-wiki**(ingest/query/lint).
- Kanban: 5노드 → 11노드로 확장, 6·9는 `kanban swarm`으로 검증자 분리.
- Wiki: llm-wiki repo에 raw→wiki→reflection 반영 + index/log + Lint 게이트.
- 성장 지표: 소요시간·재작업률·Wiki 재사용 비율(1호=0 기준선) 수집.
