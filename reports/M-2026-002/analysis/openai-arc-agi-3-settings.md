# S15 — OpenAI ARC-AGI-3 settings (wiki 재사용)

- 원자료: `raw/openai-arc-agi-3-settings.md`; canonical: `/work/llm-wiki/raw/mission-m-2026-001/openai-arc-agi-3-settings.md`
- 접근성: 공식 article URL은 JS/cookies 안내만 반환했고, 공식 RSS metadata만 보존되어 있다. [원문 L8–20]

## 원문에서 확인 가능한 주장
1. **주장:** two API settings가 GPT-5.6의 ARC-AGI-3 performance와 efficiency를 개선했으며, RSS 설명은 reasoning retention과 compaction을 해당 settings로 든다. [RSS description, L15–19]
   - **근거:** 제목은 ‘two settings tripled our scores’라고 하나, 보존 텍스트에는 setup·baseline·점수표·재현 절차가 없다. [L16–19]
2. **사실:** RSS pubDate는 2026-07-29 15:00:00 GMT다. [L16–19]

## 근거 한계
- `tripled`은 제목 표현이다. 수치 분자·분모, benchmark protocol, setting 정의가 본 보존본에 없으므로 정량 claim으로 확장 불가.
- 원문 본문은 ‘Enable JavaScript and cookies to continue’로 접근 제한됨. [L20]

## 상충·전달
- `S01`은 compaction을 long-run task-relevant context preservation으로 정의하지만, S15의 두 API setting이 어떤 정확한 configuration인지 여기서는 확인되지 않는다.
- 보고서에서는 benchmark setting sensitivity의 사례로만 쓰고 agent reliability 일반화·정량 비교의 근거로 사용하지 않는다. Cross-Verify에서 원문 접근/독립 재현 없이는 강화하지 않는다.
