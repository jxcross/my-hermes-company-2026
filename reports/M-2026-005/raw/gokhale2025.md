LOGICGUARD: IMPROVING EMBODIEDLLMAGENTS
THROUGH TEMPORAL LOGIC BASED CRITICS
Anand Gokhale1, Vaibhav Srivastava 2, Francesco Bullo 1
1Department of Mechanical Engineering, University of California at Santa Barbara
2Department of Electrical and Computer Engineering, Michigan State University
anand gokhale@ucsb.edu, vaibhav@egr.msu.edu, bullo@ucsb.edu
ABSTRACT
Large language models (LLMs) have shown promise in zero-shot and single step
reasoning and decision-making problems, but in long-horizon sequential planning
tasks, their errors compound, often leading to unreliable or inefficient behavior.
We introduce LogicGuard, a modular actor–critic architecture in which an LLM
actor is guided by a trajectory-level LLM critic that communicates through Linear
Temporal Logic (LTL). Our setup combines the reasoning strengths of language
models with the guarantees of formal logic. The actor selects high-level actions
from natural language observations, while the critic analyzes full trajectories and
proposes new LTL constraints that shield the actor from future unsafe or ineffi-
cient behavior. LogicGuard supports both fixed safety rules and adaptive, learned
constraints, and is model-agnostic: any LLM-based planner can serve as the actor,
with LogicGuard acting as a logic-generating wrapper. We formalize planning as
graph traversal under symbolic constraints, allowing LogicGuard to analyze failed
or suboptimal trajectories and generate new temporal logic rules that improve fu-
ture behavior. To demonstrate generality, we evaluate LogicGuard across two
distinct settings: short-horizon general tasks and long-horizon specialist tasks. On
the Behavior benchmark of 100 household tasks, LogicGuard increases task com-
pletion rates by 25% over a baseline InnerMonologue planner. On the Minecraft
diamond-mining task, which is long-horizon and requires multiple interdepen-
dent subgoals, LogicGuard improves both efficiency and safety compared to Say-
Can and InnerMonologue. These results show that enabling LLMs to supervise
each other through temporal logic yields more reliable, efficient and safe decision-
making for both embodied agents.
1 INTRODUCTION
Large Language Models (LLMs) have recently demonstrated strong performance on diverse reason-
ing and decision-making tasks, from natural language understanding, reasoning (Huang & Chang,
2022; Wei et al., 2022), and code generation (Li et al., 2022b; Chen et al., 2021). However, much of
this success has been in static, text-based settings. In contrast, embodied dynamical environments re-
quire agents to plan over long horizons under uncertainty, partial observability, and complex dynam-
ics. While LLMs can generate short-term plans or respond coherently to individual prompts, they
lack the consistency, memory, and iterative refinement needed to solve multi-step tasks where in-
termediate actions must align with long-term goals. These shortcomings are especially pronounced
in open-ended domains such as robotics and interactive virtual environments, where agents must
reason over large action spaces, tools, and environment dynamics.
Recent evaluations (Kambhampati et al., 2024) show that even in simplified settings, LLMs often fail
to produce reliable plans without external verification. Small prompt variations lead to compounding
errors, and generated plans frequently violate preconditions or logical constraints. To address these
weaknesses, hybrid frameworks pair LLMs with external verifiers (Silver et al., 2022; Guo et al.,
2024). Yet, these methods typically rely on manual design and labeling, limiting scalability. In this
work, we aim to reduce such manual effort by automatically generating formal constraints that guide
and safeguard LLM planning.
1
arXiv:2507.03293v2  [cs.AI]  23 Sep 2025

Embodied environments such as Minecraft (Fan et al., 2022; Wang et al., 2023a), iGibson (Li
et al., 2022a), and VirtualHome (Puig et al., 2018) serve as useful testbeds for developing such
architectures, while datasets like Behavior (Li et al., 2023) benchmark agent performance across
diverse tasks. These domains capture core challenges of embodied intelligence, perceiving high-
dimensional states, planning under sparse supervision, and executing long-horizon strategies. Re-
cent work has begun to apply LLMs in these settings, from household robotics (Ahn et al., 2022)
to resource-driven virtual worlds (Wang et al., 2023a), but scalability and reliability remain open
problems.
Ultimately, enabling LLMs to function as trustworthy autonomous agents requires robustness in
safety-critical, long-horizon, and multi-agent contexts such as healthcare (Hosny et al., 2018), au-
tomated transportation (Wang et al., 2023b), and domestic assistance (Birkmose et al., 2025). In
these domains, unsafe or inconsistent behavior risks physical failures, while inefficiency erodes hu-
man trust (Esterwood & Robert Jr, 2023). We argue that planning architectures must combine the
flexible reasoning of LLMs with the formal guarantees of symbolic logic. To this end, we propose
a symbolic actor-critic framework that uses temporal logic to enforce safety, improve performance,
and ensure interpretable decision-making in embodied environments.
1.1 RELATED WORKS
Temporal Logic for Planning and Reinforcement learningLinear Temporal Logic
(LTL) (Pnueli, 1977) is a formal language for specifying temporal properties of systems through
boolean logic based expressions. LTL has been widely used in robot motion planning (Fainekos
et al., 2005), for safe planning and control (Wongpiromsarn et al., 2012), and even in reinforce-
ment learning (Alshiekh et al., 2018). In each of these applications, LTL is used to specify safety
constraints; instead, we shall use it to specify performance constraints.
Language Models for Planning and Policy LearningRecent work has explored LLMs for short-
horizon planning (Huang et al., 2022a). SayCan (Ahn et al., 2022) scores actions with an LLM and
weights them by an affordance function, while InnerMonologue (Huang et al., 2022b) feeds LLM
feedback back into itself to enable online re-planning. In embodied environments, Ziliotto et al.
(2025) uses compositional planning for LLMs, while Wu et al. (2023) uses alignment to improve
reasoning in embodied environments. Chen et al. (2024) breaks down complicated tasks into sub-
goals. Other works such as (Kambhampati et al., 2024) suggest that LLMs do not show reliability
while operating autonomously, and require external critics. Our work builds directly upon these
ideas, augmenting LLMs with formal verifiers.
Integrating Symbolic Reasoning with LLMsRecent work at the intersection of LLMs and tem-
poral logic focuses on translating natural language into LTL constraints (Chen et al., 2023; Liu et al.,
2023), or enforcing such translations during execution to filter unsafe actions (Yang et al., 2024).
These methods use static handcrafted rules. Recent work (Ravichandran et al., 2025) uses LLMs to
generate safety constraints online for robotics, their focus is purely on avoiding unsafe behaviors. In
contrast, we leverage an LLM-based LTL law generator not only to ensure safety but also to actively
improve planning performance and long-horizon task performance, enabling adaptive, empirically
grounded constraint generation in complex sequential environments.
LLM-guided Actor-Critic ArchitecturesPrior literature explores hybrid actor-critic setups
where LLMs guide planning and evaluation, using natural language feedback or prompt optimization
loops (Dong et al., 2023; Yang et al., 2025). These models rely on unstructured feedback and lack
formal guarantees, particularly in multi-step embodied reasoning tasks. Our LTL-based trajectory
critic offers interpretable, symbolic evaluation enforcing both safety and performance constraints.
1.2 CONTRIBUTIONS
We propose LogicGuard, a novel Temporal Logic-based critic, which augments and boosts the per-
formance of existing off-the-shelf LLM planners by protecting them against unsafe and inefficient
actions. Composing LogicGuard with an LLM planner leads to a novel symbolic actor-critic ar-
chitecture designed to solve long-horizon planning tasks in dynamic, embodied environments using
large language models (LLMs). This architecture breaks sequential planning into two timescales; an
2

online actor proposes high-level actions based on current state descriptions, and an offline critic loop
that imposes symbolic performance and safety constraints learned from past trajectories. This mod-
ular decomposition leverages LLMs’ strengths in local reasoning and addresses their weaknesses in
long-term consistency.
LogicGuard is domain-agnostic, naturally integrates with existing LLM-based planners, and is the
first to use symbolic temporal logic as a communication protocol between the actor and critic, en-
abling interpretable, verifiable, and generalizable decision making. Our contributions are threefold.
1.Symbolic actor-critic architecture: We propose a two-timescale architecture where an
LLM actor generates high-level actions online, and an LLM critic periodically analyzes
trajectories offline to induce Linear Temporal Logic (LTL) constraints on the actor. These
constraints are meant to prune unsafe or inefficient decisions, improving task performance.
Our formulation allows constraints to be automatically discovered and continuously refined
over time.
2.Communication via temporal logic: We introduce a novel mechanism for actor-critic in-
teraction based on symbolic temporal logic. In contrast to traditional reinforcement learn-
ing critics or natural language feedback, our critic outputs verifiable, machine-checkable
LTL constraints. LTL constraints provide strong safety guarantees, enforces logical con-
sistency, and enables constraint reuse across similar states and tasks. We also present a
graph-theoretic abstraction of planning under temporal logic, which highlights the role of
constraint pruning in reducing planning complexity.
3.Empirical validation in generalist and specialist embodied settings:We demonstrate
gains in (i) completion rates on 100 short-horizon household tasks from the Behavior
dataset, where atomic propositions are automatically derived across diverse environments,
and (ii) efficiency and consistency in the long-horizon Minecraft diamond-mining task,
where hand-engineered propositions capture domain structure. This demonstrates that our
architecture benefits both generalist agents operating in varied environments and specialist
agents in structured long-horizon domains.
Together, these contributions advance the goal of robust, safe, and interpretable LLM-based deci-
sion making in complex, dynamic environments through self-supervision, bridging the gap between
natural language reasoning and formal planning.
2 BACKGROUND ANDPROBLEMFORMULATION
A key challenge in deploying LLM-based agents in embodied environments is their difficulty with
coherent long-horizon planning. Without explicit goal formalization or structured guidance, they
often act reactively or inconsistently, leading to unsafe and inefficient behavior that undermines
reliability in human-agent teams (Fan et al., 2008). For real-world collaboration, agents must not
only avoid unsafe actions but also demonstrate efficiency, competence, and interpretable reasoning.
We address this by developing a mechanism that provides formal guarantees on agent behavior while
allowing for self-correction and improvement from structured feedback. Our framework uses sym-
bolic constraints learned over time to guide LLM decision-making, ensuring safe and efficient be-
havior with limited data. We evaluate this approach across two settings: (i) short-horizon household
tasks in the Behavior dataset, and (ii) the long-horizon challenge of mining a diamond in Minecraft.
2.1 PROBLEMSTATEMENT
We formalize the problem of safe and efficient LLM planning in embodied environments. Consider
an agent operating in a state spaceSand a finite high-level action spaceA abstract, where|A abstract|=
m. The agent observes a representation of the state, which is modeled byϕ full :S → Sfull. Unlike
standard RL, we assume no explicit reward function, and instead rely on a natural language goal
description (e.g., “make an iron pickaxe” or “obtain a diamond”).
To enable formal reasoning, we introduce an abstract Boolean representationϕ abstract :S full →
Sabstract, whereS abstract ⊆ {0,1}n, encodesnatomic propositions capturing salient environment
3

Environment
Abstract State
High level description of 
environment via atomic 
propositions
Low level Planner
Converts abstract actions 
to game level actions
LLM Actor
Picks an abstract 
action for the agent 
Full State
Detailed description of 
environment
Verifier
Checks if action is 
allowed per LTL 
laws
LLM Critic
Generates new laws from 
trajectories of abstract 
states and actions
Memory 
Buffer
Yes
No
New Laws
Online Actor Loop Offline Critic Loop
Figure 1:LTL-guided actor-critic architecture:Online, the LLM actor selects a high-level action,
which a symbolic verifier checks against LTL safety and efficiency constraints. Valid actions are
executed, while invalid actions trigger replanning. Offline, LogicGuard reviews trajectories and
proposes new LTL constraints to improve long-term behavior.
features. WithinS abstract, we defineS goal, the set of states that satisfy task objectives, andS unsafe, the
set of states that violate safety requirements.
Behavior is regulated through two types of LTL constraints. Safety constraints are expert-authored
rules that forbid transitions intoSunsafe, such as collision avoidance. Performance constraints, in con-
trast, are automatically induced by LogicGuard from observed trajectories, eliminating redundant or
suboptimal action patterns. Assuming all high-level actions have equal cost, the agent’s objective
is to minimize the number of primitive actions required to reachS goal while satisfying all safety
constraints with high probability.
2.2 LINEARTEMPORALLOGICPRIMER
Linear Temporal Logic(LTL) (Pnueli, 1977) provides a formal language for expressing temporal
properties over sequences of states. LTL formulas consist of variables called atomic propositions,
Boolean operators, and temporal operators(discussed in Appendix A.1). LTL formulas can be con-
verted into B ¨uchi automata, which are finite-state machines enabling the algorithmic verification
of whether a trajectory satisfies a given temporal specification. Using atomic propositions corre-
sponding to physically meaningful events leads to interpretability. We employ SPOT (Duret-Lutz &
Poitrenaud, 2004) to enforce LTL laws on the LLM actor.
2.3 EXPERIMENTALDOMAINS
We evaluate LogicGuard in two contrasting embodied environments. Behavior (Li et al., 2023) con-
sists of short-horizon household tasks in diverse environments, with multiple independent subtasks.
In contrast, Minecraft presents long-horizon compositional tasks with interdependent subgoals; we
study the diamond-mining task (Guss et al., 2019). These domains allow us to evaluate Logic-
Guard on both generalist agents in diverse, short-horizon tasks and specialist agents in structured,
long-horizon tasks.
4

State: Does not have log, plank or sticks
has wooden pickaxe equipped
Action: Mine stone
Is the action allowed?  No
Reasoning: The critic enforces that if the agent does not have logs, planks 
or sticks, it should mine logs.
Verifier
State: Has 3 cobblestone, 2 sticks, and is 
near a crafting table, 
Action: Craft stone pickaxe
Is the action allowed?  Yes
.
Verifier
State: Is near diamond ore, does not 
have an iron pickaxe equipped
Action: Mine diamond
Is the action allowed?  No
Reasoning: The critic enforces that the agent cannot mine a diamond without 
an iron pickaxe .
Verifier
State: Does not have 8 cobblestone, 
has iron ore, has coal ore 
Action: Craft furnace
Is the action allowed?  No
Reasoning: The critic enforces that if the agent does not have 8 cobblestone, 
it may not attempt to craft a furnace.
Verifier
State: Has 4 planks, is near crafting table
Action: Craft crafting table
Is the action allowed? No
Reasoning: The critic enforces that if the agent is already near a crafting table, 
it may not craft another one.
Verifier
Figure 2:Examples of the operation of the LTL-based verifier in a Minecraft Environment:
Each abstract state-action pair is checked against a B ¨uchi automaton encoding existing LTL con-
straints. If the action violates any constraint, the verifier provides feedback identifying the violated
rule, and the actor is prompted to replan.
3 METHODS
3.1 ARCHITECTUREOVERVIEW
We propose a hierarchical planning architecture that integrates large language models (LLMs) with
formal symbolic reasoning to achieve safe and efficient decision-making in complex environments.
The architecture consists of two interacting loops operating at different timescales:
Online actor loop:At each timestep, an LLM actor is given a natural language state description,
xfull =ϕ full(s)∈ Sfull and chooses a high-level actiona∈ A abstract. The action is verified against
current LTL constraints, defined overS abstract. If valid, it is executed via a low level controller.
Otherwise, the actor is informed that the chosen action is invalid and prompted to choose a new
action. Examples of the LTL verifier in action are shown in Figure 2.
Offline critic loop:Periodically, an LLM-based critic analyzes completed trajectories to identify
incorrect, inefficient or unsafe behaviors, proposing new LTL constraints or removing existing ones.
Updates are immediately incorporated into the verifier, affecting subsequent actions.
The separation of online reactive planning and offline symbolic refinement enables safe, efficient
and interpretable decision-making. The modular design also supports easy transfer across domains.
A full architectural diagram is presented in Figure 1.
3.2 DEFINING THE ATOMIC PROPOSITIONS
The choice of variables inS abstract directly affects the critic’s expressive power and tractability. For
generalist environments like Behavior, we automate the design ofS abstract, initializing it with vari-
ables needed for goal satisfaction and safety constraints, and then augmenting it based on observed
state changes during exploratory rollouts. This ensures the abstract state is both task-aware and
environment-adaptive while avoiding excessive manual design (details in Appendix A.2.1).
3.3 PLANNING AS AGRAPHTRAVERSALPROBLEM
We frame efficient planning as a shortest path problem under safety constraints. Each primitive
action has unit cost, as LLM calls dominate execution time. The agent aims to reach a state inS goal
from its current state in as few steps as possible, while avoidingS unsafe.
5

We model the problem as a bipartite graphG. One partition of this graph consists of symbolic states
Sabstract, while the other partition consists ofSabstract × Aabstract. Edges froms∈ Sabstract to(s, a)exist
only ifais allowed by current LTL constraints; edges from(s, a)tos ′ represent state transitions.
This bipartite structure explicitly separates the roles of the actor, which selects edges from states to
state-action pairs, and the critic, which prunes edges via constraints.
Due to an exponential number of nodes, finding the shortest path in this graph is exponentially
hard, motivating the need for LLMs to guide exploration via natural language reasoning, efficiently
navigating the graph despite its combinatorial complexity.
3.4 LLM ACTOR: GUIDEDEXPLORATION
The LLM actor receives a full state descriptionxfull and proposes a high-level action from the action
spaceAsuch as “mine stone” or “grasp plywood”. In the bipartite graphG, the actor chooses
an edge flowing out from the agents current statex abstract, which is legal as per the current LTL
constraints. The use of the LLM allows us to replace brute force exploration with semantically
guided traversal in a large symbolic space. Our architecture allows the direct use of existing LLM
planners. We adopt InnerMonologue (Huang et al., 2022b) for Behavior, and both SayCan (Ahn
et al., 2022) and InnerMonologue for Minecraft. To ensure adaptivity and prevent overly restrictive
rules, the actor tracks repeated attempts of violations of LTL constraints; if a particular rule is
triggered beyond a fixed threshold, it is removed, allowing the agent to explore alternative strategies.
3.5 LOGICGUARD:THELINEARTEMPORALLOGIC-BASEDLLM CRITIC
Environment Feedback Overconstrained StatesShortest Path to Goal
start
goal
Constraining Rules:
have no wood => must mine wood
have furnace => must place furnace
State: has furnace, has no wood
State: Not near crafting table
Action: Craft wooden pickaxe
Environment Feedback: No crafting table found!
Implement rules that force 
goal oriented actions, 
disallow unhelpful actions No Valid 
Action
New Rules:
dont have wood => must mine wood
have furnace and have wood => must place furnace
New rule: 
Not near crafting table => Dont craft wooden pickaxe
Figure 3:Sources of LogicGuard generated laws:LogicGuard generates new LTL laws by observ-
ing complete trajectories. Particularly, it generates laws based on three sources: environment feed-
back, graph-based efficiency improvements, and contradiction detection in over-constrained states.
In our experiments, we choose to run the critic to analyze complete trajectories. In practice the critic
may be run more or less often depending on the requirements of the specific application. The critic
is prompted to identify inefficient behaviors and to propose new LTL constraints of the form
G(ϕs =⇒X(ϕ a)),(1)
whereϕ s is a boolean expression over symbolic state features, andϕ a specifies allowed or disal-
lowed actions. These constraints eliminate inefficient behaviors. For example,
G(agent has wooden pickaxe=⇒X(!action craft wooden pickaxe)),(2)
prevents crafting duplicate wooden pickaxes. Constraints are only generated ifϕ s is observed in the
trajectory, ensuring generalization grounded in data. Constraints are induced from three sources:
1.Environment feedback: Actions deemed invalid by the environment (e.g. soaking a rag
without turning on the tap or mining diamonds without an iron pickaxe) lead to an error
message from the environment. These actions are encoded into constraints to prevent future
errors.
2.Graph-based efficiency: The critic is prompted to analyze the symbolic task graph
from 3.3. The critic is asked to classify actions as efficient or inefficient, pruning wasteful
actions, with an emphasis on repetitive actions.
3.Overconstrained States: When current laws collectively eliminate all feasible actions in
a state, the system falls back to bare minimum hand-engineered laws. Offline, these states
are analyzed to refine or relax constraints, preventing overly restrictive rules.
6

Since the critic is only allowed to induce constraints grounded in trajectory data, all proposed rules
are traceable, and we may bound the number of possible rules that are generated.
Theorem 1.Let(s 1, a1, . . . , sN , aN )be a trajectory withs i ∈ Sabstract, and eacha i ∈ {0,1}m
a one-hot vector representing an action from a finite action spaceA abstract of sizem. Consider an
algorithm that generates LTL constraints of the form equation 1 whereϕ s is a boolean condition
over the symbolic state that holds for at least ones i in the trajectory andϕ a ∈ {ai,!a i}.
Then, the algorithm can generate at mostNdistinct such laws from the trajectory while ensuring
that, for every states∈ Sabstract, there exists at least one actiona∈ {0,1}m satisfying all LTL laws.
Proof.There are at mostNunique values fors i. Each constraint is of the formG(ϕ s ⇒X(ϕ a)),
andϕ s must hold for at least ones i, the number of distinctϕ s that can be constructed from the
trajectory is at mostN. Further, the algorithm can only decide if each action is allowed or disal-
lowed. As a consequence, the total number of laws is at most2N. However, since actions cannot
be simultaneously allowed and disallowed, the number of actions an algorithm operating under our
assumptions can make such that every state has at least one feasible action is at mostN.
In our bipartite graph representation, pruning edges based on observed trajectories reduces com-
plexity fromO(m·2 n)to linear in dataset size. Interpretable atomic propositions allow the critic to
generalize constraints to semantically equivalent but unseen states. Finally, the sparse structure of
goal-directed task graphs allows LogicGuard produces sample-efficient and robust behavior while
enforcing both safety and efficiency.
4 EXPERIMENTS
4.1 EXPERIMENTALSETUP
Our actors use OpenAI GPT-4.1 as a backbone LLM and our critics use o3-mini. All temperatures
are set to 0.1 to reduce stochasticity while still allowing exploration. As discussed in Section 2.3,
we evaluate LogicGuard in two embodied environments. Implementation details including prompts
and APs are presented in the appendix.
Behavior:We use the Behavior (Li et al., 2023) dataset, consisting of short-horizon (average hori-
zon: 14.6) household tasks with multiple independent subtasks. High-level actions and observations
are designed via the API and goal specifications from Li et al. (2024). Completion rate is the pri-
mary metric, as prior work shows non–chain-of-thought LLMs struggle in this domain. To support
diverse tasks and environments, atomic propositions are automatically generated, enabling Logic-
Guard for general diverse settings. We adopt InnerMonologue as the LLM actor. Given the diversity
of tasks and environments, implementing a reliable affordance function is challenging, which limits
the applicability of SayCan in this setting.
Minecraft:Minecraft provides a partially observable environment with compositional, interde-
pendent subgoals. We study the diamond-mining task (Guss et al., 2019), a long-horizon setting
(see Table 2) requiring a sequence of dependent subgoals without intermediate rewards. We inter-
face via the Mineflayer API (PrismarineJS Team, 2025), which provides structured observations and
path-planning utilities, upon which we design atomic actions. Evaluation metrics in this domain
are efficiency (number of high-level actions required to obtain a diamond) and safety (number of
failed or illegal actions). Unlike in Behavior, here we design hand-engineered atomic propositions,
highlighting LogicGuard’s ability to augment specialist agents for complex compositional goals.
4.2 BASELINES
Our modular architecture allows us to augment off-the-shelf LLM planners with our symbolic critic.
We focus on two representative planners:
InnerMonologue (Huang et al., 2022b):An LLM planner that interleaves natural language
thoughts and code actions, incorporating feedback at each step. This provides implicit reflection
and sequential planning. We use InnerMonologue in both Behavior and Minecraft.
7

SayCan (Ahn et al., 2022)A two-stage planner that filters feasible actions via affordances and
ranks them for goal relevance. We only evaluate SayCan in Minecraft, since affordance functions
do not scale to Behavior’s large, diverse action space. In Minecraft, SayCan is combined with
LogicGuard for LTL-based affordance filtering.
In Minecraft, LogicGuard refines constraints for both InnerMonologue and SayCan until perfor-
mance stabilizes (two iterations sufficed). In Behavior, LogicGuard augments InnerMonologue only,
and the critic is invoked on failed tasks iteratively for up to two iterations to prevent overconstrain-
ing successful trajectories. While LogicGuard supports hand-engineered LTL constraints, all our
experiments use only critic-generated laws. The only exception is the SayCan baseline in Minecraft,
which requires a hand-engineered affordance function.
4.3 RESULTS
4.3.1 BEHAVIORBENCHMARK: TASKCOMPLETION
Behavior (Li et al., 2023) consists of 100 short-horizon household tasks with multiple independent
subtasks (e.g., pick up objects, place items, open containers). Since tasks are short-horizon, we
focus on task completion rather than efficiency. We end all trajectories after 40 actions, or if the
actor chooses to declare it is done.
Table 1: Task completion rates on Behavior-100.
Method Completed Tasks
InnerMonologue 47%
InnerMonologue + LogicGuard 72%
4.3.2 MINECRAFT: EFFICIENCY ANDSAFETY
In Minecraft, the agent must mine a diamond from scratch, involving long-horizon dependencies
across mining and crafting subgoals. We evaluate efficiency (number of primitive actions to reach
key subgoals) and safety (number of failed or unsafe actions).
EfficiencyTable 2 shows the average number of primitives required to reach each subgoal. We
note a 23% increment in the performance of InnerMonologue in the diamond mining task. SayCan
is very easily distracted by the abstract nature of high level actions such as “explore”, and does
not make meaningful progress on the task. Our architecture identifies these drawbacks and blocks
exploration related actions till the right tools are available.
Table 2: Average primitive actions per subgoal (success rates in parentheses).
Method Wooden Tool Stone tool Iron Tool Diamond
SayCan N/A (0/5) N/A (0/5) N/A (0/5) N/A (0/5)
SayCan + LogicGuard 12.6(5/5) 17.6(5/5) 37.8(5/5) 45.4(5/5)
InnerMonologue 12.2 (5/5) 18.2 (5/5) 43.25 (4/5) 45.5 (4/5)
InnerMonologue + LogicGuard 9.4 (5/5) 14.4 (5/5) 32.0 (5/5) 35.8 (5/5)
SafetyWe measure failed actions and the number of unsafe actions blocked by the critic. Logic-
Guard significantly reduces both failure rates and unsafe actions (Table 3). Failures after LogicGuard
are due to path planning errors within Mineshafter’s API.
Our results highlight that LogicGuard generalizes across task structure and horizon, helping LLM
actors act more reliably, safely, and efficiently.
8

Table 3: Agent safety metrics. We report the number of failed actions and the number of unsafe
actions blocked by the critic (if applicable). Lower is better.
Method Failed Actions Critic-Blocked Unsafe Actions
InnerMonologue 23% N/A
InnerMonologue + LogicGuard 4.5% 15%
5 DISCUSSION
5.1 LOGICGUARD MITIGATES SYSTEMATICLLMACTOR FAILURES
Naive LLM actors often repeat actions after task completion or ignore environment feedback, lead-
ing to inefficiency and loops. In Behavior, an actor may repeatedly pick up or place already orga-
nized objects; in Minecraft, it can mine blocks beyond task requirements. These failures stem from
limited reasoning and prompt overload. LogicGuard addresses these issues by detecting redundant
or failed actions and blocking them based on task conditions. This enforces interpretable, verifiable
constraints, breaking loops and improving both reliability and task efficiency.
5.2 ATOMIC PROPOSITIONS ARE A KEY DESIGN CHOICE
Atomic propositions (APs) define the variables the critic uses to construct LTL constraints, directly
controlling rule expressivity. In the Behavior dataset, the most common failure mode for Logic-
Guard is because our APs are insufficiently expressive. For instance, our current automated AP
generation treats each item in the environment as an independent entity, which complicates com-
binatorial tasks. Consider placing four plates into four boxes such that each box contains at least
one plate. There are 24 feasible solutions. Encoding a single LTL formula that captures all feasi-
ble final states is highly complex for the critic, which must account for all possible permutations.
By contrast, in Minecraft we hand engineered APs to precisely capture task-relevant state features.
This targeted design simplifies rule generation, reduces combinatorial complexity, and enables more
reliable constraint synthesis.
5.3 GENERALIST VSSPECIALIST AGENTS
LogicGuard improves performance across diverse domains. In Behavior, the environment is un-
known and contains rules the LLM cannot anticipate (e.g., items must be inside a sink before soak-
ing), which the critic must discover iteratively, akin to human learning. In Minecraft, extensive
textual documentation allows the LLM to succeed with minimal guidance. Evaluating both domains
demonstrates that LogicGuard supports generalist agents in novel settings and specialist agents in
structured, long-horizon tasks.
6 CONCLUSION ANDFUTUREWORK
We introduced a modular actor-critic architecture in which an LLM critic supervises an LLM actor
using linear temporal logic (LTL) constraints over abstracted versions of full trajectories. The critic
operates at a slower timescale and applies zero-shot reasoning to identify and correct unsafe or inef-
ficient behavior in a few iterations. Our modular architecture enables us to use existing off-the-shelf
LLM planners as actors. The use of LTL constraints guarantees shielding of the LLM from unsafe or
inefficient behavior. By expressing constraints in LTL over human-readable atomic propositions, we
gain a symbolic structure that is immediately enforceable and human verifiable. We demonstrate our
approach in two contrasting embodied domains, achieving significant improvements over baseline
off-the-shelf LLM agents.
Several directions remain for future work. First, a critic could leverage annotated expert trajectories
to imitate optimal behavior. Second, in dynamic environments, incorporating mathematical models
of the environment into the critic could enable generation of LTL laws that evolve over time. Such
adaptive laws are particularly relevant for multi-agent coordination and human-robot teaming, where
modeling other agents can inform constraint synthesis. Finally, we aim to extend these ideas to
9

real-world robotics, where online decisions may rely on smaller, potentially unreliable models that
require formal constraints. Overall, our approach demonstrates that formal logic-based constraints
provide a promising path toward safe, scalable, and general-purpose LLM agents.
10

7 ETHICSSTATEMENT
Our work focuses on improving LLM-based planners in simulated environments (Behavior and
Minecraft) and does not involve human subjects or sensitive data. LLMs can exhibit unsafe or un-
reliable behavior, and overreliance on them in real-world robotics could be hazardous. Our research
hopes to draw attention and inspire further work towards safety nets for blackbox foundational mod-
els. Our framework is intended as a first step to improve reliability and safety in LLM-driven agents.
8 REPRODUCIBILITY STATEMENT
We provide detailed descriptions of all environments, prompts and LLM models used in our experi-
ments. While we use OpenAI’s GPT-4.1 and o3-mini APIs, which are inherently stochastic even at
low temperature.
ACKNOWLEDGMENTS
We acknowledge the use of ChatGPT for assistance in improving the wording and grammar of this
document.
REFERENCES
Michael Ahn, Anthony Brohan, Noah Brown, Yevgen Chebotar, Omar Cortes, Byron David, Chelsea
Finn, Chuyuan Fu, Keerthana Gopalakrishnan, Karol Hausman, et al. Do as I Can, not as I Say:
Grounding language in robotic affordances.arXiv preprint arXiv:2204.01691, 2022.
Mohammed Alshiekh, Roderick Bloem, R ¨udiger Ehlers, Bettina K ¨onighofer, Scott Niekum, and
Ufuk Topcu. Safe reinforcement learning via shielding. InProceedings of the AAAI conference
on artificial intelligence, volume 32, 2018.
Rune Birkmose, Nathan Mørkeberg Reece, Esben Hofstedt Norvin, Johannes Bjerva, and Mike
Zhang. On-device LLMs for home assistant: Dual role in intent detection and response generation.
arXiv preprint arXiv:2502.12923, 2025.
Mark Chen, Jerry Tworek, Heewoo Jun, Qiming Yuan, Henrique Ponde De Oliveira Pinto, Jared
Kaplan, Harri Edwards, Yuri Burda, Nicholas Joseph, Greg Brockman, et al. Evaluating large
language models trained on code.arXiv preprint arXiv:2107.03374, 2021.
Yongchao Chen, Rujul Gandhi, Yang Zhang, and Chuchu Fan. Nl2tl: Transforming natural lan-
guages to temporal logics using large language models.arXiv preprint arXiv:2305.07766, 2023.
Yongchao Chen, Jacob Arkin, Charles Dawson, Yang Zhang, Nicholas Roy, and Chuchu Fan. Au-
totamp: Autoregressive task and motion planning with llms as translators and checkers. In2024
IEEE International conference on robotics and automation (ICRA), pp. 6695–6702. IEEE, 2024.
Yihong Dong, Kangcheng Luo, Xue Jiang, Zhi Jin, and Ge Li. Pace: Improving prompt with actor-
critic editing for large language model.arXiv preprint arXiv:2308.10088, 2023.
Alexandre Duret-Lutz and Denis Poitrenaud. Spot: an extensible model checking library using
transition-based generalized B¨uchi automata. InProceedings of the 12th IEEE/ACM International
Symposium on Modeling, Analysis, and Simulation of Computer and Telecommunication Systems
(MASCOTS’04), pp. 76–83, V olendam, The Netherlands, October 2004. IEEE Computer Society.
doi: 10.1109/MASCOT.2004.1348184.
Connor Esterwood and Lionel P Robert Jr. Three strikes and you are out!: The impacts of multiple
human–robot trust violations and repairs on robot trustworthiness.Computers in Human behavior,
142:107658, 2023.
G. E. Fainekos, H. Kress-Gazit, and G. J. Pappas. Temporal logic motion planning for mobile robots.
InIEEE Int. Conf. on Robotics and Automation, pp. 2032–2037, Barcelona, Spain, April 2005.
11

Linxi Fan, Guanzhi Wang, Yunfan Jiang, Ajay Mandlekar, Yuncong Yang, Haoyi Zhu, Andrew Tang,
De-An Huang, Yuke Zhu, and Anima Anandkumar. Minedojo: Building open-ended embodied
agents with internet-scale knowledge.Advances in Neural Information Processing Systems, 35:
18343–18362, 2022.
Xiaocong Fan, Sooyoung Oh, Michael McNeese, John Yen, Haydee Cuevas, Laura Strater, and
Mica R Endsley. The influence of agent reliability on trust in human-agent collaboration. In
Proceedings of the 15th European conference on Cognitive ergonomics: the ergonomics of cool
interaction, pp. 1–8, 2008.
Xingang Guo, Darioush Keivan, Usman Syed, Lianhui Qin, Huan Zhang, Geir Dullerud, Peter
Seiler, and Bin Hu. Controlagent: Automating control system design via novel integration of
LLM agents and domain expertise.arXiv preprint arXiv:2410.19811, 2024.
William H Guss, Brandon Houghton, Nicholay Topin, Phillip Wang, Cayden Codel, Manuela
Veloso, and Ruslan Salakhutdinov. Minerl: A large-scale dataset of minecraft demonstrations.
arXiv preprint arXiv:1907.13440, 2019.
Ahmed Hosny, Chintan Parmar, John Quackenbush, Lawrence H Schwartz, and Hugo JWL Aerts.
Artificial intelligence in radiology.Nature Reviews Cancer, 18(8):500–510, 2018.
Jie Huang and Kevin Chen-Chuan Chang. Towards reasoning in large language models: A survey.
arXiv preprint arXiv:2212.10403, 2022.
Wenlong Huang, Pieter Abbeel, Deepak Pathak, and Igor Mordatch. Language models as zero-shot
planners: Extracting actionable knowledge for embodied agents. InInternational conference on
machine learning, pp. 9118–9147. PMLR, 2022a.
Wenlong Huang, Fei Xia, Ted Xiao, Harris Chan, Jacky Liang, Pete Florence, Andy Zeng, Jonathan
Tompson, Igor Mordatch, Yevgen Chebotar, et al. Inner monologue: Embodied reasoning through
planning with language models.arXiv preprint arXiv:2207.05608, 2022b.
Subbarao Kambhampati, Karthik Valmeekam, Lin Guan, Mudit Verma, Kaya Stechly, Siddhant
Bhambri, Lucas Saldyt, and Anil B Murthy. Position: LLMs can’t plan, but can help planning in
LLM-modulo frameworks. InForty-first International Conference on Machine Learning, 2024.
Chengshu Li, Fei Xia, Roberto Mart´ın-Mart´ın, Michael Lingelbach, Sanjana Srivastava, Bokui Shen,
Kent Elliott Vainio, Cem Gokmen, Gokul Dharan, Tanish Jain, Andrey Kurenkov, Karen Liu,
Hyowon Gweon, Jiajun Wu, Li Fei-Fei, and Silvio Savarese. igibson 2.0: Object-centric sim-
ulation for robot learning of everyday household tasks. In Aleksandra Faust, David Hsu, and
Gerhard Neumann (eds.),Proceedings of the 5th Conference on Robot Learning, volume 164
ofProceedings of Machine Learning Research, pp. 455–465. PMLR, 08–11 Nov 2022a. URL
https://proceedings.mlr.press/v164/li22b.html.
Chengshu Li, Ruohan Zhang, Josiah Wong, Cem Gokmen, Sanjana Srivastava, Roberto Mart ´ın-
Mart´ın, Chen Wang, Gabrael Levine, Michael Lingelbach, Jiankai Sun, et al. Behavior-1k: A
benchmark for embodied ai with 1,000 everyday activities and realistic simulation. InConference
on Robot Learning, pp. 80–93. PMLR, 2023.
Manling Li, Shiyu Zhao, Qineng Wang, Kangrui Wang, Yu Zhou, Sanjana Srivastava, Cem Gokmen,
Tony Lee, Erran Li Li, Ruohan Zhang, et al. Embodied agent interface: Benchmarking llms for
embodied decision making.Advances in Neural Information Processing Systems, 37:100428–
100534, 2024.
Yujia Li, David Choi, Junyoung Chung, Nate Kushman, Julian Schrittwieser, R ´emi Leblond, Tom
Eccles, James Keeling, Felix Gimeno, Agustin Dal Lago, et al. Competition-level code generation
with alphacode.Science, 378(6624):1092–1097, 2022b.
Jason Xinyu Liu, Ziyi Yang, Ifrah Idrees, Sam Liang, Benjamin Schornstein, Stefanie Tellex, and
Ankit Shah. Grounding complex natural language commands for temporal tasks in unseen envi-
ronments. InConference on Robot Learning, pp. 1084–1110. PMLR, 2023.
Amir Pnueli. The temporal logic of programs. In18th annual symposium on foundations of computer
science (sfcs 1977), pp. 46–57. ieee, 1977.
12

PrismarineJS Team. Mineflayer: A high-level javascript api for creating minecraft bots. GitHub
repository, 2025.https://github.com/PrismarineJS/mineflayer.
Xavier Puig, Kevin Ra, Marko Boben, Jiaman Li, Tingwu Wang, Sanja Fidler, and Antonio Tor-
ralba. Virtualhome: Simulating household activities via programs. InProceedings of the IEEE
Conference on Computer Vision and Pattern Recognition, pp. 8494–8502, 2018.
Zachary Ravichandran, Alexander Robey, Vijay Kumar, George J Pappas, and Hamed Hassani.
Safety guardrails for llm-enabled robots.arXiv preprint arXiv:2503.07885, 2025.
Tom Silver, Varun Hariprasad, Reece S Shuttleworth, Nishanth Kumar, Tom ´as Lozano-P´erez, and
Leslie Pack Kaelbling. Pddl planning with pretrained large language models. InNeurIPS 2022
foundation models for decision making workshop, 2022.
Guanzhi Wang, Yuqi Xie, Yunfan Jiang, Ajay Mandlekar, Chaowei Xiao, Yuke Zhu, Linxi Fan,
and Anima Anandkumar. V oyager: An open-ended embodied agent with large language models.
arXiv preprint arXiv:2305.16291, 2023a.
Yixuan Wang, Ruochen Jiao, Sinong Simon Zhan, Chengtian Lang, Chao Huang, Zhaoran Wang,
Zhuoran Yang, and Qi Zhu. Empowering autonomous driving with large language models: A
safety perspective.arXiv preprint arXiv:2312.00812, 2023b.
Jason Wei, Xuezhi Wang, Dale Schuurmans, Maarten Bosma, Fei Xia, Ed Chi, Quoc V Le, Denny
Zhou, et al. Chain-of-thought prompting elicits reasoning in large language models.Advances in
neural information processing systems, 35:24824–24837, 2022.
Tichakorn Wongpiromsarn, Ufuk Topcu, and Richard M Murray. Receding horizon temporal logic
planning.IEEE Transactions on Automatic Control, 57(11):2817–2830, 2012.
Zhenyu Wu, Ziwei Wang, Xiuwei Xu, Jiwen Lu, and Haibin Yan. Embodied task planning with
large language models.arXiv preprint arXiv:2307.01848, 2023.
Ruihan Yang, Fanghua Ye, Jian Li, Siyu Yuan, Yikai Zhang, Zhaopeng Tu, Xiaolong Li, and Deqing
Yang. The lighthouse of language: Enhancing LLM agents via critique-guided improvement.
arXiv preprint arXiv:2503.16024, 2025.
Ziyi Yang, Shreyas S. Raman, Ankit Shah, and Stefanie Tellex. Plug in the safety chip: Enforcing
constraints for LLM-driven robot agents. In2024 IEEE International Conference on Robotics
and Automation (ICRA), pp. 14435–14442. IEEE, May 2024. doi: 10.1109/icra57147.2024.
10611447. URLhttp://dx.doi.org/10.1109/ICRA57147.2024.10611447.
Filippo Ziliotto, Tommaso Campari, Luciano Serafini, and Lamberto Ballan. Tango: training-free
embodied ai agents for open-world tasks. InProceedings of the Computer Vision and Pattern
Recognition Conference, pp. 24603–24613, 2025.
A APPENDIX
A.1 LINEARTEMPORALLOGICOPERATORS
Linear Temporal Logic(LTL) (Pnueli, 1977) provides a formal language for expressing temporal
properties over sequences of states. LTL formulas are built using the usual Boolean operators, with
four temporal operators .
1.X(ψ):ψholds at the next timestep.
2.F(ψ): eventuallyψholds.
3.G(ψ):ψholds in all future states.
4.ψ 1U ψ2 means thatψ 1 holds untilψ 2 becomes true
13

A.2 IMPLEMENTATION DETAILS: BEHAVIOR
A.2.1 AUTOMATION OF ATOMIC PREDICATE GENERATION
As discussed in our main paper, the choice of atomic predicates is crucial to the success of the critic.
For the Behavior dataset we automate this process. First, we design a minimal set of APs to describe
the goal state manually. Then, for the remaining APs, we use an API (Li et al., 2024) to detect
actions and observations as per Table 4. If an action or an observation is detected, it is added to the
AP dictionary. This way, the actor LLM filters an exponentially large space of APs.
Source Generated Atomic Propositions (APs)
Robot hands If left/right hand holds an object, generate<object> in hand.
Object states For each object and state:
InsideRoomTypes:<obj> in <room>
Burnt:<obj> is burnt
Cooked:<obj> is cooked
Stained:<obj> is stained
Dusty:<obj> is dusty
Frozen:<obj> is frozen
HeatSourceOrSink:<obj> is heat source or sink
Open:<obj> is open
Sliced:<obj> is sliced
Soaked:<obj> is soaked
ToggledOn:<obj> is toggled on
Object relations For each object pair(o 1, o2)(excluding floor/self):
Inside:<o1> inside <o2>
NextTo:<o1> next to <o2>
OnFloor:<o1> on floor
OnTop:<o1> on top of <o2>
Under:<o1> is under <o2>
Actions (generic) For each simple action (e.g.,open,close,slice,clean), generate
<action> <object>.
Actions (binary) For binary/2-argument actions (e.g.,place ontop,place inside,
transfer contents ontop,place nextto), generate
<obj1> <action> <obj2>for all ordered pairs withobj1 != obj2.
Termination Always include the terminal propositiondone.
Table 4: Automatic generation rules for atomic propositions (APs) used in iGibson experiments.
The code systematically maps robot inventory, per-object states, pairwise relations, and actions into
sanitized propositional symbols for subsequent LTL processing.
A.3 IMPLEMENTATION DETAILS: MINECRAFT
A.3.1 MINEFLAYERAPIINTERFACE
We interface with Minecraft using the Mineflayer API, which exposes high-level observations as
structured JSON objects and provides access to built-in path-planning routines. We define a set
of action primitives on top of this interface to abstract the agent’s decision space while preserving
task complexity. Each primitive internally invokes Mineflayer’s planners and lower-level control
routines. The full list of primitives is as follows:
1.mineBlock(bot, blockName): Mines 1 block of typeblockName, provided it is
visible within a 32-block radius.
2.placeItem(bot, blockName, position): Places a block at a specified position,
assuming the location is unoccupied and adjacent to an occupied block.
14

3.craftItem(bot, itemName): Crafts 1 item of typeitemName, assuming all in-
gredients are present in the agent’s inventory. Recipes that require a crafting table assume
one is nearby.
4.smeltItem(bot, itemName, fuelName): Smelts 1 item of typeitemNameus-
ingfuelName, assuming both are present in the agent’s inventory and a furnace is nearby.
5.equipItem(bot, itemName, destination): Equips tools or armor. Some
blocks require a minimum tool tier to mine, and the appropriate tool must be equipped.
6.exploreUntil(bot, direction, condition): Causes the agent to explore in
a specified direction until a user-defined condition is met (e.g., locating a specific block).
These primitives allow for rich compositional behavior while delegating locomotion to Mineflayer’s
planners. The full sequence of subgoals required to successfully mine a diamond in this setup is as
follows:
1. Obtain wooden logs.
2. Craft logs into sticks and planks.
3. Craft a wooden pickaxe.
4. Mine stone blocks using the wooden pickaxe.
5. Craft a stone pickaxe and a furnace.
6. Obtain raw iron by mining iron blocks.
7. Smelt raw iron into iron ingots.
8. Craft an iron pickaxe.
9. Explore the world and mine a diamond block.
This structured task allows us to evaluate the ability of our actor-critic framework to perform multi-
stage reasoning, tool use, and resource management over long horizons.
A.3.2 LIST OF ATOMIC PROPOSITIONS INMINECRAFT
We have two sets of atomic propositions, one for observations and one for high-level actions.
15

Proposition Meaning
obs has log Agent has at least 1 log
obs has plank Agent has at least 1 plank
obs has 2x plank Agent has≥2planks
obs has 3x plank Agent has≥3planks
obs has 4x plank Agent has≥4planks
obs has 11x plank Agent has≥11planks
obs has 2x stick Agent has≥2sticks
obs has 3x cobble Agent has≥3cobblestone
obs has 8x cobble Agent has≥8cobblestone
obs has 11x cobble Agent has≥11cobblestone
obs has wood pickaxe Agent has wooden pickaxe
obs has stone pickaxe Agent has stone pickaxe
obs has iron pickaxe Agent has iron pickaxe
obs has diamond Agent has at least 1 diamond
obs has iron ingot Agent has≥1iron ingot
obs has 3x iron ingot Agent has≥3iron ingots
obs has 1x iron ore Agent has≥1iron ore
obs has 2x iron ore Agent has≥2iron ore
obs has 3x iron ore Agent has≥3iron ore
obs has crafting table Agent has crafting table
obs has furnace Agent has furnace
obs has fuel Agent has fuel (e.g., coal)
obs near crafting table Agent is near crafting table
obs near furnace Agent is near furnace
obs diamond in chunk Diamonds detected nearby
obs iron in chunk Iron ore detected nearby
obs coal in chunk Coal detected nearby
obs iron pickaxe equipped Iron pickaxe is equipped
obs stone pickaxe equipped Stone pickaxe is equipped
obs wood pickaxe equipped Wooden pickaxe is equipped
Table 5: Atomic propositions used for LTL constraints and their meanings.
Action Meaning
action mine log Mine wood logs
action mine stone Mine stone
action mine iron ore Mine iron ore
action mine coal Mine coal
action mine diamond Mine diamond
action craft planks Craft planks from logs
action craft stick Craft sticks from planks
action craft wooden pickaxe Craft wooden pickaxe
action craft stone pickaxe Craft stone pickaxe
action craft iron pickaxe Craft iron pickaxe
action craft crafting table Craft a crafting table
action craft furnace Craft a furnace
action smelt iron Smelt iron ore into ingots
action equip wood pickaxe Equip wooden pickaxe
action equip stone pickaxe Equip stone pickaxe
action equip iron pickaxe Equip iron pickaxe
action explore general Explore randomly
action explore diamond down Explore downward for diamonds
action place crafting table Place crafting table
action place furnace Place furnace
Table 6: Action variables used in planning and their associated meanings.
16

A.3.3 LIST OFLTLLAWS IMPOSED FOR EACH ACTOR
SayCanThe hard-hand engineered safety rules that prevent illegal actions are given below:
1.LTL:G(¬obs iron pickaxe equipped→X(¬action mine diamond))
Explanation:Diamonds cannot be mined unless an iron pickaxe is equipped.
2.LTL:G(¬obs near crafting table→X(¬action craft wooden pickaxe∧
¬action craft stone pickaxe∧ ¬actioncraft iron pickaxe))
Explanation:Cannot craft any type of pickaxe unless near a crafting table.
3.LTL:G(¬obs near crafting table→X(¬action craft furnace))
Explanation:Cannot craft a furnace unless near a crafting table.
4.LTL:G(¬(obs stone pickaxe equipped∨obs iron pickaxe equipped)→
X(¬action mine iron ore))
Explanation:Cannot mine iron ore unless a stone or iron pickaxe is equipped.
5.LTL:G(¬(obs wood pickaxe equipped∨obs stone pickaxe equipped∨
obs iron pickaxe equipped)→X(¬action mine stone))
Explanation:Cannot mine stone unless any pickaxe is equipped.
6.LTL:G(¬obs has iron pickaxe→X(¬action equip iron pickaxe))
Explanation:Cannot equip an iron pickaxe unless the agent has one.
7.LTL:G(¬obs has 3x plank∨ ¬obs has 2x stick→
X(¬action craft wooden pickaxe))
Explanation:Cannot craft a wooden pickaxe without enough planks and sticks.
8.LTL:G(¬obs has 4x plank→X(¬action craft crafting table))
Explanation:Cannot craft a crafting table without 4 planks.
9.LTL:G(¬obs has 8x cobble→X(¬action craft furnace))
Explanation:Cannot craft a furnace without 8 cobblestone.
10.LTL:G(¬(obs has 2x stick∧obs has 3x iron ingot)→
X(¬action craft iron pickaxe))
Explanation:Cannot craft an iron pickaxe without 2 sticks and 3 iron ingots.
11.LTL:G(¬obs has 3x cobble∨ ¬obs has 2x stick→
X(¬action craft stone pickaxe))
Explanation:Cannot craft a stone pickaxe without cobblestone and sticks.
12.LTL:G(¬obs coal in chunk∨ ¬(obs wood pickaxe equipped∨
obs stone pickaxe equipped∨obs iron pickaxe equipped)→
X(¬action mine coal))
Explanation:Cannot mine coal unless coal is nearby and a pickaxe is equipped.
13.LTL:G(¬obs has log→X(¬action craft planks))
Explanation:Cannot craft planks without logs.
14.LTL:G(¬obs has 2x plank→X(¬action craft stick))
Explanation:Cannot craft sticks without 2 planks.
15.LTL:G(¬obs near furnace∨ ¬obs has 1x iron ore∨ ¬obs has fuel→
X(¬action smelt iron))
Explanation:Cannot smelt iron without a furnace, fuel, and iron ore.
16.LTL:G(¬obs has wood pickaxe→X(¬action equip wood pickaxe))
Explanation:Cannot equip a wooden pickaxe unless the agent has one.
17.LTL:G(¬obs has stone pickaxe→X(¬action equip stone pickaxe))
Explanation:Cannot equip a stone pickaxe unless the agent has one.
18.LTL:G(¬obs has crafting table→X(¬action place crafting table))
Explanation:Cannot place a crafting table unless the agent has one.
19.LTL:G(¬obs has furnace→X(¬action place furnace))
Explanation:Cannot place a furnace unless the agent has one.
The soft LTL rules implemented by the critic are as follows:
17

1.LTL:G(¬obs has log∧ ¬obshas plank∧ ¬obshas 2x stick∧ ¬obshas iron pickaxe→
X(action mine log))
Explanation:If the agent lacks logs, planks, sticks, and an iron pickaxe, it should mine
wood logs.
2.LTL:G(obs has log∧ ¬obshas plank→X(action craft planks))
Explanation:If the agent has logs but no planks, it should craft planks.
3.LTL:G(obs has 2x plank∧ ¬obshas 2x stick→X(action craft stick))
Explanation:If the agent has planks but no sticks, it should craft sticks.
4.LTL:G(obs has 4x plank∧obs has 2x stick∧ ¬obs has crafting table∧
¬obs near crafting table→X(action craft crafting table))
Explanation:If the agent has 4 planks and 2 sticks but no crafting table is nearby or
already crafted, it must craft a crafting table.
5.LTL:G(obs has 4x plank∧obs has 2x stick∧obs has crafting table∧
¬obs near crafting table→X(action place crafting table))
Explanation:If the agent has 4 planks, 2 sticks, and a crafting table but is not near
one, it should place the crafting table.
6.LTL:G(obs has 3x plank∧obs has 2x stick∧ ¬obs has wood pickaxe∧
obs near crafting table→X(action craft wooden pickaxe))
Explanation:If the agent has 3 planks, 2 sticks, is near a crafting table, and doesn’t
already have a wooden pickaxe, it should craft one.
7.LTL:G(obs has wooden pickaxe∧ ¬obs wooden pickaxe equipped∧
¬obs has 3x cobble→X(action equip wooden pickaxe))
Explanation:If the agent has a wooden pickaxe but it isn’t equipped and it lacks three
cobblestones, it should equip the pickaxe.
8.LTL:G(obs wood pickaxe equipped∧ ¬obshas 3x cobble∧ ¬obshas stone pickaxe∧
¬obs has 2x stick→X(action mine stone))
Explanation:If equipped with a wooden pickaxe and lacking stone, the agent should
mine cobblestone.
9.LTL:G(obs wood pickaxe equipped∧obs has 3x cobble∧ ¬obshas stone pickaxe→
X(action craft stone pickaxe))
Explanation:If the agent has 3 cobblestones and a wooden pickaxe equipped, it should
craft a stone pickaxe.
10.LTL:G(obs has 3x iron ore∧obs near furnace∧obs has fuel∧
¬obs has 3x iron ingot→X(action smelt iron))
Explanation:If the agent has 3 iron ore, is near a furnace, has fuel, and lacks 3 ingots,
it should smelt iron.
11.LTL:G(obs has 3x iron ingot∧obs has 2x stick∧obs near crafting table∧
¬obs has iron pickaxe→X(action craft iron pickaxe))
Explanation:If the agent has the ingredients but no iron pickaxe, it should craft one.
12.LTL:G(obs has iron pickaxe∧ ¬obs iron pickaxe equipped∧ ¬obs has 2x stick→
X(action equip iron pickaxe))
Explanation:If the agent owns an iron pickaxe but hasn’t equipped it, it should equip
the pickaxe.
13.LTL:G(obs iron pickaxe equipped∧ ¬obs diamond in chunk→
X(action explore diamond down))
Explanation:If an iron pickaxe is equipped and no diamonds are nearby, explore
downward.
14.LTL:G(¬obs has iron pickaxe∧ ¬obs iron pickaxe equipped→
X(¬action explore diamond down))
Explanation:Do not explore for diamonds unless an iron pickaxe is available and
equipped.
15.LTL:G(obs has fuel∧obs iron in chunk∧obs coal in chunk→
X(¬action explore general))
Explanation:Do not explore if iron and coal are already known to be nearby.
18

InnerMonologueSince our safety violations in SayCan simply lead to environmental feedback
and new laws, we do not include any hand-engineered safety laws in InnerMonologue.
•LTL:G(¬obs has log∧ ¬obs has plank∧ ¬obs has 2x stick∧
¬obs has iron pickaxe→X(action mine log))
Explanation:If you don’t have logs, planks, or sticks, mine logs.
•LTL:G(obs has log∧ ¬obshas plank→X(action craft planks))
Explanation:If you have logs but no planks, craft planks.
•LTL:G(obs has 4x plank∧ ¬obsnear crafting table∧ ¬obshas crafting table→
X(action craft crafting table))
Explanation:If you have 4 planks, aren’t near a crafting table, and don’t have one,
craft a crafting table.
•LTL:G(obs has crafting table∧obs has plank∧ ¬obs near crafting table→
X(action place crafting table))
Explanation:If you have a crafting table and a plank, but aren’t near one, place the
crafting table.
•LTL:G(obs has 3x plank∧obs has 2x stick∧obs near crafting table∧
¬obs has wood pickaxe→X(action craft wooden pickaxe))
Explanation:If you have 3 planks, 2 sticks, are near a crafting table, and don’t have a
wooden pickaxe, craft one.
•LTL:G(obs has 3x cobble∧obs has 2x stick∧obs near crafting table∧
¬obs has stone pickaxe→X(action craft stone pickaxe))
Explanation:If you have 3 cobble, 2 sticks, are near a crafting table, and don’t have a
stone pickaxe, craft one.
•LTL:G(obs has 8x cobble∧obs near crafting table∧ ¬obs has furnace∧
¬obs near furnace→X(action craft furnace))
Explanation:If you have 8 cobble, are near a crafting table, and don’t have or see a
furnace, craft one.
•LTL:G(obs has 3x iron ore∧obs near furnace∧obs has fuel∧
¬(obs has iron pickaxe∨obs has 3x iron ingot)→X(action smelt iron))
Explanation:If you have iron ore and fuel, are near a furnace, and don’t already have
iron ingots or a pickaxe, smelt iron.
•LTL:G(obs has 3x iron ingot∧obs has 2x stick∧obs near crafting table∧
¬obs has iron pickaxe→X(action craft iron pickaxe))
Explanation:If you have 3 iron ingots, 2 sticks, are near a crafting table, and don’t
have an iron pickaxe, craft one.
•LTL:G(obs has iron pickaxe∧ ¬obs iron pickaxe equipped→
X(action equip iron pickaxe))
Explanation:If you have an iron pickaxe but it’s not equipped, equip it.
•LTL:G(obs diamond in chunk∧obs iron pickaxe equipped→
X(action mine diamond))
Explanation:If diamonds are nearby and an iron pickaxe is equipped, mine the
diamond.
•LTL:G(¬obs diamond in chunk∧obs iron pickaxe equipped→
X(action explore diamond down))
Explanation:If no diamonds are visible and an iron pickaxe is equipped, explore
downward for diamonds.
•LTL:G(obs diamond in chunk∨ ¬obs iron pickaxe equipped→
X(¬action explore diamond down))
Explanation:If diamonds are visible or no iron pickaxe is equipped, do not explore
downward.
•LTL:G(¬obs wood pickaxe equipped∧ ¬obs stone pickaxe equipped∧
¬obs iron pickaxe equipped→X(¬action mine stone))
Explanation:If no pickaxe is equipped, don’t mine stone.
19

•LTL:G(¬obs stone pickaxe equipped∧ ¬obs iron pickaxe equipped→
X(¬action mine iron ore))
Explanation:Don’t mine iron ore unless a stone or iron pickaxe is equipped.
•LTL:G(¬obs has 8x cobble→X(¬action craft furnace))
Explanation:Don’t craft a furnace without 8 cobblestone.
•LTL:G(¬obs wood pickaxe equipped∧ ¬obs stone pickaxe equipped∧
¬obs iron pickaxe equipped→X(¬action mine coal))
Explanation:Don’t mine coal without a pickaxe equipped.
•LTL:G(¬obs has 3x plank∨ ¬obs has 2x stick∨ ¬obs near crafting table∨
obs has wood pickaxe→X(¬action craft wooden pickaxe))
Explanation:Don’t craft a wooden pickaxe unless you have the materials and don’t
already have one.
•LTL:G(¬obs has 3x cobble∨ ¬obs has 2x stick∨ ¬obs near crafting table∨
obs has stone pickaxe→X(¬action craft stone pickaxe))
Explanation:Don’t craft a stone pickaxe unless you have materials and don’t already
have one.
•LTL:G(¬obs has 3x iron ingot∨ ¬obshas 2x stick∨ ¬obsnear crafting table∨
obs has iron pickaxe→X(¬action craft iron pickaxe))
Explanation:Don’t craft an iron pickaxe unless you have materials and don’t already
have one.
A.4 PROMPTS
Here, we provide the general prompts that guide the LLM. Most prompts are implemented as Python
f-strings; to keep them concise, we show the templates without substituting the variable names.
A.4.1 BEHAVIOR
Actor promptsFirst, the context prompt:
1Problem:
2You are designing instructions for a household robot.
3The goal is to guide the robot to modify its environment from its
current state to a desired final state.
4The input will be the current environment state, the target environment
state, the objects you can interact with in the environment.
5The output should be the next action command that the robot may execute
in order to make progress towards achieving the target state.
6
7Data format: After # is the explanation.
8
9Format of the states:
10The current environment state is described as a list of dictionaries.
Each dictionary describes an object, its category, followed by its
description, which includes several of its properties including a
description of its location.
11For example:
12{’name’: ’plywood_1’,
13’category’: ’plywood’,
14’State description ’:
15[’Location: living_room’, ’Stain status: Clean’, ’Dust status: Clean’,
’Touching: room_floor_living_room_0’, ’Touching: plywood_0’,
’Touching: room_floor_kitchen_0’, ’On top of:
room_floor_living_room_0’, ’On top of: room_floor_kitchen_0’, ’On
floor: room_floor_living_room_0’, ’Next to: plywood_0’]}
16
17You will be provided with the environment state of each object in the
environment in the above format.
18
19Format of the action commands:
20

20Action commands is a dictionary with the following format:
21{
22\"action\": \"action_name\",
23\"object\": \"target_obj_name\",
24\"thoughts\": \"inner monologue describing why this action is
chosen\",
25}
26
27or
28
29{
30\"action\": \"action_name\",
31\"object\": \"target_obj_name1,target_obj_name2\",
32\"thoughts\": \"inner monologue describing why this action is
chosen\",
33}
34
35The action_name must be one of the following:
36LEFT_GRASP # the robot grasps the object with its left hand, to execute
the action, the robot’s left hand must be empty, e.g. {’action’:
’LEFT_GRASP’, ’object’: ’apple_0’}.
37RIGHT_GRASP # the robot grasps the object with its right hand, to
execute the action, the robot’s right hand must be empty, e.g.
{’action’: ’RIGHT_GRASP’, ’object’: ’apple_0’}.
38LEFT_PLACE_ONTOP # the robot places the object in its left hand on top
of the target object and release the object in its left hand, e.g.
{’action’: ’LEFT_PLACE_ONTOP’, ’object’: ’table_1’}.
39RIGHT_PLACE_ONTOP # the robot places the object in its right hand on top
of the target object and release the object in its left hand, e.g.
{’action’: ’RIGHT_PLACE_ONTOP’, ’object’: ’table_1’}.
40LEFT_PLACE_INSIDE # the robot places the object in its left hand inside
the target object and release the object in its left hand, to
execute the action, the robot’s left hand must hold an object, and
the target object can’t be closed e.g. {’action’:
’LEFT_PLACE_INSIDE’, ’object’: ’fridge_1’}.
41RIGHT_PLACE_INSIDE # the robot places the object in its right hand
inside the target object and release the object in its left hand, to
execute the action, the robot’s right hand must hold an object, and
the target object can’t be closed, e.g. {’action’:
’RIGHT_PLACE_INSIDE’, ’object’: ’fridge_1’}.
42RIGHT_RELEASE # the robot directly releases the object in its right
hand, to execute the action, the robot’s left hand must hold an
object, e.g. {’action’: ’RIGHT_RELEASE’, ’object’: ’apple_0’}.
43LEFT_RELEASE # the robot directly releases the object in its left hand,
to execute the action, the robot’s right hand must hold an object,
e.g. {’action’: ’LEFT_RELEASE’, ’object’: ’apple_0’}.
44OPEN # the robot opens the target object, to execute the action, the
target object should be openable and closed, also, toggle off the
target object first if want to open it, e.g. {’action’: ’OPEN’,
’object’: ’fridge_1’}.
45CLOSE # the robot closes the target object, to execute the action, the
target object should be openable and open, e.g. {’action’: ’CLOSE’,
’object’: ’fridge_1’}.
46COOK # the robot cooks the target object, to execute the action, the
target object should be put in a pan, e.g. {’action’: ’COOK’,
’object’: ’apple_0’}.
47CLEAN # the robot cleans the target object, to execute the action, the
robot should have a cleaning tool such as rag, the cleaning tool
should be soaked if possible, or the target object should be put
into a toggled on cleaner like a sink or a dishwasher, e.g.
{’action’: ’CLEAN’, ’object’: ’window_0’}.
48FREEZE # the robot freezes the target object e.g. {’action’: ’FREEZE’,
’object’: ’apple_0’}.
49UNFREEZE # the robot unfreezes the target object, e.g. {’action’:
’UNFREEZE’, ’object’: ’apple_0’}.
21

50SLICE # the robot slices the target object, to execute the action, the
robot should have a knife in hand, e.g. {’action’: ’SLICE’,
’object’: ’apple_0’}.
51SOAK # the robot soaks the target object, to execute the action, the
target object must be put in a toggled on sink, e.g. {’action’:
’SOAK’, ’object’: ’rag_0’}.
52DRY # the robot dries the target object, e.g. {’action’: ’DRY’,
’object’: ’rag_0’}.
53TOGGLE_ON # the robot toggles on the target object, to execute the
action, the target object must be closed if the target object is
openable and open e.g. {’action’: ’TOGGLE_ON’, ’object’: ’light_0’}.
54TOGGLE_OFF # the robot toggles off the target object, e.g. {’action’:
’TOGGLE_OFF’, ’object’: ’light_0’}.
55LEFT_PLACE_NEXTTO # the robot places the object in its left hand next to
the target object and release the object in its left hand, e.g.
{’action’: ’LEFT_PLACE_NEXTTO’, ’object’: ’table_1’}.
56RIGHT_PLACE_NEXTTO # the robot places the object in its right hand next
to the target object and release the object in its right hand, e.g.
{’action’: ’RIGHT_PLACE_NEXTTO’, ’object’: ’table_1’}.
57LEFT_TRANSFER_CONTENTS_INSIDE # the robot transfers the contents in the
object in its left hand inside the target object, e.g. {’action’:
’LEFT_TRANSFER_CONTENTS_INSIDE’, ’object’: ’bow_1’}.
58RIGHT_TRANSFER_CONTENTS_INSIDE # the robot transfers the contents in the
object in its right hand inside the target object, e.g. {’action’:
’RIGHT_TRANSFER_CONTENTS_INSIDE’, ’object’: ’bow_1’}.
59LEFT_TRANSFER_CONTENTS_ONTOP # the robot transfers the contents in the
object in its left hand on top of the target object, e.g. {’action’:
’LEFT_TRANSFER_CONTENTS_ONTOP’, ’object’: ’table_1’}.
60RIGHT_TRANSFER_CONTENTS_ONTOP # the robot transfers the contents in the
object in its right hand on top of the target object, e.g.
{’action’: ’RIGHT_TRANSFER_CONTENTS_ONTOP’, ’object’: ’table_1’}.
61LEFT_PLACE_NEXTTO_ONTOP # the robot places the object in its left hand
next to target object 1 and on top of the target object 2 and
release the object in its left hand, e.g. {’action’:
’LEFT_PLACE_NEXTTO_ONTOP’, ’object’: ’window_0, table_1’}.
62RIGHT_PLACE_NEXTTO_ONTOP # the robot places the object in its right hand
next to object 1 and on top of the target object 2 and release the
object in its right hand, e.g. {’action’:
’RIGHT_PLACE_NEXTTO_ONTOP’, ’object’: ’window_0, table_1’}.
63LEFT_PLACE_UNDER # the robot places the object in its left hand under
the target object and release the object in its left hand, e.g.
{’action’: ’LEFT_PLACE_UNDER’, ’object’: ’table_1’}.
64RIGHT_PLACE_UNDER # the robot places the object in its right hand under
the target object and release the object in its right hand, e.g.
{’action’: ’RIGHT_PLACE_UNDER’, ’object’: ’table_1’}.
65DONE # the robot has achieved the target environment as per your best
judgement, e.g. {’action’: ’DONE’, ’object’: ’none’}.
66
67Format of the interactable objects:
68Interactable object will contain multiple lines, each line is a
dictionary with the following format:
69{
70\"name\": \"object_name\",
71\"category\": \"object_category\"
72}
73object_name is the name of the object, which you must use in the action
command, object_category is the category of the object, which
provides a hint for you in interpreting initial and goal condtions.
74
75
76thoughts: This is your inner monologue describing why you choose this
action, it will be used as a feedback to improve your next action
command.
77
78Please pay special attention:
22

791. The robot can only hold one object in each hand.
802. Action name must be one of the above action names, and the object
name must be one of the object names listed in the interactable
objects.
813. All PLACE actions will release the object in the robot’s hand, you
don’t need to explicitly RELEASE the object after the PLACE action.
824. For LEFT_PLACE_NEXTTO_ONTOP and RIGHT_PLACE_NEXTTO_ONTOP, the action
command are in the format of {’action’: ’action_name’, ’object’:
’obj_name1, obj_name2’}
835. If you want to perform an action to an target object, you must make
sure the target object is not inside a closed object.
846. For actions like OPEN, CLOSE, SLICE, COOK, CLEAN, SOAK, DRY, FREEZE,
UNFREEZE, TOGGLE_ON, TOGGLE_OFF, at least one of the robot’s hands
must be empty, and the target object must have the corresponding
property like they’re openable, toggleable, etc.
857. For PLACE actions and RELEASE actions, the robot must hold an object
in the corresponding hand.
868. Before slicing an object, the robot can only interact with the object
(e.g. peach_0), after slicing the object, the robot can only
interact with the sliced object (e.g. peach_0_part_0).
879. You can only clean a stain with a soaked cleaning tool like rag, or
put the stained object into a toggled on cleaner like sink or
dishwasher.
8810. To soak an object, first place the object into a toggled on sink,
then soak it. Do not soak an object outside a sink.
8911. Jars, Bags, and other objects must be OPENED, before you put things
inside them.
90
91
92Please output a SINGLE action command(in the given format) that the
robot may execute next in order to make progress towards achieving
the target environment state.
Now, the prompt given at each timestep
1Your Task:
2Input:
3
4Currently, the robot is holding:
5{robot_state}
6
7Current environment state:
8{object_state}
9
10This may be summarized as the following atomic propositions being true:
11{’, ’.join(APs) if APs else ’No atomic propositions are true.’}
12
13Goal State description:
14{task_description}
15
16Feedback on failed actions from the environment:
17{feedback if feedback else "No feedback yet."}
18
19
20Feedback from the critic:
21{failed_actions}
22
23The feedback includes instructions from your critic (via an LTL law with
an explanation), which will block certain actions that they think
will lead to failure. It also includes any failed actions you have
tried to execute in the past.
24If you fail an action, please use the feedback to guide your next action
choice.
25DO NOT REPEAT AN ACTION IF THE CRITIC HAS BLOCKED IT OR IF IT HAS FAILED
BEFORE.
23

26
27Inner Monologue:
28{inner_monologue}
29
30Previous Successful action:
31{old_action}
32
33
34
35Please output the A SINGLE ACTION COMMAND (in the given format), the
current environment state will make progress towards the target
environment state.
36Only output the action command with nothing else.
37
38Output:
Critic prompts:First, context prompt for trajectories:
1You are an expert symbolic critic analyzing a robot’s task execution
trajectory. ’
2Your goal is to propose Linear Temporal Logic (LTL) laws that will
improve the robot’s
3efficiency, prevent common mistakes, and ensure task completion.
4
5## ROBOT’S GOAL
6{rule_data}
7
8This goal is written in terms of a list of formulas involving APs. All
of these formulas need to be true in order to finish the task.
9
10## ATOMIC PROPOSITIONS
11
12### Observation Variables (Environment State):
13{chr(10).join([f" - {ap}" for ap in APs[’obs_APs’]])}
14 **Key Observation Categories: **
15- Object locations: ‘object_X_in_location‘, ‘object_X_on_Y‘,
‘object_X_inside_Y‘
16- Hand states: ‘object_X_in_hand‘ (what robot is holding)
17- Object properties: ‘object_X_is_open‘, ‘object_X_is_clean‘, etc.
18- Spatial relations: ‘object_X_next_to_Y‘, ‘object_X_under_Y‘
19
20
21### Action Variables (Robot Actions):
22{chr(10).join([f" - {ap}" for ap in APs[’action_APs_true’]])}
23
24 **Action Categories: **
251. **Direct object actions **: ‘action_object‘ (grasp, open, close,
clean, freeze, unfreeze, slice, soak, dry, toggle_on, toggle_off)
262. **Placement actions **: ‘object1_place_relation_object2‘ (place_ontop,
place_inside, place_nextto, place_under, release)
273. **Transfer actions **: ‘object1_transfer_contents_relation_object2‘
284. **Complex placement **: ‘object1_place_nextto_ontop_object2_object3‘
295. **Task completion **: ‘done‘
30
31## LTL SYNTAX RULES
32- **Operators**: ‘&‘ (and), ‘|‘ (or), ‘!‘ (not), ‘G‘ (globally), ‘X‘
(next), ‘->‘ (implies)
33- **Format**: ‘G(observation_condition -> X(action_condition))‘
34- **Focus**: Prefer blocking bad actions rather than forcing specific
actions
35- **Trace structure **: (obs, action, obs, action, ...)
36
37## YOUR TASK
38Analyze the robot’s trajectory and propose LTL laws that:
24

391. **Prevent inefficiencies **: Stop redundant or counterproductive
actions
402. **Ensure prerequisites **: Block actions when preconditions aren’t
met. ( for example, a fridge must be open to place something inside
it or take something out of it)
413. **Promote task completion **: Add rules to recognize when goals are
achieved
424. **Maintain feasibility **: Avoid over-constraining the action space
Next, the critic main prompt for trajectories:
1## TRAJECTORY ANALYSIS
2
3You have already designed a few rules, however they were not enough to
accomplish the task. You need to add an additional number of rules
to get there!
4
5
6### Robot Goal:
7{rule_data}
8
9### Execution Trace for the UNSUCCESSFUL RUN:
10{format_AP_log_for_critic(AP_log)}
11
12
13### Previous Rules:
14
15Previously, you have already designed some rules based on priot traces,
now, given a new trace, suggest a small number of ADDITIONAL RULES
16
17The previous rules are:
18{existing_rules}
19
20## ANALYSIS FRAMEWORK
21
22 **Step 1: Identify the most repeated action in the trajectory
23 **Step 2: Understand why this action was repeated, and why it is
necessary to repeat this action
24 **Step 3: Define LTL Laws which block this action when it is unnecessary
25
26## EXAMPLES OF GOOD LTL LAWS
27
28 **Prerequisite checking: **
29‘‘‘
30G(object_X_in_hand -> object_X_place_in_target_position)
31"Only place objects you’re actually holding"
32‘‘‘
33
34 **Efficiency enforcement: **
35‘‘‘
36G((task_complete_for_X) -> X(!grasp_object_X))
37"Don’t grasp objects that are already correctly placed"
38‘‘‘
39
40
41The goal consists of many parts as there are many objects in the
environment.
42You are refining an existing trajectory, focus on eliminating repeated,
useless actions.
43Do not constrain yourself to a small number of laws, make as many laws
as you need. These laws are boolean, so be very precise.
44Make different laws about different items. Dont try to merge all your
laws into one big law, write many SIMPLE laws
45
46
25

47## OUTPUT REQUIREMENTS
48
49Provide your analysis in exactly this format:
50
51 **Explanation:**
521. **Initial State **: Describe the starting configuration across all
relevant objects
532. **Goal Interpretation **: What the robot needs to accomplish for all
listed sub-goals (treat them as possibly dependent)
543. **Required Steps **: Logical sequence to achieve the full multi-object
goal
554. **Most repetitive action ** : What was the most repetitive action in
the trajctory provided?
565. **Law Strategy **: Propose a law to block this action when not
necessary
57
58 **Laws:**
59‘‘‘json
60[
61{{
62"rule": "G(observation_condition -> X(action_condition))",
63"explanation": "Clear explanation of why this law improves
performance"
64}},
65{{
66"rule": "G(another_condition -> X(another_action))",
67"explanation": "Another law addressing a different issue"
68}}
69]
70‘‘‘
71
72 **CRITICAL REMINDERS: **
73- Use ONLY the provided observation and action APs
74- Laws should be in format: ‘G(obs_condition -> X(action_condition))‘
75- Focus on blocking problematic actions, not forcing specific ones
76- Ensure laws don’t make the task impossible by over-constraining
Next, the critic context prompt for overconstrained states:
1You are an expert symbolic critic observing a robot’s behavior.
2
3The robot’s goal is:
4{AP_log[-1][’goal’]}
5
6You are given:
71. A list of all atomic observation and action variables
82. The observation variables true at the current timestep
93. A set of LTL rules that are overconstraining (they block all actions)
104. The actions currently allowed by those laws (conflicting actions)
11
12Your task:
13- Analyze why the constraining rules conflict.
14- Replace ONLY the constraining rules with new ones that resolve the
deadlock.
15- Keep all other rules unchanged.
16- New rules must enforce **sequentiality** by adding conditions like
‘!o2‘ to break ties.
17- New rules must strictly follow this format:
18‘G(expression1 -> X(expression2))‘
19
20Allowed operators:
21- & (and), | (or), ! (not), G (globally), X (next), -> (implies)
22
23Important:
24- Each output must be valid JSON.
26

25- Each rule must have the structure: {{"rule": "...", "explanation":
"..."}}
26- Output must be a JSON array of objects, with **double quotes only **.
27- Do not output anything except the JSON array.
28
29Example of correction:
30If both rules are ‘G(o1 -> X(a1))‘ and ‘G(o2 -> X(a2))‘ and both o1, o2
hold,
31replace one with ‘G(o1 & !o2 -> X(a1))‘ and keep the second as G(o2 ->
X(a2)).
32Make sure to return both.
33
34Think carefully about the goal and current state first.
35Then output the replacement rules as JSON only.
Next, the critic main prompt for overconstrained states:
1Observation variables:
2{",".join(APs[’obs_APs’])}
3
4Action variables:
5{",".join(APs[’action_APs’])}
6
7
8True observation variables at current timestep:
9{AP_list_curr}
10
11Overconstraining rules (to be replaced):
12{constraining_rules}
13
14Conflicting actions:
15{valid_actions}
16
17Now output the replacement rules in the following strict JSON format:
18
19[
20{{
21"rule": "G(... -> X(...))",
22"explanation": "..."
23}},
24{{
25"rule": "G(... -> X(...))",
26"explanation": "..."
27}}
28]
29
30Nothing else.
A.4.2 MINECRAFT
Actor promptsFirst, the context prompt:
1You are a helpful assistant that responds with a primitive (built in
mineflayer) which will lead to completing any Minecraft task
specified by me.
2
3At each round of conversation, I will give you
4Code from the last round: ...
5Execution error: ...
6Chat log: ...
7Biome: ...
8Time: ...
9Nearby blocks: ... ( A list of all uniqque blocks in a 16 block radius,
you may use mineBlock to collect any of these blocks)
27

10Nearby entities (nearest to farthest):
11Neighbourhood blocks: ... (A list of blocks in your immediate
neighbourhood i.e. a 2 block radius)
12Health: ...
13Hunger: ...
14Position: ...
15Equipment: ...
16Inventory (xx/36): ... (A list of all items in your inventory, with
their counts)
17Chests: ...
18Task: ...
19Context: ...
20Critique: ...
21Previous failed code: ...
22
23You should then respond to me with
24
25Thinking:
26Think out loud in natural language about what you observe, what you need
to accomplish, and what you should do next. This should be free-form
reasoning, not a structured list.
27
28Code:
291) You must respond with a single line of code that corresponds to one
of the following primitives:
30- Use ‘mineBlock(bot, name)‘ to collect blocks. Do not use ‘bot.dig‘
directly.
31- Use ‘craftItem(bot, name)‘ to craft items. Do not use ‘bot.craft‘
or ‘bot.recipesFor‘ directly.
32- Use ‘smeltItem(bot, itemName, fuelName)‘ to smelt itemName using
fuelName. Do not use ‘bot.openFurnace‘ directly. Each item will
consume one fuel.
33- Use ‘placeItem(bot, name, position)‘ to place blocks. Do not use
‘bot.placeBlock‘ directly.
34- Use exploreUntil(bot, direction, maxTime, callback) to explore,
where,
35- direction is a Vec3 with values -1, 0, or 1 (e.g., new Vec3(1,
0, 1) to explore diagonally).
36- maxTime is in seconds (default is 60).
37- callback is a function that returns a truthy value when the
exploration goal is met. If it returns something truthy, the
bot stops exploring early and exploreUntil returns that
value. Otherwise, exploration continues until the time runs
out. For example, callback can be () => {{
38return bot.findBlock({{ matching: block =>
block.name === "iron_ore", maxDistance: 32 }});
39}}
40- Use ‘equipItem(bot, name, destination)‘ to equip an item in the
bot’s hand or armor slots. The default for destination is
’hand’. For example, ‘equipItem(bot, "wooden_pickaxe")‘ equips a
wooden pickaxe in the bot’s hand.
412) Every primitive function must be awaited, as they are asynchronous.
423) Functions in the "last chosen primitive" section will not be saved
or executed. Do not reuse functions listed there. If there is no
error, it was executed successfully, if there is an error, it was
not executed successfully
434) ‘maxDistance‘ should always be 32 for ‘bot.findBlocks‘ and
‘bot.findBlock‘. Do not cheat.
445) Do not use ‘bot.on‘ or ‘bot.once‘ to register event listeners. You
definitely do not need them.
456) Make sure you use the correct names for blocks and items, as they
are case-sensitive. For example, use "stone" instead of "Stone",
"oak_log" instead of "Oak Log", etc.
46
47
28

48
49You should only respond in the format as described below:
50RESPONSE FORMAT:
51Thinking:
52[Free-form reasoning about what you observe, what you need to do, and
what action to take next]
53
54Code:
55‘‘‘javascript
56await yourChosenPrimitive(bot,corresponding arguments);
57‘‘‘
Now, the prompt given at each timestep
1Response from the last round: \n {state.responseLastRound} \n
2Execution error: {state.executionError if state.executionError else
"None"}
3Biome: {state.biome}
4Time: {state.time}
5Nearby blocks: {state.nearbyBlocks if state.nearbyBlocks else "None"}
6Nearby entities (nearest to farthest): {", ".join([f"{entity.name}
({entity.type})" for entity in state.nearbyEntities]) if
state.nearbyEntities else "None"}
7Neighbourhood blocks: {", ".join([f"{block.name} at ({block.position.x},
{block.position.y}, {block.position.z})" for block in
state.neighbourhood]) if state.neighbourhood else "None"}
8Health: {state.health}
9Hunger: {state.hunger}
10Position: ({state.position.x}, {state.position.y}, {state.position.z})
11Equipment: Hand: {state.equipment.hand}, Armor: [Head:
{state.equipment.armor.head}, Chest: {state.equipment.armor.chest},
Legs: {state.equipment.armor.legs}, Feet:
{state.equipment.armor.feet}]
12Inventory (count: {state.inventoryCount}): {", ".join([f"{item.name}
({item.count})" for item in state.inventory]) if state.inventory
else "None"}
13Chests: {", ".join(state.chests) if state.chests else "None"}
14Task: {state.task}
15Context: {state.context}
16Critique: {state.critic}
17Previous failed code: You previously attempted the following codes, and
they didnt work because they violated the critics recommendation
{failed_codes if failed_codes else "None"}
Next, the critic context prompt for trajectories:
1You are an expert critic observing the trajectory of a Minecraft agent.
The goal of the agent is to mine a diamond.
2
3You are given:
41) A list of atomic observation and action variables
52) A list of failures that occurred in trajectories
63) Existing LTL rules implemented
7
8You will be given a series of steps taken by the agent, including
observations, actions, and success/failure of the action with an
error message.
9Your task is to analyze the trajectory and provide LTL laws that
constrain the agent’s actions in order to boost efficiency and
performance.
10The laws should be in the form of LTL formulas, and you should provide a
brief explanation of each law. The boolean variables used in the
laws are defined as follows:
11
29

12Observation Variables:
13{", ".join(OBS_VARIABLES_LIST)}
14
15The observations in the atomic proposition space are described as
follows:
16
17- ‘obs_has_x‘ corresponds to having the item ‘x‘ in the inventory of the
agent.
18- ‘obs_near_crafting_table‘ or ‘obs_near_furnace‘ define if the agent is
within an interacting distance of a crafting table or furnace.
19- ‘obs_has_x_equipped‘ corresponds to an object ‘x‘ (e.g., an iron
pickaxe) actively equipped.
20- Only one item can be equipped at any point in time.
21- You may propose additional observation variables if needed to express
useful rules.
22
23Action Variables:
24{", ".join(ACTION_VARIABLES_LIST)}
25
26The actions the agent can perform are limited to a few types:
27
28- ‘action_mine_x‘: mines the item ‘x‘. Certain blocks require certain
tools:
29- stone: wood pickaxe or better
30- iron: stone pickaxe or better
31- diamond: iron pickaxe or better
32- ‘action_craft_x‘: crafts an item ‘x‘, if prerequisites and (if needed)
a crafting table are present.
33- ‘action_smelt_iron‘: smelts raw iron into ingots using fuel and a
furnace.
34- ‘action_equip_x‘: equips a tool for mining. Only one tool can be
equipped at a time.
35- ‘action_explore‘: used to find resources not currently visible.
36- ‘action_place_x‘: places an item like a crafting table or furnace to
enable usage.
Next, the critic main prompt for trajectories:
1You are a symbolic critic observing the trajectory of a Minecraft agent.
The agent is inefficient, often repeats work, and occasionally
causes errors like trying to mine without the right tool or crafting
without the ingredients.
2
3GOAL OF AGENT: MINE A DIAMOND
4YOUR GOAL: PROPOSE LTL LAWS THAT PROMOTE THE AGENT’S PROGRESS TOWARD
THIS GOAL AND PREVENT INEFFICIENCIES.
5
6THINK OF THE BASIC TASK GRAPH REQUIRED TO MINE A DIAMOND, and PROPOSE
LTL LAWS TO GUIDE THE AGENT ALONG THAT GRAPH.
7
8Before forcing any action, think of checking if the subgoals to do that
action are met.
9
10
11### Your task:
121. Decompose the task of mining a diamond into symbolic subgoals:
acquiring wood, crafting tools, smelting, equipping tools, etc.
132. For each subgoal transition (e.g., "has stone => craft
stone_pickaxe"), propose an **LTL law ** that enables or encourages
this step.
143. Also identify any **errors** or **inefficiencies** in the trajectory.
For each one, propose an LTL law to prevent that mistake in the
future.
30

154. Focus on writing LTL laws in the form ‘G(condition => X(action))‘.
Use observation variables for ‘condition‘, and action variables for
‘action‘.
165. Avoid overly specific or redundant laws. Try to generalize from the
plan, not just from individual steps.
176. You may also propose **new boolean observation variables ** if needed
to express useful constraints (e.g., ‘obs_has_stone_pickaxe‘,
‘obs_seen_diamond_block‘).
187. Your final set of LTL laws should include:
19- >=3 rules that **encourage efficient, goal-aligned behavior **
20- >=1 rule that **discourages observed inefficient behavior **
21
22### Existing Inputs:
23- Existing LTL laws: {SOFT_LTL_RULES_SAYCAN}
24- Action and observation variables:
25- Actions: {", ".join(ACTION_VARIABLES_LIST)}
26- Observations: {", ".join(OBS_VARIABLES_LIST)}
27
28
29### Agent Trajectory:
30{format_trajectory_for_critic(trace)}
31
32
33### Output Format:
34Return the following in your response:
35
36---
37
38### Reasoning:
391. **Plan Decomposition **: Write out the full high-level plan to mine a
diamond as a sequence of symbolic subgoals (e.g., get wood-> make
planks-> craft tools-> smelt-> equip-> mine).
402. **Plan Conversion **: List the sequence of obs props and action
props that correspond to this plan
412. **Positive Constraints **: For at least four transitions in this plan,
propose a rule of the form ‘G(preconditions => X(useful_action))‘
that helps the agent complete the task efficiently.
423. **Negative Constraints **: Identify any mistakes in the trajectory
(e.g., crafting without ingredients, mining without tools), and
write ‘G(bad_condition => X(!bad_action))‘ rules to prevent them.
434. **Coverage**: Ensure your rules cover multiple stages of the plan
(not just early or late stages).
445. **Reusability**: The rules should generalize and not rely on specific
step numbers.
45
46
47---
48Laws:
49- ‘efficiency_laws‘: a list of LTL rules that **promote efficient
behaviors**, each with a brief explanation.
50- ‘inefficiency_laws‘: a list of LTL rules that **prevent mistakes **,
each with a brief explanation.
51- Mention which part of the plan each law corresponds to.
Next, the critic context prompt for overconstrained states:
1You are an expert critic observing the trajectory of a Minecraft agent.
The goal of the agent is to mine a diamond.
2
3Sometimes, the laws you impose are too constraining and prevent all
possible actions. Your job is to break these deadlocks
4
5You are given:
61) A list of atomic observation and action variables
7
31

8You will be given a particular timestep where the LTL laws led to no
feasible action, and your task is to resolve the conflict by either
modifying or deleting one of the LTL laws.
9
10The laws should be in the form of LTL formulas, and you should provide a
brief explanation of each law. The boolean variables used in the
laws are defined as follows:
11
12Observation Variables:
13{", ".join(OBS_VARIABLES_LIST)}
14
15The observations in the atomic proposition space are described as
follows:
16
17- ‘obs_has_x‘ corresponds to having the item ‘x‘ in the inventory of the
agent.
18- ‘obs_near_crafting_table‘ or ‘obs_near_furnace‘ define if the agent is
within an interacting distance of a crafting table or furnace.
19- ‘obs_has_x_equipped‘ corresponds to an object ‘x‘ (e.g., an iron
pickaxe) actively equipped.
20- Only one item can be equipped at any point in time.
21- You may propose additional observation variables if needed to express
useful rules.
22
23Action Variables:
24{", ".join(ACTION_VARIABLES_LIST)}
25
26The actions the agent can perform are limited to a few types:
27
28- ‘action_mine_x‘: mines the item ‘x‘. Certain blocks require certain
tools:
29- stone: wood pickaxe or better
30- iron: stone pickaxe or better
31- diamond: iron pickaxe or better
32- ‘action_craft_x‘: crafts an item ‘x‘, if prerequisites and (if needed)
a crafting table are present.
33- ‘action_smelt_iron‘: smelts raw iron into ingots using fuel and a
furnace.
34- ‘action_equip_x‘: equips a tool for mining. Only one tool can be
equipped at a time.
35- ‘action_explore‘: used to find resources not currently visible.
36- ‘action_place_x‘: places an item like a crafting table or furnace to
enable usage.
Next, the critic main prompt for overconstrained states:
1You are a symbolic critic observing the trajectory of a Minecraft agent.
The agent is inefficient, often repeats work, and occasionally
causes errors like trying to mine without the right tool or crafting
without the ingredients.
2
3GOAL OF AGENT: MINE A DIAMOND
4YOUR GOAL: You are given a timestep where the LTL laws led to no
feasible action, and your task is to resolve the conflict by either
modifying or deleting one of the LTL laws.
5
6Given the set of observations, no actions are allowed in the given
instance. Modify one or both of the laws to break this deadlock.
7
8### Your task:
91. First, reason about which rule is less useful given the constraints
102. Modify that law
113. Make sure there is atleast one feasible action in the given state
after the modification of laws.
12
32

13### Rules you should output:
14- Each rule should follow the form: ‘G(condition => X(action))‘
15- Use **observation variables ** (e.g., obs_has_x, obs_near_x,
obs_equipped_x) in the ‘condition‘.
16- Use **action variables ** (e.g., action_mine_x, action_craft_x) in the
‘action‘.
17- Conditions should reflect **states that actually occurred ** in the
trajectory, so the rule can generalize and not be overly specific or
invalid. The corresponding action should either approve or
disapprove of the corresponding action in the trajectory.
18- Make sure the rules do not block **all** possible actions. The agent
always needs at least one valid option.
19- Make sure to state which timesteps your rule is based on.
20- If necessary, propose **new observation variables ** that could help
express useful rules.
21
22
23
24### Format:
25- Output the LTL laws as a list of strings, each in proper syntax
26- Then provide a brief explanation of each rule and how it prevents
error or improves efficiency
27- Output as many laws as you deem necessary, forcing efficient actions
and disallowing inefficient ones
28
29### Example LTL Law:
30G(obs_has_raw_iron ˆ obs_near_furnace => X(action_smelt_iron))
31Explanation: Smelting iron early helps the agent craft a better pickaxe
sooner.
32
33### Inputs:
34
35- Existing LTL laws
36Rule 2: G(obs_has_2x_plank & !obs_has_2x_stick ->
X(action_craft_stick))
37Number of actions allowed: 1
38Filtered actions:
39[’action_craft_stick’]
40Observation Propositions (obs_props):
41obs_has_plank: True
42obs_has_2x_plank: True
43obs_has_3x_plank: True
44obs_has_wood_pickaxe: True
45obs_has_stone_pickaxe: True
46obs_has_fuel: True
47obs_near_crafting_table: True
48obs_iron_in_chunk: True
49obs_coal_in_chunk: True
50obs_wood_pickaxe_equipped: True
51==================================================
52Rule 7: G(obs_wood_pickaxe_equipped & !obs_has_3x_cobble ->
X(action_mine_stone))
53Number of actions allowed: 1
54Filtered actions:
55[’action_mine_stone’]
56Observation Propositions (obs_props):
57obs_has_plank: True
58obs_has_2x_plank: True
59obs_has_3x_plank: True
60obs_has_wood_pickaxe: True
61obs_has_stone_pickaxe: True
62obs_has_fuel: True
63obs_near_crafting_table: True
64obs_iron_in_chunk: True
65obs_coal_in_chunk: True
33

66obs_wood_pickaxe_equipped: True
67
68These rules are too constraining, modify them.
69
70
71- Feasible actions per step are available (so do not block everything)
72- Action and observation variables:
73- Actions: {", ".join(ACTION_VARIABLES_LIST)}
74- Observations: {", ".join(OBS_VARIABLES_LIST)}
75
76
77Answer with the following three things
78
791. Identify the action the agent should take given this state
802. Identify which rules are blocking that action from happening
813. Modify those rules.
82
83
84Modify one of the rules, or delete one of them, so that the agent can
take a feasible action at this timestep.
A.5 CODE AND TRAJECTORIES
The code, trajectories, and the LTL laws generated for Behavior will be made available upon request.
34