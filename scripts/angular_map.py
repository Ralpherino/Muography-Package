#!/usr/bin/env python3
"""Task: create the two-dimensional theta_x versus theta_y map."""

from __future__ import annotations

import argparse

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import pandas as pd

from cli_common import add_common_arguments, prepare_paths
from mwpc_io import load_run
from mwpc_tracking import(
    build_angular_flux_grid,
    resolve_measurement_time,
)
from mwpc_config import get_config, set_detector

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_arguments(parser)
    parser.add_argument(
    "--run",
    type=int,
    required=True,
    help="Run number to analyse",)
    parser.add_argument("--bin-width-deg", type=float, default=5.0)

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

    measurement_time_s = resolve_measurement_time(
        events,
        time_mode=args.time_mode,
        report_time_s=args.report_time_s,
    )


    # Every event contributes one point (theta_x, theta_y). hist2d counts the
    # number of points in each rectangular angular bin.
    x_edges = np.arange(
        -65.0,
        65.0 + args.bin_width_deg,
        args.bin_width_deg,
    )

    y_edges = np.arange(
        -65.0,
        65.0 + args.bin_width_deg,
        args.bin_width_deg,
    )

    grid = build_angular_flux_grid(
        tracks["theta_x_deg"],
        tracks["theta_y_deg"],
        x_edges,
        y_edges,
        measurement_time_s,
    )

    fig, ax = plt.subplots(figsize=(8, 7))

    mesh = ax.pcolormesh(
        x_edges,
        y_edges,
        grid["flux"].T,
        shading="auto",
    )

    fig.colorbar(
        mesh,
        ax=ax,
        label=r"Flux (cm$^{-2}$ s$^{-1}$ sr$^{-1}$)",
    )

    ax.set_xlabel(r"$\theta_x$ (deg)")
    ax.set_ylabel(r"$\theta_y$ (deg)")
    ax.set_aspect("equal")

    fig.tight_layout()

    output_file = args.output_dir / "theta_x_theta_y_flux.png"

    fig.savefig(output_file, dpi=200)
    plt.close(fig)

    cfg = get_config()
    top = str(cfg["tracking"]["endpoint_top"])
    bottom = str(cfg["tracking"]["endpoint_bottom"])
    x_corr = tracks[[f"{top}_X", f"{bottom}_X"]].corr().iloc[0, 1]
    y_corr = tracks[[f"{top}_Y", f"{bottom}_Y"]].corr().iloc[0, 1]
    print(f"X endpoint correlation: {x_corr:.4f}")
    print(f"Y endpoint correlation: {y_corr:.4f}")
    print(f"Saved: {output_file}")


if __name__ == "__main__":
    main()
