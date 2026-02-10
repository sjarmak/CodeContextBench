# CodeContextBench Evaluation Report

Generated: 2026-02-10T18:54:25.589083+00:00
Report ID: eval_20260210_185425

## Run Inventory

| Benchmark       | Config                   | Model                              | MCP Mode         | Tasks | Timestamp           |
| --------------- | ------------------------ | ---------------------------------- | ---------------- | ----- | ------------------- |
| ccb_crossrepo   | baseline                 | anthropic/claude-opus-4-6          | none             | 5     | 2026-02-07 17-13-08 |
| ccb_crossrepo   | sourcegraph_base         | anthropic/claude-opus-4-6          | sourcegraph_base | 5     | 2026-02-07 17-37-04 |
| ccb_crossrepo   | sourcegraph_full         | anthropic/claude-opus-4-6          | sourcegraph_full | 5     | 2026-02-07 17-51-36 |
| ccb_dibench     | baseline                 | anthropic/claude-opus-4-5-20251101 | none             | 8     | 2026-02-03 16-43-09 |
| ccb_dibench     | sourcegraph_base         | anthropic/claude-opus-4-6          | sourcegraph_base | 8     | 2026-02-09 18-19-42 |
| ccb_dibench     | sourcegraph_full         | anthropic/claude-opus-4-6          | sourcegraph_full | 8     | 2026-02-09 18-26-45 |
| ccb_k8sdocs     | baseline                 | anthropic/claude-opus-4-6          | none             | 5     | 2026-02-10 17-37-55 |
| ccb_k8sdocs     | sourcegraph_base         | anthropic/claude-opus-4-6          | sourcegraph_base | 5     | 2026-02-10 18-02-16 |
| ccb_k8sdocs     | sourcegraph_full         | anthropic/claude-opus-4-6          | sourcegraph_base | 5     | 2026-02-10 18-19-31 |
| ccb_largerepo   | baseline                 | anthropic/claude-opus-4-5-20251101 | none             | 4     | 2026-02-05 22-53-51 |
| ccb_largerepo   | sourcegraph_base         | anthropic/claude-opus-4-5-20251101 | sourcegraph_base | 4     | 2026-02-06 00-48-34 |
| ccb_largerepo   | sourcegraph_base_latest  | anthropic/claude-opus-4-6          | sourcegraph_base | 1     | 2026-02-10 16-44-09 |
| ccb_largerepo   | sourcegraph_base_precise | anthropic/claude-opus-4-6          | sourcegraph_base | 1     | 2026-02-10 17-07-44 |
| ccb_largerepo   | sourcegraph_full         | anthropic/claude-opus-4-6          | sourcegraph_full | 4     | 2026-02-08 18-45-22 |
| ccb_locobench   | baseline                 | anthropic/claude-opus-4-5-20251101 | none             | 25    | 2026-02-03 08-38-27 |
| ccb_locobench   | sourcegraph_base         | anthropic/claude-opus-4-5-20251101 | sourcegraph_base | 20    | 2026-02-03 18-36-37 |
| ccb_locobench   | sourcegraph_full         | anthropic/claude-opus-4-6          | sourcegraph_full | 25    | 2026-02-07 22-05-15 |
| ccb_pytorch     | baseline                 | anthropic/claude-opus-4-6          | none             | 11    | 2026-02-10 16-40-10 |
| ccb_pytorch     | sourcegraph_base         | anthropic/claude-opus-4-6          | sourcegraph_base | 11    | 2026-02-10 16-48-29 |
| ccb_pytorch     | sourcegraph_full         | anthropic/claude-opus-4-6          | sourcegraph_full | 11    | 2026-02-08 14-51-56 |
| ccb_repoqa      | baseline                 | anthropic/claude-opus-4-5-20251101 | none             | 10    | 2026-02-03 16-35-20 |
| ccb_repoqa      | sourcegraph_base         | anthropic/claude-opus-4-5-20251101 | sourcegraph_base | 10    | 2026-02-03 16-58-00 |
| ccb_repoqa      | sourcegraph_full         | anthropic/claude-opus-4-6          | sourcegraph_full | 10    | 2026-02-08 13-25-29 |
| ccb_swebenchpro | baseline                 | anthropic/claude-opus-4-5-20251101 | none             | 36    | 2026-02-02 12-25-24 |
| ccb_swebenchpro | sourcegraph_base         | anthropic/claude-opus-4-5-20251101 | sourcegraph_base | 36    | 2026-02-05 03-05-37 |
| ccb_swebenchpro | sourcegraph_full         | anthropic/claude-opus-4-6          | sourcegraph_full | 34    | 2026-02-08 00-20-27 |
| ccb_sweperf     | baseline                 | anthropic/claude-opus-4-5-20251101 | none             | 3     | 2026-02-05 01-04-11 |
| ccb_sweperf     | sourcegraph_base         | anthropic/claude-opus-4-5-20251101 | sourcegraph_base | 3     | 2026-02-05 01-21-42 |
| ccb_sweperf     | sourcegraph_full         | anthropic/claude-opus-4-6          | sourcegraph_full | 3     | 2026-02-09 00-08-48 |
| ccb_tac         | baseline                 | anthropic/claude-opus-4-6          | none             | 8     | 2026-02-07 16-38-41 |
| ccb_tac         | sourcegraph_base         | anthropic/claude-opus-4-6          | sourcegraph_base | 8     | 2026-02-07 17-19-56 |
| ccb_tac         | sourcegraph_full         | anthropic/claude-opus-4-6          | sourcegraph_full | 8     | 2026-02-07 17-52-41 |
| codereview      | baseline                 | anthropic/claude-opus-4-5-20251101 | none             | 3     | 2026-02-06 15-53-56 |
| codereview      | sourcegraph_base         | anthropic/claude-opus-4-6          | sourcegraph_base | 3     | 2026-02-07 16-30-22 |
| codereview      | sourcegraph_full         | anthropic/claude-opus-4-6          | sourcegraph_full | 3     | 2026-02-08 21-07-39 |
| dependeval      | baseline                 | anthropic/claude-opus-4-6          | none             | 32    | 2026-02-09 00-12-09 |
| dependeval      | sourcegraph_base         | anthropic/claude-opus-4-6          | sourcegraph_base | 32    | 2026-02-09 00-34-42 |
| dependeval      | sourcegraph_full         | anthropic/claude-opus-4-6          | sourcegraph_full | 32    | 2026-02-09 00-58-43 |
| linuxflbench    | baseline                 | anthropic/claude-opus-4-5-20251101 | none             | 5     | 2026-02-06 16-28-49 |
| linuxflbench    | sourcegraph_base         | anthropic/claude-opus-4-6          | sourcegraph_base | 5     | 2026-02-07 18-20-16 |
| linuxflbench    | sourcegraph_full         | anthropic/claude-opus-4-6          | sourcegraph_full | 5     | 2026-02-08 21-35-42 |

## Aggregate Performance

| Config                   | Mean Reward | Pass Rate | Tasks |
| ------------------------ | ----------- | --------- | ----- |
| baseline                 | 0.567       | 0.742     | 155   |
| sourcegraph_base         | 0.547       | 0.720     | 150   |
| sourcegraph_base_latest  | 0.700       | 1.000     | 1     |
| sourcegraph_base_precise | 0.700       | 1.000     | 1     |
| sourcegraph_full         | 0.648       | 0.809     | 153   |

## Per-Benchmark Breakdown (Mean Reward)

| Benchmark       | baseline | sourcegraph_base | sourcegraph_base_latest | sourcegraph_base_precise | sourcegraph_full |
| --------------- | -------- | ---------------- | ----------------------- | ------------------------ | ---------------- |
| ccb_crossrepo   | 0.571    | 0.587            | -                       | -                        | 0.387            |
| ccb_dibench     | 0.500    | 0.500            | -                       | -                        | 0.500            |
| ccb_k8sdocs     | 0.920    | 0.920            | -                       | -                        | 0.920            |
| ccb_largerepo   | 0.250    | 0.250            | 0.700                   | 0.700                    | 0.425            |
| ccb_locobench   | 0.449    | 0.513            | -                       | -                        | 0.499            |
| ccb_pytorch     | 0.273    | 0.270            | -                       | -                        | 0.265            |
| ccb_repoqa      | 1.000    | 1.000            | -                       | -                        | 1.000            |
| ccb_swebenchpro | 0.500    | 0.417            | -                       | -                        | 0.758            |
| ccb_sweperf     | 0.591    | 0.032            | -                       | -                        | 0.367            |
| ccb_tac         | 0.492    | 0.365            | -                       | -                        | 0.544            |
| codereview      | 0.933    | 0.980            | -                       | -                        | 1.000            |
| dependeval      | 0.636    | 0.665            | -                       | -                        | 0.720            |
| linuxflbench    | 0.860    | 0.820            | -                       | -                        | 0.880            |

## Efficiency

| Benchmark       | Config                   | Mean Input Tokens | Mean Output Tokens | Mean Cache Tokens | Mean Task Time (s) | Mean Wall Clock (s) | Mean Cost (USD) |
| --------------- | ------------------------ | ----------------- | ------------------ | ----------------- | ------------------ | ------------------- | --------------- |
| ccb_crossrepo   | baseline                 | 1,725             | 17,789             | 3,270,335         | 501.9              | 584.5               | $2.6890         |
| ccb_crossrepo   | sourcegraph_base         | 104               | 14,554             | 3,414,798         | 342.5              | 603.7               | $2.6383         |
| ccb_crossrepo   | sourcegraph_full         | 57                | 18,011             | 4,102,584         | 489.1              | 620.1               | $3.9049         |
| ccb_dibench     | baseline                 | 35                | 2,679              | 861,473           | 167.5              | 275.1               | $0.7194         |
| ccb_dibench     | sourcegraph_base         | 26                | 4,372              | 1,344,485         | 163.0              | 222.1               | $1.1172         |
| ccb_dibench     | sourcegraph_full         | 22                | 3,589              | 1,066,031         | 135.4              | 170.7               | $0.9261         |
| ccb_k8sdocs     | baseline                 | 774               | 4,982              | 559,188           | 330.7              | 534.5               | $0.6868         |
| ccb_k8sdocs     | sourcegraph_base         | 15                | 4,992              | 550,432           | 188.2              | 345.4               | $0.8492         |
| ccb_k8sdocs     | sourcegraph_full         | 882               | 5,028              | 627,527           | 232.9              | 382.9               | $0.8584         |
| ccb_largerepo   | baseline                 | 85                | 23,860             | 7,356,855         | 997.2              | 2903.4              | $5.4184         |
| ccb_largerepo   | sourcegraph_base         | 2                 | 19,626             | 7,152,633         | 631.3              | 1187.3              | $4.7376         |
| ccb_largerepo   | sourcegraph_base_latest  | 5,803,848         | 491                | 5,803,759         | 587.1              | 1406.0              | $195.9150       |
| ccb_largerepo   | sourcegraph_base_precise | 74                | 19,906             | 5,276,890         | 1494.6             | 2170.2              | $3.6124         |
| ccb_largerepo   | sourcegraph_full         | 1,693             | 26,879             | 8,073,793         | 2247.1             | 3931.5              | $5.7837         |
| ccb_locobench   | baseline                 | 36                | 18,863             | 3,048,692         | 406.9              | 448.7               | $3.8388         |
| ccb_locobench   | sourcegraph_base         | 6                 | 17,437             | 3,027,015         | 314.4              | 389.5               | $2.6729         |
| ccb_locobench   | sourcegraph_full         | 1,132             | 23,906             | 5,179,082         | 805.3              | 1144.2              | $7.9783         |
| ccb_pytorch     | baseline                 | 1,783             | 9,481              | 2,533,532         | 268.7              | 977.7               | $1.8711         |
| ccb_pytorch     | sourcegraph_base         | 1,636             | 8,402              | 3,108,614         | 251.6              | 590.9               | $2.1733         |
| ccb_pytorch     | sourcegraph_full         | 224               | 12,449             | 3,742,737         | 685.4              | 2954.1              | $2.5841         |
| ccb_repoqa      | baseline                 | 2                 | 1,283              | 157,722           | 43.9               | 165.1               | $0.1666         |
| ccb_repoqa      | sourcegraph_base         | 2                 | 1,440              | 330,302           | 47.1               | 125.2               | $0.3079         |
| ccb_repoqa      | sourcegraph_full         | 5                 | 1,171              | 198,223           | 32.6               | 306.6               | $0.2427         |
| ccb_swebenchpro | baseline                 | 80                | 8,253              | 2,144,776         | 279.4              | 597.1               | $1.5785         |
| ccb_swebenchpro | sourcegraph_base         | 14                | 10,438             | 3,528,717         | 367.6              | 691.5               | $2.4845         |
| ccb_swebenchpro | sourcegraph_full         | 431               | 10,469             | 2,686,251         | 382.6              | 1585.8              | $1.9409         |
| ccb_sweperf     | baseline                 | 2                 | 18,896             | 5,061,122         | 452.7              | 795.7               | $3.8225         |
| ccb_sweperf     | sourcegraph_base         | 18                | 32,871             | 8,114,558         | 749.8              | 838.8               | $5.8527         |
| ccb_sweperf     | sourcegraph_full         | 123               | 48,174             | 11,675,461        | 1279.9             | 1388.1              | $8.5731         |
| ccb_tac         | baseline                 | 53                | 14,563             | 3,253,165         | 619.9              | 1483.0              | $2.5536         |
| ccb_tac         | sourcegraph_base         | 53                | 20,034             | 3,901,509         | 638.5              | 1123.3              | $2.9960         |
| ccb_tac         | sourcegraph_full         | 435               | 16,705             | 3,041,064         | 614.1              | 1087.3              | $2.4761         |
| codereview      | baseline                 | 2                 | 4,360              | 622,987           | 90.4               | 185.9               | $0.5640         |
| codereview      | sourcegraph_base         | 588               | 5,952              | 1,047,081         | 132.0              | 286.1               | $0.9551         |
| codereview      | sourcegraph_full         | 21                | 6,338              | 978,964           | 116.4              | 209.0               | $0.8254         |
| dependeval      | baseline                 | 49                | 3,059              | 163,919           | 77.1               | 98.5                | $0.2771         |
| dependeval      | sourcegraph_base         | 17                | 3,625              | 318,540           | 100.1              | 122.6               | $0.4008         |
| dependeval      | sourcegraph_full         | 57                | 3,442              | 361,105           | 75.9               | 98.3                | $0.4028         |
| linuxflbench    | baseline                 | 41                | 6,408              | 1,324,768         | 232.5              | 568.4               | $1.0380         |
| linuxflbench    | sourcegraph_base         | 87                | 5,270              | 1,108,409         | 332.5              | 1436.5              | $1.1045         |
| linuxflbench    | sourcegraph_full         | 25                | 6,471              | 1,399,965         | 228.9              | 414.4               | $1.3659         |

## Tool Utilization

| Benchmark       | Config                   | Mean Total Calls | Mean MCP Calls | Mean Local Calls | Mean MCP Ratio |
| --------------- | ------------------------ | ---------------- | -------------- | ---------------- | -------------- |
| ccb_crossrepo   | baseline                 | 124.0            | 0.0            | 124.0            | 0.000          |
| ccb_crossrepo   | sourcegraph_base         | 84.6             | 2.8            | 81.8             | 0.042          |
| ccb_crossrepo   | sourcegraph_full         | 122.4            | 1.4            | 121.0            | 0.018          |
| ccb_dibench     | baseline                 | 25.9             | 0.0            | 25.9             | 0.000          |
| ccb_dibench     | sourcegraph_base         | 34.8             | 14.5           | 20.2             | 0.413          |
| ccb_dibench     | sourcegraph_full         | 29.4             | 12.2           | 17.1             | 0.415          |
| ccb_k8sdocs     | baseline                 | 42.4             | 0.0            | 42.4             | 0.000          |
| ccb_k8sdocs     | sourcegraph_base         | 56.6             | 0.0            | 56.6             | 0.000          |
| ccb_k8sdocs     | sourcegraph_full         | 63.6             | 0.0            | 63.6             | 0.000          |
| ccb_largerepo   | baseline                 | 113.0            | 0.0            | 113.0            | 0.000          |
| ccb_largerepo   | sourcegraph_base         | 78.2             | 17.8           | 60.5             | 0.232          |
| ccb_largerepo   | sourcegraph_base_latest  | 60.0             | 8.0            | 52.0             | 0.133          |
| ccb_largerepo   | sourcegraph_base_precise | 104.0            | 4.0            | 100.0            | 0.038          |
| ccb_largerepo   | sourcegraph_full         | 169.2            | 13.8           | 155.5            | 0.077          |
| ccb_locobench   | baseline                 | 65.7             | 0.0            | 65.7             | 0.000          |
| ccb_locobench   | sourcegraph_base         | 48.0             | 16.0           | 31.9             | 0.338          |
| ccb_locobench   | sourcegraph_full         | 120.9            | 23.1           | 97.8             | 0.272          |
| ccb_pytorch     | baseline                 | 58.4             | 0.0            | 58.4             | 0.000          |
| ccb_pytorch     | sourcegraph_base         | 54.8             | 11.6           | 43.2             | 0.186          |
| ccb_pytorch     | sourcegraph_full         | 65.5             | 12.9           | 52.5             | 0.169          |
| ccb_repoqa      | baseline                 | 9.2              | 0.0            | 9.2              | 0.000          |
| ccb_repoqa      | sourcegraph_base         | 7.8              | 2.1            | 5.7              | 0.262          |
| ccb_repoqa      | sourcegraph_full         | 6.2              | 4.0            | 2.2              | 0.680          |
| ccb_swebenchpro | baseline                 | 51.7             | 0.0            | 51.7             | 0.000          |
| ccb_swebenchpro | sourcegraph_base         | 68.7             | 6.9            | 61.8             | 0.122          |
| ccb_swebenchpro | sourcegraph_full         | 50.1             | 6.3            | 43.7             | 0.150          |
| ccb_sweperf     | baseline                 | 60.7             | 0.0            | 60.7             | 0.000          |
| ccb_sweperf     | sourcegraph_base         | 83.0             | 8.7            | 74.3             | 0.130          |
| ccb_sweperf     | sourcegraph_full         | 135.0            | 6.7            | 128.3            | 0.058          |
| ccb_tac         | baseline                 | 65.6             | 0.0            | 65.6             | 0.000          |
| ccb_tac         | sourcegraph_base         | 67.5             | 13.5           | 54.0             | 0.295          |
| ccb_tac         | sourcegraph_full         | 51.6             | 7.2            | 44.4             | 0.172          |
| codereview      | baseline                 | 21.7             | 0.0            | 21.7             | 0.000          |
| codereview      | sourcegraph_base         | 44.7             | 1.7            | 43.0             | 0.048          |
| codereview      | sourcegraph_full         | 34.7             | 9.7            | 25.0             | 0.287          |
| dependeval      | baseline                 | 7.9              | 0.0            | 7.9              | 0.000          |
| dependeval      | sourcegraph_base         | 11.2             | 4.0            | 7.2              | 0.268          |
| dependeval      | sourcegraph_full         | 10.6             | 4.3            | 6.3              | 0.281          |
| linuxflbench    | baseline                 | 31.6             | 0.0            | 31.6             | 0.000          |
| linuxflbench    | sourcegraph_base         | 31.0             | 18.0           | 13.0             | 0.497          |
| linuxflbench    | sourcegraph_full         | 33.0             | 17.8           | 15.2             | 0.434          |

## Search Patterns

| Benchmark       | Config                   | Mean Keyword Searches | Mean NLS Searches | Mean Deep Searches | Mean DS/KW Ratio |
| --------------- | ------------------------ | --------------------- | ----------------- | ------------------ | ---------------- |
| ccb_crossrepo   | baseline                 | -                     | -                 | -                  | -                |
| ccb_crossrepo   | sourcegraph_base         | 3.5                   | 0.0               | 0.0                | 0.000            |
| ccb_crossrepo   | sourcegraph_full         | 7.0                   | 0.0               | 0.0                | 0.000            |
| ccb_dibench     | baseline                 | -                     | -                 | -                  | -                |
| ccb_dibench     | sourcegraph_base         | 3.4                   | 0.0               | 0.0                | 0.000            |
| ccb_dibench     | sourcegraph_full         | 2.6                   | 0.0               | 0.0                | 0.000            |
| ccb_k8sdocs     | baseline                 | -                     | -                 | -                  | -                |
| ccb_k8sdocs     | sourcegraph_base         | -                     | -                 | -                  | -                |
| ccb_k8sdocs     | sourcegraph_full         | -                     | -                 | -                  | -                |
| ccb_largerepo   | baseline                 | -                     | -                 | -                  | -                |
| ccb_largerepo   | sourcegraph_base         | 12.8                  | 0.2               | 0.0                | 0.000            |
| ccb_largerepo   | sourcegraph_base_latest  | 7.0                   | 1.0               | 0.0                | 0.000            |
| ccb_largerepo   | sourcegraph_base_precise | 3.0                   | 0.0               | 0.0                | 0.000            |
| ccb_largerepo   | sourcegraph_full         | 8.8                   | 0.5               | 0.0                | 0.000            |
| ccb_locobench   | baseline                 | -                     | -                 | -                  | -                |
| ccb_locobench   | sourcegraph_base         | 9.0                   | 1.2               | 0.0                | 0.000            |
| ccb_locobench   | sourcegraph_full         | 7.6                   | 1.0               | 0.0                | 0.004            |
| ccb_pytorch     | baseline                 | -                     | -                 | -                  | -                |
| ccb_pytorch     | sourcegraph_base         | 8.8                   | 0.2               | 0.0                | 0.000            |
| ccb_pytorch     | sourcegraph_full         | 6.9                   | 0.2               | 0.0                | 0.000            |
| ccb_repoqa      | baseline                 | -                     | -                 | -                  | -                |
| ccb_repoqa      | sourcegraph_base         | 0.4                   | 1.0               | 0.0                | 0.000            |
| ccb_repoqa      | sourcegraph_full         | 2.0                   | 0.9               | 0.0                | 0.000            |
| ccb_swebenchpro | baseline                 | -                     | -                 | -                  | -                |
| ccb_swebenchpro | sourcegraph_base         | 4.6                   | 0.1               | 0.0                | 0.000            |
| ccb_swebenchpro | sourcegraph_full         | 3.6                   | 0.0               | 0.0                | 0.000            |
| ccb_sweperf     | baseline                 | -                     | -                 | -                  | -                |
| ccb_sweperf     | sourcegraph_base         | 2.3                   | 0.3               | 0.0                | 0.000            |
| ccb_sweperf     | sourcegraph_full         | 3.0                   | 0.7               | 0.0                | 0.000            |
| ccb_tac         | baseline                 | -                     | -                 | -                  | -                |
| ccb_tac         | sourcegraph_base         | 1.2                   | 0.2               | 0.0                | 0.000            |
| ccb_tac         | sourcegraph_full         | 2.4                   | 0.0               | 0.0                | 0.000            |
| codereview      | baseline                 | -                     | -                 | -                  | -                |
| codereview      | sourcegraph_base         | 4.0                   | 0.0               | 0.0                | 0.000            |
| codereview      | sourcegraph_full         | 5.7                   | 0.0               | 0.0                | 0.000            |
| dependeval      | baseline                 | -                     | -                 | -                  | -                |
| dependeval      | sourcegraph_base         | 2.8                   | 0.9               | 0.0                | 0.000            |
| dependeval      | sourcegraph_full         | 2.3                   | 1.3               | 0.0                | 0.000            |
| linuxflbench    | baseline                 | -                     | -                 | -                  | -                |
| linuxflbench    | sourcegraph_base         | 10.8                  | 0.0               | 0.0                | 0.000            |
| linuxflbench    | sourcegraph_full         | 10.2                  | 0.0               | 0.0                | 0.000            |

## Code Changes

| Benchmark       | Config                   | Mean Files Modified | Mean Lines Added | Mean Lines Removed |
| --------------- | ------------------------ | ------------------- | ---------------- | ------------------ |
| ccb_crossrepo   | baseline                 | 2.4                 | 525.6            | 0.6                |
| ccb_crossrepo   | sourcegraph_base         | 1.6                 | 78.0             | 1.4                |
| ccb_crossrepo   | sourcegraph_full         | 1.4                 | 129.0            | 0.6                |
| ccb_dibench     | baseline                 | 1.0                 | 9.0              | 4.5                |
| ccb_dibench     | sourcegraph_base         | 1.0                 | 8.4              | 3.6                |
| ccb_dibench     | sourcegraph_full         | 1.0                 | 9.4              | 4.4                |
| ccb_k8sdocs     | baseline                 | 1.0                 | 132.0            | 0.0                |
| ccb_k8sdocs     | sourcegraph_base         | 1.0                 | 149.2            | 0.0                |
| ccb_k8sdocs     | sourcegraph_full         | 1.0                 | 156.2            | 0.2                |
| ccb_largerepo   | baseline                 | 5.2                 | 434.0            | 204.8              |
| ccb_largerepo   | sourcegraph_base         | 6.2                 | 291.5            | 161.0              |
| ccb_largerepo   | sourcegraph_base_latest  | 12.0                | 251.0            | 71.0               |
| ccb_largerepo   | sourcegraph_base_precise | 9.0                 | 206.0            | 92.0               |
| ccb_largerepo   | sourcegraph_full         | 7.5                 | 331.2            | 143.0              |
| ccb_locobench   | baseline                 | 3.7                 | 995.9            | 33.0               |
| ccb_locobench   | sourcegraph_base         | 2.9                 | 1053.1           | 31.8               |
| ccb_locobench   | sourcegraph_full         | 7.1                 | 1245.0           | 150.2              |
| ccb_pytorch     | baseline                 | 3.0                 | 130.0            | 106.0              |
| ccb_pytorch     | sourcegraph_base         | 2.4                 | 45.7             | 54.1               |
| ccb_pytorch     | sourcegraph_full         | 3.5                 | 188.1            | 77.2               |
| ccb_repoqa      | baseline                 | -                   | -                | -                  |
| ccb_repoqa      | sourcegraph_base         | -                   | -                | -                  |
| ccb_repoqa      | sourcegraph_full         | -                   | -                | -                  |
| ccb_swebenchpro | baseline                 | 4.2                 | 140.0            | 78.9               |
| ccb_swebenchpro | sourcegraph_base         | 4.4                 | 283.8            | 103.2              |
| ccb_swebenchpro | sourcegraph_full         | 4.5                 | 161.5            | 66.5               |
| ccb_sweperf     | baseline                 | 2.3                 | 452.0            | 104.7              |
| ccb_sweperf     | sourcegraph_base         | 3.3                 | 1032.3           | 261.0              |
| ccb_sweperf     | sourcegraph_full         | 3.3                 | 622.0            | 230.7              |
| ccb_tac         | baseline                 | 3.0                 | 254.3            | 24.7               |
| ccb_tac         | sourcegraph_base         | 7.7                 | 893.2            | 12.2               |
| ccb_tac         | sourcegraph_full         | 4.0                 | 405.7            | 10.0               |
| codereview      | baseline                 | 3.7                 | 64.7             | 27.7               |
| codereview      | sourcegraph_base         | 3.7                 | 66.7             | 20.3               |
| codereview      | sourcegraph_full         | 3.7                 | 58.3             | 16.0               |
| dependeval      | baseline                 | 1.0                 | 6.0              | 0.0                |
| dependeval      | sourcegraph_base         | 1.1                 | 14.4             | 0.0                |
| dependeval      | sourcegraph_full         | 1.0                 | 6.7              | 0.0                |
| linuxflbench    | baseline                 | 1.0                 | 7.0              | 0.0                |
| linuxflbench    | sourcegraph_base         | 1.0                 | 7.0              | 0.0                |
| linuxflbench    | sourcegraph_full         | 1.0                 | 8.6              | 0.2                |

## Cache Efficiency

| Benchmark       | Config                   | Mean Cache Hit Rate | Mean Input/Output Ratio | Mean Cost (USD) |
| --------------- | ------------------------ | ------------------- | ----------------------- | --------------- |
| ccb_crossrepo   | baseline                 | 0.967               | 0.2                     | $2.6890         |
| ccb_crossrepo   | sourcegraph_base         | 0.961               | 0.0                     | $2.6383         |
| ccb_crossrepo   | sourcegraph_full         | 0.955               | 0.0                     | $3.9049         |
| ccb_dibench     | baseline                 | 0.958               | 0.0                     | $0.7194         |
| ccb_dibench     | sourcegraph_base         | 0.969               | 0.0                     | $1.1172         |
| ccb_dibench     | sourcegraph_full         | 0.963               | 0.0                     | $0.9261         |
| ccb_k8sdocs     | baseline                 | 0.951               | 0.1                     | $0.6868         |
| ccb_k8sdocs     | sourcegraph_base         | 0.943               | 0.0                     | $0.8492         |
| ccb_k8sdocs     | sourcegraph_full         | 0.947               | 0.2                     | $0.8584         |
| ccb_largerepo   | baseline                 | 0.979               | 0.0                     | $5.4184         |
| ccb_largerepo   | sourcegraph_base         | 0.984               | 0.0                     | $4.7376         |
| ccb_largerepo   | sourcegraph_base_latest  | -                   | 11820.5                 | $195.9150       |
| ccb_largerepo   | sourcegraph_base_precise | 0.986               | 0.0                     | $3.6124         |
| ccb_largerepo   | sourcegraph_full         | 0.986               | 0.1                     | $5.7837         |
| ccb_locobench   | baseline                 | 0.948               | 0.0                     | $3.8388         |
| ccb_locobench   | sourcegraph_base         | 0.956               | 0.0                     | $2.6729         |
| ccb_locobench   | sourcegraph_full         | 0.958               | 0.0                     | $7.9783         |
| ccb_pytorch     | baseline                 | 0.977               | 0.1                     | $1.8711         |
| ccb_pytorch     | sourcegraph_base         | 0.974               | 0.3                     | $2.1733         |
| ccb_pytorch     | sourcegraph_full         | 0.981               | 0.0                     | $2.5841         |
| ccb_repoqa      | baseline                 | 0.955               | 0.0                     | $0.1666         |
| ccb_repoqa      | sourcegraph_base         | 0.942               | 0.0                     | $0.3079         |
| ccb_repoqa      | sourcegraph_full         | 0.890               | 0.0                     | $0.2427         |
| ccb_swebenchpro | baseline                 | 0.966               | 0.0                     | $1.5785         |
| ccb_swebenchpro | sourcegraph_base         | 0.972               | 0.0                     | $2.4845         |
| ccb_swebenchpro | sourcegraph_full         | 0.975               | 0.0                     | $1.9409         |
| ccb_sweperf     | baseline                 | 0.974               | 0.0                     | $3.8225         |
| ccb_sweperf     | sourcegraph_base         | 0.979               | 0.0                     | $5.8527         |
| ccb_sweperf     | sourcegraph_full         | 0.983               | 0.0                     | $8.5731         |
| ccb_tac         | baseline                 | 0.975               | 0.0                     | $2.5536         |
| ccb_tac         | sourcegraph_base         | 0.957               | 0.0                     | $2.9960         |
| ccb_tac         | sourcegraph_full         | 0.972               | 0.0                     | $2.4761         |
| codereview      | baseline                 | 0.960               | 0.0                     | $0.5640         |
| codereview      | sourcegraph_base         | 0.967               | 0.1                     | $0.9551         |
| codereview      | sourcegraph_full         | 0.970               | 0.0                     | $0.8254         |
| dependeval      | baseline                 | 0.927               | 0.0                     | $0.2771         |
| dependeval      | sourcegraph_base         | 0.922               | 0.0                     | $0.4008         |
| dependeval      | sourcegraph_full         | 0.924               | 0.0                     | $0.4028         |
| linuxflbench    | baseline                 | 0.967               | 0.0                     | $1.0380         |
| linuxflbench    | sourcegraph_base         | 0.953               | 0.0                     | $1.1045         |
| linuxflbench    | sourcegraph_full         | 0.968               | 0.0                     | $1.3659         |

## SWE-Bench Pro Partial Scores

| Config           | Mean Partial Score | Tasks |
| ---------------- | ------------------ | ----- |
| baseline         | 0.644              | 36    |
| sourcegraph_base | 0.580              | 36    |
| sourcegraph_full | 0.781              | 34    |

## Performance by SDLC Phase

| SDLC Phase                   | Tasks | baseline | sourcegraph_base | sourcegraph_base_latest | sourcegraph_base_precise | sourcegraph_full |
| ---------------------------- | ----- | -------- | ---------------- | ----------------------- | ------------------------ | ---------------- |
| Architecture & Design        | 26    | 0.770    | 0.843            | -                       | -                        | 0.799            |
| Documentation                | 5     | 0.920    | 0.920            | -                       | -                        | 0.920            |
| Implementation (bug fix)     | 55    | 0.502    | 0.443            | -                       | -                        | 0.666            |
| Implementation (feature)     | 32    | 0.366    | 0.381            | 0.700                   | 0.700                    | 0.484            |
| Implementation (refactoring) | 15    | 0.451    | 0.520            | -                       | -                        | 0.420            |
| Maintenance                  | 2     | 0.400    | 0.400            | -                       | -                        | 0.400            |
| Requirements & Discovery     | 12    | 0.833    | 0.833            | -                       | -                        | 0.833            |
| Testing & QA                 | 8     | 0.796    | 0.529            | -                       | -                        | 0.738            |

## Performance by Language

| Language   | Tasks | baseline | sourcegraph_base | sourcegraph_base_latest | sourcegraph_base_precise | sourcegraph_full |
| ---------- | ----- | -------- | ---------------- | ----------------------- | ------------------------ | ---------------- |
| c          | 12    | 0.648    | 0.658            | -                       | -                        | 0.643            |
| cpp        | 18    | 0.376    | 0.351            | -                       | -                        | 0.396            |
| csharp     | 6     | 0.416    | 0.372            | -                       | -                        | 0.437            |
| go         | 24    | 0.644    | 0.606            | 0.700                   | 0.700                    | 0.760            |
| java       | 10    | 0.739    | 0.718            | -                       | -                        | 0.703            |
| javascript | 14    | 0.742    | 0.740            | -                       | -                        | 0.869            |
| python     | 38    | 0.508    | 0.431            | -                       | -                        | 0.600            |
| python,cpp | 1     | 1.000    | 1.000            | -                       | -                        | 1.000            |
| rust       | 12    | 0.571    | 0.634            | -                       | -                        | 0.618            |
| typescript | 20    | 0.523    | 0.540            | -                       | -                        | 0.722            |

## Performance by MCP Benefit Score

| MCP Benefit Score   | Tasks | baseline | sourcegraph_base | sourcegraph_base_latest | sourcegraph_base_precise | sourcegraph_full |
| ------------------- | ----- | -------- | ---------------- | ----------------------- | ------------------------ | ---------------- |
| 0.0-0.4 (low)       | 0     | -        | -                | -                       | -                        | -                |
| 0.4-0.6 (medium)    | 34    | 0.480    | 0.400            | -                       | -                        | 0.617            |
| 0.6-0.8 (high)      | 69    | 0.571    | 0.540            | -                       | -                        | 0.667            |
| 0.8-1.0 (very high) | 52    | 0.619    | 0.665            | 0.700                   | 0.700                    | 0.644            |

