# Does Better Code Context Actually Help Coding Agents? I Built 248 Benchmarks to Find Out.

In January, I wrote about rethinking coding agent benchmarks — the evaluation gaps I saw, the enterprise-vs-open-source disconnect, and this question I couldn't stop thinking about: does giving agents better code context actually make them better at their jobs? I said I was going to go find out.

I went and found out. Kind of. The answer, like most honest answers in this space, is "it depends — but here's exactly what it depends on, and I have data."

Since that post, I built CodeContextBench (CCB): 248 software engineering tasks spanning the full software development lifecycle, designed to measure whether external code intelligence tools — specifically Sourcegraph's MCP tools — improve AI coding agent performance. I built the benchmark framework, the evaluation pipeline, the ground truth system, and the statistical analysis layer primarily using Claude Code, across 580+ conversation sessions over about 26 days. An AI coding agent building a benchmark to evaluate AI coding agents' use of code intelligence tools. It's as meta-recursive as it sounds, and I'll come back to that.

But first: the results.

## The Setup

Here's the core experimental design. The same agent (Claude Code with Haiku 4.5) runs the same task under two conditions:

**Baseline:** Full local source code. Standard tools (grep, file read, etc.). No MCP.

**MCP-augmented:** Source code is truncated — the files are there but emptied out. The agent gets 13 Sourcegraph MCP tools (semantic search, symbol resolution, dependency tracing, cross-repo navigation, etc.) and has to use them to find what it needs.

This is the part I think matters most: both configurations have access to the same information. The only difference is the access method. We're not giving the MCP agent extra information — we're testing whether a different pipe to the same information changes outcomes. (If anything, it's a conservative test: in real enterprise settings the agent typically wouldn't have full local access to every relevant repo, so the baseline is actually more favorable than reality.)

Tasks are organized by SDLC phase — Understand, Design, Build, Fix, Test, Document, Secure, Debug — plus a set of MCP-unique tasks that specifically require cross-repository discovery across 3-20 repos. The tasks span 40+ open-source repositories and 10 programming languages, from Kubernetes to Django to the Linux kernel. I wrote a [white paper](WHITE_PAPER_REPORT_V2.md) with the full methodology and an explanation of all the evaluation layers, including the information retrieval analysis pipeline.

## The Headline: Near-Zero Overall, But the Spread Is the Story

After running 230 valid task pairs across all SDLC suites plus 10 MCP-unique suites (170 SDLC + 60 MCP-unique), the overall numbers are essentially flat: baseline mean reward 0.631, MCP mean reward 0.633, delta **+0.002**. On average, MCP-augmented agents score about the same as baseline.

But that near-zero average obscures the real story, because the delta swings from **-0.183** to **+0.216** depending on the task type. That spread — from MCP hurting to MCP helping materially — is a much more interesting finding than any single number, because it tells you when code intelligence tools matter and when they don't.

## Where MCP Wins

The strongest SDLC gain is the Understand suite. MCP-unique tasks show a modest positive delta overall, with specific sub-suites showing larger gains.

| Suite | Tasks | Baseline Mean | MCP Mean | Delta |
|-------|-------|--------------|----------|-------|
| Understand | 20 | 0.660 | 0.851 | **+0.191** |
| MCP-Unique (all) | 60 | 0.652 | 0.702 | **+0.050** |
| Document | 20 | 0.847 | 0.895 | +0.048 |

**Understand tasks** show the strongest gain at +0.191 (0.660 to 0.851). This was the biggest reversal in the dataset — earlier drafts showed Understand as strongly negative, but that signal was coming from invalid/contaminated runs that were removed and rerun.

**MCP-unique tasks** require cross-repository discovery — tracing a vulnerability across an ecosystem of repos, or mapping how a config value propagates through 5 different services. These tasks span 3-20 repositories and specifically measure org-scale information retrieval. The overall +0.050 delta masks significant variation: security tasks show +0.216, cross-org tasks +0.184, org-scale tasks +0.192, while migration tasks are -0.065 and platform tasks -0.049. The sub-suite variation tells a richer story than the aggregate.

**Documentation tasks** show a modest positive at +0.048. The agent already does well on documentation with full local code (0.847), and MCP nudges it slightly higher.

## Where MCP Doesn't Help (or Hurts)

MCP hurts on **Debug** (-0.183) and **Build** (-0.121). **Design** (-0.036) and **Secure** (-0.010) are slightly negative, while **Fix** and **Test** are essentially flat.

| Suite | Tasks | Baseline Mean | MCP Mean | Delta |
|-------|-------|--------------|----------|-------|
| Debug | 20 | 0.670 | 0.487 | **-0.183** |
| Build | 25 | 0.494 | 0.372 | -0.121 |
| Design | 20 | 0.753 | 0.718 | -0.036 |
| Secure | 20 | 0.669 | 0.659 | -0.010 |
| Test | 20 | 0.480 | 0.480 | +0.000 |
| Fix | 25 | 0.479 | 0.491 | +0.012 |

The **Debug** result remains the clearest negative signal: MCP underperforms baseline by -0.183. Build is also materially negative (-0.121). These are local execution-and-modification workflows, and adding a remote retrieval layer does not reliably help the agent get to the actual code change faster or better.

Fix tasks have the lowest MCP tool ratio of any suite (35% of tool calls use MCP tools) and the highest local tool call count (39.8 per task). Bug-fixing is editing work. The agent needs to read a stack trace, find the offending code, change it, and run the tests. The relevant context is usually local. Adding a remote search layer to that workflow doesn't help — it just adds latency and another thing to do before getting to the actual fix.

This still isn't a failure of MCP tools. It's a signal about task-tool fit. Code intelligence tools are context retrieval tools, and context retrieval isn't the bottleneck on every task.

## The Retrieval Story

I built an information retrieval evaluation pipeline alongside the task scoring — it measures how agents find context, not just whether they get the right answer. The aggregate numbers across tasks with ground-truth file sets:

| Metric | Baseline | MCP | Delta | Direction |
|--------|----------|-----|-------|-----------|
| File Precision | 0.467 | 0.624 | +0.157 | better |
| File Recall | 0.549 | 0.649 | +0.100 | better |
| File F1 | 0.430 | 0.609 | +0.179 | better |
| MRR (Mean Reciprocal Rank) | 0.139 | 0.130 | -0.009 | ~flat |

MCP meaningfully improves both precision (+0.157) and recall (+0.100). File F1 — the harmonic mean combining both — jumps from 0.430 to 0.609. Translation: MCP agents find a higher fraction of the files that matter, and a higher fraction of the files they retrieve are actually relevant. The largest improvement is in the build suite (F1: 0.080 to 0.602), where baseline agents examine many irrelevant files while MCP agents use targeted search. MRR is essentially unchanged, meaning both configs find root-cause files at similar ranking positions when they find them.

The paradox: better retrieval doesn't always mean better outcomes. The suites with the best IR improvement (build: F1 from 0.080 to 0.602) don't necessarily show the best reward improvement (build delta: -0.089). This happens because finding the right files is necessary but not sufficient — the agent still has to correctly apply what it finds, and in build tasks, the local code modification step is where the truncated-source environment hurts.

When I dug into the task-level pairing data, a few distinct patterns emerged:

**Retrieval rescue.** On some tasks, the baseline agent found zero relevant context and scored zero. MCP found it and scored. These are cases where MCP didn't just help — it unlocked a capability the baseline agent flat-out didn't have.

**Execution wins despite similar retrieval.** This is the one that surprised me most. On several tasks, both configs accessed essentially the same files — flat retrieval deltas across the board — but MCP still produced better outcomes. Something about the MCP workflow — maybe the structured tool output, maybe the way search results prime the agent's reasoning, maybe just the different prompt context from using tools vs. reading files — is improving downstream execution even when the information retrieved is the same.

One finding from the refreshed IR pipeline: the Spearman correlation between retrieval quality and task outcome is now +0.395 (p=0.041, n=35) — a statistically significant positive association. Better retrieval does predict better outcomes, but the relationship is moderate, not deterministic. The MCP tool usage ratio vs. reward correlation is weaker at +0.293. Something beyond just "find the right files" is going on, and figuring out what it is might be the most interesting research question to come out of this whole project.

## The Cost Surprise

One finding I didn't expect: MCP runs are cheaper.

| Config | Mean Cost/Task | Total Cost |
|--------|---------------|------------|
| Baseline | $0.75 | $175.68 |
| MCP | $0.47 | $97.01 |

MCP-augmented runs cost less on average. The mechanism is straightforward: the truncated-source environment has less local code to read, so the agent processes fewer input tokens. MCP is also consistently faster across every suite, with time reductions ranging from about 29% (test) to 94% (design) in the current paired table.

This reframes the value question a bit. On the suites where MCP improves reward (especially MCP-unique and, in the cleaned paired set, Understand), you're getting better results at lower cost and lower latency. On the suites where reward is flat (fix, test), you're getting similar results faster. The clearly bad trade-offs remain debug and build, where the agent is faster but less effective.

## How I Built This (And What Broke)

I mentioned the meta-recursive thing. CodeContextBench was built almost entirely using Claude Code — the same AI coding agent I'm benchmarking. 580+ conversation sessions spanning January 30 to February 25, producing the task selection pipeline, 190+ Docker environment variants, a 3,500-line IR evaluation pipeline, a 7-function oracle scoring system, and more infrastructure scripts than I want to count.

The development process was its own lesson in what AI-assisted development is good at and where it falls apart.

**What worked well:** Generating Dockerfiles, writing evaluation scripts, building metrics pipelines, implementing statistical tests. This is well-structured, pattern-heavy work where you can describe what you want and validate the output deterministically. Claude Code was genuinely excellent at this.

**What broke, repeatedly:** The preamble. This is the instruction text prepended to each task telling the MCP agent about its tools. I went through five iterations:

V1 and V2 were too subtle — the agent had MCP tools available but never called them. Zero Sourcegraph tool calls across the board. V3 overcorrected with "MANDATORY" triple reinforcement, which got 90%+ adoption but caused what I started calling the "MCP death spiral": when a mirror was broken or a repo name was wrong, the agent would spend its entire context window retrying failed MCP queries, scoring 0.0 on tasks where the baseline scored 1.0. V4 swung back to "soft guidance" and adoption dropped to 40%. V5 finally landed it by leading with the constraint — "these files are not present locally, you must use MCP tools to access source code" — which forced adoption without mandating a specific workflow.

Then there was the git history bypass bug. I discovered that 5 of my first 9 test tasks were gaming the truncation: the agent figured out it could `git show HEAD:filename` to recover the full source from git history, completely defeating the experimental setup. The fix (recommitting the truncated state as a new commit so `git show HEAD:` returns empty files) was straightforward, but finding it required actually reading agent transcripts — a reminder that systematic QA on AI-generated infrastructure is non-negotiable.

The February 6th QA audit found 28 issues (9 critical) in the benchmark infrastructure — broken verifiers, instruction contamination (30 out of 156 task instructions had Sourcegraph references leaking into the baseline config), and silent scoring failures. All of this in infrastructure that was largely AI-generated and passed initial review. Iterative QA saved the entire project.

## What I Don't Know Yet

I want to be clear about the limitations. These are results from a single agent (Claude Code), a single MCP provider (Sourcegraph), running Claude Haiku 4.5. The sample sizes are meaningful (230 valid pairs) but not large enough for high-confidence conclusions on every individual suite. Multi-trial evaluation with bootstrap confidence intervals is planned but not yet complete.

The moderate correlation between retrieval quality and task outcomes (Spearman r=0.395, p=0.041) confirms that finding the right files helps — but it's not the whole story. What else matters? Is it the structure of the tool output? The way search-first workflows shape the agent's reasoning? Some interaction between retrieval strategy and the agent's existing capabilities? I don't know, and I think the answer matters a lot — both for how we build code intelligence tools and for how we design agent workflows.

## What's Next

The benchmark framework supports six agent harnesses (Claude Code, Codex, Cursor, Gemini, Copilot, OpenHands). Running the full suite across multiple agents will separate MCP tool effectiveness from agent-specific strengths — does the "design and cross-repo discovery" win pattern generalize, or is it specific to how Claude Code uses tools?

I'm also planning Deep Search forcing experiments (the semantic analysis layer was almost never invoked organically — agents default to keyword search), SCIP-indexed codebase comparisons (compiler-accurate code navigation vs. text search), and evaluations of alternative MCP providers like the GitHub MCP server. The benchmark is designed to be provider-agnostic; the MCP protocol is standardized, so swapping providers is a config change, not a redesign.

If you're building or evaluating code intelligence tools and want to run your stack against CCB, the repo is public. I'd genuinely love to see comparative results.

## The Signal

I started this project because I was drowning in noise. Every tool claims to "supercharge" agent performance. Every benchmark result is a press release. I wanted to know what was actually true, with data granular enough to understand why.

Here's what the data says so far: code intelligence tools provide measurable value on tasks that require **comprehension across large codebases** and **cross-repository discovery**. Understand tasks show +0.191, MCP-unique security and cross-org tasks show +0.216 and +0.184 respectively. When the bottleneck is finding and understanding scattered context, MCP tools help.

They provide mixed value on other SDLC tasks. MCP helps on understand (+0.191) and document (+0.048), is effectively flat on fix (+0.012) and test (+0.000), and hurts on debugging (-0.183) and build (-0.121). When the agent already has full source code and the bottleneck is local execution/editing rather than retrieval, adding a remote search layer can still be overhead. The overall delta across all 230 pairs is +0.002 — essentially zero — because the gains and losses roughly cancel out.

And there's a third category — tasks where the retrieval metrics are basically the same but outcomes still differ — that I can't fully explain yet and might be the most important one to understand.

That's a more specific, more useful, and more honest answer than "MCP improves agent performance by X%." And there's a lot more signal to find.
