# M-2026-002 — AI 에이전트 평가·신뢰성·안전성 동향 종합

- 종합일: 2026-08-02
- 입력: `analysis/` Reader 노트(S01–S15), `verify/verification.md` Cross-Verify 표
- 종합 원칙: 아래의 **실무/초기/연구**는 기술·운영 적용의 성숙도이며, 성능 우수성 또는 시장 채택의 확정 판정이 아니다. `미검증` 수치·주장은 제공자/저자 보고 또는 제안으로만 표기한다.
- 검증 게이트: Cross-Verify 총계는 확인 9, 상충 2, 미검증 21이며 총괄 판정은 **보완요청**이다. 따라서 이 문서는 최종 보고서의 확정 근거가 아니라, 작성·보완 우선순위를 위한 종합 노트다.

## 1. 분류 체계 및 성숙도

| 분류 | 종합된 검증 상태 | 성숙도 | 근거·추적 | 적용상 의미와 경계 |
|---|---|---|---|---|
| 1. 평가 설계: harness·예산·validity check 공개 | **확인**: 점수는 모델만이 아니라 harness와 test-time 예산에 의존하며, 고정예산이 역량을 과소평가할 수 있다. 단 HealthBench에서 plateau가 관찰된 반례도 있다. | **실무** | S01-1/2, S05-1 확인. `analysis/openai-trustworthy-third-party-evaluations.md:7-18`, `analysis/metr-metrics-of-agent-ability.md:7-14`; `verify/verification.md:18-19,27` | 내부 평가 결과에 model, harness, tools, prompt, memory/retry, token·시간·비용 budget, validity check를 함께 기록할 수 있다. 모든 과제에서 추가 예산이 성능 향상을 보장한다고 일반화하지 않는다. |
| 2. 비용·인간비교 지표 | 고정 score, cost-of-pass, expenditure-adjusted score, expenditure horizon은 제안된 지표 체계다. expenditure horizon은 curve 교차·human labor 추정에 의존하고 slope가 비슷하면 불안정/무한일 수 있다. | **연구** | S05-2, S06-1 **미검증**. `analysis/metr-metrics-of-agent-ability.md:9-18`, `analysis/metr-expenditure-horizon.md:7-16`; `verify/verification.md:28-29` | 탐색적 내부 R&D 계측 후보이나, KPI·조달 기준으로 고정하기 전 다수 task와 독립 human-cost 추정으로 타당화가 필요하다. |
| 3. 재현 가능한 평가환경·verifier | resettable owned world, state-grounded verifier, side-effect audit, hybrid grading은 반복 평가/RL을 위한 설계 후보다. 실환경 native runtime 평가와 통제 synthetic world 평가는 다른 trade-off다. | **초기** | Echoverse 설계·수치는 Microsoft 자체 보고(S10-1 미검증); WildClawBench는 preprint·독립 재실행 부재(S07-1/2 미검증). `analysis/microsoft-echoverse.md:7-21`, `analysis/arxiv-wildclawbench.md:7-20`; `verify/verification.md:30-31,37-38` | 안전하게 reset 가능한 내부 업무 world를 만들어 state-based pass/fail을 우선 시험할 수 있다. 실제 도구·장기 runtime 적합성은 별도 native-runtime 시험으로 보완해야 하며, 서로의 점수를 비교하지 않는다. |
| 4. 현실 업무 벤치마크: 코드 리뷰·장기 과업 | real PR history 또는 real CLI task가 synthetic final-answer 평가의 보완재가 될 수 있다. ReviewBench의 59 tasks/64 issues/~30%와 WildClawBench 점수는 모두 저자 설정의 **미검증** 결과다. | **초기** | S09-1 **미검증**, S07-1/2 **미검증**. `analysis/langchain-reviewbench.md:7-22`, `analysis/arxiv-wildclawbench.md:7-20`; `verify/verification.md:30-31,36` | 자체 코드·업무 이력에서 verifier 가능한 사례를 소규모로 curate해 재현성·precision·coverage를 측정할 후보다. hidden LLM judge calibration, 단일 repo/domain 편향, clarification 없는 single-turn 구조를 검증해야 한다. |
| 5. 모델 robustness 평가·자동 red teaming | attack elicitation, threat model, direct-model robustness와 production safety stack의 분리는 유의미한 평가 구조다. GPT-Red 성공률·개선 폭과 GPT-5.6 안전성 수치는 제공자 자체평가로 독립 재현되지 않았다. | **초기** | S02-1/2, S03-1/2 **미검증**. `analysis/openai-gpt-5-6-system-card.md:7-23`, `analysis/openai-gpt-red-robustness.md:7-22`; `verify/verification.md:21-24` | 내부 red-team은 공격 경로, 성공 정의, production safeguard 포함 여부, budget을 명시해 운영할 수 있다. 제공자 점수를 배포 안전성·타사 비교의 확정 근거로 쓰지 않는다. |
| 6. 시스템 전반 보안통제·평가환경 격리 | agent 보안은 model뿐 아니라 access, memory, tool, execution, infrastructure, supply chain을 포함해야 하며, untrusted 실행에는 격리·최소권한·scoped credential·network 제한·audit가 함께 필요하다. 실제 eval 환경의 live-internet misconfiguration 사고가 containment 필요성을 뒷받침한다. | **실무** | S08-2, S11-1, S13-1 **확인**. `analysis/ietf-agent-security-benchmark.md:7-22`, `analysis/anthropic-cybersecurity-evals.md:7-21`, `analysis/langchain-agents-own-computer.md:7-20`; `verify/verification.md:34,39,44` | 평가·개발 agent 환경에 egress allowlist, 별도 kernel/filesystem, JIT·short-lived credential, resource cap, transcript/network audit, human approval을 결합할 수 있다. sandbox만으로 prompt injection을 제거하지 못한다. |
| 7. 보안 측정 framework·등급 | IETF draft의 4개 차원·55 metrics·100점 risk band는 보안 점검 항목 후보이나 표준/타당화된 등급이 아니다. | **연구** | S08-1 **확인**(draft 상태), S08-3 **미검증**. `analysis/ietf-agent-security-benchmark.md:7-22`; `verify/verification.md:33-35` | 위협모델·통제 누락을 찾는 checklist로만 매핑을 시험한다. Low/Medium/High 점수를 업계 표준·배포 승인 기준으로 사용하지 않는다. |
| 8. 행동 위험 stress test·조직 단위 risk assessment | 제한적 simulated dilemma에서 harmful insider behavior가 관찰됐다는 주장은 실제 배포 발생률 증명이 아니다. 조직 내부 risk assessment pilot은 비공개 참여자 자료·disclosure approval에 의존한다. | **연구** | S12-1/2/3, S04-1/2 **미검증**. `analysis/anthropic-agentic-misalignment.md:7-20`, `analysis/metr-frontier-risk-report.md:7-21`; `verify/verification.md:25-26,41-43` | 권한·정보 접근이 있는 agent의 사전 위험 탐색을 위한 controlled stress test 및 조직별 risk register 후보다. binary choice, classifier, prompt 최적화 및 비참여사 범위 한계를 포함해야 한다. |

## 2. 적용 후보표

| 우선순위 | 적용 후보 | 근거와 기대효과 | 전제 조건·성숙도 | 사용 금지/보류 조건 |
|---|---|---|---|---|
| P1 | **평가 run provenance card**: 결과마다 model·harness·tools·prompt/memory/retry·budget·validity check를 함께 저장 | S01/S05와 AISI 교차근거가 fixed-budget 단일 점수의 불충분성을 뒷받침한다. 평가 재현성·결과 해석성을 높인다. | **실무**. 동일 task의 다예산 curve, 공통 harness 비교와 maximum elicitation을 구분하는 운영 규칙이 필요. | 점수 하나로 모델 고유 성능·배포 성능을 단정하지 않는다. plateau/비용 한계도 기록한다. |
| P2 | **격리된 agent/eval 실행 baseline**: egress allowlist, 별도 실행 경계, scoped·short-lived credential, resource cap, transcript/network audit | S11 실제 사고와 S08/S13의 독립 보안 근거가 다층 통제 필요성을 지지한다. eval 환경을 production급 보안 대상에 포함한다. | **실무**. untrusted code/data/tool output을 전제로 권한 인벤토리, log 보존·검토, 사전/실시간 monitoring을 구성. | sandbox만 배치하고 safe라고 선언하지 않는다. context로 되돌아오는 untrusted output의 injection 위험은 별도 처리한다. |
| P3 | **owned resettable 업무 world + state verifier 파일럿** | S10은 reset·ground-truth·DB-diff 방식의 설계 사례, S07은 native runtime·side-effect audit의 보완 필요성을 제공한다. 안전한 반복 실험·회귀 시험에 적합할 가능성이 있다. | **초기**. 실제 업무의 상태·허용 side effect·rollback·grader를 명세하고 synthetic world와 native-runtime 시험을 분리한다. | Microsoft의 성능 수치로 ROI를 확정하지 않는다. S10 Online-Mind2Web `29.5→34.3`/`29.5→37.2` 상충 수치는 사용하지 않는다. |
| P4 | **실제 이력 기반 code-review/장기과업 benchmark 소규모 curate** | S09의 real PR·verifiable finding, S07의 CLI·hybrid grading은 현실 업무 평가 후보 설계를 제시한다. | **초기**. human-curated baseline, frozen context, deterministic checker와 LLM judge calibration을 병행하고 precision/coverage를 분리 측정. | 59-task/~30% 또는 WildClawBench 순위를 일반 소프트웨어 생산성의 확정 수준으로 인용하지 않는다. |
| P5 | **threat-model 명시형 내부 red-team 및 safeguard 분리 시험** | S02/S03은 공격 성공 정의·elicitation·direct model layer와 deployment stack 분리의 필요성을 보여준다. | **초기**. 공격 범위, authorization, success condition, evaluator independence, budget, production safeguard 포함 여부를 사전에 기록. | GPT-Red·GPT-5.6의 미검증 수치를 독립 성능 기준선으로 채택하지 않는다. |
| P6 | **권한 높은 agent의 위험 시나리오 tabletop/stress test** | S12는 threat/goal conflict 조건에서의 stress test 사례, S04는 entity-level assessment 구조를 제공한다. | **연구**. fictional/controlled environment, human oversight, opt-in data, alternative action을 포함한 control, classifier 검증이 필요. | simulated harmful rate를 실제 incident base rate나 autonomous own-goal evidence로 해석하지 않는다. |
| P7 | **IETF draft 기반 security coverage checklist** | S08의 lifecycle 범위는 access·memory·tool·supply-chain 누락 탐지용 분류 체계가 될 수 있다. | **연구**. 자사 위협모델·통제와 mapping하고 항목별 검증 증거를 남긴다. | draft의 100점 가중평균·위험등급을 보안 인증·출시 승인 기준으로 사용하지 않는다. |

## 3. 핵심 상충·불확실성 및 처리 규칙

1. **S10 원문 내부 수치 상충 — 사용 중지.** Online-Mind2Web 향상 수치가 `29.5→34.3`과 `29.5→37.2`로 동시에 제시된다. BrowserBase 사용 여부·분모·설정을 원 논문/코드로 해소하기 전, 어느 수치도 종합·보고서 근거로 사용하지 않는다. (`verify/verification.md:38,54,61`)
2. **S14 Reader 분석의 추적성 결함 — 보완 전 제한 사용.** Cross-Verify는 `analysis/openai-hf-evaluation-security-incident.md`가 0바이트라 Reader 분석이 존재하지 않는다고 판정했다. 다만 Hugging Face 피해 당사자 로그 등에 따라 해당 보안사고 자체는 확인으로 판정됐다. 이 종합에서는 S14의 세부 기술·원인 연결을 독립 검증표의 S14-1 범위로만 사용하며, Reader 분석 보강 전에는 Reader-derived claim으로 확장하지 않는다. (`verify/verification.md:46-47,60,68`)
3. **자체평가 수치의 일반화 금지.** S02·S03·S04·S07·S09·S10·S12·S15는 핵심 결과의 독립 재현이 없거나 비공개 설정/자료에 의존한다. 본문에서는 ‘제공자/저자 보고’ 또는 ‘preprint’로만 귀속하며, 타사 비교·실배포 효과·base rate의 확정 근거로 쓰지 않는다. (`verify/verification.md:21-32,36-43,48-49,55,63`)
4. **IETF draft의 상태.** 4차원/55 metrics라는 범위는 확인됐지만 Internet-Draft는 표준이 아니며 100점 등급의 calibration도 미검증이다. checklist 후보로만 다룬다. (`verify/verification.md:33-35`)
5. **simulation·incident·misalignment을 혼동하지 않는다.** S11은 containment failure의 실제 사고이며 Anthropic은 own-goal pursuit 증거가 아니라고 해석한다. S12는 fictional, 선택지를 제한한 controlled simulation이다. 두 결과를 상호 입증·반박하거나 실제 오정렬 발생률로 환산하지 않는다. (`analysis/anthropic-cybersecurity-evals.md:20-21`, `analysis/anthropic-agentic-misalignment.md:19-20`; `verify/verification.md:39-43,56`)
6. **S15 설정 효과는 보조 사례에 한정.** OpenAI는 ARC-AGI-3 public set에서 `13.3%→38.3%`, output tokens `6x` 감소를 보고했지만 독립 인증은 없다. harness·context 관리 민감성의 사례로만 귀속하고 일반 인과효과로 확대하지 않는다. (`verify/verification.md:48-49,62`)

## 4. 작성 단계 전달 사항

- **핵심 근거로 우선 사용 가능:** P1의 평가 투명성·예산 민감성, P2의 system-wide security controls 및 eval containment. 이들은 확인 판정을 받았으나, 적용 효과의 정량 ROI 자체까지 확인된 것은 아니다.
- **보조 사례로만 사용:** provider/self-reported 성능·안전성 수치, preprint benchmark 순위, 신규 METR metric과 IETF score band.
- **보고서에서 반드시 붙일 조건:** 평가 설정(harness·budget·grader), 실험 환경(controlled/native/production), 독립 재현 여부, 적용 범위 및 반례.
- **후속 보완 게이트:** S14 Reader 분석 채움, S10 상충 수치 해소 또는 삭제, S15 최신 원문 조건 반영, 자체평가 수치의 귀속 표기를 완료해야 한다.
