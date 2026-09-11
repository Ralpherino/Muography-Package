"""Efficiency calculations shared by Figures 2 and 3."""

from __future__ import annotations

import numpy as np
import pandas as pd


def binomial_error(efficiency: float, n_total: int) -> float:
    """Return sqrt(epsilon * (1-epsilon) / N_total)."""
    if n_total <= 0:
        raise ValueError("n_total must be positive")
    return float(np.sqrt(efficiency * (1.0 - efficiency) / n_total))


def calculate_trigger_efficiency(events: pd.DataFrame) -> dict[str, float | int]:
    """Measure HR-B trigger efficiency using HR-14 and HR-8 as references.

    Mathematics
    -----------
    Reference event:
        R_j = (T5_j = 1) AND (T0_j = 1)

    Successful HR-B event:
        G_j = R_j AND (T3_j = 1)

    Efficiency:
        epsilon_trigger = N_good / N_total
    """
    reference = events["T5"].eq(1) & events["T0"].eq(1)
    good = reference & events["T3"].eq(1)

    n_total = int(reference.sum())
    n_good = int(good.sum())
    if n_total == 0:
        raise ValueError("No trigger-reference events were found")

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
    """Measure HR-B X or Y efficiency using endpoint coordinate hits.

    A coordinate is valid when its raw strip index is >= 0. The raw value -1
    means no coordinate; strip 0 is valid.

    For coordinate C in {X,Y}:
        R_C,j = (HR14_C,j >= 0) AND (HR8_C,j >= 0)
        G_C,j = R_C,j AND (HRB_C,j >= 0)
        epsilon_C = N(G_C) / N(R_C)
    """
    coordinate = coordinate.upper()
    if coordinate not in {"X", "Y"}:
        raise ValueError("coordinate must be 'X' or 'Y'")

    top = f"HR14_{coordinate}"
    middle = f"HRB_{coordinate}"
    bottom = f"HR8_{coordinate}"

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
    """Calculate trigger, X, Y, and report-style XY efficiencies."""
    trigger = calculate_trigger_efficiency(events)
    x_result = calculate_coordinate_efficiency(events, "X")
    y_result = calculate_coordinate_efficiency(events, "Y")

    x_eff = float(x_result["x_efficiency"])
    y_eff = float(y_result["y_efficiency"])

    # The laboratory report defines displayed XY as min(X,Y), not as the
    # event-level X AND Y intersection.
    xy_eff = min(x_eff, y_eff)
    xy_error = (
        float(x_result["x_error"])
        if x_eff <= y_eff
        else float(y_result["y_error"])
    )

    # Also calculate the true event-level joint XY efficiency under the same
    # trigger reference. This is retained for validation, even though it is not
    # the report's displayed definition.
    reference_trigger = events["T5"].eq(1) & events["T0"].eq(1)
    joint_good = (
        reference_trigger
        & events["HRB_X"].ge(0)
        & events["HRB_Y"].ge(0)
    )
    n_joint_total = int(reference_trigger.sum())
    n_joint_good = int(joint_good.sum())
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
