#!/usr/bin/env python3
"""
Biomni Batch Experiment Runner

This script runs batch experiments for non-model organism gene literature curation.
It processes papers in batches using subprocess workers to avoid memory leaks.

Experiment modes:
- USE_MCP=True: Custom Biomni with MCP tools (NCBI Gene/Taxonomy queries)
- USE_MCP=False: Default Biomni without external tools
"""

import csv
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


# ==================== EXPERIMENT CONFIGURATION ====================
@dataclass
class ExperimentConfig:
    """Configuration for batch experiment."""

    use_mcp: bool = True  # True: Custom Biomni, False: Default Biomni
    batch_size: int = 30  # Papers per subprocess (smaller = less memory leak)
    start_index: int = 0  # Starting paper index (for resume)
    worker_script: str = "scripts/Biomni_experiment_worker.py"
    input_csv: str = "results/wf_pre_agent/FINAL_20251117_172057_20241201_20241203.csv"
    cooldown_seconds: int = 3  # Wait time between batches


# ==================== MAIN EXECUTION ====================
def run_batch_experiment(config: ExperimentConfig, project_root: Path) -> None:
    """
    Run the complete batch experiment.

    Args:
        config: Experiment configuration
        project_root: Root directory of the project
    """
    csv_path = project_root / config.input_csv

    # Count total papers in CSV
    with open(csv_path, "r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        total_papers = sum(1 for _ in reader)

    # Calculate batch ranges
    remaining_papers = total_papers - config.start_index
    batches = []

    current_index = config.start_index
    while current_index < total_papers:
        batch_end = min(current_index + config.batch_size, total_papers)
        batches.append((current_index, batch_end))
        current_index = batch_end

    # Print experiment info
    experiment_mode = (
        "Custom Biomni (with MCP tools)"
        if config.use_mcp
        else "Default Biomni (no MCP tools)"
    )
    print(f"\n{'=' * 80}")
    print("Biomni Batch Experiment")
    print(f"{'=' * 80}")
    print(f"Experiment Mode:        {experiment_mode}")
    print(f"CSV file:               {csv_path.name}")
    print(f"Total papers in CSV:    {total_papers}")
    print(f"Starting from index:    {config.start_index + 1}")
    print(f"Remaining papers:       {remaining_papers}")
    print(f"Number of batches:      {len(batches)}")
    print(f"Batch size:             {config.batch_size}")
    print(f"{'=' * 80}\n")

    # Execute batches sequentially
    for batch_num, (start_idx, end_idx) in enumerate(batches, 1):
        print(f"\n{'=' * 80}")
        print(f"Starting Batch {batch_num}/{len(batches)}")
        print(f"Papers: {start_idx + 1} to {end_idx}")
        print(f"{'=' * 80}\n")

        # Build worker command
        cmd = [
            sys.executable,
            str(project_root / config.worker_script),
            str(start_idx),
            str(end_idx),
            str(config.use_mcp),  # Pass MCP flag to worker
        ]

        batch_start_time = time.time()

        try:
            result = subprocess.run(
                cmd,
                cwd=str(project_root),
                check=True,
                capture_output=False,  # Show output in real-time
                text=True,
            )

            batch_elapsed = time.time() - batch_start_time
            print(f"\n✓ Batch {batch_num} completed in {batch_elapsed:.2f}s")

        except subprocess.CalledProcessError as e:
            print(f"\n✗ Batch {batch_num} failed with exit code {e.returncode}")
            print(f"Last successful index: {end_idx - 1}")
            print(f"\nTo resume, update START_INDEX to {end_idx} and re-run.")
            sys.exit(1)

        except KeyboardInterrupt:
            print(f"\n\nInterrupted by user at batch {batch_num}")
            print(f"Last completed index: {start_idx - 1}")
            print(f"\nTo resume, update START_INDEX to {start_idx} and re-run.")
            sys.exit(130)

        # Cooldown between batches
        if batch_num < len(batches):
            print(
                f"Cooling down for {config.cooldown_seconds} seconds before next batch..."
            )
            time.sleep(config.cooldown_seconds)

    print(f"\n{'=' * 80}")
    print("All batches completed successfully!")
    print(f"{'=' * 80}\n")


def main() -> None:
    """Main entry point for the experiment."""
    # Configure experiment
    config = ExperimentConfig(
        use_mcp=True,  # Change to False for default Biomni experiment
        batch_size=30,
        start_index=0,  # Update this to resume from a specific index
        worker_script="scripts/Biomni_experiment_worker.py",
        input_csv="results/wf_pre_agent/FINAL_20251117_172057_20241201_20241203.csv",
        cooldown_seconds=3,
    )

    # Get project root
    project_root = Path(__file__).parent.parent

    # Run experiment
    run_batch_experiment(config, project_root)


if __name__ == "__main__":
    main()
