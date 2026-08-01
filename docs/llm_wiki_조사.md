# LLM Wiki 조사 정리

> **조사 기준일:** 2026-08-01
> **대상:** Karpathy의 "LLM Wiki" 개념 및 참고 구현
> **출처:** Karpathy gist, Astro-Han 참고 구현 (하단 [출처](#출처) 참조)
> **관련 문서:** [`ai_native_company_개념.md`](./ai_native_company_개념.md) 6장(LLM Wiki 구조), [`hermes_agent_조사.md`](./hermes_agent_조사.md)

> ⚠️ **주의:** 이 문서는 2026-08-01 시점에 공개 자료를 조사·정리한 것이다.
> 커뮤니티 구현의 세부 파일 형식·통계는 변동될 수 있으므로 실제 도입 전 원문·저장소를 재확인할 것.

---

## 1. LLM Wiki란 무엇인가

**핵심 아이디어 (Karpathy 원문)**
LLM Wiki는 자료를 나중에 검색하려고 단순 색인만 하는 것이 아니라,
**LLM이 자료를 읽어 핵심 정보를 추출하고 기존 위키에 통합**하여
**지속적으로 축적·복리(compounding)되는 지식 아티팩트**를 만드는 방식이다.

**동기**
전통적인 wiki는 사람이 유지·보수해야 해서 "유지 비용이 가치를 초과하면 방치된다".
LLM은 교차 참조 갱신, 일관성 유지, 행정적 정리 같은 **번거로운 관리 작업(bookkeeping)**을
저비용으로 처리할 수 있어, 이 문제를 해소한다.

**역할 분담**
- **사람**: 어떤 원자료를 넣을지(curation), 방향 제시, 분석적 판단
- **LLM**: 정리·교차참조·일관성 유지 등 행정 작업

---

## 2. 일반 RAG와의 차이

| 구분 | 일반 RAG | LLM Wiki |
|------|----------|----------|
| 지식 저장 형태 | Raw chunk + 임베딩 | **정제된 markdown 문서(article)** |
| 합성(synthesis) 시점 | **질의 시점마다** 매번 | **수집(ingest) 시점에 한 번** |
| 유지보수 | 사람이 수동, 비용 큼 | LLM이 자동, 비용 낮음 |
| 최적화 대상 | 광범위 검색 | 지식 축적·정리·교차참조 |
| 검색 방식 | 벡터 유사도 | index + 전문(full-text) 검색 |

핵심 차이는 **"언제 지식을 합성하는가"**다. RAG는 매 질의마다 chunk를 다시 조합하지만,
LLM Wiki는 자료를 넣을 때 한 번 정제해 두고 이후에는 그 정제된 문서를 재사용한다.

---

## 3. 3단계 워크플로

### 3.1 Ingest (원자료 → 지식 컴파일)

1. **Fetch** — URL/파일/텍스트에서 원자료 수집 → `raw/<topic>/YYYY-MM-DD-slug.md`로 보존
   - 메타데이터(URL, 수집일, 발행일) 포함, **원문 그대로 보존**(재작성 금지)
2. **Triage** — 기존 위키와 비교하여 분류
   - **New**: 새 article 생성
   - **Update**: 기존 article 병합
   - **Disputed**: 기존 내용과 상충 → 충돌 주석 추가
   - **No material**: 새 정보 없음 → raw에만 저장, 위키 미변경
3. **Compile** — `wiki/`에 markdown article 작성/수정
   - **Source Fidelity(출처 충실성)**: 모든 숫자·날짜·인용문은 raw 파일에서 **먼저 위치를 확인한 뒤** 그대로 기록(locate-before-write)
   - 모순 시 **`Status: Disputed`** 블록 표시
   - 여러 article에 영향을 주면 **Cascade Update**(연쇄 갱신) 수행
4. **Post-Ingest** — `wiki/index.md`(전체 목차)와 `wiki/log.md`(append-only 로그) 갱신

> 하나의 원자료가 10~15개 위키 문서에 영향을 줄 수 있다.

### 3.2 Query (지식 검색·합성)

1. `wiki/index.md`에서 후보 article 탐색
2. 전문 검색(동의어 포함)으로 관련 문서 확인
3. article을 읽어 답변 합성, **markdown 링크로 인용**
4. 필요 시 **Archive**: 합성한 답변을 새 위키 문서로 저장(Sources 필드 포함)

### 3.3 Lint (위키 건강성 점검)

| 유형 | 내용 |
|------|------|
| **Safe Fixes(자동)** | index 일관성, 내부 링크 수정, raw 참조 존재 확인, See Also 유효성 |
| **Mechanical(스크립트)** | 출처 충실성 검증(`scripts/check_evidence.py`로 숫자·날짜·인용문 grep), 근거 필드 손상 탐지, 미사용 raw 파일 |
| **Judgment(수동 판단)** | article 간 사실 모순, Status 블록 누락, 고아 문서, 대표 개념인데 전용 문서 없음 |

---

## 4. 지식 계층 구조

```
Raw (원본, 불변)
   ↓
Wiki (컴파일된 지식, LLM 소유)
   ↓
Reflection (조직의 장기 판단·통찰) ※ 개념 문서/원문에서 강조
```

| 계층 | 위치 | 소유/불변성 | 역할 |
|------|------|-------------|------|
| **Raw** | `raw/<topic>/*.md` | LLM read-only, 불변 | 원본 데이터(source of truth) |
| **Wiki** | `wiki/<topic>/*.md` | LLM 소유, 가변 | 컴파일된 지식 문서·합성 결과 |
| **Index** | `wiki/index.md` | LLM 소유, 가변 | 전역 목차 |
| **Log** | `wiki/log.md` | append-only | 모든 작업(ingest/query/lint) 기록 |
| **Reflection** | (개념 문서: `reflections/`) | 조직 소유 | 장기 판단·통찰(자료 창고 → 판단 능력) |

> **Reflection 계층의 의미:** 논문 요약만 쌓으면 "자료 창고"에 그치지만,
> reflection(적합/부적합 조건, 재검토 조건 등)이 쌓이면 **조직의 판단 능력**이 축적된다.
> (개념 문서 6장 ③ Reflection knowledge와 동일한 강조점)

---

## 5. 권장 디렉터리 구조

참고 구현(Astro-Han) 기준의 최소 구조:

```
project/
├── raw/                       # 불변 원자료
│   └── <topic>/
│       └── 2026-04-03-slug.md # YYYY-MM-DD-설명적-slug.md
├── wiki/                      # 컴파일된 지식(LLM 관리)
│   ├── index.md               # 전역 목차 [링크 | 요약 | 갱신일]
│   ├── log.md                 # append-only 작업 로그
│   └── <topic>/
│       └── concept.md
├── references/                # 템플릿(raw/article/archive/index)
├── scripts/                   # lint 유틸리티 (check_evidence.py 등)
└── SKILL.md                   # 워크플로 정의(스키마 계층)
```

핵심 규칙:
- `wiki/`는 **1단계 topic 디렉터리만**(중첩 금지)
- `raw/`는 원문 그대로 보존, `wiki/`가 이를 참조

> 개념 문서 6장의 확장 구조(`sources/`, `reflections/`, `missions/`, `claims/`, `contradictions/`, `indexes/`, `inbox/`)는
> 이 최소 구조 위에 조직 운영용 디렉터리를 더한 형태다.

---

## 6. 상충 정보(Contradictions) · 근거(Claims) 관리

**상충 표시 — Status 블록**
```markdown
### Status: Disputed
- Claim: [상충하는 주장]
- Sources: [상충 출처 링크]
- Notes: [어느 쪽이 최신인지, 근거는 무엇인지]
```
- 같은 article 내: Status 블록으로 표시
- 서로 다른 article 간: 양쪽에 Status 블록 + 상호 링크

**근거(Provenance) 추적**
- article의 **Sources** 필드: 저자/기관 + 날짜 (세미콜론 구분)
- article의 **Raw** 필드: 근거 raw 파일에 대한 markdown 링크
- **Grounding Invariant(근거 불변식):** 위키의 모든 핵심 사실은 raw 파일에 그대로 존재해야 하며,
  `scripts/check_evidence.py`로 숫자·날짜·인용문을 grep 검증한다.

---

## 7. Agent Skills / Claude Code 통합 (참고 구현)

Astro-Han 구현은 이 워크플로를 **Agent Skills 호환 skill**(`SKILL.md`)로 패키징한다.

| Operation | 트리거(예) | 결과 |
|-----------|-----------|------|
| **Ingest** | "이 URL/파일을 위키에 넣어줘" | 신규/갱신된 위키 문서 |
| **Query** | "X에 대해 내가 아는 게 뭐지?" | markdown 답변 + 위키 인용 |
| **Lint** | "위키를 점검해줘" | 자동 수정 + 이슈 리포트 |

- 설치: `npx add-skill Astro-Han/karpathy-llm-wiki`
- 지원 환경: Claude Code, Cursor, Codex, OpenCode 등(agentskills.io 표준)
- 구성: `SKILL.md`(메타데이터·워크플로) + `references/`(템플릿) + `scripts/`(도구)

> **Hermes 연결:** [`hermes_agent_조사.md`](./hermes_agent_조사.md) 5장의 skill(`/learn`, agentskills.io 호환)과 동일 표준이므로,
> LLM Wiki skill을 Hermes profile의 skill로 그대로 탑재할 수 있다.

---

## 8. Karpathy 원문 vs 커뮤니티 구현

| 항목 | Karpathy 원문 | 커뮤니티 구현(Astro-Han) |
|------|---------------|--------------------------|
| 범위 | 개념·고수준 워크플로 | 구체적 파일 형식·자동화 스크립트 |
| 3계층 아키텍처 | 제안(Raw/Wiki/Schema) | 구체화 |
| Ingest/Query/Lint | 개념 제시 | 명시적 절차·로그 형식 정의 |
| Triage 4분류 | 암시적 | 명시(New/Update/Disputed/No material) |
| Source Fidelity | "읽고 추출" | locate-before-write + `check_evidence.py` 자동화 |
| Cascade Update | 언급 없음 | 명시적 연쇄 갱신 규칙 |
| Archive(질의→위키) | "좋은 답변은 새 문서로 보관 가능" | Archive 템플릿·필드 구체화 |
| 검색 | 언급 없음 | index + 전문검색(벡터 DB 미사용) |

**의도적으로 제외된 것(구현 철학):**
소스 해시 추적, 라인 앵커, 신뢰도 점수, 문서별 검토일, 벡터/그래프 DB, 타입 온톨로지 등.
→ 5만~10만 토큰 규모에서는 **grep/전문검색이 더 단순·신뢰성 높다**는 판단.

---

## 9. 개념 문서(6장)와의 연결점

| 개념 문서 6장 요소 | 본 조사 대응 |
|--------------------|--------------|
| "원문 보존 → 추출/정규화 → 기존 지식 비교 → 중복/상충 표시 → 구조화 갱신 → 선행 지식 제공" | 3장 Ingest 워크플로 |
| ① Raw / ② Compiled / ③ Reflection | 4장 지식 계층 |
| `raw/`, `wiki/`, `reflections/`, `contradictions/`, `claims/`, `indexes/`, `inbox/` | 5장 디렉터리(최소 구조 + 조직 확장) |
| "출처·근거·상충 정보" | 6장 Contradictions·Claims 관리 |
| "미션 수행 시 선행 지식으로 제공" | 3.2 Query + Reflection 계층 |

---

## 출처

**Karpathy 원문(gist)**
- https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- (raw) https://gist.githubusercontent.com/karpathy/442a6bf555914893e9891c11519de94f/raw

**참고 구현**
- https://github.com/Astro-Han/karpathy-llm-wiki

**관련 표준**
- Agent Skills: https://agentskills.io

---
*이 문서는 2026-08-01 조사 결과다. 커뮤니티 구현의 세부 형식·통계는 원문·저장소 재확인을 권장한다.*
