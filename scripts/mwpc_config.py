"""Physical and DAQ configuration of the MWPC tracker.

Values are loaded from a detector YAML selected at runtime.
Backward-compatible names (PITCH_CM, etc.) are still provided.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mwpc_detector import load_detector

DEFAULT_DETECTOR = "elte_mwpc_2026"
_cfg: dict[str, Any] | None = None


def set_detector(name: str, detectors_dir: Path | None = None) -> None:
    """Select the detector configuration. Call once at the start of a script."""
    global _cfg
    _cfg = load_detector(name, detectors_dir)


def get_config() -> dict[str, Any]:
    if _cfg is None:
        set_detector(DEFAULT_DETECTOR)
    return _cfg  # type: ignore


def __getattr__(name: str):
    """Provide the old constant names so existing imports keep working."""
    cfg = get_config()
    mapping = {
        "PITCH_CM": "pitch_cm",
        "ENDPOINT_SEPARATION_CM": "endpoint_separation_cm",
        "N_STRIPS": "n_strips",
        "ACTIVE_SIDE_CM": "active_side_cm",
        "TRIGGER_LABELS": "trigger_labels",
        "CHAMBER_NAMES": "chamber_names",
    }
    if name in mapping:
        value = cfg[mapping[name]]
        if name in ("TRIGGER_LABELS", "CHAMBER_NAMES"):
            return tuple(value)
        return value
    raise AttributeError(f"module 'mwpc_config' has no attribute {name!r}")