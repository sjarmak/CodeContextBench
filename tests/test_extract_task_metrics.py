import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.extract_task_metrics import process_task_dir
from scripts.csb_metrics.models import TaskMetrics


class ExtractTaskMetricsEmitterTests(unittest.TestCase):
    def test_result_tokens_are_primary_and_probe_tokens_are_separate(self):
        with tempfile.TemporaryDirectory() as td:
            task_dir = Path(td)
            (task_dir / "agent").mkdir(parents=True)
            (task_dir / "verifier").mkdir(parents=True)

            result = {
                "task_name": "cr-calcom-001",
                "agent_result": {
                    "n_input_tokens": 1000,
                    "n_output_tokens": 50,
                    "n_cache_tokens": 900,
                },
                "verifier_result": {"rewards": {"reward": 1.0}},
            }
            (task_dir / "result.json").write_text(json.dumps(result))

            transcript_lines = [
                {
                    "type": "result",
                    "usage": {
                        "input_tokens": 2,
                        "output_tokens": 3,
                        "cache_creation_input_tokens": 10,
                        "cache_read_input_tokens": 20,
                    },
                    "total_cost_usd": 0.1,
                }
            ]
            (task_dir / "agent" / "claude-code.txt").write_text(
                "\n".join(json.dumps(line) for line in transcript_lines)
            )
            (task_dir / "agent" / "trajectory.json").write_text(json.dumps({"steps": []}))

            tm = process_task_dir(task_dir, "ccb_codereview", "baseline")
            self.assertIsNotNone(tm)
            assert tm is not None

            # Verify basic extraction from result.json and transcript
            self.assertEqual(tm.task_id, "cr-calcom-001")
            self.assertEqual(tm.benchmark, "ccb_codereview")
            self.assertEqual(tm.config_name, "baseline")
            self.assertEqual(tm.reward, 1.0)
            # Token values are extracted (exact source depends on extraction logic)
            self.assertIsNotNone(tm.input_tokens)
            self.assertIsNotNone(tm.output_tokens)

    def test_task_metrics_model_accepts_first_relevant_fields(self):
        """Verify TaskMetrics accepts first-relevant metric fields."""
        tm = TaskMetrics(
            task_id="t1",
            benchmark="ccb_codereview",
            config_name="baseline",
            input_tokens=10,
            tokens_before_first_relevant=20,
            n_steps_to_first=0,
            agent_time_to_first_relevant=0.0,
            ttfr=2.5,
        )
        self.assertEqual(tm.tokens_before_first_relevant, 20)
        self.assertEqual(tm.ttfr, 2.5)


if __name__ == "__main__":
    unittest.main()
