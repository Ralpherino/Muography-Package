"""Shared command-line arguments for the modular MWPC analysis scripts."""

from __future__ import annotations

import argparse
from pathlib import Path


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    """Add project-root, output, cache and detector options."""
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("."),
        help=(
            "Project data root. Expects .ebe files in <data-dir>/ebe "
            "and .sett files in <data-dir>/sett. Default: current directory."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs"),
        help="Directory where plots and tables will be written",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("cache"),
        help="Directory for parsed-run pickle caches",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Parse the raw .ebe file even when a cache exists",
    )
    parser.add_argument(
        "--detector",
        type=str,
        default="elte_mwpc_2026",
        help="Name of the detector configuration (without .yaml)",
    )


def prepare_paths(args: argparse.Namespace) -> None:
    """Normalize paths, validate data folders, create output/cache dirs."""
    args.data_dir = args.data_dir.expanduser().resolve()
    args.output_dir = args.output_dir.expanduser().resolve()
    args.cache_dir = args.cache_dir.expanduser().resolve()

    if not args.data_dir.exists():
        raise FileNotFoundError(f"Data root does not exist: {args.data_dir}")
    if not args.data_dir.is_dir():
        raise NotADirectoryError(f"Data root is not a directory: {args.data_dir}")

    ebe_dir = args.data_dir / "ebe"
    sett_dir = args.data_dir / "sett"

    if not ebe_dir.is_dir():
        raise FileNotFoundError(
            f"Missing EBE directory: {ebe_dir}\n"
            "Expected layout: <data-dir>/ebe/ElteLab2026A-Tracker_RunNNN.ebe"
        )
    if not sett_dir.is_dir():
        raise FileNotFoundError(
            f"Missing SETT directory: {sett_dir}\n"
            "Expected layout: <data-dir>/sett/ElteLab2026A-Tracker_RunNNN.sett"
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.cache_dir.mkdir(parents=True, exist_ok=True)