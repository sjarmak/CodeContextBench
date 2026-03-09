import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.daytona_cost_guard import teardown_candidates


def write_job_config(job_dir: Path, task_id: str, config_name: str) -> None:
    payload = {
        "timeout_multiplier": 1.0,
        "environment": {
            "kwargs": {
                "label_task_id": task_id,
                "label_config": config_name,
                "task_source_dir": f"benchmarks/csb_sdlc_secure/{task_id}",
            }
        },
        "tasks": [{"path": f"benchmarks/csb_sdlc_secure/{task_id}"}],
    }
    (job_dir / "config.json").write_text(json.dumps(payload))


class DaytonaCostGuardTests(unittest.TestCase):
    def make_sandbox(self, *, run_id: str, task_id: str, config_name: str, created_hours_ago: float) -> dict:
        now = datetime.now(timezone.utc)
        created_at = now - timedelta(hours=created_hours_ago)
        updated_at = now - timedelta(minutes=5)
        return {
            "id": "sandbox-1",
            "name": "sandbox-1",
            "state": "SandboxState.STARTED",
            "created_at": created_at.isoformat(),
            "updated_at": updated_at.isoformat(),
            "hourly_burn_usd": 0.1,
            "labels": {
                "managed_by": "codescalebench",
                "run_id": run_id,
                "task_id": task_id,
                "config": config_name,
            },
        }

    def test_marks_active_sandbox_stale_when_local_result_exists(self):
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "run-1"
            job_dir = run_dir / "baseline-local-direct" / "2026-03-09__00-00-00"
            trial_dir = job_dir / "django-role-based-access-001__abc123"
            trial_dir.mkdir(parents=True)
            write_job_config(job_dir, "django-role-based-access-001", "baseline-local-direct")
            (trial_dir / "result.json").write_text("{}")

            run_index = {
                "run-1": {
                    "path": str(run_dir),
                    "mtime": datetime.now(timezone.utc),
                    "root": "runs/staging",
                }
            }
            registry = {
                "django-role-based-access-001": {
                    "timeouts": {"agent_sec": 900, "build_sec": 600},
                }
            }

            candidates = teardown_candidates(
                [self.make_sandbox(run_id="run-1", task_id="django-role-based-access-001", config_name="baseline-local-direct", created_hours_ago=0.1)],
                run_index,
                registry,
            )

            self.assertEqual(len(candidates), 1)
            self.assertIn("local result exists", candidates[0]["reason"])

    def test_marks_managed_sandbox_stale_after_timeout_budget(self):
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "run-2"
            job_dir = run_dir / "mcp-remote-direct" / "2026-03-09__00-00-00"
            trial_dir = job_dir / "django-audit-trail-implement-001__abc123"
            trial_dir.mkdir(parents=True)
            write_job_config(job_dir, "django-audit-trail-implement-001", "mcp-remote-direct")

            run_index = {
                "run-2": {
                    "path": str(run_dir),
                    "mtime": datetime.now(timezone.utc),
                    "root": "runs/staging",
                }
            }
            registry = {
                "django-audit-trail-implement-001": {
                    "timeouts": {"agent_sec": 600, "build_sec": 300},
                }
            }

            candidates = teardown_candidates(
                [self.make_sandbox(run_id="run-2", task_id="django-audit-trail-implement-001", config_name="mcp-remote-direct", created_hours_ago=2.0)],
                run_index,
                registry,
            )

            self.assertEqual(len(candidates), 1)
            self.assertIn("effective timeout budget", candidates[0]["reason"])

    def test_keeps_managed_sandbox_when_within_timeout_budget(self):
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "run-3"
            job_dir = run_dir / "baseline-local-direct" / "2026-03-09__00-00-00"
            trial_dir = job_dir / "django-repo-scoped-access-001__abc123"
            trial_dir.mkdir(parents=True)
            write_job_config(job_dir, "django-repo-scoped-access-001", "baseline-local-direct")

            run_index = {
                "run-3": {
                    "path": str(run_dir),
                    "mtime": datetime.now(timezone.utc),
                    "root": "runs/staging",
                }
            }
            registry = {
                "django-repo-scoped-access-001": {
                    "timeouts": {"agent_sec": 3600, "build_sec": 600},
                }
            }

            candidates = teardown_candidates(
                [self.make_sandbox(run_id="run-3", task_id="django-repo-scoped-access-001", config_name="baseline-local-direct", created_hours_ago=0.5)],
                run_index,
                registry,
            )

            self.assertEqual(candidates, [])


if __name__ == "__main__":
    unittest.main()
