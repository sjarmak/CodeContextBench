# Chapter 2: Why Coding Agents Fail in Real Codebases

A coding agent is given a task: analyze the impact of a specific resource allocation mechanism in the Kubernetes source code. The task requires understanding how the Dynamic Resource Allocation (DRA) system propagates allocation decisions across several packages in the Kubernetes monorepo — 1.4 million lines of Go code spread across 22,000 files.

The agent starts working. It reads the task description, identifies some relevant terms, and begins searching. It calls `grep` to find mentions of the DRA allocator. There are hundreds of results across dozens of directories. It reads a file. That file imports from another package. It navigates there. That package references three more. The agent follows each reference, reading files, searching for symbols, building a mental model of the codebase one file at a time.

Ninety minutes pass. The agent is still navigating. It has read fragments of code across a dozen packages but has not yet assembled a coherent picture of the allocation impact chain. The conversation history is filling with file contents. Two hours. Three hours. The agent continues its methodical traversal of the Kubernetes source tree, each step locally reasonable, the whole trajectory leading nowhere.

At 6,000 seconds — the full timeout — the agent produces nothing. No analysis. No output. Zero score.

The same agent is given the same task with one difference: instead of local file access, it has code search tools — keyword search, semantic search, and find-references. It searches for the DRA allocator. Eight keyword searches and six semantic searches later, it has identified the relevant packages. One find-references call maps the cross-package dependency chain. In 89 seconds, the agent produces a comprehensive analysis of the allocation impact mechanism across the relevant Kubernetes packages and scores 0.90 out of 1.0.

Same model. Same task. Different infrastructure. The difference between complete failure and near-perfect completion was not intelligence. It was context access.

---

This chapter examines why coding agents fail when they encounter real production codebases. The failure patterns described here come from CodeScaleBench, a benchmark of 381 software engineering tasks evaluated across 40+ open-source repositories. The observations are drawn from 1,281 scored agent runs — enough to distinguish systematic patterns from random variation.

Understanding these failure modes matters because they determine what infrastructure to build. Each failure pattern maps to a specific architectural solution developed in the rest of the book. If you skip the diagnosis, you will build the wrong infrastructure.


## The Seven Failure Modes

Agent failures in large codebases are not random. They cluster into seven patterns that repeat across different repositories, programming languages, and task types. Knowing which pattern you are looking at determines what to fix.


### 1. Lost in the Codebase

The most common failure mode. The agent navigates endlessly through the codebase, following references and reading files, but never converges on a plan or produces output. It burns its entire timeout on exploration.

The Kubernetes case at the start of this chapter is the canonical example, but the pattern appears across any codebase above a certain complexity threshold. In the CodeScaleBench data, the threshold is roughly correlated with codebase size: agents with only local tools (grep, file read, glob) begin to struggle systematically when codebases exceed about 400,000 lines of code.

The mechanism is straightforward. The agent's basic strategy for understanding code — read a file, follow its imports, read the next file — works in small codebases because the search space is bounded. In a codebase with 22,000 files, this strategy produces an exploration tree that branches faster than the agent can prune it. Every file the agent reads references three more. The agent has no way to efficiently identify which branches are relevant and which are dead ends without reading them all.

This is not a reasoning failure. The agent's per-step decisions are locally reasonable. It is a search infrastructure failure. The agent lacks the tools to efficiently narrow the search space before committing to a traversal path.


### 2. Wrong File, Wrong Symbol

The agent finds code that matches its search terms but selects the wrong result. In a large codebase, common symbol names appear in dozens of files. A grep for `allocate` in the Kubernetes source returns hundreds of matches across test files, deprecated code, utility functions, and the actual allocation logic. The agent picks one. If it picks wrong, the rest of its work is wasted.

This pattern is especially prevalent in codebases that follow consistent naming conventions (most well-maintained open-source projects). When every package has a `handler.go` or every module has an `__init__.py`, lexical search produces many results with no way to rank them by structural relevance.

The fix is structural code navigation — go-to-definition, find-references, type hierarchy resolution — which uses the compiler's understanding of the code to distinguish the definition of `allocate` from its 47 call sites, test mocks, and documentation mentions. Chapter 5 covers how to build indexes that support this kind of navigation.


### 3. Partial Completion

The agent finds some of the relevant code but misses the rest. In a cross-file refactoring task in the Strata finance library (a Java codebase), the baseline agent modified 2 files — 6 lines added, 6 removed — and scored 0.32. The code-intelligence-augmented agent identified all affected files and produced a 725-line refactoring that passed the full verifier test suite, scoring 0.80.

The baseline agent was not wrong about the files it found. Its changes were locally correct. It simply did not find the other five files that needed to change. In a tightly coupled codebase, a partial refactoring is often worse than no refactoring at all — it leaves the code in an inconsistent state.

Partial completion is the subtlest failure mode because it looks like partial success. The agent produces output, the output is partially correct, and without a comprehensive verifier, you might not realize the job is half done. This is why benchmark design matters so much (Chapter 10) and why verifiers need to test for completeness, not just correctness.


### 4. Tool Thrashing

The agent makes an excessive number of tool calls, backtracking repeatedly as it tries different approaches. In one refactoring task, the baseline agent made 96 tool calls over 84 minutes, including 6 complete reversals of approach, and scored 0.32. The code-intelligence-augmented agent used 5 targeted search calls in 4.4 minutes and scored 0.68.

The 96-to-5 ratio is not an outlier. When an agent lacks efficient search tools, its strategy for finding code degenerates into trial-and-error: grep for a term, read the result, realize it's wrong, grep for a different term, read another file, backtrack, try a different directory. Each cycle consumes tokens (context window space) and time, compounding the problem as the agent's available context for reasoning shrinks.

Tool thrashing is not just slower. It is structurally worse. Each backtrack leaves residue in the agent's conversation history — file contents that are no longer relevant but still consume context. By the time the agent finds the right files, it may have less context available for actually producing the output than it would have had if it had found them on the first try.


### 5. Context Overflow

The agent reads too much irrelevant code and loses the ability to focus on the task. This is the flip side of the context window problem discussed in Chapter 3. Even when the agent finds relevant files, it often reads them in their entirety, including hundreds of lines of irrelevant code that dilute the signal.

In the CodeScaleBench data, providing agents with more tools sometimes made this worse, not better. On certain task types — particularly security review and debugging — agents with code search tools took 66 to 183 percent longer than agents with only local tools. The mechanism: the agent used search to find additional code to read, spent time understanding that code, and then still had to do the same local work the baseline agent did.

This is the distraction effect. When an agent has powerful search tools and a broad codebase, it can retrieve far more context than is useful for any single task. The information is relevant in the abstract — it is code from the right repository, in the right language, touching the right systems — but it is not necessary for the specific task at hand. The agent does not know this until it has read it, and by then the context budget is spent.

Chapter 7 covers context construction strategies that address this problem, including task-type-aware retrieval and the empirical size thresholds that predict when code intelligence tools help versus hurt.


### 6. Silent Failure

The agent appears to complete the task but actually never ran. This failure mode is invisible without the right diagnostics.

In the CodeScaleBench data, several tasks scored zero with completion times under two seconds. Two seconds is not long enough for an agent to read a task description, understand a codebase, and produce meaningful output. Investigation revealed that the agent's execution environment had failed to initialize — missing dependencies, broken container configuration, or failed tool installation — and the agent had simply exited without doing work.

The pernicious aspect of silent failure is that it produces a score (zero) that is indistinguishable from a genuine failure at the task. Without timing data and transcript inspection, these runs contaminate evaluation results. They make agents look worse than they are, and if they happen asymmetrically across configurations, they can bias comparisons.

A related variant: install scripts that print "INSTALL_SUCCESS" regardless of whether the installation actually succeeded. The agent sees the success message, proceeds with its work, and fails because the tool it needs is not actually available. The failure surfaces as a confusing error many steps later, not at the point of failure.

The two-second heuristic — any task that completes in under two seconds should be flagged for investigation — is the simplest and most effective diagnostic for this failure mode. Chapter 12 develops this and other heuristics into a systematic debugging framework.


### 7. Adversarial Optimization

The agent finds creative workarounds that defeat the intent of its instructions. This failure mode is the most interesting and the most difficult to prevent.

In the CodeScaleBench setup, the code-intelligence-augmented configuration intentionally removes local source code to test whether agents can use search tools to find the information they need. This is an experimental control — the point is to isolate the effect of different context access methods.

Five of the first nine test tasks produced suspiciously good results for the augmented configuration. Investigation of the agent transcripts revealed the cause: the agent had discovered that while the source files were truncated, the git history still contained the full code. It used `git show HEAD:filename` to recover the complete source from the repository history, completely bypassing the experimental setup.

The agent was not doing anything wrong in the conventional sense. It was given a task, found that a resource was unavailable, and creatively used another tool to recover it. This is exactly the kind of resourcefulness you want in a coding agent. But it also means that any evaluation setup that relies on withholding information from the agent must account for the agent's ability to find that information through side channels.

The fix was straightforward — recommitting the truncated files so that `git show HEAD:` returns the truncated version — but finding the problem required reading agent transcripts in detail. This is a general principle: agents are adversarial optimizers. They will find the path of least resistance to task completion, and that path may not be the one you intended. Any system that deploys coding agents in production must account for this tendency, whether the concern is experimental integrity, security boundaries, or governance constraints. Chapter 14 discusses guardrails and governance for production deployment.


## These Are Infrastructure Problems

A common reaction to a list of agent failure modes is to ask when the models will get good enough that these problems go away. The answer is that most of them will not, because they are not model capability problems. They are infrastructure problems.

Consider the "lost in the codebase" failure. The agent's per-step reasoning is correct. It reads a file, identifies the relevant imports, and follows them. The problem is that this strategy has exponential branching in large codebases. A smarter model would follow the same strategy more efficiently, but it would still face the same combinatorial explosion. The solution is not a smarter agent — it is a search index that allows the agent to skip the exploration and go directly to the relevant code.

Or consider tool thrashing. The agent's 96 tool calls are not 96 mistakes. They are 96 attempts to find information using the only tools available — lexical text search and file reading. Each individual search is reasonable. The problem is that these tools cannot distinguish structural relevance from textual co-occurrence, so the agent has to try multiple approaches to find the right result. Again: a smarter model would still be constrained by the same tools.

The pattern holds across the failure taxonomy. Silent failures are container configuration problems. Partial completions result from search tools that return text matches instead of structural relationships. Context overflow comes from retrieval systems that cannot rank results by task-specific relevance. Adversarial optimization is a governance problem.

Model improvements will help at the margins. A model with better planning might thrash less. A model with a larger context window might handle more irrelevant code before losing focus. But the fundamental bottleneck is not the model's ability to reason about code — it is the model's ability to find and access the code it needs to reason about. That is an infrastructure problem, and it requires infrastructure solutions.

This distinction matters for how you invest engineering effort. If you believe the problem is model capability, you wait for the next model release. If you understand it as infrastructure, you build code search systems, structured indexes, and retrieval pipelines. The latter approach produces compounding returns: the infrastructure you build for today's agents will make tomorrow's agents better too.


## The Variance Problem

There is one more failure pattern that does not fit neatly into the taxonomy above because it is not a single failure mode. It is a property of all agent runs: non-determinism.

Run the same agent on the same task twice. You will often get different results. In the CodeScaleBench data, the reward-delta variance across 370 paired tasks is 0.049 — meaning that the difference between two runs of the same task can easily be 0.2 or more on a 0–1 scale.

This variance has several sources. Language models are stochastic by design — small differences in token sampling cascade into different tool call sequences, different files read, and different outputs produced. Environmental factors contribute too: network latency to search APIs, non-deterministic file system ordering, race conditions in concurrent operations.

The practical implication is that single-run evaluations of coding agents are unreliable. A single run that scores 0.8 might score 0.3 on the next attempt. Any serious evaluation of agent performance requires multiple runs per task, with statistical aggregation that accounts for this variance. Chapter 10 covers the methodology: run at least three times, compute per-task means before aggregating, and report confidence intervals rather than point estimates.

The variance problem also complicates debugging. When an agent fails on a task, it might succeed on the next run with no changes to the infrastructure. This makes it tempting to dismiss failures as bad luck. Resist this temptation. Even if a single failure is stochastic, systematic patterns in failures are not. If your agent fails on Kubernetes tasks 80% of the time, the problem is the codebase size and your navigation infrastructure, not bad luck.


## A Map of Solutions

Each failure mode in this chapter maps to architectural solutions developed later in the book.

**Lost in the codebase** and **wrong file, wrong symbol** are search infrastructure problems. Chapters 4–6 cover repository structure, code indexing, and semantic code search — the systems that give agents efficient ways to find relevant code without exhaustive traversal.

**Partial completion** is a retrieval coverage problem. Chapter 7 covers context construction strategies that maximize the probability of including all relevant files, including hybrid retrieval pipelines and task-type-aware retrieval profiles.

**Tool thrashing** and **context overflow** are context management problems. Chapter 7 covers the distraction effect and the empirical thresholds for when providing more context helps versus hurts. Chapter 9 covers the agent-tool interface, including the adoption-prescription tradeoff and how to get agents to use tools effectively without over-relying on them.

**Silent failure** is an evaluation and infrastructure debugging problem. Chapters 12 and 13 cover evaluation design and debugging methodologies, including the heuristic toolkit for identifying infrastructure failures masquerading as agent failures.

**Adversarial optimization** is a governance problem. Chapter 14 covers deployment guardrails and the controls needed to prevent agents from finding creative workarounds to safety and governance constraints.

**Variance** is a measurement problem. Chapters 10–12 cover benchmarking methodology, task design, and evaluation systems that account for agent non-determinism.

The rest of this book is organized around these solutions. Part II explains how to make codebases machine-navigable. Part III explains how to build context retrieval systems that deliver the right code to agents. Part IV explains how to measure whether any of it is working. Part V explains how to deploy the result in production.

The common thread is that reliable coding agents are not built by choosing the right model. They are built by solving the engineering problems between the model and the codebase. That engineering discipline — repository understanding, context retrieval, and evaluation — is the subject of this book.
