# S06 — METR: Expenditure Horizon

- 원자료: `raw/metr-expenditure-horizon.md` (METR blog, 2026-07-21)
- 성격: NanoGPT speedrun으로 설명한 agentic optimization ability 방법론. 실증 일반화에는 저자도 한계를 둔다.

## 핵심 주장과 근거
1. **주장:** AI R&D 가속 능력 평가는 token·experiment compute·human labor cost를 동시에 고려해야 한다. [§서론, L49–65]
   - **근거:** human/agent의 cost 대비 performance curve를 추정하면 사람이 AI보다 비용효율적인 지점을 지출 곡선 교차로 표현할 수 있다고 제안한다. [L49–51]
2. **주장:** `expenditure horizon`은 agent와 human이 같은 예산에서 goal metric 개선을 같게 만드는 달러 가치다. [§정의, L67–73]
   - **근거:** agent inference-scaling curve와 human labor의 local return estimate가 모두 필요하다고 명시한다. [L69–73]
3. **주장:** 기존 AI R&D benchmark 및 frontier optimization problem에서 agent performance를 요약하는 데 적용할 수 있으나, 기여 크기와 human effort 대비는 평가가 어렵다. [L61–65]
   - **근거:** 자율/AI 보조 optimization 성공 사례 보고는 성공 편향이 있고 human effort 대비 기여 추정이 어렵다고 경고한다. [L61–63]

## 한계·방법론
- smooth한 labor return에서 특히 유용하며, lumpy return이면 human·agent curve 추정 모두 어려워진다. [§Limitations, L81–85]
- 다른 agent가 이미 optimization에 기여했을 때 horizon은 더 짧게 추정될 수 있다. [L81–85]

## 사용 경계·상충 표시
- `S05`가 일반 metric taxonomy를 제시하는 반면, 본 자료는 optimization problem의 expenditure horizon 적용에 초점을 둔다. 두 정의는 상보적이며, 단일 fixed-budget benchmark score와 직접 대체 관계라고 단정하지 않는다.
