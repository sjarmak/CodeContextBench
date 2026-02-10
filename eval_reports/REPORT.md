# CodeContextBench Evaluation Report

Generated: 2026-02-10T12:22:16.571469+00:00
Report ID: eval_20260210_122216

## Run Inventory

| Benchmark       | Config                  | Model                              | MCP Mode         | Tasks | Timestamp           |
| --------------- | ----------------------- | ---------------------------------- | ---------------- | ----- | ------------------- |
| ccb_crossrepo   | baseline                | anthropic/claude-opus-4-6          | none             | 5     | 2026-02-07 17-13-08 |
| ccb_crossrepo   | sourcegraph_base        | anthropic/claude-opus-4-6          | sourcegraph_base | 5     | 2026-02-07 17-37-04 |
| ccb_crossrepo   | sourcegraph_full        | anthropic/claude-opus-4-6          | sourcegraph_full | 5     | 2026-02-07 17-51-36 |
| ccb_dibench     | baseline                | anthropic/claude-opus-4-5-20251101 | none             | 8     | 2026-02-03 16-43-09 |
| ccb_dibench     | sourcegraph_base        | anthropic/claude-opus-4-6          | sourcegraph_base | 8     | 2026-02-09 18-19-42 |
| ccb_dibench     | sourcegraph_full        | anthropic/claude-opus-4-6          | sourcegraph_full | 8     | 2026-02-09 18-26-45 |
| ccb_k8sdocs     | baseline                | anthropic/claude-opus-4-5-20251101 | none             | 5     | 2026-02-05 22-53-43 |
| ccb_k8sdocs     | sourcegraph_base        | anthropic/claude-opus-4-5-20251101 | sourcegraph_base | 5     | 2026-02-05 23-58-36 |
| ccb_k8sdocs     | sourcegraph_full        | anthropic/claude-opus-4-6          | sourcegraph_full | 5     | 2026-02-08 14-41-27 |
| ccb_largerepo   | baseline                | anthropic/claude-opus-4-5-20251101 | none             | 4     | 2026-02-05 22-53-51 |
| ccb_largerepo   | sourcegraph_base        | anthropic/claude-opus-4-5-20251101 | sourcegraph_base | 4     | 2026-02-06 00-48-34 |
| ccb_largerepo   | sourcegraph_base_latest | anthropic/claude-opus-4-6          | sourcegraph_base | 1     | 2026-02-10 11-04-55 |
| ccb_largerepo   | sourcegraph_full        | anthropic/claude-opus-4-6          | sourcegraph_full | 4     | 2026-02-08 18-45-22 |
| ccb_locobench   | baseline                | anthropic/claude-opus-4-5-20251101 | none             | 25    | 2026-02-03 08-38-27 |
| ccb_locobench   | sourcegraph_base        | anthropic/claude-opus-4-5-20251101 | sourcegraph_base | 25    | 2026-02-03 18-36-37 |
| ccb_locobench   | sourcegraph_full        | anthropic/claude-opus-4-6          | sourcegraph_full | 25    | 2026-02-07 22-05-15 |
| ccb_pytorch     | baseline                | anthropic/claude-opus-4-5-20251101 | none             | 9     | 2026-02-05 23-37-37 |
| ccb_pytorch     | sourcegraph_base        | anthropic/claude-opus-4-5-20251101 | sourcegraph_base | 9     | 2026-02-06 00-16-13 |
| ccb_pytorch     | sourcegraph_full        | anthropic/claude-opus-4-6          | sourcegraph_full | 12    | 2026-02-08 14-51-56 |
| ccb_repoqa      | baseline                | anthropic/claude-opus-4-5-20251101 | none             | 10    | 2026-02-03 16-35-20 |
| ccb_repoqa      | sourcegraph_base        | anthropic/claude-opus-4-5-20251101 | sourcegraph_base | 10    | 2026-02-03 16-58-00 |
| ccb_repoqa      | sourcegraph_full        | anthropic/claude-opus-4-6          | sourcegraph_full | 10    | 2026-02-08 13-25-29 |
| ccb_swebenchpro | baseline                | anthropic/claude-opus-4-5-20251101 | none             | 36    | 2026-02-02 12-25-24 |
| ccb_swebenchpro | sourcegraph_base        | anthropic/claude-opus-4-5-20251101 | sourcegraph_base | 36    | 2026-02-05 03-05-37 |
| ccb_swebenchpro | sourcegraph_full        | anthropic/claude-opus-4-6          | sourcegraph_full | 36    | 2026-02-08 00-20-27 |
| ccb_sweperf     | baseline                | anthropic/claude-opus-4-5-20251101 | none             | 3     | 2026-02-05 01-04-11 |
| ccb_sweperf     | sourcegraph_base        | anthropic/claude-opus-4-5-20251101 | sourcegraph_base | 3     | 2026-02-05 01-21-42 |
| ccb_sweperf     | sourcegraph_full        | anthropic/claude-opus-4-6          | sourcegraph_full | 3     | 2026-02-09 00-08-48 |
| ccb_tac         | baseline                | anthropic/claude-opus-4-6          | none             | 8     | 2026-02-07 16-38-41 |
| ccb_tac         | sourcegraph_base        | anthropic/claude-opus-4-6          | sourcegraph_base | 8     | 2026-02-07 17-19-56 |
| ccb_tac         | sourcegraph_full        | anthropic/claude-opus-4-6          | sourcegraph_full | 8     | 2026-02-07 17-52-41 |
| codereview      | baseline                | anthropic/claude-opus-4-5-20251101 | none             | 3     | 2026-02-06 15-53-56 |
| codereview      | sourcegraph_base        | anthropic/claude-opus-4-6          | sourcegraph_base | 3     | 2026-02-07 16-30-22 |
| codereview      | sourcegraph_full        | anthropic/claude-opus-4-6          | sourcegraph_full | 3     | 2026-02-08 21-07-39 |
| dependeval      | baseline                | anthropic/claude-opus-4-6          | none             | 32    | 2026-02-09 00-12-09 |
| dependeval      | sourcegraph_base        | anthropic/claude-opus-4-6          | sourcegraph_base | 32    | 2026-02-09 00-34-42 |
| dependeval      | sourcegraph_full        | anthropic/claude-opus-4-6          | sourcegraph_full | 32    | 2026-02-09 00-58-43 |
| linuxflbench    | baseline                | anthropic/claude-opus-4-5-20251101 | none             | 5     | 2026-02-06 16-28-49 |
| linuxflbench    | sourcegraph_base        | anthropic/claude-opus-4-6          | sourcegraph_base | 5     | 2026-02-07 18-20-16 |
| linuxflbench    | sourcegraph_full        | anthropic/claude-opus-4-6          | sourcegraph_full | 5     | 2026-02-08 21-35-42 |

## Aggregate Performance

| Config                  | Mean Reward | Pass Rate | Tasks |
| ----------------------- | ----------- | --------- | ----- |
| baseline                | 0.542       | 0.719     | 153   |
| sourcegraph_base        | 0.496       | 0.660     | 153   |
| sourcegraph_base_latest | 0.700       | 1.000     | 1     |
| sourcegraph_full        | 0.645       | 0.814     | 156   |

## Per-Benchmark Breakdown (Mean Reward)

| Benchmark       | baseline | sourcegraph_base | sourcegraph_base_latest | sourcegraph_full |
| --------------- | -------- | ---------------- | ----------------------- | ---------------- |
| ccb_crossrepo   | 0.571    | 0.587            | -                       | 0.387            |
| ccb_dibench     | 0.500    | 0.500            | -                       | 0.500            |
| ccb_k8sdocs     | 0.920    | 0.920            | -                       | 0.920            |
| ccb_largerepo   | 0.250    | 0.250            | 0.700                   | 0.425            |
| ccb_locobench   | 0.449    | 0.363            | -                       | 0.499            |
| ccb_pytorch     | 0.111    | 0.108            | -                       | 0.265            |
| ccb_repoqa      | 1.000    | 1.000            | -                       | 1.000            |
| ccb_swebenchpro | 0.417    | 0.333            | -                       | 0.769            |
| ccb_sweperf     | 0.591    | 0.032            | -                       | 0.367            |
| ccb_tac         | 0.492    | 0.365            | -                       | 0.544            |
| codereview      | 0.933    | 0.980            | -                       | 1.000            |
| dependeval      | 0.636    | 0.665            | -                       | 0.720            |
| linuxflbench    | 0.860    | 0.820            | -                       | 0.880            |

## Efficiency

| Benchmark       | Config                  | Mean Input Tokens | Mean Output Tokens | Mean Cache Tokens | Mean Wall Clock (s) | Mean Cost (USD) |
| --------------- | ----------------------- | ----------------- | ------------------ | ----------------- | ------------------- | --------------- |
| ccb_crossrepo   | baseline                | 1,725             | 17,789             | 3,270,335         | 584.5               | $2.6890         |
| ccb_crossrepo   | sourcegraph_base        | 104               | 14,554             | 3,414,798         | 603.7               | $2.6383         |
| ccb_crossrepo   | sourcegraph_full        | 57                | 18,011             | 4,102,584         | 620.1               | $3.9049         |
| ccb_dibench     | baseline                | 35                | 2,679              | 861,473           | 275.1               | $0.7194         |
| ccb_dibench     | sourcegraph_base        | 26                | 4,372              | 1,344,485         | 222.1               | $1.1172         |
| ccb_dibench     | sourcegraph_full        | 22                | 3,589              | 1,066,031         | 170.7               | $0.9261         |
| ccb_k8sdocs     | baseline                | 2                 | 4,858              | 862,883           | 1426.0              | $0.9183         |
| ccb_k8sdocs     | sourcegraph_base        | 2                 | 3,653              | 698,953           | 650.6               | $0.7171         |
| ccb_k8sdocs     | sourcegraph_full        | 12                | 4,049              | 569,531           | 224.6               | $0.6359         |
| ccb_largerepo   | baseline                | 85                | 23,860             | 7,356,855         | 2903.4              | $5.4184         |
| ccb_largerepo   | sourcegraph_base        | 2                 | 19,626             | 7,152,633         | 1187.3              | $4.7376         |
| ccb_largerepo   | sourcegraph_base_latest | 7,138,759         | 866                | 7,138,652         | 4213.1              | $240.9961       |
| ccb_largerepo   | sourcegraph_full        | 1,693             | 26,879             | 8,073,793         | 3931.5              | $5.7837         |
| ccb_locobench   | baseline                | 36                | 18,863             | 3,048,692         | 448.7               | $3.8388         |
| ccb_locobench   | sourcegraph_base        | 3                 | 12,735             | 2,273,208         | 300.2               | $1.9733         |
| ccb_locobench   | sourcegraph_full        | 1,132             | 23,906             | 5,179,082         | 1144.2              | $7.9783         |
| ccb_pytorch     | baseline                | 2,155             | 10,431             | 2,935,665         | 1105.5              | $2.1385         |
| ccb_pytorch     | sourcegraph_base        | 1,991             | 9,086              | 3,573,256         | 665.7               | $2.4689         |
| ccb_pytorch     | sourcegraph_full        | 224               | 12,449             | 3,742,737         | 2716.4              | $2.5841         |
| ccb_repoqa      | baseline                | 2                 | 1,283              | 157,722           | 165.1               | $0.1666         |
| ccb_repoqa      | sourcegraph_base        | 2                 | 1,440              | 330,302           | 125.2               | $0.3079         |
| ccb_repoqa      | sourcegraph_full        | 5                 | 1,171              | 198,223           | 306.6               | $0.2427         |
| ccb_swebenchpro | baseline                | 78                | 7,761              | 2,086,241         | 574.9               | $1.5216         |
| ccb_swebenchpro | sourcegraph_base        | 11                | 9,409              | 3,393,766         | 662.6               | $2.3665         |
| ccb_swebenchpro | sourcegraph_full        | 508               | 11,208             | 2,850,388         | 2456.5              | $2.0589         |
| ccb_sweperf     | baseline                | 2                 | 18,896             | 5,061,122         | 795.7               | $3.8225         |
| ccb_sweperf     | sourcegraph_base        | 18                | 32,871             | 8,114,558         | 838.8               | $5.8527         |
| ccb_sweperf     | sourcegraph_full        | 123               | 48,174             | 11,675,461        | 1388.1              | $8.5731         |
| ccb_tac         | baseline                | 53                | 14,563             | 3,253,165         | 1483.0              | $2.5536         |
| ccb_tac         | sourcegraph_base        | 53                | 20,034             | 3,901,509         | 1123.3              | $2.9960         |
| ccb_tac         | sourcegraph_full        | 435               | 16,705             | 3,041,064         | 1087.3              | $2.4761         |
| codereview      | baseline                | 2                 | 4,360              | 622,987           | 185.9               | $0.5640         |
| codereview      | sourcegraph_base        | 588               | 5,952              | 1,047,081         | 286.1               | $0.9551         |
| codereview      | sourcegraph_full        | 21                | 6,338              | 978,964           | 209.0               | $0.8254         |
| dependeval      | baseline                | 49                | 3,059              | 163,919           | 98.5                | $0.2771         |
| dependeval      | sourcegraph_base        | 17                | 3,625              | 318,540           | 122.6               | $0.4008         |
| dependeval      | sourcegraph_full        | 57                | 3,442              | 361,105           | 98.3                | $0.4028         |
| linuxflbench    | baseline                | 41                | 6,408              | 1,324,768         | 568.4               | $1.0380         |
| linuxflbench    | sourcegraph_base        | 87                | 5,270              | 1,108,409         | 1436.5              | $1.1045         |
| linuxflbench    | sourcegraph_full        | 25                | 6,471              | 1,399,965         | 414.4               | $1.3659         |

## Tool Utilization

| Benchmark       | Config                  | Mean Total Calls | Mean MCP Calls | Mean Local Calls | Mean MCP Ratio |
| --------------- | ----------------------- | ---------------- | -------------- | ---------------- | -------------- |
| ccb_crossrepo   | baseline                | 124.0            | 0.0            | 124.0            | 0.000          |
| ccb_crossrepo   | sourcegraph_base        | 84.6             | 2.8            | 81.8             | 0.042          |
| ccb_crossrepo   | sourcegraph_full        | 122.4            | 1.4            | 121.0            | 0.018          |
| ccb_dibench     | baseline                | 25.9             | 0.0            | 25.9             | 0.000          |
| ccb_dibench     | sourcegraph_base        | 34.8             | 14.5           | 20.2             | 0.413          |
| ccb_dibench     | sourcegraph_full        | 29.4             | 12.2           | 17.1             | 0.415          |
| ccb_k8sdocs     | baseline                | 36.4             | 0.0            | 36.4             | 0.000          |
| ccb_k8sdocs     | sourcegraph_base        | 16.6             | 10.6           | 6.0              | 0.628          |
| ccb_k8sdocs     | sourcegraph_full        | 29.6             | 11.0           | 18.6             | 0.479          |
| ccb_largerepo   | baseline                | 113.0            | 0.0            | 113.0            | 0.000          |
| ccb_largerepo   | sourcegraph_base        | 78.2             | 17.8           | 60.5             | 0.232          |
| ccb_largerepo   | sourcegraph_base_latest | 75.0             | 11.0           | 64.0             | 0.147          |
| ccb_largerepo   | sourcegraph_full        | 169.2            | 13.8           | 155.5            | 0.077          |
| ccb_locobench   | baseline                | 65.7             | 0.0            | 65.7             | 0.000          |
| ccb_locobench   | sourcegraph_base        | 48.2             | 13.9           | 34.3             | 0.292          |
| ccb_locobench   | sourcegraph_full        | 120.9            | 23.1           | 97.8             | 0.272          |
| ccb_pytorch     | baseline                | 64.6             | 0.0            | 64.6             | 0.000          |
| ccb_pytorch     | sourcegraph_base        | 60.0             | 13.3           | 46.7             | 0.199          |
| ccb_pytorch     | sourcegraph_full        | 65.5             | 12.9           | 52.5             | 0.169          |
| ccb_repoqa      | baseline                | 9.2              | 0.0            | 9.2              | 0.000          |
| ccb_repoqa      | sourcegraph_base        | 7.8              | 2.1            | 5.7              | 0.262          |
| ccb_repoqa      | sourcegraph_full        | 6.2              | 4.0            | 2.2              | 0.680          |
| ccb_swebenchpro | baseline                | 56.6             | 0.0            | 56.6             | 0.000          |
| ccb_swebenchpro | sourcegraph_base        | 75.6             | 7.4            | 68.2             | 0.115          |
| ccb_swebenchpro | sourcegraph_full        | 53.0             | 6.1            | 46.9             | 0.135          |
| ccb_sweperf     | baseline                | 60.7             | 0.0            | 60.7             | 0.000          |
| ccb_sweperf     | sourcegraph_base        | 83.0             | 8.7            | 74.3             | 0.130          |
| ccb_sweperf     | sourcegraph_full        | 135.0            | 6.7            | 128.3            | 0.058          |
| ccb_tac         | baseline                | 65.6             | 0.0            | 65.6             | 0.000          |
| ccb_tac         | sourcegraph_base        | 67.5             | 13.5           | 54.0             | 0.295          |
| ccb_tac         | sourcegraph_full        | 51.6             | 7.2            | 44.4             | 0.172          |
| codereview      | baseline                | 21.7             | 0.0            | 21.7             | 0.000          |
| codereview      | sourcegraph_base        | 44.7             | 1.7            | 43.0             | 0.048          |
| codereview      | sourcegraph_full        | 34.7             | 9.7            | 25.0             | 0.287          |
| dependeval      | baseline                | 7.9              | 0.0            | 7.9              | 0.000          |
| dependeval      | sourcegraph_base        | 11.2             | 4.0            | 7.2              | 0.268          |
| dependeval      | sourcegraph_full        | 10.6             | 4.3            | 6.3              | 0.281          |
| linuxflbench    | baseline                | 31.6             | 0.0            | 31.6             | 0.000          |
| linuxflbench    | sourcegraph_base        | 31.0             | 18.0           | 13.0             | 0.497          |
| linuxflbench    | sourcegraph_full        | 33.0             | 17.8           | 15.2             | 0.434          |

## Search Patterns

| Benchmark       | Config                  | Mean Keyword Searches | Mean NLS Searches | Mean Deep Searches | Mean DS/KW Ratio |
| --------------- | ----------------------- | --------------------- | ----------------- | ------------------ | ---------------- |
| ccb_crossrepo   | baseline                | -                     | -                 | -                  | -                |
| ccb_crossrepo   | sourcegraph_base        | 3.5                   | 0.0               | 0.0                | 0.000            |
| ccb_crossrepo   | sourcegraph_full        | 7.0                   | 0.0               | 0.0                | 0.000            |
| ccb_dibench     | baseline                | -                     | -                 | -                  | -                |
| ccb_dibench     | sourcegraph_base        | 3.4                   | 0.0               | 0.0                | 0.000            |
| ccb_dibench     | sourcegraph_full        | 2.6                   | 0.0               | 0.0                | 0.000            |
| ccb_k8sdocs     | baseline                | -                     | -                 | -                  | -                |
| ccb_k8sdocs     | sourcegraph_base        | 2.5                   | 0.0               | 0.0                | 0.000            |
| ccb_k8sdocs     | sourcegraph_full        | 3.8                   | 0.0               | 0.0                | 0.000            |
| ccb_largerepo   | baseline                | -                     | -                 | -                  | -                |
| ccb_largerepo   | sourcegraph_base        | 12.8                  | 0.2               | 0.0                | 0.000            |
| ccb_largerepo   | sourcegraph_base_latest | 9.0                   | 2.0               | 0.0                | 0.000            |
| ccb_largerepo   | sourcegraph_full        | 8.8                   | 0.5               | 0.0                | 0.000            |
| ccb_locobench   | baseline                | -                     | -                 | -                  | -                |
| ccb_locobench   | sourcegraph_base        | 9.9                   | 1.4               | 0.0                | 0.000            |
| ccb_locobench   | sourcegraph_full        | 7.6                   | 1.0               | 0.0                | 0.004            |
| ccb_pytorch     | baseline                | -                     | -                 | -                  | -                |
| ccb_pytorch     | sourcegraph_base        | 9.7                   | 0.2               | 0.0                | 0.000            |
| ccb_pytorch     | sourcegraph_full        | 6.9                   | 0.2               | 0.0                | 0.000            |
| ccb_repoqa      | baseline                | -                     | -                 | -                  | -                |
| ccb_repoqa      | sourcegraph_base        | 0.4                   | 1.0               | 0.0                | 0.000            |
| ccb_repoqa      | sourcegraph_full        | 2.0                   | 0.9               | 0.0                | 0.000            |
| ccb_swebenchpro | baseline                | -                     | -                 | -                  | -                |
| ccb_swebenchpro | sourcegraph_base        | 5.2                   | 0.1               | 0.0                | 0.000            |
| ccb_swebenchpro | sourcegraph_full        | 3.5                   | 0.0               | 0.0                | 0.000            |
| ccb_sweperf     | baseline                | -                     | -                 | -                  | -                |
| ccb_sweperf     | sourcegraph_base        | 2.3                   | 0.3               | 0.0                | 0.000            |
| ccb_sweperf     | sourcegraph_full        | 3.0                   | 0.7               | 0.0                | 0.000            |
| ccb_tac         | baseline                | -                     | -                 | -                  | -                |
| ccb_tac         | sourcegraph_base        | 1.2                   | 0.2               | 0.0                | 0.000            |
| ccb_tac         | sourcegraph_full        | 2.4                   | 0.0               | 0.0                | 0.000            |
| codereview      | baseline                | -                     | -                 | -                  | -                |
| codereview      | sourcegraph_base        | 4.0                   | 0.0               | 0.0                | 0.000            |
| codereview      | sourcegraph_full        | 5.7                   | 0.0               | 0.0                | 0.000            |
| dependeval      | baseline                | -                     | -                 | -                  | -                |
| dependeval      | sourcegraph_base        | 2.8                   | 0.9               | 0.0                | 0.000            |
| dependeval      | sourcegraph_full        | 2.3                   | 1.3               | 0.0                | 0.000            |
| linuxflbench    | baseline                | -                     | -                 | -                  | -                |
| linuxflbench    | sourcegraph_base        | 10.8                  | 0.0               | 0.0                | 0.000            |
| linuxflbench    | sourcegraph_full        | 10.2                  | 0.0               | 0.0                | 0.000            |

## Code Changes

| Benchmark       | Config                  | Mean Files Modified | Mean Lines Added | Mean Lines Removed |
| --------------- | ----------------------- | ------------------- | ---------------- | ------------------ |
| ccb_crossrepo   | baseline                | 2.4                 | 525.6            | 0.6                |
| ccb_crossrepo   | sourcegraph_base        | 1.6                 | 78.0             | 1.4                |
| ccb_crossrepo   | sourcegraph_full        | 1.4                 | 129.0            | 0.6                |
| ccb_dibench     | baseline                | 1.0                 | 9.0              | 4.5                |
| ccb_dibench     | sourcegraph_base        | 1.0                 | 8.4              | 3.6                |
| ccb_dibench     | sourcegraph_full        | 1.0                 | 9.4              | 4.4                |
| ccb_k8sdocs     | baseline                | 1.0                 | 151.4            | 0.0                |
| ccb_k8sdocs     | sourcegraph_base        | 1.0                 | 118.6            | 0.0                |
| ccb_k8sdocs     | sourcegraph_full        | 1.0                 | 111.2            | 0.2                |
| ccb_largerepo   | baseline                | 5.2                 | 434.0            | 204.8              |
| ccb_largerepo   | sourcegraph_base        | 6.2                 | 291.5            | 161.0              |
| ccb_largerepo   | sourcegraph_base_latest | 11.0                | 159.0            | 74.0               |
| ccb_largerepo   | sourcegraph_full        | 7.5                 | 331.2            | 143.0              |
| ccb_locobench   | baseline                | 3.7                 | 995.9            | 33.0               |
| ccb_locobench   | sourcegraph_base        | 3.1                 | 1089.1           | 35.3               |
| ccb_locobench   | sourcegraph_full        | 7.1                 | 1245.0           | 150.2              |
| ccb_pytorch     | baseline                | 2.8                 | 144.3            | 114.3              |
| ccb_pytorch     | sourcegraph_base        | 2.2                 | 45.8             | 54.2               |
| ccb_pytorch     | sourcegraph_full        | 3.5                 | 188.1            | 77.2               |
| ccb_repoqa      | baseline                | -                   | -                | -                  |
| ccb_repoqa      | sourcegraph_base        | -                   | -                | -                  |
| ccb_repoqa      | sourcegraph_full        | -                   | -                | -                  |
| ccb_swebenchpro | baseline                | 4.6                 | 146.9            | 88.8               |
| ccb_swebenchpro | sourcegraph_base        | 4.9                 | 260.9            | 120.7              |
| ccb_swebenchpro | sourcegraph_full        | 4.8                 | 175.6            | 70.0               |
| ccb_sweperf     | baseline                | 2.3                 | 452.0            | 104.7              |
| ccb_sweperf     | sourcegraph_base        | 3.3                 | 1032.3           | 261.0              |
| ccb_sweperf     | sourcegraph_full        | 3.3                 | 622.0            | 230.7              |
| ccb_tac         | baseline                | 3.0                 | 254.3            | 24.7               |
| ccb_tac         | sourcegraph_base        | 7.7                 | 893.2            | 12.2               |
| ccb_tac         | sourcegraph_full        | 4.0                 | 405.7            | 10.0               |
| codereview      | baseline                | 3.7                 | 64.7             | 27.7               |
| codereview      | sourcegraph_base        | 3.7                 | 66.7             | 20.3               |
| codereview      | sourcegraph_full        | 3.7                 | 58.3             | 16.0               |
| dependeval      | baseline                | 1.0                 | 6.0              | 0.0                |
| dependeval      | sourcegraph_base        | 1.1                 | 14.4             | 0.0                |
| dependeval      | sourcegraph_full        | 1.0                 | 6.7              | 0.0                |
| linuxflbench    | baseline                | 1.0                 | 7.0              | 0.0                |
| linuxflbench    | sourcegraph_base        | 1.0                 | 7.0              | 0.0                |
| linuxflbench    | sourcegraph_full        | 1.0                 | 8.6              | 0.2                |

## Cache Efficiency

| Benchmark       | Config                  | Mean Cache Hit Rate | Mean Input/Output Ratio | Mean Cost (USD) |
| --------------- | ----------------------- | ------------------- | ----------------------- | --------------- |
| ccb_crossrepo   | baseline                | 0.967               | 0.2                     | $2.6890         |
| ccb_crossrepo   | sourcegraph_base        | 0.961               | 0.0                     | $2.6383         |
| ccb_crossrepo   | sourcegraph_full        | 0.955               | 0.0                     | $3.9049         |
| ccb_dibench     | baseline                | 0.958               | 0.0                     | $0.7194         |
| ccb_dibench     | sourcegraph_base        | 0.969               | 0.0                     | $1.1172         |
| ccb_dibench     | sourcegraph_full        | 0.963               | 0.0                     | $0.9261         |
| ccb_k8sdocs     | baseline                | 0.941               | 0.0                     | $0.9183         |
| ccb_k8sdocs     | sourcegraph_base        | 0.930               | 0.0                     | $0.7171         |
| ccb_k8sdocs     | sourcegraph_full        | 0.941               | 0.0                     | $0.6359         |
| ccb_largerepo   | baseline                | 0.979               | 0.0                     | $5.4184         |
| ccb_largerepo   | sourcegraph_base        | 0.984               | 0.0                     | $4.7376         |
| ccb_largerepo   | sourcegraph_base_latest | -                   | 8243.4                  | $240.9961       |
| ccb_largerepo   | sourcegraph_full        | 0.986               | 0.1                     | $5.7837         |
| ccb_locobench   | baseline                | 0.948               | 0.0                     | $3.8388         |
| ccb_locobench   | sourcegraph_base        | 0.959               | 0.0                     | $1.9733         |
| ccb_locobench   | sourcegraph_full        | 0.958               | 0.0                     | $7.9783         |
| ccb_pytorch     | baseline                | 0.981               | 0.2                     | $2.1385         |
| ccb_pytorch     | sourcegraph_base        | 0.976               | 0.4                     | $2.4689         |
| ccb_pytorch     | sourcegraph_full        | 0.981               | 0.0                     | $2.5841         |
| ccb_repoqa      | baseline                | 0.955               | 0.0                     | $0.1666         |
| ccb_repoqa      | sourcegraph_base        | 0.942               | 0.0                     | $0.3079         |
| ccb_repoqa      | sourcegraph_full        | 0.890               | 0.0                     | $0.2427         |
| ccb_swebenchpro | baseline                | 0.968               | 0.0                     | $1.5216         |
| ccb_swebenchpro | sourcegraph_base        | 0.975               | 0.0                     | $2.3665         |
| ccb_swebenchpro | sourcegraph_full        | 0.976               | 0.0                     | $2.0589         |
| ccb_sweperf     | baseline                | 0.974               | 0.0                     | $3.8225         |
| ccb_sweperf     | sourcegraph_base        | 0.979               | 0.0                     | $5.8527         |
| ccb_sweperf     | sourcegraph_full        | 0.983               | 0.0                     | $8.5731         |
| ccb_tac         | baseline                | 0.975               | 0.0                     | $2.5536         |
| ccb_tac         | sourcegraph_base        | 0.957               | 0.0                     | $2.9960         |
| ccb_tac         | sourcegraph_full        | 0.972               | 0.0                     | $2.4761         |
| codereview      | baseline                | 0.960               | 0.0                     | $0.5640         |
| codereview      | sourcegraph_base        | 0.967               | 0.1                     | $0.9551         |
| codereview      | sourcegraph_full        | 0.970               | 0.0                     | $0.8254         |
| dependeval      | baseline                | 0.927               | 0.0                     | $0.2771         |
| dependeval      | sourcegraph_base        | 0.922               | 0.0                     | $0.4008         |
| dependeval      | sourcegraph_full        | 0.924               | 0.0                     | $0.4028         |
| linuxflbench    | baseline                | 0.967               | 0.0                     | $1.0380         |
| linuxflbench    | sourcegraph_base        | 0.953               | 0.0                     | $1.1045         |
| linuxflbench    | sourcegraph_full        | 0.968               | 0.0                     | $1.3659         |

## SWE-Bench Pro Partial Scores

| Config           | Mean Partial Score | Tasks |
| ---------------- | ------------------ | ----- |
| baseline         | 0.595              | 36    |
| sourcegraph_base | 0.530              | 36    |
| sourcegraph_full | 0.769              | 36    |

## Performance by SDLC Phase

| SDLC Phase                   | Tasks | baseline | sourcegraph_base | sourcegraph_base_latest | sourcegraph_full |
| ---------------------------- | ----- | -------- | ---------------- | ----------------------- | ---------------- |
| Architecture & Design        | 26    | 0.770    | 0.689            | -                       | 0.799            |
| Documentation                | 5     | 0.920    | 0.920            | -                       | 0.920            |
| Implementation (bug fix)     | 56    | 0.426    | 0.357            | -                       | 0.659            |
| Implementation (feature)     | 32    | 0.366    | 0.381            | 0.700                   | 0.484            |
| Implementation (refactoring) | 15    | 0.451    | 0.481            | -                       | 0.420            |
| Maintenance                  | 2     | 0.400    | 0.400            | -                       | 0.400            |
| Requirements & Discovery     | 12    | 0.833    | 0.833            | -                       | 0.833            |
| Testing & QA                 | 8     | 0.796    | 0.529            | -                       | 0.738            |

## Performance by Language

| Language   | Tasks | baseline | sourcegraph_base | sourcegraph_base_latest | sourcegraph_full |
| ---------- | ----- | -------- | ---------------- | ----------------------- | ---------------- |
| c          | 12    | 0.648    | 0.558            | -                       | 0.643            |
| cpp        | 19    | 0.298    | 0.270            | -                       | 0.396            |
| csharp     | 6     | 0.416    | 0.248            | -                       | 0.437            |
| go         | 24    | 0.644    | 0.606            | 0.700                   | 0.738            |
| java       | 10    | 0.739    | 0.718            | -                       | 0.703            |
| javascript | 14    | 0.742    | 0.740            | -                       | 0.833            |
| python     | 38    | 0.429    | 0.330            | -                       | 0.600            |
| python,cpp | 1     | 1.000    | 1.000            | -                       | 1.000            |
| rust       | 12    | 0.571    | 0.581            | -                       | 0.618            |
| typescript | 20    | 0.523    | 0.540            | -                       | 0.812            |

## Performance by MCP Benefit Score

| MCP Benefit Score   | Tasks | baseline | sourcegraph_base | sourcegraph_base_latest | sourcegraph_full |
| ------------------- | ----- | -------- | ---------------- | ----------------------- | ---------------- |
| 0.0-0.4 (low)       | 0     | -        | -                | -                       | -                |
| 0.4-0.6 (medium)    | 34    | 0.464    | 0.381            | -                       | 0.617            |
| 0.6-0.8 (high)      | 69    | 0.527    | 0.497            | -                       | 0.662            |
| 0.8-1.0 (very high) | 52    | 0.611    | 0.569            | 0.700                   | 0.644            |

