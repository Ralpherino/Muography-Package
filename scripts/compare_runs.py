#!/usr/bin/env python3
"""Task: compare trigger efficiency between selected runs.

The runs are supplied on the command line rather than being hard-coded.

For each run, the script:
    1. loads the event data,
    2. reads the corresponding .sett metadata,
    3. calculates trigger efficiency,
    4. compares the efficiencies pairwise,
    5. checks whether the runs were taken at the same nominal HV.

If all selected runs have the same nominal voltage, they are treated as
candidate repeated-condition measurements and a count-weighted combined
efficiency is calculated.

If the nominal voltages differ, the comparison is still performed, but the
runs are not combined.
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from cli_common import add_common_arguments, prepare_paths
from mwpc_efficiency import calculate_trigger_efficiency
from mwpc_io import load_run, parse_sett_file, sett_path


def main() -> None:
    # Command-line arguments

    parser = argparse.ArgumentParser(description=__doc__)

    # Shared arguments:
    # --data-dir
    # --output-dir
    # --cache-dir
    # --no-cache
    add_common_arguments(parser)

    # Runs selected for comparison
    parser.add_argument(
        "--runs",
        type=int,
        nargs="+",
        required=True,
        help="Run numbers to compare",
    )

    args = parser.parse_args()

    # A comparison requires at least two runs
    if len(args.runs) < 2:
        parser.error("--runs requires at least two run numbers")

    prepare_paths(args)

    # Process selected runs

    rows: list[dict[str, object]] = []

    for run in args.runs:
        # Load the raw event data
        events = load_run(
            args.data_dir,
            run,
            cache_dir=args.cache_dir,
            use_cache=not args.no_cache,
        )

        # Read metadata from the matching .sett file
        metadata = parse_sett_file(
            sett_path(args.data_dir, run)
        )

        # Calculate trigger efficiency for this run
        result = calculate_trigger_efficiency(events)

        # Store everything in one row
        rows.append(
            {
                **metadata,
                **result,
                "n_events": len(events),
            }
        )

    # Build comparison table

    table = (
        pd.DataFrame(rows)
        .sort_values("run")
        .reset_index(drop=True)
    )

    table["efficiency_percent"] = (
        100.0 * table["trigger_efficiency"]
    )

    table["error_percent"] = (
        100.0 * table["trigger_error"]
    )

    # Check run conditions

    print("\nRUN CONDITIONS")
    print("--------------")

    for _, row in table.iterrows():
        print(
            f"Run {int(row['run'])}: "
            f"{float(row['hv_nominal']):g} V"
        )

    unique_voltages = set(
        float(value)
        for value in table["hv_nominal"]
    )

    same_voltage = len(unique_voltages) == 1

    if same_voltage:
        voltage = next(iter(unique_voltages))

        run_numbers = ", ".join(
            str(int(run))
            for run in table["run"]
        )

        print(
            f"\nRuns {run_numbers} were all taken at "
            f"{voltage:g} V."
        )

        print(
            "These runs are consistent with a "
            "repeated-condition comparison."
        )

    else:
        run_description = ", ".join(
            f"Run {int(row['run'])} "
            f"({float(row['hv_nominal']):g} V)"
            for _, row in table.iterrows()
        )

        print("\nWARNING")
        print("-------")

        print(
            f"{run_description} were taken under different "
            "nominal voltages."
        )

        print(
            "Comparison will proceed, but this is not a "
            "repeated-condition measurement."
        )

        print(
            "A count-weighted combined efficiency will therefore "
            "not be calculated."
        )

    # Print efficiency table

    print("\nRUN EFFICIENCIES")
    print("----------------")

    print(
        table[
            [
                "run",
                "hv_nominal",
                "n_events",
                "n_total_trigger",
                "n_good_trigger",
                "efficiency_percent",
                "error_percent",
                "note",
            ]
        ].to_string(
            index=False,
            float_format=lambda x: f"{x:.5f}",
        )
    )

    # Pairwise compatibility

    print("\nPAIRWISE COMPATIBILITY z VALUES")
    print("--------------------------------")

    for i in range(len(table)):
        for j in range(i + 1, len(table)):
            a = table.iloc[i]
            b = table.iloc[j]

            difference = abs(
                a["trigger_efficiency"]
                - b["trigger_efficiency"]
            )

            difference_error = np.sqrt(
                a["trigger_error"] ** 2
                + b["trigger_error"] ** 2
            )

            # Protect against division by zero
            if difference_error > 0:
                z = difference / difference_error
            else:
                z = np.nan

            print(
                f"Run {int(a['run'])} vs "
                f"Run {int(b['run'])}: "
                f"z = {z:.3f}"
            )

    # Count-weighted combination
    # Only meaningful here when all runs correspond to the same
    # nominal operating voltage.

    if same_voltage:
        combined_good = int(
            table["n_good_trigger"].sum()
        )

        combined_total = int(
            table["n_total_trigger"].sum()
        )

        combined_eff = (
            combined_good / combined_total
        )

        combined_error = np.sqrt(
            combined_eff
            * (1.0 - combined_eff)
            / combined_total
        )

        print("\nCOUNT-WEIGHTED COMBINATION")
        print("--------------------------")

        print(f"N_good  = {combined_good:,}")
        print(f"N_total = {combined_total:,}")

        print(
            f"epsilon = "
            f"{100.0 * combined_eff:.5f} %"
        )

        print(
            f"error   = "
            f"{100.0 * combined_error:.5f} "
            "percentage points"
        )

    else:
        print("\nCOUNT-WEIGHTED COMBINATION")
        print("--------------------------")

        print(
            "Skipped because the selected runs were taken "
            "at different nominal voltages."
        )

    # Save table

    output_file = (
        args.output_dir
        / "comparison_runs.csv"
    )

    table.to_csv(
        output_file,
        index=False,
    )

    print(f"\nSaved: {output_file}")


if __name__ == "__main__":
    main()