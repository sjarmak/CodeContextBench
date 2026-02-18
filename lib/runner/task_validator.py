"""Validator to ensure baseline and hybrid runs complete all assigned tasks."""

import json
from pathlib import Path
from typing import Optional


class TaskValidator:
    """Validates that paired runs completed the same set of tasks."""
    
    def __init__(self, jobs_dir: Path, output_dir: Path):
        self.jobs_dir = Path(jobs_dir)
        self.output_dir = Path(output_dir)
    
    def validate_pair_tasks(self, baseline_job_id: str, mcp_job_id: str) -> dict:
        """
        Validate that both runs in a pair completed the same tasks.
        
        Args:
            baseline_job_id: Harbor job ID for baseline run
            mcp_job_id: Harbor job ID for MCP run
        
        Returns:
            dict with validation results:
            {
                "is_valid": bool,
                "baseline_tasks": set,
                "mcp_tasks": set,
                "missing_in_baseline": set,
                "missing_in_mcp": set,
                "common_tasks": int,
                "baseline_total": int,
                "mcp_total": int
            }
        """
        baseline_result = self._get_job_result(baseline_job_id)
        mcp_result = self._get_job_result(mcp_job_id)
        
        baseline_tasks = self._extract_task_ids(baseline_result)
        mcp_tasks = self._extract_task_ids(mcp_result)
        
        missing_in_baseline = mcp_tasks - baseline_tasks
        missing_in_mcp = baseline_tasks - mcp_tasks
        
        return {
            "is_valid": missing_in_baseline == set() and missing_in_mcp == set(),
            "baseline_tasks": baseline_tasks,
            "mcp_tasks": mcp_tasks,
            "missing_in_baseline": missing_in_baseline,
            "missing_in_mcp": missing_in_mcp,
            "common_tasks": len(baseline_tasks & mcp_tasks),
            "baseline_total": len(baseline_tasks),
            "mcp_total": len(mcp_tasks),
        }
    
    def _get_job_result(self, job_id: str) -> Optional[dict]:
        """Load Harbor job result.json."""
        result_path = self.jobs_dir / job_id / "result.json"
        if not result_path.exists():
            return None
        
        with open(result_path) as f:
            return json.load(f)
    
    def _extract_task_ids(self, result: dict) -> set:
        """Extract unique task instance IDs from Harbor result."""
        if not result or "stats" not in result:
            return set()
        
        tasks = set()
        
        # Extract from reward_stats
        evals = result["stats"].get("evals", {})
        for eval_data in evals.values():
            reward_stats = eval_data.get("reward_stats", {})
            for reward_value, task_list in reward_stats.get("reward", {}).items():
                for task_instance in task_list:
                    # Extract base task ID (remove trailing __hash)
                    base_id = task_instance.rsplit("__", 1)[0]
                    tasks.add(base_id)
        
        return tasks


def check_and_log_pairing_integrity(jobs_dir: Path, output_dir: Path, pair_specs: list) -> bool:
    """
    Check all pairs for task completeness.
    
    Args:
        jobs_dir: Harbor jobs directory
        output_dir: v2 output directory  
        pair_specs: List of PairSpec objects from MatrixExpander
    
    Returns:
        True if all pairs have matching task sets, False otherwise
    """
    validator = TaskValidator(jobs_dir, output_dir)
    all_valid = True
    
    for pair in pair_specs:
        result = validator.validate_pair(pair.baseline_run_id, pair.mcp_run_id)
        
        if not result["is_valid"]:
            all_valid = False
            print(f"\n⚠️  PAIRING MISMATCH - {pair.pair_id}")
            print(f"   Baseline: {result['baseline_total']} tasks")
            print(f"   MCP ({pair.mcp_mode}): {result['mcp_total']} tasks")
            print(f"   Common: {result['common_tasks']} tasks")
            
            if result["missing_in_baseline"]:
                print(f"   Missing in baseline: {len(result['missing_in_baseline'])} tasks")
                for task in sorted(result["missing_in_baseline"])[:5]:
                    print(f"     - {task}")
            
            if result["missing_in_mcp"]:
                print(f"   Missing in {pair.mcp_mode}: {len(result['missing_in_mcp'])} tasks")
                for task in sorted(result["missing_in_mcp"])[:5]:
                    print(f"     - {task}")
        else:
            print(f"✓ {pair.pair_id}: {result['baseline_total']} tasks (matched)")
    
    return all_valid
