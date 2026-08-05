# 14. 로컬 모델 백엔드 (Ollama) — 한도에 묶이지 않는 실행 경로

> **한 줄 요약:** `python3 scripts/set_backend.py --backend ollama|codex` 하나로 프로필 11종의
> 추론 백엔드를 통째로 바꾼다. 배치표는 `scripts/set_backend.py` 상단 한 곳에만 있다.

---

## 1. 왜 만들었나

2026-08-05, 실미션 M-2026-005 가 stage 4 에서 멈췄다. 원인은 파이프라인이 아니라
**`openai-codex` 주간 한도 소진**(HTTP 429 · plan=team · 리셋 2026-08-09 14:07)이었다
(`docs/11 §7 ⑦`). 리셋까지 나흘 동안 **파이프라인·게이트 62종·템플릿 20종 어느 것도 실행으로
검증할 수 없었다.** 호스트(M4 Max · 64GB)에는 Ollama 가 이미 돌고 있었다.

여기서 얻은 규율은 하나다 — **추론 백엔드는 갈아끼울 수 있어야 한다.** 한 공급자의 한도가
회사 전체를 세우면 안 된다.

## 2. 배치 — 3티어, 계열 분리

| 티어 | 프로필 | codex | ollama | 원본 | 계열 | tok/s | 로드(64K) |
|---|---|---|---|---|---|---|---|
| 작성자 | `default`(Solomon)·`scout`·`reader`·`curator`·`synthesizer`·`writer` | `gpt-5.6-terra` | **`qwen3.6-64k`** | `qwen3.6:35b` (MoE a3b · 262K) | Qwen | 68 | 24GB |
| 검증자 | `fact-checker`·`reviewer`·`tester` | `gpt-5.6-sol` | **`gemma4-26b-64k`** | `gemma4:26b` (MoE 25.8B · 262K) | Gemma | **96** | 17GB |
| 코더 | `architect`·`developer` | `gpt-5.6-terra` | **`qwen3-coder-64k`** | `qwen3-coder:30b` (MoE · 262K) | Qwen | 89 | 24GB |

**`-64k` 는 원본에 `num_ctx` 를 못박은 파생본이다** — 이유는 §3.1. 원본과 **같은 blob 을
공유**하므로 디스크가 늘지 않는다(실측: `ollama show --modelfile` 의 `FROM` 이 동일 sha256).
없으면 만든다: `python3 scripts/set_backend.py --build-models`.

**작성자≠검증자 불변식을 모델 *계열* 수준까지 지킨다.** 검증자에 작성자와 같은 모델(혹은 같은
계열)을 쓰면 같은 맹점을 공유해 독립검증이 성립하지 않는다. 그래서 검증자만 Qwen 이 아닌
GLM 계열이다. `scripts/tests/test_set_backend.py::test_writer_and_verifier_never_share_a_model`
이 이것을 강제한다 — 배치표를 고치다 이 불변식을 깨면 테스트가 막는다.

**모델 선택 기준(순서대로):**
1. **tool calling 지원** — Hermes 는 모든 동작이 tool call 이다. `tools` capability 가 없는
   모델은 아무것도 못 한다. `ollama show <model>` 의 Capabilities 로 확인하라.
2. **계열 분리** — 작성자와 검증자.
3. **64GB 안에서 상주 가능** — 24GB 모델 + 64K KV 캐시가 상한선이다.
4. 속도. 실측(호스트 · 8K ctx · 100% GPU): `qwen3.6:35b` 89.7 tok/s(로드 11.9s) ·
   `gpt-oss:20b` 93.1 tok/s(로드 4.6s).

## 2.1 배치는 측정으로 정했다 — `scripts/probe_protocol.py`

"더 큰 모델이면 낫지 않을까"는 가설이다. 가설은 잰다. 프로브는 **모델 벤치마크 점수가 아니라
우리 파이프라인이 실제로 요구하는 것**을 재고, Hermes 를 거치지 않고 Ollama `/api/chat` 에
같은 모양의 tool 스키마를 직접 준다(프로필·Kanban 을 끼우면 무엇이 실패했는지가 두 층 아래로
내려가 안 보인다).

| 항목 | 무엇을 보는가 | 파이프라인에서의 의미 |
|---|---|---|
| `arg_fidelity` | 도구 인자를 준 그대로 넣는가 | 관찰된 실패가 정확히 이것(경로를 백틱으로 감쌈) |
| `no_stray` | 시키지 않은 곳에 쓰지 않는가 | 부작용 |
| `must_finish` | 종료 도구를 정확히 1회 부르는가 | 빠뜨린 것이 `protocol violation` 이다 |
| `v_found` | `VERDICT:\s*(PASS\|FAIL)` 이 본문에 있는가 | **게이트키퍼의 실제 기준**(`gate_keeper.py:53`) |
| `v_unambiguous` | PASS·FAIL 이 함께 나오지 않는가 | 첫 매치가 이기므로 섞이면 오판 |
| `v_correct` | 판정 내용이 맞는가 | 반려 게이트의 실질 |
| `v_lastline` | 마지막 줄에 오는가 | 템플릿이 요구("끝에") · 게이트키퍼는 미요구 |

**결과 (2026-08-05 · reps 3~5 · temp 0.2)**

| 모델 | arg_fid | no_stray | finish | v_found | v_unambig | v_correct | v_lastline | tok/s |
|---|---|---|---|---|---|---|---|---|
| **`gemma4:26b`** ✅채택 | 100 | 100 | 100 | 100 | 100 | 100 | **100** | **96** |
| `qwen3.6:35b` ✅채택 | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 68 |
| `qwen3-coder:30b` ✅채택 | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 89 |
| `gemma4:12b` | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 47 |
| `gemma4:31b` | 100 | 100 | 100 | 100 | 100 | 100 | 100 | **11** ❌느림 |
| `glm-4.7-flash` | 100 | 100 | 100 | 100 | 100 | 100 | **0** | 67 |
| `gpt-oss:20b` | 100 | 100 | 100 | — | — | 67 | 67 | 93 |

**⚠️ 이 측정에서 내가 한 번 틀렸고, 그게 이 절의 핵심 교훈이다.**
처음 프로브는 VERDICT 를 **"마지막 줄에 정확히"** 로 쟀고 `glm-4.7-flash` 가 **0%** 로 나왔다.
"검증자로 못 쓴다"고 결론 낼 뻔했다. 그런데 `gate_keeper.py:53` 을 읽어 보니
`VERDICT_RE.search()` — **본문 어디든** 있으면 된다. 실제 기준으로 다시 재니 glm 은 100% 였다.
**게이트를 재기 전에 게이트가 무엇을 읽는지 읽어라.** 잣대를 잘못 잡으면 멀쩡한 후보를
탈락시키고, 반대로 재면 못 쓸 것을 통과시킨다(`docs/13 §5` 의 "동작하는 척하는 게이트"의 거울상).

**왜 `gemma4:26b` 인가**(모두 필요조건을 통과한 뒤의 선택):
1. **엄격 기준까지 100%** — 템플릿이 요구하는 "끝에"까지 지킨다. 게이트키퍼가 지금은
   관대하지만, 관대한 파서에 기대는 것보다 규격을 지키는 모델이 낫다.
2. **가장 빠르다**(96 tok/s) — 측정한 것 중 최고. MoE 25.8B.
3. **가장 작다**(17GB) — 검증자가 작을수록 작성자 모델과의 스왑이 싸다.
4. **계열이 다르다**(Gemma ≠ Qwen) — 작성자≠검증자를 계열 수준까지 유지.

**탈락 사유**: `gemma4:31b` 은 dense 라 **11 tok/s**(실사용 불가) · `gpt-oss:20b` 은 판정
포맷이 3회 중 1회 비었다 · `glm-4.7-flash` 는 기능상 문제없으나 위 4가지에서 gemma4:26b 에
밀린다(**폴백으로 남겨 둔다** — `BASE_MODELS` 에 유지).

**받지 않은 것**: `qwen3-next:80b`(50GB) · `qwen3-coder-next`(52GB)는 **받지 않았다.** 배치
모델 3종이 이미 필요조건에서 만점이라 50GB 를 더 쓸 근거가 없다. `minimax-m2.7`·`glm-5.2` 는
Ollama 에 **`:cloud` 태그뿐**이라 로컬 실행 자체가 안 된다.

⚠️ **이 프로브가 재지 않는 것: 검증의 *깊이*다.** 포맷을 지킨다는 것과 틀린 주장을 잡아낸다는
것은 다르다. 후자는 실미션으로만 알 수 있다.

## 3. config 스키마 — 각 키가 없으면 무엇이 깨지는가

```yaml
model:
  default: "qwen3.6-64k"
  provider: "ollama"                                # → Hermes 내부에서 custom 으로 매핑
  base_url: "http://host.docker.internal:11434/v1"
  api_key: "ollama"
  api_mode: "chat_completions"
  context_length: 65536
  ollama_num_ctx: 65536
  max_tokens: 16384
```

| 키 | 빠지면 | 근거(컨테이너 내부 소스) |
|---|---|---|
| `provider` | `No inference provider configured` (named 프로필은 루트 config 를 상속하지 않는다) | `docs/10 §2.1` |
| `provider` 가 **base_url 과 다른 파일**에 | base_url 이 **버려지고 OpenRouter 로 흘러간다** | `hermes_cli/runtime_provider.py:73` `_config_base_url_trustworthy_for_bare_custom()` |
| `base_url` 의 `/v1` | 로컬 서버가 OpenAI 호환 경로를 못 찾는다 | `hermes_cli/model_setup_flows.py:946` |
| `host.docker.internal` 대신 `localhost` | 컨테이너 자신을 가리켜 연결 실패 | 컨테이너는 bridge 네트워크(`docker-compose.yml`) |
| `api_key` | 클라이언트가 빈 키를 거부한다(Ollama 는 값을 무시한다) | `plugins/model-providers/custom/__init__.py` `env_vars=()` |
| `ollama_num_ctx` | Hermes 가 `/api/show` 로 모델 최대를 읽어 그 값을 요청한다 | `agent/agent_init.py:2631` |
| **`context_length`** | Hermes 의 **압축 임계**가 모델 최대(262144)로 잡힌다 — 실제 서빙 창보다 크면 프롬프트가 조용히 잘린다 | `agent/agent_init.py:2655` |
| `max_tokens` | 기본 65536 이라 **출력이 창을 다 먹는다** | `custom/__init__.py` `default_max_tokens=65536` |

### 3.1 ⚠️ `ollama_num_ctx` 만으로는 창이 안 잡힌다 — 실측

계획 단계에서 `ollama_num_ctx: 65536` 이면 Ollama 가 그 창으로 로드할 것이라고 봤다. **틀렸다.**
`ollama ps` 의 CONTEXT 가 **262144**(모델 최대)로 나왔고, 원인을 좁혀 보니 이렇다:

| 엔드포인트 | 보낸 것 | 로드된 CONTEXT | 메모리 |
|---|---|---|---|
| `/v1/chat/completions` | `options.num_ctx = 8192` | **131072** (무시됨) | **22GB** |
| `/api/chat` | `options.num_ctx = 8192` | **8192** | **5.9GB** |

(llama3.1:8b 로 측정. Hermes 의 `custom` 프로바이더는 `api_mode: chat_completions` = **`/v1`** 로
말한다. `custom/__init__.py` 가 `think` 에 대해 같은 계열의 주의를 이미 적어 놓았다 —
"Ollama 의 `/v1/chat/completions` 는 `extra_body.think` 를 무시한다(ollama#14820)". `options` 도
같은 취급이다.)

**같은 모델이 창 하나로 3.7배의 메모리를 쓴다.** 64GB 에서 이건 그냥 낭비가 아니라 배치 자체를
불가능하게 만든다.

**해법: 창을 서버 쪽에 못박는다.** Modelfile 로 파생 모델을 만든다.

```
FROM qwen3.6:35b
PARAMETER num_ctx 65536
```
```bash
python3 scripts/set_backend.py --build-models     # 없는 것만 만든다
```

파생본은 원본과 **같은 blob 을 참조**하므로 디스크가 늘지 않는다. `PARAMETER num_ctx` 는
서버가 모델을 로드할 때 적용하므로 **어느 엔드포인트로 부르든 유효하다.**

`ollama_num_ctx` 는 config 에 그대로 뒀다 — 무시돼도 해가 없고, Hermes 가 `/api/chat` 이나
프록시 경로를 쓰게 되면 그때는 유효하다. Modelfile 의 `num_ctx` 와 config 의 두 값은
`scripts/set_backend.py` 의 상수 `OLLAMA_NUM_CTX` **하나**에서 나오므로 갈라질 수 없고,
`test_modelfile_pins_the_same_window_as_the_config` 가 그것을 강제한다.

**검증(2026-08-05 실측):** 세 티어 모두 `ollama ps` CONTEXT = **65536**
(qwen3.6-64k 24GB · glm-4.7-flash-64k 22GB · qwen3-coder-64k 24GB).

⚠️ **`context_length` 와 Modelfile 의 `num_ctx` 는 항상 같은 값이어야 한다.** 압축 임계가 실제
서빙 창보다 크면 Hermes 는 넣었다고 믿고 모델은 못 본 상태가 된다 — `docs/11 §7 ⑦` 의
"실패 표면과 근본 원인이 두 층 떨어진다"가 그대로 재현되는 모양이다.

**교훈:** 설정 키가 존재한다는 것은 그 키가 **먹힌다**는 뜻이 아니다. `docs/13 §5` 의
"동작하는 척하는 게이트" 와 같은 계열이다 — **설정을 넣었으면 그것이 실제로 반영됐는지를
바깥에서 관측하라**(여기서는 `ollama ps` 의 CONTEXT 열).

## 4. 전환 절차

```bash
python3 scripts/set_backend.py --show                     # 현재 상태
python3 scripts/set_backend.py --backend ollama --dry-run # 대상 확인
python3 scripts/set_backend.py --build-models             # -64k 파생본 생성(없는 것만)
python3 scripts/set_backend.py --backend ollama           # 적용
docker compose up -d --force-recreate hermes-solomon hermes-gatekeeper
docker exec hermes-solomon hermes profile list            # 모델명 확인
python3 scripts/usage_report.py                           # 로컬 준비 상태(exit 0 이어야 착수 가능)
ollama ps                                                 # ★ CONTEXT 가 65536 인지 확인
```

`--build-models` 는 원본이 없으면 `ollama pull <원본>` 을 안내하고 exit 1 한다. 원본 3종은
`qwen3.6:35b`(24GB) · `glm-4.7-flash`(19GB) · `qwen3-coder:30b`(18GB).

**한도 리셋 후 복귀(2026-08-09 14:07 이후):**
```bash
python3 scripts/usage_report.py --backend codex   # 리셋됐는지 확인
python3 scripts/set_backend.py --backend codex
docker compose up -d --force-recreate hermes-solomon hermes-gatekeeper
```

스크립트가 손대는 파일:
- `profiles-src/<name>/config.yaml` × 10 — **git 소스**(새 PC 부트스트랩의 기준)
- `hermes-home/profiles/<name>/config.yaml` × 10 + `hermes-home/config.yaml` — **라이브**(gitignore)

`model:` **최상위 블록만** 행 단위로 치환한다. `agent:`·`onboarding:`(Hermes 가 스스로 써 넣는다)·
root config 의 `platform_toolsets:`·`personalities:` 는 무손상이다. PyYAML 에 의존하지 않는다 —
호스트 python3 에 PyYAML 이 없고, 이 스크립트는 호스트에서 도는 운영 도구다.

**상태 파일은 없다.** 현재 백엔드는 config 파일 자체를 읽어 판정한다(단일 진실원). 일부만
전환된 상태(`mixed`)는 `--show` 가 exit 1 로 잡는다 — 절반이 조용히 한도를 계속 태우는 사고를
막는다.

## 5. 호스트 Ollama 설정

배치 모델 3종은 64K 창에서 각각 22~24GB 를 쓴다(실측). 두 개가 동시에 올라가면 46GB,
세 개면 70GB 로 **64GB 를 넘는다** — **상주 1개**가 안전하다. 11단계 파이프라인은 순차
실행이고 스테이지 내 병렬은 같은 profile(=같은 모델)의 subagent 팬아웃이므로(`docs/11 §5`)
동시에 두 모델이 필요한 구간이 없다. 단계 전환 시 5~12초 로드 비용만 든다.

```bash
launchctl setenv OLLAMA_MAX_LOADED_MODELS 1
launchctl setenv OLLAMA_KEEP_ALIVE 30m
# 그 뒤 Ollama 재시작(메뉴바 앱 quit → 재실행)
```

⚠️ `launchctl setenv` 는 로그인 세션 단위라 **재부팅하면 사라진다.** 없어도 동작은 하지만
모델 두 개가 동시에 올라가 메모리를 압박하고 느려진다. 재부팅 후 다시 걸어라.

⚠️ Ollama 는 `127.0.0.1:11434` 에만 바인딩돼 있다(`OLLAMA_HOST` 미설정). 그래도 Docker Desktop 이
`host.docker.internal`(192.168.65.254) 로 프록시해 주므로 컨테이너에서 닿는다 — **실측 확인**:
`docker exec hermes-solomon curl http://host.docker.internal:11434/api/version` → HTTP 200.
`docker-compose.yml` 은 손대지 않았다.

## 6. `usage_report.py` 의 백엔드 인식

미션 착수 전 점검(`python3 scripts/usage_report.py`)은 백엔드에 따라 **다른 것을 본다.**

| 백엔드 | 점검 대상 | exit 1 조건 |
|---|---|---|
| `codex` | 워커 로그의 429 `resets_at` | 한도 소진 중 |
| `ollama` | Ollama 서버 도달 + 배치 모델 설치 여부 | 서버 불통 또는 모델 없음 |

로컬로 옮겼는데도 로그의 429 기록 때문에 리셋 시각까지 계속 `exit 1` 이 나면 전환의 의미가
없다. 그래서 로컬 백엔드에서는 codex 한도를 **참고로만 표시**하고 exit code 는 로컬 준비
상태로 정한다. `--backend codex|ollama` 로 강제 지정할 수 있다(복귀 시점 확인용).

로컬 점검도 **LLM 을 호출하지 않는다** — `/api/tags` 는 메타데이터 조회다. "한도를 확인하려고
한도를 쓰면 안 된다"는 원래 규율이 그대로 유지된다.

## 7. 알려진 한계 · 다음

1. **프로토콜 준수는 재서 확인했다(§2.1) — 다만 재현되지 않은 실패가 하나 있다.**
   연결 검증 때 `developer` 가 목표 파일은 정확히 썼지만 **경로를 백틱으로 감싼 채** 엉뚱한
   곳(`/tmp/...`)에도 두 번 더 쓰려 했다(`HERMES_WRITE_SAFE_ROOT` 와 `.json` 문법 검증이 둘 다
   막았다 — 가드레일이 일했다). 그런데 **프로브 3과제 × 5회 반복에서는 재현되지 않았다.**
   즉 드물게 나오는 실패이지 상시 결함이 아니다. 실미션에서 같은 계열의 실패
   (`kanban_complete` 미호출 = `protocol violation`)가 나오면 §2.1 프로브부터 다시 돌려라.
   객관 게이트 62종은 산출물을 보므로 그대로 작동한다.
2. **`reasoning_effort: medium` 은 그대로 뒀다.** custom 프로바이더는 이 값을 top-level
   `reasoning_effort` 로 넘긴다 — 인식하지 못하는 엔드포인트는 무시한다
   (`custom/__init__.py` build_api_kwargs_extras).
3. **Ollama 모델은 codex 사용량 기록에 남지 않는다.** `hermes insights` 의 누적 토큰은 계속
   codex 기준이다. 로컬 사용량 계측은 아직 없다(성장 지표 대시보드 과제와 함께 볼 것).
4. **이미지 생성**(`image_gen.provider: openai-codex`)은 전환 대상이 아니다 — 파이프라인에서
   쓰지 않는다.
