# Governance Benchmark — Repository Mirrors

Repos used by `ccb_governance` tasks, with commit SHAs and Sourcegraph indexing status.

## Repos

| Task | Repo | Commit SHA | SG Mirror | Indexed |
|------|------|-----------|-----------|---------|
| repo-scoped-access-001 | django/django | `674eda1c03a3187905f48afee0f15226aa62fdf3` | `sg-benchmarks/django--674eda1c` | Yes (shared with crossrepo) |
| repo-scoped-access-002 | flipt-io/flipt | `3d5a345f94c2adc8a0eaa102c189c08ad4c0f8e8` | `sg-benchmarks/flipt--3d5a345f` | Yes (shared with swebenchpro) |
| sensitive-file-exclusion-001 | django/django | `674eda1c03a3187905f48afee0f15226aa62fdf3` | `sg-benchmarks/django--674eda1c` | Yes (shared with crossrepo) |

## Notes

- Both repos are already indexed in Sourcegraph via existing `sg-benchmarks` mirrors — no new mirrors needed.
- Django mirror `sg-benchmarks/django--674eda1c` is shared with CrossRepo benchmark tasks.
- Flipt mirror `sg-benchmarks/flipt--3d5a345f` is shared with SWE-bench Pro tasks.
- All commits are pinned — Dockerfiles use `git checkout <SHA>`, not HEAD or tags.
