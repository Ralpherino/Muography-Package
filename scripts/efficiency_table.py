#!/usr/bin/env python3
"""Task: calculate the efficiency table from the actual scan runs."""

from __future__ import annotations

import argparse

import pandas as pd

from cli_common import add_common_arguments, prepare_paths
from mwpc_config import set_detector
from mwpc_efficiency import calculate_run_efficiencies
from mwpc_io import load_run, parse_sett_file, sett_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_arguments(parser)
    parser.add_argument(
        "--runs",
        type=int,
        nargs="+",
        required=True,
        help="Run numbers forming the efficiency scan",
    )
    args = parser.parse_args()

    set_detector(args.detector)
    prepare_paths(args)

    rows: list[dict[str, object]] = []

    for run in args.runs:
        events = load_run(
            args.data_dir,
            run,
            cache_dir=args.cache_dir,
            use_cache=not args.no_cache,
        )
        metadata = parse_sett_file(sett_path(args.data_dir, run))
        efficiencies = calculate_run_efficiencies(events)
        rows.append({**metadata, **efficiencies, "n_events": len(events)})

    table = (
        pd.DataFrame(rows)
        .sort_values("hv_nominal")
        .reset_index(drop=True)
    )

    for quantity in ("trigger", "x", "y", "xy", "xy_joint"):
        table[f"{quantity}_percent"] = 100.0 * table[f"{quantity}_efficiency"]
        table[f"{quantity}_error_percent"] = 100.0 * table[f"{quantity}_error"]

    output_file = args.output_dir / "efficiency_scan_table.csv"
    table.to_csv(output_file, index=False)

    display_columns = [
        "run", "hv_nominal", "n_events",
        "n_total_trigger", "n_good_trigger",
        "trigger_percent", "trigger_error_percent",
        "x_percent", "x_error_percent",
        "y_percent", "y_error_percent",
        "xy_percent", "xy_error_percent",
    ]
    print(
        table[display_columns].to_string(
            index=False,
            float_format=lambda x: f"{x:.4f}",
        )
    )
    print(f"\nSaved: {output_file}")


if __name__ == "__main__":
    main()