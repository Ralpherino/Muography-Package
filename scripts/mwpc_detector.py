"""Load detector geometry and DAQ mapping from a YAML file."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_detector(name: str, detectors_dir: Path | None = None) -> dict[str, Any]:
    """Return the full detector configuration dictionary."""
    if detectors_dir is None:
        detectors_dir = Path("detectors")

    path = detectors_dir / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Detector config not found: {path}")

    with open(path, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)

    required = [
        "pitch_cm",
        "endpoint_separation_cm",
        "n_strips",
        "trigger_labels",
        "chamber_names",
    ]
    for key in required:
        if key not in cfg:
            raise KeyError(f"Detector config missing required key: {key}")

    # Keep derived quantity consistent
    cfg["active_side_cm"] = float(cfg["n_strips"]) * float(cfg["pitch_cm"])

    return cfg