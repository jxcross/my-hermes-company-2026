# M-2026-002 · 4 Dedup·Relevance 선별

- 선별일: 2026-08-02
- 범위: AI 에이전트의 평가·신뢰성·안전성 동향, 2026-05-01~2026-08-02 발행 공개자료.
- 입력: `sources.md`의 원자료 17건. 원문 URL 17개가 모두 고유함을 확인했다.
- 판정 원칙: (1) 기간·주제 적합성, (2) 1차/독립 연구·표준 초안 우선, (3) 기존 wiki와 URL·원문 보존본이 겹칠 때 원문을 다시 독립 출처로 세지 않고 재사용으로 표시, (4) 발행일이 범위 밖이거나 범위 충족을 확인할 수 없으면 제외.
- 이 문서는 선별·중복·재사용 기록이며, 주장 종합·사실검증을 수행하지 않는다.

## 결과

- 입력 17건 → 선별 15건 (신규 8, 기존 wiki 재사용 7) → 제외 2건.
- 미션 내부 URL 중복: 0건.
- 기존 wiki 원문과 중복(재사용): 7건. 모두 각 원자료의 `재사용표시`가 가리키는 `/work/llm-wiki/raw/mission-m-2026-001/` 보존본의 존재를 확인했다. 이들은 선별 집합에는 유지하되, 이후 단계에서 별도 신규 근거로 이중 계상하지 않는다.
- 공식 재사용률(스키마 분모=새 미션 원자료 전체): **7/17 = 41.2%**.
- 참고: 선별 집합 기준 재사용 비율은 **7/15 = 46.7%**. 제외된 2건은 모두 신규 수집물이므로, 공식 수치와 구분해 기록한다.

## 선별 목록

| ID | 원자료 | 구분 | 관련성 | 근거/후속 사용 경계 |
|---|---|---|---:|---|
| S01 | `openai-trustworthy-third-party-evaluations.md` | 신규 | 5/5 | agentic harness와 독립 제3자 평가 설계의 직접 1차 자료. ^[openai-trustworthy-third-party-evaluations.md] |
| S02 | `openai-gpt-5-6-system-card.md` | 신규 | 5/5 | 배포 전 안전성 평가·완화의 공식 system card. 제공자 자기보고 근거로 취급한다. ^[openai-gpt-5-6-system-card.md] |
| S03 | `openai-gpt-red-robustness.md` | 신규 | 5/5 | 자동 red-teaming·prompt injection robustness의 직접 자료. 제공자 자기보고 근거로 취급한다. ^[openai-gpt-red-robustness.md] |
| S04 | `metr-frontier-risk-report.md` | 신규 | 5/5 | 독립 연구기관의 frontier risk 평가 자료. ^[metr-frontier-risk-report.md] |
| S05 | `metr-metrics-of-agent-ability.md` | 신규 | 5/5 | 비용/시간/토큰을 포함한 agent ability 측정 방법론. ^[metr-metrics-of-agent-ability.md] |
| S06 | `metr-expenditure-horizon.md` | 신규 | 4/5 | agent 최적화 능력의 비용-성과 측정 방법론; 신뢰성/평가 맥락에 보조적으로 적합. ^[metr-expenditure-horizon.md] |
| S07 | `arxiv-wildclawbench.md` | 신규 | 5/5 | native-runtime·long-horizon agent 평가 벤치마크의 원 논문 preprint. 아직 peer review 전임을 유지한다. ^[arxiv-wildclawbench.md] |
| S08 | `ietf-agent-security-benchmark.md` | 신규 | 5/5 | agent security 평가 차원·방법론의 표준화 초안. Internet-Draft는 work in progress로만 인용한다. ^[ietf-agent-security-benchmark.md] |
| S09 | `langchain-reviewbench.md` | 재사용:wiki | 5/5 | 실제 PR feedback 기반 agent 평가. canonical raw: `raw/mission-m-2026-001/langchain-reviewbench.md`. ^[langchain-reviewbench.md] |
| S10 | `microsoft-echoverse.md` | 재사용:wiki | 5/5 | computer-use 환경·state-grounded verifier. canonical raw: `raw/mission-m-2026-001/microsoft-echoverse-computer-use-agents.md`. ^[microsoft-echoverse.md] |
| S11 | `anthropic-cybersecurity-evals.md` | 재사용:wiki | 5/5 | evaluation environment 격리·모니터링의 실제 incident 자료. canonical raw: `raw/mission-m-2026-001/anthropic-cybersecurity-evals-incidents.md`. ^[anthropic-cybersecurity-evals.md] |
| S12 | `anthropic-agentic-misalignment.md` | 재사용:wiki | 5/5 | 통제된 simulation에서의 안전성 평가 자료; 실제 배포 증거와 혼동하지 않는다. canonical raw: `raw/mission-m-2026-001/anthropic-agentic-misalignment.md`. ^[anthropic-agentic-misalignment.md] |
| S13 | `langchain-agents-own-computer.md` | 재사용:wiki | 4/5 | agent execution isolation·credential·audit controls의 운영 안전성 보조 자료. canonical raw: `raw/mission-m-2026-001/langchain-agents-own-computer.md`. ^[langchain-agents-own-computer.md] |
| S14 | `openai-hf-evaluation-security-incident.md` | 재사용:wiki | 5/5 | model evaluation security incident의 직접 관련 자료. 원문은 공식 RSS 제목·설명 수준이므로 세부 주장 근거로 확장하지 않는다. canonical raw: `raw/mission-m-2026-001/openai-hf-model-evaluation-security-incident.md`. ^[openai-hf-evaluation-security-incident.md] |
| S15 | `openai-arc-agi-3-settings.md` | 재사용:wiki | 3/5 | benchmark 설정·측정 사례로만 제한해 사용한다. 원문은 공식 RSS 제목·설명 수준이며, agent reliability 일반화 근거는 아니다. canonical raw: `raw/mission-m-2026-001/openai-arc-agi-3-settings.md`. ^[openai-arc-agi-3-settings.md] |

## 제외 목록

| 원자료 | 구분 | 제외 사유 |
|---|---|---|
| `anthropic-demystifying-agent-evals.md` | 신규 | 원문이 `Published Jan 09, 2026`으로 명시되어 미션 기간(2026-05~08) 밖이다. 주제는 직접 관련이나 최근 3개월 동향 집합에서는 제외한다. ^[anthropic-demystifying-agent-evals.md] |
| `ibm-360-review-agent-benchmarks.md` | 신규 | 수집 보존본과 `sources.md` 모두 발행일이 `미확인`이다. 시간 범위 충족을 확인할 수 없으므로 기간 제한 동향 집합에서 제외한다. ^[ibm-360-review-agent-benchmarks.md] |

## 전달 경계

- 다음 단계는 S01–S15만 검토 대상으로 삼고, S09–S15는 위의 canonical wiki raw를 우선 참조한다.
- 제외 E01–E02는 이 미션의 시간 제한된 동향 근거·정량 집계에서 사용하지 않는다. 발행일 확인 또는 기간 제한 변경 시에만 재선별한다.
- 이 선별은 자료의 사실성·상호 일치·보고서 주장 적합성을 보증하지 않는다. 이는 독립 Deep Analysis 및 Cross-Verify 단계의 책임이다.
