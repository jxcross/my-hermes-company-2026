# 15. ChatGPT(codex) 계정 추가 런북

> **목적**: Hermes 에 ChatGPT 계정을 **하나 더** 붙인다. 한도가 소진돼도 다른 계정으로 계속 돈다.
> **대상**: 새 PC / 다른 PC 에서 수동으로 하는 사람.
> **소요**: 3~5분.

⚠️ **교체가 아니라 추가다.** Hermes 는 자격을 **풀(pool)** 로 관리한다. 소진된 계정은 자동으로
건너뛰고, 한도가 리셋되면 다시 쓴다. 그래서 기존 계정을 지울 이유가 없다.

---

## 0. 전제

- `hermes-solomon` 컨테이너가 떠 있어야 한다.
  ```bash
  docker compose up -d
  docker compose ps          # hermes-solomon 이 Up
  ```
- 추가할 ChatGPT 계정의 로그인 정보(브라우저에서 로그인할 수 있어야 한다).

---

## 1. 브라우저 준비 — **여기가 가장 중요하다**

- 브라우저에서 **추가할 새 계정으로 먼저 로그인**해 둔다.
- 또는 **시크릿 창**을 열어 둔다.

⚠️⚠️ **기존 계정으로 로그인된 상태면 승인이 그 계정에 묶인다.** 그러면 `hermes auth list` 에는
2개로 보이는데 **둘 다 같은 계정**이라 한도가 소진되면 같이 죽는다. 목록만 보고는 알 수 없다
(→ 5번에서 실제로 갈라내는 방법을 쓴다).

---

## 2. 백업

```bash
cp -p hermes-home/auth.json hermes-home/auth.json.bak.$(date +%Y%m%d_%H%M%S)
```

⚠️ OAuth 흐름이 잘못되면 기존 자격을 잃을 수 있다. 백업은 되돌릴 유일한 수단이다.

---

## 3. 추가 명령

```bash
docker exec -it hermes-solomon hermes auth add openai-codex --type oauth --label account2 --no-browser
```

- **`-it` 는 필수다** — 대화형이라 없으면 입력이 전달되지 않는다.
- `--label` 은 목록에 표시될 이름. 아무거나 좋다(`account2`, `personal`, …).
- `--no-browser` — 컨테이너에는 브라우저가 없다. URL 을 직접 열 것이므로 명시한다.

⚠️ **`hermes setup` 이 아니다.** 그건 모델·게이트웨이 마법사라
[`scripts/set_backend.py`](../scripts/set_backend.py) 가 관리하는 배치표와 충돌한다.

---

## 4. 승인 (device code 흐름)

- 화면에 **URL 과 코드**가 표시된다.
- 그 URL 을 **1번에서 준비한 브라우저 창**에 붙여넣고, 코드를 입력해 승인한다.
- 승인되면 명령이 스스로 끝난다.

> 💡 device code 방식이라 **localhost 콜백이 필요 없다** — 컨테이너 안에서 그대로 된다.
> 브라우저가 다른 기기에 있어도 된다.

---

## 5. 확인

### 5-a. 목록

```bash
docker exec hermes-solomon hermes auth list
```

기대 출력:

```
openai-codex (2 credentials):
  #1  device_code          oauth   device_code
  #2  account2             oauth   device_code ←
```

- `(2 credentials)` 로 늘어야 한다.
- `←` 가 지금 쓰이는 자격이다.
- 소진된 자격에는 `rate-limited usage_limit_reached (429) (2d 15h left)` 가 붙는다.

### 5-b. **정말 다른 계정인지** 갈라낸다 (1번의 함정 검증)

목록만으로는 같은 계정을 두 번 넣었는지 알 수 없다. 토큰(JWT)의 계정 식별자를 대조한다:

```bash
python3 - <<'PY'
import json, base64
d = json.load(open('hermes-home/auth.json'))
for i, e in enumerate(d['credential_pool']['openai-codex'], 1):
    p = e['access_token'].split('.')[1]; p += '=' * (-len(p) % 4)
    c = json.loads(base64.urlsafe_b64decode(p))
    # ⚠️ 계정 클레임은 최상위가 아니라 이 네임스페이스 안에 있다.
    #    c.get('chatgpt_account_id') 로 꺼내면 전부 None 이라 검증이 무의미해진다.
    a = c.get('https://api.openai.com/auth') or {}
    print(f"#{i} {e.get('label'):12} account={a.get('chatgpt_account_id')} "
          f"plan={a.get('chatgpt_plan_type')}")
PY
```

출력 예:

```
#1 device_code  account=c9b5b8d8-46da-4b5c-b378-c07ec6a504fb plan=team
#2 account2     account=59559fa2-6da6-422f-8f75-296e486b9ea8 plan=plus
```

⚠️ **`account=` 값이 서로 달라야 한다.** 같으면 1번의 함정에 빠진 것이다 →
그 항목을 지우고(`hermes auth remove openai-codex <label>`) 브라우저를 정리한 뒤 3번부터 다시.

### 5-c. 이 저장소의 점검 도구

```bash
python3 scripts/usage_report.py --live
```

```
── 자격 풀 ──  openai-codex · 1/2 사용 가능
    ✗ #a934e2 device_code  usage_limit_reached · 리셋 08-09 14:07
    ✓ #e49333 account2  ← 지금 쓰이는 자격
        잔량 주간 0%(리셋 08-13 22:25) · 방금
── 한도 ──
  ✓ 착수 가능 — 사용 가능한 자격 1개
```

`--live` 는 업스트림에 물어 잔량을 갱신한다(§7 참조).

---

## 6. 어느 계정이 쓰이는지 — 선택 규칙

**리스트 순서대로 훑어 쿨다운이 아닌 첫 항목**을 쓴다
(`/opt/hermes/hermes_cli/auth.py:4280` `_pool_codex_access_token`).

| | |
|---|---|
| 선택 기준 | **auth.json 의 리스트 순서** (먼저 추가한 것이 먼저) |
| `priority` 필드 | auth.json 에 있지만 **codex 경로는 읽지 않는다**(Nous 경로만 정렬에 씀) |
| 고르는 명령 | **없다** — `hermes auth` 에 `use`/`select`/`switch` 가 없다 |

특정 계정을 쓰고 싶으면:

| 원하는 것 | 방법 | 대가 |
|---|---|---|
| 순서 바꾸기 | auth.json 의 리스트 순서를 편집 | 수동 · 백업 필수 |
| 한 계정만 쓰기 | `hermes auth remove openai-codex <id\|label\|index>` | 되돌리려면 **OAuth 재승인** |

⛔ **`hermes auth reset openai-codex` 는 쓰지 마라.** 이름과 달리 **전체 자격의 소진 표시를
지운다.** 리스트 앞의 소진된 자격이 즉시 다시 선택돼 요청 하나를 그냥 버린다.

---

## 7. 사용량(잔량)은 어떻게 보나

⚠️ **Hermes 는 잔량을 기록하지 않는다.** codex 응답의 rate-limit 헤더를 읽는 코드가 없고,
`hermes insights` 는 계정별로 가르지 못한다(`--days`·`--source` 뿐).

업스트림은 준다 — `POST /codex/responses` 응답의 `x-codex-*` 헤더:

```
x-codex-plan-type: plus              x-codex-primary-used-percent: 0
x-codex-active-limit: premium        x-codex-primary-window-minutes: 10080   (7일)
x-codex-credits-balance: 0           x-codex-primary-reset-at: 1786627540
```

⚠️⚠️ **400 응답에는 이 헤더가 안 붙는다**(실측 — 없는 모델·스키마 위반 둘 다 0개).
**추론이 실제로 시작돼야** 온다. 즉 **잔량 조회는 공짜가 아니다**(최소 요청 1회).

그래서 [`scripts/usage_report.py`](../scripts/usage_report.py) 는 이렇게 나눈다:

| 명령 | 동작 | 비용 |
|---|---|---|
| `usage_report.py --live` | 업스트림에 묻고 캐시에 기록 | 요청 1회 · 0.6s |
| `usage_report.py --brief` | **캐시만** 읽음(+ `· 12분 전` 나이 표시) | 0 · 47ms |

`.claude/settings.json` 의 훅이 자동으로 보여준다 — SessionStart 는 `--live`(세션당 1회),
Stop 은 캐시. ⚠️ `· 3시간 전` 이 붙어 있으면 **그 숫자는 옛것**이다.
⚠️ `%` 는 정수라 주간 창(7일)에서는 초반에 계속 `0%` 로 보인다.

---

## 8. 보안

- ⛔ **토큰 값을 화면·문서·커밋에 붙여넣지 마라. 이 저장소는 PUBLIC 이다.**
  (`SLACK_BOT_TOKEN` 이 세션 로그에 노출된 이력이 있다 — `CLAUDE.md` 참조.)
- 진단할 때는 값을 **셸 안에서만** 확장한다(작은따옴표):
  ```bash
  docker exec hermes-solomon sh -c 'curl -sS -H "Authorization: Bearer $TOKEN" ...'
  ```
- `hermes-home/` 은 **gitignore** 다. `auth.json` 과 잔량 캐시(`codex_quota.json`)는 커밋되지 않는다.
- 계정 id·플랜 이름은 비밀이 아니다(문서에 적어도 된다). **토큰만** 비밀이다.

---

## 9. PC 마다 다시 해야 한다

`hermes-home/auth.json` 은 **git 에 없다**(로컬 전용). 새 PC 에서는:

1. `docs/05_stage0_setup_guide.md` 의 부트스트랩을 먼저 끝내고
2. 이 문서의 1~5번을 계정 수만큼 반복한다.

---

## 부록 · 문제 해결

| 증상 | 원인 / 조치 |
|---|---|
| 명령이 입력을 안 받는다 | `-it` 를 빠뜨렸다 |
| 목록은 2개인데 둘 다 소진된다 | 같은 계정을 두 번 승인했다 → 5-b 로 확인, `remove` 후 재시도 |
| `usage_report.py` 가 착수 불가라고 한다 | 풀의 **모든** 자격이 소진 상태다. `--live` 로 리셋 시각 확인 |
| 잔량이 계속 `0%` | 정상. 주간 창이라 정수 %가 잘 안 오른다 |
| 잔량이 안 보인다 | 아직 `--live` 를 한 번도 안 돌렸다 |

## 참고

- 배치(모델·백엔드) 전환은 이 문서가 아니라 [`docs/14_local_model_backend.md`](14_local_model_backend.md) 와
  `scripts/set_backend.py` 다. **계정 추가와 배치 전환은 별개다.**
- 근거 코드(컨테이너 내부): `/opt/hermes/hermes_cli/auth.py`
  — `_pool_codex_access_token`(:4280 선택 규칙) · `_sync_codex_pool_entries`(:3521 독립 계정 보호 #39236)
