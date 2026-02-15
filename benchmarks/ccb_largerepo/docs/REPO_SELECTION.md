# Repository Selection Rationale

## Overview

The `ccb_largerepo` benchmark selects repositories across two tiers: **Tier A** (general systems infrastructure) and **Tier B** (capital markets / financial services aligned). This document explains why each repository was chosen and how the selection criteria were applied.

## Selection Criteria

Repositories were evaluated on five dimensions:

1. **LOC Scale** — Must exceed 350K lines of code to exercise large-codebase navigation
2. **Language Coverage** — Collective set must cover Go, Java, Python, C, C++, Rust, TypeScript
3. **Domain Diversity** — Mix of systems infrastructure, web frameworks, financial services, and data processing
4. **Architectural Complexity** — Deep module hierarchies, cross-cutting concerns, or multi-language boundaries
5. **Capital Markets Alignment** — At least half of expansion repos serve financial services use cases (pricing, risk, messaging, stream processing)

## Tier A: Systems Infrastructure

These repositories represent foundational software systems with broad enterprise adoption.

| Repository | Language | LOC | Tag | Selection Rationale |
|---|---|---|---|---|
| **kubernetes/kubernetes** | Go | ~3.5M | v1.30.0 | Industry-standard orchestration platform. Deep scheduler/controller architecture with 30+ packages. Already used in original 4 tasks. |
| **torvalds/linux** | C | ~30M | v6.19 | Largest actively-maintained codebase. Tests extreme-scale navigation. Subsystem boundaries (fs/, net/, drivers/) create natural architectural analysis tasks. |
| **rust-lang/rust** | Rust | ~2M | 1.93.1 | Complex compiler architecture spanning parsing, type checking, MIR, codegen. Deep trait resolution and lifetime inference chains. |
| **postgres/postgres** | C | ~1.5M | REL_18_2 | 25+ year legacy codebase. Query execution pipeline (parse → analyze → rewrite → plan → execute) is a canonical architectural tracing target. Authentication chain exercises security analysis. |
| **django/django** | Python | ~350K | 5.2 | Most popular Python web framework. ORM query compilation pipeline, middleware chain, and CSRF handling provide well-documented architectural and security tasks. |
| **microsoft/vscode** | TypeScript | ~1.5M | 1.91.1 | Large TypeScript monorepo. Extension API, language server protocol, and diagnostics pipeline. Already used in original 4 tasks. |
| **servo/servo** | Rust | ~1.2M | (pinned) | Browser engine with parallel layout. Already used in original 4 tasks. |
| **NVIDIA/TensorRT-LLM** | Python/C++ | ~800K | (pinned) | Cross-language boundary (Python ↔ C++). Already used in original 4 tasks. |

### Tier A Notes

- Kubernetes, VS Code, Servo, and TensorRT-LLM carry forward from the original 4 tasks.
- Linux is included despite its extreme size (30M LOC) specifically to test how agents handle codebases that cannot be fully indexed or searched.
- Django at 350K LOC is the smallest Tier A repo but compensates with deep Python metaprogramming (descriptors, metaclasses) that challenges code navigation.

## Tier B: Capital Markets Aligned

These repositories serve financial services workloads — messaging, stream processing, pricing, risk analytics, and data governance.

| Repository | Language | LOC | Tag | Selection Rationale |
|---|---|---|---|---|
| **apache/camel** | Java | ~2.4M | camel-4.18.0 | Enterprise Integration Patterns. 300+ connectors, deep Component→Endpoint→Consumer→Processor→Producer hierarchy. Used in FIX protocol and market data routing. |
| **apache/flink** | Java | ~1.3M | release-2.2.0 | Stream processing backbone for real-time risk and pricing. Checkpoint coordination, complex operator chaining, 5+ level abstract class hierarchies. Already indexed in Sourcegraph. |
| **apache/kafka** | Java/Scala | ~1.1M | 4.1.1 | Event streaming backbone for trade capture and market data distribution. KRaft consensus (replacing ZooKeeper), SASL authentication, 500+ config settings. |
| **OpenGamma/Strata** | Java | ~521K | v2.12.65 | Open-source pricing and risk analytics. Deep financial domain models (SwapTrade, CreditDefaultSwap), Joda-Beans code generation creates 100+ auto-generated files that refactoring must respect. |
| **lballabio/QuantLib** | C++ | ~437K | v1.41 | 25-year legacy quantitative finance library. Template metaprogramming, pricing engine chains (Instrument→PricingEngine→TermStructure→StochasticProcess), SWIG cross-language bindings. |
| **hazelcast/hazelcast** | Java | ~1.6M | v5.6.0 | Distributed caching and compute for low-latency trading. Split-brain handling, partition migration, 7% of codebase is XML Schema config. |
| **finos/legend-engine** | Java | ~1M+ | legend-engine-4.120.1 | Goldman Sachs open-source data governance. Custom Pure language compiler, multi-module Maven (200+ modules), model-driven architecture. |

### Capital Markets Justification

These repos were chosen because they represent the actual technology stack used in capital markets:

- **Trade lifecycle**: Kafka (capture) → Flink (enrichment) → Strata/QuantLib (pricing) → Legend (governance)
- **Infrastructure**: Camel (integration routing), Hazelcast (distributed caching), Kafka (messaging)
- **Analytics**: Strata (rates/credit), QuantLib (derivatives), Legend Engine (data modeling)

This alignment means the benchmark tasks exercise the same code navigation patterns that a financial services developer or agent would encounter in practice.

## Language Distribution

| Language | Repos | Tasks (planned) |
|---|---|---|
| Java | 6 (Camel, Flink, Kafka, Strata, Hazelcast, Legend) | ~12 |
| Go | 1 (Kubernetes) | ~4 |
| C | 2 (Linux, PostgreSQL) | ~4 |
| C++ | 1 (QuantLib) | ~3 |
| Python | 1 (Django) | ~3 |
| Rust | 2 (rust-lang/rust, Servo) | ~3 |
| TypeScript | 1 (VS Code) | ~1 |

Java dominance reflects capital markets reality — most enterprise financial systems are built in Java.

## Sourcegraph Indexing Status

All repos require Sourcegraph indexing for MCP tool access. Status tracked in `configs/sg_indexing_list.json` under the `largerepo_expansion` section.

| Status | Count | Repos |
|---|---|---|
| Already indexed | 1 | Flink |
| Pending mirror | 10 | Linux, Rust, PostgreSQL, Django, Camel, Hazelcast, Kafka, Legend, Strata, QuantLib |
| Original 4 (indexed) | 4 | Kubernetes, VS Code, Servo, TensorRT-LLM |

Repos are mirrored to the `sg-benchmarks` GitHub org with pinned commits, then indexed by Sourcegraph. See the `_indexed` field in `sg_indexing_list.json` for current status.

## Commit Pinning

All repos are pinned to specific release tags to ensure reproducibility:

- Tags are resolved to full commit SHAs via `git ls-remote`
- Dockerfiles clone at the pinned commit using `--filter=blob:none --no-checkout` + `git checkout {sha}`
- Ground truth is validated against the pinned version, not HEAD

This prevents benchmark drift — the same task always runs against the same code.

## See Also

- [LOCOBENCH_ADAPTATION.md](LOCOBENCH_ADAPTATION.md) — How LoCoBench methodology was adapted
- [../../configs/sg_indexing_list.json](../../configs/sg_indexing_list.json) — Full repo + commit pinning list
- [../MANIFEST.json](../MANIFEST.json) — Current task registry
