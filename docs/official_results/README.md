# Official Results Browser

This bundle is generated from `runs/official/` and includes only valid scored tasks (`passed`/`failed` with numeric reward).

Generated: `2026-03-02T21:30:49.001942+00:00`

## Local Browse

```bash
python3 scripts/export_official_results.py --serve
```

Suite-level views are deduplicated to the latest row per `suite + config + task_name`.
Historical reruns/backfills remain available in `data/official_results.json` under `all_tasks`.

## Suite/Config Summary

| Suite | Config | Valid Tasks | Min Required | Mean Reward | Pass Rate | Coverage |
|---|---|---:|---:|---:|---:|---|
| [ccb_mcp_migration](suites/ccb_mcp_migration.md) | `baseline-local-direct` | 26 | 41 | 0.317 | 0.808 | FLAG: below minimum |
| [ccb_mcp_migration](suites/ccb_mcp_migration.md) | `mcp-remote-direct` | 41 | 41 | 0.464 | 0.902 | ok |
| [csb_org_compliance](suites/csb_org_compliance.md) | `baseline-local-artifact` | 1 | 88 | 0.375 | 1.000 | FLAG: below minimum |
| [csb_org_compliance](suites/csb_org_compliance.md) | `baseline-local-direct` | 21 | 88 | 0.246 | 0.762 | FLAG: below minimum |
| [csb_org_compliance](suites/csb_org_compliance.md) | `mcp-remote-artifact` | 1 | 88 | 0.742 | 1.000 | FLAG: below minimum |
| [csb_org_compliance](suites/csb_org_compliance.md) | `mcp-remote-direct` | 88 | 88 | 0.347 | 0.886 | ok |
| [csb_org_crossorg](suites/csb_org_crossorg.md) | `baseline-local-artifact` | 4 | 61 | 0.406 | 0.750 | FLAG: below minimum |
| [csb_org_crossorg](suites/csb_org_crossorg.md) | `baseline-local-direct` | 17 | 61 | 0.188 | 0.647 | FLAG: below minimum |
| [csb_org_crossorg](suites/csb_org_crossorg.md) | `mcp-remote-artifact` | 4 | 61 | 0.586 | 0.750 | FLAG: below minimum |
| [csb_org_crossorg](suites/csb_org_crossorg.md) | `mcp-remote-direct` | 61 | 61 | 0.219 | 0.672 | ok |
| [csb_org_crossrepo](suites/csb_org_crossrepo.md) | `baseline-local-artifact` | 5 | 157 | 0.565 | 0.600 | FLAG: below minimum |
| [csb_org_crossrepo](suites/csb_org_crossrepo.md) | `baseline-local-direct` | 42 | 157 | 0.310 | 0.786 | FLAG: below minimum |
| [csb_org_crossrepo](suites/csb_org_crossrepo.md) | `mcp-remote-artifact` | 5 | 157 | 0.654 | 1.000 | FLAG: below minimum |
| [csb_org_crossrepo](suites/csb_org_crossrepo.md) | `mcp-remote-direct` | 157 | 157 | 0.377 | 0.847 | ok |
| [csb_org_domain](suites/csb_org_domain.md) | `baseline-local-artifact` | 3 | 77 | 0.000 | 0.000 | FLAG: below minimum |
| [csb_org_domain](suites/csb_org_domain.md) | `baseline-local-direct` | 20 | 77 | 0.347 | 0.900 | FLAG: below minimum |
| [csb_org_domain](suites/csb_org_domain.md) | `mcp-remote-artifact` | 3 | 77 | 0.529 | 1.000 | FLAG: below minimum |
| [csb_org_domain](suites/csb_org_domain.md) | `mcp-remote-direct` | 77 | 77 | 0.342 | 0.883 | ok |
| [csb_org_incident](suites/csb_org_incident.md) | `baseline-local-artifact` | 4 | 85 | 0.250 | 0.500 | FLAG: below minimum |
| [csb_org_incident](suites/csb_org_incident.md) | `baseline-local-direct` | 20 | 85 | 0.462 | 0.850 | FLAG: below minimum |
| [csb_org_incident](suites/csb_org_incident.md) | `mcp-remote-artifact` | 4 | 85 | 0.837 | 1.000 | FLAG: below minimum |
| [csb_org_incident](suites/csb_org_incident.md) | `mcp-remote-direct` | 85 | 85 | 0.613 | 0.953 | ok |
| [csb_org_migration](suites/csb_org_migration.md) | `baseline-local-direct` | 26 | 85 | 0.325 | 0.846 | FLAG: below minimum |
| [csb_org_migration](suites/csb_org_migration.md) | `mcp-remote-direct` | 85 | 85 | 0.452 | 0.835 | ok |
| [csb_org_onboarding](suites/csb_org_onboarding.md) | `baseline-local-artifact` | 5 | 155 | 0.200 | 0.200 | FLAG: below minimum |
| [csb_org_onboarding](suites/csb_org_onboarding.md) | `baseline-local-direct` | 28 | 155 | 0.631 | 0.821 | FLAG: below minimum |
| [csb_org_onboarding](suites/csb_org_onboarding.md) | `mcp-remote-artifact` | 5 | 155 | 0.875 | 1.000 | FLAG: below minimum |
| [csb_org_onboarding](suites/csb_org_onboarding.md) | `mcp-remote-direct` | 155 | 155 | 0.801 | 0.974 | ok |
| [csb_org_org](suites/csb_org_org.md) | `baseline-local-artifact` | 2 | 70 | 0.500 | 1.000 | FLAG: below minimum |
| [csb_org_org](suites/csb_org_org.md) | `baseline-local-direct` | 20 | 70 | 0.343 | 0.950 | FLAG: below minimum |
| [csb_org_org](suites/csb_org_org.md) | `mcp-remote-artifact` | 2 | 70 | 0.705 | 1.000 | FLAG: below minimum |
| [csb_org_org](suites/csb_org_org.md) | `mcp-remote-direct` | 70 | 70 | 0.356 | 0.800 | ok |
| [csb_org_platform](suites/csb_org_platform.md) | `baseline-local-direct` | 21 | 83 | 0.283 | 0.810 | FLAG: below minimum |
| [csb_org_platform](suites/csb_org_platform.md) | `mcp-remote-direct` | 83 | 83 | 0.300 | 0.952 | ok |
| [csb_org_security](suites/csb_org_security.md) | `baseline-local-artifact` | 25 | 93 | 0.283 | 0.720 | FLAG: below minimum |
| [csb_org_security](suites/csb_org_security.md) | `baseline-local-direct` | 24 | 93 | 0.486 | 0.875 | FLAG: below minimum |
| [csb_org_security](suites/csb_org_security.md) | `mcp-remote-artifact` | 26 | 93 | 0.563 | 1.000 | FLAG: below minimum |
| [csb_org_security](suites/csb_org_security.md) | `mcp-remote-direct` | 93 | 93 | 0.560 | 0.914 | ok |
| [csb_sdlc_build](suites/csb_sdlc_build.md) | `baseline-local-direct` | 23 | 23 | 0.601 | 0.826 | ok |
| [csb_sdlc_build](suites/csb_sdlc_build.md) | `mcp-remote-direct` | 20 | 23 | 0.592 | 0.800 | FLAG: below minimum |
| [csb_sdlc_debug](suites/csb_sdlc_debug.md) | `baseline-local-direct` | 20 | 20 | 0.688 | 1.000 | ok |
| [csb_sdlc_debug](suites/csb_sdlc_debug.md) | `mcp-remote-direct` | 31 | 20 | 0.508 | 0.774 | ok |
| [csb_sdlc_design](suites/csb_sdlc_design.md) | `baseline-local-direct` | 20 | 20 | 0.770 | 1.000 | ok |
| [csb_sdlc_design](suites/csb_sdlc_design.md) | `mcp-remote-direct` | 33 | 20 | 0.720 | 0.970 | ok |
| [csb_sdlc_document](suites/csb_sdlc_document.md) | `baseline-local-direct` | 20 | 20 | 0.845 | 1.000 | ok |
| [csb_sdlc_document](suites/csb_sdlc_document.md) | `mcp-remote-direct` | 44 | 20 | 0.875 | 1.000 | ok |
| [csb_sdlc_feature](suites/csb_sdlc_feature.md) | `baseline-local-direct` | 23 | 20 | 0.599 | 0.870 | ok |
| [csb_sdlc_feature](suites/csb_sdlc_feature.md) | `mcp-remote-direct` | 34 | 20 | 0.524 | 0.794 | ok |
| [csb_sdlc_fix](suites/csb_sdlc_fix.md) | `baseline-local-direct` | 26 | 25 | 0.496 | 0.654 | ok |
| [csb_sdlc_fix](suites/csb_sdlc_fix.md) | `mcp-remote-direct` | 98 | 25 | 0.570 | 0.714 | ok |
| [csb_sdlc_refactor](suites/csb_sdlc_refactor.md) | `baseline-local-direct` | 20 | 20 | 0.804 | 0.950 | ok |
| [csb_sdlc_refactor](suites/csb_sdlc_refactor.md) | `mcp-remote-direct` | 20 | 20 | 0.703 | 1.000 | ok |
| [csb_sdlc_secure](suites/csb_sdlc_secure.md) | `baseline-local-direct` | 20 | 20 | 0.712 | 1.000 | ok |
| [csb_sdlc_secure](suites/csb_sdlc_secure.md) | `mcp-remote-direct` | 24 | 20 | 0.707 | 0.958 | ok |
| [csb_sdlc_test](suites/csb_sdlc_test.md) | `baseline-local-direct` | 20 | 20 | 0.482 | 0.750 | ok |
| [csb_sdlc_test](suites/csb_sdlc_test.md) | `mcp-remote-direct` | 53 | 20 | 0.503 | 0.792 | ok |
| [csb_sdlc_understand](suites/csb_sdlc_understand.md) | `baseline-local-direct` | 34 | 20 | 0.902 | 0.971 | ok |
| [csb_sdlc_understand](suites/csb_sdlc_understand.md) | `mcp-remote-direct` | 48 | 20 | 0.873 | 0.979 | ok |

<details>
<summary>Run/Config Summary</summary>


| Run | Suite | Config | Valid Tasks | Mean Reward | Pass Rate |
|---|---|---|---:|---:|---:|
| [ccb_mcp_migration_haiku_20260302_175827](runs/ccb_mcp_migration_haiku_20260302_175827.md) | `ccb_mcp_migration` | `baseline-local-direct` | 26 | 0.318 | 0.808 |
| [ccb_mcp_migration_haiku_20260302_175827](runs/ccb_mcp_migration_haiku_20260302_175827.md) | `ccb_mcp_migration` | `mcp-remote-direct` | 25 | 0.317 | 0.840 |
| [ccb_mcp_migration_haiku_20260302_183602](runs/ccb_mcp_migration_haiku_20260302_183602.md) | `ccb_mcp_migration` | `baseline-local-direct` | 8 | 0.681 | 1.000 |
| [ccb_mcp_migration_haiku_20260302_183602](runs/ccb_mcp_migration_haiku_20260302_183602.md) | `ccb_mcp_migration` | `mcp-remote-direct` | 8 | 0.696 | 1.000 |
| [ccb_mcp_migration_haiku_20260302_183608](runs/ccb_mcp_migration_haiku_20260302_183608.md) | `ccb_mcp_migration` | `baseline-local-direct` | 8 | 0.659 | 1.000 |
| [ccb_mcp_migration_haiku_20260302_183608](runs/ccb_mcp_migration_haiku_20260302_183608.md) | `ccb_mcp_migration` | `mcp-remote-direct` | 8 | 0.694 | 1.000 |
| [csb_org_compliance_haiku_20260224_181919](runs/csb_org_compliance_haiku_20260224_181919.md) | `csb_org_compliance` | `mcp-remote-artifact` | 1 | 0.742 | 1.000 |
| [csb_org_compliance_haiku_20260225_011700](runs/csb_org_compliance_haiku_20260225_011700.md) | `csb_org_compliance` | `baseline-local-artifact` | 1 | 0.375 | 1.000 |
| [csb_org_compliance_haiku_20260226_035515_variance](runs/csb_org_compliance_haiku_20260226_035515_variance.md) | `csb_org_compliance` | `baseline-local-direct` | 1 | 0.386 | 1.000 |
| [csb_org_compliance_haiku_20260226_035515_variance](runs/csb_org_compliance_haiku_20260226_035515_variance.md) | `csb_org_compliance` | `mcp-remote-direct` | 3 | 0.489 | 1.000 |
| [csb_org_compliance_haiku_20260226_035617](runs/csb_org_compliance_haiku_20260226_035617.md) | `csb_org_compliance` | `baseline-local-direct` | 1 | 0.327 | 1.000 |
| [csb_org_compliance_haiku_20260226_035617](runs/csb_org_compliance_haiku_20260226_035617.md) | `csb_org_compliance` | `mcp-remote-direct` | 4 | 0.485 | 1.000 |
| [csb_org_compliance_haiku_20260226_035622_variance](runs/csb_org_compliance_haiku_20260226_035622_variance.md) | `csb_org_compliance` | `baseline-local-direct` | 1 | 0.373 | 1.000 |
| [csb_org_compliance_haiku_20260226_035622_variance](runs/csb_org_compliance_haiku_20260226_035622_variance.md) | `csb_org_compliance` | `mcp-remote-direct` | 4 | 0.590 | 1.000 |
| [csb_org_compliance_haiku_20260226_035628_variance](runs/csb_org_compliance_haiku_20260226_035628_variance.md) | `csb_org_compliance` | `baseline-local-direct` | 1 | 0.302 | 1.000 |
| [csb_org_compliance_haiku_20260226_035628_variance](runs/csb_org_compliance_haiku_20260226_035628_variance.md) | `csb_org_compliance` | `mcp-remote-direct` | 4 | 0.548 | 1.000 |
| [csb_org_compliance_haiku_20260226_035633_variance](runs/csb_org_compliance_haiku_20260226_035633_variance.md) | `csb_org_compliance` | `baseline-local-direct` | 1 | 0.356 | 1.000 |
| [csb_org_compliance_haiku_20260226_035633_variance](runs/csb_org_compliance_haiku_20260226_035633_variance.md) | `csb_org_compliance` | `mcp-remote-direct` | 4 | 0.638 | 1.000 |
| [csb_org_compliance_haiku_20260226_145828](runs/csb_org_compliance_haiku_20260226_145828.md) | `csb_org_compliance` | `baseline-local-direct` | 5 | 0.436 | 0.600 |
| [csb_org_compliance_haiku_20260226_205845](runs/csb_org_compliance_haiku_20260226_205845.md) | `csb_org_compliance` | `baseline-local-direct` | 3 | 0.700 | 1.000 |
| [csb_org_compliance_haiku_20260226_214446](runs/csb_org_compliance_haiku_20260226_214446.md) | `csb_org_compliance` | `baseline-local-direct` | 2 | 0.778 | 1.000 |
| [csb_org_compliance_haiku_20260226_221038](runs/csb_org_compliance_haiku_20260226_221038.md) | `csb_org_compliance` | `mcp-remote-direct` | 2 | 0.833 | 1.000 |
| [csb_org_compliance_haiku_20260228_011250](runs/csb_org_compliance_haiku_20260228_011250.md) | `csb_org_compliance` | `baseline-local-direct` | 7 | 0.652 | 1.000 |
| [csb_org_compliance_haiku_20260228_011250](runs/csb_org_compliance_haiku_20260228_011250.md) | `csb_org_compliance` | `mcp-remote-direct` | 7 | 0.597 | 1.000 |
| [csb_org_compliance_haiku_20260228_123206](runs/csb_org_compliance_haiku_20260228_123206.md) | `csb_org_compliance` | `baseline-local-direct` | 1 | 0.593 | 1.000 |
| [csb_org_compliance_haiku_20260228_133005](runs/csb_org_compliance_haiku_20260228_133005.md) | `csb_org_compliance` | `baseline-local-direct` | 1 | 0.655 | 1.000 |
| [csb_org_compliance_haiku_20260301_185444](runs/csb_org_compliance_haiku_20260301_185444.md) | `csb_org_compliance` | `baseline-local-direct` | 14 | 0.153 | 0.714 |
| [csb_org_compliance_haiku_20260301_185444](runs/csb_org_compliance_haiku_20260301_185444.md) | `csb_org_compliance` | `mcp-remote-direct` | 14 | 0.186 | 0.714 |
| [csb_org_compliance_haiku_20260302_014939](runs/csb_org_compliance_haiku_20260302_014939.md) | `csb_org_compliance` | `baseline-local-direct` | 12 | 0.179 | 0.833 |
| [csb_org_compliance_haiku_20260302_014939](runs/csb_org_compliance_haiku_20260302_014939.md) | `csb_org_compliance` | `mcp-remote-direct` | 12 | 0.194 | 0.833 |
| [csb_org_compliance_haiku_20260302_175821](runs/csb_org_compliance_haiku_20260302_175821.md) | `csb_org_compliance` | `baseline-local-direct` | 16 | 0.202 | 0.875 |
| [csb_org_compliance_haiku_20260302_175821](runs/csb_org_compliance_haiku_20260302_175821.md) | `csb_org_compliance` | `mcp-remote-direct` | 16 | 0.242 | 0.875 |
| [csb_org_compliance_haiku_20260302_175827](runs/csb_org_compliance_haiku_20260302_175827.md) | `csb_org_compliance` | `baseline-local-direct` | 16 | 0.204 | 0.812 |
| [csb_org_compliance_haiku_20260302_175827](runs/csb_org_compliance_haiku_20260302_175827.md) | `csb_org_compliance` | `mcp-remote-direct` | 16 | 0.248 | 0.875 |
| [csb_org_compliance_haiku_20260302_183602](runs/csb_org_compliance_haiku_20260302_183602.md) | `csb_org_compliance` | `baseline-local-direct` | 1 | 0.355 | 1.000 |
| [csb_org_compliance_haiku_20260302_183602](runs/csb_org_compliance_haiku_20260302_183602.md) | `csb_org_compliance` | `mcp-remote-direct` | 1 | 0.455 | 1.000 |
| [csb_org_compliance_haiku_20260302_183608](runs/csb_org_compliance_haiku_20260302_183608.md) | `csb_org_compliance` | `baseline-local-direct` | 1 | 0.351 | 1.000 |
| [csb_org_compliance_haiku_20260302_183608](runs/csb_org_compliance_haiku_20260302_183608.md) | `csb_org_compliance` | `mcp-remote-direct` | 1 | 0.917 | 1.000 |
| [csb_org_crossorg_haiku_022126](runs/csb_org_crossorg_haiku_022126.md) | `csb_org_crossorg` | `baseline-local-artifact` | 2 | 0.750 | 1.000 |
| [csb_org_crossorg_haiku_022126](runs/csb_org_crossorg_haiku_022126.md) | `csb_org_crossorg` | `mcp-remote-artifact` | 2 | 1.000 | 1.000 |
| [csb_org_crossorg_haiku_20260224_181919](runs/csb_org_crossorg_haiku_20260224_181919.md) | `csb_org_crossorg` | `mcp-remote-artifact` | 2 | 0.171 | 0.500 |
| [csb_org_crossorg_haiku_20260225_011700](runs/csb_org_crossorg_haiku_20260225_011700.md) | `csb_org_crossorg` | `baseline-local-artifact` | 2 | 0.062 | 0.500 |
| [csb_org_crossorg_haiku_20260226_035617](runs/csb_org_crossorg_haiku_20260226_035617.md) | `csb_org_crossorg` | `mcp-remote-direct` | 1 | 0.800 | 1.000 |
| [csb_org_crossorg_haiku_20260226_035622_variance](runs/csb_org_crossorg_haiku_20260226_035622_variance.md) | `csb_org_crossorg` | `mcp-remote-direct` | 1 | 0.680 | 1.000 |
| [csb_org_crossorg_haiku_20260226_035628_variance](runs/csb_org_crossorg_haiku_20260226_035628_variance.md) | `csb_org_crossorg` | `mcp-remote-direct` | 1 | 0.680 | 1.000 |
| [csb_org_crossorg_haiku_20260226_035633_variance](runs/csb_org_crossorg_haiku_20260226_035633_variance.md) | `csb_org_crossorg` | `mcp-remote-direct` | 1 | 0.711 | 1.000 |
| [csb_org_crossorg_haiku_20260226_145828](runs/csb_org_crossorg_haiku_20260226_145828.md) | `csb_org_crossorg` | `baseline-local-direct` | 1 | 0.335 | 1.000 |
| [csb_org_crossorg_haiku_20260226_205845](runs/csb_org_crossorg_haiku_20260226_205845.md) | `csb_org_crossorg` | `baseline-local-direct` | 1 | 0.658 | 1.000 |
| [csb_org_crossorg_haiku_20260228_005320](runs/csb_org_crossorg_haiku_20260228_005320.md) | `csb_org_crossorg` | `baseline-local-direct` | 5 | 0.330 | 0.800 |
| [csb_org_crossorg_haiku_20260228_005320](runs/csb_org_crossorg_haiku_20260228_005320.md) | `csb_org_crossorg` | `mcp-remote-direct` | 5 | 0.434 | 0.800 |
| [csb_org_crossorg_haiku_20260228_123206](runs/csb_org_crossorg_haiku_20260228_123206.md) | `csb_org_crossorg` | `baseline-local-direct` | 2 | 0.345 | 1.000 |
| [csb_org_crossorg_haiku_20260228_133005](runs/csb_org_crossorg_haiku_20260228_133005.md) | `csb_org_crossorg` | `baseline-local-direct` | 2 | 0.334 | 1.000 |
| [csb_org_crossorg_haiku_20260302_014939](runs/csb_org_crossorg_haiku_20260302_014939.md) | `csb_org_crossorg` | `baseline-local-direct` | 12 | 0.107 | 0.583 |
| [csb_org_crossorg_haiku_20260302_014939](runs/csb_org_crossorg_haiku_20260302_014939.md) | `csb_org_crossorg` | `mcp-remote-direct` | 12 | 0.181 | 0.667 |
| [csb_org_crossorg_haiku_20260302_034936](runs/csb_org_crossorg_haiku_20260302_034936.md) | `csb_org_crossorg` | `baseline-local-direct` | 12 | 0.103 | 0.500 |
| [csb_org_crossorg_haiku_20260302_034936](runs/csb_org_crossorg_haiku_20260302_034936.md) | `csb_org_crossorg` | `mcp-remote-direct` | 12 | 0.096 | 0.500 |
| [csb_org_crossorg_haiku_20260302_175821](runs/csb_org_crossorg_haiku_20260302_175821.md) | `csb_org_crossorg` | `baseline-local-direct` | 14 | 0.144 | 0.714 |
| [csb_org_crossorg_haiku_20260302_175821](runs/csb_org_crossorg_haiku_20260302_175821.md) | `csb_org_crossorg` | `mcp-remote-direct` | 14 | 0.184 | 0.714 |
| [csb_org_crossorg_haiku_20260302_175827](runs/csb_org_crossorg_haiku_20260302_175827.md) | `csb_org_crossorg` | `baseline-local-direct` | 14 | 0.161 | 0.643 |
| [csb_org_crossorg_haiku_20260302_175827](runs/csb_org_crossorg_haiku_20260302_175827.md) | `csb_org_crossorg` | `mcp-remote-direct` | 14 | 0.175 | 0.643 |
| [csb_org_crossrepo_haiku_20260226_035617](runs/csb_org_crossrepo_haiku_20260226_035617.md) | `csb_org_crossrepo` | `mcp-remote-direct` | 1 | 0.767 | 1.000 |
| [csb_org_crossrepo_haiku_20260226_035622_variance](runs/csb_org_crossrepo_haiku_20260226_035622_variance.md) | `csb_org_crossrepo` | `mcp-remote-direct` | 1 | 0.644 | 1.000 |
| [csb_org_crossrepo_haiku_20260226_035628_variance](runs/csb_org_crossrepo_haiku_20260226_035628_variance.md) | `csb_org_crossrepo` | `mcp-remote-direct` | 1 | 0.767 | 1.000 |
| [csb_org_crossrepo_haiku_20260226_035633_variance](runs/csb_org_crossrepo_haiku_20260226_035633_variance.md) | `csb_org_crossrepo` | `mcp-remote-direct` | 1 | 0.850 | 1.000 |
| [csb_org_crossrepo_haiku_20260226_145828](runs/csb_org_crossrepo_haiku_20260226_145828.md) | `csb_org_crossrepo` | `baseline-local-direct` | 1 | 0.900 | 1.000 |
| [csb_org_crossrepo_haiku_20260226_205845](runs/csb_org_crossrepo_haiku_20260226_205845.md) | `csb_org_crossrepo` | `baseline-local-direct` | 1 | 0.867 | 1.000 |
| [csb_org_crossrepo_haiku_20260228_005303](runs/csb_org_crossrepo_haiku_20260228_005303.md) | `csb_org_crossrepo` | `baseline-local-direct` | 1 | 0.850 | 1.000 |
| [csb_org_crossrepo_haiku_20260228_005303](runs/csb_org_crossrepo_haiku_20260228_005303.md) | `csb_org_crossrepo` | `mcp-remote-direct` | 1 | 0.633 | 1.000 |
| [csb_org_crossrepo_haiku_20260301_191250](runs/csb_org_crossrepo_haiku_20260301_191250.md) | `csb_org_crossrepo` | `baseline-local-direct` | 11 | 0.253 | 1.000 |
| [csb_org_crossrepo_haiku_20260301_191250](runs/csb_org_crossrepo_haiku_20260301_191250.md) | `csb_org_crossrepo` | `mcp-remote-direct` | 11 | 0.250 | 1.000 |
| [csb_org_crossrepo_haiku_20260301_201320](runs/csb_org_crossrepo_haiku_20260301_201320.md) | `csb_org_crossrepo` | `baseline-local-direct` | 6 | 0.040 | 0.333 |
| [csb_org_crossrepo_haiku_20260301_201320](runs/csb_org_crossrepo_haiku_20260301_201320.md) | `csb_org_crossrepo` | `mcp-remote-direct` | 6 | 0.049 | 0.333 |
| [csb_org_crossrepo_haiku_20260302_014939](runs/csb_org_crossrepo_haiku_20260302_014939.md) | `csb_org_crossrepo` | `baseline-local-direct` | 11 | 0.293 | 1.000 |
| [csb_org_crossrepo_haiku_20260302_014939](runs/csb_org_crossrepo_haiku_20260302_014939.md) | `csb_org_crossrepo` | `mcp-remote-direct` | 11 | 0.291 | 1.000 |
| [csb_org_crossrepo_haiku_20260302_034936](runs/csb_org_crossrepo_haiku_20260302_034936.md) | `csb_org_crossrepo` | `baseline-local-direct` | 5 | 0.253 | 1.000 |
| [csb_org_crossrepo_haiku_20260302_034936](runs/csb_org_crossrepo_haiku_20260302_034936.md) | `csb_org_crossrepo` | `mcp-remote-direct` | 5 | 0.250 | 1.000 |
| [csb_org_crossrepo_haiku_20260302_175821](runs/csb_org_crossrepo_haiku_20260302_175821.md) | `csb_org_crossrepo` | `baseline-local-direct` | 13 | 0.259 | 1.000 |
| [csb_org_crossrepo_haiku_20260302_175821](runs/csb_org_crossrepo_haiku_20260302_175821.md) | `csb_org_crossrepo` | `mcp-remote-direct` | 13 | 0.227 | 1.000 |
| [csb_org_crossrepo_haiku_20260302_175827](runs/csb_org_crossrepo_haiku_20260302_175827.md) | `csb_org_crossrepo` | `baseline-local-direct` | 13 | 0.271 | 1.000 |
| [csb_org_crossrepo_haiku_20260302_175827](runs/csb_org_crossrepo_haiku_20260302_175827.md) | `csb_org_crossrepo` | `mcp-remote-direct` | 13 | 0.265 | 1.000 |
| [csb_org_crossrepo_tracing_haiku_022126](runs/csb_org_crossrepo_tracing_haiku_022126.md) | `csb_org_crossrepo` | `baseline-local-artifact` | 3 | 0.941 | 1.000 |
| [csb_org_crossrepo_tracing_haiku_022126](runs/csb_org_crossrepo_tracing_haiku_022126.md) | `csb_org_crossrepo` | `mcp-remote-artifact` | 3 | 0.899 | 1.000 |
| [csb_org_crossrepo_tracing_haiku_20260224_181919](runs/csb_org_crossrepo_tracing_haiku_20260224_181919.md) | `csb_org_crossrepo` | `mcp-remote-artifact` | 2 | 0.287 | 1.000 |
| [csb_org_crossrepo_tracing_haiku_20260225_011700](runs/csb_org_crossrepo_tracing_haiku_20260225_011700.md) | `csb_org_crossrepo` | `baseline-local-artifact` | 2 | 0.000 | 0.000 |
| [csb_org_crossrepo_tracing_haiku_20260226_035617](runs/csb_org_crossrepo_tracing_haiku_20260226_035617.md) | `csb_org_crossrepo` | `mcp-remote-direct` | 3 | 0.669 | 1.000 |
| [csb_org_crossrepo_tracing_haiku_20260226_035622_variance](runs/csb_org_crossrepo_tracing_haiku_20260226_035622_variance.md) | `csb_org_crossrepo` | `mcp-remote-direct` | 3 | 0.762 | 1.000 |
| [csb_org_crossrepo_tracing_haiku_20260226_035628_variance](runs/csb_org_crossrepo_tracing_haiku_20260226_035628_variance.md) | `csb_org_crossrepo` | `mcp-remote-direct` | 3 | 0.756 | 1.000 |
| [csb_org_crossrepo_tracing_haiku_20260226_035633_variance](runs/csb_org_crossrepo_tracing_haiku_20260226_035633_variance.md) | `csb_org_crossrepo` | `mcp-remote-direct` | 3 | 0.595 | 1.000 |
| [csb_org_crossrepo_tracing_haiku_20260226_145828](runs/csb_org_crossrepo_tracing_haiku_20260226_145828.md) | `csb_org_crossrepo` | `baseline-local-direct` | 4 | 0.525 | 0.750 |
| [csb_org_crossrepo_tracing_haiku_20260226_205845](runs/csb_org_crossrepo_tracing_haiku_20260226_205845.md) | `csb_org_crossrepo` | `baseline-local-direct` | 3 | 0.722 | 1.000 |
| [csb_org_crossrepo_tracing_haiku_20260226_214446](runs/csb_org_crossrepo_tracing_haiku_20260226_214446.md) | `csb_org_crossrepo` | `baseline-local-direct` | 1 | 0.571 | 1.000 |
| [csb_org_crossrepo_tracing_haiku_20260226_221038](runs/csb_org_crossrepo_tracing_haiku_20260226_221038.md) | `csb_org_crossrepo` | `mcp-remote-direct` | 1 | 0.800 | 1.000 |
| [csb_org_crossrepo_tracing_haiku_20260228_022542](runs/csb_org_crossrepo_tracing_haiku_20260228_022542.md) | `csb_org_crossrepo` | `baseline-local-direct` | 9 | 0.538 | 0.778 |
| [csb_org_crossrepo_tracing_haiku_20260228_025547](runs/csb_org_crossrepo_tracing_haiku_20260228_025547.md) | `csb_org_crossrepo` | `baseline-local-direct` | 2 | 0.096 | 0.500 |
| [csb_org_crossrepo_tracing_haiku_20260228_025547](runs/csb_org_crossrepo_tracing_haiku_20260228_025547.md) | `csb_org_crossrepo` | `mcp-remote-direct` | 2 | 0.204 | 0.500 |
| [csb_org_crossrepo_tracing_haiku_20260228_123206](runs/csb_org_crossrepo_tracing_haiku_20260228_123206.md) | `csb_org_crossrepo` | `baseline-local-direct` | 2 | 0.195 | 1.000 |
| [csb_org_crossrepo_tracing_haiku_20260228_124521](runs/csb_org_crossrepo_tracing_haiku_20260228_124521.md) | `csb_org_crossrepo` | `mcp-remote-direct` | 3 | 1.000 | 1.000 |
| [csb_org_crossrepo_tracing_haiku_20260301_191250](runs/csb_org_crossrepo_tracing_haiku_20260301_191250.md) | `csb_org_crossrepo` | `baseline-local-direct` | 9 | 0.075 | 0.556 |
| [csb_org_crossrepo_tracing_haiku_20260301_191250](runs/csb_org_crossrepo_tracing_haiku_20260301_191250.md) | `csb_org_crossrepo` | `mcp-remote-direct` | 9 | 0.080 | 0.556 |
| [csb_org_crossrepo_tracing_haiku_20260301_195739](runs/csb_org_crossrepo_tracing_haiku_20260301_195739.md) | `csb_org_crossrepo` | `baseline-local-direct` | 11 | 0.069 | 0.545 |
| [csb_org_crossrepo_tracing_haiku_20260301_195739](runs/csb_org_crossrepo_tracing_haiku_20260301_195739.md) | `csb_org_crossrepo` | `mcp-remote-direct` | 11 | 0.081 | 0.545 |
| [csb_org_crossrepo_tracing_haiku_20260301_231457](runs/csb_org_crossrepo_tracing_haiku_20260301_231457.md) | `csb_org_crossrepo` | `baseline-local-direct` | 2 | 0.819 | 1.000 |
| [csb_org_crossrepo_tracing_haiku_20260301_231457](runs/csb_org_crossrepo_tracing_haiku_20260301_231457.md) | `csb_org_crossrepo` | `mcp-remote-direct` | 2 | 0.818 | 1.000 |
| [csb_org_crossrepo_tracing_haiku_20260302_013655](runs/csb_org_crossrepo_tracing_haiku_20260302_013655.md) | `csb_org_crossrepo` | `mcp-remote-direct` | 1 | 0.333 | 1.000 |
| [csb_org_crossrepo_tracing_haiku_20260302_014939](runs/csb_org_crossrepo_tracing_haiku_20260302_014939.md) | `csb_org_crossrepo` | `baseline-local-direct` | 4 | 0.509 | 0.750 |
| [csb_org_crossrepo_tracing_haiku_20260302_014939](runs/csb_org_crossrepo_tracing_haiku_20260302_014939.md) | `csb_org_crossrepo` | `mcp-remote-direct` | 4 | 0.427 | 0.750 |
| [csb_org_crossrepo_tracing_haiku_20260302_022538](runs/csb_org_crossrepo_tracing_haiku_20260302_022538.md) | `csb_org_crossrepo` | `baseline-local-direct` | 2 | 0.875 | 1.000 |
| [csb_org_crossrepo_tracing_haiku_20260302_022538](runs/csb_org_crossrepo_tracing_haiku_20260302_022538.md) | `csb_org_crossrepo` | `mcp-remote-direct` | 2 | 0.834 | 1.000 |
| [csb_org_crossrepo_tracing_haiku_20260302_022540](runs/csb_org_crossrepo_tracing_haiku_20260302_022540.md) | `csb_org_crossrepo` | `mcp-remote-direct` | 1 | 0.500 | 1.000 |
| [csb_org_crossrepo_tracing_haiku_20260302_175821](runs/csb_org_crossrepo_tracing_haiku_20260302_175821.md) | `csb_org_crossrepo` | `baseline-local-direct` | 17 | 0.227 | 0.588 |
| [csb_org_crossrepo_tracing_haiku_20260302_175821](runs/csb_org_crossrepo_tracing_haiku_20260302_175821.md) | `csb_org_crossrepo` | `mcp-remote-direct` | 18 | 0.353 | 0.778 |
| [csb_org_crossrepo_tracing_haiku_20260302_175827](runs/csb_org_crossrepo_tracing_haiku_20260302_175827.md) | `csb_org_crossrepo` | `baseline-local-direct` | 18 | 0.306 | 0.722 |
| [csb_org_crossrepo_tracing_haiku_20260302_175827](runs/csb_org_crossrepo_tracing_haiku_20260302_175827.md) | `csb_org_crossrepo` | `mcp-remote-direct` | 17 | 0.349 | 0.706 |
| [csb_org_crossrepo_tracing_haiku_20260302_183602](runs/csb_org_crossrepo_tracing_haiku_20260302_183602.md) | `csb_org_crossrepo` | `baseline-local-direct` | 5 | 0.841 | 1.000 |
| [csb_org_crossrepo_tracing_haiku_20260302_183602](runs/csb_org_crossrepo_tracing_haiku_20260302_183602.md) | `csb_org_crossrepo` | `mcp-remote-direct` | 5 | 0.914 | 1.000 |
| [csb_org_crossrepo_tracing_haiku_20260302_183608](runs/csb_org_crossrepo_tracing_haiku_20260302_183608.md) | `csb_org_crossrepo` | `baseline-local-direct` | 5 | 0.865 | 1.000 |
| [csb_org_crossrepo_tracing_haiku_20260302_183608](runs/csb_org_crossrepo_tracing_haiku_20260302_183608.md) | `csb_org_crossrepo` | `mcp-remote-direct` | 5 | 0.956 | 1.000 |
| [csb_org_domain_haiku_20260224_181919](runs/csb_org_domain_haiku_20260224_181919.md) | `csb_org_domain` | `mcp-remote-artifact` | 3 | 0.529 | 1.000 |
| [csb_org_domain_haiku_20260225_011700](runs/csb_org_domain_haiku_20260225_011700.md) | `csb_org_domain` | `baseline-local-artifact` | 3 | 0.000 | 0.000 |
| [csb_org_domain_haiku_20260226_035617](runs/csb_org_domain_haiku_20260226_035617.md) | `csb_org_domain` | `mcp-remote-direct` | 6 | 0.559 | 1.000 |
| [csb_org_domain_haiku_20260226_035622_variance](runs/csb_org_domain_haiku_20260226_035622_variance.md) | `csb_org_domain` | `mcp-remote-direct` | 6 | 0.508 | 1.000 |
| [csb_org_domain_haiku_20260226_035628_variance](runs/csb_org_domain_haiku_20260226_035628_variance.md) | `csb_org_domain` | `mcp-remote-direct` | 6 | 0.627 | 1.000 |
| [csb_org_domain_haiku_20260226_035633_variance](runs/csb_org_domain_haiku_20260226_035633_variance.md) | `csb_org_domain` | `mcp-remote-direct` | 6 | 0.543 | 1.000 |
| [csb_org_domain_haiku_20260226_145828](runs/csb_org_domain_haiku_20260226_145828.md) | `csb_org_domain` | `baseline-local-direct` | 6 | 0.618 | 1.000 |
| [csb_org_domain_haiku_20260226_205845](runs/csb_org_domain_haiku_20260226_205845.md) | `csb_org_domain` | `baseline-local-direct` | 6 | 0.604 | 1.000 |
| [csb_org_domain_haiku_20260226_222632](runs/csb_org_domain_haiku_20260226_222632.md) | `csb_org_domain` | `baseline-local-direct` | 1 | 0.800 | 1.000 |
| [csb_org_domain_haiku_20260226_222632](runs/csb_org_domain_haiku_20260226_222632.md) | `csb_org_domain` | `mcp-remote-direct` | 1 | 0.800 | 1.000 |
| [csb_org_domain_haiku_20260226_224414](runs/csb_org_domain_haiku_20260226_224414.md) | `csb_org_domain` | `baseline-local-direct` | 1 | 0.800 | 1.000 |
| [csb_org_domain_haiku_20260226_224414](runs/csb_org_domain_haiku_20260226_224414.md) | `csb_org_domain` | `mcp-remote-direct` | 1 | 0.800 | 1.000 |
| [csb_org_domain_haiku_20260228_021254](runs/csb_org_domain_haiku_20260228_021254.md) | `csb_org_domain` | `baseline-local-direct` | 10 | 0.567 | 1.000 |
| [csb_org_domain_haiku_20260228_025547](runs/csb_org_domain_haiku_20260228_025547.md) | `csb_org_domain` | `baseline-local-direct` | 3 | 0.418 | 1.000 |
| [csb_org_domain_haiku_20260228_025547](runs/csb_org_domain_haiku_20260228_025547.md) | `csb_org_domain` | `mcp-remote-direct` | 3 | 0.444 | 1.000 |
| [csb_org_domain_haiku_20260228_123206](runs/csb_org_domain_haiku_20260228_123206.md) | `csb_org_domain` | `baseline-local-direct` | 3 | 0.424 | 1.000 |
| [csb_org_domain_haiku_20260301_191250](runs/csb_org_domain_haiku_20260301_191250.md) | `csb_org_domain` | `baseline-local-direct` | 8 | 0.186 | 0.875 |
| [csb_org_domain_haiku_20260301_191250](runs/csb_org_domain_haiku_20260301_191250.md) | `csb_org_domain` | `mcp-remote-direct` | 8 | 0.184 | 0.875 |
| [csb_org_domain_haiku_20260301_195739](runs/csb_org_domain_haiku_20260301_195739.md) | `csb_org_domain` | `baseline-local-direct` | 10 | 0.132 | 0.800 |
| [csb_org_domain_haiku_20260301_195739](runs/csb_org_domain_haiku_20260301_195739.md) | `csb_org_domain` | `mcp-remote-direct` | 10 | 0.159 | 0.800 |
| [csb_org_domain_haiku_20260302_014939](runs/csb_org_domain_haiku_20260302_014939.md) | `csb_org_domain` | `baseline-local-direct` | 2 | 0.080 | 0.500 |
| [csb_org_domain_haiku_20260302_014939](runs/csb_org_domain_haiku_20260302_014939.md) | `csb_org_domain` | `mcp-remote-direct` | 2 | 0.000 | 0.000 |
| [csb_org_domain_haiku_20260302_175821](runs/csb_org_domain_haiku_20260302_175821.md) | `csb_org_domain` | `baseline-local-direct` | 14 | 0.256 | 0.857 |
| [csb_org_domain_haiku_20260302_175821](runs/csb_org_domain_haiku_20260302_175821.md) | `csb_org_domain` | `mcp-remote-direct` | 14 | 0.257 | 0.929 |
| [csb_org_domain_haiku_20260302_175827](runs/csb_org_domain_haiku_20260302_175827.md) | `csb_org_domain` | `baseline-local-direct` | 13 | 0.222 | 0.923 |
| [csb_org_domain_haiku_20260302_175827](runs/csb_org_domain_haiku_20260302_175827.md) | `csb_org_domain` | `mcp-remote-direct` | 14 | 0.237 | 0.786 |
| [csb_org_incident_haiku_022126](runs/csb_org_incident_haiku_022126.md) | `csb_org_incident` | `baseline-local-artifact` | 1 | 0.500 | 1.000 |
| [csb_org_incident_haiku_022126](runs/csb_org_incident_haiku_022126.md) | `csb_org_incident` | `mcp-remote-artifact` | 1 | 1.000 | 1.000 |
| [csb_org_incident_haiku_20260224_181919](runs/csb_org_incident_haiku_20260224_181919.md) | `csb_org_incident` | `mcp-remote-artifact` | 3 | 0.782 | 1.000 |
| [csb_org_incident_haiku_20260225_011700](runs/csb_org_incident_haiku_20260225_011700.md) | `csb_org_incident` | `baseline-local-artifact` | 3 | 0.167 | 0.333 |
| [csb_org_incident_haiku_20260226_035617](runs/csb_org_incident_haiku_20260226_035617.md) | `csb_org_incident` | `mcp-remote-direct` | 6 | 0.753 | 1.000 |
| [csb_org_incident_haiku_20260226_035622_variance](runs/csb_org_incident_haiku_20260226_035622_variance.md) | `csb_org_incident` | `mcp-remote-direct` | 6 | 0.632 | 1.000 |
| [csb_org_incident_haiku_20260226_035628_variance](runs/csb_org_incident_haiku_20260226_035628_variance.md) | `csb_org_incident` | `mcp-remote-direct` | 6 | 0.661 | 1.000 |
| [csb_org_incident_haiku_20260226_035633_variance](runs/csb_org_incident_haiku_20260226_035633_variance.md) | `csb_org_incident` | `mcp-remote-direct` | 6 | 0.669 | 1.000 |
| [csb_org_incident_haiku_20260226_145828](runs/csb_org_incident_haiku_20260226_145828.md) | `csb_org_incident` | `baseline-local-direct` | 6 | 0.672 | 1.000 |
| [csb_org_incident_haiku_20260226_205845](runs/csb_org_incident_haiku_20260226_205845.md) | `csb_org_incident` | `baseline-local-direct` | 6 | 0.722 | 1.000 |
| [csb_org_incident_haiku_20260226_224414](runs/csb_org_incident_haiku_20260226_224414.md) | `csb_org_incident` | `baseline-local-direct` | 1 | 0.667 | 1.000 |
| [csb_org_incident_haiku_20260226_224414](runs/csb_org_incident_haiku_20260226_224414.md) | `csb_org_incident` | `mcp-remote-direct` | 1 | 0.800 | 1.000 |
| [csb_org_incident_haiku_20260228_021904](runs/csb_org_incident_haiku_20260228_021904.md) | `csb_org_incident` | `baseline-local-direct` | 11 | 0.566 | 0.818 |
| [csb_org_incident_haiku_20260228_025547](runs/csb_org_incident_haiku_20260228_025547.md) | `csb_org_incident` | `baseline-local-direct` | 3 | 0.746 | 1.000 |
| [csb_org_incident_haiku_20260228_025547](runs/csb_org_incident_haiku_20260228_025547.md) | `csb_org_incident` | `mcp-remote-direct` | 3 | 0.779 | 1.000 |
| [csb_org_incident_haiku_20260228_123206](runs/csb_org_incident_haiku_20260228_123206.md) | `csb_org_incident` | `baseline-local-direct` | 3 | 0.723 | 1.000 |
| [csb_org_incident_haiku_20260228_124521](runs/csb_org_incident_haiku_20260228_124521.md) | `csb_org_incident` | `mcp-remote-direct` | 1 | 1.000 | 1.000 |
| [csb_org_incident_haiku_20260301_191250](runs/csb_org_incident_haiku_20260301_191250.md) | `csb_org_incident` | `baseline-local-direct` | 6 | 0.349 | 1.000 |
| [csb_org_incident_haiku_20260301_191250](runs/csb_org_incident_haiku_20260301_191250.md) | `csb_org_incident` | `mcp-remote-direct` | 6 | 0.357 | 1.000 |
| [csb_org_incident_haiku_20260301_195739](runs/csb_org_incident_haiku_20260301_195739.md) | `csb_org_incident` | `baseline-local-direct` | 9 | 0.314 | 0.778 |
| [csb_org_incident_haiku_20260301_195739](runs/csb_org_incident_haiku_20260301_195739.md) | `csb_org_incident` | `mcp-remote-direct` | 9 | 0.410 | 0.889 |
| [csb_org_incident_haiku_20260302_013655](runs/csb_org_incident_haiku_20260302_013655.md) | `csb_org_incident` | `mcp-remote-direct` | 1 | 1.000 | 1.000 |
| [csb_org_incident_haiku_20260302_014939](runs/csb_org_incident_haiku_20260302_014939.md) | `csb_org_incident` | `baseline-local-direct` | 3 | 0.222 | 0.333 |
| [csb_org_incident_haiku_20260302_014939](runs/csb_org_incident_haiku_20260302_014939.md) | `csb_org_incident` | `mcp-remote-direct` | 3 | 0.167 | 0.333 |
| [csb_org_incident_haiku_20260302_022540](runs/csb_org_incident_haiku_20260302_022540.md) | `csb_org_incident` | `mcp-remote-direct` | 1 | 0.933 | 1.000 |
| [csb_org_incident_haiku_20260302_175821](runs/csb_org_incident_haiku_20260302_175821.md) | `csb_org_incident` | `baseline-local-direct` | 15 | 0.466 | 0.800 |
| [csb_org_incident_haiku_20260302_175821](runs/csb_org_incident_haiku_20260302_175821.md) | `csb_org_incident` | `mcp-remote-direct` | 16 | 0.566 | 0.938 |
| [csb_org_incident_haiku_20260302_175827](runs/csb_org_incident_haiku_20260302_175827.md) | `csb_org_incident` | `baseline-local-direct` | 15 | 0.428 | 0.733 |
| [csb_org_incident_haiku_20260302_175827](runs/csb_org_incident_haiku_20260302_175827.md) | `csb_org_incident` | `mcp-remote-direct` | 14 | 0.622 | 1.000 |
| [csb_org_incident_haiku_20260302_183602](runs/csb_org_incident_haiku_20260302_183602.md) | `csb_org_incident` | `baseline-local-direct` | 3 | 0.630 | 0.667 |
| [csb_org_incident_haiku_20260302_183602](runs/csb_org_incident_haiku_20260302_183602.md) | `csb_org_incident` | `mcp-remote-direct` | 3 | 0.968 | 1.000 |
| [csb_org_incident_haiku_20260302_183608](runs/csb_org_incident_haiku_20260302_183608.md) | `csb_org_incident` | `baseline-local-direct` | 3 | 0.619 | 0.667 |
| [csb_org_incident_haiku_20260302_183608](runs/csb_org_incident_haiku_20260302_183608.md) | `csb_org_incident` | `mcp-remote-direct` | 3 | 0.929 | 1.000 |
| [csb_org_migration_haiku_20260226_035617](runs/csb_org_migration_haiku_20260226_035617.md) | `csb_org_migration` | `baseline-local-direct` | 1 | 1.000 | 1.000 |
| [csb_org_migration_haiku_20260226_035617](runs/csb_org_migration_haiku_20260226_035617.md) | `csb_org_migration` | `mcp-remote-direct` | 1 | 1.000 | 1.000 |
| [csb_org_migration_haiku_20260226_035622_variance](runs/csb_org_migration_haiku_20260226_035622_variance.md) | `csb_org_migration` | `baseline-local-direct` | 1 | 1.000 | 1.000 |
| [csb_org_migration_haiku_20260226_035622_variance](runs/csb_org_migration_haiku_20260226_035622_variance.md) | `csb_org_migration` | `mcp-remote-direct` | 1 | 1.000 | 1.000 |
| [csb_org_migration_haiku_20260226_035628_variance](runs/csb_org_migration_haiku_20260226_035628_variance.md) | `csb_org_migration` | `baseline-local-direct` | 1 | 1.000 | 1.000 |
| [csb_org_migration_haiku_20260226_035628_variance](runs/csb_org_migration_haiku_20260226_035628_variance.md) | `csb_org_migration` | `mcp-remote-direct` | 1 | 1.000 | 1.000 |
| [csb_org_migration_haiku_20260226_035633_variance](runs/csb_org_migration_haiku_20260226_035633_variance.md) | `csb_org_migration` | `baseline-local-direct` | 1 | 1.000 | 1.000 |
| [csb_org_migration_haiku_20260226_035633_variance](runs/csb_org_migration_haiku_20260226_035633_variance.md) | `csb_org_migration` | `mcp-remote-direct` | 1 | 1.000 | 1.000 |
| [csb_org_migration_haiku_20260226_145828](runs/csb_org_migration_haiku_20260226_145828.md) | `csb_org_migration` | `baseline-local-direct` | 5 | 0.033 | 0.400 |
| [csb_org_migration_haiku_20260226_214446](runs/csb_org_migration_haiku_20260226_214446.md) | `csb_org_migration` | `baseline-local-direct` | 3 | 0.930 | 1.000 |
| [csb_org_migration_haiku_20260226_221038](runs/csb_org_migration_haiku_20260226_221038.md) | `csb_org_migration` | `mcp-remote-direct` | 3 | 0.917 | 1.000 |
| [csb_org_migration_haiku_20260226_231458](runs/csb_org_migration_haiku_20260226_231458.md) | `csb_org_migration` | `baseline-local-direct` | 3 | 0.639 | 1.000 |
| [csb_org_migration_haiku_20260226_231458](runs/csb_org_migration_haiku_20260226_231458.md) | `csb_org_migration` | `mcp-remote-direct` | 3 | 0.771 | 1.000 |
| [csb_org_migration_haiku_20260228_011912](runs/csb_org_migration_haiku_20260228_011912.md) | `csb_org_migration` | `baseline-local-direct` | 7 | 0.801 | 1.000 |
| [csb_org_migration_haiku_20260228_011912](runs/csb_org_migration_haiku_20260228_011912.md) | `csb_org_migration` | `mcp-remote-direct` | 7 | 0.804 | 1.000 |
| [csb_org_migration_haiku_20260301_191250](runs/csb_org_migration_haiku_20260301_191250.md) | `csb_org_migration` | `baseline-local-direct` | 12 | 0.115 | 0.917 |
| [csb_org_migration_haiku_20260301_191250](runs/csb_org_migration_haiku_20260301_191250.md) | `csb_org_migration` | `mcp-remote-direct` | 12 | 0.135 | 0.833 |
| [csb_org_migration_haiku_20260301_195739](runs/csb_org_migration_haiku_20260301_195739.md) | `csb_org_migration` | `baseline-local-direct` | 13 | 0.100 | 0.692 |
| [csb_org_migration_haiku_20260301_195739](runs/csb_org_migration_haiku_20260301_195739.md) | `csb_org_migration` | `mcp-remote-direct` | 13 | 0.094 | 0.615 |
| [csb_org_migration_haiku_20260301_231457](runs/csb_org_migration_haiku_20260301_231457.md) | `csb_org_migration` | `baseline-local-direct` | 5 | 0.570 | 1.000 |
| [csb_org_migration_haiku_20260301_231457](runs/csb_org_migration_haiku_20260301_231457.md) | `csb_org_migration` | `mcp-remote-direct` | 6 | 0.632 | 1.000 |
| [csb_org_migration_haiku_20260301_235018](runs/csb_org_migration_haiku_20260301_235018.md) | `csb_org_migration` | `baseline-local-direct` | 1 | 0.741 | 1.000 |
| [csb_org_migration_haiku_20260302_014939](runs/csb_org_migration_haiku_20260302_014939.md) | `csb_org_migration` | `baseline-local-direct` | 7 | 0.492 | 0.857 |
| [csb_org_migration_haiku_20260302_014939](runs/csb_org_migration_haiku_20260302_014939.md) | `csb_org_migration` | `mcp-remote-direct` | 7 | 0.612 | 0.857 |
| [csb_org_migration_haiku_20260302_022538](runs/csb_org_migration_haiku_20260302_022538.md) | `csb_org_migration` | `baseline-local-direct` | 6 | 0.583 | 1.000 |
| [csb_org_migration_haiku_20260302_022538](runs/csb_org_migration_haiku_20260302_022538.md) | `csb_org_migration` | `mcp-remote-direct` | 6 | 0.765 | 1.000 |
| [csb_org_migration_haiku_20260302_175821](runs/csb_org_migration_haiku_20260302_175821.md) | `csb_org_migration` | `baseline-local-direct` | 25 | 0.335 | 0.840 |
| [csb_org_migration_haiku_20260302_175821](runs/csb_org_migration_haiku_20260302_175821.md) | `csb_org_migration` | `mcp-remote-direct` | 24 | 0.344 | 0.750 |
| [csb_org_onboarding_haiku_022126](runs/csb_org_onboarding_haiku_022126.md) | `csb_org_onboarding` | `baseline-local-artifact` | 1 | 1.000 | 1.000 |
| [csb_org_onboarding_haiku_022126](runs/csb_org_onboarding_haiku_022126.md) | `csb_org_onboarding` | `mcp-remote-artifact` | 1 | 1.000 | 1.000 |
| [csb_org_onboarding_haiku_20260224_181919](runs/csb_org_onboarding_haiku_20260224_181919.md) | `csb_org_onboarding` | `mcp-remote-artifact` | 4 | 0.843 | 1.000 |
| [csb_org_onboarding_haiku_20260225_011700](runs/csb_org_onboarding_haiku_20260225_011700.md) | `csb_org_onboarding` | `baseline-local-artifact` | 4 | 0.000 | 0.000 |
| [csb_org_onboarding_haiku_20260226_035617](runs/csb_org_onboarding_haiku_20260226_035617.md) | `csb_org_onboarding` | `mcp-remote-direct` | 4 | 0.501 | 1.000 |
| [csb_org_onboarding_haiku_20260226_035622_variance](runs/csb_org_onboarding_haiku_20260226_035622_variance.md) | `csb_org_onboarding` | `mcp-remote-direct` | 4 | 0.452 | 1.000 |
| [csb_org_onboarding_haiku_20260226_035628_variance](runs/csb_org_onboarding_haiku_20260226_035628_variance.md) | `csb_org_onboarding` | `mcp-remote-direct` | 4 | 0.550 | 1.000 |
| [csb_org_onboarding_haiku_20260226_035633_variance](runs/csb_org_onboarding_haiku_20260226_035633_variance.md) | `csb_org_onboarding` | `mcp-remote-direct` | 4 | 0.472 | 1.000 |
| [csb_org_onboarding_haiku_20260226_145828](runs/csb_org_onboarding_haiku_20260226_145828.md) | `csb_org_onboarding` | `baseline-local-direct` | 3 | 0.539 | 1.000 |
| [csb_org_onboarding_haiku_20260226_205845](runs/csb_org_onboarding_haiku_20260226_205845.md) | `csb_org_onboarding` | `baseline-local-direct` | 3 | 0.540 | 1.000 |
| [csb_org_onboarding_haiku_20260226_231458](runs/csb_org_onboarding_haiku_20260226_231458.md) | `csb_org_onboarding` | `baseline-local-direct` | 1 | 0.473 | 1.000 |
| [csb_org_onboarding_haiku_20260226_231458](runs/csb_org_onboarding_haiku_20260226_231458.md) | `csb_org_onboarding` | `mcp-remote-direct` | 1 | 0.432 | 1.000 |
| [csb_org_onboarding_haiku_20260227_132300](runs/csb_org_onboarding_haiku_20260227_132300.md) | `csb_org_onboarding` | `baseline-local-direct` | 14 | 0.936 | 1.000 |
| [csb_org_onboarding_haiku_20260227_132300](runs/csb_org_onboarding_haiku_20260227_132300.md) | `csb_org_onboarding` | `mcp-remote-direct` | 12 | 1.000 | 1.000 |
| [csb_org_onboarding_haiku_20260227_132304](runs/csb_org_onboarding_haiku_20260227_132304.md) | `csb_org_onboarding` | `baseline-local-direct` | 14 | 0.864 | 0.929 |
| [csb_org_onboarding_haiku_20260227_132304](runs/csb_org_onboarding_haiku_20260227_132304.md) | `csb_org_onboarding` | `mcp-remote-direct` | 12 | 1.000 | 1.000 |
| [csb_org_onboarding_haiku_20260228_023118](runs/csb_org_onboarding_haiku_20260228_023118.md) | `csb_org_onboarding` | `baseline-local-direct` | 25 | 0.784 | 0.960 |
| [csb_org_onboarding_haiku_20260228_025547](runs/csb_org_onboarding_haiku_20260228_025547.md) | `csb_org_onboarding` | `baseline-local-direct` | 4 | 0.843 | 1.000 |
| [csb_org_onboarding_haiku_20260228_025547](runs/csb_org_onboarding_haiku_20260228_025547.md) | `csb_org_onboarding` | `mcp-remote-direct` | 4 | 0.843 | 1.000 |
| [csb_org_onboarding_haiku_20260228_123206](runs/csb_org_onboarding_haiku_20260228_123206.md) | `csb_org_onboarding` | `baseline-local-direct` | 4 | 0.779 | 1.000 |
| [csb_org_onboarding_haiku_20260228_124521](runs/csb_org_onboarding_haiku_20260228_124521.md) | `csb_org_onboarding` | `mcp-remote-direct` | 17 | 0.931 | 1.000 |
| [csb_org_onboarding_haiku_20260301_191250](runs/csb_org_onboarding_haiku_20260301_191250.md) | `csb_org_onboarding` | `baseline-local-direct` | 2 | 0.008 | 0.500 |
| [csb_org_onboarding_haiku_20260301_191250](runs/csb_org_onboarding_haiku_20260301_191250.md) | `csb_org_onboarding` | `mcp-remote-direct` | 2 | 0.015 | 0.500 |
| [csb_org_onboarding_haiku_20260301_195739](runs/csb_org_onboarding_haiku_20260301_195739.md) | `csb_org_onboarding` | `baseline-local-direct` | 2 | 0.036 | 0.500 |
| [csb_org_onboarding_haiku_20260301_195739](runs/csb_org_onboarding_haiku_20260301_195739.md) | `csb_org_onboarding` | `mcp-remote-direct` | 2 | 0.015 | 0.500 |
| [csb_org_onboarding_haiku_20260301_231457](runs/csb_org_onboarding_haiku_20260301_231457.md) | `csb_org_onboarding` | `baseline-local-direct` | 8 | 0.626 | 0.875 |
| [csb_org_onboarding_haiku_20260301_231457](runs/csb_org_onboarding_haiku_20260301_231457.md) | `csb_org_onboarding` | `mcp-remote-direct` | 8 | 0.735 | 1.000 |
| [csb_org_onboarding_haiku_20260302_014939](runs/csb_org_onboarding_haiku_20260302_014939.md) | `csb_org_onboarding` | `baseline-local-direct` | 1 | 0.962 | 1.000 |
| [csb_org_onboarding_haiku_20260302_014939](runs/csb_org_onboarding_haiku_20260302_014939.md) | `csb_org_onboarding` | `mcp-remote-direct` | 1 | 1.000 | 1.000 |
| [csb_org_onboarding_haiku_20260302_022538](runs/csb_org_onboarding_haiku_20260302_022538.md) | `csb_org_onboarding` | `baseline-local-direct` | 1 | 0.928 | 1.000 |
| [csb_org_onboarding_haiku_20260302_022538](runs/csb_org_onboarding_haiku_20260302_022538.md) | `csb_org_onboarding` | `mcp-remote-direct` | 1 | 1.000 | 1.000 |
| [csb_org_onboarding_haiku_20260302_030627](runs/csb_org_onboarding_haiku_20260302_030627.md) | `csb_org_onboarding` | `mcp-remote-direct` | 2 | 1.000 | 1.000 |
| [csb_org_onboarding_haiku_20260302_175821](runs/csb_org_onboarding_haiku_20260302_175821.md) | `csb_org_onboarding` | `baseline-local-direct` | 18 | 0.823 | 0.944 |
| [csb_org_onboarding_haiku_20260302_175821](runs/csb_org_onboarding_haiku_20260302_175821.md) | `csb_org_onboarding` | `mcp-remote-direct` | 18 | 0.769 | 1.000 |
| [csb_org_onboarding_haiku_20260302_175827](runs/csb_org_onboarding_haiku_20260302_175827.md) | `csb_org_onboarding` | `baseline-local-direct` | 21 | 0.807 | 0.952 |
| [csb_org_onboarding_haiku_20260302_175827](runs/csb_org_onboarding_haiku_20260302_175827.md) | `csb_org_onboarding` | `mcp-remote-direct` | 19 | 0.734 | 0.895 |
| [csb_org_onboarding_haiku_20260302_183602](runs/csb_org_onboarding_haiku_20260302_183602.md) | `csb_org_onboarding` | `baseline-local-direct` | 18 | 0.882 | 0.944 |
| [csb_org_onboarding_haiku_20260302_183602](runs/csb_org_onboarding_haiku_20260302_183602.md) | `csb_org_onboarding` | `mcp-remote-direct` | 18 | 0.896 | 1.000 |
| [csb_org_onboarding_haiku_20260302_183608](runs/csb_org_onboarding_haiku_20260302_183608.md) | `csb_org_onboarding` | `baseline-local-direct` | 18 | 0.792 | 0.889 |
| [csb_org_onboarding_haiku_20260302_183608](runs/csb_org_onboarding_haiku_20260302_183608.md) | `csb_org_onboarding` | `mcp-remote-direct` | 18 | 0.917 | 1.000 |
| [csb_org_onboarding_haiku_20260302_210829](runs/csb_org_onboarding_haiku_20260302_210829.md) | `csb_org_onboarding` | `baseline-local-direct` | 1 | 0.000 | 0.000 |
| [csb_org_onboarding_haiku_20260302_210829](runs/csb_org_onboarding_haiku_20260302_210829.md) | `csb_org_onboarding` | `mcp-remote-direct` | 1 | 0.750 | 1.000 |
| [csb_org_onboarding_haiku_20260302_210835](runs/csb_org_onboarding_haiku_20260302_210835.md) | `csb_org_onboarding` | `baseline-local-direct` | 1 | 0.000 | 0.000 |
| [csb_org_onboarding_haiku_20260302_210835](runs/csb_org_onboarding_haiku_20260302_210835.md) | `csb_org_onboarding` | `mcp-remote-direct` | 1 | 0.500 | 1.000 |
| [csb_org_onboarding_haiku_20260302_210842](runs/csb_org_onboarding_haiku_20260302_210842.md) | `csb_org_onboarding` | `baseline-local-direct` | 1 | 0.000 | 0.000 |
| [csb_org_onboarding_haiku_20260302_210842](runs/csb_org_onboarding_haiku_20260302_210842.md) | `csb_org_onboarding` | `mcp-remote-direct` | 1 | 0.500 | 1.000 |
| [csb_org_onboarding_haiku_20260302_212645](runs/csb_org_onboarding_haiku_20260302_212645.md) | `csb_org_onboarding` | `baseline-local-direct` | 1 | 0.000 | 0.000 |
| [csb_org_onboarding_haiku_20260302_212645](runs/csb_org_onboarding_haiku_20260302_212645.md) | `csb_org_onboarding` | `mcp-remote-direct` | 1 | 0.432 | 1.000 |
| [csb_org_org_haiku_20260224_181919](runs/csb_org_org_haiku_20260224_181919.md) | `csb_org_org` | `mcp-remote-artifact` | 2 | 0.705 | 1.000 |
| [csb_org_org_haiku_20260225_011700](runs/csb_org_org_haiku_20260225_011700.md) | `csb_org_org` | `baseline-local-artifact` | 2 | 0.500 | 1.000 |
| [csb_org_org_haiku_20260226_035617](runs/csb_org_org_haiku_20260226_035617.md) | `csb_org_org` | `mcp-remote-direct` | 3 | 0.503 | 1.000 |
| [csb_org_org_haiku_20260226_035622_variance](runs/csb_org_org_haiku_20260226_035622_variance.md) | `csb_org_org` | `mcp-remote-direct` | 3 | 0.557 | 1.000 |
| [csb_org_org_haiku_20260226_035628_variance](runs/csb_org_org_haiku_20260226_035628_variance.md) | `csb_org_org` | `mcp-remote-direct` | 3 | 0.497 | 1.000 |
| [csb_org_org_haiku_20260226_035633_variance](runs/csb_org_org_haiku_20260226_035633_variance.md) | `csb_org_org` | `mcp-remote-direct` | 3 | 0.515 | 1.000 |
| [csb_org_org_haiku_20260226_145828](runs/csb_org_org_haiku_20260226_145828.md) | `csb_org_org` | `baseline-local-direct` | 3 | 0.385 | 1.000 |
| [csb_org_org_haiku_20260226_205845](runs/csb_org_org_haiku_20260226_205845.md) | `csb_org_org` | `baseline-local-direct` | 3 | 0.404 | 1.000 |
| [csb_org_org_haiku_20260228_010402](runs/csb_org_org_haiku_20260228_010402.md) | `csb_org_org` | `baseline-local-direct` | 5 | 0.543 | 1.000 |
| [csb_org_org_haiku_20260228_010402](runs/csb_org_org_haiku_20260228_010402.md) | `csb_org_org` | `mcp-remote-direct` | 5 | 0.592 | 1.000 |
| [csb_org_org_haiku_20260228_051032](runs/csb_org_org_haiku_20260228_051032.md) | `csb_org_org` | `baseline-local-direct` | 1 | 0.720 | 1.000 |
| [csb_org_org_haiku_20260228_123206](runs/csb_org_org_haiku_20260228_123206.md) | `csb_org_org` | `baseline-local-direct` | 2 | 0.683 | 1.000 |
| [csb_org_org_haiku_20260228_133005](runs/csb_org_org_haiku_20260228_133005.md) | `csb_org_org` | `baseline-local-direct` | 1 | 0.574 | 1.000 |
| [csb_org_org_haiku_20260301_191250](runs/csb_org_org_haiku_20260301_191250.md) | `csb_org_org` | `baseline-local-direct` | 13 | 0.000 | 0.000 |
| [csb_org_org_haiku_20260301_191250](runs/csb_org_org_haiku_20260301_191250.md) | `csb_org_org` | `mcp-remote-direct` | 13 | 0.000 | 0.000 |
| [csb_org_org_haiku_20260301_195739](runs/csb_org_org_haiku_20260301_195739.md) | `csb_org_org` | `baseline-local-direct` | 15 | 0.308 | 0.933 |
| [csb_org_org_haiku_20260301_195739](runs/csb_org_org_haiku_20260301_195739.md) | `csb_org_org` | `mcp-remote-direct` | 15 | 0.338 | 0.933 |
| [csb_org_org_haiku_20260302_014939](runs/csb_org_org_haiku_20260302_014939.md) | `csb_org_org` | `baseline-local-direct` | 2 | 0.282 | 1.000 |
| [csb_org_org_haiku_20260302_014939](runs/csb_org_org_haiku_20260302_014939.md) | `csb_org_org` | `mcp-remote-direct` | 2 | 0.274 | 1.000 |
| [csb_org_org_haiku_20260302_175821](runs/csb_org_org_haiku_20260302_175821.md) | `csb_org_org` | `baseline-local-direct` | 12 | 0.381 | 1.000 |
| [csb_org_org_haiku_20260302_175821](runs/csb_org_org_haiku_20260302_175821.md) | `csb_org_org` | `mcp-remote-direct` | 12 | 0.427 | 1.000 |
| [csb_org_org_haiku_20260302_175827](runs/csb_org_org_haiku_20260302_175827.md) | `csb_org_org` | `baseline-local-direct` | 11 | 0.402 | 0.909 |
| [csb_org_org_haiku_20260302_175827](runs/csb_org_org_haiku_20260302_175827.md) | `csb_org_org` | `mcp-remote-direct` | 11 | 0.454 | 1.000 |
| [csb_org_platform_haiku_20260226_035617](runs/csb_org_platform_haiku_20260226_035617.md) | `csb_org_platform` | `baseline-local-direct` | 2 | 0.744 | 1.000 |
| [csb_org_platform_haiku_20260226_035617](runs/csb_org_platform_haiku_20260226_035617.md) | `csb_org_platform` | `mcp-remote-direct` | 3 | 0.544 | 1.000 |
| [csb_org_platform_haiku_20260226_035622_variance](runs/csb_org_platform_haiku_20260226_035622_variance.md) | `csb_org_platform` | `baseline-local-direct` | 2 | 0.728 | 1.000 |
| [csb_org_platform_haiku_20260226_035622_variance](runs/csb_org_platform_haiku_20260226_035622_variance.md) | `csb_org_platform` | `mcp-remote-direct` | 3 | 0.572 | 1.000 |
| [csb_org_platform_haiku_20260226_035628_variance](runs/csb_org_platform_haiku_20260226_035628_variance.md) | `csb_org_platform` | `baseline-local-direct` | 2 | 0.744 | 1.000 |
| [csb_org_platform_haiku_20260226_035628_variance](runs/csb_org_platform_haiku_20260226_035628_variance.md) | `csb_org_platform` | `mcp-remote-direct` | 3 | 0.635 | 1.000 |
| [csb_org_platform_haiku_20260226_035633_variance](runs/csb_org_platform_haiku_20260226_035633_variance.md) | `csb_org_platform` | `baseline-local-direct` | 2 | 0.717 | 1.000 |
| [csb_org_platform_haiku_20260226_035633_variance](runs/csb_org_platform_haiku_20260226_035633_variance.md) | `csb_org_platform` | `mcp-remote-direct` | 3 | 0.552 | 1.000 |
| [csb_org_platform_haiku_20260226_145828](runs/csb_org_platform_haiku_20260226_145828.md) | `csb_org_platform` | `baseline-local-direct` | 2 | 0.292 | 0.500 |
| [csb_org_platform_haiku_20260226_205845](runs/csb_org_platform_haiku_20260226_205845.md) | `csb_org_platform` | `baseline-local-direct` | 1 | 0.583 | 1.000 |
| [csb_org_platform_haiku_20260226_214446](runs/csb_org_platform_haiku_20260226_214446.md) | `csb_org_platform` | `baseline-local-direct` | 1 | 0.632 | 1.000 |
| [csb_org_platform_haiku_20260226_221038](runs/csb_org_platform_haiku_20260226_221038.md) | `csb_org_platform` | `mcp-remote-direct` | 1 | 0.556 | 1.000 |
| [csb_org_platform_haiku_20260228_010919](runs/csb_org_platform_haiku_20260228_010919.md) | `csb_org_platform` | `baseline-local-direct` | 5 | 0.678 | 1.000 |
| [csb_org_platform_haiku_20260228_010919](runs/csb_org_platform_haiku_20260228_010919.md) | `csb_org_platform` | `mcp-remote-direct` | 5 | 0.597 | 1.000 |
| [csb_org_platform_haiku_20260301_191250](runs/csb_org_platform_haiku_20260301_191250.md) | `csb_org_platform` | `baseline-local-direct` | 11 | 0.177 | 0.818 |
| [csb_org_platform_haiku_20260301_191250](runs/csb_org_platform_haiku_20260301_191250.md) | `csb_org_platform` | `mcp-remote-direct` | 11 | 0.192 | 0.909 |
| [csb_org_platform_haiku_20260301_195739](runs/csb_org_platform_haiku_20260301_195739.md) | `csb_org_platform` | `baseline-local-direct` | 16 | 0.184 | 0.938 |
| [csb_org_platform_haiku_20260301_195739](runs/csb_org_platform_haiku_20260301_195739.md) | `csb_org_platform` | `mcp-remote-direct` | 16 | 0.147 | 0.938 |
| [csb_org_platform_haiku_20260302_014939](runs/csb_org_platform_haiku_20260302_014939.md) | `csb_org_platform` | `baseline-local-direct` | 5 | 0.241 | 1.000 |
| [csb_org_platform_haiku_20260302_014939](runs/csb_org_platform_haiku_20260302_014939.md) | `csb_org_platform` | `mcp-remote-direct` | 5 | 0.173 | 1.000 |
| [csb_org_platform_haiku_20260302_175821](runs/csb_org_platform_haiku_20260302_175821.md) | `csb_org_platform` | `baseline-local-direct` | 14 | 0.277 | 0.929 |
| [csb_org_platform_haiku_20260302_175821](runs/csb_org_platform_haiku_20260302_175821.md) | `csb_org_platform` | `mcp-remote-direct` | 15 | 0.251 | 0.933 |
| [csb_org_platform_haiku_20260302_175827](runs/csb_org_platform_haiku_20260302_175827.md) | `csb_org_platform` | `baseline-local-direct` | 16 | 0.224 | 0.812 |
| [csb_org_platform_haiku_20260302_175827](runs/csb_org_platform_haiku_20260302_175827.md) | `csb_org_platform` | `mcp-remote-direct` | 14 | 0.233 | 0.929 |
| [csb_org_platform_haiku_20260302_183602](runs/csb_org_platform_haiku_20260302_183602.md) | `csb_org_platform` | `baseline-local-direct` | 2 | 0.753 | 1.000 |
| [csb_org_platform_haiku_20260302_183602](runs/csb_org_platform_haiku_20260302_183602.md) | `csb_org_platform` | `mcp-remote-direct` | 2 | 0.567 | 1.000 |
| [csb_org_platform_haiku_20260302_183608](runs/csb_org_platform_haiku_20260302_183608.md) | `csb_org_platform` | `baseline-local-direct` | 2 | 0.762 | 1.000 |
| [csb_org_platform_haiku_20260302_183608](runs/csb_org_platform_haiku_20260302_183608.md) | `csb_org_platform` | `mcp-remote-direct` | 2 | 0.507 | 1.000 |
| [csb_org_security_haiku_022126](runs/csb_org_security_haiku_022126.md) | `csb_org_security` | `baseline-local-artifact` | 2 | 0.500 | 1.000 |
| [csb_org_security_haiku_022126](runs/csb_org_security_haiku_022126.md) | `csb_org_security` | `mcp-remote-artifact` | 2 | 0.821 | 1.000 |
| [csb_org_security_haiku_20260224_181919](runs/csb_org_security_haiku_20260224_181919.md) | `csb_org_security` | `mcp-remote-artifact` | 4 | 0.777 | 1.000 |
| [csb_org_security_haiku_20260225_011700](runs/csb_org_security_haiku_20260225_011700.md) | `csb_org_security` | `baseline-local-artifact` | 4 | 0.000 | 0.000 |
| [csb_org_security_haiku_20260226_035617](runs/csb_org_security_haiku_20260226_035617.md) | `csb_org_security` | `baseline-local-direct` | 1 | 0.433 | 1.000 |
| [csb_org_security_haiku_20260226_035617](runs/csb_org_security_haiku_20260226_035617.md) | `csb_org_security` | `mcp-remote-direct` | 4 | 0.744 | 1.000 |
| [csb_org_security_haiku_20260226_035622_variance](runs/csb_org_security_haiku_20260226_035622_variance.md) | `csb_org_security` | `baseline-local-direct` | 1 | 0.514 | 1.000 |
| [csb_org_security_haiku_20260226_035622_variance](runs/csb_org_security_haiku_20260226_035622_variance.md) | `csb_org_security` | `mcp-remote-direct` | 4 | 0.578 | 1.000 |
| [csb_org_security_haiku_20260226_035628_variance](runs/csb_org_security_haiku_20260226_035628_variance.md) | `csb_org_security` | `baseline-local-direct` | 1 | 0.367 | 1.000 |
| [csb_org_security_haiku_20260226_035628_variance](runs/csb_org_security_haiku_20260226_035628_variance.md) | `csb_org_security` | `mcp-remote-direct` | 4 | 0.767 | 1.000 |
| [csb_org_security_haiku_20260226_035633_variance](runs/csb_org_security_haiku_20260226_035633_variance.md) | `csb_org_security` | `baseline-local-direct` | 1 | 0.586 | 1.000 |
| [csb_org_security_haiku_20260226_035633_variance](runs/csb_org_security_haiku_20260226_035633_variance.md) | `csb_org_security` | `mcp-remote-direct` | 4 | 0.731 | 1.000 |
| [csb_org_security_haiku_20260226_145828](runs/csb_org_security_haiku_20260226_145828.md) | `csb_org_security` | `baseline-local-direct` | 3 | 0.641 | 1.000 |
| [csb_org_security_haiku_20260226_205845](runs/csb_org_security_haiku_20260226_205845.md) | `csb_org_security` | `baseline-local-direct` | 3 | 0.682 | 1.000 |
| [csb_org_security_haiku_20260228_012337](runs/csb_org_security_haiku_20260228_012337.md) | `csb_org_security` | `baseline-local-direct` | 7 | 0.420 | 0.714 |
| [csb_org_security_haiku_20260228_012337](runs/csb_org_security_haiku_20260228_012337.md) | `csb_org_security` | `mcp-remote-direct` | 5 | 0.690 | 1.000 |
| [csb_org_security_haiku_20260228_020502](runs/csb_org_security_haiku_20260228_020502.md) | `csb_org_security` | `baseline-local-direct` | 9 | 0.496 | 0.778 |
| [csb_org_security_haiku_20260228_025547](runs/csb_org_security_haiku_20260228_025547.md) | `csb_org_security` | `baseline-local-direct` | 4 | 0.662 | 1.000 |
| [csb_org_security_haiku_20260228_025547](runs/csb_org_security_haiku_20260228_025547.md) | `csb_org_security` | `mcp-remote-direct` | 4 | 0.811 | 1.000 |
| [csb_org_security_haiku_20260228_123206](runs/csb_org_security_haiku_20260228_123206.md) | `csb_org_security` | `baseline-local-direct` | 4 | 0.731 | 1.000 |
| [csb_org_security_haiku_20260301_201904](runs/csb_org_security_haiku_20260301_201904.md) | `csb_org_security` | `baseline-local-artifact` | 19 | 0.320 | 0.842 |
| [csb_org_security_haiku_20260301_201904](runs/csb_org_security_haiku_20260301_201904.md) | `csb_org_security` | `mcp-remote-artifact` | 20 | 0.494 | 1.000 |
| [csb_org_security_haiku_20260301_231457](runs/csb_org_security_haiku_20260301_231457.md) | `csb_org_security` | `baseline-local-direct` | 3 | 0.786 | 1.000 |
| [csb_org_security_haiku_20260301_231457](runs/csb_org_security_haiku_20260301_231457.md) | `csb_org_security` | `mcp-remote-direct` | 4 | 0.753 | 1.000 |
| [csb_org_security_haiku_20260301_235018](runs/csb_org_security_haiku_20260301_235018.md) | `csb_org_security` | `baseline-local-direct` | 1 | 0.673 | 1.000 |
| [csb_org_security_haiku_20260302_014939](runs/csb_org_security_haiku_20260302_014939.md) | `csb_org_security` | `baseline-local-direct` | 6 | 0.718 | 1.000 |
| [csb_org_security_haiku_20260302_014939](runs/csb_org_security_haiku_20260302_014939.md) | `csb_org_security` | `mcp-remote-direct` | 6 | 0.731 | 1.000 |
| [csb_org_security_haiku_20260302_022538](runs/csb_org_security_haiku_20260302_022538.md) | `csb_org_security` | `baseline-local-direct` | 4 | 0.767 | 1.000 |
| [csb_org_security_haiku_20260302_022538](runs/csb_org_security_haiku_20260302_022538.md) | `csb_org_security` | `mcp-remote-direct` | 4 | 0.737 | 1.000 |
| [csb_org_security_haiku_20260302_175821](runs/csb_org_security_haiku_20260302_175821.md) | `csb_org_security` | `baseline-local-direct` | 10 | 0.305 | 0.900 |
| [csb_org_security_haiku_20260302_175821](runs/csb_org_security_haiku_20260302_175821.md) | `csb_org_security` | `mcp-remote-direct` | 13 | 0.478 | 1.000 |
| [csb_org_security_haiku_20260302_175827](runs/csb_org_security_haiku_20260302_175827.md) | `csb_org_security` | `baseline-local-direct` | 11 | 0.417 | 0.909 |
| [csb_org_security_haiku_20260302_175827](runs/csb_org_security_haiku_20260302_175827.md) | `csb_org_security` | `mcp-remote-direct` | 14 | 0.448 | 1.000 |
| [csb_org_security_haiku_20260302_183602](runs/csb_org_security_haiku_20260302_183602.md) | `csb_org_security` | `baseline-local-direct` | 6 | 0.515 | 0.667 |
| [csb_org_security_haiku_20260302_183602](runs/csb_org_security_haiku_20260302_183602.md) | `csb_org_security` | `mcp-remote-direct` | 6 | 0.697 | 0.833 |
| [csb_org_security_haiku_20260302_183608](runs/csb_org_security_haiku_20260302_183608.md) | `csb_org_security` | `baseline-local-direct` | 6 | 0.588 | 0.833 |
| [csb_org_security_haiku_20260302_183608](runs/csb_org_security_haiku_20260302_183608.md) | `csb_org_security` | `mcp-remote-direct` | 6 | 0.771 | 1.000 |
| [csb_org_security_haiku_20260302_210829](runs/csb_org_security_haiku_20260302_210829.md) | `csb_org_security` | `baseline-local-direct` | 1 | 0.000 | 0.000 |
| [csb_org_security_haiku_20260302_210829](runs/csb_org_security_haiku_20260302_210829.md) | `csb_org_security` | `mcp-remote-direct` | 4 | 0.119 | 0.500 |
| [csb_org_security_haiku_20260302_210835](runs/csb_org_security_haiku_20260302_210835.md) | `csb_org_security` | `baseline-local-direct` | 1 | 0.000 | 0.000 |
| [csb_org_security_haiku_20260302_210835](runs/csb_org_security_haiku_20260302_210835.md) | `csb_org_security` | `mcp-remote-direct` | 4 | 0.193 | 0.500 |
| [csb_org_security_haiku_20260302_210842](runs/csb_org_security_haiku_20260302_210842.md) | `csb_org_security` | `baseline-local-direct` | 1 | 0.000 | 0.000 |
| [csb_org_security_haiku_20260302_210842](runs/csb_org_security_haiku_20260302_210842.md) | `csb_org_security` | `mcp-remote-direct` | 4 | 0.200 | 0.500 |
| [csb_org_security_haiku_20260302_212645](runs/csb_org_security_haiku_20260302_212645.md) | `csb_org_security` | `baseline-local-direct` | 3 | 0.231 | 0.667 |
| [csb_org_security_haiku_20260302_212645](runs/csb_org_security_haiku_20260302_212645.md) | `csb_org_security` | `mcp-remote-direct` | 3 | 0.127 | 0.667 |
| [csb_sdlc_build_haiku_20260227_025524](runs/csb_sdlc_build_haiku_20260227_025524.md) | `csb_sdlc_build` | `baseline-local-direct` | 3 | 0.513 | 1.000 |
| [csb_sdlc_build_haiku_20260227_034711](runs/csb_sdlc_build_haiku_20260227_034711.md) | `csb_sdlc_build` | `baseline-local-direct` | 1 | 0.500 | 1.000 |
| [csb_sdlc_build_haiku_20260227_123839](runs/csb_sdlc_build_haiku_20260227_123839.md) | `csb_sdlc_build` | `baseline-local-direct` | 8 | 0.641 | 1.000 |
| [csb_sdlc_build_haiku_20260227_123839](runs/csb_sdlc_build_haiku_20260227_123839.md) | `csb_sdlc_build` | `mcp-remote-direct` | 7 | 0.571 | 1.000 |
| [csb_sdlc_build_haiku_20260228_025547](runs/csb_sdlc_build_haiku_20260228_025547.md) | `csb_sdlc_build` | `baseline-local-direct` | 13 | 0.554 | 0.692 |
| [csb_sdlc_build_haiku_20260228_025547](runs/csb_sdlc_build_haiku_20260228_025547.md) | `csb_sdlc_build` | `mcp-remote-direct` | 10 | 0.595 | 0.700 |
| [csb_sdlc_build_haiku_20260228_124521](runs/csb_sdlc_build_haiku_20260228_124521.md) | `csb_sdlc_build` | `mcp-remote-direct` | 1 | 0.880 | 1.000 |
| [csb_sdlc_build_haiku_20260228_160517](runs/csb_sdlc_build_haiku_20260228_160517.md) | `csb_sdlc_build` | `baseline-local-direct` | 1 | 1.000 | 1.000 |
| [csb_sdlc_build_haiku_20260228_161037](runs/csb_sdlc_build_haiku_20260228_161037.md) | `csb_sdlc_build` | `baseline-local-direct` | 1 | 1.000 | 1.000 |
| [csb_sdlc_build_haiku_20260228_161037](runs/csb_sdlc_build_haiku_20260228_161037.md) | `csb_sdlc_build` | `mcp-remote-direct` | 1 | 1.000 | 1.000 |
| [csb_sdlc_build_haiku_20260228_161452](runs/csb_sdlc_build_haiku_20260228_161452.md) | `csb_sdlc_build` | `baseline-local-direct` | 1 | 1.000 | 1.000 |
| [csb_sdlc_build_haiku_20260228_161452](runs/csb_sdlc_build_haiku_20260228_161452.md) | `csb_sdlc_build` | `mcp-remote-direct` | 1 | 0.000 | 0.000 |
| [csb_sdlc_debug_haiku_20260228_025547](runs/csb_sdlc_debug_haiku_20260228_025547.md) | `csb_sdlc_debug` | `baseline-local-direct` | 5 | 0.500 | 1.000 |
| [csb_sdlc_debug_haiku_20260228_025547](runs/csb_sdlc_debug_haiku_20260228_025547.md) | `csb_sdlc_debug` | `mcp-remote-direct` | 5 | 0.000 | 0.000 |
| [csb_sdlc_debug_haiku_20260228_051032](runs/csb_sdlc_debug_haiku_20260228_051032.md) | `csb_sdlc_debug` | `baseline-local-direct` | 3 | 0.900 | 1.000 |
| [csb_sdlc_debug_haiku_20260228_123206](runs/csb_sdlc_debug_haiku_20260228_123206.md) | `csb_sdlc_debug` | `baseline-local-direct` | 2 | 0.300 | 1.000 |
| [csb_sdlc_debug_haiku_20260301_230240](runs/csb_sdlc_debug_haiku_20260301_230240.md) | `csb_sdlc_debug` | `baseline-local-direct` | 2 | 0.500 | 1.000 |
| [csb_sdlc_debug_haiku_20260301_230240](runs/csb_sdlc_debug_haiku_20260301_230240.md) | `csb_sdlc_debug` | `mcp-remote-direct` | 2 | 0.500 | 1.000 |
| [csb_sdlc_debug_haiku_20260302_004746](runs/csb_sdlc_debug_haiku_20260302_004746.md) | `csb_sdlc_debug` | `baseline-local-direct` | 2 | 0.750 | 1.000 |
| [csb_sdlc_debug_haiku_20260302_004746](runs/csb_sdlc_debug_haiku_20260302_004746.md) | `csb_sdlc_debug` | `mcp-remote-direct` | 2 | 0.500 | 1.000 |
| [csb_sdlc_debug_haiku_20260302_013712](runs/csb_sdlc_debug_haiku_20260302_013712.md) | `csb_sdlc_debug` | `baseline-local-direct` | 1 | 0.500 | 1.000 |
| [csb_sdlc_debug_haiku_20260302_013713](runs/csb_sdlc_debug_haiku_20260302_013713.md) | `csb_sdlc_debug` | `mcp-remote-direct` | 1 | 0.500 | 1.000 |
| [csb_sdlc_debug_haiku_20260302_022552](runs/csb_sdlc_debug_haiku_20260302_022552.md) | `csb_sdlc_debug` | `baseline-local-direct` | 1 | 0.500 | 1.000 |
| [csb_sdlc_debug_haiku_20260302_022553](runs/csb_sdlc_debug_haiku_20260302_022553.md) | `csb_sdlc_debug` | `mcp-remote-direct` | 1 | 0.500 | 1.000 |
| [csb_sdlc_design_haiku_022326](runs/csb_sdlc_design_haiku_022326.md) | `csb_sdlc_design` | `baseline-local-direct` | 13 | 0.770 | 1.000 |
| [csb_sdlc_design_haiku_022326](runs/csb_sdlc_design_haiku_022326.md) | `csb_sdlc_design` | `mcp-remote-direct` | 20 | 0.718 | 1.000 |
| [csb_sdlc_design_haiku_20260225_234223](runs/csb_sdlc_design_haiku_20260225_234223.md) | `csb_sdlc_design` | `baseline-local-direct` | 7 | 0.723 | 0.857 |
| [csb_sdlc_design_haiku_20260226_015500_backfill](runs/csb_sdlc_design_haiku_20260226_015500_backfill.md) | `csb_sdlc_design` | `baseline-local-direct` | 7 | 0.723 | 0.857 |
| [csb_sdlc_design_haiku_20260228_025547](runs/csb_sdlc_design_haiku_20260228_025547.md) | `csb_sdlc_design` | `baseline-local-direct` | 13 | 0.598 | 1.000 |
| [csb_sdlc_design_haiku_20260228_025547](runs/csb_sdlc_design_haiku_20260228_025547.md) | `csb_sdlc_design` | `mcp-remote-direct` | 13 | 0.751 | 1.000 |
| [csb_sdlc_document_haiku_022326](runs/csb_sdlc_document_haiku_022326.md) | `csb_sdlc_document` | `baseline-local-direct` | 14 | 0.904 | 1.000 |
| [csb_sdlc_document_haiku_022326](runs/csb_sdlc_document_haiku_022326.md) | `csb_sdlc_document` | `mcp-remote-direct` | 15 | 0.953 | 1.000 |
| [csb_sdlc_document_haiku_20260224_174311](runs/csb_sdlc_document_haiku_20260224_174311.md) | `csb_sdlc_document` | `baseline-local-direct` | 5 | 0.658 | 1.000 |
| [csb_sdlc_document_haiku_20260224_174311](runs/csb_sdlc_document_haiku_20260224_174311.md) | `csb_sdlc_document` | `mcp-remote-direct` | 5 | 0.720 | 1.000 |
| [csb_sdlc_document_haiku_20260226_015500_backfill](runs/csb_sdlc_document_haiku_20260226_015500_backfill.md) | `csb_sdlc_document` | `baseline-local-direct` | 1 | 1.000 | 1.000 |
| [csb_sdlc_document_haiku_20260228_025547](runs/csb_sdlc_document_haiku_20260228_025547.md) | `csb_sdlc_document` | `baseline-local-direct` | 18 | 0.879 | 1.000 |
| [csb_sdlc_document_haiku_20260228_025547](runs/csb_sdlc_document_haiku_20260228_025547.md) | `csb_sdlc_document` | `mcp-remote-direct` | 18 | 0.887 | 1.000 |
| [csb_sdlc_document_haiku_20260228_124521](runs/csb_sdlc_document_haiku_20260228_124521.md) | `csb_sdlc_document` | `mcp-remote-direct` | 1 | 1.000 | 1.000 |
| [csb_sdlc_feature_haiku_20260301_212230](runs/csb_sdlc_feature_haiku_20260301_212230.md) | `csb_sdlc_feature` | `baseline-local-direct` | 3 | 0.500 | 0.667 |
| [csb_sdlc_feature_haiku_20260301_212230](runs/csb_sdlc_feature_haiku_20260301_212230.md) | `csb_sdlc_feature` | `mcp-remote-direct` | 3 | 0.500 | 0.667 |
| [csb_sdlc_feature_haiku_20260301_230003](runs/csb_sdlc_feature_haiku_20260301_230003.md) | `csb_sdlc_feature` | `baseline-local-direct` | 4 | 0.358 | 0.750 |
| [csb_sdlc_feature_haiku_20260301_230003](runs/csb_sdlc_feature_haiku_20260301_230003.md) | `csb_sdlc_feature` | `mcp-remote-direct` | 4 | 0.407 | 0.750 |
| [csb_sdlc_feature_haiku_20260302_004743](runs/csb_sdlc_feature_haiku_20260302_004743.md) | `csb_sdlc_feature` | `baseline-local-direct` | 3 | 0.444 | 0.667 |
| [csb_sdlc_feature_haiku_20260302_004743](runs/csb_sdlc_feature_haiku_20260302_004743.md) | `csb_sdlc_feature` | `mcp-remote-direct` | 3 | 0.500 | 0.667 |
| [csb_sdlc_feature_haiku_20260302_005828](runs/csb_sdlc_feature_haiku_20260302_005828.md) | `csb_sdlc_feature` | `baseline-local-direct` | 3 | 0.222 | 0.667 |
| [csb_sdlc_feature_haiku_20260302_005828](runs/csb_sdlc_feature_haiku_20260302_005828.md) | `csb_sdlc_feature` | `mcp-remote-direct` | 3 | 0.500 | 0.667 |
| [csb_sdlc_feature_haiku_20260302_005948](runs/csb_sdlc_feature_haiku_20260302_005948.md) | `csb_sdlc_feature` | `mcp-remote-direct` | 1 | 0.140 | 1.000 |
| [csb_sdlc_feature_haiku_20260302_022544](runs/csb_sdlc_feature_haiku_20260302_022544.md) | `csb_sdlc_feature` | `baseline-local-direct` | 1 | 0.000 | 0.000 |
| [csb_sdlc_fix_haiku_20260228_185835](runs/csb_sdlc_fix_haiku_20260228_185835.md) | `csb_sdlc_fix` | `baseline-local-direct` | 25 | 0.471 | 0.640 |
| [csb_sdlc_fix_haiku_20260228_185835](runs/csb_sdlc_fix_haiku_20260228_185835.md) | `csb_sdlc_fix` | `mcp-remote-direct` | 25 | 0.592 | 0.720 |
| [csb_sdlc_fix_haiku_20260228_203750](runs/csb_sdlc_fix_haiku_20260228_203750.md) | `csb_sdlc_fix` | `baseline-local-direct` | 3 | 0.457 | 1.000 |
| [csb_sdlc_fix_haiku_20260228_205741](runs/csb_sdlc_fix_haiku_20260228_205741.md) | `csb_sdlc_fix` | `baseline-local-direct` | 25 | 0.440 | 0.600 |
| [csb_sdlc_fix_haiku_20260228_205741](runs/csb_sdlc_fix_haiku_20260228_205741.md) | `csb_sdlc_fix` | `mcp-remote-direct` | 25 | 0.536 | 0.680 |
| [csb_sdlc_fix_haiku_20260228_230722](runs/csb_sdlc_fix_haiku_20260228_230722.md) | `csb_sdlc_fix` | `baseline-local-direct` | 20 | 0.510 | 0.650 |
| [csb_sdlc_fix_haiku_20260228_230722](runs/csb_sdlc_fix_haiku_20260228_230722.md) | `csb_sdlc_fix` | `mcp-remote-direct` | 20 | 0.593 | 0.750 |
| [csb_sdlc_fix_haiku_20260301_173337](runs/csb_sdlc_fix_haiku_20260301_173337.md) | `csb_sdlc_fix` | `baseline-local-direct` | 9 | 0.597 | 0.889 |
| [csb_sdlc_fix_haiku_20260301_173337](runs/csb_sdlc_fix_haiku_20260301_173337.md) | `csb_sdlc_fix` | `mcp-remote-direct` | 5 | 0.646 | 1.000 |
| [csb_sdlc_fix_haiku_20260301_173342](runs/csb_sdlc_fix_haiku_20260301_173342.md) | `csb_sdlc_fix` | `mcp-remote-direct` | 8 | 0.621 | 0.625 |
| [csb_sdlc_fix_haiku_20260301_212230](runs/csb_sdlc_fix_haiku_20260301_212230.md) | `csb_sdlc_fix` | `baseline-local-direct` | 1 | 0.000 | 0.000 |
| [csb_sdlc_fix_haiku_20260301_212230](runs/csb_sdlc_fix_haiku_20260301_212230.md) | `csb_sdlc_fix` | `mcp-remote-direct` | 1 | 0.000 | 0.000 |
| [csb_sdlc_fix_haiku_20260301_214459](runs/csb_sdlc_fix_haiku_20260301_214459.md) | `csb_sdlc_fix` | `baseline-local-direct` | 1 | 0.500 | 1.000 |
| [csb_sdlc_fix_haiku_20260301_214459](runs/csb_sdlc_fix_haiku_20260301_214459.md) | `csb_sdlc_fix` | `mcp-remote-direct` | 1 | 0.500 | 1.000 |
| [csb_sdlc_fix_haiku_20260301_230003](runs/csb_sdlc_fix_haiku_20260301_230003.md) | `csb_sdlc_fix` | `baseline-local-direct` | 1 | 0.667 | 1.000 |
| [csb_sdlc_fix_haiku_20260301_230048](runs/csb_sdlc_fix_haiku_20260301_230048.md) | `csb_sdlc_fix` | `baseline-local-direct` | 3 | 0.413 | 0.667 |
| [csb_sdlc_fix_haiku_20260301_230048](runs/csb_sdlc_fix_haiku_20260301_230048.md) | `csb_sdlc_fix` | `mcp-remote-direct` | 1 | 0.500 | 1.000 |
| [csb_sdlc_fix_haiku_20260301_230240](runs/csb_sdlc_fix_haiku_20260301_230240.md) | `csb_sdlc_fix` | `baseline-local-direct` | 3 | 0.537 | 0.667 |
| [csb_sdlc_fix_haiku_20260301_230240](runs/csb_sdlc_fix_haiku_20260301_230240.md) | `csb_sdlc_fix` | `mcp-remote-direct` | 3 | 0.667 | 0.667 |
| [csb_sdlc_fix_haiku_20260302_005828](runs/csb_sdlc_fix_haiku_20260302_005828.md) | `csb_sdlc_fix` | `baseline-local-direct` | 1 | 0.500 | 1.000 |
| [csb_sdlc_fix_haiku_20260302_005828](runs/csb_sdlc_fix_haiku_20260302_005828.md) | `csb_sdlc_fix` | `mcp-remote-direct` | 1 | 0.500 | 1.000 |
| [csb_sdlc_fix_haiku_20260302_005945](runs/csb_sdlc_fix_haiku_20260302_005945.md) | `csb_sdlc_fix` | `baseline-local-direct` | 2 | 0.191 | 0.500 |
| [csb_sdlc_fix_haiku_20260302_013712](runs/csb_sdlc_fix_haiku_20260302_013712.md) | `csb_sdlc_fix` | `baseline-local-direct` | 2 | 0.333 | 0.500 |
| [csb_sdlc_fix_haiku_20260302_013713](runs/csb_sdlc_fix_haiku_20260302_013713.md) | `csb_sdlc_fix` | `mcp-remote-direct` | 1 | 1.000 | 1.000 |
| [csb_sdlc_fix_haiku_20260302_015531](runs/csb_sdlc_fix_haiku_20260302_015531.md) | `csb_sdlc_fix` | `mcp-remote-direct` | 1 | 1.000 | 1.000 |
| [csb_sdlc_fix_haiku_20260302_020340](runs/csb_sdlc_fix_haiku_20260302_020340.md) | `csb_sdlc_fix` | `mcp-remote-direct` | 2 | 0.280 | 0.500 |
| [csb_sdlc_fix_haiku_20260302_021447](runs/csb_sdlc_fix_haiku_20260302_021447.md) | `csb_sdlc_fix` | `baseline-local-direct` | 2 | 0.429 | 0.500 |
| [csb_sdlc_fix_haiku_20260302_022542](runs/csb_sdlc_fix_haiku_20260302_022542.md) | `csb_sdlc_fix` | `baseline-local-direct` | 1 | 0.667 | 1.000 |
| [csb_sdlc_fix_haiku_20260302_022542](runs/csb_sdlc_fix_haiku_20260302_022542.md) | `csb_sdlc_fix` | `mcp-remote-direct` | 1 | 0.500 | 1.000 |
| [csb_sdlc_fix_haiku_20260302_022550](runs/csb_sdlc_fix_haiku_20260302_022550.md) | `csb_sdlc_fix` | `baseline-local-direct` | 1 | 0.667 | 1.000 |
| [csb_sdlc_fix_haiku_20260302_022550](runs/csb_sdlc_fix_haiku_20260302_022550.md) | `csb_sdlc_fix` | `mcp-remote-direct` | 1 | 1.000 | 1.000 |
| [csb_sdlc_fix_haiku_20260302_022552](runs/csb_sdlc_fix_haiku_20260302_022552.md) | `csb_sdlc_fix` | `baseline-local-direct` | 1 | 0.000 | 0.000 |
| [csb_sdlc_refactor_haiku_20260301_133910](runs/csb_sdlc_refactor_haiku_20260301_133910.md) | `csb_sdlc_refactor` | `baseline-local-direct` | 1 | 0.800 | 1.000 |
| [csb_sdlc_secure_haiku_022326](runs/csb_sdlc_secure_haiku_022326.md) | `csb_sdlc_secure` | `baseline-local-direct` | 18 | 0.688 | 0.944 |
| [csb_sdlc_secure_haiku_022326](runs/csb_sdlc_secure_haiku_022326.md) | `csb_sdlc_secure` | `mcp-remote-direct` | 18 | 0.705 | 1.000 |
| [csb_sdlc_secure_haiku_20260224_213146](runs/csb_sdlc_secure_haiku_20260224_213146.md) | `csb_sdlc_secure` | `baseline-local-direct` | 2 | 0.500 | 1.000 |
| [csb_sdlc_secure_haiku_20260224_213146](runs/csb_sdlc_secure_haiku_20260224_213146.md) | `csb_sdlc_secure` | `mcp-remote-direct` | 2 | 0.250 | 0.500 |
| [csb_sdlc_secure_haiku_20260228_124521](runs/csb_sdlc_secure_haiku_20260228_124521.md) | `csb_sdlc_secure` | `mcp-remote-direct` | 2 | 0.555 | 1.000 |
| [csb_sdlc_test_haiku_20260224_180149](runs/csb_sdlc_test_haiku_20260224_180149.md) | `csb_sdlc_test` | `baseline-local-direct` | 11 | 0.486 | 0.727 |
| [csb_sdlc_test_haiku_20260224_180149](runs/csb_sdlc_test_haiku_20260224_180149.md) | `csb_sdlc_test` | `mcp-remote-direct` | 11 | 0.387 | 0.727 |
| [csb_sdlc_test_haiku_20260226_015500_backfill](runs/csb_sdlc_test_haiku_20260226_015500_backfill.md) | `csb_sdlc_test` | `baseline-local-direct` | 1 | 0.370 | 1.000 |
| [csb_sdlc_test_haiku_20260226_015500_backfill](runs/csb_sdlc_test_haiku_20260226_015500_backfill.md) | `csb_sdlc_test` | `mcp-remote-direct` | 1 | 0.900 | 1.000 |
| [csb_sdlc_test_haiku_20260228_124521](runs/csb_sdlc_test_haiku_20260228_124521.md) | `csb_sdlc_test` | `mcp-remote-direct` | 4 | 0.985 | 1.000 |
| [csb_sdlc_test_haiku_20260301_230048](runs/csb_sdlc_test_haiku_20260301_230048.md) | `csb_sdlc_test` | `baseline-local-direct` | 13 | 0.644 | 0.923 |
| [csb_sdlc_test_haiku_20260301_230048](runs/csb_sdlc_test_haiku_20260301_230048.md) | `csb_sdlc_test` | `mcp-remote-direct` | 6 | 0.798 | 1.000 |
| [csb_sdlc_test_haiku_20260302_004743](runs/csb_sdlc_test_haiku_20260302_004743.md) | `csb_sdlc_test` | `baseline-local-direct` | 3 | 0.660 | 1.000 |
| [csb_sdlc_test_haiku_20260302_005945](runs/csb_sdlc_test_haiku_20260302_005945.md) | `csb_sdlc_test` | `baseline-local-direct` | 1 | 0.500 | 1.000 |
| [csb_sdlc_test_haiku_20260302_005945](runs/csb_sdlc_test_haiku_20260302_005945.md) | `csb_sdlc_test` | `mcp-remote-direct` | 1 | 0.370 | 1.000 |
| [csb_sdlc_test_haiku_20260302_005947](runs/csb_sdlc_test_haiku_20260302_005947.md) | `csb_sdlc_test` | `baseline-local-direct` | 5 | 0.732 | 1.000 |
| [csb_sdlc_test_haiku_20260302_013712](runs/csb_sdlc_test_haiku_20260302_013712.md) | `csb_sdlc_test` | `baseline-local-direct` | 1 | 0.000 | 0.000 |
| [csb_sdlc_test_haiku_20260302_013713](runs/csb_sdlc_test_haiku_20260302_013713.md) | `csb_sdlc_test` | `mcp-remote-direct` | 1 | 0.000 | 0.000 |
| [csb_sdlc_test_haiku_20260302_020340](runs/csb_sdlc_test_haiku_20260302_020340.md) | `csb_sdlc_test` | `mcp-remote-direct` | 6 | 0.450 | 1.000 |
| [csb_sdlc_test_haiku_20260302_021358](runs/csb_sdlc_test_haiku_20260302_021358.md) | `csb_sdlc_test` | `mcp-remote-direct` | 1 | 0.620 | 1.000 |
| [csb_sdlc_test_haiku_20260302_021447](runs/csb_sdlc_test_haiku_20260302_021447.md) | `csb_sdlc_test` | `baseline-local-direct` | 7 | 0.627 | 1.000 |
| [csb_sdlc_test_haiku_20260302_022542](runs/csb_sdlc_test_haiku_20260302_022542.md) | `csb_sdlc_test` | `baseline-local-direct` | 1 | 0.440 | 1.000 |
| [csb_sdlc_test_haiku_20260302_022542](runs/csb_sdlc_test_haiku_20260302_022542.md) | `csb_sdlc_test` | `mcp-remote-direct` | 1 | 0.290 | 1.000 |
| [csb_sdlc_test_haiku_20260302_022544](runs/csb_sdlc_test_haiku_20260302_022544.md) | `csb_sdlc_test` | `baseline-local-direct` | 4 | 0.775 | 1.000 |
| [csb_sdlc_test_haiku_20260302_022552](runs/csb_sdlc_test_haiku_20260302_022552.md) | `csb_sdlc_test` | `baseline-local-direct` | 2 | 0.240 | 0.500 |
| [csb_sdlc_test_haiku_20260302_022553](runs/csb_sdlc_test_haiku_20260302_022553.md) | `csb_sdlc_test` | `mcp-remote-direct` | 1 | 0.000 | 0.000 |
| [csb_sdlc_test_haiku_20260302_041201](runs/csb_sdlc_test_haiku_20260302_041201.md) | `csb_sdlc_test` | `mcp-remote-direct` | 3 | 0.503 | 1.000 |
| [csb_sdlc_understand_haiku_022426](runs/csb_sdlc_understand_haiku_022426.md) | `csb_sdlc_understand` | `baseline-local-direct` | 13 | 0.592 | 0.692 |
| [csb_sdlc_understand_haiku_022426](runs/csb_sdlc_understand_haiku_022426.md) | `csb_sdlc_understand` | `mcp-remote-direct` | 13 | 0.841 | 1.000 |
| [csb_sdlc_understand_haiku_20260227_132300](runs/csb_sdlc_understand_haiku_20260227_132300.md) | `csb_sdlc_understand` | `baseline-local-direct` | 14 | 1.000 | 1.000 |
| [csb_sdlc_understand_haiku_20260227_132300](runs/csb_sdlc_understand_haiku_20260227_132300.md) | `csb_sdlc_understand` | `mcp-remote-direct` | 12 | 0.858 | 0.917 |
| [csb_sdlc_understand_haiku_20260227_132304](runs/csb_sdlc_understand_haiku_20260227_132304.md) | `csb_sdlc_understand` | `baseline-local-direct` | 14 | 0.864 | 0.929 |
| [csb_sdlc_understand_haiku_20260227_132304](runs/csb_sdlc_understand_haiku_20260227_132304.md) | `csb_sdlc_understand` | `mcp-remote-direct` | 12 | 0.942 | 1.000 |
| [csb_sdlc_understand_haiku_20260228_124521](runs/csb_sdlc_understand_haiku_20260228_124521.md) | `csb_sdlc_understand` | `mcp-remote-direct` | 4 | 0.823 | 1.000 |
| [debug_haiku_20260228_230112](runs/debug_haiku_20260228_230112.md) | `csb_sdlc_debug` | `baseline-local-direct` | 10 | 0.833 | 1.000 |
| [debug_haiku_20260228_230112](runs/debug_haiku_20260228_230112.md) | `csb_sdlc_debug` | `mcp-remote-direct` | 8 | 0.730 | 1.000 |
| [debug_haiku_20260228_230648](runs/debug_haiku_20260228_230648.md) | `csb_sdlc_debug` | `baseline-local-direct` | 11 | 0.864 | 1.000 |
| [debug_haiku_20260228_230648](runs/debug_haiku_20260228_230648.md) | `csb_sdlc_debug` | `mcp-remote-direct` | 2 | 1.000 | 1.000 |
| [debug_haiku_20260228_231033](runs/debug_haiku_20260228_231033.md) | `csb_sdlc_debug` | `baseline-local-direct` | 11 | 0.857 | 1.000 |
| [debug_haiku_20260228_231033](runs/debug_haiku_20260228_231033.md) | `csb_sdlc_debug` | `mcp-remote-direct` | 10 | 0.804 | 1.000 |
| [debug_haiku_20260301_021540](runs/debug_haiku_20260301_021540.md) | `csb_sdlc_debug` | `baseline-local-direct` | 11 | 0.847 | 1.000 |
| [debug_haiku_20260301_021540](runs/debug_haiku_20260301_021540.md) | `csb_sdlc_debug` | `mcp-remote-direct` | 11 | 0.813 | 1.000 |
| [debug_haiku_20260301_030159](runs/debug_haiku_20260301_030159.md) | `csb_sdlc_debug` | `baseline-local-direct` | 11 | 0.837 | 1.000 |
| [debug_haiku_20260301_030159](runs/debug_haiku_20260301_030159.md) | `csb_sdlc_debug` | `mcp-remote-direct` | 11 | 0.801 | 1.000 |
| [debug_haiku_20260301_031844](runs/debug_haiku_20260301_031844.md) | `csb_sdlc_debug` | `baseline-local-direct` | 11 | 0.806 | 1.000 |
| [debug_haiku_20260301_031844](runs/debug_haiku_20260301_031844.md) | `csb_sdlc_debug` | `mcp-remote-direct` | 11 | 0.750 | 1.000 |
| [debug_haiku_20260301_033225](runs/debug_haiku_20260301_033225.md) | `csb_sdlc_debug` | `baseline-local-direct` | 9 | 0.444 | 0.889 |
| [debug_haiku_20260301_033225](runs/debug_haiku_20260301_033225.md) | `csb_sdlc_debug` | `mcp-remote-direct` | 9 | 0.389 | 0.778 |
| [debug_haiku_20260301_035030](runs/debug_haiku_20260301_035030.md) | `csb_sdlc_debug` | `baseline-local-direct` | 9 | 0.333 | 0.667 |
| [debug_haiku_20260301_035030](runs/debug_haiku_20260301_035030.md) | `csb_sdlc_debug` | `mcp-remote-direct` | 9 | 0.278 | 0.556 |
| [debug_haiku_20260301_040300](runs/debug_haiku_20260301_040300.md) | `csb_sdlc_debug` | `baseline-local-direct` | 9 | 0.500 | 1.000 |
| [debug_haiku_20260301_040300](runs/debug_haiku_20260301_040300.md) | `csb_sdlc_debug` | `mcp-remote-direct` | 9 | 0.389 | 0.778 |
| [debug_haiku_20260301_071226](runs/debug_haiku_20260301_071226.md) | `csb_sdlc_debug` | `baseline-local-direct` | 11 | 0.842 | 1.000 |
| [debug_haiku_20260301_071226](runs/debug_haiku_20260301_071226.md) | `csb_sdlc_debug` | `mcp-remote-direct` | 11 | 0.841 | 1.000 |
| [design_haiku_20260301_022406](runs/design_haiku_20260301_022406.md) | `csb_sdlc_design` | `baseline-local-direct` | 20 | 0.766 | 1.000 |
| [design_haiku_20260301_022406](runs/design_haiku_20260301_022406.md) | `csb_sdlc_design` | `mcp-remote-direct` | 20 | 0.734 | 1.000 |
| [design_haiku_20260301_031030](runs/design_haiku_20260301_031030.md) | `csb_sdlc_design` | `baseline-local-direct` | 20 | 0.762 | 0.950 |
| [design_haiku_20260301_031030](runs/design_haiku_20260301_031030.md) | `csb_sdlc_design` | `mcp-remote-direct` | 20 | 0.747 | 1.000 |
| [design_haiku_20260301_031845](runs/design_haiku_20260301_031845.md) | `csb_sdlc_design` | `baseline-local-direct` | 20 | 0.807 | 1.000 |
| [design_haiku_20260301_031845](runs/design_haiku_20260301_031845.md) | `csb_sdlc_design` | `mcp-remote-direct` | 19 | 0.701 | 1.000 |
| [design_haiku_20260301_071227](runs/design_haiku_20260301_071227.md) | `csb_sdlc_design` | `baseline-local-direct` | 20 | 0.770 | 1.000 |
| [design_haiku_20260301_071227](runs/design_haiku_20260301_071227.md) | `csb_sdlc_design` | `mcp-remote-direct` | 20 | 0.699 | 0.950 |
| [document_haiku_20260223_164240](runs/document_haiku_20260223_164240.md) | `csb_sdlc_document` | `baseline-local-direct` | 19 | 0.851 | 1.000 |
| [document_haiku_20260223_164240](runs/document_haiku_20260223_164240.md) | `csb_sdlc_document` | `mcp-remote-direct` | 20 | 0.822 | 1.000 |
| [document_haiku_20260226_013910](runs/document_haiku_20260226_013910.md) | `csb_sdlc_document` | `baseline-local-direct` | 1 | 1.000 | 1.000 |
| [document_haiku_20260301_031846](runs/document_haiku_20260301_031846.md) | `csb_sdlc_document` | `baseline-local-direct` | 20 | 0.875 | 1.000 |
| [document_haiku_20260301_031846](runs/document_haiku_20260301_031846.md) | `csb_sdlc_document` | `mcp-remote-direct` | 20 | 0.908 | 1.000 |
| [document_haiku_20260301_071228](runs/document_haiku_20260301_071228.md) | `csb_sdlc_document` | `baseline-local-direct` | 20 | 0.845 | 1.000 |
| [document_haiku_20260301_071228](runs/document_haiku_20260301_071228.md) | `csb_sdlc_document` | `mcp-remote-direct` | 20 | 0.898 | 1.000 |
| [feature_haiku_20260228_190114](runs/feature_haiku_20260228_190114.md) | `csb_sdlc_feature` | `baseline-local-direct` | 5 | 0.507 | 0.600 |
| [feature_haiku_20260228_190114](runs/feature_haiku_20260228_190114.md) | `csb_sdlc_feature` | `mcp-remote-direct` | 6 | 0.550 | 0.833 |
| [feature_haiku_20260228_211127](runs/feature_haiku_20260228_211127.md) | `csb_sdlc_feature` | `baseline-local-direct` | 17 | 0.694 | 1.000 |
| [feature_haiku_20260228_211127](runs/feature_haiku_20260228_211127.md) | `csb_sdlc_feature` | `mcp-remote-direct` | 16 | 0.618 | 0.938 |
| [feature_haiku_20260228_220733](runs/feature_haiku_20260228_220733.md) | `csb_sdlc_feature` | `baseline-local-direct` | 4 | 0.375 | 0.500 |
| [feature_haiku_20260228_220733](runs/feature_haiku_20260228_220733.md) | `csb_sdlc_feature` | `mcp-remote-direct` | 4 | 0.542 | 0.750 |
| [feature_haiku_20260228_230114](runs/feature_haiku_20260228_230114.md) | `csb_sdlc_feature` | `mcp-remote-direct` | 1 | 0.280 | 1.000 |
| [feature_haiku_20260228_231035](runs/feature_haiku_20260228_231035.md) | `csb_sdlc_feature` | `mcp-remote-direct` | 4 | 0.333 | 0.750 |
| [feature_haiku_20260228_231041](runs/feature_haiku_20260228_231041.md) | `csb_sdlc_feature` | `baseline-local-direct` | 4 | 0.557 | 1.000 |
| [feature_haiku_20260301_023333](runs/feature_haiku_20260301_023333.md) | `csb_sdlc_feature` | `baseline-local-direct` | 8 | 0.835 | 1.000 |
| [feature_haiku_20260301_023333](runs/feature_haiku_20260301_023333.md) | `csb_sdlc_feature` | `mcp-remote-direct` | 6 | 0.867 | 1.000 |
| [feature_haiku_20260301_031848](runs/feature_haiku_20260301_031848.md) | `csb_sdlc_feature` | `baseline-local-direct` | 19 | 0.665 | 0.947 |
| [feature_haiku_20260301_031848](runs/feature_haiku_20260301_031848.md) | `csb_sdlc_feature` | `mcp-remote-direct` | 18 | 0.644 | 0.889 |
| [feature_haiku_20260301_071229](runs/feature_haiku_20260301_071229.md) | `csb_sdlc_feature` | `baseline-local-direct` | 20 | 0.656 | 0.900 |
| [feature_haiku_20260301_071229](runs/feature_haiku_20260301_071229.md) | `csb_sdlc_feature` | `mcp-remote-direct` | 19 | 0.608 | 0.895 |
| [feature_haiku_vscode_rerun_20260301_023018](runs/feature_haiku_vscode_rerun_20260301_023018.md) | `csb_sdlc_feature` | `baseline-local-direct` | 1 | 0.500 | 1.000 |
| [fix_haiku_20260301_190026](runs/fix_haiku_20260301_190026.md) | `csb_sdlc_fix` | `baseline-local-direct` | 2 | 0.000 | 0.000 |
| [fix_haiku_20260301_190026](runs/fix_haiku_20260301_190026.md) | `csb_sdlc_fix` | `mcp-remote-direct` | 2 | 0.000 | 0.000 |
| [refactor_haiku_20260228_210652](runs/refactor_haiku_20260228_210652.md) | `csb_sdlc_refactor` | `baseline-local-direct` | 1 | 0.750 | 1.000 |
| [refactor_haiku_20260228_210652](runs/refactor_haiku_20260228_210652.md) | `csb_sdlc_refactor` | `mcp-remote-direct` | 1 | 0.790 | 1.000 |
| [refactor_haiku_20260228_231037](runs/refactor_haiku_20260228_231037.md) | `csb_sdlc_refactor` | `mcp-remote-direct` | 4 | 0.592 | 1.000 |
| [refactor_haiku_20260228_231045](runs/refactor_haiku_20260228_231045.md) | `csb_sdlc_refactor` | `baseline-local-direct` | 4 | 0.463 | 1.000 |
| [refactor_haiku_20260301_010758](runs/refactor_haiku_20260301_010758.md) | `csb_sdlc_refactor` | `baseline-local-direct` | 20 | 0.791 | 0.950 |
| [refactor_haiku_20260301_010758](runs/refactor_haiku_20260301_010758.md) | `csb_sdlc_refactor` | `mcp-remote-direct` | 20 | 0.737 | 0.950 |
| [refactor_haiku_20260301_023530](runs/refactor_haiku_20260301_023530.md) | `csb_sdlc_refactor` | `baseline-local-direct` | 10 | 0.950 | 1.000 |
| [refactor_haiku_20260301_023530](runs/refactor_haiku_20260301_023530.md) | `csb_sdlc_refactor` | `mcp-remote-direct` | 10 | 0.717 | 0.900 |
| [refactor_haiku_20260301_031849](runs/refactor_haiku_20260301_031849.md) | `csb_sdlc_refactor` | `baseline-local-direct` | 20 | 0.755 | 1.000 |
| [refactor_haiku_20260301_031849](runs/refactor_haiku_20260301_031849.md) | `csb_sdlc_refactor` | `mcp-remote-direct` | 20 | 0.671 | 1.000 |
| [refactor_haiku_20260301_071230](runs/refactor_haiku_20260301_071230.md) | `csb_sdlc_refactor` | `baseline-local-direct` | 20 | 0.789 | 0.950 |
| [refactor_haiku_20260301_071230](runs/refactor_haiku_20260301_071230.md) | `csb_sdlc_refactor` | `mcp-remote-direct` | 19 | 0.713 | 1.000 |
| [secure_haiku_20260223_232545](runs/secure_haiku_20260223_232545.md) | `csb_sdlc_secure` | `baseline-local-direct` | 20 | 0.669 | 0.950 |
| [secure_haiku_20260223_232545](runs/secure_haiku_20260223_232545.md) | `csb_sdlc_secure` | `mcp-remote-direct` | 18 | 0.705 | 1.000 |
| [secure_haiku_20260224_011825](runs/secure_haiku_20260224_011825.md) | `csb_sdlc_secure` | `mcp-remote-direct` | 2 | 0.500 | 0.500 |
| [secure_haiku_20260301_031850](runs/secure_haiku_20260301_031850.md) | `csb_sdlc_secure` | `baseline-local-direct` | 20 | 0.737 | 0.950 |
| [secure_haiku_20260301_031850](runs/secure_haiku_20260301_031850.md) | `csb_sdlc_secure` | `mcp-remote-direct` | 20 | 0.728 | 1.000 |
| [secure_haiku_20260301_071231](runs/secure_haiku_20260301_071231.md) | `csb_sdlc_secure` | `baseline-local-direct` | 20 | 0.712 | 1.000 |
| [secure_haiku_20260301_071231](runs/secure_haiku_20260301_071231.md) | `csb_sdlc_secure` | `mcp-remote-direct` | 20 | 0.767 | 1.000 |
| [test_haiku_20260224_011816](runs/test_haiku_20260224_011816.md) | `csb_sdlc_test` | `baseline-local-direct` | 11 | 0.295 | 0.545 |
| [test_haiku_20260224_011816](runs/test_haiku_20260224_011816.md) | `csb_sdlc_test` | `mcp-remote-direct` | 11 | 0.262 | 0.455 |
| [test_haiku_20260228_230654](runs/test_haiku_20260228_230654.md) | `csb_sdlc_test` | `mcp-remote-direct` | 1 | 0.000 | 0.000 |
| [test_haiku_20260228_231039](runs/test_haiku_20260228_231039.md) | `csb_sdlc_test` | `mcp-remote-direct` | 1 | 0.200 | 1.000 |
| [test_haiku_20260301_031851](runs/test_haiku_20260301_031851.md) | `csb_sdlc_test` | `baseline-local-direct` | 17 | 0.571 | 0.824 |
| [test_haiku_20260301_031851](runs/test_haiku_20260301_031851.md) | `csb_sdlc_test` | `mcp-remote-direct` | 8 | 0.769 | 1.000 |
| [test_haiku_20260301_071232](runs/test_haiku_20260301_071232.md) | `csb_sdlc_test` | `baseline-local-direct` | 17 | 0.569 | 0.824 |
| [test_haiku_20260301_071232](runs/test_haiku_20260301_071232.md) | `csb_sdlc_test` | `mcp-remote-direct` | 8 | 0.780 | 1.000 |
| [test_haiku_20260301_192246](runs/test_haiku_20260301_192246.md) | `csb_sdlc_test` | `baseline-local-direct` | 4 | 0.128 | 0.250 |
| [test_haiku_20260301_192246](runs/test_haiku_20260301_192246.md) | `csb_sdlc_test` | `mcp-remote-direct` | 3 | 0.000 | 0.000 |
| [understand_haiku_20260224_001815](runs/understand_haiku_20260224_001815.md) | `csb_sdlc_understand` | `baseline-local-direct` | 20 | 0.533 | 0.650 |
| [understand_haiku_20260224_001815](runs/understand_haiku_20260224_001815.md) | `csb_sdlc_understand` | `mcp-remote-direct` | 20 | 0.679 | 0.850 |
| [understand_haiku_20260225_211346](runs/understand_haiku_20260225_211346.md) | `csb_sdlc_understand` | `baseline-local-direct` | 7 | 0.789 | 1.000 |
| [understand_haiku_20260225_211346](runs/understand_haiku_20260225_211346.md) | `csb_sdlc_understand` | `mcp-remote-direct` | 7 | 0.870 | 1.000 |
| [understand_haiku_20260301_031852](runs/understand_haiku_20260301_031852.md) | `csb_sdlc_understand` | `baseline-local-direct` | 20 | 0.728 | 0.850 |
| [understand_haiku_20260301_031852](runs/understand_haiku_20260301_031852.md) | `csb_sdlc_understand` | `mcp-remote-direct` | 20 | 0.832 | 0.950 |
| [understand_haiku_20260301_071233](runs/understand_haiku_20260301_071233.md) | `csb_sdlc_understand` | `baseline-local-direct` | 20 | 0.884 | 1.000 |
| [understand_haiku_20260301_071233](runs/understand_haiku_20260301_071233.md) | `csb_sdlc_understand` | `mcp-remote-direct` | 20 | 0.850 | 1.000 |

</details>

`index.html`, `data/official_results.json`, and `audits/*.json` provide GitHub-auditable artifacts.