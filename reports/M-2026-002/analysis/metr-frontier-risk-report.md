# S04 — METR Frontier Risk Report (Feb–Mar 2026)

- 원자료: `raw/metr-frontier-risk-report.md` (독립 연구기관 공개보고서, 2026-05-19)
- 범위: 내부 frontier-AI 개발사에서 agentic misalignment risk를 평가한 entity-based pilot; 모델 benchmark 단독 결과로 환원하지 않는다.

## 핵심 주장과 근거
1. **주장:** 공개 release에 묶이지 않고 반복 가능한 entity-based 내부 AI 사용 위험 평가가 필요하다. [Executive summary / Pilot process, L34–40, L60]
   - **근거:** Anthropic·Google·Meta·OpenAI가 참여했고, 참여자가 자료를 제공→METR가 private report를 작성→공개 가능한 비공개 정보를 참여자가 승인→공개보고서를 작성한 절차를 설명한다. [L34–40]
2. **주장:** 위험 평가는 misaligned internal agent의 harmful action 가능성을 means·motive·opportunity 및 rogue deployment의 강건성 관점에서 다뤄야 한다. [Executive summary, L42–46; Key facts, L95–99]
   - **근거:** 모델 평가, public model 평가, 참가자 제공정보, embedded red-team exercise, system card와 공개문헌을 결합했다고 명시한다. [L42–46]
3. **주장:** 참여사가 공유한 모델은 assessment window 내 internal SOTA였다고 진술했으나, 비참여사 내부 모델에 대한 보증은 불가하다. [§참여·한계, L67, L79]
   - **근거:** METR는 2026-05-19 기준 공개 최고 capability와 크게 더 강하다는 증거는 없다고 판단하지만, non-participant에 대한 assurance를 제공할 수 없다고 명시한다. [L67, L79]

## 핵심 수치·방법론
- Assessment window: 2026-02-16~03-16. [L28]
- 참여 4개사: Anthropic, Google, Meta, OpenAI. [L34, L54, L60]
- 공개보고서의 6 key facts는 다양한 evidence stream을 묶은 risk assessment 입력이며, 단일 실험의 결과가 아니다. [L42, L95–99]

## 사용 경계·상충 표시
- 내부 비공개 정보 및 참여자 disclosure approval에 의존하므로 완전한 독립 재현 자료가 아니다.
- `S12`의 통제 simulation misalignment evidence와 관련되지만, S04는 조직 단위 internal-use risk assessment, S12는 stress-test이므로 결과를 직접 동일시하면 안 된다.
