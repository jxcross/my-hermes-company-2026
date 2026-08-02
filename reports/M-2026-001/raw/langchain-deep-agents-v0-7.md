# Deep Agents v0.7

## 메타데이터
- URL: https://www.langchain.com/blog/deep-agents-v0-7
- 발행일: 2026-07-29
- 수집일: 2026-08-02
- 출처유형: 공식 블로그/프레임워크
- 수집상태: curl_exit=0; bytes=168411
- 원문 보존 파일: raw/_fetched/langchain-deep-agents-v0-7.html

## 검색/선정 근거
- 최근 3개월(2026-05~2026-08) 범위 내 공식/1차 공개 자료이며, 에이전트·툴/컴퓨터 유즈·평가·신뢰성 중 하나 이상의 키워드와 관련되어 수집함.

## 원문 텍스트 추출(사실 확인용; 자동 추출)
- Build long-running agents for complex tasks
- Build reliable agents with low-level control
- Quick start agents with any model provider
- Today we're shipping deep agents v0.7. This release simplifies the base harness, resulting in 65% fewer base input tokens at comparable performance.
- Building effective agents comes down to context engineering: a model is only as powerful as the context you give it, and that context comes down to what's in the prompt. Assembling that prompt well is the harness's job. But the guidance on how to do it changes constantly: OpenAI , Anthropic , and Google all publish their own prompting guides, and all three have rewritten them as models got more capable. Harnesses need to keep pace, or they end up carrying prompting the model has outgrown.
- Anthropic just published an updated guide on context engineering for modern models, alongside a report that they cut over 80% of Claude Code's system prompt for models like Opus 5 and Fable 5, with no measurable drop in coding evals. A couple of their findings mirror what we saw building v0.7:
- Interfaces beat examples: good tool schemas teach usage better than the once popular few shot examples, which can narrow how the model explores.
- Avoid repetition: repeating an instruction in both the system prompt and a tool's description doesn't offer meaningful reinforcement.
- Deep Agents v0.7 offers a leaner, more configurable base harness that's more token and cost-efficient.
- Our hypothesis: trimming unnecessary tokens from the base input prompt would boost token and cost efficiency while holding performance steady. We made three changes to test this:
- Removed base system prompt: We cut the system prompt that Deep Agents used under the hood, which included general guidelines and tool-usage prose ( #4859 ).
- Trimmed tool descriptions: We trimmed builtin tool descriptions by 43% ( #5009 ).
- Opt-in todos: create_deep_agent no longer includes TodoListMiddleware by default. Our evals showed the planning prompt and write_todos tool did not significantly improve performance ( #4929 ).
- Together, these changes drop base input tokens * on a default-agent turn by 65% (~6k → ~2k).
- * base input tokens : tokens associated with the builtin prompt, tools, and middleware
- We validated that performance didn't drop using a new eval suite built around three categories of benchmarks. Each targets a different kind of agent work:
- Autonomous: end-to-end tasks like coding and data analysis
- Conversational: multi-turn conversation with a simulated user
- Long-context: tasks that require retrieval and reasoning over long-context
- We ran the new v0.7 harness against the old baseline (v0.6.12) through a matrix of all three eval categories across four models: gpt-5.6-luna , gemini-3.6-flash , claude-sonnet-4-6 , and claude-opus-4-8 .
- Reward held steady overall, and tokens/cost generally dropped*. Most notably gpt-5.6-luna was down 34% on tokens and 15% on cost with reward up 4%. claude-sonnet-4-6 was the exception; analyzing the LangSmith traces showed that a significant cost increase was largely from two challenging autonomous tasks.
- For more information, see our recent blog on how we run evals for Deep Agents.
- TodoListMiddleware is now opt-in. Our evals across three categories and three models showed slightly better rewards and lower cost with todos disabled, so we removed the write_todos tool from the base harness. The changes and full experiment results can be found here .
- Long, multi-step tasks , where an agent benefits from an explicit plan to stay on track across many turns.
- Configurability was the top ask from Deep Agents users over the last six months, including requests to override FilesystemMiddleware , customize SummarizationMiddleware thresholds, and override the base prompt globally. They all hit the same wall: there was no supported way to change what the default harness stack does. v0.7 fixes that in two ways.
- from deepagents import create_deep_agent
- from deepagents.middleware import SummarizationMiddleware
- The filesystem is Deep Agents' core context management layer: the environment agents read, write, and navigate state through. This release makes some optimizations driven by the same eval suite plus trajectory optimizations identified from real dcode usage, with open and closed models.
- The delete tool was added to the default filesystem tool list. FilesystemMiddleware accepts a tool allowlist so you can opt out of this if desired ( #4325 , #4698 ).
- Full details, including migration notes and an “upgrade” prompt for coding agents, are in the changelog .
- Give the latest deepagents a try, and let us know what you think via GitHub issues , the forum , or on X / LinkedIn.
- Docs: filesystem tools and virtual filesystem access
- Eval suite blog: how we benchmark Deep Agents
- How we built LangChain’s agent-first data stack
- 3 Years of Graph Engineering with LangGraph
- LangSmith, our agent engineering platform, helps developers debug every agent decision, eval changes, and deploy in one click.
- LangSmith Platform LangSmith Observability LangSmith Evaluation LangSmith Deployment LangSmith Fleet LangSmith Sandboxes Deep Agents LangChain LangGraph
