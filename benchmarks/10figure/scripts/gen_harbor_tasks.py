#!/usr/bin/env python3
"""
Generate Harbor tasks from 10Figure YAML task definitions.

Converts 10Figure task YAML files into Harbor task format:
- instruction.md - Human-readable task description
- task.toml - Harbor task metadata
- environment/Dockerfile - Task-specific container setup
- tests/test.sh - Validation script using validate_patch.py

Usage:
    ./gen_harbor_tasks.py --input ~/10Figure-Codebases/tasks --output tasks/
"""

import argparse
import json
import yaml
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class HarborTaskGenerator:
    """Generate Harbor task structure from 10Figure YAML."""

    def __init__(self, template_dir: Path, corpus_root: str = "/10figure"):
        self.template_dir = template_dir
        self.corpus_root = corpus_root
        self.jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))

    def load_10figure_task(self, yaml_path: Path) -> dict:
        """Load 10Figure task YAML."""
        with open(yaml_path) as f:
            return yaml.safe_load(f)

    def generate_instruction(self, task: dict) -> str:
        """Generate instruction.md from task metadata."""
        task_type = task.get('type', 'unknown')
        description = task.get('description', 'No description provided')

        # Type-specific instructions
        if task_type == 'cross_file_reasoning':
            start_symbol = task.get('start_symbol', 'UNKNOWN')
            goal = task.get('goal', 'Find implementation')
            instruction = f"""# Cross-File Reasoning Task

**Goal:** {goal}

**Starting Symbol:** `{start_symbol}`

**Description:** {description}

**Task:** Trace the call path of `{start_symbol}` through the codebase to find its actual implementation. The codebase contains multiple wrapper layers and indirection that you must navigate through.

Provide a summary of:
1. The call path from `{start_symbol}` to the final implementation
2. Key intermediate functions/methods encountered
3. The file and line number of the actual implementation

Make any necessary code changes to document your findings or fix issues discovered during tracing.
"""

        elif task_type == 'refactor_rename':
            old_name = task.get('symbol_to_rename', 'UNKNOWN')
            new_name = task.get('new_name', 'UNKNOWN_NEW')
            goal = task.get('goal', 'Rename symbol')
            instruction = f"""# Refactor/Rename Task

**Goal:** {goal}

**Symbol to Rename:** `{old_name}` → `{new_name}`

**Description:** {description}

**Task:** Rename the symbol `{old_name}` to `{new_name}` throughout the codebase. This includes:
1. The original definition/declaration
2. All references and call sites
3. Any documentation or comments that mention it

Ensure the codebase remains functionally equivalent after the rename.
"""

        elif task_type == 'api_upgrade':
            old_api = task.get('old_api', task.get('old_api_pattern', 'UNKNOWN'))
            new_api = task.get('new_api', task.get('new_api_pattern', 'UNKNOWN'))
            goal = task.get('goal', 'Upgrade API usage')
            instruction = f"""# API Upgrade Task

**Goal:** {goal}

**Migration:** `{old_api}` → `{new_api}`

**Description:** {description}

**Task:** Migrate all usages of the deprecated API pattern `{old_api}` to the new API pattern `{new_api}`.

Find all call sites that use the old pattern and update them to use the new pattern correctly. The new API may have different:
- Parameter order or naming
- Return types
- Error handling requirements

Use Deep Search to find examples of correct usage of the new API if available.
"""

        elif task_type == 'bug_localization':
            error_msg = task.get('error_message', task.get('bug_symptom', 'Unknown error'))
            symptoms = task.get('symptoms', [])
            symptoms_text = '\n'.join(f'- {s}' for s in symptoms) if symptoms else 'See description'
            goal = task.get('goal', 'Localize and fix bug')
            instruction = f"""# Bug Localization Task

**Goal:** {goal}

**Error Message:** {error_msg}

**Symptoms:**
{symptoms_text}

**Description:** {description}

**Task:** Localize the bug causing the error "{error_msg}" and provide a fix.

Steps:
1. Identify the root cause of the bug
2. Find the file(s) and line(s) where the bug exists
3. Implement a fix that resolves the issue
4. Verify the fix doesn't introduce new problems

Use Deep Search to find similar bugs or related code patterns that might help with localization.
"""

        else:
            instruction = f"""# {task_type.replace('_', ' ').title()} Task

**Description:** {description}

**Goal:** {task.get('goal', 'Complete the task')}

**Task ID:** {task.get('task_id', 'unknown')}
"""

        # Add time limit and difficulty
        time_limit = task.get('max_time_minutes', 15)
        difficulty = task.get('difficulty', 'medium')

        instruction += f"""
---

**Time Limit:** {time_limit} minutes
**Difficulty:** {difficulty}

**Important:** All changes should be made as git commits in the repository. Your patch will be evaluated by comparing the git diff against expected outcomes.
"""

        return instruction

    def generate_task_toml(self, task: dict, repo_name: str) -> str:
        """Generate task.toml Harbor metadata."""
        task_id = task.get('task_id', 'unknown')
        task_type = task.get('type', 'unknown')
        max_time = task.get('max_time_minutes', 15)
        description = task.get('description', 'No description')

        toml_content = f"""[metadata]
name = "{task_id}"
description = "{description}"
license = "MIT"

[task]
id = "{task_id}"
type = "{task_type}"
max_time_minutes = {max_time}
difficulty = "{task.get('difficulty', 'medium')}"

[environment]
# Repository path will be injected by the base image
repo_name = "{repo_name}"
repo_path = "{self.corpus_root}/src/{repo_name}"

[scoring]
# Scoring is handled by validate_patch.py using ground truth
ground_truth = "{task.get('ground_truth', 'scoring/oracle/expected.json')}"
"""
        return toml_content

    def generate_dockerfile(self, task: dict, base_image: str = "harbor-10figure:base") -> str:
        """Generate environment/Dockerfile.

        Note: Using short image name without registry prefix so Docker buildkit
        can find it in local cache. The image should exist locally as both
        'harbor-10figure:base' and 'docker.io/library/harbor-10figure:base'.
        """
        return f"""FROM {base_image}

# Task-specific setup (if needed)
# The base image already contains the 10Figure corpus and validator

WORKDIR /workspace
"""

    def generate_task(self, yaml_path: Path, output_dir: Path, repo_name: str = "kubernetes"):
        """Generate complete Harbor task from 10Figure YAML."""
        logger.info(f"Generating Harbor task from {yaml_path.name}")

        # Load task
        task = self.load_10figure_task(yaml_path)
        task_id = task.get('task_id', yaml_path.stem)

        # Create task directory
        task_dir = output_dir / task_id
        task_dir.mkdir(parents=True, exist_ok=True)

        # Generate instruction.md
        instruction = self.generate_instruction(task)
        (task_dir / "instruction.md").write_text(instruction)
        logger.info(f"  ✓ instruction.md")

        # Generate task.toml
        task_toml = self.generate_task_toml(task, repo_name)
        (task_dir / "task.toml").write_text(task_toml)
        logger.info(f"  ✓ task.toml")

        # Copy task.yaml for validator with fixed paths
        import shutil
        # Fix ground_truth path to be absolute
        if 'ground_truth' in task and not task['ground_truth'].startswith('/'):
            task['ground_truth'] = f"{self.corpus_root}/{task['ground_truth']}"
        (task_dir / "task.yaml").write_text(yaml.dump(task))
        logger.info(f"  ✓ task.yaml (with fixed paths)")

        # Generate environment/Dockerfile
        env_dir = task_dir / "environment"
        env_dir.mkdir(exist_ok=True)
        dockerfile = self.generate_dockerfile(task)
        (env_dir / "Dockerfile").write_text(dockerfile)
        logger.info(f"  ✓ environment/Dockerfile")

        # Generate tests/test.sh from template
        tests_dir = task_dir / "tests"
        tests_dir.mkdir(exist_ok=True)
        template = self.jinja_env.get_template("test.sh.j2")
        test_script = template.render(corpus_root=self.corpus_root)
        test_sh = tests_dir / "test.sh"
        test_sh.write_text(test_script)
        test_sh.chmod(0o755)
        logger.info(f"  ✓ tests/test.sh")

        # Create repo_path file for BasePatchAgent
        (task_dir / "repo_path").write_text(f"{self.corpus_root}/src/{repo_name}\n")
        logger.info(f"  ✓ repo_path")

        logger.info(f"✅ Generated Harbor task: {task_dir}")

    def generate_all(self, input_dir: Path, output_dir: Path, repo_name: str = "kubernetes"):
        """Generate all Harbor tasks from directory of 10Figure YAMLs."""
        yaml_files = sorted(input_dir.glob("*.yaml"))

        # Filter out repos.yaml
        task_files = [f for f in yaml_files if f.name != "repos.yaml"]

        logger.info(f"Found {len(task_files)} task files in {input_dir}")

        for yaml_file in task_files:
            try:
                self.generate_task(yaml_file, output_dir, repo_name)
            except Exception as e:
                logger.error(f"Failed to generate task from {yaml_file.name}: {e}")

        logger.info(f"\n✅ Generated {len(task_files)} Harbor tasks in {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Generate Harbor tasks from 10Figure YAML definitions")
    parser.add_argument("--input", required=True, help="Input directory with 10Figure task YAMLs")
    parser.add_argument("--output", required=True, help="Output directory for Harbor tasks")
    parser.add_argument("--templates", default="templates", help="Template directory (default: templates)")
    parser.add_argument("--repo", default="kubernetes", help="Repository name (default: kubernetes)")
    parser.add_argument("--corpus-root", default="/10figure", help="Corpus root path in container")

    args = parser.parse_args()

    input_dir = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output).expanduser().resolve()
    template_dir = Path(args.templates).expanduser().resolve()

    if not input_dir.exists():
        logger.error(f"Input directory not found: {input_dir}")
        return 1

    if not template_dir.exists():
        logger.error(f"Template directory not found: {template_dir}")
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    generator = HarborTaskGenerator(template_dir, args.corpus_root)
    generator.generate_all(input_dir, output_dir, args.repo)

    return 0


if __name__ == "__main__":
    exit(main())
