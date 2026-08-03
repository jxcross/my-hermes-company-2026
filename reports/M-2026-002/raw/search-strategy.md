# M-2026-002 — Search Strategy

- 작성일: 2026-08-02
- 주제: AI 에이전트 평가·신뢰성·안전성 동향
- 대상 기간: 2026-05-01~2026-08-02 (발행일 기준; 8월은 2일까지)
- 수집 범위: 공개 원문만. 1차 출처(연구기관·모델 제공자·표준화 기구·arXiv 원문)를 우선하고, 2차 출처는 후보 탐색 보조로만 사용한다.
- 이 문서는 검색 전략만 기록한다. 이 단계에서 원문 수집·추출·평가·판정은 하지 않았다.

## 재사용 후보 — llm-wiki / M-2026-001

아래는 `/work/llm-wiki/index.md` 및 `concepts/`를 먼저 조회하여 확인한 기존 원문이다. 이번 범위와의 연결은 해당 wiki가 이미 기록한 태그·출처 기준이며, 후속 단계에서 원문 및 발행일을 다시 확인한다.

| ID | 기존 원문 | URL | 기존 발행일 | 기존 출처유형 | 연결 범주 |
|---|---|---|---:|---|---|
| R1 | Evaluating code review agents with ReviewBench | https://www.langchain.com/blog/evaluating-code-review-agents-with-reviewbench | 2026-07-31 | 공식 블로그/평가 | 실제 업무 기반 agent 평가 |
| R2 | Echoverse: Deep, evolving environments for computer-use agents | https://www.microsoft.com/en-us/research/blog/echoverse-deep-evolving-environments-for-computer-use-agents/ | 2026-07-30 | 공식 연구 블로그 | 재현 가능한 환경·state-grounded verifier |
| R3 | Investigating incidents cybersecurity evals | https://www.anthropic.com/news/investigating-incidents-cybersecurity-evals | 2026-07-30 | 공식 뉴스/평가 | evaluation 환경 접근통제·격리 |
| R4 | Agentic misalignment | https://www.anthropic.com/research/agentic-misalignment | 2026-07-13 | 공식 연구 | controlled simulation의 안전성·오정렬 |
| R5 | Agents need their own computer. Here's how to give them one safely. | https://www.langchain.com/blog/agents-need-their-own-computer | 2026-07-21 | 공식 블로그/컴퓨터 유즈 | 실행 격리·credential·audit |
| R6 | OpenAI and Hugging Face partner to address security incident during model evaluation | https://openai.com/index/hugging-face-model-evaluation-security-incident | 2026-07-21 | 공식 블로그/평가·보안 | model-evaluation security incident |
| R7 | How enabling two settings tripled our scores on the ARC-AGI-3 benchmark | https://openai.com/index/how-two-settings-tripled-our-arc-agi-3-scores | 2026-07-29 | 공식 블로그/평가 | benchmark 설정·측정 |

- 재사용 후보 수: 7건.
- 기존 wiki의 관련 concept: `agent-evaluation`, `agent-governance`, `agentic-misalignment`, `computer-use-agents`, `skill-optimization`, `evolving-knowledge`, `agentic-ai-trends`.
- R1~R7은 발행일이 모두 이번 기간 안에 기록되어 있다. 기존 기록의 수집일은 2026-08-02이다.

## 신규 검색식

Tavily `web_search`로 아래 검색식을 실행했다. 후속 Collection 단계는 결과 URL을 원문으로 열어 발행일·원문 접근성·중복 여부를 기록한다.

| 우선순위 | 검색식 | 목적 |
|---:|---|---|
| 1 | `AI agent evaluation benchmark verifier reliability safety 2026 May June July official research` | 평가·verifier·신뢰성·안전성의 교집합 후보 탐색 |
| 2 | `site:openai.com AI agents safety evaluations 2026 May OR June OR July` | OpenAI 1차 안전성·독립평가 자료 |
| 3 | `site:anthropic.com research AI agent safety evaluation 2026 May OR June OR July` | Anthropic 1차 평가·안전성 자료 |
| 4 | `site:metr.org agent evaluation benchmark safety reliability 2026` | 독립 평가기관의 reliability·risk 자료 |
| 5 | `site:arxiv.org AI agent benchmark evaluation reliability safety submittedDate 2026` | 최근 공개 preprint/benchmark 원문 |
| 6 | `site:research.ibm.com AI agent benchmark evaluation safety trustworthiness 2026` | 연구기관의 benchmark·trustworthiness 자료 |
| 7 | `site:ietf.org AI agent security evaluation benchmark 2026` | 표준화 기구의 security-evaluation draft |
| 8 | `"agent reliability" "ICML 2026" evaluation` | 신뢰성 연구·학회 공개본 후보 |
| 9 | `("prompt injection" OR "tool misuse") "AI agent" safety evaluation 2026` | agent 공격 표면과 안전성 평가 후보 |
| 10 | `("reproducibility" OR "repeatability") "AI agent" evaluation benchmark 2026` | 재현성·반복 측정 방법 후보 |

## Tavily 검색 결과 기반 신규 소스 후보

아래는 검색 결과에 표시된 제목·URL·설명 수준의 후보 목록이다. 원문은 아직 수집하지 않았다. 발행일이 결과에 명시되지 않은 경우 `미확인`으로 표기한다.

| ID | 제목 | URL | 검색 결과상 발행일 | 출처유형 | 검색 축 |
|---|---|---|---:|---|---|
| N1 | A shared playbook for trustworthy third party evaluations | https://openai.com/index/trustworthy-third-party-evaluations-foundations | 2026-05-29 | 공식 블로그/안전성 | 독립·제3자 평가 |
| N2 | GPT-5.6 System Card | https://deploymentsafety.openai.com/gpt-5-6/evaluations-with-challenging-prompts | 2026-07-09 | 공식 안전성 허브/system card | deployment safety·evaluation |
| N3 | GPT-Red: Unlocking Self-Improvement for Robustness | https://openai.com/index/unlocking-self-improvement-gpt-red | 2026-07-15 | 공식 블로그/안전성 | automated red teaming·robustness |
| N4 | Frontier Risk Report (February to March 2026) | https://metr.org/blog/2026-05-19-frontier-risk-report | 2026-05-19 | 독립 연구기관 블로그 | agent risk·reliability |
| N5 | Metrics of Agent Ability | https://metr.org/notes/2026-07-24-metrics-of-model-ability | 2026-07-24 | 독립 연구기관 노트 | reliability metrics |
| N6 | Expenditure Horizon: Measuring Optimization Ability, with ... | https://metr.org/blog/2026-07-21-expenditure-horizon | 2026-07-21 | 독립 연구기관 블로그 | repeated evaluation·human comparison |
| N7 | A Benchmark for Real-World, Long-Horizon Agent Evaluation | https://arxiv.org/html/2605.10912v1 | 2026-05 (정확한 일자 미확인) | arXiv preprint | long-horizon benchmark·adversarial safety tasks |
| N8 | Security Evaluation Benchmark for AI Agents | https://www.ietf.org/archive/id/draft-han-bmwg-agent-security-benchmark-00.html | 2026-07 | IETF Internet-Draft | agent security benchmark |
| N9 | SAgE: Science of Agent Evaluation | https://sage.cs.princeton.edu | 미확인 | 대학 연구그룹 웹사이트 | open-world evaluation·agent reliability |
| N10 | The future of AI agent evaluation | https://research.ibm.com/blog/AI-agent-benchmarks | 미확인 | 기업 연구 블로그 | benchmark·safety·trustworthiness |

## 보조 탐색 결과 — 우선 원문 수집 대상 아님

| 후보 | 이유 / 표시 |
|---|---|
| https://www.algolia.com/blog/ai/ai-agent-evaluation-frameworks-metrics-testing-strategies | 2차 기업 블로그. benchmark 명칭 탐색 보조용으로 표시한다. |
| https://galileo.ai/blog/state-of-ai-evaluation | 결과 본문이 사이트 공통 텍스트 중심이어서 원문성·발행일을 후속 단계에서 확인해야 한다. |

## Collection 단계 전달 규칙

1. R1~R7 원문부터 다시 열어 URL·발행일·원문 접근 여부를 확인하고, 이번 미션 raw에 별도 보존한다.
2. N1~N8을 1차 신규 수집 후보로 우선 열고, N9~N10은 발행일을 확인한 뒤 기간 필터에 맞을 때 수집한다.
3. 각 원문은 `raw/`에 URL, 수집일, 발행일, 출처유형과 함께 원문 그대로 저장한다. 발행일을 원문에서 확인할 수 없으면 `미확인`을 유지한다.
4. 제목·URL 동일 후보는 중복 표시만 하고 삭제·관련성 판정은 curator 단계로 넘긴다.
5. 최소 목표는 재사용 7건 + 신규 5건 이상을 열어, 최종 검토 대상 8건 이상(권장 10~12건)을 확보하는 것이다. 이 수량은 전략 목표이며 아직 수집 완료 수가 아니다.
