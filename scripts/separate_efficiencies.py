#!/usr/bin/env python3
"""Task: create four separate efficiency plots and one 2x2 panel."""

from __future__ import annotations

import argparse

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from cli_common import add_common_arguments, prepare_paths
from mwpc_config import set_detector

PLOTS = (
    ("trigger_percent", "trigger_error_percent", "Trigger efficiency", "trigger"),
    ("x_percent", "x_error_percent", "X efficiency", "x"),
    ("y_percent", "y_error_percent", "Y efficiency", "y"),
    ("xy_percent", "xy_error_percent", "XY efficiency", "xy"),
)


def draw_one(ax: plt.Axes, table: pd.DataFrame, y: str, yerr: str, title: str) -> None:
    ax.errorbar(
        table["hv_nominal"],
        table[y],
        yerr=table[yerr],
        marker="o",
        capsize=3,
    )
    ax.set_title(title)
    ax.set_xlabel("High voltage (V)")
    ax.set_ylabel("Efficiency (%)")
    ax.set_ylim(0, 102)
    ax.grid(True, alpha=0.3)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_arguments(parser)
    parser.add_argument(
        "--table", 
        default="efficiency_scan_table.csv")
    
    args = parser.parse_args()
    prepare_paths(args)

    set_detector(args.detector)

    table_path = args.output_dir / args.table
    if not table_path.exists():
        raise FileNotFoundError(
            f"Missing {table_path}. Run 01_build_efficiency_table.py first."
        )
    table = pd.read_csv(table_path)

    # Four independent image files.
    for y, yerr, title, short_name in PLOTS:
        fig, ax = plt.subplots(figsize=(7, 5))
        draw_one(ax, table, y, yerr, title)
        fig.tight_layout()
        output_file = args.output_dir / f"figure3_{short_name}_efficiency.png"
        fig.savefig(output_file, dpi=200)
        plt.close(fig)
        print(f"Saved: {output_file}")

    # One combined 2x2 version.
    fig, axes = plt.subplots(2, 2, figsize=(10, 8), sharex=True, sharey=True)
    for ax, (y, yerr, title, _short_name) in zip(axes.flat, PLOTS, strict=True):
        draw_one(ax, table, y, yerr, title)
    fig.tight_layout()
    panel_file = args.output_dir / "efficiencies_2x2.png"
    fig.savefig(panel_file, dpi=200)
    plt.close(fig)
    print(f"Saved: {panel_file}")


if __name__ == "__main__":
    main()
