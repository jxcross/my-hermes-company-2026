# 사용자 질문

```
hermes agent를 이용하여 ai native company를 만들려고한다.
처음엔 사람인 나와 대화할 수 있는 대표 ai 에이전트로 시작하여 슬랙을 통해 대화하면서 업무를 해결하고자 한다. 아주 중요한 개인정보나 보란과 같은 문제에 대한 승인 결정외에  최대한 인간의 간섭을 최소화하고 ai 스스로 판단하여 미션을 완성한다. hermes agent에서 제공하는 profile 기능 사용도 고려한다. llm wiki 고 구축하여 미션이 주어지거나 할일이 없을 때에도 웹사이트에 공새된 자료를 수집하여 지식을 지속적으로 축적하고, 미션 수행시 필요 지식을 선행적으로 제공 받을 수도 있다. 내가 관심있는 미션은 논문이나 기술동향 파악, 웹 기반 프로그램 개발, 학술 논문 작성 등이다.
```

-----------


## 제안 방향: “대표 AI 한 명”에서 시작하는 AI-Native Company

처음부터 여러 AI 직원을 만드는 것보다, **사용자와 Slack에서 대화하는 대표 AI 에이전트 하나**를 먼저 만들고, 대표가 필요에 따라 전문 에이전트를 호출하도록 구성하는 것이 좋습니다.

Hermes Agent는 Slack 같은 메시징 채널, 지속 메모리, skills, subagent 위임, 브라우저·터미널 실행, 예약 작업을 하나의 에이전트 코어에서 지원하므로 이 구조의 출발점으로 적합합니다. ([GitHub][1])

---

# 1. 전체 개념

```text
┌──────────────────────────────────────────────────────────────┐
│                         사람: CEO                            │
│                                                              │
│  - 회사의 방향과 최종 목표 제시                              │
│  - 개인정보·보안·비용·대외 공개 승인                         │
│  - 중요한 연구 방향 및 최종 결과 판단                        │
└──────────────────────────────┬───────────────────────────────┘
                               │ Slack
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                  대표 AI 에이전트: Chief AI                  │
│                                                              │
│  - 사람과 대화하는 유일한 기본 창구                          │
│  - 미션 해석 및 목표 구체화                                  │
│  - 작업계획 수립                                             │
│  - 전문 에이전트 구성·호출                                   │
│  - 진행상황·비용·위험 관리                                   │
│  - 결과 검증 및 최종 보고                                    │
└───────────────┬───────────────────────┬──────────────────────┘
                │                       │
          미션 수행팀               지속 학습팀
                │                       │
       ┌────────▼────────┐      ┌──────▼───────────┐
       │ Research Agents │      │ Knowledge Curator│
       │ Coding Agents   │      │ Web Scout        │
       │ Writing Agents  │      │ Wiki Compiler    │
       │ Review Agents   │      │ Contradiction QA │
       └────────┬────────┘      └──────┬───────────┘
                │                      │
                └──────────┬───────────┘
                           ▼
                ┌─────────────────────┐
                │      LLM Wiki       │
                │                     │
                │ 원자료 / 논문 / 코드 │
                │ 구조화된 지식 문서   │
                │ 출처·근거·상충 정보  │
                │ 프로젝트 수행 이력   │
                │ 재사용 가능한 Skill │
                └─────────────────────┘
```

핵심 원리는 다음과 같습니다.

> **사람은 목표와 경계조건을 결정하고, AI는 계획·조사·구현·검증·정리를 수행한다.**

---

# 2. Hermes Profile을 어떻게 사용할 것인가

Hermes의 profile은 단순한 역할 프롬프트가 아닙니다. 각 profile은 독립적인 `config.yaml`, `.env`, `SOUL.md`, 세션, 메모리, 로그, cron 작업, gateway 상태 등을 가집니다. 따라서 각각을 독립된 AI 직원 또는 부서처럼 운영할 수 있습니다. ([GitHub][2])

다만 초기에는 profile을 많이 만들지 않는 것이 좋습니다.

## 1단계: 대표 profile 하나

```text
Profile: chief-ai
```

포함 요소:

```text
chief-ai/
├── SOUL.md
├── config.yaml
├── .env
├── memory/
├── skills/
├── sessions/
├── cron/
└── workspace/
```

`SOUL.md`에는 대표 AI의 정체성과 행동 원칙을 정의합니다.

```markdown
# Identity

너는 AI-Native Company의 대표 AI다.

# Mission

사용자가 제시한 목표를 분석하고,
최소한의 인간 개입으로 실행 가능한 미션으로 전환한다.

# Operating principles

1. 목표가 명확하면 추가 질문 없이 실행한다.
2. 불확실한 세부사항은 합리적인 가정을 세우고 기록한다.
3. 조사, 구현, 검토를 동일 에이전트가 단독으로 완료하지 않는다.
4. 모든 중요한 주장에는 출처를 남긴다.
5. 재사용 가능한 지식은 LLM Wiki와 skill로 축적한다.
6. 보안, 개인정보, 유료 결제, 외부 공개는 사람의 승인을 받는다.
7. 실패하면 원인을 분석하고 다른 방법으로 재시도한다.
8. 완료 기준이 충족될 때까지 미션을 종료하지 않는다.
```

## 2단계: 전문 profile 분리

업무가 반복되기 시작하면 다음과 같이 분리합니다.

| Profile         | 역할                   |
| --------------- | -------------------- |
| `chief-ai`      | 대표, 사용자 대화, 미션 총괄    |
| `research-lab`  | 논문 조사, 기술동향 분석       |
| `software-lab`  | 웹 프로그램 설계·개발·테스트     |
| `paper-lab`     | 학술논문 구성·집필·교정        |
| `knowledge-lab` | 웹 자료 수집, LLM Wiki 관리 |
| `audit-lab`     | 결과 검증, 출처·보안·품질 검사   |

Hermes는 한 시스템에서 여러 profile을 운영할 수 있고, 각각 별도 세션·메모리·비밀정보를 유지할 수 있습니다. profile distribution을 사용하면 성격, skills, cron 작업, MCP 연결, 설정을 Git 저장소 형태로 패키징할 수도 있습니다. ([GitHub][3])

### 권장 원칙

```text
Profile = 독립된 장기 정체성·메모리·권한이 필요한 조직 단위
Subagent = 특정 미션에서 일시적으로 구성되는 작업자
Skill = 반복 가능한 업무 절차
Tool = 실제 행동 수단
```

예를 들어 기술동향 보고서를 만들 때마다 `trend-agent` profile을 새로 만들 필요는 없습니다.

```text
chief-ai
  └─ research-lab profile
       ├─ 검색 subagent
       ├─ 논문 분석 subagent
       ├─ 중복 제거 subagent
       └─ 검증 subagent
```

---

# 3. Slack 운영 구조

Hermes Gateway는 Slack과 연결할 수 있으며 Socket Mode를 이용하면 외부에 공개된 webhook URL 없이 WebSocket 방식으로 Slack 앱을 연결할 수 있습니다. Hermes는 하나의 gateway에서 여러 Slack workspace 연결도 지원합니다. ([GitHub][4])

## 초기 Slack 구성

```text
#ai-ceo
사용자와 대표 AI가 대화하는 기본 채널

#mission-control
미션 상태, 작업계획, 진행률, 결과 보고

#approvals
보안·비용·외부 공개 등 사람의 승인이 필요한 요청

#research
논문 및 기술동향 조사 결과

#development
개발 작업, 테스트, 배포 진행

#knowledge
새로 축적된 위키 지식과 출처

#alerts
실패, 보안 문제, 비용 초과, 충돌 정보
```

그러나 초기에는 채널을 너무 많이 만들지 않고 다음 세 개만 사용해도 됩니다.

```text
#ai-ceo
#approvals
#mission-log
```

## 대화 예시

사용자:

```text
최근 3개월간 Agentic AI 연구 동향을 조사하고,
우리 연구단에서 활용할 만한 기술을 정리해줘.
```

대표 AI:

```text
미션 M-2026-031을 시작합니다.

목표:
- 최근 3개월의 주요 논문과 기술 발표 수집
- 중복 주제 통합
- 기술 성숙도와 적용 가능성 평가
- 우리 환경에 적용 가능한 후보 5개 선정

자동 수행:
- 자료 검색
- 논문 분류
- 핵심 내용 분석
- 교차 검증
- 보고서 작성
- LLM Wiki 반영

승인 필요 예상:
- 없음

완료 시 최종 보고서와 위키 변경사항을 제출하겠습니다.
```

이후 일반적인 진행은 AI가 스스로 처리하고, 사람에게는 예외 상황만 전달합니다.

---

# 4. 인간 승인 범위

“중요한 개인정보나 보안 문제 외에는 자율적으로 판단한다”는 방향은 좋지만, 승인 기준을 좀 더 명확하게 정의해야 합니다.

## 사람의 승인이 필요한 작업

| 분류     | 사례                               |
| ------ | -------------------------------- |
| 개인정보   | 사람의 이메일·전화번호·인사정보 사용             |
| 보안     | 서버 계정 생성, 방화벽 변경, 비밀키 접근         |
| 비용     | 유료 API 등록, 클라우드 자원 증설, 구매        |
| 외부 공개  | 논문 제출, GitHub 공개, SNS 게시, 이메일 발송 |
| 파괴적 작업 | DB 삭제, 운영 배포, 파일 대량 삭제           |
| 법적 약속  | 계약, 라이선스 선택, 저작권 관련 결정           |
| 전략 변경  | 프로젝트 목표 또는 연구 방향의 중대한 변경         |

## AI가 자율 결정할 수 있는 작업

```text
- 공개 웹 자료 검색
- 공개 논문 다운로드 및 요약
- 기술 비교
- 코드 작성
- 로컬 테스트
- 테스트용 컨테이너 실행
- 문서 초안 작성
- Git 브랜치와 커밋 생성
- 내부 위키 업데이트
- 실패 원인 분석 및 재시도
- 하위 에이전트 선택
- 일정과 작업 순서 조정
```

## 승인 요청 형식

```text
[승인 요청 A-042]

행동:
운영 서버에 신규 Docker 컨테이너 배포

필요한 이유:
완성된 논문 검색 서비스를 내부 사용자가 시험해야 함

영향:
- 포트 8084 사용
- CPU 최대 2코어
- 메모리 최대 4GB
- 외부 공개 없음

위험:
기존 서비스와 포트 충돌 가능성 낮음

복구:
docker compose down으로 즉시 제거 가능

권고:
승인

선택:
[승인] [거부] [수정 요청]
```

승인이 필요한 행동을 막연하게 묻지 않고, **행동·이유·영향·위험·복구 방법**을 함께 제시해야 합니다.

---

# 5. 미션 실행 상태 모델

대표 AI가 단순히 대화만 하는 봇이 되지 않도록 모든 업무를 “미션” 단위로 관리합니다.

```text
PROPOSED
   ↓
PLANNING
   ↓
RESEARCHING
   ↓
EXECUTING
   ↓
VERIFYING
   ↓
DELIVERING
   ↓
ARCHIVING
   ↓
COMPLETED
```

예외 상태:

```text
WAITING_APPROVAL
BLOCKED
RETRYING
FAILED
CANCELLED
```

각 미션에는 다음 정보가 있어야 합니다.

```yaml
mission_id: M-2026-031
title: Agentic AI 기술동향 조사
requested_by: human-ceo
objective: 최근 3개월 기술동향 및 적용 후보 선정
status: researching

constraints:
  - 공개 자료만 사용
  - 유료 API 사용 금지
  - 출처가 없는 주장은 제외

deliverables:
  - trend-report.md
  - paper-list.csv
  - recommendation.md
  - wiki-updates/

completion_criteria:
  - 주요 논문 30편 이상 검토
  - 독립 출처로 핵심 주장 교차 검증
  - 적용 후보 5개 선정
  - 모든 결과에 출처 포함

approval_policy:
  external_publish: required
  paid_api: required
  local_code_execution: autonomous
```

핵심은 **“무엇을 했는가”가 아니라 “완료 조건이 충족되었는가”로 미션을 종료하는 것**입니다.

---

# 6. LLM Wiki 구조

LLM Wiki는 단순한 문서 저장소나 일반 RAG 데이터베이스가 아닙니다.

기본 흐름은 다음과 같습니다.

```text
웹페이지·논문·PDF·코드
        ↓
원문 보존
        ↓
내용 추출 및 정규화
        ↓
기존 지식과 비교
        ↓
중복 통합·상충 정보 표시
        ↓
구조화된 Wiki 문서 갱신
        ↓
미션 수행 시 선행 지식으로 제공
```

Karpathy의 LLM Wiki 패턴을 구현한 사례들은 원자료를 `raw/`에 보관하고, 이를 구조화된 `wiki/` 문서로 컴파일하며, 새로운 자료가 들어오면 요약·상호 링크·색인·상충 관계를 갱신하는 방식을 사용합니다. ([GitHub][5])

## 권장 디렉터리

```text
llm-wiki/
├── purpose.md
├── sources/
│   ├── papers/
│   ├── websites/
│   ├── repositories/
│   └── internal/
├── raw/
│   ├── 2026/
│   └── metadata/
├── wiki/
│   ├── concepts/
│   ├── technologies/
│   ├── people/
│   ├── organizations/
│   ├── projects/
│   ├── methods/
│   └── comparisons/
├── reflections/
│   ├── technology-directions/
│   ├── research-opportunities/
│   └── lessons-learned/
├── missions/
│   └── M-2026-031/
├── claims/
├── contradictions/
├── indexes/
└── inbox/
```

## 세 가지 지식 계층

### ① Raw knowledge

원문과 원문 메타데이터입니다.

```text
논문 PDF
웹페이지 snapshot
GitHub README
기술 블로그
프로젝트 결과
실험 로그
```

### ② Compiled knowledge

여러 출처에서 공통적으로 확인된 지식입니다.

```markdown
# Agent Memory Architectures

## 정의

## 주요 접근법

## 대표 구현

## 장점

## 한계

## 상충하는 견해

## 적용 사례

## 관련 개념

## 출처
```

### ③ Reflection knowledge

조직의 장기적인 판단과 통찰입니다.

```markdown
# 우리 조직에서 장기 메모리를 도입할 때의 판단

현재까지의 증거를 종합하면...

적합한 조건:
- ...

부적합한 조건:
- ...

향후 재검토 조건:
- ...
```

이 계층이 중요합니다. 논문 요약만 쌓으면 “자료 창고”가 되지만, reflection이 쌓이면 **회사의 판단 능력**이 축적됩니다.

---

# 7. 할 일이 없을 때의 자율 학습

Hermes는 cron 작업을 통해 자연어 또는 cron 표현식으로 예약 작업을 실행할 수 있습니다. gateway의 scheduler가 주기적으로 실행할 작업을 확인하는 구조입니다. ([GitHub][6])

하지만 “할 일이 없으면 인터넷을 탐색하라”처럼 무제한 자율 행동을 허용하면 비용과 품질 문제가 생깁니다.

따라서 **Idle Mission Queue**를 둡니다.

## 자율 학습 우선순위

```text
1. 기존 미션에서 부족했던 지식 보완
2. 사용자가 지정한 관심 분야의 최신 논문 탐색
3. 기존 Wiki 문서의 오래된 정보 검증
4. 상충된 주장 재조사
5. 출처가 하나뿐인 중요 주장 교차 검증
6. 기존 프로젝트 코드와 문서 정리
7. 반복 업무를 skill로 변환
8. 장기 연구 아이디어 발굴
```

## 예시 예약 작업

```text
매일 06:00
- 관심 분야별 신규 논문 검색
- 기존 자료와 중복 확인
- 후보 자료를 inbox에 저장

매일 07:00
- 신뢰도 높은 자료만 Wiki에 반영
- 변경 내용과 근거 기록

매주 월요일
- 지난주 기술 변화 요약
- 주목할 연구 주제 5개 선정

매주 금요일
- 완료 미션 분석
- 반복된 작업을 skill 후보로 추출
- 실패 패턴과 개선안을 reflection에 기록

매월 1일
- 오래된 Wiki 문서 검토
- 기술 전망과 연구 우선순위 재평가
```

## 자율 수집 제한

```yaml
autonomous_research:
  allowed_domains:
    - arxiv.org
    - openreview.net
    - github.com
    - official vendor documentation
    - academic institution sites

  daily_limits:
    pages: 100
    papers: 30
    llm_tokens: 1000000

  forbidden:
    - 로그인 우회
    - 유료 자료 무단 접근
    - 개인정보 수집
    - robots.txt 위반
    - 사이트 과부하
    - 자동 회원가입
```

---

# 8. 관심 미션별 실행 파이프라인

## A. 논문·기술동향 조사

```text
미션 분석
   ↓
검색식 생성
   ↓
논문·공식 문서·코드 저장소 수집
   ↓
중복 제거
   ↓
관련성 평가
   ↓
핵심 논문 상세 분석
   ↓
주장 단위 교차 검증
   ↓
기술 분류와 성숙도 평가
   ↓
적용 가능성 분석
   ↓
보고서 작성
   ↓
독립 검토
   ↓
LLM Wiki 반영
```

전문 작업자:

```text
Scout Agent
Paper Reader
Repository Analyst
Trend Synthesizer
Fact Checker
Domain Reviewer
Report Editor
```

최종 산출물:

```text
- 기술동향 보고서
- 핵심 논문 목록
- 기술 분류표
- 적용 후보와 근거
- 불확실성과 반대 근거
- Wiki 변경 내역
```

---

## B. 웹 기반 프로그램 개발

```text
요구사항 해석
   ↓
사용자 시나리오 작성
   ↓
기술 조사
   ↓
아키텍처 설계
   ↓
Issue와 작업 분해
   ↓
프론트엔드·백엔드 구현
   ↓
자동 테스트
   ↓
보안·코드 검토
   ↓
통합 테스트
   ↓
문서화
   ↓
배포 승인 요청
   ↓
배포
```

작업 구성:

```text
Product Agent
Architect Agent
Frontend Agent
Backend Agent
Data Agent
QA Agent
Security Reviewer
Documentation Agent
```

중요한 원칙:

```text
코드를 작성한 에이전트와
코드를 승인하는 에이전트를 분리한다.
```

Git 기반으로 운영하면 다음 구조가 적합합니다.

```text
대표 AI
  ├─ 요구사항 Issue 생성
  ├─ 구현 에이전트가 branch 생성
  ├─ 코드 작성 및 테스트
  ├─ 검토 에이전트가 PR review
  ├─ QA 에이전트가 acceptance test
  └─ 대표 AI가 merge 또는 승인 요청
```

---

## C. 학술논문 작성

```text
연구 질문 정의
   ↓
선행 연구 조사
   ↓
Research Gap 추출
   ↓
가설·연구 방법 설계
   ↓
실험 또는 데이터 분석
   ↓
결과 해석
   ↓
논문 구조 설계
   ↓
초안 작성
   ↓
인용 검증
   ↓
반론 검토
   ↓
저널 양식 적용
   ↓
사람의 최종 승인
```

전문 작업자:

```text
Literature Agent
Research Design Agent
Experiment Agent
Statistics Agent
Scientific Writer
Citation Auditor
Critical Reviewer
Journal Format Agent
```

AI가 학술논문을 작성하더라도 다음 항목은 반드시 사람이 승인해야 합니다.

```text
- 실제 실험을 했다는 주장
- 저자 목록과 기여도
- 연구윤리 관련 내용
- 데이터의 공개 여부
- 학술지 제출
- 최종 결론의 과학적 책임
```

---

# 9. 지식과 Skill의 구분

Hermes에서는 memory와 skill을 구분해서 사용하는 것이 중요합니다.

공식 설명에 따르면 memory는 항상 참고할 작고 지속적인 사실에 적합하고, skill은 필요할 때만 불러오는 더 긴 절차에 적합합니다. `/learn`을 이용해 반복 절차를 새로운 skill로 만들 수도 있습니다. ([GitHub][7])

| 종류          | 저장할 내용                     |
| ----------- | -------------------------- |
| Memory      | 사용자 선호, 조직 원칙, 중요한 환경 정보   |
| LLM Wiki    | 논문, 기술 지식, 프로젝트 경험, 근거와 출처 |
| Skill       | 반복 가능한 업무 수행 절차            |
| Mission log | 특정 업무의 계획·실행·결과            |
| Profile     | 장기 정체성, 권한, 설정, 독립 메모리     |
| Workspace   | 실제 코드와 문서를 작업하는 디렉터리       |

예를 들어:

```text
“사용자는 한국어 보고서를 선호한다”
→ Memory

“RO-Crate의 구조와 VSMR 적용 방법”
→ LLM Wiki

“기술동향 보고서를 만드는 절차”
→ Skill

“2026년 7월 Agentic AI 동향 조사”
→ Mission

“논문 조사 전문 조직”
→ research-lab Profile
```

---

# 10. 대표 AI의 핵심 판단 루프

대표 AI는 미션을 받을 때 다음 과정을 수행해야 합니다.

```text
1. 목표를 이해했는가?
2. 완료 조건을 정의할 수 있는가?
3. 기존 Wiki에 필요한 지식이 있는가?
4. 최신 정보가 필요한가?
5. 어떤 전문 작업자가 필요한가?
6. 병렬 수행 가능한 작업은 무엇인가?
7. 사람의 승인이 필요한 행동이 있는가?
8. 결과를 어떻게 검증할 것인가?
9. 무엇을 Wiki와 Skill에 남길 것인가?
```

이를 실행 루프로 나타내면 다음과 같습니다.

```text
Observe
  ↓
Understand
  ↓
Retrieve Knowledge
  ↓
Plan
  ↓
Delegate
  ↓
Execute
  ↓
Verify
  ↓
Reflect
  ↓
Update Wiki / Skill
  ↓
Continue or Complete
```

---

# 11. 권장 초기 구현 범위

처음부터 완전한 AI 회사를 만들지 말고 다음 MVP로 시작하는 것이 좋습니다.

## Phase 1 — 대표 AI

```text
- Hermes Agent 설치
- chief-ai profile 생성
- Slack 연결
- SOUL.md 작성
- 승인 정책 작성
- 미션 파일 형식 정의
- 작업 로그 저장
```

## Phase 2 — 지식 시스템

```text
- LLM Wiki Git 저장소 생성
- raw/wiki/reflections 구조 생성
- 웹페이지·논문 수집 skill
- Wiki compile skill
- 출처·중복·상충 검사
- 정기 수집 cron 등록
```

## Phase 3 — 세 가지 핵심 Skill

```text
/research-trend
최신 논문·기술동향 조사

/build-web-app
웹 애플리케이션 기획·개발·테스트

/write-paper
선행연구 조사부터 논문 초안까지 수행
```

## Phase 4 — 전문 조직 분리

```text
research-lab
software-lab
paper-lab
knowledge-lab
audit-lab
```

## Phase 5 — 인력풀과 인큐베이터

```text
신규 Agent 후보
   ↓
제한된 미션 수행
   ↓
능력 평가
   ↓
실패 분석과 지식 학습
   ↓
재평가
   ↓
승격
   ↓
전문 Agent Pool 등록
```

---

# 12. 처음 만들어야 할 실제 시스템

첫 번째 버전의 구성은 다음 정도가 가장 현실적입니다.

```text
Slack
  │
  ▼
Hermes Gateway
  │
  ▼
chief-ai Profile
  ├── SOUL.md
  ├── Mission Manager Skill
  ├── Approval Guard Skill
  ├── Research Skill
  ├── Coding Delegation Skill
  ├── Paper Writing Skill
  ├── Wiki Search Skill
  └── Wiki Update Skill
          │
          ▼
     Git-based LLM Wiki
          │
          ├── raw
          ├── wiki
          ├── reflections
          └── missions
```

초기에는 별도 중앙 오케스트레이션 플랫폼을 먼저 개발하지 않아도 됩니다.

Hermes의 다음 기능을 먼저 조합하면 됩니다.

```text
Profile
+ SOUL.md
+ Skills
+ Subagents
+ Cron
+ Slack Gateway
+ Git
+ LLM Wiki
```

미션이 늘어나고 여러 에이전트의 상태·비용·권한을 한 화면에서 관리할 필요가 생길 때 별도의 **AI Company Control Plane**을 개발하는 것이 좋습니다.

---

# 최종 권장안

사용자의 AI-Native Company에서 첫 번째 직원은 단순 비서가 아니라 다음 역할을 가진 **대표 AI Chief Agent**여야 합니다.

```text
사용자 의도 이해
→ 미션 정의
→ 필요한 지식 선행 확보
→ 전문 작업자 구성
→ 자율 실행
→ 독립 검증
→ 예외 상황만 승인 요청
→ 결과 보고
→ 지식과 절차 축적
→ 다음 미션에서 더 나은 판단
```

가장 중요한 설계 원칙은 세 가지입니다.

1. **대화 중심이 아니라 미션 중심으로 운영한다.**
2. **Profile, Subagent, Skill, Wiki의 역할을 구분한다.**
3. **사람의 개입을 작업 과정이 아니라 위험 경계에 배치한다.**

그리고 첫 구현은 다음 하나의 시나리오를 완주하도록 만드는 것이 적절합니다.

> Slack에서 “최신 Agentic AI 기술동향을 조사해 웹 보고서로 만들어라”라고 요청하면, 대표 AI가 조사팀과 개발팀을 구성하고, 논문 수집·분석·보고서 작성·웹 프로그램 구현·테스트·Wiki 반영까지 수행한 뒤 결과만 보고한다.

이 시나리오가 정상적으로 작동하면 이후 논문 작성, 연구과제 기획, 웹 플랫폼 개발 등으로 자연스럽게 확장할 수 있습니다.

[1]: https://github.com/NousResearch/hermes-agent/blob/main/README.md?utm_source=chatgpt.com "hermes-agent/README.md at main - GitHub"
[2]: https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/profiles.md?utm_source=chatgpt.com "hermes-agent/website/docs/user-guide/profiles.md at main - GitHub"
[3]: https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/profile-distributions.md?utm_source=chatgpt.com "hermes-agent/website/docs/user-guide/profile-distributions.md at main · NousResearch ..."
[4]: https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/messaging/slack.md?utm_source=chatgpt.com "hermes-agent/website/docs/user-guide/messaging/slack.md at main - GitHub"
[5]: https://github.com/Astro-Han/karpathy-llm-wiki?utm_source=chatgpt.com "GitHub - Astro-Han/karpathy-llm-wiki: Agent Skills-compatible LLM wiki for Claude Code ..."
[6]: https://github.com/NousResearch/hermes-agent/blob/main/cron/scheduler.py?utm_source=chatgpt.com "hermes-agent/cron/scheduler.py at main - GitHub"
[7]: https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/skills.md?utm_source=chatgpt.com "hermes-agent/website/docs/user-guide/features/skills.md at main - GitHub"
