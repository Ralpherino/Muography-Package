#!/usr/bin/env python3
"""Task: inspect one real run before doing any physics analysis."""

from __future__ import annotations

import argparse

from cli_common import add_common_arguments, prepare_paths
from mwpc_config import set_detector
from mwpc_io import ebe_path, load_run, parse_sett_file, sett_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_arguments(parser)
    parser.add_argument("--run", type=int, default=206, help="Run number to inspect")
    parser.add_argument("--rows", type=int, default=5, help="Number of parsed events to print")
    args = parser.parse_args()

    set_detector(args.detector)
    prepare_paths(args)

    event_file = ebe_path(args.data_dir, args.run)
    settings_file = sett_path(args.data_dir, args.run)

    metadata = parse_sett_file(settings_file)
    events = load_run(
        args.data_dir,
        args.run,
        cache_dir=args.cache_dir,
        use_cache=not args.no_cache,
    )

    print("\nSETTINGS METADATA")
    print("-----------------")
    for key, value in metadata.items():
        print(f"{key:24s}: {value}")

    print("\nRAW FIRST EVENT")
    print("---------------")
    with event_file.open("r", encoding="utf-8") as input_file:
        first_line = input_file.readline().rstrip("\n")
    print(first_line)

    print("\nFIRST EVENT TOKENS")
    print("------------------")
    for index, token in enumerate(first_line.split()):
        print(f"{index:2d}: {token}")

    print("\nPARSED TABLE SUMMARY")
    print("--------------------")
    print(f"Rows (events):   {len(events):,}")
    print(f"Columns:         {len(events.columns)}")
    print(f"First timestamp: {events['date_time'].iloc[0]}")
    print(f"Last timestamp:  {events['date_time'].iloc[-1]}")

    columns = [
        "event_id", "T5", "T4", "T3", "T2", "T1", "T0",
        "HR14_X", "HR14_Y", "HRB_X", "HRB_Y", "HR8_X", "HR8_Y",
    ]
    print("\nFIRST PARSED EVENTS")
    print("-------------------")
    print(events[columns].head(args.rows).to_string(index=False))


if __name__ == "__main__":
    main()