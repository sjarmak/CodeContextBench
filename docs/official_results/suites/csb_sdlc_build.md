# csb_sdlc_build

## Run/Config Summary

| Run | Config | Valid Tasks | Mean Reward | Pass Rate |
|---|---|---:|---:|---:|
| [build_haiku_20260222_125217__pre_sgenv_fix](../runs/build_haiku_20260222_125217__pre_sgenv_fix.md) | `baseline-local-artifact` | 1 | 0.700 | 1.000 |
| [csb_sdlc_build_haiku_20260227_034711](../runs/csb_sdlc_build_haiku_20260227_034711.md) | `baseline-local-direct` | 1 | 0.000 | 0.000 |
| [csb_sdlc_build_haiku_20260227_123839](../runs/csb_sdlc_build_haiku_20260227_123839.md) | `baseline-local-direct` | 8 | 0.641 | 1.000 |
| [csb_sdlc_build_haiku_20260227_123839](../runs/csb_sdlc_build_haiku_20260227_123839.md) | `mcp-remote-direct` | 7 | 0.571 | 1.000 |
| [csb_sdlc_build_haiku_20260228_025547](../runs/csb_sdlc_build_haiku_20260228_025547.md) | `baseline-local-direct` | 13 | 0.554 | 0.692 |
| [csb_sdlc_build_haiku_20260228_025547](../runs/csb_sdlc_build_haiku_20260228_025547.md) | `mcp-remote-direct` | 10 | 0.595 | 0.700 |
| [csb_sdlc_build_haiku_20260228_124521](../runs/csb_sdlc_build_haiku_20260228_124521.md) | `mcp-remote-direct` | 1 | 0.880 | 1.000 |
| [csb_sdlc_build_haiku_20260228_161037](../runs/csb_sdlc_build_haiku_20260228_161037.md) | `mcp-remote-direct` | 1 | 1.000 | 1.000 |
| [csb_sdlc_build_haiku_20260228_161452](../runs/csb_sdlc_build_haiku_20260228_161452.md) | `baseline-local-direct` | 1 | 1.000 | 1.000 |
| [csb_sdlc_build_haiku_20260228_161452](../runs/csb_sdlc_build_haiku_20260228_161452.md) | `mcp-remote-direct` | 1 | 0.000 | 0.000 |

## Tasks

| Task | Benchmark | Config | Status | Reward | Passed | Scorer Family | Output Contract | Runs | MCP Ratio |
|---|---|---|---|---:|---|---|---|---:|---:|
| [artifact_bl_k8s-noschedule-taint-feat-001](../tasks/build_haiku_20260222_125217__pre_sgenv_fix--baseline-local-artifact--artifact_bl_k8s-noschedule-taint-feat-001--ce726e8bce.html) | — | `baseline-local-artifact` | `passed` | 0.700 | `True` | `-` | `-` | 1 | 0.000 |
| [bustub-hyperloglog-impl-001](../tasks/csb_sdlc_build_haiku_20260228_025547--baseline-local-direct--bustub-hyperloglog-impl-001--448cfd3b42.html) | — | `baseline-local-direct` | `passed` | 0.500 | `True` | `checklist` | `unspecified` | 1 | 0.000 |
| [camel-fix-protocol-feat-001](../tasks/csb_sdlc_build_haiku_20260227_123839--baseline-local-direct--camel-fix-protocol-feat-001--b8252e24cf.html) | — | `baseline-local-direct` | `passed` | 0.220 | `None` | `ir_checklist` | `answer_json_bridge` | 2 | 0.000 |
| [mcp_camel-fix-protocol-feat-001_fWsOdb](../tasks/csb_sdlc_build_haiku_20260227_123839--mcp-remote-direct--mcp_camel-fix-protocol-feat-001_fWsOdb--6fe106ea51.html) | — | `mcp-remote-direct` | `passed` | 0.340 | `None` | `ir_checklist` | `answer_json_bridge` | 1 | 0.239 |
| [cgen-deps-install-001](../tasks/csb_sdlc_build_haiku_20260228_161452--baseline-local-direct--cgen-deps-install-001--0c886f68f6.html) | — | `baseline-local-direct` | `passed` | 1.000 | `True` | `-` | `-` | 3 | 0.000 |
| [mcp_cgen-deps-install-001_OhP8ju](../tasks/csb_sdlc_build_haiku_20260228_161452--mcp-remote-direct--mcp_cgen-deps-install-001_OhP8ju--0bfddd04db.html) | — | `mcp-remote-direct` | `failed` | 0.000 | `False` | `-` | `-` | 2 | 0.262 |
| [mcp_cgen-deps-install-001_qSYZF2](../tasks/csb_sdlc_build_haiku_20260228_161037--mcp-remote-direct--mcp_cgen-deps-install-001_qSYZF2--54e9b7e5ed.html) | — | `mcp-remote-direct` | `passed` | 1.000 | `True` | `-` | `-` | 2 | 0.378 |
| [codecoverage-deps-install-001](../tasks/csb_sdlc_build_haiku_20260228_025547--baseline-local-direct--codecoverage-deps-install-001--21f607d009.html) | — | `baseline-local-direct` | `failed` | 0.000 | `False` | `-` | `-` | 1 | 0.000 |
| [mcp_codecoverage-deps-install-001_x8rcGu](../tasks/csb_sdlc_build_haiku_20260228_025547--mcp-remote-direct--mcp_codecoverage-deps-install-001_x8rcGu--dd03ff519a.html) | — | `mcp-remote-direct` | `failed` | 0.000 | `False` | `-` | `-` | 1 | 0.533 |
| [dotenv-expand-deps-install-001](../tasks/csb_sdlc_build_haiku_20260228_025547--baseline-local-direct--dotenv-expand-deps-install-001--df787cdf1a.html) | — | `baseline-local-direct` | `passed` | 1.000 | `True` | `-` | `-` | 1 | 0.000 |
| [mcp_dotenv-expand-deps-install-001_gtBAHY](../tasks/csb_sdlc_build_haiku_20260228_025547--mcp-remote-direct--mcp_dotenv-expand-deps-install-001_gtBAHY--b00dd5fb2c.html) | — | `mcp-remote-direct` | `failed` | 0.000 | `False` | `-` | `-` | 1 | 0.282 |
| [dotnetkoans-deps-install-001](../tasks/csb_sdlc_build_haiku_20260228_025547--baseline-local-direct--dotnetkoans-deps-install-001--b7d9960b20.html) | — | `baseline-local-direct` | `failed` | 0.000 | `False` | `-` | `-` | 1 | 0.000 |
| [envoy-grpc-server-impl-001](../tasks/csb_sdlc_build_haiku_20260228_025547--baseline-local-direct--envoy-grpc-server-impl-001--b997995f10.html) | — | `baseline-local-direct` | `passed` | 0.440 | `True` | `f1` | `answer_json_bridge` | 1 | 0.000 |
| [mcp_envoy-grpc-server-impl-001_y67Otz](../tasks/csb_sdlc_build_haiku_20260228_025547--mcp-remote-direct--mcp_envoy-grpc-server-impl-001_y67Otz--5aaa9bfafd.html) | — | `mcp-remote-direct` | `passed` | 0.220 | `True` | `f1` | `answer_json_bridge` | 1 | 0.969 |
| [eslint-markdown-deps-install-001](../tasks/csb_sdlc_build_haiku_20260228_025547--baseline-local-direct--eslint-markdown-deps-install-001--884b3b176b.html) | — | `baseline-local-direct` | `passed` | 1.000 | `True` | `-` | `-` | 1 | 0.000 |
| [flink-pricing-window-feat-001](../tasks/csb_sdlc_build_haiku_20260227_123839--baseline-local-direct--flink-pricing-window-feat-001--fae8f7db01.html) | — | `baseline-local-direct` | `passed` | 0.480 | `None` | `ir_checklist` | `answer_json_bridge` | 1 | 0.000 |
| [mcp_flink-pricing-window-feat-001_qlRfCm](../tasks/csb_sdlc_build_haiku_20260227_123839--mcp-remote-direct--mcp_flink-pricing-window-feat-001_qlRfCm--a132121b12.html) | — | `mcp-remote-direct` | `passed` | 0.510 | `None` | `ir_checklist` | `answer_json_bridge` | 1 | 0.393 |
| [flipt-flagexists-refactor-001](../tasks/csb_sdlc_build_haiku_20260228_025547--baseline-local-direct--flipt-flagexists-refactor-001--0270661208.html) | — | `baseline-local-direct` | `passed` | 0.300 | `True` | `repo_state_heuristic` | `answer_json_bridge` | 1 | 0.000 |
| [mcp_flipt-flagexists-refactor-001_xDOm7g](../tasks/csb_sdlc_build_haiku_20260228_025547--mcp-remote-direct--mcp_flipt-flagexists-refactor-001_xDOm7g--09e3552e46.html) | — | `mcp-remote-direct` | `passed` | 0.850 | `True` | `repo_state_heuristic` | `answer_json_bridge` | 1 | 0.197 |
| [iamactionhunter-deps-install-001](../tasks/csb_sdlc_build_haiku_20260228_025547--baseline-local-direct--iamactionhunter-deps-install-001--5649e76f1b.html) | — | `baseline-local-direct` | `passed` | 1.000 | `True` | `-` | `-` | 1 | 0.000 |
| [mcp_iamactionhunter-deps-install-001_ePchSL](../tasks/csb_sdlc_build_haiku_20260228_025547--mcp-remote-direct--mcp_iamactionhunter-deps-install-001_ePchSL--c74ac6a8bd.html) | — | `mcp-remote-direct` | `passed` | 1.000 | `True` | `-` | `-` | 1 | 0.479 |
| [k8s-noschedule-taint-feat-001](../tasks/csb_sdlc_build_haiku_20260227_123839--baseline-local-direct--k8s-noschedule-taint-feat-001--3f5fd55e5f.html) | — | `baseline-local-direct` | `passed` | 0.700 | `None` | `repo_state_heuristic` | `answer_json_bridge` | 2 | 0.000 |
| [mcp_k8s-noschedule-taint-feat-001_A0pm5V](../tasks/csb_sdlc_build_haiku_20260227_123839--mcp-remote-direct--mcp_k8s-noschedule-taint-feat-001_A0pm5V--4fe1bd2167.html) | — | `mcp-remote-direct` | `passed` | 0.500 | `None` | `repo_state_heuristic` | `answer_json_bridge` | 1 | 0.248 |
| [k8s-score-normalizer-refac-001](../tasks/csb_sdlc_build_haiku_20260227_123839--baseline-local-direct--k8s-score-normalizer-refac-001--1fe8efee43.html) | — | `baseline-local-direct` | `passed` | 0.880 | `None` | `ir_checklist` | `answer_json_bridge` | 2 | 0.000 |
| [mcp_k8s-score-normalizer-refac-001_uBneDv](../tasks/csb_sdlc_build_haiku_20260227_123839--mcp-remote-direct--mcp_k8s-score-normalizer-refac-001_uBneDv--30fb8ada52.html) | — | `mcp-remote-direct` | `passed` | 0.800 | `None` | `ir_checklist` | `answer_json_bridge` | 1 | 0.081 |
| [kafka-batch-accumulator-refac-001](../tasks/csb_sdlc_build_haiku_20260227_123839--baseline-local-direct--kafka-batch-accumulator-refac-001--c2ae35494c.html) | — | `baseline-local-direct` | `passed` | 0.790 | `None` | `ir_checklist` | `answer_json_bridge` | 1 | 0.000 |
| [mcp_kafka-batch-accumulator-refac-001_03s0bF](../tasks/csb_sdlc_build_haiku_20260227_123839--mcp-remote-direct--mcp_kafka-batch-accumulator-refac-001_03s0bF--ec666b9b5f.html) | — | `mcp-remote-direct` | `passed` | 0.680 | `None` | `ir_checklist` | `answer_json_bridge` | 1 | 0.307 |
| [pcap-parser-deps-install-001](../tasks/csb_sdlc_build_haiku_20260228_025547--baseline-local-direct--pcap-parser-deps-install-001--3f72d8f59e.html) | — | `baseline-local-direct` | `passed` | 1.000 | `True` | `-` | `-` | 1 | 0.000 |
| [mcp_pcap-parser-deps-install-001_fgSA2o](../tasks/csb_sdlc_build_haiku_20260228_025547--mcp-remote-direct--mcp_pcap-parser-deps-install-001_fgSA2o--01198a6d55.html) | — | `mcp-remote-direct` | `passed` | 1.000 | `True` | `-` | `-` | 1 | 0.457 |
| [python-http-class-naming-refac-001](../tasks/csb_sdlc_build_haiku_20260228_025547--baseline-local-direct--python-http-class-naming-refac-001--658b02a4f7.html) | — | `baseline-local-direct` | `passed` | 0.960 | `True` | `semantic_similarity` | `answer_json_bridge` | 1 | 0.000 |
| [mcp_python-http-class-naming-refac-001_Z74daj](../tasks/csb_sdlc_build_haiku_20260228_025547--mcp-remote-direct--mcp_python-http-class-naming-refac-001_Z74daj--c1a79f935b.html) | — | `mcp-remote-direct` | `passed` | 0.880 | `True` | `semantic_similarity` | `answer_json_bridge` | 1 | 0.173 |
| [rust-subtype-relation-refac-001](../tasks/csb_sdlc_build_haiku_20260227_123839--baseline-local-direct--rust-subtype-relation-refac-001--e95226c9e9.html) | — | `baseline-local-direct` | `passed` | 0.760 | `None` | `-` | `-` | 1 | 0.000 |
| [mcp_rust-subtype-relation-refac-001_cwbXwY](../tasks/csb_sdlc_build_haiku_20260227_123839--mcp-remote-direct--mcp_rust-subtype-relation-refac-001_cwbXwY--4a09937ac7.html) | — | `mcp-remote-direct` | `passed` | 0.890 | `None` | `-` | `-` | 1 | 0.151 |
| [servo-scrollend-event-feat-001](../tasks/csb_sdlc_build_haiku_20260227_034711--baseline-local-direct--servo-scrollend-event-feat-001--a5c7451728.html) | — | `baseline-local-direct` | `failed` | 0.000 | `False` | `repo_state_heuristic` | `answer_json_bridge` | 1 | 0.000 |
| [similar-asserts-deps-install-001](../tasks/csb_sdlc_build_haiku_20260228_025547--baseline-local-direct--similar-asserts-deps-install-001--8350399c48.html) | — | `baseline-local-direct` | `passed` | 1.000 | `True` | `-` | `-` | 1 | 0.000 |
| [mcp_similar-asserts-deps-install-001_udUva4](../tasks/csb_sdlc_build_haiku_20260228_025547--mcp-remote-direct--mcp_similar-asserts-deps-install-001_udUva4--37234d2740.html) | — | `mcp-remote-direct` | `passed` | 1.000 | `True` | `-` | `-` | 1 | 0.333 |
| [strata-cds-tranche-feat-001](../tasks/csb_sdlc_build_haiku_20260227_123839--baseline-local-direct--strata-cds-tranche-feat-001--a13c9b6ded.html) | — | `baseline-local-direct` | `passed` | 0.590 | `None` | `ir_checklist` | `answer_json_bridge` | 1 | 0.000 |
| [mcp_strata-cds-tranche-feat-001_ink1qb](../tasks/csb_sdlc_build_haiku_20260227_123839--mcp-remote-direct--mcp_strata-cds-tranche-feat-001_ink1qb--6b1579a173.html) | — | `mcp-remote-direct` | `passed` | 0.280 | `None` | `ir_checklist` | `answer_json_bridge` | 1 | 0.500 |
| [strata-fx-european-refac-001](../tasks/csb_sdlc_build_haiku_20260227_123839--baseline-local-direct--strata-fx-european-refac-001--4c6780797b.html) | — | `baseline-local-direct` | `passed` | 0.710 | `None` | `ir_checklist` | `answer_json_bridge` | 1 | 0.000 |
| [mcp_strata-fx-european-refac-001_nd0ML5](../tasks/csb_sdlc_build_haiku_20260228_124521--mcp-remote-direct--mcp_strata-fx-european-refac-001_nd0ML5--9043760e64.html) | — | `mcp-remote-direct` | `passed` | 0.880 | `True` | `ir_checklist` | `answer_json_bridge` | 1 | 0.447 |
| [tensorrt-mxfp4-quant-feat-001](../tasks/csb_sdlc_build_haiku_20260228_025547--baseline-local-direct--tensorrt-mxfp4-quant-feat-001--127bde79d7.html) | — | `baseline-local-direct` | `failed` | 0.000 | `False` | `repo_state_heuristic` | `answer_json_bridge` | 1 | 0.000 |
| [mcp_tensorrt-mxfp4-quant-feat-001_QgJMEd](../tasks/csb_sdlc_build_haiku_20260228_025547--mcp-remote-direct--mcp_tensorrt-mxfp4-quant-feat-001_QgJMEd--10e876c420.html) | — | `mcp-remote-direct` | `passed` | 1.000 | `True` | `repo_state_heuristic` | `answer_json_bridge` | 1 | 0.314 |
| [vscode-stale-diagnostics-feat-001](../tasks/csb_sdlc_build_haiku_20260228_025547--baseline-local-direct--vscode-stale-diagnostics-feat-001--e1690fecd5.html) | — | `baseline-local-direct` | `failed` | 0.000 | `False` | `repo_state_heuristic` | `answer_json_bridge` | 1 | 0.000 |
| [mcp_vscode-stale-diagnostics-feat-001_UBNxW5](../tasks/csb_sdlc_build_haiku_20260228_025547--mcp-remote-direct--mcp_vscode-stale-diagnostics-feat-001_UBNxW5--a4d0fe807b.html) | — | `mcp-remote-direct` | `failed` | 0.000 | `False` | `repo_state_heuristic` | `answer_json_bridge` | 1 | 0.224 |

## Multi-Run Variance

Tasks with multiple valid runs (5 task/config pairs).

| Task | Benchmark | Config | Runs | Mean | Std | Individual Rewards |
|---|---|---|---:|---:|---:|---|
| camel-fix-protocol-feat-001 | — | `baseline-local-direct` | 2 | 0.170 | 0.071 | 0.120, 0.220 |
| cgen-deps-install-001 | — | `baseline-local-direct` | 3 | 1.000 | 0.000 | 1.000, 1.000, 1.000 |
| cgen-deps-install-001 | — | `mcp-remote-direct` | 2 | 0.500 | 0.707 | 1.000, 0.000 |
| k8s-noschedule-taint-feat-001 | — | `baseline-local-direct` | 2 | 0.700 | 0.000 | 0.700, 0.700 |
| k8s-score-normalizer-refac-001 | — | `baseline-local-direct` | 2 | 0.800 | 0.113 | 0.720, 0.880 |
