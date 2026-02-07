# Rethinking Coding Agent Benchmarks Part II: Building CodeContextBench

**TL;DR:** I built CodeContextBench — a 156-task evaluation framework spanning bug fixes in PyTorch, documentation generation from stripped Kubernetes source, code review of real PRs with injected defects, feature implementation in 1GB+ repos, kernel fault localization, and cross-file reasoning across a multi-repo corpus — to test whether giving AI coding agents access to Sourcegraph's code search tools actually makes them better at their jobs. This post is about the journey of building it: the research, the engineering, and the surprisingly hard problem of measuring something that seems straightforward. Spoiler: building the benchmark taught me as much as the results will.

---

## Wait, what's a "better" benchmark?

In [Part I](https://medium.com/@steph.jarmak/rethinking-coding-agent-benchmarks-5cde3c696e4a), I wrote about rethinking how we evaluate coding agents (because, really, we need to do better here). I talked about building a code intelligence digest as a way to gather relevant research and synthesize what the field actually knows about agent evaluation. That digest turned into a rabbit hole: I ended up curating a [library of 150+ papers](https://scixplorer.org/user/libraries/CCNrzL0GRxmkho6Hg2368Q) on code generation, agent evaluation, retrieval-augmented coding, and benchmark design. I built a separate embeddings and chunking pipeline on top of [ADS/SciX's API](https://ui.adsabs.harvard.edu/) for annotation, highlighting, and exploration views across the library, and generated podcasts and synthesis reports from different slices of the material to help me internalize it.

All of that research pointed to the same gap: we've seen that agents are remarkably capable when they have the right context, and getting that context tends to be fairly straightforward in small, greenfield projects. But in enterprise codebases — the kind with millions of lines, tangled dependencies, and conventions that only make sense if you've been there for three years — finding the right context is the bottleneck. Existing benchmarks either tested isolated coding tasks, evaluated on synthetic code, or didn't account for the tooling dimension at all.

At Sourcegraph we build code search and intelligence tools. So naturally we hypothesize that if you give agents better tools for finding and understanding code, they should produce better results. But "obviously" is a hypothesis (albeit a decent one grounded in qualitative, anecdotal feedback from happy customers and users), and "better results" means different things depending on the task. I'm a scientist and I want data to back up that "obviously."

So I built CodeContextBench.

## From qualitative signal to quantitative framework

I wasn't starting completely from scratch on the qualitative side. My colleague Trevor, a solutions engineer, had been doing hands-on testing with large-scale codebases — VS Code, Kubernetes, Servo, and NVIDIA/TensorRT-LLM — comparing Claude Code's performance with and without the Sourcegraph MCP across various feature requests and bug fixes.

His findings were compelling: all tests with the Sourcegraph MCP added significant value in larger repos. Without the MCP, Claude Code was "too eager," leading to "shakier implementations that do not account for the full architecture and patterns of the codebase." It missed certain areas. It hallucinated much more often.

Trevor developed a simple but effective prompt strategy that I'd later formalize:

> *"This repository is very big, so it isn't efficient to search with usual tooling. NEVER blindly run grep or rg commands without specifying a narrow set of directories to search. When working on this repository, you MUST use the Sourcegraph MCP search tools if you want to know about something."*

This was the qualitative foundation. Now I needed to turn it into something measurable. I took Trevor's VS Code and Kubernetes codebase prompts and formalized them into structured tasks for systematic evaluation — same tasks, controlled conditions, reproducible results.

## Designing the experiment

The core experimental design is deceptively simple:

| Configuration | What the agent gets |
|---|---|
| **Baseline** | Claude Code's native tools only: file reading, grep, shell |
| **MCP-Base** | + Sourcegraph keyword search, natural language search, file navigation (6 tools) |
| **MCP-Full** | + Deep Search — semantic, multi-hop code understanding (8 tools total) |

Same agent. Same model (Claude). Same tasks. Same containerized environment. The only variable is the level of code intelligence tooling available through [MCP](https://modelcontextprotocol.io/) (Model Context Protocol). Baseline is our control. I have plans for open harnesses like OpenHands and other model testing with this setup, but those are future work.

The tasks span real development work organized by SDLC phase — not just bug fixes, but documentation generation, code review, feature implementation, refactoring, fault localization, and dependency reasoning. 156 tasks across 13 benchmark suites and 10 programming languages.

This seems straightforward until you start thinking about what can go wrong. And a *lot* can go wrong.

## The research library that became a roadmap

The 150+ paper library wasn't just background reading — it became a design roadmap. Papers on benchmark contamination taught me to worry about instruction leakage. Work on LLM-as-judge evaluation shaped how I think about verification. Studies on agent tool use influenced how I structured the MCP configurations.

But the most important thing the research taught me was what *not* to do. Too many benchmarks optimize for a clean headline number — "Agent X achieves 73% on Benchmark Y!" — without examining whether the 73% means what you think it means. Are the tasks representative? Is the verification sound? Are there confounders hiding in the setup?

I wanted CodeContextBench to be built for *understanding*, not just measurement. That meant designing tasks where the per-category and per-task breakdowns tell you more than the aggregate, and investing heavily in quality assurance even when it slowed everything down.

## What I built

### Custom benchmarks

These are the benchmarks I designed from scratch, targeting capabilities that existing benchmarks don't cover.

**Kubernetes Documentation Generation (5 tasks).** This is the benchmark I'm most excited about. I stripped all documentation from a Kubernetes checkout and asked agents to regenerate it from code alone — API docs for the apiserver library, controller deep-dives for the Garbage Collector, scheduler plugin docs for PodTopologySpread. The existing human-written docs serve as ground truth.

These tasks are *hard*. Here's an abbreviated version of the apiserver task:

> *Generate comprehensive package documentation for the `staging/src/k8s.io/apiserver` package in Kubernetes. This library maps multiple sub-packages — pkg/server, pkg/admission, pkg/authentication, pkg/authorization, pkg/endpoints, pkg/registry — that together form the framework for extension API servers. Understanding its scope requires discovering how GenericAPIServer composes these sub-packages and how API aggregation works.*

Understanding how any of this works requires tracing dependency graph propagation, owner reference resolution, and cross-package composition across the entire codebase. You can't just grep for it. The Kubernetes team has a [mandate of no AI-generated docs](https://github.com/kubernetes/website/pull/48913) precisely *because* of how challenging it is for agents to get this right. If code intelligence tools can crack this, that's a meaningful result.

**Large-Repo Feature Implementation (4 tasks).** Building directly on Trevor's research, four feature implementation tasks in codebases over 1GB:

- Adding `scrollend` DOM event support across Servo's browser engine (Rust, ~300K files)
- Implementing a `NoScheduleNoTraffic` taint effect across Kubernetes' scheduler, admission, endpoint, and node controllers (Go)
- Adding a W4A8 quantization mode across TensorRT-LLM's Python/C++ boundary (C++)
- Fixing stale TypeScript diagnostics after a Git branch switch in VS Code (TypeScript)

To put the scale in perspective: a 1M token context window holds roughly the Lord of the Rings trilogy, and you probably only get effective usage from about 200K tokens — so, The Hobbit. These codebases are *thousands of Hobbits*. An agent cannot read its way through them. It has to search.

**Code Review with Injected Defects (3 tasks).** I took real merged PRs from Ghost, ASP.NET Core, and cal.com, then injected realistic defects back into the code — functional bugs and compliance violations. Agents have to both *detect* the defects and *fix* them.

The Ghost task, for example, uses [PR #26260](https://github.com/TryGhost/Ghost/pull/26260) (comment likes feature) and injects 4 defects across three backend files: a missing NotFoundError guard, a wrong variable reference for `frame.options.id`, a broken cache invalidation call, and a missing `member` relation in the data model. Scoring is hybrid: 50% detection F1 (precision and recall) + 50% fix correctness.

Designing the defect injection was its own iteration. I started with sed-based transformations but multi-line code removal is fragile in sed. I switched to Python regex, which was better. For the ASP.NET Core task, I ended up using Python `str.replace()` with exact multi-line string matching — simpler and more reliable when the code blocks are unique. Each defect injection script is idempotent, so sections can be re-run independently without collisions. Small details, but they matter when you're trying to create reproducible ground truth.

**Cross-Repository Reasoning (5 tasks).** A single Docker image with Kubernetes, Envoy, Django, and TensorFlow (~5GB of code). Tasks require understanding relationships across packages: migrating deprecated gRPC `Dial()` calls to `NewClient()` across etcd, Kubernetes, and containerd; localizing a nil pointer dereference in EventedPLEG; tracing a Pod creation request from HTTP handler through validation; renaming a symbol throughout the codebase without breaking anything.

These tasks are tedious, error-prone, and require exactly the kind of codebase-wide awareness that code search tools are designed to provide.

### Curated from existing benchmarks

I selected subsets from 10 existing benchmarks to complement the custom ones:

- **SWE-bench Pro (36 tasks)**: Real bug fixes across 11 repositories (NodeBB, Ansible, Teleport, Element, Flipt, and others). Proportionally sampled, prioritizing tasks that touch the most files.
- **LoCoBench (25 tasks)**: Synthetic codebases with 1M+ token contexts and 70+ files. Prioritizing architectural reasoning and cross-file refactoring.
- **PyTorch (12 tasks)**: Cross-module bug fixes mined from real PRs, each touching 2–8 files.
- **LinuxFLBench (5 tasks)**: Linux kernel fault localization from real Bugzilla reports. Expert-level difficulty. One task asks the agent to trace an ACPI backlight control failure on an Acer TravelMate 5735Z from a user report through the kernel's video detection subsystem to identify the exact file and function that needs a DMI quirk entry.
- **DependEval (32 tasks)**: Dependency ordering across 4 languages.
- **Plus** RepoQA (10), TAC (8), DIBench (8), SWE-Perf (3)

The selection methodology uses a 4-component MCP benefit scoring formula to predict which tasks should benefit most from code intelligence tools:

```
score = 0.25 × context_complexity + 0.30 × cross_file_deps
      + 0.20 × semantic_search_potential + 0.25 × task_category_weight
```

This gives us a way to test whether the predicted benefit matches actual outcomes — not just "did MCP help overall" but "did it help *where we expected it to*?"

## Everything that went wrong (the engineering journey)

Building the benchmark tasks was maybe 30% of the work. The other 70% was infrastructure, and the infrastructure humbled me.

### Platform musical chairs

My first attempt was running everything from my MacBook. That lasted until the first Docker build failed with an architecture mismatch — the benchmark containers are `amd64` and my Mac is `arm64`. Cross-architecture emulation exists but it's slow and unreliable for complex builds like the Linux kernel or PyTorch.

Plan B was [Daytona](https://www.daytona.io/), a cloud development environment. That worked for baseline runs, but on the free tier you can't connect to external networks — which is a requirement for the Sourcegraph MCP. The entire point of the evaluation is testing external tool access, so this was a non-starter for MCP configurations.

Plan C was a GCP virtual machine, which is where everything runs now. Getting the full environment set up — Docker, Harbor, multi-account Claude Code auth, Sourcegraph MCP connectivity, sufficient disk for 1GB+ codebases — was its own project. But it works, and it's reproducible.

### Harbor: my new best friend and occasional nemesis

[Harbor](https://github.com/laude-institute/harbor/tree/main) is the execution platform that runs each task in an isolated Docker container with standardized interfaces for agent interaction and verification. None of the existing benchmarks came with Harbor adapters out of the box, so I had to create adapters for all 13 benchmark suites — each with its own Dockerfile, `task.toml` configuration, and verification scripts. That was its own learning process.

The critical insight that took weeks to internalize: Harbor's Docker build context is the *task root directory*, not the `environment/` subdirectory where the Dockerfile lives. This means `COPY environment/inject_defects.sh /workspace/` works, but `COPY inject_defects.sh /workspace/` doesn't. Harbor also uploads the `tests/` directory to `/tests/` in the container at runtime, so you reference test scripts at `/tests/test.sh`, not `/workspace/tests/test.sh`. Getting these paths wrong produces cryptic Docker build failures that don't obviously point to the root cause. I hit this enough times that I eventually added it to my project memory as a bolded warning.

### The 1,000-repo mirroring problem

Here's something I didn't anticipate when I designed the experiment: for the MCP configurations to be valid, the code the agent searches in Sourcegraph must be the *exact same code* running in the Docker container. Same repository, same commit. Off by one commit and you're measuring noise.

Sourcegraph indexes repositories and by default searches over HEAD — the latest code on the default branch. But benchmark tasks pin specific historical commits. A bug fix from PyTorch PR #169484 runs against commit `ca2466126a`, not whatever's on `main` today.

The solution was creating mirror repositories in a dedicated [sg-benchmarks](https://github.com/sg-benchmarks) GitHub organization, each pinned to the precise commit used in the benchmark task. For the 91 tasks that use MCP, I created 42 custom mirrors and mapped 49 public GitHub repos. Every mirror has its HEAD set to the exact commit the agent works against.

This got interesting for large repositories. The Linux kernel (used in LinuxFLBench) is over 2GB with full history. Pushing full history to GitHub fails with HTTP 500 errors. I ended up using an orphan commit approach: shallow clone at the specific tag, `checkout --orphan`, `git add -A`, commit, push. One clean snapshot, no history, correct content.

Linux stable releases like v5.6.7 aren't in `torvalds/linux` — they're in `gregkh/linux`. RC releases like v5.6-rc2 are in `torvalds/linux`. I learned this the hard way, wondering why a tag didn't exist.

### When the agent won't use the tools you gave it

Giving an agent MCP tools doesn't mean it will use them. In early runs, I watched Claude Code receive Sourcegraph search capabilities and then... just use `grep`. It already knows how to grep. Grep is fast and familiar. Why would it try something new?

This kicked off an iteration cycle on prompt engineering that I hadn't planned for. The agent harness injects MCP guidance through a system prompt preamble — separate from the task instructions, so baseline runs stay uncontaminated. But the preamble went through multiple versions:

- Version 1: Politely suggest using MCP tools. **Result:** Agent ignores suggestion, greps everything.
- Version 2: Strongly recommend MCP tools with a tool substitution guide (Grep → `sg_keyword_search`, Glob → `sg_list_files`, etc.). **Result:** Better adoption, but still inconsistent.
- Version 3: Block local search tools entirely via `--disallowedTools`. **Result:** Agent uses MCP but loses fallback when MCP isn't helpful. Too aggressive.
- Final approach: Hybrid. Allow all tools but lead with strong MCP-first guidance and include the specific repository name the agent should search. Let the agent make strategic choices.

The biggest prompting lesson was repository targeting. The MCP searches across *all* indexed repositories by default. If you don't tell the agent "search in `pytorch/pytorch`," it might search in forks, mirrors, or unrelated repos. Adding the repo name to the preamble was a one-line change that dramatically improved search relevance.

### Deep Search: the async tool problem

This one was painful. Deep Search is Sourcegraph's semantic, multi-hop code understanding tool. It's powerful — it can trace data flow across files, understand architectural patterns, and answer questions about code relationships. It's also asynchronous: you submit a query, it takes 50–300 seconds to process, and you poll for results.

During a QA audit, I discovered that **70.1% of Deep Search calls** were returning only polling responses, and **38% of tasks never got results at all**. The agents were polling once or twice, seeing "still processing," and moving on to something else. From the agent's perspective, the tool was broken. From our perspective, we were measuring "does the agent give up on slow tools" rather than "does Deep Search help."

The fix was embarrassingly simple: add an instruction telling the agent to retry `sg_deepsearch_read` at least 3 times before giving up, because Deep Search takes 50–120 seconds. Compliance jumped from <10% to 90%+.

But here's the deeper insight: LLMs don't naturally understand asynchronous I/O patterns. They're trained on synchronous interactions where you call a tool and get a result. An async tool that says "check back later" breaks that mental model. This isn't a tool bug or a model bug — it's an interaction design problem. And without a systematic audit, I never would have caught it.

### Verification: trust nothing

Your benchmark is only as good as your verification. Here's a sampler of verifier bugs I caught:

**PyTorch:** The original verifier used `make test` to check agent solutions. Sounds reasonable. Except the test suite had build issues in the containerized environment that caused it to always exit 0 — every run got reward=1.0 regardless of code quality. I rebuilt the verifier with a diff-based approach comparing against expected patches from the ground-truth PR.

**CrossRepo:** The test script looked for verification files at `/task/tests/` when Harbor uploads them to `/tests/`. Every test "failed" even when the agent's code was correct.

**TAC:** Test scripts expected `--result_path` but the verifier was passing `--output_path`. Silent mismatch, silent failure.

Each of these, individually, would have produced results that looked reasonable. A mean reward of 0.6 seems plausible. You'd publish a paper with a clean table and nobody would question it. That's what makes evaluation hard — the failure mode isn't "obviously wrong numbers," it's "subtly wrong numbers that confirm your priors."

## The QA audit that changed everything

About a week into running benchmarks, I conducted a systematic quality audit across six dimensions:

1. **Instruction contamination**: Do baseline task files mention MCP/Sourcegraph?
2. **Reproducibility**: Are Docker images, commits, and dependencies pinned?
3. **Verifier correctness**: Do test scripts produce accurate rewards?
4. **Ghost/false-positive detection**: Are there runs with 0 tokens and perfect scores?
5. **Error misclassification**: Are infrastructure failures counted as task failures?
6. **Tool effectiveness**: Is the MCP actually being used? Is Deep Search returning results?

**I found 28 issues.** Nine critical, five high-priority, six medium, eight low.

Beyond the verifier bugs above, I found 47 ghost runs — tasks that "completed" with 0 tokens and perfect scores, from broken verifiers interacting with unindexed repos. Five context window errors were being misclassified as task failures, inflating failure rates for the hardest tasks. And the Deep Search polling failure meant an entire configuration's results were unreliable.

After the audit, I archived corrupted runs (preserving them for forensic analysis rather than deleting — you never know when you'll need to understand a failure mode), fixed verifiers, added Deep Search retry instructions, and built a pre-flight validation pipeline with automated error fingerprinting across 12 pattern categories. The fingerprinting system classifies failures into actionable buckets — `token_refresh_403`, `api_500`, `mcp_connection`, `context_window_exceeded`, `deep_search_polling_only` — so I can immediately tell whether a failure is infrastructure, task difficulty, or a verifier bug.

## Building the benchmark with the agent I'm benchmarking

Yes, a large portion of CodeContextBench was built using Claude Code itself. The irony wasn't lost on me.

Claude Code scaffolded task structures, wrote Docker configurations, generated verification scripts, iterated on defect injection code, and built the operational infrastructure — 11 slash commands for the full benchmark lifecycle, from `/check-infra` (verify tokens, Docker, disk space before a run) to `/triage-failure` (investigate why a specific task failed with log analysis and error fingerprinting).

It was genuinely useful. But it also gave me firsthand experience with both its strengths and limitations in ways that directly informed benchmark design. When Claude Code struggled to write a correct multi-line sed transformation for defect injection, I switched the approach to Python `str.replace()` — and then included that kind of multi-file code transformation task in the benchmark. When it needed three attempts to get a Dockerfile's COPY paths right because of Harbor's build context semantics, I knew that was a real-world challenge worth testing.

Using the agent-under-test to build the test is unusual, but I'd argue it's a feature. You develop intuition for where the agent needs help that you can't get from reading papers alone.

## Early signals (with caveats)

I want to be upfront: the full results aren't ready. I'm still validating runs — fixing cases where the MCP wasn't searching the correct repo because the repo name wasn't in the preamble, or where Deep Search results were lost to polling, or where the LLM judge didn't have sufficient context, or where Docker build errors masked the actual outcome. Evaluation is an ongoing process, not a single measurement.

That said, here's what preliminary data from 66 tasks across 3 benchmarks shows:

| Config | Mean Reward | Pass Rate |
|---|---|---|
| Baseline | 0.548 | 74.2% |
| MCP-Full | 0.553 | 74.2% |

The aggregate is close. But the aggregate hides what's interesting.

**By task type, the story diverges:**
- *Implementation (refactoring)*: Baseline 0.422 → MCP-Full 0.445 (+5.5%) — these are 1M+ token tasks with 70+ files
- *Architecture & Design*: 0.451 → 0.452 (flat)
- *Implementation (bug fix)*: 0.608 → 0.608 (identical)

**Tool utilization varies dramatically:**
- LoCoBench agents averaged 12.6 MCP calls per task (27% of all tool calls)
- SWE-bench Pro agents averaged only 1.9 MCP calls (4.4%)
- Keyword search dominates; Deep Search was barely used (0.0–0.1 calls per task — this was before the polling fix)

**The cost dimension:**
MCP-Full runs cost more. LoCoBench: $181 MCP vs $133 baseline (+36%). SWE-bench Pro: $205 vs $185 (+11%). The additional cost comes from MCP tool call tokens.

The small aggregate difference doesn't surprise me. These early runs had the Deep Search polling bug (70% failure rate), so MCP-Full was essentially operating as MCP-Base-minus. The refactoring improvement in LoCoBench is the most promising signal — tasks with massive contexts and many files, exactly where you'd expect code search to matter. But I won't draw conclusions until the validation is complete and all three configurations are running clean.

## What I've learned about benchmarking (so far)

**Measuring is harder than building.** The tasks themselves took real effort, but verification, quality assurance, and confounder elimination took 3× as long. If you're building an evaluation and you haven't budgeted more time for QA than for task design, recalibrate.

**Aggregate numbers obscure.** A mean reward of 0.548 vs 0.553 looks like "no difference." But within that aggregate, there are task categories showing 5%+ improvement and others showing zero. The interesting findings are always in the breakdowns.

**Verifier bugs are silent killers.** A verifier that always returns 1.0 produces results that look perfectly plausible. The only way to catch it is to manually inspect runs end-to-end. Trust, but verify your verifiers.

**Async tools need explicit interaction design.** LLMs don't naturally understand asynchronous I/O. If a tool takes 2 minutes to return results, an agent will move on after 10 seconds unless you explicitly tell it to wait. This isn't a tool problem — it's an interaction design problem that affects any agent system with slow external tools.

**Your evaluation infrastructure is a product.** Error fingerprinting, pre-flight validation, automated archival, cost reporting — I didn't plan to build any of this. But you can't manage 468 runs (156 tasks × 3 configs) without it. The operational tooling became as important as the benchmark itself.

**Build with the thing you're evaluating.** Using Claude Code to build CodeContextBench gave me firsthand intuition for where agents need help. When the agent I'm building a benchmark for struggles with a task I designed, that's signal.

## What this doesn't tell you (yet)

I want to be upfront about the limitations, because I think the field has a problem with overclaiming benchmark results:

- **Single agent family.** I've only tested Claude Code so far. Other agents might show different patterns.
- **Single MCP provider.** I work at Sourcegraph, so I tested Sourcegraph's MCP. Other code intelligence tools might yield different results.
- **Open-source codebases only.** Enterprise codebases have characteristics — legacy complexity, proprietary frameworks, regulatory constraints — that we haven't captured. Not to mention the contamination concern of benchmark code appearing in model training data. That's why I'm actively looking for industry partners for case studies.
- **Validation in progress.** The early numbers above come with real caveats about prompt issues, polling bugs, and verifier fixes. I'll report clean numbers when I have them.

## What's next

The full results — all 156 tasks, all 3 configurations, with statistical analysis and per-task breakdowns — are coming in Part III alongside a companion white paper. I'm particularly watching for:

- **K8s documentation generation** with working Deep Search (if code intelligence cracks documentation inference, that's a headline result)
- **Code review defect detection** rates across configurations (can MCP help agents find more bugs?)
- **LargeRepo outcomes** (can an agent implement a feature across a 1GB codebase without code search? Trevor's qualitative testing says no — I want the numbers)
- **Cost-per-successful-task** analysis (even if MCP improves outcomes, is it worth the token cost?)
- **Deep Search impact post-fix** (what happens when agents actually *use* the tool?)

## Try it yourself

Everything is open source and under active development:

- **CodeContextBench**: [github.com/sjarmak/CodeContextBench](https://github.com/sjarmak/CodeContextBench)
- **Dashboard**: [github.com/sjarmak/CodeContextBench_Dashboard](https://github.com/sjarmak/CodeContextBench_Dashboard)
- **Mirrored repos for Sourcegraph indexing**: [github.com/sg-benchmarks](https://github.com/sg-benchmarks)

The benchmark framework supports custom task definitions and new agent configurations. I'm particularly interested in hearing from teams who want to run evaluations against their own codebases, or who want to plug in different agents or code intelligence tools. If you're interested in an enterprise case study, reach out.

---

*Methodology note: This post presents the benchmark design journey and preliminary findings from partial runs under active validation. Part III will link to a white paper with the complete methodology, all validated results with statistical analysis, threats to validity, and full reproducibility details.*
