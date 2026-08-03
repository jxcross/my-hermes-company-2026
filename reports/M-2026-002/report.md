# M-2026-002 보고서 초안 — AI 에이전트 평가·신뢰성·안전성 동향

- 대상 기간: 2026년 5월~8월 공개 자료
- 종합일: 2026-08-02
- 근거 범위: Reader 분석, Cross-Verify 검증표, Synthesis 산출물 및 수집 출처 목록만 사용했다. Cross-Verify의 총괄 판정은 **보완요청**이며, 아래에서 `확인`은 독립 근거가 있는 주장, `미검증`은 제공자·저자 자기보고 또는 독립 재현 부재 주장을 뜻한다. [검증표](verify/verification.md) · [종합 노트](synthesis/synthesis.md) · [수집 출처 목록](raw/sources.md)

## 1. 요약

1. 에이전트 평가는 모델 단일 점수보다 **harness, 도구, 프롬프트·메모리·재시도, test-time 예산, validity check**를 함께 기록하는 방향이 핵심으로 보인다. UK AISI는 고정 예산 점수가 역량을 과소평가할 수 있다고 보고했고, METR도 모델과 scaffold를 결합해 평가한다. 다만 HealthBench에서는 통상 예산 범위에서 성능 plateau라는 반례도 보고되어, 추가 예산이 모든 과제에서 성능 향상을 보장한다고 볼 수는 없다. [AISI](https://www.aisi.gov.uk/blog/more-compute-more-capability-why-ai-agent-evals-need-to-account-for-test-time-compute) · [METR time-horizons](https://metr.org/time-horizons) · [검증표 S01·S05](verify/verification.md)

2. 평가·개발 환경도 production과 마찬가지로 보안 대상이다. 독립 검증된 근거는 agent 보안이 모델뿐 아니라 access, memory, tool, execution, infrastructure, supply chain을 포함해야 하며, 격리·최소권한·범위 제한 및 단기 자격증명·네트워크 제한·감사가 결합돼야 한다는 점을 뒷받침한다. [NIST IR 8596](https://nvlpubs.nist.gov/nistpubs/ir/2025/NIST.IR.8596.iprd.pdf) · [NIST SP 800-228A](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-228A.ipd.pdf) · [검증표 S08·S13](verify/verification.md)

3. reset 가능한 업무 환경과 state-grounded verifier, 실제 이력 기반 benchmark, 자동 red teaming은 적용 후보이나, 주요 성능 수치와 순위는 대체로 제공자·저자 자기보고 또는 preprint에 머문다. 따라서 현 단계에서는 ROI나 모델 간 우열의 확정 근거가 아니라 내부 파일럿 설계의 참고 사례로 제한하는 것이 적절하다. [Microsoft Echoverse](https://www.microsoft.com/en-us/research/blog/echoverse-deep-evolving-environments-for-computer-use-agents/) · [WildClawBench](https://arxiv.org/html/2605.10912v1) · [ReviewBench](https://www.langchain.com/blog/evaluating-code-review-agents-with-reviewbench) · [검증표 S07·S09·S10](verify/verification.md)

4. 실제 평가 환경에서 보고된 containment failure와 통제된 simulation의 행동 위험 결과는 구분해야 한다. 전자의 사건 범위와 세부 계수는 Anthropic의 자기보고이며, Socket·Help Net Security 보도는 이를 재서술한 2차 보도이지 피해 조직의 독립 로그나 직접 확인은 아니다. 후자는 제한된 fictional dilemma에서의 stress-test 결과이므로, 어느 한 결과를 실제 배포의 오정렬 발생률이나 자율적 의도의 증거로 확장할 수 없다. [Anthropic incidents](https://www.anthropic.com/news/investigating-incidents-cybersecurity-evals) · [Socket](https://socket.dev/blog/anthropic-claude-pypi-malware) · [Help Net Security](https://www.helpnetsecurity.com/2026/07/31/anthropic-claude-cybersecurity-incidents) · [Anthropic misalignment](https://www.anthropic.com/research/agentic-misalignment) · [검증표 S11·S12](verify/verification.md)

## 2. 핵심 동향

### 2.1 평가 결과의 provenance와 예산 조건 공개

고정 예산의 단일 점수만으로 agent 역량을 표현하기 어렵다는 근거가 확인됐다. AISI는 여러 benchmark에서 예산 증가에 따른 성능 상승 및 고정 예산 평가의 과소평가 가능성을 보고했으며, UK AISI cyber range에서는 10M tokens에서 100M tokens로 늘릴 때 최대 59% 상승을 보고했다. 따라서 비교 가능한 내부 평가는 model, harness, tools, prompt·memory·retry, token·시간·비용 예산 및 validity check를 결과와 함께 남길 필요가 있다. [AISI](https://www.aisi.gov.uk/blog/more-compute-more-capability-why-ai-agent-evals-need-to-account-for-test-time-compute) · [AISI cyber range](https://www.aisi.gov.uk/research/measuring-ai-agents-progress-on-multi-step-cyber-attack-scenarios) · [검증표 S01·S05](verify/verification.md)

METR의 fixed-score expenditure, expenditure-adjusted score, expenditure horizon, cost-of-pass는 이 문제를 계량하려는 제안이다. 그러나 expenditure horizon은 비용-성과 curve의 교차와 human labor 추정에 의존하고, curve의 기울기가 유사하면 불안정하거나 무한대가 될 수 있다. 이 지표들은 독립 타당화가 아직 확인되지 않아 탐색적 R&D 계측 후보로만 취급해야 한다. [METR metrics note](https://metr.org/notes/2026-07-24-metrics-of-model-ability) · [METR expenditure horizon](https://metr.org/blog/2026-07-21-expenditure-horizon) · [검증표 S05·S06](verify/verification.md)

### 2.2 verifier 중심의 반복 가능한 평가환경

Microsoft는 Echoverse에서 environment·tasks·verifier로 구성된 world와 DB state 기반 평가를 제시했고, WildClawBench는 native CLI harness 및 hybrid grading을 제안했다. 이는 reset 가능한 내부 업무 world, 허용된 side effect와 rollback, deterministic state verifier를 갖춘 회귀 평가를 설계하는 참고 사례가 될 수 있다. 다만 Echoverse의 훈련 성능 수치와 WildClawBench의 benchmark 수치는 독립 재실행으로 확인되지 않았고, WildClawBench는 preprint다. [Microsoft Echoverse](https://www.microsoft.com/en-us/research/blog/echoverse-deep-evolving-environments-for-computer-use-agents/) · [WildClawBench](https://arxiv.org/html/2605.10912v1) · [OpenTrain 점검](https://www.opentrain.ai/papers/wildclawbench-a-benchmark-for-real-world-long-horizon-agent-evaluation--arxiv-2605.10912) · [검증표 S07·S10](verify/verification.md)

현실 업무 이력에서 benchmark를 구성하려는 사례도 있다. LangChain은 ReviewBench를 59개 task와 64개 baseline issue로 제시하고, 기본 harness의 strongest run이 약 30%를 회수했다고 보고했다. 그러나 이 결과는 단일 mono-repo, hidden LLM judge 및 독립 재평가 부재의 한계가 있어, 실제 코드 리뷰 자동화의 일반 성능으로 해석할 수 없다. [ReviewBench](https://www.langchain.com/blog/evaluating-code-review-agents-with-reviewbench) · [검증표 S09](verify/verification.md)

### 2.3 robustness 평가는 공격 조건과 배포 안전장치를 분리

OpenAI는 GPT-Red와 GPT-5.6 system card를 통해 공격 elicitation, direct-model robustness 및 production safety stack을 분리하는 평가 구조를 제시했다. 다만 GPT-Red의 scenario 성공률·개선 폭, GPT-5.6의 prompt-injection·정책 위반 수치는 모두 제공자 원문과는 일치하나 독립 재현이 확인되지 않았다. 내부 red-team을 운용한다면 threat model, authorization, 성공 정의, evaluator independence, 예산, production safeguard 포함 여부를 사전에 명시하는 것이 우선이다. [OpenAI GPT-Red](https://openai.com/index/unlocking-self-improvement-gpt-red) · [OpenAI system card](https://deploymentsafety.openai.com/gpt-5-6/evaluations-with-challenging-prompts) · [검증표 S02·S03](verify/verification.md)

### 2.4 보안 범위는 실행 경계와 평가환경까지 확장

IETF Internet-Draft는 agent security benchmark를 4개 1차 차원과 55개 2차 metric으로 구성해 access·memory·tool·execution·infrastructure·supply chain을 포괄하는 범위를 제안한다. 다만 해당 문서는 표준이 아닌 individual Internet-Draft이며, 100점 가중평균 및 Low/Medium/High 등급의 타당화도 확인되지 않았다. 따라서 범위 누락을 찾는 checklist 후보로만 사용할 수 있다. [IETF Datatracker](https://datatracker.ietf.org/doc/draft-han-bmwg-agent-security-benchmark/) · [IETF draft](https://www.ietf.org/archive/id/draft-han-bmwg-agent-security-benchmark-00.html) · [검증표 S08](verify/verification.md)

평가환경도 강한 containment가 필요하다는 적용 후보에는 NIST의 시스템 전반 통제 지침을 우선 근거로 사용해야 한다. Anthropic은 live internet 설정 오류가 있는 사이버보안 평가에서 세 조직의 production infrastructure에 무단 접근이 발생했다고 보고했다. 다만 Socket·Help Net Security 보도는 Anthropic 발표의 재서술이며, 피해 조직·평가 파트너의 직접 로그 또는 독립 공개는 이 근거 묶음에서 확인되지 않았다. 따라서 사건 범위와 141,006 runs·3 incidents·6 runs 등의 세부 계수는 모두 Anthropic 자기보고·**미검증**으로 한정한다. [Anthropic incidents](https://www.anthropic.com/news/investigating-incidents-cybersecurity-evals) · [Socket](https://socket.dev/blog/anthropic-claude-pypi-malware) · [Help Net Security](https://www.helpnetsecurity.com/2026/07/31/anthropic-claude-cybersecurity-incidents) · [검증표 S11](verify/verification.md)

## 3. 근거·수치 정리

| 항목 | 근거·수치 | 검증 상태와 해석 | 출처 |
|---|---|---|---|
| 예산 민감성 | UK AISI cyber range에서 10M→100M tokens 시 최대 59% 상승 | **확인**. 단일 fixed-budget 점수 해석의 한계 근거이며, 모든 benchmark의 증가 효과를 뜻하지 않는다. | [AISI 연구](https://www.aisi.gov.uk/research/measuring-ai-agents-progress-on-multi-step-cyber-attack-scenarios) · [검증표](verify/verification.md) |
| ReviewBench | 59 tasks, 64 baseline issues, strongest common-harness run 약 30% 회수 | **미검증**. LangChain의 단일 repo·LLM judge 조건 결과다. | [LangChain](https://www.langchain.com/blog/evaluating-code-review-agents-with-reviewbench) · [검증표](verify/verification.md) |
| WildClawBench | 60개 bilingual·multimodal task, native CLI harness, hybrid grading | **미검증**. preprint이며 독립 재실행이 확인되지 않았다. | [논문](https://arxiv.org/html/2605.10912v1) · [OpenTrain](https://www.opentrain.ai/papers/wildclawbench-a-benchmark-for-real-world-long-horizon-agent-evaluation--arxiv-2605.10912) |
| IETF 보안 framework | 4개 1차 차원, 55개 2차 metric | **범위는 확인**, 등급 calibration은 **미검증**. 표준이 아닌 draft다. | [IETF Datatracker](https://datatracker.ietf.org/doc/draft-han-bmwg-agent-security-benchmark/) · [검증표](verify/verification.md) |
| 평가환경 사고 | Anthropic은 세 조직 production infrastructure에 무단 접근이 발생했다고 보고 | **미검증**. 사건 범위와 세부 발생 계수는 Anthropic 자기보고다. Socket·Help Net Security는 이 발표를 재서술한 2차 보도이며, 피해 조직의 독립 로그·직접 확인은 제시되지 않았다. | [Anthropic](https://www.anthropic.com/news/investigating-incidents-cybersecurity-evals) · [Socket](https://socket.dev/blog/anthropic-claude-pypi-malware) · [Help Net Security](https://www.helpnetsecurity.com/2026/07/31/anthropic-claude-cybersecurity-incidents) · [검증표](verify/verification.md) |
| ARC-AGI-3 설정 사례 | OpenAI는 public set에서 13.3%→38.3%, output token 6x 감소를 보고 | **미검증**. OpenAI 자체 harness 비교이므로 context·harness 관리 민감성의 보조 사례로만 사용한다. | [OpenAI](https://openai.com/index/how-two-settings-tripled-our-arc-agi-3-scores) · [검증표](verify/verification.md) |

## 4. 시사점 및 적용 후보

1. **평가 run provenance card를 기본 산출물로 설정한다.** 동일 task에서 model과 함께 harness·도구·프롬프트·메모리·재시도·예산·grader를 기록하고, 가능하면 다예산 curve를 병기한다. 단일 점수로 모델 고유 성능이나 배포 성능을 단정하지 않는 운영 규칙이 필요하다. [AISI](https://www.aisi.gov.uk/blog/more-compute-more-capability-why-ai-agent-evals-need-to-account-for-test-time-compute) · [METR](https://metr.org/time-horizons) · [검증표 S01·S05](verify/verification.md)

2. **격리된 agent/eval 실행 baseline을 우선 구축한다.** NIST SP 800-228A의 strict schema·human approval·short-lived scoped token과 NIST IR 8596의 least privilege를 기본 통제로 삼고, Hugging Face 기술 타임라인이 제시한 strict isolation·narrow trust boundary·monitoring을 함께 검토한다. sandbox만으로 prompt injection이 제거되는 것은 아니므로, untrusted tool output이 context로 돌아오는 경로도 별도로 다뤄야 한다. 이 조합의 적용 효과는 본 자료에서 정량 검증되지 않았다. [NIST SP 800-228A](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-228A.ipd.pdf) · [NIST IR 8596](https://nvlpubs.nist.gov/nistpubs/ir/2025/NIST.IR.8596.iprd.pdf) · [Hugging Face technical timeline](https://huggingface.co/blog/agent-intrusion-technical-timeline) · [검증표 S13](verify/verification.md)

3. **owned resettable 업무 world와 state verifier를 소규모 파일럿으로 검토한다.** 실제 업무 상태, 허용 side effect, rollback 및 grader를 명세하고 synthetic world 평가와 native-runtime 시험을 분리한다. Microsoft의 성능 수치를 파일럿 ROI나 예상 개선폭으로 사용하지 않는다. [Microsoft Echoverse](https://www.microsoft.com/en-us/research/blog/echoverse-deep-evolving-environments-for-computer-use-agents/) · [검증표 S07·S10](verify/verification.md)

4. **실제 이력 기반 code-review·장기과업 benchmark를 작게 curate한다.** human-curated baseline, frozen context, deterministic checker 및 LLM judge calibration을 병행하고 precision과 coverage를 분리 측정한다. 외부 benchmark의 task 수나 순위를 일반 소프트웨어 생산성의 확정 수준으로 인용하지 않는다. [ReviewBench](https://www.langchain.com/blog/evaluating-code-review-agents-with-reviewbench) · [WildClawBench](https://arxiv.org/html/2605.10912v1) · [검증표 S07·S09](verify/verification.md)

5. **권한 높은 agent에는 controlled tabletop/stress test를 보조 게이트로 둔다.** 다만 fictional environment, alternative action을 포함한 control, classifier 검증 및 human oversight를 전제로 해야 하며, simulation의 harmful rate를 실배포 incident base rate로 환산하지 않는다. [Anthropic misalignment](https://www.anthropic.com/research/agentic-misalignment) · [METR frontier risk report](https://metr.org/blog/2026-05-19-frontier-risk-report) · [검증표 S04·S12](verify/verification.md)

## 5. 불확실성·반대근거·상충 지점

- **검증 게이트 미통과 상태:** Cross-Verify의 총괄 판정은 보완요청이다. 제공자·저자 자체 benchmark 수치, 신규 METR 지표, IETF score band는 독립 재현 또는 타당화 전까지 확정적 근거로 사용할 수 없다. [검증표 총괄](verify/verification.md)

- **Echoverse 수치 상충:** Online-Mind2Web 향상치가 같은 Microsoft 원문에서 `29.5→34.3` 및 `29.5→37.2`로 병존한다. BrowserBase 사용 여부·분모·설정을 해소하기 전 두 수치 모두 보고서 근거에서 제외했다. [Microsoft Echoverse](https://www.microsoft.com/en-us/research/blog/echoverse-deep-evolving-environments-for-computer-use-agents/) · [검증표 S10](verify/verification.md)

- **S14 Reader 노트의 근거 범위:** `analysis/openai-hf-evaluation-security-incident.md`는 빈 파일이 아니라 공식 RSS의 제목·발행일·고수준 설명과 본문 자동추출 한계를 기록한 노트다. 다만 RSS 수준의 보존본에는 incident의 원인·취약점·영향 범위·remediation·모델 행위에 관한 세부 claim이 없으므로, 이 보고서도 해당 OpenAI 자료를 세부 사고 기술이나 원인 연결의 근거로 사용하지 않는다. [S14 Reader 노트](analysis/openai-hf-evaluation-security-incident.md) · [OpenAI RSS 기반 원자료](raw/openai-hf-evaluation-security-incident.md) · [검증표 S14](verify/verification.md)

- **실제 사고와 simulation의 층위 차이:** Anthropic은 실제 평가 사고에서 모델이 자체 목표를 추구했다는 증거가 없다고 설명했다. 반면 agentic misalignment 연구는 선택지가 제한된 fictional simulation 결과다. 두 자료는 서로를 입증·반박하지 않으며, 실제 배포 발생률로 일반화할 수 없다. [Anthropic incidents](https://www.anthropic.com/news/investigating-incidents-cybersecurity-evals) · [Anthropic misalignment](https://www.anthropic.com/research/agentic-misalignment) · [검증표 S11·S12](verify/verification.md)

- **예산 민감성의 반례:** AISI는 fixed-budget 평가의 한계를 보고했지만, HealthBench에서는 통상 예산 범위에서 plateau가 관찰됐다. 추가 compute가 항상 성능 향상으로 이어진다는 식의 일반화는 근거 범위를 벗어난다. [AISI](https://www.aisi.gov.uk/blog/more-compute-more-capability-why-ai-agent-evals-need-to-account-for-test-time-compute) · [검증표 S05](verify/verification.md)

## 6. 출처 목록

1. [M-2026-002 수집 출처 목록](raw/sources.md) — 전체 17건(신규 10건, wiki 재사용 7건)의 출처 유형·수집일·원문 경로와 발행일 기록. 수집일은 모두 `2026-08-02`로 기록됐으나, WildClawBench·IETF는 월 단위 발행일이고 IBM·Anthropic 2건은 발행일이 `미확인`으로 남아 있다.
2. [M-2026-002 Cross-Verify 검증표](verify/verification.md) — 주장별 확인·상충·미검증 판정과 독립 대조.
3. [M-2026-002 Synthesis 종합 노트](synthesis/synthesis.md) — 성숙도 분류와 적용 후보의 입력 산출물.
4. [UK AISI — More compute, more capability](https://www.aisi.gov.uk/blog/more-compute-more-capability-why-ai-agent-evals-need-to-account-for-test-time-compute)
5. [UK AISI — Multi-step cyber attack scenarios](https://www.aisi.gov.uk/research/measuring-ai-agents-progress-on-multi-step-cyber-attack-scenarios)
6. [METR — Time horizons](https://metr.org/time-horizons)
7. [METR — Metrics of agent ability](https://metr.org/notes/2026-07-24-metrics-of-model-ability)
8. [NIST IR 8596](https://nvlpubs.nist.gov/nistpubs/ir/2025/NIST.IR.8596.iprd.pdf) 및 [NIST SP 800-228A](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-228A.ipd.pdf)
9. [IETF Agent Security Benchmark draft](https://www.ietf.org/archive/id/draft-han-bmwg-agent-security-benchmark-00.html)
10. [Microsoft Research — Echoverse](https://www.microsoft.com/en-us/research/blog/echoverse-deep-evolving-environments-for-computer-use-agents/)
11. [LangChain — ReviewBench](https://www.langchain.com/blog/evaluating-code-review-agents-with-reviewbench)
12. [WildClawBench preprint](https://arxiv.org/html/2605.10912v1)
13. [OpenAI — GPT-Red](https://openai.com/index/unlocking-self-improvement-gpt-red) 및 [GPT-5.6 system card](https://deploymentsafety.openai.com/gpt-5-6/evaluations-with-challenging-prompts)
14. [Anthropic — Cybersecurity evaluation incidents](https://www.anthropic.com/news/investigating-incidents-cybersecurity-evals)
15. [Anthropic — Agentic misalignment](https://www.anthropic.com/research/agentic-misalignment)
16. [Hugging Face — 2026-07 보안사고 공개](https://huggingface.co/blog/security-incident-july-2026) 및 [technical timeline](https://huggingface.co/blog/agent-intrusion-technical-timeline)
17. [OpenAI — ARC-AGI-3 설정 사례](https://openai.com/index/how-two-settings-tripled-our-arc-agi-3-scores)
