from __future__ import annotations

import math

import numpy as np

from models import (
    BladeSection,
    ChordAlignedSection2D,
    ConvertedSection,
    DimensionalSection2D,
    NormalizedSection2D,
)


NP_MAX = 201


def redistribute(points: np.ndarray, count: int = NP_MAX) -> np.ndarray:
    if points.ndim != 2 or points.shape[1] != 3 or len(points) < 2:
        raise ValueError("each blade surface must contain at least two XYZ points")
    distances = np.linalg.norm(np.diff(points, axis=0), axis=1)
    arc = np.concatenate(([0.0], np.cumsum(distances)))
    if arc[-1] <= 0.0:
        raise ValueError("blade surface has zero arc length")
    arc /= arc[-1]
    if np.any(np.diff(arc) <= 0.0):
        keep = np.concatenate(([True], np.diff(arc) > 0.0))
        arc, points = arc[keep], points[keep]
    stations = 0.5 * (1.0 - np.cos(np.linspace(0.0, math.pi, count)))
    return np.column_stack([np.interp(stations, arc, points[:, axis]) for axis in range(3)])


def _signed_meridional_increments(z: np.ndarray, radius: np.ndarray) -> np.ndarray:
    """Return dimensional meridional steps signed in the global flow direction."""
    dz_flow, dr_flow = z[-1] - z[0], radius[-1] - radius[0]
    dz, dr = np.diff(z), np.diff(radius)
    dm = np.hypot(dz, dr)
    sign_source = np.where(np.abs(dz) >= np.abs(dr), dz_flow * dz, dr_flow * dr)
    signs = np.where(sign_source < 0.0, -1.0, 1.0)
    return signs * dm


def meridional_coordinate(z: np.ndarray, radius: np.ndarray) -> tuple[np.ndarray, float]:
    signed_dm = _signed_meridional_increments(z, radius)
    average_radius = 0.5 * (radius[1:] + radius[:-1])
    if np.any(average_radius == 0.0):
        raise ValueError("m' is undefined where the average radius is zero")
    return (
        np.concatenate(([0.0], np.cumsum(signed_dm / average_radius))),
        float(np.sum(np.abs(signed_dm))),
    )


def dimensional_coordinates(section: BladeSection) -> DimensionalSection2D:
    """Integrate signed meridional and circumferential lengths on each surface."""
    sides = (redistribute(section.suction), redistribute(section.pressure))
    radii = [np.hypot(side[:, 0], side[:, 1]) for side in sides]
    theta = [np.unwrap(np.arctan2(side[:, 1], side[:, 0])) for side in sides]
    theta_reference = 0.5 * (theta[0][0] + theta[1][0])
    meridional_arcs = [
        np.concatenate(([0.0], np.cumsum(_signed_meridional_increments(side[:, 2], radius))))
        for side, radius in zip(sides, radii)
    ]
    circumferential_arcs = [
        np.concatenate(
            (
                [0.0],
                np.cumsum(0.5 * (radius[1:] + radius[:-1]) * np.diff(angle)),
            )
        )
        for radius, angle in zip(radii, theta)
    ]

    common_s_te = 0.5 * (meridional_arcs[0][-1] + meridional_arcs[1][-1])
    adjusted_s = []
    for arc in meridional_arcs:
        span = arc[-1] - arc[0]
        if span == 0.0:
            raise ValueError(f"section {section.index} has zero meridional arc length")
        adjusted_s.append(arc + (common_s_te - arc[-1]) * (arc - arc[0]) / span)

    common_u_te = 0.5 * (
        circumferential_arcs[0][-1] + circumferential_arcs[1][-1]
    )
    adjusted_u = []
    for arc, streamwise in zip(circumferential_arcs, adjusted_s):
        span = streamwise[-1] - streamwise[0]
        adjusted_u.append(
            arc
            + (common_u_te - arc[-1])
            * (streamwise - streamwise[0])
            / span
        )

    return DimensionalSection2D(
        section.index,
        adjusted_s[0],
        adjusted_u[0],
        adjusted_s[1],
        adjusted_u[1],
        float(theta_reference),
    )


def align_chord_to_x(coordinates: DimensionalSection2D) -> ChordAlignedSection2D:
    """Rigidly rotate (s, u) so the LE-TE chord lies on the positive x-axis."""
    le_s = 0.5 * (coordinates.suction_s[0] + coordinates.pressure_s[0])
    le_u = 0.5 * (coordinates.suction_u[0] + coordinates.pressure_u[0])
    te_s = 0.5 * (coordinates.suction_s[-1] + coordinates.pressure_s[-1])
    te_u = 0.5 * (coordinates.suction_u[-1] + coordinates.pressure_u[-1])
    chord_s, chord_u = te_s - le_s, te_u - le_u
    chord_length = math.hypot(chord_s, chord_u)
    if chord_length == 0.0:
        raise ValueError(f"section {coordinates.index} has zero chord length")
    angle = math.atan2(chord_u, chord_s)
    cosine, sine = math.cos(angle), math.sin(angle)

    def rotate(s: np.ndarray, u: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        relative_s, relative_u = s - le_s, u - le_u
        return (
            relative_s * cosine + relative_u * sine,
            -relative_s * sine + relative_u * cosine,
        )

    suction_x, suction_y = rotate(coordinates.suction_s, coordinates.suction_u)
    pressure_x, pressure_y = rotate(coordinates.pressure_s, coordinates.pressure_u)
    return ChordAlignedSection2D(
        coordinates.index,
        suction_x,
        suction_y,
        pressure_x,
        pressure_y,
        -angle,
        chord_length,
    )


def normalize_chord(coordinates: ChordAlignedSection2D) -> NormalizedSection2D:
    """Uniformly scale chord-aligned coordinates so LE=(0,0), TE=(1,0)."""
    if coordinates.chord_length <= 0.0:
        raise ValueError(f"section {coordinates.index} has non-positive chord length")
    scale = 1.0 / coordinates.chord_length
    return NormalizedSection2D(
        coordinates.index,
        coordinates.suction_x * scale,
        coordinates.suction_y * scale,
        coordinates.pressure_x * scale,
        coordinates.pressure_y * scale,
        coordinates.rotation_angle,
        coordinates.chord_length,
        scale,
    )


def convert_section(section: BladeSection) -> ConvertedSection:
    sides = (redistribute(section.suction), redistribute(section.pressure))
    radii = [np.hypot(side[:, 0], side[:, 1]) for side in sides]
    theta = [np.unwrap(np.arctan2(side[:, 1], side[:, 0])) for side in sides]
    suction_mp, chord_m = meridional_coordinate(sides[0][:, 2], radii[0])
    pressure_mp, _ = meridional_coordinate(sides[1][:, 2], radii[1])
    mavg = 0.5 * (suction_mp[-1] + pressure_mp[-1])
    adjusted = []
    for mp in (suction_mp, pressure_mp):
        span = mp[-1] - mp[0]
        if span == 0.0:
            raise ValueError(f"section {section.index} has zero meridional chord")
        adjusted.append(mp + (mavg - mp[-1]) * (mp - mp[0]) / span)
    suction_mp, pressure_mp = adjusted
    x_le = suction_mp[0] + 0.1 * (suction_mp[-1] - suction_mp[0])
    y_le = 0.5 * (
        np.interp(x_le, suction_mp, theta[0]) + np.interp(x_le, pressure_mp, theta[1])
    )
    sinl = (y_le - theta[0][0]) / (x_le - suction_mp[0])
    x_te = suction_mp[-1] - 0.1 * (suction_mp[-1] - suction_mp[0])
    y_te = 0.5 * (
        np.interp(x_te, suction_mp, theta[0]) + np.interp(x_te, pressure_mp, theta[1])
    )
    sout = (y_te - theta[0][-1]) / (x_te - suction_mp[-1])
    return ConvertedSection(
        section.index,
        suction_mp,
        theta[0],
        radii[0],
        pressure_mp,
        theta[1],
        chord_m,
        float(sinl),
        float(sout),
    )
