#!/usr/bin/env python3
"""Generate Figures 4-7 for one selected run."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


TRACKING_SCRIPTS = (
    "04_figure4_angular_distributions.py",
    "05_figure5_angular_map.py",
    "06_figure6_y_slice.py",
    "07_figure7_flux.py",
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=int, required=True)
    parser.add_argument("--data-dir", type=Path, default=Path("."))
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--cache-dir", type=Path, default=Path("cache"))
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument(
        "--time-mode",
        choices=("report", "timestamps"),
        default="timestamps",
        help="Time convention passed to the flux script",
    )
    parser.add_argument("--max-dy-strip", type=int, default=1)
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    output_dir = args.output_dir or Path("outputs") / f"run{args.run}"

    common_args = [
        "--run", str(args.run),
        "--data-dir", str(args.data_dir),
        "--output-dir", str(output_dir),
        "--cache-dir", str(args.cache_dir),
    ]
    if args.no_cache:
        common_args.append("--no-cache")

    for script_name in TRACKING_SCRIPTS:
        command = [sys.executable, str(script_dir / script_name), *common_args]

    if script_name in {
        "04_figure4_angular_distributions.py",
        "05_figure5_angular_map.py",
        "06_figure6_y_slice.py",
        "07_figure7_flux.py",
    }:
        command.extend(
            [
                "--time-mode",
                args.time_mode,
            ]
        )

    if script_name in {
        "06_figure6_y_slice.py",
        "07_figure7_flux.py",
    }:
        command.extend(
            [
                "--max-dy-strip",
                str(args.max_dy_strip),
            ]
        )

        print("\n" + "=" * 80)
        print("RUNNING:", " ".join(command))
        print("=" * 80)
        subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
