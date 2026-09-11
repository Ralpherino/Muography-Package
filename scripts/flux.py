#!/usr/bin/env python3
"""Task: calculate and plot the report-style angular muon flux.

For angular bin i:
    Phi_i = N_i / (A_i * t * DeltaOmega_i)

Report-style effective area:
    A_i = L * (L - h tan(alpha_i)) * cos(alpha_i)
    alpha_i = |theta_x,i|

Poisson counting uncertainty:
    sigma_Phi,i = sqrt(N_i) / (A_i * t * DeltaOmega_i)
"""

from __future__ import annotations

import argparse

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cli_common import add_common_arguments, prepare_paths
from mwpc_io import load_run
from mwpc_tracking import (
    effective_area_report,
    projected_solid_angle,
    select_y_slice,
    timestamp_span_seconds,
)
from mwpc_config import set_detector


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_arguments(parser)
    parser.add_argument(
    "--run",
    type=int,
    required=True,
    help="Run number to analyse",)

    parser.add_argument(
        "--max-dy-strip", 
        type=int, 
        default=1)
    
    parser.add_argument(
        "--theta-x-min", 
        type=float, 
        default=-50.0)
    
    parser.add_argument(
        "--theta-x-max", 
        type=float, 
        default=50.0)
    
    parser.add_argument(
        "--bin-width-deg", 
        type=float, 
        default=10.0)
    
    parser.add_argument(
        "--theta-y-low-deg",
        type=float,
        default=-5.0,
        help="Lower theta_y boundary used in DeltaOmega",
    )

    parser.add_argument(
        "--theta-y-high-deg",
        type=float,
        default=5.0,
        help="Upper theta_y boundary used in DeltaOmega",
    )

    parser.add_argument(
        "--time-mode",
        choices=("report", "timestamps"),
        default="timestamps",
        help="Use report's 3600 s or exact timestamp span",
    )

    parser.add_argument(
        "--report-time-s",
        type=float,
        default=3600.0,
        help="Measurement time when --time-mode report is used",
    )

    parser.add_argument(
        "--tracks-file",
        type=str,
        default=None,
        help=(
            "Endpoint-track CSV produced by 04_figure4_angular_distributions.py. "
            "Default: <output-dir>/run<run>_endpoint_tracks.csv"
        ),
    )
    args = parser.parse_args()
    prepare_paths(args)

    set_detector(args.detector)

    # Raw events are still needed here (only here) to get the true timestamp
    # span of the full run for --time-mode timestamps; the track reconstruction
    # itself is NOT redone, it is read back from 04's output below.
    events = load_run(
        args.data_dir,
        args.run,
        cache_dir=args.cache_dir,
        use_cache=not args.no_cache,
    )

    tracks_path = (
        args.output_dir / f"run{args.run}_endpoint_tracks.csv"
        if args.tracks_file is None
        else args.output_dir / args.tracks_file
    )
    if not tracks_path.exists():
        raise FileNotFoundError(
            f"Missing {tracks_path}. Run 04_figure4_angular_distributions.py first."
        )
    tracks = pd.read_csv(tracks_path, parse_dates=["date_time"])
    selected = select_y_slice(tracks, args.max_dy_strip)

    edges = np.arange(
        args.theta_x_min,
        args.theta_x_max + args.bin_width_deg,
        args.bin_width_deg,
    )
    counts, _ = np.histogram(selected["theta_x_deg"], bins=edges)
    centres = 0.5 * (edges[:-1] + edges[1:])

    # A_i in cm^2.
    effective_area_cm2 = effective_area_report(centres)
    if np.any(effective_area_cm2 <= 0):
        raise ValueError(
            "At least one angular bin has non-positive geometrical overlap. "
            "Reduce the angular range."
        )

    # DeltaOmega_i in sr, evaluated by integrating the projected-angle Jacobian.
    solid_angle_sr = np.array(
        [
            projected_solid_angle(
                low,
                high,
                args.theta_y_low_deg,
                args.theta_y_high_deg,
            )
            for low, high in zip(edges[:-1], edges[1:], strict=True)
        ]
    )

    timestamp_time_s = timestamp_span_seconds(events)
    measurement_time_s = (
        args.report_time_s if args.time_mode == "report" else timestamp_time_s
    )

    denominator = effective_area_cm2 * measurement_time_s * solid_angle_sr
    flux = counts / denominator
    flux_error = np.sqrt(counts) / denominator

    table = pd.DataFrame(
        {
            "theta_x_low_deg": edges[:-1],
            "theta_x_high_deg": edges[1:],
            "theta_x_center_deg": centres,
            "counts": counts,
            "effective_area_cm2": effective_area_cm2,
            "solid_angle_sr": solid_angle_sr,
            "measurement_time_s": measurement_time_s,
            "flux_cm-2_s-1_sr-1": flux,
            "stat_error_cm-2_s-1_sr-1": flux_error,
        }
    )
    table_file = args.output_dir / "flux_table.csv"
    table.to_csv(table_file, index=False)

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.errorbar(centres, flux, yerr=flux_error, fmt="o", capsize=3)
    ax.set_xlabel(r"$\theta_x$ (deg)")
    ax.set_ylabel(r"Flux (cm$^{-2}$ s$^{-1}$ sr$^{-1}$)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    plot_file = args.output_dir / "flux.png"
    fig.savefig(plot_file, dpi=200)
    plt.close(fig)

    print(f"Run events:              {len(events):,}")
    print(f"Valid endpoint tracks:   {len(tracks):,}")
    print(f"Events in Y slice:       {len(selected):,}")
    print(f"Timestamp span:          {timestamp_time_s:.1f} s")
    print(f"Time used in flux:       {measurement_time_s:.1f} s")
    print(f"Saved: {table_file}")
    print(f"Saved: {plot_file}")


if __name__ == "__main__":
    main()
