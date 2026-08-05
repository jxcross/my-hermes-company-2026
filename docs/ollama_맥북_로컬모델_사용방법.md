M4·64GB 통합 메모리라면 **Hermes Agent + Ollama 서브에이전트 3개 병렬 실행**을 충분히 시도할 수 있습니다. 다만 M4, M4 Pro, M4 Max에 따라 생성 속도는 달라지지만 메모리 구성 방향은 같습니다.

## 가장 추천하는 구성

### 코딩 중심

```bash
ollama pull devstral-small-2:24b
```

* Q4 모델 크기 약 15GB
* 코드베이스 탐색, 터미널 사용, 다중 파일 수정, 에이전트 코딩에 특화
* Ollama 모델 페이지 기준 384K 컨텍스트와 도구 호출을 지원합니다. ([Ollama][1])

### 범용 도구 사용 중심

```bash
ollama pull gemma4:31b
```

Hermes 공식 로컬 Ollama 가이드는 도구 호출과 에이전트 작업에 `gemma4:31b`를 우선 추천하며, 모델 메모리 요구량을 24GB 이상으로 안내합니다. ([Hermes Agent][2])

### 대규모 코드 분석 중심

```bash
ollama pull qwen3-coder:30b
```

`qwen3-coder:30b`는 약 19GB이고, 30B 전체 파라미터 중 약 3.3B를 활성화하는 MoE 모델입니다. 저장소 단위 코드 분석과 장시간 에이전트 작업에 맞춰져 있습니다. ([Ollama][3])

제 추천 순서는 다음과 같습니다.

| 목적             | 추천 모델                  | Hermes 병렬 수 |
| -------------- | ---------------------- | ----------: |
| 실제 코딩·파일 수정    | `devstral-small-2:24b` |           3 |
| 코드 분석·계획·리뷰    | `qwen3-coder:30b`      |           3 |
| 범용 에이전트·도구 안정성 | `gemma4:31b`           |         2~3 |
| 최대 응답 속도       | 12B~14B 도구 모델          |           4 |

## 중요한 점: 컨텍스트를 64K로 제한

Ollama는 48GiB 이상 환경에서 기본 컨텍스트를 크게 잡을 수 있으며, 공식 문서는 에이전트 및 코딩 작업에 최소 64K를 권장합니다. 병렬 요청에서는 컨텍스트 메모리가 `병렬 수 × 컨텍스트 길이`에 비례해 증가합니다. 따라서 64GB라고 해서 256K 컨텍스트를 3개 병렬로 사용하는 것은 비효율적입니다. ([Ollama][4])

M4 64GB에서는 우선 다음 조합이 좋습니다.

```text
모델: 24B~31B Q4
컨텍스트: 65536
Hermes 서브에이전트: 3
Ollama 병렬 요청: 3
KV 캐시: q8_0
동시 로딩 모델: 1
```

## macOS Ollama 설정

Ollama를 메뉴 막대 애플리케이션으로 실행한다면 `launchctl`로 설정해야 합니다. ([Ollama][5])

터미널에서 실행합니다.

```bash
launchctl setenv OLLAMA_NUM_PARALLEL "3"
launchctl setenv OLLAMA_CONTEXT_LENGTH "65536"
launchctl setenv OLLAMA_MAX_LOADED_MODELS "1"
launchctl setenv OLLAMA_FLASH_ATTENTION "1"
launchctl setenv OLLAMA_KV_CACHE_TYPE "q8_0"
launchctl setenv OLLAMA_KEEP_ALIVE "24h"
```

그다음 Ollama를 완전히 종료하고 다시 실행합니다.

```bash
osascript -e 'quit app "Ollama"'
open -a Ollama
```

`q8_0` KV 캐시는 기본 `f16` 대비 약 절반의 메모리를 사용하고, 일반적으로 품질 손실이 매우 작다고 Ollama가 안내합니다. ([Ollama][5])

설정 확인:

```bash
launchctl getenv OLLAMA_NUM_PARALLEL
launchctl getenv OLLAMA_CONTEXT_LENGTH
launchctl getenv OLLAMA_KV_CACHE_TYPE
```

모델 실행 후:

```bash
ollama ps
```

`PROCESSOR`가 `100% GPU` 또는 Metal GPU 중심으로 표시되는지 확인합니다.

## Hermes 설정

`~/.hermes/config.yaml`:

```yaml
model:
  default: "devstral-small-2:24b"
  provider: "custom"
  base_url: "http://127.0.0.1:11434/v1"
  api_key: "no-key"

delegation:
  max_concurrent_children: 3
  max_iterations: 30
  max_spawn_depth: 1
  orchestrator_enabled: false
```

`max_spawn_depth: 1`과 `orchestrator_enabled: false`를 권장하는 이유는 서브에이전트가 다시 서브에이전트를 만들면서 수가 폭발하는 것을 막기 위해서입니다. Hermes는 기본적으로 3개의 서브에이전트를 병렬 실행하며, 이 값은 `delegation.max_concurrent_children`로 조정합니다. ([Hermes Agent][6])

### Qwen3-Coder를 사용할 경우

```yaml
model:
  default: "qwen3-coder:30b"
  provider: "custom"
  base_url: "http://127.0.0.1:11434/v1"
  api_key: "no-key"

delegation:
  max_concurrent_children: 3
  max_iterations: 30
  max_spawn_depth: 1
  orchestrator_enabled: false
```

처음에는 부모와 자식에 **같은 모델**을 사용하세요. 부모와 자식 모델을 다르게 지정하면 Ollama가 두 모델을 동시에 메모리에 올리려고 할 수 있습니다. Hermes에서 delegation 모델을 생략하면 부모와 동일한 모델을 사용합니다. ([Hermes Agent][6])

## 3개 병렬 실행 프롬프트

```text
delegate_task의 tasks 배열을 한 번 호출하여 다음 작업을
3개의 서브에이전트로 동시에 실행하라.

1. 프로젝트 아키텍처와 모듈 의존성 분석
2. 테스트 실행 및 실패 원인 분석
3. 보안, 예외 처리, 성능 문제 검토

각 에이전트는 파일을 수정하지 말고 분석 결과만 반환한다.
모든 결과가 도착하면 중복 문제를 제거하고,
우선순위별 수정 계획을 작성한다.
```

Hermes의 병렬 실행 여부는 다음 명령으로 확인할 수 있습니다.

```text
/agents
```

실시간 로그도 볼 수 있습니다.

```bash
tail -f ~/.hermes/cache/delegation/live/*/task-0.log
```

Hermes는 각 자식 에이전트마다 독립 터미널과 컨텍스트를 제공하며, 최종 요약만 부모 컨텍스트에 전달합니다. ([Hermes Agent][6])

## 권장 운영 방식

처음에는 다음 설정으로 시작하는 것이 가장 안정적입니다.

```text
devstral-small-2:24b
64K context
3 parallel subagents
q8_0 KV cache
```

메모리 압박이나 스왑이 발생하면 병렬 수만 2로 낮춥니다.

```bash
launchctl setenv OLLAMA_NUM_PARALLEL "2"
```

```yaml
delegation:
  max_concurrent_children: 2
```

반대로 메모리 압박이 없더라도 4개 이상은 추천하지 않습니다. 같은 모델의 병렬 요청은 모델 가중치를 각각 새로 복제하지 않지만, 각 요청의 KV 캐시와 컨텍스트 메모리는 별도로 증가하고, GPU 연산 성능도 에이전트끼리 나누기 때문에 3개에서 가장 균형이 좋습니다. ([Ollama][5])

**최종 추천:** M4 64GB에서는 `Hermes + devstral-small-2:24b + 64K + 병렬 3개`로 시작하고, 복잡한 저장소 분석 품질이 부족할 때 `qwen3-coder:30b`로 교체하는 구성이 가장 실용적입니다.

[1]: https://ollama.com/library/devstral-small-2/tags "Tags · devstral-small-2"
[2]: https://hermes-agent.nousresearch.com/docs/guides/local-ollama-setup "Run Hermes Locally with Ollama — Zero API Cost | Hermes Agent"
[3]: https://ollama.com/library/qwen3-coder%3A30b?utm_source=chatgpt.com "qwen3-coder:30b"
[4]: https://docs.ollama.com/context-length?utm_source=chatgpt.com "Context length - Ollama"
[5]: https://docs.ollama.com/faq "FAQ - Ollama"
[6]: https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation/ "Subagent Delegation | Hermes Agent"
