"""Track reconstruction and geometrical calculations for Figures 4-7."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.integrate import dblquad

from mwpc_config import ACTIVE_SIDE_CM, ENDPOINT_SEPARATION_CM, PITCH_CM


def reconstruct_endpoint_tracks(events: pd.DataFrame) -> pd.DataFrame:
    """Select valid HR14-HR8 endpoint hits and reconstruct track angles.

    Endpoint displacement:
        Delta X_strip = X_HR8 - X_HR14
        Delta Y_strip = Y_HR8 - Y_HR14

    Physical displacement:
        Delta x = pitch * Delta X_strip
        Delta y = pitch * Delta Y_strip

    Projected angles:
        theta_x = atan2(Delta x, h)
        theta_y = atan2(Delta y, h)

    Full zenith angle:
        theta = atan2(sqrt(Delta x^2 + Delta y^2), h)
    """
    valid = (
        events["HR14_X"].ge(0)
        & events["HR14_Y"].ge(0)
        & events["HR8_X"].ge(0)
        & events["HR8_Y"].ge(0)
    )
    tracks = events.loc[valid].copy()

    tracks["delta_x_strip"] = tracks["HR8_X"] - tracks["HR14_X"]
    tracks["delta_y_strip"] = tracks["HR8_Y"] - tracks["HR14_Y"]
    tracks["delta_x_cm"] = PITCH_CM * tracks["delta_x_strip"]
    tracks["delta_y_cm"] = PITCH_CM * tracks["delta_y_strip"]

    tracks["theta_x_deg"] = np.degrees(
        np.arctan2(tracks["delta_x_cm"], ENDPOINT_SEPARATION_CM)
    )
    tracks["theta_y_deg"] = np.degrees(
        np.arctan2(tracks["delta_y_cm"], ENDPOINT_SEPARATION_CM)
    )
    tracks["theta_deg"] = np.degrees(
        np.arctan2(
            np.hypot(tracks["delta_x_cm"], tracks["delta_y_cm"]),
            ENDPOINT_SEPARATION_CM,
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
    """Return the report-style effective area in cm^2.

    A_i = L * (L - h tan(alpha_i)) * cos(alpha_i)
    alpha_i = |theta_x,i|
    """
    alpha = np.radians(np.abs(theta_x_center_deg))
    area = (
        ACTIVE_SIDE_CM
        * (ACTIVE_SIDE_CM - ENDPOINT_SEPARATION_CM * np.tan(alpha))
        * np.cos(alpha)
    )
    return area

def effective_area_2d(
    theta_x_deg: np.ndarray,
    theta_y_deg: np.ndarray,
) -> np.ndarray:
    """Effective perpendicular overlap area for a 2D track direction.

    A_eff(theta_x, theta_y)
        = overlap_x * overlap_y * cos(theta)

    where
        overlap_x = L - h * |tan(theta_x)|
        overlap_y = L - h * |tan(theta_y)|

    Returns
    -------
    np.ndarray
        Effective area in cm^2.
    """

    theta_x = np.radians(theta_x_deg)
    theta_y = np.radians(theta_y_deg)

    u = np.tan(theta_x)
    v = np.tan(theta_y)

    overlap_x = ACTIVE_SIDE_CM - ENDPOINT_SEPARATION_CM * np.abs(u)
    overlap_y = ACTIVE_SIDE_CM - ENDPOINT_SEPARATION_CM * np.abs(v)

    valid = (overlap_x > 0.0) & (overlap_y > 0.0)

    cos_theta = 1.0 / np.sqrt(1.0 + u**2 + v**2)

    area = np.zeros_like(cos_theta, dtype=float)
    area[valid] = (
        overlap_x[valid]
        * overlap_y[valid]
        * cos_theta[valid]
    )

    return area

def build_angular_flux_grid(
    theta_x_deg,
    theta_y_deg,
    x_edges_deg: np.ndarray,
    y_edges_deg: np.ndarray,
    measurement_time_s: float,
) -> dict[str, np.ndarray]:
    """Build a 2D angular counts/acceptance/flux grid.

    For each angular cell (i, j):

        Phi_ij = N_ij / (A_ij * t * DeltaOmega_ij)

    Returns flux in cm^-2 s^-1 sr^-1.
    """

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

    effective_area_cm2 = effective_area_2d(
        theta_x_grid,
        theta_y_grid,
    )

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

    geometric_acceptance_cm2_sr = (
        effective_area_cm2 * solid_angle_sr
    )

    exposure = (
        geometric_acceptance_cm2_sr * measurement_time_s
    )

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
    return float((events["date_time"].iloc[-1] - events["date_time"].iloc[0]).total_seconds())

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

    raise ValueError(
        "time_mode must be 'timestamps' or 'report'"
    )