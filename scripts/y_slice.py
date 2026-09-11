#!/usr/bin/env python3
"""Task: apply |Delta Y_strip| <= 1 and plot the theta_x distribution."""

from __future__ import annotations

import argparse

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cli_common import add_common_arguments, prepare_paths

from mwpc_tracking import (
    effective_area_report,
    projected_solid_angle,
    resolve_measurement_time,
    select_y_slice,
)
from mwpc_io import load_run
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
        default=1,
        help="Keep |Delta Y_strip| <= this value",
    )

    parser.add_argument(
    "--time-mode",
    choices=("report", "timestamps"),
    default="timestamps",
    )

    parser.add_argument(
        "--report-time-s",
        type=float,
        default=3600.0,
    )

    parser.add_argument(
        "--theta-y-low-deg",
        type=float,
        default=-5.0,
    )

    parser.add_argument(
        "--theta-y-high-deg",
        type=float,
        default=5.0,
    )

    parser.add_argument("--bin-width-deg", type=float, default=5.0)
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
    events = load_run(
    args.data_dir,
    args.run,
    cache_dir=args.cache_dir,
    use_cache=not args.no_cache,
    )


    selected = select_y_slice(tracks, args.max_dy_strip)

    edges = np.arange(
        -65.0,
        65.0 + args.bin_width_deg,
        args.bin_width_deg,
    )

    counts, _ = np.histogram(
        selected["theta_x_deg"],
        bins=edges,
    )

    centres = 0.5 * (
        edges[:-1] + edges[1:]
    )

    effective_area_cm2 = effective_area_report(
        centres
    )

    solid_angle_sr = np.array(
        [
            projected_solid_angle(
                low,
                high,
                args.theta_y_low_deg,
                args.theta_y_high_deg,
            )
            for low, high in zip(
                edges[:-1],
                edges[1:],
                strict=True,
            )
        ]
    )

    measurement_time_s = resolve_measurement_time(
        events,
        time_mode=args.time_mode,
        report_time_s=args.report_time_s,
    )

    denominator = (
        effective_area_cm2
        * measurement_time_s
        * solid_angle_sr
    )

    flux = np.full_like(
        counts,
        np.nan,
        dtype=float,
    )

    flux_error = np.full_like(
        counts,
        np.nan,
        dtype=float,
    )

    valid = denominator > 0.0

    flux[valid] = (
        counts[valid]
        / denominator[valid]
    )

    flux_error[valid] = (
        np.sqrt(counts[valid])
        / denominator[valid]
    )

    fig, ax = plt.subplots(figsize=(9, 6))

    ax.errorbar(
        centres[valid],
        flux[valid],
        yerr=flux_error[valid],
        fmt="o",
        capsize=3,
    )

    ax.set_xlabel(r"$\theta_x$ (deg)")
    ax.set_ylabel(
        r"Flux (cm$^{-2}$ s$^{-1}$ sr$^{-1}$)"
    )

    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    output_file = args.output_dir / "theta_x_y_slice_flux.png"

    fig.savefig(output_file, dpi=200)
    plt.close(fig)

    selected_file = args.output_dir / f"run{args.run}_y_slice_events.csv"
    selected[
        [
            "event_id",
            "date_time",
            "delta_x_strip",
            "delta_y_strip",
            "theta_x_deg",
            "theta_y_deg",
            "theta_deg",
        ]
    ].to_csv(selected_file, index=False)

    print(f"Valid endpoint tracks: {len(tracks):,}")
    print(f"Selected events:       {len(selected):,}")
    print(f"Saved: {output_file}")
    print(f"Saved: {selected_file}")


if __name__ == "__main__":
    main()
