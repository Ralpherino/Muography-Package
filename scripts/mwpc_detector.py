"""Load and validate detector geometry and DAQ mapping from YAML."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_detector(name: str, detectors_dir: Path | None = None) -> dict[str, Any]:
    """Return a validated detector configuration dictionary.

    The YAML file is the single source of truth for geometry, chamber order,
    trigger order, and detector roles used by the physics code.
    """
    if detectors_dir is None:
        detectors_dir = Path("detectors")

    path = detectors_dir / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Detector config not found: {path}")

    with open(path, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)

    if not isinstance(cfg, dict):
        raise TypeError(f"Detector config must be a YAML mapping: {path}")

    required = [
        "pitch_cm",
        "endpoint_separation_cm",
        "n_strips",
        "trigger_labels",
        "chamber_names",
        "efficiency",
        "tracking",
    ]
    for key in required:
        if key not in cfg:
            raise KeyError(f"Detector config missing required key: {key}")

    chamber_names = list(cfg["chamber_names"])
    trigger_labels = list(cfg["trigger_labels"])

    if not chamber_names:
        raise ValueError("Detector config must contain at least one chamber")
    if len(chamber_names) != len(trigger_labels):
        raise ValueError(
            "Detector config requires one trigger label per chamber: "
            f"got {len(chamber_names)} chambers and {len(trigger_labels)} triggers"
        )
    if len(set(chamber_names)) != len(chamber_names):
        raise ValueError("chamber_names contains duplicates")
    if len(set(trigger_labels)) != len(trigger_labels):
        raise ValueError("trigger_labels contains duplicates")

    eff = cfg["efficiency"]
    for key in ("reference_top", "reference_bottom", "under_test"):
        if key not in eff:
            raise KeyError(f"Detector config efficiency section missing: {key}")
        if eff[key] not in chamber_names:
            raise ValueError(
                f"efficiency.{key}={eff[key]!r} is not present in chamber_names"
            )

    tracking = cfg["tracking"]
    for key in ("endpoint_top", "endpoint_bottom"):
        if key not in tracking:
            raise KeyError(f"Detector config tracking section missing: {key}")
        if tracking[key] not in chamber_names:
            raise ValueError(
                f"tracking.{key}={tracking[key]!r} is not present in chamber_names"
            )

    # Keep the selected filename available even if the YAML omitted `name`.
    cfg["name"] = str(cfg.get("name", name))

    # Keep derived quantities and lookup maps internally consistent.
    cfg["active_side_cm"] = float(cfg["n_strips"]) * float(cfg["pitch_cm"])
    cfg["chamber_to_trigger"] = dict(zip(chamber_names, trigger_labels, strict=True))

    return cfg
