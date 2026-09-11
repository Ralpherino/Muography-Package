#!/usr/bin/env python3
"""Run the complete modular analysis in the correct order."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


SCRIPTS = (
    "00_inspect_run.py",
    "01_build_efficiency_table.py",
    "02_figure2_all_efficiencies.py",
    "03_figure3_separate_efficiencies.py",
    "04_figure4_angular_distributions.py",
    "05_figure5_angular_map.py",
    "06_figure6_y_slice.py",
    "07_figure7_flux.py",
    "08_compare_1650_runs.py",
)

TRACKING_SCRIPTS = {
    "04_figure4_angular_distributions.py",
    "05_figure5_angular_map.py",
    "06_figure6_y_slice.py",
    "07_figure7_flux.py",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("."))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--cache-dir", type=Path, default=Path("cache"))
    parser.add_argument("--tracking-run", type=int, default=200)
    parser.add_argument(
        "--time-mode",
        choices=("report", "timestamps"),
        default="timestamps",
    )
    parser.add_argument("--no-cache", action="store_true")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    common_args = [
        "--data-dir", str(args.data_dir),
        "--output-dir", str(args.output_dir),
        "--cache-dir", str(args.cache_dir),
    ]
    if args.no_cache:
        common_args.append("--no-cache")

    for script_name in SCRIPTS:
        command = [sys.executable, str(script_dir / script_name), *common_args]
        if script_name in TRACKING_SCRIPTS:
            command.extend(
                [
                    "--run",
                    str(args.tracking_run),
                    "--time-mode",
                    args.time_mode,
                ]
            )

        print("\n" + "=" * 80)
        print("RUNNING:", " ".join(command))
        print("=" * 80)
        subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
