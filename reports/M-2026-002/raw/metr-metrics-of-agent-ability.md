# Metrics of Agent Ability

## 메타데이터
- URL: https://metr.org/notes/2026-07-24-metrics-of-model-ability
- 발행일: 2026-07-24
- 수집일: 2026-08-02
- 출처유형: 독립 연구기관 노트
- 수집방법: Tavily web_extract
- 원문 범위: 공개 웹 페이지에서 추출된 원문 텍스트.

## 원문 텍스트 (Tavily web_extract 보존본)

![METR Logo](/assets/images/logo/logo-sketch.png)
![METR Logo](/assets/images/logo/logo-sketch.png)

##### CONTRIBUTORS

##### DATE

##### SHARE

`@misc{metr-2026-metrics-of-model-ability,
title = {Metrics of Agent Ability},
author = {Tom Cunningham},
howpublished = {\url{https://metr.org/notes/2026-07-24-metrics-of-model-ability/}},
year = {2026},
month = {07},
}`
![Tom Cunningham](/assets/images/metrics-of-agent-ability/tom-cunningham-sketch.webp "Tom Cunningham")

Every metric is based off the following two score functions:

Expenditure can be interpreted as money spent, or tokens, or time required.

I will not give a deep discussion of how to measure the score curves, $s\_H$ and $s\_A$. There are many practical difficulties involved in this.

I will generally address only scores on a single task; applications to collections of tasks (benchmark scores) can be a bit more complicated.

I will mostly not discuss other desirable properties of metrics - e.g. whether it is understandable, whether it is generalizable.

If score curves are very concave (meaning score is invariant to expenditure) then just reporting the raw score is fine, given some reasonable amount of expenditure.

If score curves show high returns to expenditure then we need a metric that takes into account test-time scaling.

Benchmarking against human abilities helps us generalize to entirely new tasks.

As the models get very good then many of the human-relevant benchmarks become no longer useful.

# Setup and Definitions

![Agent and human expenditure-to-score curves](/assets/images/metrics-of-agent-ability/setup-and-definitions.png)

![Agent and human expenditure-to-score curves](/assets/images/metrics-of-agent-ability/setup-and-definitions.png)

Each agent and each human is characterized by a function from expenditure to score, $s(x)$, and $s^{-1}(\bar{s})$ represents the expenditure required to reach a score $\bar{s}$.

In general I interpret score as performance on a single task, e.g., the speedup on an optimization problem. We could also interpret score as the share of binary tasks completed, or the probability of completing a single task.[1](#fn:1)

Expenditure will generally be treated as money, but it can also be interpreted as time or tokens.

Human-grounded metrics that compare agent and human expenditure require both expenditures to be measured in the same units or converted into a common unit such as dollars.

I will typically draw the agent curves ($s\_A(\cdot)$) as more concave than the human curves ($s\_H(\cdot)$).[2](#fn:2) I think this accurately represents the reality for most tasks today (e.g., Wijk et al. ([2025](#ref-wijk2025rebench))), but it could change.

AISI’s recent post on [More test-time compute, more capability](https://www.aisi.gov.uk/blog/more-compute-more-capability-why-ai-agent-evals-need-to-account-for-test-time-compute) has a good discussion and visualization of test-time scaling curves across a variety of different benchmarks:

![AISI test-time compute scaling curves](/assets/images/metrics-of-agent-ability/aisi-scaling-curve.webp)

![AISI test-time compute scaling curves](/assets/images/metrics-of-agent-ability/aisi-scaling-curve.webp)

# Agent-Only Metrics of Ability

We first discuss metrics that depend only on the agent’s score, without benchmarking against humans.[3](#fn:3)

## Score at Fixed Expenditure

![Agent scores compared at fixed expenditure](/assets/images/metrics-of-agent-ability/score-at-fixed-expenditure.png)

![Agent scores compared at fixed expenditure](/assets/images/metrics-of-agent-ability/score-at-fixed-expenditure.png)

This is the typical way we report most evals: pick a fixed expenditure $\bar{x}$ and report each agent’s score $s\_A(\bar{x})$. If $s\_A(\cdot)$ reliably asymptotes at a fairly low value of $x$, then this is a sufficient statistic for most purposes.

This metric becomes less useful when agent scores continue increasing even at high levels of expenditure; e.g., see the criticisms by [Noam Brown](https://x.com/polynoamial/status/2064210146558136827) and Kapoor et al. ([2025](#ref-kapoor2024agents)).[4](#fn:4)

Another reason for fixing expenditure is to increase separation in scores, where a higher level of expenditure would cause saturation, and so little discrimination between model capabilities (e.g. [in a recent AISI post](https://www.aisi.gov.uk/blog/how-fast-is-autonomous-ai-cyber-capability-advancing)).[5](#fn:5)

## Score at Practical Plateau

![Agent scores measured where returns to expenditure become sufficiently low](/assets/images/metrics-of-agent-ability/score-at-practical-plateau.png)

![Agent scores measured where returns to expenditure become sufficiently low](/assets/images/metrics-of-agent-ability/score-at-practical-plateau.png)

A common practical response is to report the score at the point where the function plateaus, or falls below a certain slope (assuming concavity). E.g., Kwa and West et al. ([2025](#ref-kwa2025longtasks)) say “Models were given sufficiently high token limits to reach a plateau in success rate.”

This is roughly equivalent to reporting score at a high expenditure level, representing the highest reasonable level of expenditure. It will not be well-defined if the score function never plateaus.

## Expenditure at Fixed Score

![Agent expenditures compared at fixed score](/assets/images/metrics-of-agent-ability/expenditure-at-fixed-score.png)

![Agent expenditures compared at fixed score](/assets/images/metrics-of-agent-ability/expenditure-at-fixed-score.png)

We can instead fix a target score $\bar{s}$ and report the infimum expenditure needed to reach that score: $x=s\_{A}^{-1}(\bar{s})$.

This metric will only give a finite number if the evaluated model can achieve the score $\bar{s}$. This is a cost-efficiency metric, often used when looking at declines in model costs over time ([Gundlach et al. 2026](#ref-gundlach2026priceprogress); [Cottier et al. 2025](#ref-cottier2025prices)).[6](#fn:6)

If agents all had the same *relative* costs of performance, then new generations of models would shift multiplicatively left (additively left in log-space), and this type of “efficiency” metric would be a sufficient statistic for ability. However, there is some reason to believe that new models typically have disproportionate impacts at high expenditures, i.e. they make certain scores available that would have been almost impossible at any expenditure for an earlier model.[7](#fn:7)

## Returns to Expenditure

![Returns to expenditure on log-log axes, with each agent's elasticity marked](/assets/images/metrics-of-agent-ability/returns-to-expenditure.png)

![Returns to expenditure on log-log axes, with each agent's elasticity marked](/assets/images/metrics-of-agent-ability/returns-to-expenditure.png)

If the returns to expenditure do not plateau, even at significant levels of expenditure, then score at a fixed expenditure is not a satisfactory metric.

Instead, it can be useful for a metric to express the marginal returns to expenditure. The nature of the scaling can vary across domains, and so the appropriate metric is often chosen depending on the shape of the scaling. Two common patterns:

In each case the relationship will be linear on a graph with appropriately transformed axes. However it’s also possible that no consistent relationship exists.

## Expenditure-Adjusted Score

![Expenditure-adjusted score as utility net of cost](/assets/images/metrics-of-agent-ability/expenditure-adjusted-score.png)

![Expenditure-adjusted score as utility net of cost](/assets/images/metrics-of-agent-ability/expenditure-adjusted-score.png)

If we are willing to be opinionated about the relative value of expenditure and score, then we can express those tradeoffs with a utility function $U(s,x)$, which will give us a metric of value. Each agent will have a different level of optimal expenditure (represented by a tangency point on the diagram) and a different level of utility.

The utility can be expressed as an expenditure-adjusted score: the score at zero expenditure that would make you indifferent between receiving that score and using the agent at its optimal expenditure:

The utility can also be expressed in monetary units, representing the total value you get from using the agent. Visually this will be the intersection of the optimal indifference curve with the $x$-axis (not pictured, it would fall on the negative part of the $x$-axis).

# Human-Grounded Metrics

A natural metric for human expenditure is time spent on the problem, and so some of these metrics use human-equivalent time as a metric of agent capability. However, if we are comparing agent and human expenditure on the same axes, then money is a more natural interpretation of $x$.

## Binary Time Horizon

![Binary human-equivalent expenditure or time horizon](/assets/images/metrics-of-agent-ability/time-horizon.png)

![Binary human-equivalent expenditure or time horizon](/assets/images/metrics-of-agent-ability/time-horizon.png)

Many continuously-scored tasks grade agents by a single human expenditure threshold. E.g. the [Opus 5 system card](https://www-cdn.anthropic.com/c5fbac3f0b1280a933ebd26d3cb8bb9f5bdeaf48/Claude%20Opus%205%20System%20Card.pdf) reports a series of AI R&D tasks, and for each a score that was achieved by a human after a specific amount of time (e.g. 8 hours or 40 hours). Agents can then be graded as passing if they beat the baseline.

METR’s “time horizon” metric (Kwa and West et al. ([2025](#ref-kwa2025longtasks))) combines many binary scores into a human-equivalent time for each model, based on the $x$ at which the agent matches or exceeds the human score half the time.[9](#fn:9)

Formally, for each task we choose a reference score \(\bar{s}\) and calculate the infimum human expenditure \(x\_H^\*=s\_H^{-1}(\bar{s})\) needed to achieve that score. Here expenditure is measured in time, but it could also be measured in money.

We then calculate the agent’s score at some fixed expenditure \(\bar{x}\_A\), and give the agent a binary score based on whether \(s\_A(\bar{x}\_A)\) is above or below \(\bar{s}\).

The diagram shows equal expenditure on humans and agents (\(\bar{x}\_A=x\_H^\*\)). The fixed agent expenditure \(\bar{x}\_A\) need not equal the human expenditure \(x\_H^\*\), but equal expenditure on each is a natural choice for interpretability.

## Continuous Time Horizon

![Continuous human-equivalent expenditure](/assets/images/metrics-of-agent-ability/continuous-time-horizon.png)

![Continuous human-equivalent expenditure](/assets/images/metrics-of-agent-ability/continuous-time-horizon.png)

We can extend the time horizon metric by retaining the agent’s continuous score rather than reducing it to a binary comparison.

We elicit each agent at a single expenditure level, $\bar{x}\_A$, and then compare the resulting score with the whole human curve, rather than with one binary threshold.

The human-equivalent expenditure is $s\_H^{-1}(s\_A(\bar{x}\_A))$: the expenditure at which a human would achieve the same score.

This method is much more statistically efficient than the binary time-horizon method. Reasons to use binary scoring include (1) that it may be difficult to map out the entire $s\_H(\cdot)$ function but easier to measure a single point, and (2) that the returns to human effort may look like a step function, e.g., if the score metric $s$ is itself binary.

## Expenditure Horizon (Human-Matching Expenditure)

![Human-matching expenditure or expenditure horizon](/assets/images/metrics-of-agent-ability/expenditure-horizon.png)

![Human-matching expenditure or expenditure horizon](/assets/images/metrics-of-agent-ability/expenditure-horizon.png)

Unlike the fixed-budget metrics, this metric uses the agent’s entire performance curve, making it useful for tasks where we expect significant test-time scaling.

We define the “expenditure horizon” as the supremum of the common expenditures at which the agent matches or beats humans: $\sup\{x\geq 0:s\_A(x)\geq s\_H(x)\}$.

The expenditure horizon does not provide a finite crossing point if agents dominate humans at every level of expenditure.

Expenditure horizon can also be unstable if the slopes of $s\_H$ and $s\_A$ are similar.

Cunningham et al. ([2026](#ref-cunningham2026expenditurehorizon)) introduce this metric, based in part on the apple-picking model ([Cunningham and Shetty 2026](#ref-cunningham2026applepicking)).[10](#fn:10)

## Human-Relative Expenditure Saving

![Human-relative expenditure saving](/assets/images/metrics-of-agent-ability/human-relative-expenditure-saving.png)

![Human-relative expenditure saving](/assets/images/metrics-of-agent-ability/human-relative-expenditure-saving.png)

We can also directly measure the effective cost-saving relative to using a human on a task.

For simplicity we draw the human score curve as linear. We can then identify the point at which the marginal returns to expenditure are equal between agents and humans (assuming concave returns to expenditure on agents). If you are allocating budget between agents and humans then this will be the point at which you switch from spending on agents to spending on humans.

This point also identifies the economic value: the horizontal distance between the red and blue points represents the expenditure saving due to using an agent:

This applies the utility framework discussed above, but now our indifference curves are determined by the returns to human labor (our outside option).

This is discussed further in Cunningham et al. ([2026](#ref-cunningham2026expenditurehorizon)) and Cunningham and Shetty ([2026](#ref-cunningham2026applepicking)).

## Human-Relative Cost at Fixed Score

![Human-relative cost at fixed score](/assets/images/metrics-of-agent-ability/human-power-at-fixed-score.png)

![Human-relative cost at fixed score](/assets/images/metrics-of-agent-ability/human-power-at-fixed-score.png)

An alternative metric is to simply compare the cost of achieving some fixed score, $\bar{s}$. In the figure, $x\_{A\_i}=s\_{A\_i}^{-1}(\bar{s})$ and $x\_H=s\_H^{-1}(\bar{s})$:

This metric is consistent across values of $\bar{s}$ when the human and agent score curves differ only by a multiplicative horizontal rescaling.

Unlike the other metrics in this section, this metric remains useful when agents strictly dominate humans (i.e. the red curve is entirely to the left of the blue curve).

# FAQ / Notes

Two related papers incorporate model and human costs in different ways (both are somewhat different from a true hybrid: they use a rule-based allocation of tasks between agents and humans):

Erol et al. ([2025](#ref-erol2025costofpass)) define a model’s cost-of-pass on problem $p$ as $v(m,p)=C\_m(p)/R\_m(p)$: the cost of one attempt divided by its probability of success, or equivalently the expected cost of obtaining a correct answer under independent retries. Their frontier cost-of-pass chooses the cheapest available model or qualified human expert separately for each problem:

Thus, the frontier can use a human for tasks on which human labor is cheaper and a model for tasks on which inference is cheaper; its average over a task distribution measures the cost of assigning each task to the cheaper producer.[13](#fn:13) This combines humans and models through task-by-task routing rather than within-task collaboration.

Patwardhan et al. ([2025](#ref-patwardhan2025gdpval)) (GDPval) describe speed-and-cost metrics that combine model win rates with the time and cost of model generation, expert review, and human rework.[14](#fn:14)

# Acknowledgements

Thanks to Beth Barnes, Manish Shetty, Nate Rush, Thomas Kwa, Parker Whitfill, Megan Kinniment, Alexander Barry, and Kaivu Hariharan for helpful discussions and feedback.

# References

Alomrani, Mohammad Ali, Yingxue Zhang, Derek Li, et al. 2025. *Reasoning on a Budget: A Survey of Adaptive and Controllable Test-Time Compute in LLMs*. <https://arxiv.org/pdf/2507.02076.pdf>.

Bartz-Beielstein, Thomas, Carola Doerr, Daan van den Berg, et al. 2020. *Benchmarking in Optimization: Best Practice and Open Issues*. <https://arxiv.org/pdf/2007.03488.pdf>.

Brown, Bradley, Jordan Juravsky, Ryan Ehrlich, et al. 2024. *Large Language Monkeys: Scaling Inference Compute with Repeated Sampling*. <https://arxiv.org/abs/2407.21787>.

Cottier, Ben, Ben Snodin, David Owen, and Tom Adamczewski. 2025. *LLM Inference Prices Have Fallen Rapidly but Unequally Across Tasks*. <https://epoch.ai/data-insights/llm-inference-price-trends>.

Cunningham, Tom, and Manish Shetty. 2026. “An Apple-Picking Model of AI R&D.” March 13. <https://tecunningham.github.io/posts/2026-03-13-apple-picking-ai.html>.

Cunningham, Tom, Manish Shetty, Vincent Cheng, and Nate Rush. 2026. “Expenditure Horizon: Measuring Optimization Ability, with an Application to NanoGPT.” METR, July 21. <https://metr.org/blog/2026-07-21-expenditure-horizon/#appendix-d>.

Erol, Mehmet Hamza, Batu El, Mirac Suzgun, Mert Yuksekgonul, and James Zou. 2025. *Cost-of-Pass: An Economic Framework for Evaluating Language Models*. <https://arxiv.org/abs/2504.13359>.

Fogelson, Alex, Zachary A. Brown, Hans Gundlach, Jayson Lynch, and Neil Thompson. 2026. *Two AI Metrics Diverged: Will It Make All the Difference?* <https://arxiv.org/pdf/2607.00913.pdf>.

Folkerts, Linus, Will Payne, Simon Inman, et al. 2026. *Measuring AI Agents’ Progress on Multi-Step Cyber Attack Scenarios*. <https://arxiv.org/abs/2603.11214>.

Gundlach, Hans, Jayson Lynch, Matthias Mertens, and Neil Thompson. 2026. *The Price of Progress: Price Performance and the Future of AI*. <https://arxiv.org/abs/2511.23455>.

Jones, Charles I. 1995. “R&D-Based Models of Economic Growth.” *Journal of Political Economy* 103 (4): 759–784. <https://doi.org/10.1086/262002>.

Kapoor, Sayash, Benedikt Stroebl, Zachary S. Siegel, Nitya Nadgir, and Arvind Narayanan. 2025. “AI Agents That Matter.” *Transactions on Machine Learning Research*. <https://arxiv.org/abs/2407.01502>.

Kwa, Thomas, Ben West, Joel Becker, et al. 2025. “Measuring AI Ability to Complete Long Tasks.” *arXiv Preprint arXiv:2503.14499*, ahead of print. <https://doi.org/10.48550/arXiv.2503.14499>.

McFadyen, Jessica, Ole Jorgensen, Harry Coppock, Kevin Wei, and Cozmin Ududec. 2026. *How Inference Compute Shapes Frontier LLM Evaluation*. <https://arxiv.org/abs/2606.17930>.

OpenAI. 2026. “An OpenAI Model Has Disproved a Central Conjecture in Discrete Geometry.” May 20. <https://openai.com/index/model-disproves-discrete-geometry-conjecture/>.

Patwardhan, Tejal, Rachel Dias, Elizabeth Proehl, et al. 2025. *GDPval: Evaluating AI Model Performance on Real-World Economically Valuable Tasks*. <https://arxiv.org/abs/2510.04374>.

Wijk, Hjalmar, Tao Lin, Joel Becker, et al. 2025. *RE-Bench: Evaluating Frontier AI R&D Capabilities of Language Model Agents Against Human Experts*. <https://arxiv.org/abs/2411.15114>.

For most of this discussion I had in mind a single task with a continuous score, but we can also interpret score as the share of tasks passed in a benchmark (Terminal-Bench, GPQA, etc.). If the overall pass rate is a sufficient statistic then this seems probably fine but I’m wary to make strong claims without thinking more about this. It could be a sufficient statistic if either (A) every constituent task is equally valuable or (B) the ranking of task difficulty is the same across all agents. [↩](#fnref:1)

In Cunningham and Shetty ([2026](#ref-cunningham2026applepicking)), we describe this as a “tortoise-hare” pattern: agents win at low expenditure, humans win at high expenditure. [↩](#fnref:2)

Many have analogues in optimization benchmarking; for example, Bartz-Beielstein et al. ([2020, sec. 5](#ref-bartzbeielstein2020benchmarking)) discuss fixed-cost and fixed-target metrics. [↩](#fnref:3)

In a section titled “Maximizing accuracy can lead to unbounded cost,” Kapoor et al. write: “Calling language models repeatedly and taking a majority vote can lead to non-trivial increases in accuracy across benchmarks like GSM-8K, MATH, Chess, and MMLU. … When the agent environment has easy signals to check if an answer is correct, repeatedly retrying can lead to even more compelling performance gains. … Li et al. showed that the accuracy of AlphaCode increases from close to 0% zero-shot to over 15% with 1,000 retries and over 30% with a million retries. … Thus, there is seemingly no limit to the amount of inference compute that can increase accuracy” ([Kapoor et al. 2025, sec. 2.1](#ref-kapoor2024agents)). [↩](#fnref:4)

“Without the 2.5M token cap, success rates are so high that time horizons become impossible to calculate.” [↩](#fnref:5)

Gundlach et al. ([2026](#ref-gundlach2026priceprogress)) emphasize the distinction between frontier and fixed-score costs: “while a fixed capability level becomes dramatically cheaper over time, achieving frontier performance continues to demand higher frontier expenditure” (Conclusion). Erol et al. ([2025](#ref-erol2025costofpass)) define a similar “cost-of-pass” metric: $\mathrm{CoP}=\frac{\text{cost per attempt}}{\Pr(\text{success per attempt})}$. [↩](#fnref:6)

McFadyen et al. ([2026](#ref-mcfadyen2026inferencecompute)) find that “the cross-generational gains visible in these curves come mainly from greater task reach and reliability rather than improved efficiency.” Folkerts et al. ([2026](#ref-folkerts2026cyberattack)) say “improvement likely operates on both dimensions identified above: newer models are more token-efficient (visible in the steeper early slopes in Figure 1) and possess deeper specialist capabilities (visible in whether a model plateaus or continues progressing).” [↩](#fnref:7)

Brown et al. write: “Across multiple tasks and models, we observe that coverage—the fraction of problems that are solved by any generated sample—scales with the number of samples over four orders of magnitude. Interestingly, the relationship between coverage and the number of samples is often log-linear and can be modelled with an exponentiated power law, suggesting the existence of inference-time scaling laws.” They qualify this result: “In domains without automatic verifiers, we find that common methods for picking from a sample collection (majority voting and reward models) plateau beyond several hundred samples and fail to fully scale with the sample budget” ([Brown et al. 2024](#ref-brown2024largelanguagemonkeys), abstract). [↩](#fnref:8)

They define the 50% task-completion time horizon as “the time humans typically take to complete tasks that AI models can complete with 50% success rate”—Kwa and West et al. ([2025](#ref-kwa2025longtasks), abstract). [↩](#fnref:9)

It defines the metric as “the dollar value at which the improvement to the goal metric is equal to the improvement by a human with the same budget” ([Cunningham et al. 2026](#ref-cunningham2026expenditurehorizon)). [↩](#fnref:10)

Fogelson et al. ([2026](#ref-fogelson2026twometrics)) write that “$\log(1/\epsilon)$ can be thought of as error rate orders of magnitude or ‘the number of nines of reliability’” and emphasize that the appropriate scale depends on utility: “if one’s utility is in error rate orders of magnitude, meek and frontier models will diverge. If near perfect accuracy on a fixed benchmark suffices, meek models will indeed inherit the earth” [sec. 3.1.2]. [↩](#fnref:11)

Alomrani et al. ([2025](#ref-alomrani2025reasoningbudget)) distinguish “L1 controllability—methods that operate under fixed compute budgets—and L2 adaptiveness—methods that dynamically scale inference based on input difficulty or model confidence” [abstract]. [↩](#fnref:12)

“This frontier cost-of-pass represents the true minimum expected cost to obtain a correct solution for problem $p$ using the best available option, whether it’s an LM or a human” ([Erol et al. 2025, sec. 2.4](#ref-erol2025costofpass)). [↩](#fnref:13)

For their “try 1 time, then fix it” metric, they “take the sampling time for the model, add review time $R\_T$ for an expert to assess quality, and then with probability $(1-w\_i)$ add in the human completion time for any fixes needed”; they calculate cost analogously ([Patwardhan et al. 2025](#ref-patwardhan2025gdpval), Appendix A.2.1). [↩](#fnref:14)

`@misc{metr-2026-metrics-of-model-ability,
title = {Metrics of Agent Ability},
author = {Tom Cunningham},
howpublished = {\url{https://metr.org/notes/2026-07-24-metrics-of-model-ability/}},
year = {2026},
month = {07},
}`
![METR Logo](/assets/images/logo/logo-sketch.png)

**METR** researches, develops, and evaluates frontier AI systems to measure how well they can perform complex tasks autonomously. Subscribe to our newsletter for updates.

Want to contribute to this work? METR is hiring: [View open roles](/careers)

## Featured research

METR researches, develops and runs cutting-edge tests of AI capabilities, including broad autonomous capabilities and the ability of AI systems to conduct AI R&D.

![Measuring the Self-Reported Impact of Early-2026 AI on Technical Worker Productivity](/assets/images/ai-usage-survey/headline.png)

### Measuring the Self-Reported Impact of Early-2026 AI on Technical Worker Productivity

A survey of 349 technical workers finds a median 1.4–2x self-reported change in value of work due to AI tools, expected to grow over time, though there are reasons to be skeptical of the magnitude.

![Early Work on Monitorability Evaluations](/assets/images/monitorability-post/time_horizon_ratio_non_visible_reasoning.png)

### Early Work on Monitorability Evaluations

We show preliminary results on a prototype evaluation that tests monitors' ability to catch AI agents doing side tasks, and AI agents' ability to bypass this monitoring.

![How Does Time Horizon Vary Across Domains?](/assets/images/time-horizon-domains/time-horizons-increasing.png)

### How Does Time Horizon Vary Across Domains?

We build on our time-horizon work and analyze 9 benchmarks for scientific reasoning, math, robotics, computer use, and self-driving in terms of time-horizon trends; we observe generally similar rates of improvement to the 7-month doubling time in our original time-horizon work.

![METR Logo](/assets/images/gen/home/evals-logo-slideable.svg)

METR (pronounced 'meter') is a research nonprofit that scientifically measures whether and when AI systems might threaten catastrophic harm to society.

#### Resources

#### Follow METR

#### Company