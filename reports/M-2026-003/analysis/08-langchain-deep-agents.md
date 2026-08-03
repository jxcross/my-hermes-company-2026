# LangChain — Deep Agents v0.7

- 자료: `langchain-deep-agents-v0-7` (vendor, 위키 재사용 원문)
- 원문: `raw/langchain-deep-agents-v0-7.md`.

## 핵심 주장
1. base harness를 단순화해 comparable performance에서 base input token을 65% 줄였다고 주장한다. [원문: l.27, l.40–48]
2. tool schema가 few-shot example보다 사용법을 더 잘 전달하고, system prompt/tool description의 instruction 반복은 유의미한 강화가 아니라는 관찰을 제시한다. [원문: l.31–35]
3. default TodoListMiddleware는 평가상 유의미한 성능 향상이 없어 opt-in으로 변경했으나, 긴 다단계 과업·저성능 모델·UI progress 필요 상황에는 유용하다고 제한한다. [원문: l.42–46, l.66–76]

## 근거·방법론
- base system prompt 제거, built-in tool description 43% 축소, todo middleware 기본 제외의 3 변경을 수행했다. [원문: l.40–46]
- autonomous/conversational/long-context 3 범주와 4개 모델의 matrix로 v0.7과 v0.6.12를 평가했다. [원문: l.50–60]
- 결과 설명상 reward의 confidence interval은 모든 모델에서 0을 가로지른다. [원문: l.60–62]

## 정의·수치
- base input tokens: builtin prompt·tools·middleware에 연관된 tokens. [원문: l.46–48]
- default-agent turn: 약 6k→약 2k base input tokens(65% 감소). [원문: l.46]
- tool description 43% 축소. [원문: l.42–44]
- 특정 `gpt-5.6-luna`: token −34%, cost −15%, reward +4%(저자 보고). [원문: l.58–62]
- SummarizationMiddleware 기본 trigger: context window 85%. [원문: l.90]

## 한계·검증 이관
- reward CI가 0을 span하므로 ‘성능 유지/향상’의 통계적 확정성은 모델·지표별 추가 검토가 필요하다.
- 공개 블로그의 자체 eval이며, 다른 harness나 memory architecture로 일반화하지 않는다.
