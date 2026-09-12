"""Input/output helpers for MWPC .ebe and .sett files."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pandas as pd

from mwpc_config import get_config


def ebe_path(data_dir: Path, run: int) -> Path:
    """Return ``<data_dir>/ebe/...RunNNN.ebe`` and verify it exists."""
    path = data_dir / "ebe" / f"ElteLab2026A-Tracker_Run{run}.ebe"
    if not path.exists():
        raise FileNotFoundError(
            f"Could not find event file: {path}\n"
            "Place .ebe files inside the ebe/ directory."
        )
    return path


def sett_path(data_dir: Path, run: int) -> Path:
    """Return ``<data_dir>/sett/...RunNNN.sett`` and verify it exists."""
    path = data_dir / "sett" / f"ElteLab2026A-Tracker_Run{run}.sett"
    if not path.exists():
        raise FileNotFoundError(
            f"Could not find settings file: {path}\n"
            "Place .sett files inside the sett/ directory."
        )
    return path


def parse_ebe_file(file_path: Path) -> pd.DataFrame:
    """Parse one tracker .ebe file into one DataFrame row per event.

    Chamber names and trigger labels are resolved from the *currently selected*
    detector configuration when this function is called.  Therefore a new YAML
    can change the logical DAQ mapping without Python edits.
    """
    cfg = get_config()
    chamber_names = tuple(cfg["chamber_names"])
    trigger_labels = tuple(cfg["trigger_labels"])
    expected_coordinates = 2 * len(chamber_names)

    rows: list[dict[str, object]] = []

    with file_path.open("r", encoding="utf-8") as input_file:
        for line_number, line in enumerate(input_file, start=1):
            tokens = line.split()
            if not tokens:
                continue

            try:
                adc_position = tokens.index("Adc")
                pattern_position = tokens.index("P")
                hv_position = tokens.index("Hv")
                channel_position = tokens.index("Ch")
            except ValueError as exc:
                raise ValueError(
                    f"Missing Adc/P/Hv/Ch marker on line {line_number} in {file_path}"
                ) from exc

            adc_values = [
                int(value)
                for value in tokens[adc_position + 1 : pattern_position]
            ]
            pattern_values = [
                int(value)
                for value in tokens[pattern_position + 1 : hv_position]
            ]
            hv_values = [
                float(value)
                for value in tokens[hv_position + 1 : channel_position]
            ]
            channel_values = [int(value) for value in tokens[channel_position + 1 :]]

            if len(adc_values) != len(chamber_names):
                raise ValueError(
                    f"Line {line_number}: expected {len(chamber_names)} ADC values "
                    f"for detector {cfg['name']!r}, found {len(adc_values)}"
                )
            if len(pattern_values) != len(trigger_labels):
                raise ValueError(
                    f"Line {line_number}: expected {len(trigger_labels)} trigger values, "
                    f"found {len(pattern_values)}"
                )
            if len(hv_values) != 3:
                raise ValueError(
                    f"Line {line_number}: expected 3 HV values, found {len(hv_values)}"
                )
            if len(channel_values) != expected_coordinates:
                raise ValueError(
                    f"Line {line_number}: expected {expected_coordinates} coordinates "
                    f"({len(chamber_names)} chambers x 2), found {len(channel_values)}"
                )

            row: dict[str, object] = {
                "event_id": int(tokens[0]),
                "event_type": tokens[1],
                "date_time": tokens[2],
                "time_tag_raw": int(tokens[3]),
                "hv_readback": hv_values[0],
                "hv_set_event": hv_values[1],
                "hv_monitor": hv_values[2],
            }

            for adc_index, adc_value in enumerate(adc_values):
                row[f"ADC{adc_index}"] = adc_value

            for trigger_label, pattern_value in zip(
                trigger_labels, pattern_values, strict=True
            ):
                row[trigger_label] = pattern_value

            for chamber_index, chamber_name in enumerate(chamber_names):
                x_index = 2 * chamber_index
                y_index = x_index + 1
                row[f"{chamber_name}_X"] = channel_values[x_index]
                row[f"{chamber_name}_Y"] = channel_values[y_index]

            rows.append(row)

    events = pd.DataFrame(rows)
    if events.empty:
        raise ValueError(f"No events were parsed from {file_path}")

    events["date_time"] = pd.to_datetime(
        events["date_time"], format="%Y-%m-%d_%H:%M:%S", errors="raise"
    )
    return events


def _cache_file(cache_dir: Path, run: int) -> Path:
    """Return a detector-configuration-specific cache filename.

    Parsed column names depend on the detector YAML.  The short configuration
    hash prevents stale caches from surviving a detector-mapping edit made
    under the same detector name.
    """
    cfg = get_config()
    detector_name = str(cfg["name"]).replace("/", "_")
    fingerprint = hashlib.sha256(
        json.dumps(cfg, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()[:10]
    return cache_dir / f"run_{run}__{detector_name}__{fingerprint}.pkl"


def load_run(
    data_dir: Path,
    run: int,
    cache_dir: Path | None = None,
    use_cache: bool = True,
) -> pd.DataFrame:
    """Load a run, optionally using a detector-specific pandas pickle cache."""
    cache_file: Path | None = None
    if use_cache and cache_dir is not None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = _cache_file(cache_dir, run)
        if cache_file.exists():
            return pd.read_pickle(cache_file)

    events = parse_ebe_file(ebe_path(data_dir, run))

    if use_cache and cache_file is not None:
        events.to_pickle(cache_file)

    return events


def parse_sett_file(file_path: Path) -> dict[str, object]:
    """Extract the main metadata fields from a .sett file."""
    text = file_path.read_text(encoding="utf-8")

    def required(pattern: str, field_name: str) -> str:
        match = re.search(pattern, text, flags=re.MULTILINE)
        if match is None:
            raise ValueError(f"Could not find {field_name!r} in {file_path}")
        return match.group(1).strip()

    run = int(required(r"^Run\s+(\d+)", "run"))
    hv_nominal = int(required(r"^HV:\s*(\d+)\s*V", "nominal HV"))
    statistics_requested = int(
        required(r"^Statistics\s+(-?\d+)", "requested statistics")
    )

    note_match = re.search(r"^Note:\s*(.*)$", text, flags=re.MULTILINE)
    note = note_match.group(1).strip() if note_match else ""

    start_match = re.search(r"^Start\s+(.*)$", text, flags=re.MULTILINE)
    start = start_match.group(1).strip() if start_match else ""

    return {
        "run": run,
        "hv_nominal": hv_nominal,
        "statistics_requested": statistics_requested,
        "start_text": start,
        "note": note,
    }
