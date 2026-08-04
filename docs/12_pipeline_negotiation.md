# 12. 미션 파이프라인 협상 — 설계

> 작성일: 2026-08-04 · 상태: **검토용 초안(구현 전)** · 성격: design spec
> 관련: [`11_template_driven_missions.md`](./11_template_driven_missions.md)(§3.F 협상 4단계·§2 3계층) · [`03_mission_pipeline_and_workflow.md`](./03_mission_pipeline_and_workflow.md)(Scoping 소유권) · [`10_stage1_plan.md`](./10_stage1_plan.md)(§4.3 자율분해 사고) · 참고 소스: 형제 repo `other_projects/harness-templates`
> 후속: 이 문서는 "협상을 어떻게 성립시킬 것인가"를 고정한다. 구현은 §8 phasing에 따라 **phase별 별도 계획**으로 진행한다.

## 0. 왜 이 설계인가 (Context)

Sam이 원하는 업무 방식은 명확하다:

> **①** 아주 잘 동작하는 워크플로우 스킬을 만들거나 얻은 다음 **②** Kanban task를 위해 YAML로 등록해 놓으면
> **③** Solomon이 주어진 미션과 가장 알맞은 템플릿을 찾고 **④** 그 단계를 Sam과 논의한다(그대로 승인할 수도,
> 특정 단계를 가감할 수도 있다). **⑤** 템플릿이 적어 찾지 못하면 처음부터 구성할 수도 있다.

즉 **미션은 던지는 것이 아니라 합의하는 것**이고, 합의가 끝난 뒤에야 Solomon에게 전권이 넘어간다. 이 방향은
[`11 §3.F`](./11_template_driven_missions.md)가 그린 협상 4단계와 같다. 그러나 **협상을 받칠 컴포넌트가 전부
미구현**이고, 더 근본적으로 **현행 구조에는 협상이 들어갈 자리 자체가 없다**(§1). 또한 구상을 문자 그대로
구현하면 네 개의 함정 — **억지 매칭 · 빈 종이 · 품질 저하 · 조정 휘발** — 에 빠진다(§2).

이 문서는 그 자리를 만들고 함정을 피하는 설계를 고정한다.

## 1. 현행 구조 진단

| 구상 단계 | 현재 상태 |
|---|---|
| ① 스킬 확보 | `other_projects/harness-templates`에 **28종**. 이 중 **미션 아키타입 후보 20종**(domain 9 · research 11). cli 8종은 코딩도구 하네스라 제외 |
| ② YAML 등록 | 템플릿 **1개뿐**(`templates/trend-report.yaml`). 스킬→YAML 변환기 없음 |
| ③ 템플릿 매칭 | **미구현** — `scripts/match_template.py`·`templates/manifest.json` 둘 다 없음([`11 §3.C`](./11_template_driven_missions.md) 설계만 존재) |
| ④ 단계 논의·가감 | **불가능** — 아래 구조적 모순 |
| ⑤ 신규 구성 | 없음. 빈 종이에서 Solomon이 자율 작성해야 함 |

### 1.1 구조적 모순 — 협상할 자리가 없다

협상은 카드 생성 **전**에 끝나야 한다. 그런데 현재 Scoping은 카드가 이미 다 만들어진 **후**의 stage 1이다.
그 증거가 `templates/trend-report.yaml` stage 1 본문에 박힌 방어 문구다:

```
⚠️ 파이프라인 카드는 이미 생성돼 있다 — 하위 task를 새로 만들거나 kanban decompose 하지 마라(중복 방지).
```

이 문구는 [`10 §4.3`](./10_stage1_plan.md) 개선점 2(Solomon 자율분해가 수동 카드와 충돌)의 대증요법이다.
근본 원인은 **인스턴스화가 협상보다 먼저 일어난다는 순서 오류**다. 그래서 지금의 Scoping은 협상이 아니라
**SCOPE.md 작성 + 실행 개시 승인**일 뿐이고, "단계를 빼자"는 대화는 성립할 수 없다.

### 1.2 불변식 검사가 협상 주기에 못 붙는다

불변식 검사 `check_invariants()`는 `scripts/instantiate_template.py:78`에 **인라인**으로 있어
**인스턴스화 시점에 한 번만** 돈다. 협상은 "조정 → 검사 → 재제시"를 여러 번 반복하는 루프이므로
**독립 CLI 린터**가 필요하다([`11 §3.E`](./11_template_driven_missions.md)에 설계만 존재).

## 2. 구상의 문제점 6가지

### ① 논의 단위가 "단계"인 것이 잘못됐다 — 가장 큰 문제
"5단계를 빼자"라고 말하려면 Sam이 파이프라인 내부 구조를 알아야 한다. 그건 창업자가 할 일이 아니고 회를
거듭할수록 피곤해진다. Sam이 실제로 가진 것은 **의도**다 — "깊이보다 속도", "특허도 봐야 한다",
"2023년 이후만", "검증은 빡세게". **논의 단위는 의도여야 하고, 단계 가감은 Solomon이 수행하는 번역 결과**여야 한다.
Sam은 YAML도 stage 번호도 보지 않는다.

### ② 매칭의 실패 모드가 설계에 없다 — 가장 큰 리스크
"가장 알맞은 템플릿을 찾는다"는 잘 맞을 때만 좋다. 실제로는 세 경우가 있고 **어중간하게 맞는 경우가 안 맞는
경우보다 위험하다**. 70% 맞는 템플릿은 억지로 밀기 쉽고, 그러면 미션에 맞지 않는 파이프라인이 11단계를 다
돌고 나서야 문제가 드러난다(실패 비용이 가장 늦게·가장 크게 발생). 매처는 **점수 + 근거 + "적합 없음" 판정**을
낼 수 있어야 한다.

### ③ "처음부터 구성"이 가장 어려운데 가장 대충 계획돼 있다
빈 종이에서 11단계를 만들면 품질 편차가 크고 불변식을 놓친다. 그런데 **모든 미션의 뼈대는 사실 같다**:
`범위합의 → 수집 → 가공 → 검증 → 산출 → 검증 → 인도`. 이 골격을 파일로 못박으면 "처음부터"가
**빈 종이가 아니라 빈칸 채우기**가 된다.

### ④ 검증 등급이 없으면 라이브러리가 커질수록 품질이 떨어진다
"아주 잘 동작하는 스킬"을 무엇으로 아는가? harness의 스킬은 **Claude Code 로컬 파일 런타임**에서 동작한
것이지, 우리 **Kanban + profile + 이중 게이트** 환경에서 동작한다는 보장이 없다. 현재 실증된 템플릿은
`trend-report` 하나뿐이다(M-2026-003·004 완주). 등급 없이 20종을 쏟아 넣으면 라이브러리는 커지지만 신뢰도는
떨어진다.

### ⑤ 임포트의 진짜 작업은 "agent → profile 매핑"이다
paperforge는 자기 agent를 12개 갖고 있으나(`.claude/agents/paperforge-*.md`), 우리 profile은 **8종 고정**이다
— `default(Solomon)`·`scout`·`reader`·`writer`·`synthesizer`·`curator`·`fact-checker`·`reviewer`.
따라서 임포트는 파일 변환이 아니라 **역할 매핑 판단**이고, 매핑되지 않는 역할이 나오면 기존 profile에
흡수할지 새 profile을 만들지 결정해야 한다. 린터가 `stage.profile ∈ 8종`을 강제하지 않으면 **존재하지 않는
assignee로 카드가 생성**된다.

### ⑥ 조정이 자산으로 쌓이지 않는다
"특허 수집 단계 추가"를 세 번째 미션에서도 하고 있다면 그건 새 템플릿이어야 한다. 복리 성장을 표방하는데
조정이 매번 휘발되면 라이브러리가 자라지 않는다.

## 3. 제안 A — 3층 구조

```
Layer 0  templates/_base.yaml         불변 골격. 린터의 기준이자 신규 구성의 출발점
Layer 1  templates/<archetype>.yaml   아키타입(A 동향 · B 논문 · D 웹개발) + maturity 등급
Layer 2  missions/<MID>.yaml          이번 미션만의 조정(오버레이). 승인 시 동결
```

이는 [`11 §2`](./11_template_driven_missions.md)의 3계층(불변식/아키타입/미션별 적응)을 **파일로 실체화**한 것이다.

- **Layer 0** — `_base.yaml`이 있으면 "처음부터 구성"이 빈칸 채우기가 되고(문제 ③), 린터의 기준이 한 곳으로 모인다.
- **Layer 2** — base 대비 **차이만**(`drop`/`add`/`override`) 담아 변경 diff가 명확하다. 승인 순간 병합 결과를
  `reports/<MID>/pipeline.resolved.yaml`로 **동결**해 **"승인한 것 = 실제 도는 것"을 파일로 증명**한다.

미션 스펙(Layer 2) 예시:

```yaml
mission: M-2026-005
template: trend-report
topic: "온디바이스 LLM 추론 최적화 동향"
intent:                       # 협상에서 오간 Sam의 의도(감사추적용 원문)
  - "특허도 봐야 한다"
adjust:
  add:
    - stage: 3
      parallel.workers: [+patents]
  override:
    policy.source_balance_policy.min_per_category.patents: 2
```

`drop`으로 단계를 빼면 번역기가 **upstream을 자동 재배선**한다(7을 빼면 8의 upstream `[7]` → `[6]`).

## 4. 제안 B — 의도 기반 협상 프로토콜

```
Sam:      "온디바이스 LLM 동향. 근데 특허도 봐야 하고, 이번엔 빨리."

Solomon:  [매칭] trend-report (proven, 적합도 0.82)
                근거: 동향 조사 · 출처 검증 필요 · Markdown 보고서 산출
          [번역] "특허"  → stage3 워커에 patents 추가 · min_per_category.patents=2
                 "빨리"  → stage5 분석 심도 축소 · batch_size 3→5
          [제시] mermaid DAG + 변경 3줄 요약
          [검사] 린터 통과 — 검증자 2 · Sam게이트 2 · 작성자≠검증자 유지

Sam:      "특허는 좋은데 속도는 됐다. 검증은 그대로."
Solomon:  [재제시] ...
Sam:      "승인"

          → pipeline.resolved.yaml 동결 → 인스턴스화 → 카드 생성 → 실행
```

**핵심: 승인 전까지 Kanban 카드가 하나도 없다.** 협상은 **Phase 0(비파괴)**으로 앞당겨지고, §1.1의
방어 문구는 불필요해진다 — 자율분해와 충돌할 카드가 애초에 없기 때문이다.

Sam이 보는 것은 **mermaid DAG + 변경 요약 3줄**뿐이다. YAML은 Solomon과 린터만 본다.

## 5. 제안 C — 매칭 3-way 판정

| 적합도 | Solomon의 행동 |
|---|---|
| **높음** | 그대로 제시 → 조정 협상 |
| **어중간** | **경고와 함께** 제시 + "이 부분이 안 맞습니다" 명시 + **신규 구성도 함께** 제안 |
| **낮음** | 억지로 고르지 않음 → `_base.yaml` 골격에서 신규 구성 |

`maturity: draft | tested | proven`을 점수에 반영하고, **draft를 쓸 땐 Sam에게 경고**한다(문제 ④).
매칭 결과는 항상 **근거와 함께** 제시한다 — 점수만 보여주면 Sam이 판단할 수 없다.

## 6. 제안 D — 축적 루프 (복리 성장의 실체)

- 신규 구성한 파이프라인 → `templates/`에 **draft**로 자동 저장
- 실미션 1회 완주 → **tested** · 2회 완주 → **proven**
- 같은 조정이 3회 반복 → Solomon이 **"이걸 아키타입으로 승격할까요?"를 선제 제안**

미션을 돌릴수록 라이브러리가 스스로 자란다. 이것이 없으면 템플릿 수는 사람이 넣은 만큼에서 멈춘다.

## 7. 컴포넌트 (구현 시 파일)

| 파일 | 역할 | 상태 |
|---|---|---|
| `templates/_base.yaml` | 불변 골격(Layer 0) | 신규 |
| `templates/manifest.json` | 템플릿 목록 · 키워드 · maturity | 신규 |
| `scripts/lint_template.py` | 불변식 린터(독립 CLI). `instantiate_template.check_invariants` 이관 + **profile 8종 검사** 추가 | 신규(이관) |
| `scripts/match_template.py` | 3-way 매칭 + 근거 출력 | 신규 |
| `scripts/mission_spec.py` | 오버레이 병합 · upstream 재배선 · 승인 시 동결 | 신규 |
| `scripts/import_skill.py` | harness 스킬 → YAML 초안(agent→profile 매핑 포함) | 신규 |
| `scripts/instantiate_template.py` | `--spec missions/<MID>.yaml` 수용, 불변식 검사는 린터로 위임 | 수정 |
| `templates/trend-report.yaml` | stage 1 방어 문구 제거(협상이 앞당겨지므로 불필요) | 수정 |
| `solomon-profile/SOUL.md` | 의도 번역 · 매칭 근거 제시 · 협상 규약 | 수정 |

## 8. 권장 단계 (phasing) — 각 phase는 별도 구현 계획

1. **오버레이 + 린터** — 단계 가감과 불변식 강제. 템플릿이 1개여도 즉시 쓸모가 있고 나머지 전부의 토대.
2. **매처 + manifest** — 템플릿이 3개 이상일 때 의미가 생긴다.
3. **스킬 임포터** — B(논문)·D(웹개발) 확보. **린터가 있어야 변환본 품질을 검증**할 수 있으므로 1 이후.
4. **의도 번역 프로토콜** — Solomon SOUL에 협상 규약 반영. 라이브 미션으로 검증.
5. **축적 루프** — maturity 승격 · 조정 반복 감지.

## 9. 미결 (Sam 결정 필요)

- **협상 장소** — Claude Code에서 먼저 / Slack에서 Solomon과 / 설계는 같게 두고 양쪽 진입 허용.
  *(2026-08-04 현재 Slack은 네트워크 도달 불가 상태라 즉시성은 Claude Code가 유리. 다만 장기적으로는
  Solomon이 협상 경험을 쌓는 편이 "AI CEO" 취지에 맞는다.)*
- **첫 구현 범위** — §8의 1번만 / 1+2 / 협상 루프 전체.
- **단계 가감 자유도** — 임의 가감 + 린터 불변식 강제(권장) / 템플릿이 `optional: true`로 표시한 단계만.

## 10. 검증 (설계 타당성 판정)

- 린터가 불변식 위반 오버레이(**검증자 제거 · Sam 게이트 제거 · 미등록 profile**)를 거부한다.
- 오버레이로 단계를 제거하면 upstream이 자동 재배선되어 **DAG가 끊기지 않는다**(dry-run mermaid로 확인).
- 승인 동결본(`pipeline.resolved.yaml`)과 실제 생성된 카드 그래프가 **일치**한다.
- 조정 없는 `trend-report` 인스턴스화 결과가 현행과 **동일**(회귀 없음).
- 어중간한 미션(예: "논문 초고 쓰기"를 trend-report로 매칭)에서 매처가 **경고 또는 적합 없음**을 낸다.

## 11. 리스크·주의

- **의도 번역의 오역** — "빨리"를 Solomon이 검증 단계 축소로 번역하면 불변식을 건드린다. 린터가 막지만,
  **번역 결과를 항상 Sam에게 3줄 요약으로 보여주는 것**이 1차 방어선이다.
- **오버레이 병합의 복잡도** — `drop`+`add`가 겹치면 순서에 따라 결과가 달라진다. 병합 규칙을 문서로
  고정하고(`drop` → `add` → `override` 순), 테스트로 못박는다.
- **임포트의 신뢰 경계** — 외부 스킬의 프롬프트·스크립트를 그대로 실행하면 프롬프트 인젝션·임의 코드 실행
  위험이 있다. 임포트는 **초안 생성까지만** 하고 사람 검토 게이트를 반드시 거친다.
- **범위 억제** — 웹 UI 편집기는 이 문서의 범위 밖이다(§9 협상 장소 결정 후 별도 판단).
