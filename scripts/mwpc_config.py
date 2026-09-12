"""Runtime-selected physical and DAQ configuration of the MWPC tracker.

Detector-specific values are loaded from YAML.  Physics modules should call
``get_config()`` at function execution time instead of importing geometry or
chamber constants at module-import time.  This is what makes ``--detector``
actually dynamic.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mwpc_detector import load_detector

DEFAULT_DETECTOR = "elte_mwpc_2026"
_cfg: dict[str, Any] | None = None


def set_detector(name: str, detectors_dir: Path | None = None) -> None:
    """Select the detector configuration for the current process."""
    global _cfg
    _cfg = load_detector(name, detectors_dir)


def get_config() -> dict[str, Any]:
    """Return the currently selected detector configuration."""
    if _cfg is None:
        set_detector(DEFAULT_DETECTOR)
    return _cfg  # type: ignore[return-value]


def chamber_trigger(chamber_name: str) -> str:
    """Return the trigger label associated with one chamber."""
    cfg = get_config()
    try:
        return str(cfg["chamber_to_trigger"][chamber_name])
    except KeyError as exc:
        raise KeyError(
            f"No trigger mapping exists for chamber {chamber_name!r} "
            f"in detector {cfg['name']!r}"
        ) from exc


def __getattr__(name: str):
    """Backward-compatible access to old constant names.

    New physics code should prefer ``get_config()`` so values are looked up at
    execution time.  These aliases remain for external code that still imports
    ``mwpc_config.PITCH_CM`` and similar names.
    """
    # Import machinery probes attributes such as ``__path__``.  Do not let
    # those probes implicitly load the default detector.
    if name.startswith("__"):
        raise AttributeError(name)

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
