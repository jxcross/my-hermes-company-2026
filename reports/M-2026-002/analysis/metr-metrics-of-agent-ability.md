# S05 — METR: Metrics of Agent Ability

- 원자료: `raw/metr-metrics-of-agent-ability.md` (METR note, 2026-07-24)
- 성격: 단일 task score–expenditure curve를 중심으로 한 방법론 note. 실측 benchmark 순위 보고가 아니다.

## 핵심 주장과 근거
1. **주장:** agent score가 높은 expenditure에서도 계속 증가한다면 fixed-budget raw score는 충분한 능력 지표가 아니다. [§Setup / Agent-only metrics, L31–45, L75–85]
   - **근거:** expenditure는 money·tokens·time으로 해석 가능하며, returns가 크면 test-time scaling을 반영할 지표가 필요하다고 한다. [L31–45]
2. **주장:** 평가는 고정예산 score, practical-plateau score, fixed-score 달성 지출, returns-to-expenditure, utility 기반 expenditure-adjusted score를 구분해야 한다. [§Agent-only metrics, L71–131]
   - **근거:** fixed-score 지출은 `x=s_A^{-1}(s̄)`이며 target score 달성 가능할 때만 유한한 cost-efficiency 수치가 된다고 정의한다. [L97–107]
3. **주장:** human-grounded measurement는 agent와 human의 expenditure를 동 단위 또는 공통 단위(예: 달러)로 환산해야 한다. [§Setup, L55–63]
   - **근거:** continuous time horizon은 `s_H^{-1}(s_A(x̄_A))`로 human-equivalent expenditure를 계산하며 binary threshold보다 통계적으로 효율적이라고 제안한다. [L153–165]
4. **주장:** expenditure horizon은 test-time scaling이 유의미한 task에 유용하지만, agent가 전 구간에서 human을 지배하거나 두 curve의 slope가 비슷하면 불안정/무한일 수 있다. [§Human-grounded metrics, L167–181]
   - **근거:** 정의는 `sup{x≥0: s_A(x)≥s_H(x)}`. [L173–181]

## 정의·수식
- `s(x)`: expenditure에서의 score; `s^{-1}(s̄)`: score `s̄`에 필요한 지출. [L55–61]
- **Cost-of-pass:** cost per attempt / success probability, 독립 재시도 하 정답 1건의 기대비용. [FAQ, L213–217]

## 사용 경계·상충 표시
- 저자는 score curve 측정의 실무 난점과 benchmark collection으로의 확장 복잡성을 명시한다. [L31–39]
- `S01`의 예산 공개·under-elicitation 문제와 정합적이다. 어느 지표가 보편적으로 최선인지는 본문이 확정하지 않는다.
