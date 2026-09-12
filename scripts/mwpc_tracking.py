"""Track reconstruction and geometrical calculations for Figures 4-7."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.integrate import dblquad

from mwpc_config import get_config


def _tracking_geometry() -> tuple[str, str, float, float, float]:
    """Resolve endpoint chambers and geometry from the active detector YAML."""
    cfg = get_config()
    tracking = cfg["tracking"]
    return (
        str(tracking["endpoint_top"]),
        str(tracking["endpoint_bottom"]),
        float(cfg["pitch_cm"]),
        float(cfg["endpoint_separation_cm"]),
        float(cfg["active_side_cm"]),
    )


def reconstruct_endpoint_tracks(events: pd.DataFrame) -> pd.DataFrame:
    """Select valid configured endpoint hits and reconstruct track angles."""
    top, bottom, pitch_cm, separation_cm, _active_side_cm = _tracking_geometry()

    top_x = f"{top}_X"
    top_y = f"{top}_Y"
    bottom_x = f"{bottom}_X"
    bottom_y = f"{bottom}_Y"

    valid = (
        events[top_x].ge(0)
        & events[top_y].ge(0)
        & events[bottom_x].ge(0)
        & events[bottom_y].ge(0)
    )
    tracks = events.loc[valid].copy()

    tracks["delta_x_strip"] = tracks[bottom_x] - tracks[top_x]
    tracks["delta_y_strip"] = tracks[bottom_y] - tracks[top_y]
    tracks["delta_x_cm"] = pitch_cm * tracks["delta_x_strip"]
    tracks["delta_y_cm"] = pitch_cm * tracks["delta_y_strip"]

    tracks["theta_x_deg"] = np.degrees(
        np.arctan2(tracks["delta_x_cm"], separation_cm)
    )
    tracks["theta_y_deg"] = np.degrees(
        np.arctan2(tracks["delta_y_cm"], separation_cm)
    )
    tracks["theta_deg"] = np.degrees(
        np.arctan2(
            np.hypot(tracks["delta_x_cm"], tracks["delta_y_cm"]),
            separation_cm,
        )
    )
    return tracks


def select_y_slice(tracks: pd.DataFrame, max_strip_difference: int = 1) -> pd.DataFrame:
    """Select |Delta Y_strip| <= max_strip_difference."""
    return tracks.loc[
        tracks["delta_y_strip"].abs().le(max_strip_difference)
    ].copy()


def projected_solid_angle(
    theta_x_low_deg: float,
    theta_x_high_deg: float,
    theta_y_low_deg: float,
    theta_y_high_deg: float,
) -> float:
    """Integrate solid angle in projected-slope coordinates.

    With u = tan(theta_x) and v = tan(theta_y):
        dOmega = du dv / (1 + u^2 + v^2)^(3/2)
    """
    u_low, u_high = np.tan(np.radians([theta_x_low_deg, theta_x_high_deg]))
    v_low, v_high = np.tan(np.radians([theta_y_low_deg, theta_y_high_deg]))

    value, _ = dblquad(
        lambda v, u: (1.0 + u * u + v * v) ** (-1.5),
        u_low,
        u_high,
        lambda _u: v_low,
        lambda _u: v_high,
    )
    return float(value)


def effective_area_report(theta_x_center_deg: np.ndarray) -> np.ndarray:
    """Return the report-style effective area in cm^2 using active YAML geometry."""
    _top, _bottom, _pitch_cm, separation_cm, active_side_cm = _tracking_geometry()
    alpha = np.radians(np.abs(theta_x_center_deg))
    area = (
        active_side_cm
        * (active_side_cm - separation_cm * np.tan(alpha))
        * np.cos(alpha)
    )
    return area


def effective_area_2d(
    theta_x_deg: np.ndarray,
    theta_y_deg: np.ndarray,
) -> np.ndarray:
    """Effective perpendicular overlap area for a 2D track direction."""
    _top, _bottom, _pitch_cm, separation_cm, active_side_cm = _tracking_geometry()

    theta_x = np.radians(theta_x_deg)
    theta_y = np.radians(theta_y_deg)

    u = np.tan(theta_x)
    v = np.tan(theta_y)

    overlap_x = active_side_cm - separation_cm * np.abs(u)
    overlap_y = active_side_cm - separation_cm * np.abs(v)

    valid = (overlap_x > 0.0) & (overlap_y > 0.0)
    cos_theta = 1.0 / np.sqrt(1.0 + u**2 + v**2)

    area = np.zeros_like(cos_theta, dtype=float)
    area[valid] = overlap_x[valid] * overlap_y[valid] * cos_theta[valid]
    return area


def build_angular_flux_grid(
    theta_x_deg,
    theta_y_deg,
    x_edges_deg: np.ndarray,
    y_edges_deg: np.ndarray,
    measurement_time_s: float,
) -> dict[str, np.ndarray]:
    """Build a 2D angular counts/acceptance/flux grid."""
    counts, _, _ = np.histogram2d(
        theta_x_deg,
        theta_y_deg,
        bins=[x_edges_deg, y_edges_deg],
    )

    x_centres = 0.5 * (x_edges_deg[:-1] + x_edges_deg[1:])
    y_centres = 0.5 * (y_edges_deg[:-1] + y_edges_deg[1:])

    theta_x_grid, theta_y_grid = np.meshgrid(
        x_centres,
        y_centres,
        indexing="ij",
    )

    effective_area_cm2 = effective_area_2d(theta_x_grid, theta_y_grid)
    solid_angle_sr = np.zeros_like(counts, dtype=float)

    for i, (x_low, x_high) in enumerate(
        zip(x_edges_deg[:-1], x_edges_deg[1:], strict=True)
    ):
        for j, (y_low, y_high) in enumerate(
            zip(y_edges_deg[:-1], y_edges_deg[1:], strict=True)
        ):
            solid_angle_sr[i, j] = projected_solid_angle(
                x_low,
                x_high,
                y_low,
                y_high,
            )

    geometric_acceptance_cm2_sr = effective_area_cm2 * solid_angle_sr
    exposure = geometric_acceptance_cm2_sr * measurement_time_s

    flux = np.full_like(counts, np.nan, dtype=float)
    flux_error = np.full_like(counts, np.nan, dtype=float)
    valid = exposure > 0.0

    flux[valid] = counts[valid] / exposure[valid]
    flux_error[valid] = np.sqrt(counts[valid]) / exposure[valid]

    return {
        "counts": counts,
        "x_centres_deg": x_centres,
        "y_centres_deg": y_centres,
        "effective_area_cm2": effective_area_cm2,
        "solid_angle_sr": solid_angle_sr,
        "geometric_acceptance_cm2_sr": geometric_acceptance_cm2_sr,
        "flux": flux,
        "flux_error": flux_error,
    }


def timestamp_span_seconds(events: pd.DataFrame) -> float:
    """Return last timestamp minus first timestamp in seconds."""
    return float(
        (events["date_time"].iloc[-1] - events["date_time"].iloc[0]).total_seconds()
    )


def resolve_measurement_time(
    events: pd.DataFrame,
    time_mode: str = "timestamps",
    report_time_s: float = 3600.0,
) -> float:
    """Return measurement time according to the selected convention."""
    if time_mode == "timestamps":
        return timestamp_span_seconds(events)
    if time_mode == "report":
        return float(report_time_s)
    raise ValueError("time_mode must be 'timestamps' or 'report'")
