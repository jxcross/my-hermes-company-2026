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

## 2. 배치 — 단일 모델 (2026-08-05 Sam 지시로 통일)

| 티어 | 프로필 | codex | **ollama(현재)** | 원본 |
|---|---|---|---|---|
| 작성자 | `default`(Solomon)·`scout`·`reader`·`curator`·`synthesizer`·`writer` | `gpt-5.6-terra` | **`gemma4-26b-256k`** | `gemma4:26b` |
| 검증자 | `fact-checker`·`reviewer`·`tester` | `gpt-5.6-sol` | **`gemma4-26b-256k`** | `gemma4:26b` |
| 코더 | `architect`·`developer` | `gpt-5.6-terra` | **`gemma4-26b-256k`** | `gemma4:26b` |

### 2.2 ⚠️ 로컬 백엔드는 **작성자≠검증자를 모델 계열 수준에서 포기했다** (Sam 승인 2026-08-05)

Sam 지시로 속도 우선 통일했다. **남는 분리**: profile 경계·SOUL(역할 프롬프트)·객관 게이트
62종(산출물을 기계 판정)·작성 task ≠ 검증 task. **잃는 분리**: 모델 계열 다양성 —
검증자가 작성자와 **같은 맹점을 공유**한다.

이 결정을 조용히 잃지 않도록 `BACKENDS["ollama"]["shared_verifier_model"]` 에 사유를 선언하고,
테스트가 **선언 없는 통일을 FAIL** 시킨다(`test_writer_and_verifier_share_a_model_only_by_
explicit_declaration`). 실미션에서 **검증자가 놓치는 것**을 눈여겨봐야 한다.

`gemma4:26b`(MoE 25.8B · 17GB · 최대 창 262144) 는 무경합 측정에서 프로토콜 전 항목 100%,
프로토콜 벽시계 45초(3회)로 `gemma4:e4b` 와 동률이었고 `gemma4:12b`(97초)보다 2배 빨랐다.
**동률에서 `창 여유`로 갈랐다** — e4b 는 131072 이 천장이다. **2026-08-05 (3) 에 그 여유를
실제로 썼다: 131072 → 262144(26b 의 천장).**

**`-256k` 는 원본에 `num_ctx 262144` 를 못박은 파생본이다** — 창을 왜 서버 쪽에 박는지는
§3.1, **하한이 왜 있는지는 §3.2**(이게 실미션을 멈춰 세운 결함이다).
⚠️ **접미사가 창을 담는다 — 창을 바꾸면 이름을 바꿔라.** `--build-models` 는 존재를
**이름으로만** 판정해서, 이름을 그대로 두면 "이미 있음"을 찍고 서버는 옛 창을 계속 서빙한다. 원본과 **같은 blob 을
공유**하므로 디스크가 늘지 않는다. 없으면 만든다:
`python3 scripts/set_backend.py --build-models`.

**모델 선택 기준(순서대로):**
1. **tool calling 지원** — Hermes 는 모든 동작이 tool call 이다. `tools` capability 가 없는
   모델은 아무것도 못 한다. `ollama show <model>` 의 Capabilities 로 확인하라.
2. **프로토콜 준수** — §2.1 프로브의 구속 항목 100%.
3. **실작업 벽시계** — tok/s 가 아니다(§2.1 의 주의).
4. **창 여유** — §3.2 가 요구하는 `context_length − max_tokens > 64000` 을 만족하고도
   더 올릴 여지가 있는가. `gemma4:e4b`(131072 천장)와 `gemma4:26b`(262144)를 여기서 갈랐다.
5. 메모리. 실측: `gemma4-26b-256k` **17.64GB @262144** · `gemma4-26b-128k` 17.50GB @131072 ·
   `gemma4-e4b-128k` 9.9GB @131072. **26b 는 창을 2배로 해도 메모리가 +0.8% 다**(§3.1 하단).

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

| 모델 | arg_fid | no_stray | finish | v_found | v_unambig | v_correct | v_lastline | tok/s | 프로브 벽시계(3회) |
|---|---|---|---|---|---|---|---|---|---|
| **`gemma4:26b`** ✅채택 | 100 | 100 | 100 | 100 | 100 | 100 | **100** | 96 | **45초** |
| `gemma4:e4b` | 100 | 100 | 100 | 100 | 100 | 100 | 33 | 81 | **45초** |
| `gemma4:12b` | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 47 | 97초 |
| `qwen3.6:35b` | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 68 | – |
| `qwen3-coder:30b` | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 89 | – |
| `gemma4:31b` | 100 | 100 | 100 | 100 | 100 | 100 | 100 | **11** ❌느림 | 288초 |
| `glm-4.7-flash` | 100 | 100 | 100 | 100 | 100 | 100 | **0** | 67 | – |
| `gpt-oss:20b` | 100 | 100 | 100 | — | — | 67 | 67 | 93 | – |

⚠️ **`tok/s` 로 고르지 마라.** `gemma4:e4b` 는 tok/s 가 `gemma4:12b` 보다 훨씬 높은데(81 vs 47)
프로브 벽시계는 45초 대 97초로 **비율이 다르다**. 턴 수·사고량·프롬프트 처리가 더 크게 작용한다.
**벽시계로 골라라.** 그리고 **경합 상태에서 잰 값은 서로 비교할 수 없다** — 미션이 도는 중에
잰 첫 e4b 측정(3회 265초)은 무경합 재측정에서 45초로 바뀌었다.

**⚠️ 이 측정에서 내가 한 번 틀렸고, 그게 이 절의 핵심 교훈이다.**
처음 프로브는 VERDICT 를 **"마지막 줄에 정확히"** 로 쟀고 `glm-4.7-flash` 가 **0%** 로 나왔다.
"검증자로 못 쓴다"고 결론 낼 뻔했다. 그런데 `gate_keeper.py:53` 을 읽어 보니
`VERDICT_RE.search()` — **본문 어디든** 있으면 된다. 실제 기준으로 다시 재니 glm 은 100% 였다.
**게이트를 재기 전에 게이트가 무엇을 읽는지 읽어라.** 잣대를 잘못 잡으면 멀쩡한 후보를
탈락시키고, 반대로 재면 못 쓸 것을 통과시킨다(`docs/13 §5` 의 "동작하는 척하는 게이트"의 거울상).

**왜 `gemma4:26b` 로 통일했나**(모두 필요조건을 통과한 뒤의 선택):
1. **벽시계 최속 동률** — 프로브 45초로 `gemma4:e4b` 와 같고 `gemma4:12b`(97초)의 절반.
   실작업(18.8k 입력)도 61.5초 대 57.2초로 e4b 와 사실상 동률.
2. **동률에서 창 여유로 갈랐다** — 262144 vs e4b 의 131072(천장). §3.2 의 설정에 여유가 있다.
3. **엄격 기준까지 100%** — 템플릿이 요구하는 "끝에"까지 지킨다(e4b 는 33%). 관대한 파서에
   기대는 것보다 규격을 지키는 모델이 낫다.

**탈락 사유**: `gemma4:12b`(Sam 이 처음 지시한 모델)은 dense 라 **벽시계 2배** ·
`gemma4:31b` 은 dense 라 **11 tok/s**(실사용 불가) · `gpt-oss:20b` 은 판정 포맷이 3회 중 1회
비었다 · `gemma4:e4b`·`glm-4.7-flash` 는 기능상 문제없어 **폴백으로 남긴다**(`BASE_MODELS`).

**받지 않은 것**: `qwen3-next:80b`(50GB) · `qwen3-coder-next`(52GB)는 **받지 않았다.** 배치
후보들이 이미 필요조건에서 만점이라 50GB 를 더 쓸 근거가 없다. `minimax-m2.7`·`glm-5.2` 는
Ollama 에 **`:cloud` 태그뿐**이라 로컬 실행 자체가 안 된다.

⚠️ **이 프로브가 재지 않는 것: 검증의 *깊이*다.** 포맷을 지킨다는 것과 틀린 주장을 잡아낸다는
것은 다르다. 후자는 실미션으로만 알 수 있다.

## 3. config 스키마 — 각 키가 없으면 무엇이 깨지는가

```yaml
model:
  default: "gemma4-26b-256k"
  provider: "ollama"                                # → Hermes 내부에서 custom 으로 매핑
  base_url: "http://host.docker.internal:11434/v1"
  api_key: "ollama"
  api_mode: "chat_completions"
  context_length: 262144
  ollama_num_ctx: 262144
  max_tokens: 16384
compression:
  threshold: 0.85       # ⚠️ 프로필에 직접 — 루트에서 상속 안 됨(§3.3)
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

⚠️⚠️ **그런데 이 3.7배는 `llama3.1:8b` 의 숫자다 — 모델 계열을 건너뛰지 않는다(2026-08-05 (3) 실측).**
배치 모델을 131072 → 262144 로 올리면서 메모리가 2배 될 것을 각오했는데, **거의 안 늘었다**:

| 파생본 | 창 | 메모리(`/api/ps` 의 `size`) |
|---|---:|---:|
| `gemma4-26b-128k` | 131072 | 17.50 GB |
| **`gemma4-26b-256k`** | **262144** | **17.64 GB** (+0.14 GB · **+0.8%**) |

창을 2배로 했는데 +0.8% 다. `gemma4` 계열은 대부분의 층이 sliding-window attention 이라
KV 캐시가 선언 창에 비례해 늘지 않는 것으로 보인다 — `llama3.1:8b`(전 층 full attention)에서
관찰한 비례 증가가 **여기엔 적용되지 않는다.**

> **교훈이 두 개다.** ① 위 3.7배를 일반 법칙으로 읽지 마라 — **모델마다 다시 재라.**
> ② 이 측정을 더 일찍 했다면 처음부터 262144 로 갔을 것이고, `docs/11 §7 ⑧` 의 stage 5
> 압축 사고를 겪지 않았을 수도 있다. **메모리가 아까워서 창을 아꼈는데, 아낄 것이 없었다.**

**해법: 창을 서버 쪽에 못박는다.** Modelfile 로 파생 모델을 만든다.

```
FROM gemma4:26b
PARAMETER num_ctx 262144
```
```bash
python3 scripts/set_backend.py --build-models     # 없는 것만 만든다
```

파생본은 원본과 **같은 blob 을 참조**하므로 디스크가 늘지 않는다. `PARAMETER num_ctx` 는
서버가 모델을 로드할 때 적용하므로 **어느 엔드포인트로 부르든 유효하다.**

`ollama_num_ctx` 는 config 에 그대로 뒀다 — 무시돼도 해가 없고, Hermes 가 `/api/chat` 이나
프록시 경로를 쓰게 되면 그때는 유효하다. **배치 모델**의 Modelfile `num_ctx` 와 config 의 두
값은 `scripts/set_backend.py` 의 상수 `OLLAMA_NUM_CTX` **하나**에서 나오므로 갈라질 수 없고,
`test_deployed_models_pin_the_same_window_as_the_config` 가 그것을 강제한다.
⚠️ **폴백은 창을 공유하지 않는다** — `gemma4:e4b` 는 천장이 131072 이라 262144 를 못 준다.
그래서 `BASE_MODELS` 는 모델마다 `num_ctx`·`ceiling` 을 들고 있고,
`test_no_model_is_pinned_above_its_measured_ceiling` 이 천장 초과를 막는다.

**검증(2026-08-05 (3) 실측):** `ollama ps` CONTEXT = **262144** · `gemma4-26b-256k` **17.64 GB** ·
100% GPU. 확인 경로: 프로필로 실제 호출(`hermes -p fact-checker chat -q …`) → `ollama ps`.
**설정 파일이 아니라 서버가 보고하는 값을 봐야 한다.**

⚠️ **`context_length` 와 Modelfile 의 `num_ctx` 는 항상 같은 값이어야 한다.** 압축 임계가 실제
서빙 창보다 크면 Hermes 는 넣었다고 믿고 모델은 못 본 상태가 된다 — `docs/11 §7 ⑦` 의
"실패 표면과 근본 원인이 두 층 떨어진다"가 그대로 재현되는 모양이다.

**교훈:** 설정 키가 존재한다는 것은 그 키가 **먹힌다**는 뜻이 아니다. `docs/13 §5` 의
"동작하는 척하는 게이트" 와 같은 계열이다 — **설정을 넣었으면 그것이 실제로 반영됐는지를
바깥에서 관측하라**(여기서는 `ollama ps` 의 CONTEXT 열).

### 3.2 ⚠️⚠️ 창 크기는 성능 손잡이가 아니라 **정확성 손잡이**다 — M-2026-005 가 이걸로 멈췄다

`context_length: 65536` 으로 실미션을 돌리자 stage 5 가 **압축 루프에 갇혀 사실상 멈췄다**
(75분간 산출물 2/11, 워커 1회는 signal 7 로 사망). 로그:

```
📦 Pre-API compression: ~47,277 tokens near the context/output limit.
🗜️ Compacting context …            (6회)
⚠️ Session compressed 2 times — accuracy may degrade
```

**압축 발동 지점은 `context_length` 가 아니라 *입력 예산*에서 나온다**
(`/opt/hermes/agent/context_compressor.py:2113` `_compute_threshold_tokens`):

```
effective_window = context_length − max_tokens
floored = max(effective_window × threshold, MINIMUM_CONTEXT_LENGTH=64000)
floored >= effective_window  →  ★퇴화 분기★ = int(effective_window × 0.85)
```

`65536 − 16384 = 49152 < 64000` 이라 **항상 퇴화 분기**로 떨어진다. 결과:

| context_length | max_tokens | threshold | 압축 발동 | 비고 |
|---|---|---|---|---|
| 65536 | 16384 | 0.5 | **41,779** | 로그의 47,277 이 여기 걸렸다 |
| 65536 | 16384 | **0.9** | **41,779** | ★ **임계를 올려도 값이 안 바뀐다 — 완전 무력** |
| 98304 | 16384 | 0.85 | 69,632 | 퇴화 탈출 |
| 131072 | 16384 | 0.85 | 97,484 | 이전 설정 (2.33배) |
| **262144** | 16384 | **0.85** | **208,896** | ★ **현재 설정** (5.00배) — 메모리 비용은 +0.8%(§3.1) |

**규칙: `context_length − max_tokens > 64000` 을 반드시 만족시켜라.** 못 지키면
`compression.threshold` 를 아무리 조정해도 창의 85%에서 압축이 상시 발동하고, 압축 자체가
LLM 호출이라 **파이프라인이 전진하지 못한다.**
`scripts/tests/test_set_backend.py::test_window_escapes_the_degenerate_compaction_branch`
가 이 조건을 강제한다.

### 3.3 ⚠️ `compression.*` 는 루트 config 에서 **상속되지 않는다**

named 프로필은 `HERMES_HOME=<root>/profiles/<name>` 이라 **자기 `config.yaml` 만** 읽는다
(`hermes_cli/config.py:694` `get_config_path()`). 레이어는
`DEFAULT_CONFIG → <HERMES_HOME>/config.yaml → /etc/hermes/config.yaml` 뿐이고 **루트는
레이어가 아니다.** 우리 `hermes-home/config.yaml` 의 `compression:` 블록은 지금까지
**무시되고 있었다**(값이 전부 기본값과 같아서 티가 안 났다).

그래서 `set_backend.py` 가 `compression:` 블록을 **프로필마다 직접 쓴다**(`extra_blocks`).
`agent.reasoning_effort` 도 같은 규칙이다.

⚠️ `<512K` 창에서는 `threshold` 가 **0.75 로 하한이 강제**되므로(`_effective_threshold_percent`)
0.75 이하 값은 의미가 없다. 우리는 0.85 를 쓴다.

## 4. 전환 절차

```bash
python3 scripts/set_backend.py --show                     # 현재 상태
python3 scripts/set_backend.py --backend ollama --dry-run # 대상 확인
python3 scripts/set_backend.py --build-models             # -256k 파생본 생성(없는 것만)
python3 scripts/set_backend.py --backend ollama           # 적용
docker compose up -d --force-recreate hermes-solomon hermes-gatekeeper
docker exec hermes-solomon hermes profile list            # 모델명 확인
python3 scripts/usage_report.py                           # 로컬 준비 상태(exit 0 이어야 착수 가능)
ollama ps                                                 # ★ CONTEXT 가 262144 인지 확인
```

`--build-models` 는 원본이 없으면 `ollama pull <원본>` 을 안내하고 exit 1 한다. 원본은
`gemma4:26b`(17GB) 하나. 폴백은 `gemma4:e4b`(9.6GB)·`glm-4.7-flash`(19GB).

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

배치가 단일 모델(`gemma4-26b-256k` **17.64GB @262144** · 실측 2026-08-05 (3))이라 스왑 자체가
없어졌다. 호스트 64GB 중 상주 17.64GB — **창을 천장까지 올리고도 여유가 크다**(§3.1 의
+0.8% 측정). 상주 1개면 충분하다. 11단계 파이프라인은 순차
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

## 6.5 ⚠️ 미션을 세울 때의 함정 (2026-08-05 실측 — 내가 전부 밟았다)

**① `kanban block` 을 두 번 하면 카드가 `triage` 로 가고, 거기엔 비-LLM 탈출구가 없다.**
`block --help` 에 적혀 있다 — *"Repeated same-kind re-blocks after unblock route the task to
triage to break unblock loops."* 그런데 `triage` 에서 나오는 길은:
- `unblock` ❌ — `blocked`/`scheduled` 만 받는다(`kanban_db.py:5901` `unblock_task`)
- `promote` ❌ — *"promote only applies to 'todo' or 'blocked'"*
- `specify` ⚠️ — **LLM 이 카드 제목·본문을 다시 쓴다.** stage 계약이 날아갈 수 있다
- `decompose` ⚠️ — 자식 카드를 만든다(중복 생성)

→ **정지는 한 번만 `block` 하고, 재개 후 다시 세울 일이 있으면 `schedule` 을 써라**(아래 ⑤).

⚠️ 실측 보정: 2회째 `block` 이 `triage` 로 간다고 적었지만, 실제로 두 번 관측한 결과는
**`block_loop_detected {recurrences: 2, limit: 2}` → `promoted`**, 즉 **도로 `ready` 가 되어
디스패처가 바로 집는다**. `triage` 보다 위험하다 — 세우려던 카드가 오히려 실행된다.

**② 카드 상태를 SQL 로 직접 고치면 디스패처가 즉시 다시 집는다.**
`triage → blocked` 로 되돌렸더니 **워커 2개가 동시에 뜨고**, 완료돼 있던
`analysis/dhuliawala2024.md` 를 덮어써 14.1KB → 4.1KB 로 **잘렸다**(git 에 없어 복구 불가 ·
샤드 재실행으로 복원). 상태기계를 우회하면 `block_kind`·`current_run_id` 같은 메타가
어긋난 채로 남아 디스패처가 정상 카드로 본다.

**③ 확실한 일시중지 = 컨테이너를 세운다.**
```bash
docker exec hermes-solomon ps -eo pid,args | grep '[k]anban task'   # 워커 확인
docker exec hermes-solomon kill -9 <pid>                             # 먼저 죽인다
docker compose stop hermes-solomon hermes-gatekeeper                 # 디스패처까지 정지
```
재개는 `docker compose up -d` → `hermes kanban unblock <id> --reason "…"`.
**보드 상태를 손으로 고치는 것보다 디스패처를 세우는 것이 안전하다.**

⚠️ **미션 산출물은 커밋되기 전까지 백업이 없다.** 워커가 덮어쓰면 그걸로 끝이다
(위 ②가 정확히 그랬다). 단계가 끝날 때마다 커밋하는 것을 고려하라.

**④ 컨테이너를 세우면 claim lock 이 DB 에 남는다 — 카드가 `ready` 인데 디스패처가 영영 안 집는다.**
③ 대로 컨테이너를 세우고 다음 세션에 `docker compose up -d` 로 재개했더니, 카드는 `ready` 인데
**아무 일도 일어나지 않았다.** 진단 명령이 전부 정상을 가리킨다:

```bash
hermes kanban list          # ▶ t_b07b1739  ready  reader   ← 정상으로 보인다
hermes kanban diagnostics   # No active diagnostics on this board.
hermes kanban dispatch --dry-run --json
#   {"spawned": [], "skipped_nonspawnable": [], "skipped_per_profile_capped": [], …}
#   ↑ spawn 도 안 하고 skip 목록에도 없다. 후보에조차 안 오른다. 로그도 남지 않는다.
```

원인은 **정지된 옛 컨테이너의 claim lock**이다. claim 은 컨테이너 호스트명으로 키가 잡히는데
(`a6bb036653e2:206`), 컨테이너를 죽이면 lock 을 반납할 주체가 사라진다. 새 컨테이너는
호스트명이 다르므로 그 lock 을 자기 것으로 인식하지 못하고, 카드는 `ready` 인 채로 영원히
후보에서 빠진다. `hermes kanban show <tid>` 의 `Runs` 마지막 항목이 `reclaimed`/`crashed` 인데
상태는 `ready` 이면 이 상황이다.

```bash
hermes kanban reclaim <tid>       # ← 이것만 고친다
hermes kanban dispatch --dry-run --json   # spawned 에 뜨는지 확인
```

⚠️ **`unblock` 도 `promote` 도 이걸 고치지 못한다** — 상태가 이미 `ready` 라 둘 다 no-op 이고,
"명령은 성공했는데 여전히 안 돈다" 만 남는다. ①과 같은 계열의 실패다: **보드는 멀쩡해
보이는데 아무 일도 일어나지 않고, 그 이유가 어디에도 안 적힌다.**

→ 재개 절차에 넣어라: `docker compose up -d` → **`hermes kanban reclaim <tid>`** →
`unblock`(필요하면) → `dispatch --dry-run` 으로 후보에 올랐는지 확인.

**⑤ 이미 한 번 `blocked` 됐던 카드를 다시 세우는 방법은 `schedule` 이다 — `link` 도 `block` 도 안 된다.**
Slack 승인이 stage 8 을 열어 워커가 뜬 것을 세우고(워커 kill + 컨테이너 stop) 다시 닫으려는데,
쓸 수 있는 수단이 생각보다 적었다. **셋 다 실측했다:**

| 수단 | 결과 |
|---|---|
| `link <상류> <이 카드>` (미완료 부모 추가) | ❌ **막지 못한다.** 사후 `link` 는 `ready` 를 `todo` 로 되돌리지 않는다. `dispatch --dry-run` 에 그대로 `spawned` 로 뜬다 — 부모/자식 관계는 **생성 시점**에만 초기 상태를 정한다(`instantiate_template.py` 가 게이트 카드를 `--parent` 없이 만든 뒤 곧바로 `block` 하는 이유가 이것이다) |
| `block` 2회째 | ❌ **위험하다.** `block_loop_detected` → `promoted` → 도로 `ready`(위 ① 보정) |
| **`schedule <tid> "<사유>"`** | ✅ **된다.** `Scheduled`(시간 대기)는 `needs_input` 과 **다른 상태**라 block-loop 카운터를 건드리지 않는다. `dispatch --dry-run` → `spawned: []` |

**부수 효과가 하나 더 있는데 이게 오히려 중요하다**: 게이트키퍼의 `pending_sam_gates` 는
`task_status(tid) == "blocked"` 만 본다. 따라서 `scheduled` 카드는 **`#approvals` 에 다시
게시되지 않고 Slack 의 `승인` 으로도 열리지 않는다.** 작업 중 승인 루프가 카드를 도로 여는
것을 막으려면 `schedule` 이 정답이다.

재개는 `unblock` 이다 — *"Return **blocked/scheduled** tasks to ready"*.

⚠️ **어느 수단을 쓰든 `dispatch --dry-run --json` 으로 `spawned` 가 비었는지 확인하라.**
카드 목록의 상태 표시만 믿지 마라 — ④가 정확히 그 반대 방향의 사고였다(`ready` 로
보이는데 안 돌았다). **상태 표시와 디스패치 가능성은 별개다.**

## 7. 알려진 한계 · 다음

1. **프로토콜 준수는 재서 확인했다(§2.1) — 다만 재현되지 않은 실패가 하나 있다.**
   연결 검증 때 `developer` 가 목표 파일은 정확히 썼지만 **경로를 백틱으로 감싼 채** 엉뚱한
   곳(`/tmp/...`)에도 두 번 더 쓰려 했다(`HERMES_WRITE_SAFE_ROOT` 와 `.json` 문법 검증이 둘 다
   막았다 — 가드레일이 일했다). 그런데 **프로브 3과제 × 5회 반복에서는 재현되지 않았다.**
   즉 드물게 나오는 실패이지 상시 결함이 아니다. 실미션에서 같은 계열의 실패
   (`kanban_complete` 미호출 = `protocol violation`)가 나오면 §2.1 프로브부터 다시 돌려라.
   ~~객관 게이트 62종은 산출물을 보므로 그대로 작동한다.~~ → **틀렸다. 아래 1.5 를 보라.**

   **1.5. ⚠️⚠️ 프로브가 못 잰 것이 무엇이었는지 이제 안다 — 그리고 그게 실미션을 망쳤다
   (2026-08-05 · `docs/11 §7 ⑧`).**
   §2.1 프로브는 **도구 프로토콜 준수**를 쟀다: 인자를 충실히 채우는가, 부작용을 내지 않는가,
   종료를 호출하는가, `VERDICT` 포맷이 맞는가. 채택 모델은 전 항목 100% 였고 **그 측정은
   지금도 유효하다.** 그러나 프로브가 재지 않은 축이 있었다 — **성실성**이다.

   M-2026-005 stage 5 에서 `reader` 는 `raw/` 에 원문(35KB~384KB)을 **다 가지고 있으면서
   읽지 않고** `curated.md` 의 관련성 메모를 재서술한 뒤, 본문에 이렇게 적었다:
   `**Evidence:** [Simulated deep analysis based on relevance impacts.]` — 11편 중 **7편**이다.
   프로토콜은 완벽하게 지켰다. 파일을 정확한 경로에 쓰고 `kanban_complete` 를 호출했다.
   **형식은 100%, 내용은 0% 다.**

   그리고 위 취소선 문장이 왜 틀렸는지가 핵심이다. **객관 게이트가 산출물을 본다는 것은
   게이트마다 참이 아니다.** 그 stage 의 게이트(`recency_check`·`source_balance`)는
   `raw/sources.yaml` **메타데이터만** 읽었다 — 산출물을 아예 열지 않는다. LLM 검증자는
   11편 중 5편만 대조하고 `VERDICT: PASS` 를 냈다.

   > **모델을 프로토콜로 고르는 것은 필요조건이지 충분조건이 아니다.**
   > 프로브는 "이 모델이 우리 배관에 연결되는가"를 재고, 그 이상은 재지 않는다.
   > 성실성은 **모델 선정이 아니라 게이트로** 다뤄야 한다 — 게이트는 결정적이고,
   > 모델이 바뀌어도 남는다. → `analysis_substance` 신설(`docs/11 §7 ⑧`).
2. **`reasoning_effort: medium` 은 그대로 뒀다.** custom 프로바이더는 이 값을 top-level
   `reasoning_effort` 로 넘긴다 — 인식하지 못하는 엔드포인트는 무시한다
   (`custom/__init__.py` build_api_kwargs_extras).
3. **Ollama 모델은 codex 사용량 기록에 남지 않는다.** `hermes insights` 의 누적 토큰은 계속
   codex 기준이다. 로컬 사용량 계측은 아직 없다(성장 지표 대시보드 과제와 함께 볼 것).
4. **이미지 생성**(`image_gen.provider: openai-codex`)은 전환 대상이 아니다 — 파이프라인에서
   쓰지 않는다.
