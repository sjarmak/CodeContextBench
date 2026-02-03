# CodeContextBench Evaluation Report

Generated: 2026-02-03T13:17:58.019434+00:00
Report ID: eval_20260203_131758

## Run Inventory

| Benchmark      | Config             | Model                              | MCP Mode         | Tasks | Timestamp           |
| -------------- | ------------------ | ---------------------------------- | ---------------- | ----- | ------------------- |
| crossrepo_opus | baseline           | anthropic/claude-opus-4-5-20251101 | none             | 5     | 2026-02-02 20-47-38 |
| crossrepo_opus | sourcegraph_full | anthropic/claude-opus-4-5-20251101 | sourcegraph_full | 5     | 2026-02-02 20-47-40 |
| locobench      | baseline           | anthropic/claude-opus-4-5-20251101 | none             | 25    | 2026-02-03 08-38-27 |
| locobench      | sourcegraph_full | anthropic/claude-opus-4-5-20251101 | sourcegraph_full | 25    | 2026-02-03 11-17-00 |
| swebenchpro    | baseline           | anthropic/claude-opus-4-5-20251101 | none             | 36    | 2026-02-03 03-43-17 |
| swebenchpro    | sourcegraph_full | anthropic/claude-opus-4-5-20251101 | sourcegraph_full | 36    | 2026-02-03 04-18-51 |

## Aggregate Performance

| Config             | Mean Reward | Pass Rate | Tasks |
| ------------------ | ----------- | --------- | ----- |
| baseline           | 0.548       | 0.742     | 66    |
| sourcegraph_full | 0.553       | 0.742     | 66    |

## Per-Benchmark Breakdown (Mean Reward)

| Benchmark      | baseline | sourcegraph_full |
| -------------- | -------- | ------------------ |
| crossrepo_opus | 0.200    | 0.200              |
| locobench      | 0.487    | 0.501              |
| swebenchpro    | 0.639    | 0.639              |

## Efficiency

| Benchmark      | Config             | Mean Input Tokens | Mean Output Tokens | Mean Cache Tokens | Mean Wall Clock (s) | Mean Cost (USD) |
| -------------- | ------------------ | ----------------- | ------------------ | ----------------- | ------------------- | --------------- |
| crossrepo_opus | baseline           | 7,928,285         | 2,719              | 7,944,842         | 343.7               | $267.8006       |
| crossrepo_opus | sourcegraph_full | 7,874,241         | 800                | 7,874,239         | 307.7               | $265.8156       |
| locobench      | baseline           | 3,932,586         | 4,335              | 4,602,471         | 393.4               | $133.3883       |
| locobench      | sourcegraph_full | 5,382,048         | 659                | 5,382,044         | 342.9               | $181.6935       |
| swebenchpro    | baseline           | 5,485,778         | 672                | 5,485,495         | 678.3               | $185.1902       |
| swebenchpro    | sourcegraph_full | 6,080,009         | 597                | 6,080,001         | 766.2               | $205.2450       |

## Tool Utilization

| Benchmark      | Config             | Mean Total Calls | Mean MCP Calls | Mean Local Calls | Mean MCP Ratio |
| -------------- | ------------------ | ---------------- | -------------- | ---------------- | -------------- |
| crossrepo_opus | baseline           | 88.8             | 0.0            | 88.8             | 0.000          |
| crossrepo_opus | sourcegraph_full | 75.8             | 8.4            | 67.4             | 0.236          |
| locobench      | baseline           | 56.8             | 0.0            | 56.8             | 0.000          |
| locobench      | sourcegraph_full | 47.2             | 12.6           | 34.6             | 0.273          |
| swebenchpro    | baseline           | 53.8             | 0.0            | 53.8             | 0.000          |
| swebenchpro    | sourcegraph_full | 50.7             | 1.9            | 48.8             | 0.044          |

## Search Patterns

| Benchmark      | Config             | Mean Keyword Searches | Mean NLS Searches | Mean Deep Searches | Mean DS/KW Ratio |
| -------------- | ------------------ | --------------------- | ----------------- | ------------------ | ---------------- |
| crossrepo_opus | baseline           | -                     | -                 | -                  | -                |
| crossrepo_opus | sourcegraph_full | 12.0                  | 0.0               | 0.0                | 0.000            |
| locobench      | baseline           | -                     | -                 | -                  | -                |
| locobench      | sourcegraph_full | 9.8                   | 2.0               | 0.1                | 0.005            |
| swebenchpro    | baseline           | -                     | -                 | -                  | -                |
| swebenchpro    | sourcegraph_full | 4.2                   | 0.1               | 0.0                | 0.000            |

## Code Changes

| Benchmark      | Config             | Mean Files Modified | Mean Lines Added | Mean Lines Removed |
| -------------- | ------------------ | ------------------- | ---------------- | ------------------ |
| crossrepo_opus | baseline           | 9.0                 | 240.8            | 48.0               |
| crossrepo_opus | sourcegraph_full | 3.8                 | 165.0            | 17.8               |
| locobench      | baseline           | 3.7                 | 1064.7           | 36.8               |
| locobench      | sourcegraph_full | 2.9                 | 949.3            | 34.2               |
| swebenchpro    | baseline           | 4.0                 | 158.1            | 82.5               |
| swebenchpro    | sourcegraph_full | 3.7                 | 144.4            | 70.7               |

## Cache Efficiency

| Benchmark      | Config             | Mean Cache Hit Rate | Mean Input/Output Ratio | Mean Cost (USD) |
| -------------- | ------------------ | ------------------- | ----------------------- | --------------- |
| crossrepo_opus | baseline           | 0.799               | 7988.4                  | $267.8006       |
| crossrepo_opus | sourcegraph_full | -                   | 12345.5                 | $265.8156       |
| locobench      | baseline           | 0.961               | 6843.0                  | $133.3883       |
| locobench      | sourcegraph_full | -                   | 8332.1                  | $181.6935       |
| swebenchpro    | baseline           | -                   | 7204.5                  | $185.1902       |
| swebenchpro    | sourcegraph_full | -                   | 9195.2                  | $205.2450       |

## SWE-Bench Pro Partial Scores

| Config             | Mean Partial Score | Tasks |
| ------------------ | ------------------ | ----- |
| baseline           | 0.742              | 36    |
| sourcegraph_full | 0.743              | 36    |

## Performance by SDLC Phase

| SDLC Phase                   | Tasks | baseline | sourcegraph_full |
| ---------------------------- | ----- | -------- | ------------------ |
| Architecture & Design        | 10    | 0.451    | 0.452              |
| Implementation (bug fix)     | 40    | 0.608    | 0.608              |
| Implementation (refactoring) | 15    | 0.422    | 0.445              |
| Testing & QA                 | 1     | 1.000    | 1.000              |

## Performance by Language

| Language   | Tasks | baseline | sourcegraph_full |
| ---------- | ----- | -------- | ------------------ |
| c          | 7     | 0.497    | 0.514              |
| cpp        | 1     | 0.427    | 0.435              |
| csharp     | 3     | 0.478    | 0.509              |
| go         | 18    | 0.667    | 0.667              |
| javascript | 3     | 0.667    | 0.667              |
| python     | 19    | 0.526    | 0.531              |
| rust       | 7     | 0.477    | 0.476              |
| typescript | 8     | 0.437    | 0.443              |

## Performance by MCP Benefit Score

| MCP Benefit Score   | Tasks | baseline | sourcegraph_full |
| ------------------- | ----- | -------- | ------------------ |
| 0.0-0.4 (low)       | 0     | -        | -                  |
| 0.4-0.6 (medium)    | 9     | 0.889    | 0.889              |
| 0.6-0.8 (high)      | 28    | 0.571    | 0.571              |
| 0.8-1.0 (very high) | 29    | 0.420    | 0.432              |

