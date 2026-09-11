#!/usr/bin/env python3
"""Task: reconstruct and plot the Figure 4 angular distributions."""

from __future__ import annotations

import argparse

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from cli_common import add_common_arguments, prepare_paths
from mwpc_config import set_detector
from mwpc_io import load_run
from mwpc_tracking import (
    build_angular_flux_grid,
    reconstruct_endpoint_tracks,
    resolve_measurement_time,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_arguments(parser)
    parser.add_argument("--run", type=int, required=True)
    parser.add_argument("--bin-width-deg", type=float, default=5.0)
    parser.add_argument(
        "--time-mode",
        choices=("report", "timestamps"),
        default="timestamps",
    )
    parser.add_argument("--report-time-s", type=float, default=3600.0)
    args = parser.parse_args()

    set_detector(args.detector)
    prepare_paths(args)

    events = load_run(
        args.data_dir,
        args.run,
        cache_dir=args.cache_dir,
        use_cache=not args.no_cache,
    )

    tracks = reconstruct_endpoint_tracks(events)
    measurement_time_s = resolve_measurement_time(
        events,
        time_mode=args.time_mode,
        report_time_s=args.report_time_s,
    )

    xy_edges = np.arange(-65.0, 65.0 + args.bin_width_deg, args.bin_width_deg)

    grid = build_angular_flux_grid(
        tracks["theta_x_deg"],
        tracks["theta_y_deg"],
        xy_edges,
        xy_edges,
        measurement_time_s,
    )

    counts_2d = grid["counts"]
    acceptance_2d = grid["geometric_acceptance_cm2_sr"]
    x_centres = grid["x_centres_deg"]
    y_centres = grid["y_centres_deg"]

    # Figure 4a – full zenith angle
    theta_x_grid, theta_y_grid = np.meshgrid(x_centres, y_centres, indexing="ij")
    u = np.tan(np.radians(theta_x_grid))
    v = np.tan(np.radians(theta_y_grid))
    theta_grid = np.degrees(np.arctan(np.hypot(u, v)))

    theta_edges = np.arange(0.0, 70.0 + args.bin_width_deg, args.bin_width_deg)
    theta_centres = 0.5 * (theta_edges[:-1] + theta_edges[1:])
    theta_counts = np.zeros(len(theta_centres))
    theta_acceptance = np.zeros(len(theta_centres))

    for k, (low, high) in enumerate(zip(theta_edges[:-1], theta_edges[1:], strict=True)):
        mask = (theta_grid >= low) & (theta_grid < high)
        theta_counts[k] = counts_2d[mask].sum()
        theta_acceptance[k] = acceptance_2d[mask].sum()

    theta_denominator = measurement_time_s * theta_acceptance
    theta_flux = np.full_like(theta_counts, np.nan, dtype=float)
    theta_flux_error = np.full_like(theta_counts, np.nan, dtype=float)
    valid_theta = theta_denominator > 0.0
    theta_flux[valid_theta] = theta_counts[valid_theta] / theta_denominator[valid_theta]
    theta_flux_error[valid_theta] = (
        np.sqrt(theta_counts[valid_theta]) / theta_denominator[valid_theta]
    )

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.errorbar(
        theta_centres[valid_theta],
        theta_flux[valid_theta],
        yerr=theta_flux_error[valid_theta],
        fmt="o",
        capsize=3,
    )
    ax.set_xlabel(r"$\theta$ (deg)")
    ax.set_ylabel(r"Flux (cm$^{-2}$ s$^{-1}$ sr$^{-1}$)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    output_a = args.output_dir / "zenith_theta_flux.png"
    fig.savefig(output_a, dpi=200)
    plt.close(fig)

    # Figure 4b – signed X projection
    counts_x = counts_2d.sum(axis=1)
    acceptance_x = acceptance_2d.sum(axis=1)
    denominator_x = measurement_time_s * acceptance_x
    flux_x = np.full_like(counts_x, np.nan, dtype=float)
    flux_x_error = np.full_like(counts_x, np.nan, dtype=float)
    valid_x = denominator_x > 0.0
    flux_x[valid_x] = counts_x[valid_x] / denominator_x[valid_x]
    flux_x_error[valid_x] = np.sqrt(counts_x[valid_x]) / denominator_x[valid_x]

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.errorbar(
        x_centres[valid_x],
        flux_x[valid_x],
        yerr=flux_x_error[valid_x],
        fmt="o",
        capsize=3,
    )
    ax.set_xlabel(r"$\theta_x$ (deg)")
    ax.set_ylabel(r"Flux (cm$^{-2}$ s$^{-1}$ sr$^{-1}$)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    output_b = args.output_dir / "theta_x_flux.png"
    fig.savefig(output_b, dpi=200)
    plt.close(fig)

    # Save tracks
    track_columns = [
        "event_id", "date_time",
        "HR14_X", "HR14_Y", "HR8_X", "HR8_Y",
        "delta_x_strip", "delta_y_strip",
        "delta_x_cm", "delta_y_cm",
        "theta_x_deg", "theta_y_deg", "theta_deg",
    ]
    track_file = args.output_dir / f"run{args.run}_endpoint_tracks.csv"
    tracks[track_columns].to_csv(track_file, index=False)

    print(f"Run events:             {len(events):,}")
    print(f"Valid endpoint tracks:  {len(tracks):,}")
    print(f"Saved: {output_a}")
    print(f"Saved: {output_b}")
    print(f"Saved: {track_file}")


if __name__ == "__main__":
    main()