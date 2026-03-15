# Reliable AI Coding Agents — Chapter Outline

**Estimated length: 300–350 pages**

---

## Part I — The Coding Agent Problem

Three chapters that establish the mental model. A reader who knows nothing about coding agents starts here and understands why naive approaches fail by the end of Part I.

---

### Chapter 1: The Rise of AI Coding Agents

**~20 pages**

What coding agents are, how they work, and why they represent a qualitatively different challenge from code completion or chat-based assistants.

- From autocomplete to autonomous agents: the progression from Copilot-style completion to agents that plan, search, edit, and verify
- The anatomy of a coding agent: model, tools, context, execution loop
- Tool use as the distinguishing capability: agents interact with codebases through tools (file read, search, terminal, code navigation), not just generation
- The promise: automate real software engineering work across the full development lifecycle
- The reality: agents work impressively on small demos and fail unpredictably on real codebases
- What changed in 2025–2026: MCP standardization, background agents, enterprise deployment pressure
- The central question this book answers: what infrastructure makes coding agents reliable?

---

### Chapter 2: Why Coding Agents Fail in Real Codebases

**~25 pages**

The failure taxonomy. Opens with a case study and develops the systematic patterns that cause agents to fail at scale.

- **Opening case study:** An agent is given a code comprehension task in the Kubernetes monorepo (1.4M lines, 22,000+ Go files). It burns its entire 6,000-second timeout navigating the codebase and produces nothing. The same agent, given code search tools, completes the task in 89 seconds with a score of 0.90. Same model. Same task. Different infrastructure.
- The seven failure modes (from 1,281 scored agent runs):
  1. **Lost in the codebase** — agent navigates endlessly, exhausts timeout
  2. **Wrong file, wrong symbol** — grep returns 200 matches, agent picks the wrong one
  3. **Partial completion** — found 3 of 7 affected files in a cross-file refactoring
  4. **Tool thrashing** — 96 tool calls over 84 minutes vs. 5 targeted searches in 4 minutes
  5. **Context overflow** — agent reads too much irrelevant code, loses track of the task
  6. **Silent failure** — agent completes in under 2 seconds because it never actually installed or ran
  7. **Adversarial optimization** — agent uses `git show HEAD:filename` to recover code from history, circumventing experimental controls
- Why these failures are infrastructure problems, not intelligence problems
- The variance problem: same agent, same task, different outcome on every run
- Why single-number benchmarks (pass@1, solve rate) hide everything interesting
- Preview: how Parts II–V address each failure mode

---

### Chapter 3: The Context Window Problem

**~20 pages**

The gap between what an agent can see and what it needs to see. This is not just about token limits.

- Context windows explained: what fits, what doesn't, and why "just make the window bigger" doesn't solve the problem
- The real bottleneck: even with a million-token window, the agent still needs to know which files to read
- Three dimensions of the context gap:
  1. **Scale** — codebase has 10M lines, context window holds 200K tokens
  2. **Spread** — relevant code spans 7 files across 4 repositories
  3. **Selection** — agent must decide what to include before it knows what matters
- The retrieval-outcome disconnect: better file recall does not reliably predict better task outcomes. Finding the right files is necessary but not sufficient.
- Context quality vs. context quantity: the distraction effect (providing more context can hurt agent performance)
- Empirical data: MCP-augmented agents are 30% cheaper and 100 seconds faster on average — not because they see more code, but because they see the right code
- The thesis: reliable coding agents require a context retrieval layer — an infrastructure system that finds, ranks, and delivers relevant code to the agent. The rest of this book explains how to build one.

---

## Part II — Understanding Large Codebases

Three chapters that explain the systems needed to make codebases machine-navigable. This is the infrastructure layer that sits between raw source code and an agent's context window.

---

### Chapter 4: Repository Structure and Dependency Graphs

**~22 pages**

Before an agent can search code, the code must be structured for machine understanding. This chapter covers what that structure looks like.

- What agents need to know about a codebase that humans take for granted:
  - Which files belong to which components
  - How modules depend on each other
  - Where the boundaries are between packages, services, and repositories
- Monorepo vs. polyrepo: qualitatively different challenges for agents
  - Monorepo: single clone, but path explosion (22K files in Kubernetes)
  - Polyrepo: manageable per-repo, but cross-repo dependencies are invisible to local tools
- Dependency graphs at three levels:
  1. **File-level:** imports, includes, requires
  2. **Package-level:** Go modules, Java packages, npm workspaces, Python packages
  3. **Service-level:** API contracts, event schemas, runtime dependencies
- Build system awareness: understanding `BUILD`, `pom.xml`, `package.json`, `go.mod` relationships
- Version pinning: agents must work against specific commits, not trunk. The infrastructure for consistent version access is non-trivial.
- Repository mirroring strategies and the clone-at-verify pattern
- Multi-language codebases: when the dependency graph spans language boundaries

---

### Chapter 5: Indexing Code for Machine Understanding

**~22 pages**

How to build and maintain indexes that make code searchable by agents. This is the most infrastructure-heavy chapter and where the Sourcegraph domain expertise differentiates.

- What a code index needs to capture:
  - Lexical content (tokens, identifiers, string literals)
  - Structural relationships (definitions, references, call sites, type hierarchies)
  - Semantic meaning (what a function does, not just what it's named)
- Indexing strategies:
  - Trigram indexes for fast lexical search
  - SCIP/LSIF for precise cross-repository code navigation (go-to-definition, find-references)
  - Embedding indexes for semantic similarity search
- Agent-facing indexes vs. human-facing indexes:
  - Humans browse; agents query. Different access patterns require different index designs.
  - Freshness requirements: agents working on pinned commits vs. trunk
  - Index coverage decisions: what to index, what to skip, how stale is too stale
- Scaling indexing infrastructure:
  - Single-tenant vs. multi-tenant
  - Incremental indexing vs. full reindex
  - The 180-mirror problem: maintaining version-pinned indexes for benchmark evaluation
- The cost of not indexing: what happens when agents rely on grep and glob alone
  - Empirical data: keyword search (7,993 calls) vs. semantic search (2,449 calls) vs. deep search (57 calls) — agents overwhelmingly prefer the simplest tool that works

---

### Chapter 6: Semantic Code Search

**~22 pages**

The search layer that agents use most. Covers the spectrum from lexical to AI-powered search and when each is appropriate.

- The search modality spectrum:
  1. **Lexical search** — exact and regex matching. Fast, precise, the workhorse.
  2. **Semantic search** — embedding-based similarity. Handles natural language queries ("find the retry logic with exponential backoff").
  3. **Symbol navigation** — go-to-definition, find-references. The structural backbone for refactoring and dependency tracing.
  4. **AI-powered search** — multi-step retrieval that combines search, reading, and reasoning. Powerful but expensive and slow.
- Why agents prefer keyword search (and why that's fine): it's predictable, fast, and composable. Semantic search is a complement, not a replacement.
- Search quality metrics for agents:
  - Time to First Relevant File (TTFR)
  - File recall and precision at k
  - Search result ranking quality (MRR, MAP)
- Building search APIs for agent consumption:
  - Result format: what agents need (file path, line range, content snippet, confidence)
  - Pagination and streaming for large result sets
  - Rate limiting: graceful degradation, not hard failure
  - Schema stability: breaking changes cascade into agent failures at scale
- Case study: Strata Java refactoring — keyword search for `RecordAccumulator` found all 7 affected files in 5 calls vs. baseline's 96 grep calls finding 2

---

## Part III — Context Retrieval Systems

Three chapters on assembling context from search results and delivering it to agents through reliable interfaces. This is the layer between "code is searchable" and "agent has what it needs."

---

### Chapter 7: Constructing Context for AI Coding Agents

**~25 pages**

The practical core of the book. How to select, rank, and assemble the right code context for an agent to consume.

- The context construction pipeline:
  1. **Task analysis** — what does the agent need to accomplish?
  2. **Broad retrieval** — cast a wide net to find candidate files
  3. **Relevance filtering** — rank and prune candidates
  4. **Context assembly** — arrange selected content within token budget
- The "would this file appear in git diff?" heuristic: the single most effective relevance filter discovered during ground truth curation
- Task-type-aware retrieval: different work types need different strategies
  - Bug fixes: narrow, focused retrieval (find the broken code)
  - Refactoring: broad structural retrieval (find all affected files)
  - Security audit: cross-cutting retrieval (find all instances of a pattern)
  - Comprehension: hierarchical retrieval (understand the architecture first, then zoom in)
- The distraction effect: when more context hurts
  - Empirical data: MCP-augmented agents took 66–183% longer on some task types
  - Mechanism: agents read search results instead of implementing solutions
  - The attention budget: every context addition costs reasoning tokens
  - When to withhold context: single-file fixes, test generation, small-repo tasks
- Codebase size thresholds: where code intelligence tools help most
  - 400K–2M LOC: strongest positive effect (+0.259 reward delta)
  - 8M–40M LOC: consistent positive effect (+0.055)
  - <400K LOC: tools add overhead (−0.080)
- Hybrid retrieval pipelines: broad search + precise curation
  - Curator-only F1=0.524 beats union merge F1=0.468 — simpler is better
  - Provenance data: files found by both methods are correct 92% of the time
- The retrieval-outcome disconnect: better retrieval does not reliably predict better task outcomes. Why this matters and what it implies for system design.

---

### Chapter 8: Multi-Repository Reasoning

**~22 pages**

The highest-value problem for enterprise coding agents. This is where code intelligence tools show their strongest empirical signal.

- Why multi-repo is qualitatively different from single-repo:
  - Single-repo: grep often works. Multi-repo: agents are blind to code outside their clone.
  - Empirical data: multi-repo retrieval improvement is +0.209 F1 delta vs. +0.085 for single-repo
- The organizational discovery problem: "which of our 200 repos are affected by this CVE?"
- Multi-repo reasoning patterns:
  1. **Cross-repo symbol resolution** — following a function definition across repository boundaries
  2. **Dependency chain tracing** — from consumer to provider to transitive dependency
  3. **Impact analysis** — mapping all downstream consumers of a changed interface
  4. **Incident debugging** — tracing error propagation across microservices
- Enterprise use cases with the strongest empirical signal:
  - Vulnerability remediation across repositories: +0.085 to +0.113 reward delta
  - Framework migration: finding all consumers of a deprecated API
  - Incident debugging across microservices: +0.081 reward delta
  - Compliance review: tracing data flows across service boundaries
- Multi-repo infrastructure requirements:
  - Cross-repo indexes (SCIP/LSIF that spans organizational boundaries)
  - Repository manifests: declaring which repos are relevant to a task
  - Cross-repo search APIs: querying across repositories in a single call
- Case study: Cross-organization Kubernetes + Grafana task (2.9GB combined) — how the agent maps dependencies across two massive codebases

---

### Chapter 9: Tool Interfaces and Agent Architectures

**~25 pages**

How agents connect to code intelligence systems. Covers protocols, connection modes, and the adoption problem.

- **Four connection architectures:**
  1. **MCP (Model Context Protocol)** — standardized tool interface, native to some agent frameworks. Strengths: structured schemas, tool discovery. Weaknesses: framework-specific config, nascent governance.
  2. **CLI** — agent invokes command-line tools via shell. Strengths: universal, simple, composable. Weaknesses: startup latency, output parsing, no streaming.
  3. **SDK** — agent code imports a library directly. Strengths: lowest latency, richest error handling. Weaknesses: language-specific, tighter coupling.
  4. **Raw API** — agent makes HTTP/GraphQL requests. Strengths: universal, cacheable. Weaknesses: most boilerplate, no tool discovery.
- When to use each: decision framework based on deployment model
  - Interactive agents: MCP or CLI
  - Background agents: SDK or MCP
  - Batch evaluation: SDK
  - Prototyping: CLI
  - Multi-framework: API + abstraction layer
- The adoption problem: making agents actually use tools
  - Five iterations of prompt engineering for tool adoption (V1–V5)
  - The adoption-prescription tradeoff: mandate tools and agents over-rely on them; suggest tools and agents ignore them
  - The sweet spot: constrain the environment (remove local source), guide the workflow (explain what tools do and when to use them)
  - Tool mandating → "death spirals" (agents retry failing queries in infinite loops, consuming entire timeout)
- The abstraction layer pattern for future-proofing:
  - Build a thin interface: `search()`, `navigate()`, `references()`
  - Swap connection modes behind the interface
  - When protocols evolve, only the adapter changes
- API design considerations for agent-facing endpoints:
  - Auth conventions: the `Bearer` vs. `token` header disaster (OpenHands integration failure)
  - Timeout contracts: 30s default vs. 60s+ for complex queries
  - Idempotency: agents retry failed calls; endpoints must be safe to retry
  - Result schema stability: agents parse outputs; breaking changes cascade at scale
- Protocol evolution: where MCP is heading (enterprise governance, multi-agent communication, SSO integration) and how to build systems that survive protocol changes

---

## Part IV — Evaluation

Three chapters on measuring whether coding agents actually work. This is the section that transforms the field from "it seems to work" to "we can prove it works."

---

### Chapter 10: Why Existing Benchmarks Fail

**~22 pages**

Most coding agent benchmarks produce misleading results. This chapter explains why and what to do instead.

- Five flaws in current benchmarks:
  1. **Small/single repos** — SWE-Bench uses ~50K LOC Python repos. Enterprise codebases are 100–1000x larger.
  2. **Language monoculture** — >90% Python in most benchmarks. Enterprise code is polyglot.
  3. **Bug-fix-only task distribution** — issue resolution is easiest to mine from GitHub. Real development is broader.
  4. **Gameable verifiers** — install scripts that print "SUCCESS" regardless of outcome. Test suites that pass with empty implementations.
  5. **No retrieval measurement** — pass/fail tells you whether the agent succeeded, not how it found the code it needed.
- Why benchmark results are universally misinterpreted:
  - Leaderboard incentives vs. engineering insight
  - The pass@1 illusion: variance across runs is enormous
  - Single-number aggregates hide the interesting signal
- What a useful benchmark actually measures:
  - Task completion across the full development lifecycle (not just bug fixes)
  - Retrieval quality: precision, recall, MRR, TTFR
  - Efficiency: cost, wall-clock time, tool utilization
  - Auditability: full transcripts, not just scores
- The information parity principle:
  - Test tool effectiveness, not information advantage
  - Same agent, same task, same information, different access method
- Dual evaluation modes:
  - Direct (patch-based): agent modifies code, verifier runs tests
  - Artifact (oracle-based): agent produces structured answer, verifier compares to ground truth
  - Why both are needed: separates code generation ability from information retrieval ability
- The case for shipping agent transcripts with results

---

### Chapter 11: Mining Tasks from Software Repositories

**~22 pages**

Where evaluation tasks come from and how to construct high-quality benchmarks from real codebases.

- Why synthetic tasks produce misleading results
- Mining strategies:
  1. **Issue-PR pairs** — real bugs with real fixes (SWE-Bench approach). Easiest to mine, but biased toward bug fixes.
  2. **Commit archaeology** — reconstruct development tasks from commit history. Broader coverage but harder to verify.
  3. **Codebase analysis** — identify structural patterns that generate tasks (unused APIs, inconsistent patterns, missing tests). Best for refactoring and comprehension tasks.
  4. **Cross-repo pattern mining** — find tasks that span organizational boundaries. Hardest to mine, highest value.
- Task quality criteria:
  - Non-trivial: agent must do real work, not just copy a template
  - Verifiable: deterministic scoring without LLM involvement
  - Representative: reflects actual developer work, not benchmark-optimized scenarios
  - Reproducible: pinned commits, deterministic containers, version-locked dependencies
- The nine work types that cover enterprise development:
  cross-repo navigation, understanding, refactoring, security, feature implementation, debugging, bug fixing, testing, documentation
- Constructing ground truth:
  - Curator agents for automated oracle generation
  - Task-type-aware curation profiles
  - The two-question test file gate
  - Multi-repo path normalization challenges
- Scaling task construction: from 10 hand-crafted tasks to 381 systematically curated tasks
- Common pitfalls:
  - Bare `$VAR` in instructions gets expanded
  - Install scripts that always report success
  - Validators duplicated across tasks (changes must apply to all copies)

---

### Chapter 12: Designing Realistic Agent Evaluations

**~22 pages**

How to build evaluation systems that produce useful, reproducible signal for your own codebase and agents.

- Designing reproducible evaluations:
  - Deterministic verification: compile, test, diff, checklist → reproducible 0.0–1.0 score
  - LLM judges as secondary signal only (non-deterministic, JSON parsing failures, calibration required)
  - The verification hierarchy: deterministic verifier > LLM judge > IR metrics > statistical analysis
- Multi-run measurement:
  - Single runs are unreliable. Always run 3+ times per task/config pair.
  - Per-task mean before cross-task aggregation (avoids run-count bias)
  - Confidence intervals, not point estimates
  - Reward-delta variance: what "noisy" vs. "stable" looks like in practice
- The metrics hierarchy:
  1. **Task metrics:** reward score, pass rate, partial credit
  2. **Retrieval metrics:** file recall, MRR, MAP, precision@k, TTFR
  3. **Efficiency metrics:** cost, wall-clock time, agent execution time, tool call count
  4. **Behavioral metrics:** tool adoption rate, utilization overlap, backtrack count
- The retrieval-outcome disconnect:
  - Better file recall doesn't reliably predict better task outcomes
  - Correlation is weak. Why: the structure of tool output, how search results prime reasoning, and agent non-determinism all matter.
  - Implication: optimizing retrieval alone is insufficient
- The six-dimension QA framework:
  1. Task validity — instruction quality, Dockerfile correctness
  2. Outcome validity — verifier soundness, scoring accuracy
  3. Reporting — result extraction, metrics completeness
  4. Reproducibility — deterministic environments, pinned commits
  5. Tool effectiveness — adoption rates, death spiral detection
  6. Statistical validity — sample size, paired comparison integrity
- Building an evaluation pipeline for your own codebase:
  - Start with 10 tasks from your actual development workflow
  - Build deterministic verifiers before anything else
  - Instrument agent runs for full transcript capture
  - Iterate on task quality before scaling quantity

---

## Part V — Production Systems

Three chapters on deploying coding agents in real enterprise environments. This is where the book bridges from "this works in evaluation" to "this works in production."

---

### Chapter 13: Debugging Agent Failures

**~22 pages**

Systematic approaches to understanding why agents fail and how to fix the infrastructure, not the agent.

- The debugging mindset: most agent failures are infrastructure failures
  - Infrastructure failure: OOM, timeout misconfiguration, missing dependencies, auth mismatch
  - Retrieval failure: agent can't find the relevant code
  - Reasoning failure: agent found the code but produced the wrong output
  - Separating these categories is the first step
- Reading agent transcripts:
  - Tool call sequences: what the agent tried and in what order
  - Backtrack patterns: 6 backtracks in 84 minutes = retrieval failure
  - Token usage: where the context budget went
  - Time distribution: search vs. reading vs. editing vs. verification
- The heuristic toolkit:
  - <2 second completion = agent never ran
  - Score=0 with duration <30s = rate limited, not failed
  - Zero tool usage with tools available = adoption failure
  - 314 timeouts in one batch = systemic infrastructure issue
- Infrastructure debugging:
  - Container resource limits (Jest + TypeScript needs 4–6GB, not the default 2GB)
  - Auth header mismatches (the OpenHands disaster: all "MCP" runs had 0 tools loaded)
  - Environment variable propagation (`export` for subprocesses)
  - Orphaned sandboxes consuming resources
- Retrieval debugging:
  - File recall analysis: which relevant files did the agent find?
  - TTFR (Time to First Relevant file): how long before the agent found useful code?
  - Search query quality: did the agent search for the right terms?
- Building feedback loops:
  - Transcript analysis at scale (behavioral metrics across hundreds of runs)
  - Anomaly detection: all-zero batches, all-perfect suites, high-variance tasks
  - Staging-to-production quality gates

---

### Chapter 14: Deploying Reliable Coding Agents

**~22 pages**

The operational reality of running coding agents at enterprise scale, including security and governance.

- The deployment spectrum:
  - Interactive: human-in-the-loop, IDE integration
  - Background: event-driven, CI/CD triggered, webhook-initiated
  - Autonomous: always-on, self-directed within guardrails
- Background agent architectures:
  - Webhook ingress, queue-based processing, durable execution
  - Blueprint-driven workflows: declarative specifications for agent tasks
- Cloud sandbox orchestration:
  - Container management at scale (125 concurrent sandboxes)
  - Memory and resource caps
  - Orphaned sandbox cleanup
- Cost management:
  - Model selection by task complexity
  - Per-task cost tracking and budget caps
  - Multi-account token management
  - Empirical data: baseline $0.73/task vs. code-intelligence-augmented $0.51/task (−30%)
- Security and governance:
  - Agent-introduced vulnerabilities: agents optimize for task completion, not security
  - Credential exposure and data residency for code search indexes
  - Sandboxing: agents must not escape their execution environment
  - Approval workflows: which agent-produced changes require human review?
  - Audit trail requirements: SOC 2, GDPR compliance
  - Quality gates at every level (pre-flight, runtime, post-run, batch)
  - Rollback and recovery
- Enterprise readiness checklist:
  - SSO-integrated auth for code intelligence tools
  - Multi-tenant isolation
  - Data residency compliance
  - Kill switches and budget caps

---

### Chapter 15: The Future of AI-Native Software Development

**~18 pages**

Where this field is heading and what engineers should prepare for.

- From task completion to continuous codebase evolution:
  - Agents as persistent collaborators, not one-shot tools
  - Continuous refactoring, dependency monitoring, security scanning
  - Documentation that stays in sync with code changes
- The shifting role of the software engineer:
  - From code writer to system architect and agent orchestrator
  - Designing codebases for agent comprehension
  - Institutional knowledge capture: agents as organizational memory
- What needs to be solved:
  - The retrieval-outcome disconnect: why doesn't better retrieval always improve outcomes?
  - Agent non-determinism: making agent behavior more predictable
  - Multi-agent coordination: specialized agents collaborating on complex tasks
  - Cost economics: when does agent infrastructure pay for itself?
- Protocol evolution: MCP governance maturation, multi-agent communication, competing standards
- A practical closing: start with measurement
  - Build an evaluation pipeline for your own codebase before scaling agents
  - Instrument your agents before optimizing them
  - Share results — the field needs more empirical data, not more hype

---

## Page Budget

| Section | Chapters | Pages |
|---|---|---|
| Part I: The Coding Agent Problem | 1–3 | 65 |
| Part II: Understanding Large Codebases | 4–6 | 66 |
| Part III: Context Retrieval Systems | 7–9 | 72 |
| Part IV: Evaluation | 10–12 | 66 |
| Part V: Production Systems | 13–15 | 62 |
| Front matter, index | — | 15 |
| **Total** | **15 chapters** | **~345 pages** |
