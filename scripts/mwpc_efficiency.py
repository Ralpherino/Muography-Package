"""Detector-configurable efficiency calculations shared by Figures 2 and 3."""

from __future__ import annotations

import numpy as np
import pandas as pd

from mwpc_config import chamber_trigger, get_config


def binomial_error(efficiency: float, n_total: int) -> float:
    """Return sqrt(epsilon * (1-epsilon) / N_total)."""
    if n_total <= 0:
        raise ValueError("n_total must be positive")
    return float(np.sqrt(efficiency * (1.0 - efficiency) / n_total))


def _efficiency_roles() -> tuple[str, str, str]:
    cfg = get_config()
    eff = cfg["efficiency"]
    return (
        str(eff["reference_top"]),
        str(eff["reference_bottom"]),
        str(eff["under_test"]),
    )


def calculate_trigger_efficiency(events: pd.DataFrame) -> dict[str, float | int]:
    """Measure DUT trigger efficiency using YAML-configured reference chambers.

    Trigger labels are derived from the chamber order / trigger order mapping in
    the selected detector YAML; no T5/T3/T0 names are hard-coded here.
    """
    top, bottom, dut = _efficiency_roles()
    top_trigger = chamber_trigger(top)
    bottom_trigger = chamber_trigger(bottom)
    dut_trigger = chamber_trigger(dut)

    reference = events[top_trigger].eq(1) & events[bottom_trigger].eq(1)
    good = reference & events[dut_trigger].eq(1)

    n_total = int(reference.sum())
    n_good = int(good.sum())
    if n_total == 0:
        raise ValueError(
            "No trigger-reference events were found for "
            f"{top}/{bottom} ({top_trigger}/{bottom_trigger})"
        )

    efficiency = n_good / n_total
    return {
        "n_total_trigger": n_total,
        "n_good_trigger": n_good,
        "trigger_efficiency": efficiency,
        "trigger_error": binomial_error(efficiency, n_total),
    }


def calculate_coordinate_efficiency(
    events: pd.DataFrame, coordinate: str
) -> dict[str, float | int]:
    """Measure DUT X or Y efficiency using YAML-configured chamber roles."""
    coordinate = coordinate.upper()
    if coordinate not in {"X", "Y"}:
        raise ValueError("coordinate must be 'X' or 'Y'")

    top_chamber, bottom_chamber, dut_chamber = _efficiency_roles()
    top = f"{top_chamber}_{coordinate}"
    middle = f"{dut_chamber}_{coordinate}"
    bottom = f"{bottom_chamber}_{coordinate}"

    reference = events[top].ge(0) & events[bottom].ge(0)
    good = reference & events[middle].ge(0)

    n_total = int(reference.sum())
    n_good = int(good.sum())
    if n_total == 0:
        raise ValueError(f"No {coordinate}-coordinate reference events were found")

    efficiency = n_good / n_total
    key = coordinate.lower()
    return {
        f"n_total_{key}": n_total,
        f"n_good_{key}": n_good,
        f"{key}_efficiency": efficiency,
        f"{key}_error": binomial_error(efficiency, n_total),
    }


def calculate_run_efficiencies(events: pd.DataFrame) -> dict[str, float | int]:
    """Calculate trigger, X, Y, report-style XY, and true joint XY efficiencies."""
    trigger = calculate_trigger_efficiency(events)
    x_result = calculate_coordinate_efficiency(events, "X")
    y_result = calculate_coordinate_efficiency(events, "Y")

    x_eff = float(x_result["x_efficiency"])
    y_eff = float(y_result["y_efficiency"])

    # Preserve the laboratory report definition used by the existing plots.
    xy_eff = min(x_eff, y_eff)
    xy_error = (
        float(x_result["x_error"])
        if x_eff <= y_eff
        else float(y_result["y_error"])
    )

    top_chamber, bottom_chamber, dut_chamber = _efficiency_roles()
    top_trigger = chamber_trigger(top_chamber)
    bottom_trigger = chamber_trigger(bottom_chamber)

    reference_trigger = events[top_trigger].eq(1) & events[bottom_trigger].eq(1)
    joint_good = (
        reference_trigger
        & events[f"{dut_chamber}_X"].ge(0)
        & events[f"{dut_chamber}_Y"].ge(0)
    )
    n_joint_total = int(reference_trigger.sum())
    n_joint_good = int(joint_good.sum())
    if n_joint_total == 0:
        raise ValueError("No trigger-reference events were found for joint XY efficiency")
    joint_eff = n_joint_good / n_joint_total

    return {
        **trigger,
        **x_result,
        **y_result,
        "xy_efficiency": xy_eff,
        "xy_error": xy_error,
        "n_total_xy_joint": n_joint_total,
        "n_good_xy_joint": n_joint_good,
        "xy_joint_efficiency": joint_eff,
        "xy_joint_error": binomial_error(joint_eff, n_joint_total),
    }
