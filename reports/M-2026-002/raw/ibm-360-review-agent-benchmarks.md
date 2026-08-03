# A 360 review of AI agent benchmarks

## 메타데이터
- URL: https://research.ibm.com/blog/AI-agent-benchmarks
- 발행일: 미확인
- 수집일: 2026-08-02
- 출처유형: 기업 연구 블로그
- 수집방법: Tavily web_extract
- 원문 범위: 공개 웹 페이지에서 추출된 원문 텍스트.

## 원문 텍스트 (Tavily web_extract 보존본)

4 minute read

# A 360 review of AI agent benchmarks

In a survey of 120 AI agent evaluation methods, researchers at Hebrew University, IBM, and Yale summarize recent trends and identify four ways testing could be improved to advance the field.

If the phrase, “there’s “an app for that,” came to define the smartphone era, its modern equivalent, “there’s an agent for that,” could sum up this one.

From coding to customer care, large language model (LLM) agents are taking on increasingly complex tasks that involve interacting with real-world people and environments. Agents are honing new skillsets to pull this off, from calling on outside tools and other agents, to “reasoning” through multi-step problems and “reflecting” on intermediate steps to minimize mistakes and adapting to changing conditions.

The benchmarks for evaluating this new fleet of LLM agents are evolving, too. To get a bird’s eye view of this changing landscape, IBM researchers joined colleagues at Hebrew University and Yale to review 120 frameworks for evaluating LLM agents. They reported their findings in a [new preprint study](https://arxiv.org/pdf/2503.16416) submitted to the EMNLP conference.

Much of today’s revolution in AI and natural language processing can be traced back to rigorous, standardized benchmarks. Without them, researchers would have difficulty measuring progress, comparing methods, or even agreeing on what progress looks like.

“Well-designed benchmarks do more than just rank systems; they spotlight gaps, motivate new research, and sometimes surface surprising failure modes or unintended behaviors,” said study co-author Arman Cohan, an assistant professor of computer science at Yale. “Robust evaluation of AI agents is especially critical to understand to what extent these systems are capable, reliable, and safe before they’re widely deployed.”

Like AI agents themselves, agent benchmarks vary in quality. The researchers undertook their survey with the aim of pinpointing where both agents and agent-evaluation could be improved.

[IMAGE: blogArt-evaluatingTheEvaluationofAIAgents-diagram.png]

Researchers summarize key trends and notable gaps in what may be the most comprehensive survey of AI agent benchmarks to date.

“Evaluation can be thought of as a compass,” said the study’s lead author, Asaf Yehudai, an IBM researcher focused on AI evaluation. “If your compass is working properly, it can take you to where you want to go a lot faster.”

## Agent SATs

As LLM agents become the new focal point of AI development, understanding their capabilities and limitations has become ever more important. Benchmarks today target what are now considered core competencies for LLM agents.

LLM agents are expected to break down complex problems into bite-sized pieces and generate a plan of action. Developers can now choose from [PlanBench](https://arxiv.org/pdf/2206.10498), [MINT](https://arxiv.org/pdf/2309.10691), and IBM’s own [ACPBench](https://arxiv.org/pdf/2410.05669), among others, to test their agents’ planning and reasoning chops.

Tool calling is another fundamental competency that allows agents to execute real-world tasks. Benchmarks that once rated agents on isolated API calls have tacked on additional challenges. Berkeley’s [Gorilla leaderboard V3](https://gorilla.cs.berkeley.edu/blogs/13_bfcl_v3_multi_turn.html) rates agents on how well they handle multi-step and multi-turn calls while IBM’s [NESTFUL benchmark](https://arxiv.org/pdf/2409.03797v3) introduces implicit, parallel, and “nested” calls, in which one call serves as input to the next.

“Our goal was help push the development of more capable and reliable autonomous agents,” said IBM researcher Kinjal Basu, who led the team behind NESTFUL.

A third hallmark of LLM agents is the ability to “reflect” on feedback from their environment, to recover from mistakes and to adjust when confronted with new information. Microsoft’s [LLF-Bench](https://arxiv.org/pdf/2312.06853) measures how well agents can take feedback to correctly complete a task.

A fourth trait of LLM agents that is becoming increasingly important is longer-term memory, which can help agents go beyond examples in their training data to a deeper, experience-based understanding of the world. LLM agents augmented with mechanisms to enhance their memory can now be tested on benchmarks like [LoCoMo](https://snap-research.github.io/locomo/) (short for “long conversation memory”).

## Simulating enterprise environments

As more LLM agents take on expert tasks, benchmarks are shifting to more closely resemble scenarios professionals face in real life. Shopping agents in CMU’s [WebArena](https://webarena.dev/) navigate a simulated web environment to make purchases (IBM’s [computer-using generalist agent](https://ibm-cuga.19pc1vtv090u.us-east.codeengine.appdomain.cloud/html/landing.html) (CUGA) continues to hold first place with a 62% success rate). Software engineering agents in Princeton’s [SWE-bench](https://www.swebench.com) pick apart actual GitHub issues while freelancers navigating OpenAI’s SWE-Lancer environment try to maximize take-home pay.

Customer care and research lab environments are also represented. Retail agents in Sierra’s [τ-bench](https://arxiv.org/pdf/2406.12045), interact with simulated customers to resolve disputes while scientific agents in OpenAI’s [PaperBench](https://openai.com/index/paperbench/) try to replicate state-of-the art AI research, developing a code base, understanding how previous work fits in, and executing experiments, among other tasks.

An emerging set of benchmarks test agents on several expert skills at once. In [OSWorld](https://os-world.github.io/), [AppWorld](https://appworld.dev/), and [CRMWorld](https://arxiv.org/pdf/2411.02305), among others, agents update spreadsheets, execute code without crashing the system, and analyze monthly sales data.

These new benchmarks are significantly more challenging than those that have come before. “Even the best-performing agents score as low as 5%,” said Yehudai.

## The future of AI agent evaluation

The researchers identified four ways that evaluation could be improved to make AI agents safer, more robust, and performant. Their recommendations are as follows:

Evaluations should be more granular. Rather than focus narrowly on agents getting the right answer, more attention should be paid to intermediate steps to see how they get there. Just as some teachers only give partial credit to students who don’t show their work, benchmarks should require the same as agents, they say. That way, researchers can get a better sense of where agents are still struggling.

Benchmarks should measure cost-efficiency. A team at Princeton was among the first [to call out](https://arxiv.org/pdf/2407.01502) many state-of-the-art agents for being too complex and costly. This isn’t a surprise, given how many evaluations prioritize accuracy over cost or efficiency, which can make high-performing agents impractical to impossible to deploy in real life. API costs, token usage, inference speeds, and overall resource consumption should be measured and reported to level the playing field.

More of the evaluation process should be automated to lower costs and speed up reviews. Agents could evaluate other agents with an “[agent-as-a judge](https://arxiv.org/pdf/2410.10934)” approach to reduce the burden on human reviewers. IBM just launched [EvalAssist](https://ibm.github.io/eval-assist/), an application that makes it easier to use LLMs to evaluate other LLMS. AI-generated data could also be used to a greater extent to create more diverse, realistic task scenarios.

Finally, more benchmarks should focus on safety, trustworthiness, and policy compliance. One benchmark, Gray Swan AI’s [AgentHarm](https://arxiv.org/pdf/2410.09024), tries to coax agents into overriding their guardrails to do things like jailbreak an AI system or commit fraud, while IBM’s new [ST-WebAgentBench](https://arxiv.org/pdf/2410.06703) simulates high-risk business applications in which safety and trustworthiness are especially critical.

“Good science is grounded in evidence, and AI is no exception,” said Michal Shmueli-Scheuer, a distinguished engineer who leads IBM’s AI benchmarking and evaluation team. “This survey has helped validate that we are headed in the right direction.”

[Subscribe to our Future Forward newsletter and stay up to date on the latest research news

Subscribe to our newsletter](https://www.ibm.com/account/reg/us-en/signup?formid=news-urx-53237)

## Related posts

* ### [Bringing a common language to AI evaluation](/blog/every-evaluation-ever)

  [IMAGE]

  News

  Kim Martineau

  + [AI](/artificial-intelligence)
  + [AI Transparency](/topics/trustworthy-ai)
  + [Fairness, Accountability, Transparency](/topics/fairness-accountability-transparency)
  + [Generative AI](/topics/generative-ai)
* ### [IBM is committing up to $50 million worth of quantum compute access for the US Genesis Mission, and more](/blog/ibm-us-genesis-mission-quantum-ai)

  [IMAGE: The hardware and software for the era of quantum utility is here]

  News

  + [AI](/artificial-intelligence)
  + [Quantum](/quantum-computing)
* ### [IBM open sources CodeAlchemy, a massive synthetic dataset of high-quality code](/blog/code-alchemy-for-synthetic-code)

  [IMAGE]

  Kim Martineau

  + [AI](/artificial-intelligence)
  + [AI for Code](/topics/ai-for-code)
  + [Generative AI](/topics/generative-ai)
  + [Natural Language Processing](/topics/natural-language-processing)
* ### [Replacing the ‘bones’ of transformer-based models](/blog/cofrgenets-replace-the-bones-of-transformer-based-models)

  [IMAGE]

  Research

  Peter Hess

  + [AI](/artificial-intelligence)
  + [Generative AI](/topics/generative-ai)