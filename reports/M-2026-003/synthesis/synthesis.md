# M-2026-003 — Synthesis: AI 에이전트 메모리·컨텍스트 관리

> 단계 7 Synthesis · 입력: Reader 분석 12건, `verify/verification.md` (6R2 `VERDICT: PASS`)

## 1. 판정 범위

- Cross-Verify의 기준 상태는 **확인 20, 상충 0, 미검증 14**이다. `PASS`는 미검증 항목의 성격·사용 제한을 공개한 조정 게이트 판정이다. 미검증이 확인된 사실이 되었다는 뜻은 아니다. [검증: `verify/verification.md` 판정·§6R2]
- 성숙도: **연구**=방법/평가 제안 또는 독립 재현 부재, **초기**=구현·운영 관행은 있으나 일반화·비교효과 제한, **실무**=현재 적용 가능한 명확한 운영·거버넌스 절차. 실무는 보편적 성능 우위를 뜻하지 않는다.

## 2. 기술 분류와 성숙도

| 분류 | 기술/메커니즘 | 성숙도 | 근거와 경계 | 추적 경로 |
|---|---|---|---|---|
| A. 장기기억 평가 | 장기 대화·증분 상호작용 평가(LoCoMo, LongMemEval, MemoryAgentBench) | 연구 | LoCoMo의 과업/규모(평균 300턴·9K 토큰·최대 35세션), LongMemEval의 5개 능력·500문항, MemoryAgentBench의 incremental multi-turn 형식은 확인됐다. 벤치마크 단위·과업이 달라 점수 직접 비교는 금지한다. MemoryAgentBench는 arXiv v4의 `selective forgetting`과 현행 README의 `Conflict Resolution`이 다르므로 문서·commit 고정이 필요하다. | 분석 `01`,`02`,`04`; 검증 01-2,02-1,04-1,04-2 |
| B. 구조화·진화형 메모리 | note/link, dynamic indexing, memory evolution(A-MEM); skill/insight, consolidation, weighting(EvoLib) | 연구 | 두 메커니즘은 확인됐다. A-MEM의 6개 모델 SOTA 우위와 EvoLib의 token 효율 우위는 독립 재현이 없어 채택 근거가 아닌 탐색 가설이다. 저장 단위·갱신 규칙·평가 조건의 동등성도 미확인이다. | 분석 `03`,`07`; 검증 03-1~03-3,07-1~07-3 |
| C. 컨텍스트 구성·검색 | 고신호 context, just-in-time/progressive disclosure, session·key·query 검색 분해 | 초기 | 긴 입력에서 정보 활용 성능 저하 방향과 context 관리 병목은 독립 지지된다. LongMemEval의 분해와 확장 기법의 개선은 저자 보고이므로 특정 검색 조합의 우위는 확정하지 않는다. | 분석 `02`,`05`; 검증 02-2~02-3,05-1~05-2 |
| D. 컨텍스트 수명주기·장기 실행 | compaction, 구조화 노트, progress artifact, session handoff, 역할 분리 | 초기 | 새 세션의 prior state 상실과 단순 압축의 세부 근거 손실은 확인됐다. 상태 전달 artifact는 적용 가능하지만, compaction·구조화 노트·sub-agent의 상대 적합성과 ‘한 feature씩’의 효과는 비교 검증되지 않은 vendor 권고다. | 분석 `05`,`06`; 검증 05-3,06-1~06-3 |
| E. Harness token 예산 | prompt/tool schema 축소, middleware 선택 적용, summarization trigger | 초기 | Deep Agents v0.7의 base input 6K→2K(약 65%)와 세 변경점은 대조됐다. reward CI가 모든 모델에서 0을 포함하므로 성능 동등/향상은 입증되지 않았다. | 분석 `08`; 검증 08-1~08-3 |
| F. 메모리 보안·프라이버시 | persistent/distributed memory 위험, compartment, purpose tag, audit, dashboard/retention | 초기 | 장기기억의 cross-session poisoning·비인가 접근 위험 방향은 독립 지지된다. dashboard·retention·memory-free mode는 정책 제안이며 통제 효과는 미검증이다. MCP authorization 존재와 identity/delegation/fine-grained policy의 잔여 과제는 분리한다. | 분석 `10`; 검증 10-1~10-3 |
| G. 거버넌스·위험관리 | NIST AI 600-1의 Govern/Map/Measure/Manage, use별 risk assessment | 실무 | 조직·용도별 적용 판단을 전제한 risk-management 틀로 활용 가능하다. memory 성능 비교나 특정 safeguard 효과의 실증 근거는 아니다. | 분석 `11`; 검증 11-1~11-3 |
| H. Agent security benchmark 제안 | memory poisoning·isolation·deletion/integrity를 포함한 4차원·55 metric IETF draft | 연구 | individual Internet-Draft의 제안 내용으로만 원문 일치가 확인됐다. 독립 구현·재현·test case/reproducibility 근거가 없어 확정 표준·검증 benchmark가 아니다. | 분석 `12`; 검증 12-1~12-3 |

## 3. 적용 후보·전제 조건

| 우선 | 후보 | 근거·전제 조건 | 보류/불확실성 |
|---:|---|---|---|
| 1 | **세션 handoff artifact 기본화**: 목표·결정·미해결 항목·trace·검증 상태를 구조화해 다음 세션에 전달 | 새 세션의 상태 상실과 단순 압축 한계가 확인됐다. ownership, 갱신 시점, stale 처리, 재개 시 검토를 정의하고 완료율·재작업·결정 누락으로 관찰한다. [06-1,06-2] | artifact의 최적 형식/양과 ‘한 feature씩’의 효과는 미검증 권고(05-3,06-3). |
| 2 | **고신호·점진적 context retrieval baseline** | 식별자 기반 보관과 필요 시 읽기를 적용하고 retrieval 단위·권한·freshness·fallback을 명시한다. recall·근거 누락·토큰·지연을 함께 측정한다. [05-1,05-2] | LongMemEval의 특정 index/key/query 확장 우위는 독립 재현 없음(02-2,02-3). |
| 3 | **단일 점수 대신 과업 축별 memory 평가** | retrieval, multi-session/temporal reasoning, update, abstention 등 내부 scenario별 test set·기준선·비용·지연을 기록한다. [01-2,02-1,04-1] | 세 벤치마크 점수 직접 비교 금지. MemoryAgentBench의 문서/commit 고정 필요. |
| 4 | **consolidation 소규모 실험**: raw log와 재사용 insight/skill 분리 | 원문 evidence 보존, 승격 기준·승인자·rollback·provenance를 둔 내부 비교 실험을 한다. [03-1,03-2,07-1,07-2] | A-MEM/EvoLib 성능·비용 우위는 독립 재현 없음(03-3,07-3). |
| 5 | **Harness token budget 점검** | 중복 prompt/tool description을 측정하고 middleware를 과업별 opt-in으로 평가한다. 변경 전후 동일 과업의 base token·cost·품질 CI를 기록한다. [08-1~08-3] | 65%는 특정 제품의 관찰값이며 목표값/보장으로 쓰지 않는다. reward 유의차 미확정. |
| 6 | **NIST 절차에 memory data-flow 위험검토 연결** | 저장·검색·공유·삭제별 expected/acceptable use, 보존기간, access 목적, audit 책임, incident 대응을 문서화한다. [11-1,11-2] | NIST action 자체는 safeguard 효과의 실증이 아님(11-3). |
| 7 | **민감/공유 memory 통제 pilot** | 데이터 분류·동의·authorization scope·삭제/복구 정책과 공격/오남용 test·운영부담을 함께 평가한다. [10-1] | dashboard·retention·memory-free mode는 정책 제안이며 효과 미검증(10-3). |
| 8 | **IETF draft를 내부 threat-model checklist 참고로만 사용** | 내부 test case·pass/fail 정의와 draft 버전·날짜를 별도 기록한다. | 55 metric/점수는 미검증 제안이며 표준·외부 인증 기준으로 사용 금지(12-1~12-3). |

## 4. 상충·불확실성

### 해소된 상충과 재발 방지

1. **MemoryAgentBench 용어**: 보존된 arXiv v4는 `selective forgetting`, 현재 GitHub/Hugging Face README는 `Conflict Resolution`을 쓴다. 현재 판정은 전자를 보존본의 저자 정의로 한정한다. 구현·인용은 문서와 commit/version을 고정한다. [분석 `04`; 검증 04-2, §수치·정의·버전 점검 1]
2. **MCP authorization 범위**: New America의 ‘lack’은 저자 문제 제기다. 최신 authorization 명세의 존재와 identity·upstream delegation·fine-grained policy의 별도 과제를 분리한다. ‘authorization이 없다’와 ‘authorization이 있으니 모든 통제가 해결됐다’ 모두 단정하지 않는다. [분석 `10`; 검증 10-2, §수치·정의·버전 점검 2]

### 미검증 14건의 상태 보존

| 성격 | ID | 허용 표현 | 금지하는 승격 |
|---|---|---|---|
| 저자/제공자 성능·숙달 보고 | 02-2, 02-3, 03-3, 04-3, 07-3 | 저자 보고·독립 재현 없음·실험 가설 | 일반 성능 사실·설계 우위·목표 성능치 |
| 문헌 범위·운영/정책·내부 절차 | 01-1, 05-3, 06-3, 09-2, 10-3 | 문제 제기·운영 권고·정책 제안·기관 자기보고 | 인과효과·최선 관행·독립 감사 절차 |
| 유일 1차 문서의 제안 | 11-3, 12-1, 12-2, 12-3 | 문서가 제안/나열한 항목 | 검증 benchmark·확정 표준·safeguard 효과 |

## 5. Writer 인계용 경계

- 중심 결론은 (a) memory/context 평가는 과업 축별로 분해하고, (b) 장기 실행에서는 상태·근거 전달을 운영물로 다루며, (c) persistent memory는 성능 논의와 분리된 privacy/security·governance 검토가 필요하다는 수준으로 제한한다.
- LoCoMo의 300턴·9K 토큰·35세션, LongMemEval의 5개 능력·500문항, Deep Agents의 6K→2K는 각각의 출처·조건에 귀속한다. LongMemEval 30% 저하, A-MEM/EvoLib 우위는 같은 문장에 ‘독립 재현 없음’을 유지한다.
- IETF는 비승인 연구적 제안, NIST는 use별 적용을 전제한 risk-management profile, New America는 정책 제안으로 구분한다.

## 6. 추적성

- Reader: `analysis/README.md`, `analysis/01-*.md`~`analysis/12-*.md`
- 검증 상태의 단일 기준: `verify/verification.md`
- 본 노트는 위 입력을 새로 검증하지 않고 분류·성숙도·적용 전제로 재구성했다.
