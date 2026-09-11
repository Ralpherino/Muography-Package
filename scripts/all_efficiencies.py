#!/usr/bin/env python3
"""Task: create Figure 2, all efficiencies versus high voltage."""

from __future__ import annotations

import argparse

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from cli_common import add_common_arguments, prepare_paths
from mwpc_config import set_detector

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_arguments(parser)
    parser.add_argument(
        "--table",
        type=str,
        default="efficiency_scan_table.csv",
        help="Efficiency CSV produced by 01_build_efficiency_table.py",
    )
    
    args = parser.parse_args()
    prepare_paths(args)

    set_detector(args.detector)

    table_path = args.output_dir / args.table
    if not table_path.exists():
        raise FileNotFoundError(
            f"Missing {table_path}. Run 01_build_efficiency_table.py first."
        )
    table = pd.read_csv(table_path)

    voltage = table["hv_nominal"]
    fig, ax = plt.subplots(figsize=(8, 6))

    # Every y value is 100 * epsilon; every error bar is 100 * sigma_epsilon.
    ax.errorbar(
        voltage,
        table["trigger_percent"],
        yerr=table["trigger_error_percent"],
        marker="o",
        capsize=3,
        label="Trigger",
    )
    ax.errorbar(
        voltage,
        table["x_percent"],
        yerr=table["x_error_percent"],
        marker="s",
        capsize=3,
        label="X",
    )
    ax.errorbar(
        voltage,
        table["y_percent"],
        yerr=table["y_error_percent"],
        marker="^",
        capsize=3,
        label="Y",
    )
    ax.errorbar(
        voltage,
        table["xy_percent"],
        yerr=table["xy_error_percent"],
        marker="D",
        capsize=3,
        label="XY = min(X, Y)",
    )

    ax.set_xlabel("High voltage (V)")
    ax.set_ylabel("Efficiency (%)")
    ax.set_ylim(0, 102)
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()

    output_file = args.output_dir / "all_efficiencies.png"
    fig.savefig(output_file, dpi=200)
    plt.close(fig)
    print(f"Saved: {output_file}")


if __name__ == "__main__":
    main()
