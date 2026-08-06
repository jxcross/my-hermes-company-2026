# 17. Discord 연결 런북 (Sam 수동 작업)

> **소요 15~20분.** Discord Developer Portal 작업은 사람만 할 수 있다.
> 코드 작업과 **병행 가능**하다 — 먼저 해 두면 완성 즉시 검증할 수 있다.
> 배경·설계는 [`docs/16_discord_parallel_channel.md`](16_discord_parallel_channel.md).

⚠️ **Slack 을 지우는 작업이 아니다.** Discord 를 나란히 붙여 **둘 다** 게시한다.
Slack 이 복구되면 자동으로 다시 산다.

---

## 1. Discord 서버 준비

- Discord 앱 좌측 `+` → **직접 만들기** → 이름(예: `Solomon Company`)
- 이미 **관리자 권한**이 있는 서버가 있으면 그걸 써도 된다(봇 초대에 서버 관리 권한이 필요).

## 2. 애플리케이션 생성

- https://discord.com/developers/applications → **New Application**
- 이름 `Solomon` → 약관 동의 → **Create**

## 3. Application ID 복사

- **General Information** 탭 → **Application ID** 복사 (10번 초대 URL 에 쓴다)
- 비밀이 아니다. ⚠️ **Client Secret 은 필요 없다 — 복사하지 마라.**

## 4. Bot 설정

- 좌측 **Bot** 탭 → (구 UI 면 *Add Bot* → *Yes*)
- Username 을 `Solomon` 으로

## 5. ⭐ Privileged Gateway Intents — **가장 조용한 실패 지점**

같은 **Bot** 탭 하단:

| 항목 | 설정 | 이유 |
|---|---|---|
| **MESSAGE CONTENT INTENT** | ✅ **ON** | **끄면 봇이 메시지 내용을 못 읽는다 — 에러 없이 그냥 침묵한다.** 승인이 영영 감지되지 않는다 |
| SERVER MEMBERS INTENT | ⬜ OFF | 숫자 user ID 만 쓰면 어댑터가 요청하지 않는다 |
| PRESENCE INTENT | ⬜ OFF | 불필요 |

**Save Changes** 를 반드시 누른다.

> 증상이 없는 실패다. 봇은 온라인이고 API 는 200 을 주는데 메시지 `content` 만 빈 문자열로
> 온다. 나중에 §검증 3번에서 실제로 잰다.

## 6. Public Bot 끄기

- 같은 탭 → **PUBLIC BOT** ⬜ **OFF** (아무나 이 봇을 자기 서버에 초대하지 못하게)

## 7. ⭐ 봇 토큰 발급

- **Reset Token** → 확인(2FA 요구될 수 있음) → **토큰이 딱 한 번 표시된다** → 복사
- 저장소 `.env` 에:
  ```
  DISCORD_BOT_TOKEN=<붙여넣기>
  ```

⛔ **이 값을 채팅·문서·커밋에 절대 붙이지 마라. 이 저장소는 PUBLIC 이다.**
놓쳤으면 **Reset Token** 을 다시 눌러 새로 받으면 된다(옛 것은 즉시 무효화).

## 8. OAuth2 Scope

- 좌측 **OAuth2** → **URL Generator** → **SCOPES** 에서 정확히 2개:
  - ✅ `bot`
  - ✅ `applications.commands` — Hermes 는 슬래시 커맨드를 **런타임에 자동 sync** 한다.
    (Slack 과 달리 Discord 는 매니페스트 파일이 없다. 포털에서 할 일은 이게 전부다.)

## 9. Bot Permissions

같은 화면 아래 **BOT PERMISSIONS**:

| 체크 | 권한 | 왜 |
|---|---|---|
| ✅ | View Channels | 채널을 본다 |
| ✅ | Send Messages | 통지·승인요청 게시 |
| ✅ | Read Message History | **승인 폴링의 필수 권한** |
| ✅ | Embed Links | 커밋 링크 미리보기 |
| ✅ | Attach Files | 산출물 첨부 여지 |
| ✅ | Add Reactions | 처리 표식(선택) |
| ✅ | Use Slash Commands | `applications.commands` 의 짝 |
| ✅ | Send Messages in Threads | 스레드 사용 시 |
| ❌ | **Administrator** / Manage Messages / Mention Everyone / Manage Channels | **주지 마라.** 필요 없고 사고 반경만 키운다 |

생성된 URL 의 `permissions=` 가 **`277025508416`** 이면 위 조합과 일치한다.
최소 구성(통지·승인만)은 `68608`.

## 10. 초대

- 화면 맨 아래 **GENERATED URL** 복사 → 브라우저 → 1번 서버 선택 → **승인**
- 서버 멤버 목록에 `Solomon` 이 보이면 성공

## 11. 채널 3개 생성

Slack 과 **같은 이름**으로:

| 채널 | 용도 | `.env` 키 |
|---|---|---|
| `#ceo-office` | Sam ↔ Solomon 대화 | (allowlist 에만) |
| `#mission-log` | 진행 통지 | `DISCORD_HOME_CHANNEL` |
| `#approvals` | 승인 게이트 | `GATE_KEEPER_DISCORD_APPROVALS_CHANNEL` |

비공개 채널로 만들었다면 채널 설정 → 권한 → `Solomon` 역할에
**채널 보기 / 메시지 보내기 / 메시지 기록 보기**가 있는지 확인하라.
(공개 채널이면 자동으로 접근된다 — Slack 의 `/invite` 같은 절차는 없다.)

## 12. ⭐ 개발자 모드 켜기

- 사용자 설정(톱니) → **고급** → **개발자 모드 ON**
- 안 켜면 아래 13·14 의 "ID 복사" 메뉴가 **아예 안 보인다**

## 13. 채널 ID 3개

- 각 채널 이름 **우클릭 → 채널 ID 복사** (19자리 숫자)

## 14. 본인 user ID

- 아무 채널에서 자기 이름/아바타 **우클릭 → 사용자 ID 복사** (19자리 숫자)

## 15. `.env` 채우기

```bash
DISCORD_BOT_TOKEN=<7번>
DISCORD_ALLOWED_USERS=<14번 숫자 ID>
DISCORD_ALLOWED_CHANNELS=<ceo-office>,<mission-log>,<approvals>
DISCORD_HOME_CHANNEL=<mission-log>
GATE_KEEPER_DISCORD_APPROVALS_CHANNEL=<approvals>
GATE_KEEPER_DISCORD=discord:<mission-log>
```

⚠️ **값 뒤에 인라인 주석(`# ...`)을 붙이지 마라** — docker compose 가 값의 일부로 읽는다.
⚠️ **fail-closed**: `DISCORD_ALLOWED_USERS`·`DISCORD_ALLOWED_CHANNELS` 를 비워 두면
Discord 봇은 **모든 메시지를 거부한다**(조용히 — 로그도 안 남는다).
⚠️ **숫자 ID 를 써라.** username 을 쓰면 어댑터가 SERVER MEMBERS INTENT 를 추가로 요구한다.

## 16. ⭐ 툴셋 보정 — **빠뜨리면 Discord 의 Solomon 이 무능해진다**

`hermes-home/config.yaml` 의 `platform_toolsets:` 블록에서 `discord:` 목록을
`slack:` 과 **같은 17종**으로 바꾼다.

```yaml
  discord:            # ← 기본값은 [hermes-discord] 하나뿐이다
    - bfl
    - browser
    - clarify
    - code_execution
    - computer_use
    - cronjob
    - delegation
    - file
    - image_gen
    - memory
    - session_search
    - skills
    - terminal
    - todo
    - tts
    - vision
    - web
```

⚠️ 이 파일은 **gitignore** 다 — **PC 마다 다시 해야 한다.**
✅ `set_backend.py` 는 루트 config 의 `platform_toolsets` 를 건드리지 않으므로
백엔드를 전환해도 이 편집은 날아가지 않는다.

## 17. 재기동

```bash
docker compose up -d --force-recreate hermes-solomon hermes-gatekeeper
```

`env_file` 은 컨테이너 **생성 시점**에 읽힌다 — `restart` 로는 반영되지 않는다.

## 18. 첫 확인

`#ceo-office` 에서 **`@Solomon 안녕`**

- 응답이 오면 5번(intent)·9번(권한)·16번(툴셋)이 모두 통과한 것이다.
- **응답이 없으면 5번(Message Content Intent)을 가장 먼저 의심하라.**

---

## 문제 해결

| 증상 | 원인 |
|---|---|
| 봇이 온라인인데 아무 반응이 없다 | **5번 Intent OFF** (1순위) · 또는 15번 allowlist 미설정 |
| 봇이 오프라인 | 토큰 오류 · 17번 재기동 안 함 |
| `403` | 9번 권한 누락 · 비공개 채널에 역할 권한 없음 |
| `404` | 채널 ID 오타 |
| Solomon 이 파일·터미널을 못 쓴다 | **16번 툴셋 보정 누락** |
| 슬래시 커맨드가 안 뜬다 | 8번 `applications.commands` 누락 → 재초대 |
