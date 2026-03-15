# Reliable AI Coding Agents

**Context Retrieval, Large Codebases, and Evaluation**

*Proposal for O'Reilly Media*
*Stephanie Jarmak — March 2026*

---

## 1. Working Title and Subtitle

**Reliable AI Coding Agents**
Context Retrieval, Large Codebases, and Evaluation

---

## 2. Book Summary

### Problem

AI coding agents promise to automate software development tasks, but most fail when confronted with real production codebases. The root cause is not model capability. It is context access. Agents cannot reliably find and understand the code they need to work with.

Enterprise codebases contain millions of lines of code spread across dozens of repositories, written in multiple languages, maintained by hundreds of contributors. When a coding agent encounters this kind of environment, it faces problems that prompt engineering and model upgrades do not solve: path explosion in monorepos, cross-repository blindness, dependency chains that span organizational boundaries, and context windows too small to hold the relevant code. These are infrastructure problems, not intelligence problems.

The result is predictable. Agents burn their timeouts navigating large codebases without producing output. They find two of seven affected files in a refactoring task. They make 96 tool calls over 84 minutes to accomplish what targeted code search achieves in five calls and four minutes. Or they complete in under two seconds because they never actually installed and ran. These are not edge cases. They are the dominant failure modes observed across 1,281 scored agent runs in the CodeScaleBench evaluation framework.

### Gap

Existing books on large language models focus on prompt engineering, general LLM application development, or AI engineering pipelines. None address the specific architectural challenges of building AI systems that interact with large software repositories. The problems of repository indexing, semantic code retrieval, dependency modeling, context construction, and agent evaluation form a coherent engineering discipline that has no reference text.

This gap is becoming urgent. Gartner projects 40% of enterprise applications will embed AI agents by end of 2026. Every major software vendor has shipped or announced agentic coding features. Engineering teams are deploying these systems without understanding why they fail or how to make them reliable. The field needs a book that treats this as a systems engineering problem, not a tutorial on a specific framework.

### Solution

This book introduces the architectural patterns and evaluation techniques required to build reliable AI coding agents for large codebases. It covers:

- **How agents work and why they fail** — the architecture of coding agents, the failure modes that emerge at scale, and why context access is the primary bottleneck
- **Understanding large codebases** — repository structure, dependency graphs, code indexing strategies, and semantic search systems that make codebases machine-navigable
- **Context retrieval systems** — how to construct effective context for agents, reason across multiple repositories, and design tool interfaces and protocols (including MCP, CLI, SDK, and API approaches)
- **Evaluation and reliability** — benchmarking methodologies, task mining from real repositories, and systematic approaches to debugging agent failures
- **Production deployment** — enterprise deployment patterns, security and governance guardrails, and the trajectory of AI-native software development

Every pattern in the book is grounded in empirical data from CodeScaleBench, a benchmark of 381 software engineering tasks across 40+ open-source repositories (Kubernetes, Django, Linux kernel, VSCode, PyTorch, Grafana) and 9 programming languages. The book uses this data to show where specific approaches work, where they fail, and why — but it teaches systems and patterns, not tool-specific configurations.

---

## 3. Target Audience

**Primary audience:**
- Platform engineers building internal coding assistants or developer productivity systems
- ML engineers developing AI developer tools that interact with code repositories
- Staff+ engineers responsible for evaluating, deploying, or governing AI coding agents

**Secondary audience:**
- Researchers studying AI code generation and retrieval-augmented generation for code
- Engineering leaders evaluating AI developer tooling investments and ROI

**Prerequisites:**
- Familiarity with software engineering workflows (version control, CI/CD, code review)
- Basic knowledge of how large language models work (tokens, context windows, tool use)
- No prior experience with coding agents, MCP, or code search systems required

---

## 4. Table of Contents

**Part I — The Coding Agent Problem**

1. The Rise of AI Coding Agents
2. Why Coding Agents Fail in Real Codebases
3. The Context Window Problem

**Part II — Understanding Large Codebases**

4. Repository Structure and Dependency Graphs
5. Indexing Code for Machine Understanding
6. Semantic Code Search

**Part III — Context Retrieval Systems**

7. Constructing Context for AI Coding Agents
8. Multi-Repository Reasoning
9. Tool Interfaces and Agent Architectures

**Part IV — Evaluation**

10. Why Existing Benchmarks Fail
11. Mining Tasks from Software Repositories
12. Designing Realistic Agent Evaluations

**Part V — Production Systems**

13. Debugging Agent Failures
14. Deploying Reliable Coding Agents
15. The Future of AI-Native Software Development

*(See accompanying CHAPTER_OUTLINE.md for the detailed chapter breakdown.)*

---

## 5. Competitive Titles

**AI Engineering** by Chip Huyen (O'Reilly, 2025)
The closest existing book. Covers LLM application pipelines, evaluation, and deployment patterns. Does not address code-specific retrieval, repository indexing, or the architectural challenges unique to software engineering agents. *Reliable AI Coding Agents* picks up where *AI Engineering* leaves off for the specific domain of code.

**Hands-On Large Language Models** by Jay Alammar and Maarten Grootendorst (O'Reilly, 2024)
Practical guide to working with LLMs. Covers embeddings, semantic search, and generation. Does not address the domain-specific challenges of code repositories: dependency graphs, cross-repository navigation, multi-language indexing, or deterministic verification of agent output.

**Building Agentic AI Systems** by Manikandan Parasuraman (O'Reilly, 2025)
Generic agent architecture patterns (planning, tool use, memory). No code-specific patterns, no enterprise codebase scale, no retrieval infrastructure for software repositories.

**AI-Assisted Programming** by Tom Taulli (O'Reilly, 2024)
Individual developer productivity with Copilot-style tools. Single-developer focus. Does not address multi-repository reasoning, organizational-scale code intelligence, or evaluation methodologies.

**Positioning:**
These books explain LLM pipelines and AI applications but do not address the architectural challenges of building AI systems that interact with large software repositories. *Reliable AI Coding Agents* fills that gap. It treats coding agent reliability as a systems engineering discipline — the equivalent of what *Designing Data-Intensive Applications* did for data systems or *Site Reliability Engineering* did for operations.

---

## 6. Author Bio

Stephanie Jarmak works on code intelligence and developer tools at Sourcegraph. She designed and built CodeScaleBench, the largest public benchmark for evaluating AI coding agents on enterprise-scale software engineering tasks: 381 tasks across 40+ open-source repositories, 9 programming languages, and 1,281 scored agent runs with full audit trails.

**Practitioner credibility:**
- Built the complete benchmark pipeline — task design, containerized execution (Harbor), deterministic verification, information retrieval evaluation, and statistical analysis — across approximately 1,000 agent-assisted coding sessions
- Hands-on experience with multiple agent frameworks (Claude Code, OpenHands, custom harnesses) on identical enterprise tasks, providing direct comparative data on where different approaches succeed and fail
- Designed the information parity experimental methodology that isolates code intelligence tool effectiveness from information advantage
- Operational experience with large-scale agent evaluation infrastructure: cloud sandbox orchestration (125 concurrent containers), multi-account token management, and staging-to-production promotion pipelines with quality gates
- Discovered and documented novel agent failure modes through systematic experimentation: agents circumventing experimental controls via git history, tool mandate spirals, silent integration failures, and infrastructure failures masquerading as agent failures

**Domain expertise:**
- Deep understanding of code search, indexing, and navigation systems from building with and evaluating Sourcegraph's code intelligence platform
- Practical experience with the MCP ecosystem, CLI tools, and SDK integration — including the failure modes that arise when these are deployed across different agent frameworks
- Published technical report, blog post, and interactive results browser with full agent transcripts and reproducible evaluation methodology

---

## 7. Marketing Plan

**Existing audience and assets:**
- CodeScaleBench benchmark and results browser are publicly available, already generating visibility in the developer tools and AI agent communities
- Published blog post on benchmark findings with detailed engineering narrative
- Technical report documenting full methodology and results

**Conference and event alignment:**
- O'Reilly AI Codecon (topic alignment with agentic software engineering track)
- KubeCon, PyCon, GopherCon (enterprise developer audience; benchmark uses these ecosystems)
- AI Engineer Summit (practitioner and researcher crossover audience)

**Content marketing:**
- Technical blog series extracting key findings from each chapter (building on existing CodeScaleBench writing)
- Companion GitHub repository with runnable examples, benchmark task samples, and evaluation scripts — continuously updated
- Sourcegraph's developer community and enterprise customer base provide an established distribution channel

**Ongoing engagement:**
- The benchmark is a living project. New tasks, new agent evaluations, and updated findings provide a continuous stream of relevant content tied to the book's topics
- The companion repository serves as both a learning resource and a promotion vehicle

---

## 8. Sample Chapter

**Chapter 2: Why Coding Agents Fail in Real Codebases** accompanies this proposal as the sample chapter.

It opens with the Kubernetes monorepo case study: an agent burns its entire 6,000-second timeout navigating a 1.4-million-line codebase and produces nothing. The same agent, given code search tools, completes the task in 89 seconds. The chapter develops the systematic failure taxonomy observed across 1,281 scored agent runs, explains why each failure mode is an infrastructure problem rather than an intelligence problem, and connects each to the architectural solutions in Parts II–V.

This chapter was chosen because it is the book's highest-impact chapter, it draws directly from the author's benchmark work, and it demonstrates the ability to explain complex systems clearly — the quality editors evaluate most carefully.

*(See accompanying SAMPLE_CHAPTER.md.)*

---

## 9. Content Mapping from Existing Writing

Several chapters draw directly from published work and existing expertise:

**Published articles → chapters:**
- "Rethinking Coding Agent Benchmarks" (Medium) → Chapter 10: Why Existing Benchmarks Fail — expanded to cover flaws in current benchmarks, unrealistic evaluation tasks, single-file vs. repository-scale reasoning, and cost/latency tradeoffs
- "I Couldn't Find a Good Enough Benchmark for Large-Scale Software Development" (Medium) → Chapter 11: Mining Tasks from Software Repositories — expanded methodology behind CodeScaleBench task extraction, ground truth generation, and difficulty classification

**Benchmark work → chapters:**
- CodeScaleBench technical report → Chapters 10–12 (evaluation methodology, task mining, evaluation design)
- CodeScaleBench blog post → Chapters 2, 7, 8 (failure modes, context construction, multi-repo reasoning)
- Hybrid retrieval pipeline experiments → Chapter 7 (context construction)
- Curator agent and ground truth system → Chapter 11 (task mining)

**Domain expertise → chapters:**
- Sourcegraph code intelligence systems → Chapters 5, 6, 8 (indexing, semantic search, multi-repo)
- MCP/CLI/SDK integration experience → Chapter 9 (tool interfaces)
- Agent evaluation infrastructure → Chapters 12, 13, 14 (evaluation design, debugging, deployment)
