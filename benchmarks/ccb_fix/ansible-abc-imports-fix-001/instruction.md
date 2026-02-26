# Inconsistent Use and Dependencies on the Internal Shim for Importing Collection ABCs

**Repository:** ansible/ansible
**Language:** Python
**Difficulty:** hard

## Problem

In various parts of the Ansible codebase (modules, `module_utils`, and controller code), abstract collection classes (ABCs such as `Mapping`, `Sequence`, etc.) continue to be imported from the internal compatibility module `ansible.module_utils.common._collections_compat`. This shim was created for temporary compatibility, and its continued direct use promotes undesired internal paths. The coexistence of internal and supported paths creates inconsistency, confusion for contributors, and conflicting signals in style/sanity checks, in addition to increasing technical debt.

## Key Components

- `lib/ansible/module_utils/common/_collections_compat.py` — the internal shim being migrated away from
- Module and utility files under `lib/ansible/modules/` and `lib/ansible/module_utils/` that import ABCs
- Sanity/lint check configuration that may still reference or allow internal paths

## Task

1. Identify all imports of `ansible.module_utils.common._collections_compat` across modules, `module_utils`, and controller code
2. Replace those imports with the supported canonical path (e.g., direct `collections.abc` imports)
3. Ensure the compatibility shim remains as a re-export layer for backward compatibility but is no longer directly imported internally
4. Verify that style/sanity checks are aligned with the new policy and do not recommend the obsolete internal path
5. Run the existing test suite to ensure no regressions

## Success Criteria

- No internal code directly imports from `_collections_compat` (only external consumers via backward compatibility)
- All ABCs are imported from the supported canonical path consistently
- Sanity checks are aligned with the updated import policy
- All existing tests pass

---

**Base commit:** `e658995760ac1209cb12df97027a2e282b4536ae`
**Instance ID:** `instance_ansible__ansible-379058e10f3dbc0fdcaf80394bd09b18927e7d33-v1055803c3a812189a1133297f7f5468579283f86`
