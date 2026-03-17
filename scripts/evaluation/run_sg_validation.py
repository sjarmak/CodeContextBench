#!/usr/bin/env python3
"""Run sourcegraph validation tasks via Daytona.

Usage:
  # Dry run (validate setup, no sandboxes)
  source .env.local && python3 scripts/run_sg_validation.py --dry-run

  # Run all 6 tasks with Haiku baseline (OAuth subscription)
  source .env.local && python3 scripts/run_sg_validation.py --auth oauth

  # Run just SDLC tasks
  source .env.local && python3 scripts/run_sg_validation.py --auth oauth \\
      --tasks sg-gitlab-ratelimit-fix-001,sg-deepsearch-imgbomb-fix-001,sg-deepsearch-anchor-fix-001

  # Run just org-scale tasks
  source .env.local && python3 scripts/run_sg_validation.py --auth oauth \\
      --tasks ccx-sgauth-301,ccx-sgcompletion-302,ccx-sgencrypt-305
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

SG_REGISTRY = REPO_ROOT / "scripts" / "sg_validation_registry.json"
SG_RUNS_DIR = REPO_ROOT / "runs" / "sg_validation"

import daytona_runner  # noqa: E402

# Monkey-patch the TaskRegistry class to use our custom registry by default
_orig_init = daytona_runner.TaskRegistry.__init__


def _patched_init(self, registry_path=SG_REGISTRY):
    _orig_init(self, registry_path)


daytona_runner.TaskRegistry.__init__ = _patched_init
daytona_runner.RUNS_DIR = SG_RUNS_DIR

if __name__ == "__main__":
    daytona_runner.main()
