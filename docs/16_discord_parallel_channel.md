# 16. Discord 병렬 경로 — 계획

> **왜**: 회사망에서 `slack.com` 이 차단됐다. 실측(2026-08-06):
> `discord.com` **200 (0.06s)** · `slack.com` **타임아웃**.
> **무엇**: Slack 을 **유지한 채** Discord 를 나란히 붙인다(둘 다 항상 게시).
> **Sam 결정(2026-08-06)**: ① 교체·추상화 아님 — **병렬 추가** ② Slack 3채널 그대로 이식
> ③ 템플릿 20종의 게시 대상은 **인스턴스화 시 주입**

---

## 1. 전제 (조사로 확인 · 다시 조사하지 마라)

### Hermes 는 Discord 를 1급으로 지원한다
| | Discord | Slack |
|---|---|---|
| 어댑터 | `plugins/platforms/discord/adapter.py` **10,036줄** | 9,085줄 |
| 필수 env | **`DISCORD_BOT_TOKEN` 하나** | `SLACK_BOT_TOKEN` + `SLACK_APP_TOKEN` |
| 인바운드 | discord.py WebSocket Gateway | slack-bolt Socket Mode |
| 자동 활성 | 토큰 존재만으로 (`gateway/config.py:1867-1871`) | 동일 |
| 아웃바운드 | `hermes send --to discord:<id>` REST v10 직결 | 동일 |
| 메시지 상한 | **2000자** | ~40000자 |

### 우리 코드의 Slack 결합은 얇다
- Web API 호출 지점은 **`gate_keeper.slack_api()` 하나**(`:600-616`), 메서드 2개
  (`conversations.history` · `chat.postMessage`).
- 통지는 `notify()`(`:165-177`)가 `hermes send --to $GATE_KEEPER_SLACK`.
- 템플릿 20종의 Deliver stage body 에 `hermes send --to slack:#mission-log` 가 1회씩.

### ⚠️ 조사가 찾은 함정 둘 — 이것부터 고친다
1. **`platform_toolsets.discord` 가 툴셋 1종**(`hermes-home/config.yaml:152-153`).
   `slack` 은 17종이다. 토큰만 넣으면 `#ceo-office` 의 Solomon 이 file·terminal·delegation
   **없이** 대답한다 — 로그도 안 남는다. `hermes-home/` 은 gitignore 라 **PC 마다 수동**이다.
2. **`approval_poll` 의 조기 `return`**(`:911-912`). Slack history 조회가 실패하면 함수를
   빠져나간다. 플랫폼 루프를 안쪽에 넣고 이 줄을 그대로 두면 **Slack 이 죽어 있을 때
   Discord 승인이 영영 처리되지 않는다** — 그런데 Slack 이 죽은 것이 이 작업의 존재 이유다.
   반드시 `continue` 로 바꾸고 **테스트로 못박는다**.

---

## 2. 설계 원칙

**전송 계층만 새로 만들고 판단 계층은 공유한다.** Slack 과 Discord 는 HTTP 모양만 다르고
승인 판단은 완전히 같다. 그래서 경계를 하나만 둔다 — 응답을 `{id, author, text, bot}`
리스트(오래된→최신)로 **정규화**하는 함수를 플랫폼마다 하나씩.

**Slack 쪽은 시그니처·동작을 바꾸지 않는다**(Sam 지시). `slack_api()`·`parse_approval()`·
`resolve_approval_target()`·`gate_summary()`·`poll_once()` 는 그대로.

---

## 3. 작업 순서 (각 단계마다 테스트 초록)

| # | 작업 | 검증 |
|---|---|---|
| 1 | 테스트 하네스 + **Slack 골든 채집**(현재 출력을 상수로 박는다) | 현 코드 그대로 통과 |
| 2 | 순수 함수: `chunk_message` · `normalize_*_history` · `render_approval_request` · `warn_throttled` | 신규 단위 테스트 |
| 3 | `approval_poll` 을 정규화+`consume_approvals` 로 **리팩터만**(Discord 없음) | 기존 34종 + 골든 동일 |
| 4 | 상태 네임스페이싱 + **마이그레이션** + `approval_seeded` | 구 상태 파일 로드 검증 |
| 5 | `discord_api` + `enabled_platforms` + 플랫폼 루프(**`continue`**) | Slack 다운 시 Discord 동작 |
| 6 | `notify` 다중 대상 + 서킷 브레이커 | 첫 대상 실패 시 둘째 실행 |
| 7 | `<NOTIFY_CMDS>` + `check_invariants` 하드코딩 금지 | `lint_template --all` 20/20 |
| 8 | 템플릿 20종 편집(**파일별로** — 문구가 조금씩 다르다) | 누출 0 · 골든(단일 대상=오늘 문장) |
| 9 | `secret_redaction` Discord 토큰 패턴 + 픽스처 | 정상 PASS + 깨뜨린 FAIL |
| 10 | `.env.example` · `docker-compose.yml` 주석 | — |
| 11 | **Sam 의 수동 작업**(§5) | `#ceo-office` 응답 |
| 12 | `platform_toolsets.discord` 17종 보정 | `@Solomon` 이 도구를 쓴다 |
| 13 | 라이브 검증(§6) | 특히 보안 앵커 · Slack 다운 격리 |

**3단계가 중요하다**: Discord 를 넣기 **전에** Slack 만으로 리팩터를 끝내고 골든으로
무손상을 증명한다. 그래야 이후 실패가 리팩터 탓인지 Discord 탓인지 갈린다.

---

## 4. 핵심 구현 노트

### Discord REST 는 Slack 과 네 군데가 다르다
1. 인증 헤더가 **`Bot <token>`**(`Bearer` 아님)
2. POST 본문이 **JSON**(Slack 은 form-urlencoded)
3. 응답에 `{"ok": true}` 래퍼가 **없다** — GET messages 는 **배열**이 그냥 온다
4. **User-Agent 를 명시**해야 한다(urllib 기본값은 Cloudflare 가 거절할 수 있다 → 403)

⚠️ urllib 은 4xx/5xx 에서 **`HTTPError` 를 raise 한다.** `except Exception` 앞에
`except urllib.error.HTTPError` 를 두지 않으면 **429 재시도가 영영 안 돈다**.

### 2000자 — 자르지 않고 나눈다
`gate_summary()` 는 산출물 실측치를 담아 길다. 자르면 `artifact_inspection` 이 만든 방어
(사람에게 오염되지 않은 정보를 준다)가 무효가 된다.
- 줄 경계 우선, 넘치는 줄만 하드 분할
- 조각마다 `` `— t_xxx (i/N)` `` 표식 · 지시문은 자연히 마지막 조각에
- **전량 성공해야 `posted.add`** (부분 게시를 성공으로 치면 반토막이 영영 고정된다)
- 단, 실패 3회면 **짧은 폴백 1건**을 올리고 소비 — 10초마다 중복이 쏟아지는 것도 막는다

⚠️ **2000 은 UTF-16 코드유닛**이다. `len()` 로 재면 이모지가 많은 요약에서 400 을 받는다.

### 상태 네임스페이싱 — 마이그레이션이 없으면 사고가 난다
`approval_seen` = `{"slack:1754...", "discord:1401..."}` · `approval_posted` 도 동일.

⚠️⚠️ 구 상태 파일은 **접두사 없는 Slack ts** 다. 마이그레이션을 빼면 그것들이 전부
"미확인"이 되고, `seed_approval_baseline` 은 집합이 **비어있지 않아** 재시딩을 건너뛰고,
다음 틱에 history 25건이 통째로 새 메시지로 처리된다 → **Sam 의 과거 `승인` 이 현재
대기 게이트에 소급 적용된다.**
→ `load_state()` 에서 `":" not in e` 인 항목을 `slack:` 으로 승격.
→ 시딩 여부는 **`approval_seeded` 별도 키**로 둔다(항목 유무 추론은 양방향으로 틀린다).

### 이중 unblock 은 불가능하다 (논증)
1. 모듈은 단일 스레드(`:92`), 플랫폼 루프는 순차 → 겹칠 실행 창이 없다.
2. 승인 메시지마다 `pending_sam_gates()` 를 **재조회**한다(`:924-926`). 이 함수는 실제
   `task_status` 를 물어 `blocked` 인 것만 반환한다(`:648`).
3. 첫 unblock 후 그 게이트는 목록에서 사라진다.
4. 따라서 두 번째 승인은 `resolve_approval_target` 에서 "대기 게이트 없음" → 소비만 되고
   `run(["unblock"...])` 에 도달하지 않는다.
5. unblock 이 **실패**했다면 게이트가 `blocked` 로 남아 두 번째 승인이 재시도한다 —
   버그가 아니라 **Discord 를 붙이는 이유 그 자체**다.

### WARN 폭주 + 타임아웃 예산
Slack 이 죽어 있으면 틱마다 최소 2회 WARN → 하루 17,000줄. Discord 실패가 그 소음에 묻힌다.
→ 지수 백오프 스로틀(억제 건수를 **합산해 드러낸다** — 조용해지는 것과 나아지는 것은 다르다)
→ 서킷 브레이커: 연속 3회 실패면 그 플랫폼을 백오프 동안 건너뛴다.
  (`urlopen(timeout=15)`×2 + `notify` `NOTIFY_TIMEOUT=60`×대상수가 10초 틱을 밀어낸다.)

### 템플릿: `<NOTIFY_CMDS>`
`resolve()` 의 `sub()` 가 `body` 에 이미 적용된다(`instantiate_template.py:233`) — 같은 자리에
끼운다. 대상이 **1개면 오늘의 문장과 글자 그대로 같아야 한다**(골든 테스트).
2개면 명령을 **줄로 전개**한다 — "두 번 쳐라"를 모델 추측에 맡기지 않는다.

⚠️ 20개 파일의 앞뒤 문장이 조금씩 다르다. **일괄 sed 금지**.
⚠️ `"Slack 요약에 커버리지 수치를 포함하라"` 의 Slack 은 **내용 지시**다 — 명령과 섞지 마라.
⚠️ `security-audit`·`dataset-release` 의 `"(Slack 도 영구 기록이다)"` 는 의미가 유지돼야 한다.

`check_invariants` 에 **게시 대상 하드코딩 금지**를 불변식으로 추가한다 —
안 그러면 새 템플릿이 다시 `slack:#mission-log` 를 박아도 아무도 못 잡는다(`docs/13 §5`).

---

## 5. Sam 이 직접 해야 하는 일 (Discord Developer Portal)

별도 런북: **[`docs/17_discord_setup_runbook.md`](17_discord_setup_runbook.md)**

요약: 앱 생성 → **Message Content Intent ON**(끄면 봇이 **에러 없이 침묵**한다) →
봇 토큰 → OAuth(`bot` + `applications.commands`) 초대 → 채널 3개 → ID 수집 → `.env`.

---

## 6. 검증 (라이브)

| # | 확인 | 통과 조건 |
|---|---|---|
| 0 | 도달성(호스트·**게이트키퍼 컨테이너** 양쪽) | `200` |
| 1 | `GET /users/@me` | `{"bot":true}` |
| 2 | `GET /channels/<approvals>/messages?limit=1` | `200` + **배열** |
| 3 | ⭐ **Intent 실측** — Sam 이 메시지를 치고 2번 재실행 | `content` 가 **비어있지 않다** |
| 4 | `POST .../messages` | 채널에 표시 |
| 5 | `hermes send --to discord:<id>` / `discord:#name` | 이름 형식은 **미확인 — 실측하라** |
| 6 | `--dry-run --once` | 플랫폼별 `[dry]` 로그 · **채널엔 아무것도 안 올라간다** |
| 7 | 스크래치 미션 실게시 | Discord `#approvals` 도착 · Slack WARN 은 **1줄** |
| 8 | 청킹 실물(2000자 초과 게이트) | N개 순서대로 · 이어붙이면 원문 |
| 9 | 승인 E2E | 10초 내 unblock + `#mission-log` 통지 |
| 10 | ⭐ **보안 앵커** — allowlist 밖 계정이 `승인` | **unblock 안 됨** |
| 11 | 오탐 방지 — `보류`/`반려` | 승인 아님 |
| 12 | 재시작 안전 | baseline 은 최초 1회 · 처리한 승인 재처리 안 함 |
| 13 | ⭐ **Slack 다운 격리** | Slack 불통 상태에서 Discord 승인이 **처리된다** |
| 14 | WARN 소음 | 10분(60틱)에 한 자리 수 |

**"됐다"의 정의**: 0~4 · 6 · 7 · 9 · **10** · 12 · **13** · 회귀 일괄. 10·13 이 빠지면 통과가 아니다 —
각각 보안 앵커와 **이 작업의 존재 이유**를 재는 유일한 단계다.

---

## 7. 알려진 한계

- **이미 만들어진 미션의 카드는 Slack 만 적혀 있다**(M-2026-006·007·008). 플레이스홀더는
  인스턴스화 시점에 본문으로 구워지기 때문이다. 게이트 이벤트 통지는 `notify()` 가 동적이라
  즉시 Discord 로도 가지만, **워커가 직접 치는 Deliver 게시는 안 간다.**
- `discord:#channel-name` 이 standalone 경로에서 해석되는지 **미확인**. 실패하면 숫자 ID 를
  쓰고 그 사실을 문서에 박는다.
- Discord standalone 전송(`hermes send`)에는 **429 재시도가 없다** — 통지는 유실될 수 있다
  (진실은 Kanban 과 로그다). 승인 요청은 우리 `discord_api` 로 직접 쳐서 이를 피한다.
