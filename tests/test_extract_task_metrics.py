import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.extract_task_metrics import process_task_dir, _normalize_first_relevant_metrics
from scripts.ccb_metrics.models import TaskMetrics


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

            self.assertEqual(tm.input_tokens, 1000)
            self.assertEqual(tm.output_tokens, 50)
            self.assertEqual(tm.cache_creation_tokens, 900)

            self.assertEqual(tm.metric_probe_input_tokens, 2)
            self.assertEqual(tm.metric_probe_output_tokens, 3)
            self.assertEqual(tm.metric_probe_cache_creation_tokens, 10)
            self.assertEqual(tm.metric_probe_cache_read_tokens, 20)
            self.assertEqual(tm.cache_read_tokens, 20)

    def test_first_relevant_metrics_are_clamped_and_consistent(self):
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

        _normalize_first_relevant_metrics(tm)

        self.assertEqual(tm.tokens_before_first_relevant, 10)
        self.assertEqual(tm.n_steps_to_first, 1)
        self.assertEqual(tm.agent_time_to_first_relevant, 2.5)


if __name__ == "__main__":
    unittest.main()
