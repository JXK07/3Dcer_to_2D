"""Geometric validation for converted two-dimensional blade contours."""

from __future__ import annotations

import numpy as np

from models import DimensionalSection2D


def _cross(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    ab, ac = b - a, c - a
    return float(ab[0] * ac[1] - ab[1] * ac[0])


def _properly_intersects(
    a: np.ndarray, b: np.ndarray, c: np.ndarray, d: np.ndarray
) -> bool:
    return _cross(a, b, c) * _cross(a, b, d) < 0.0 and _cross(c, d, a) * _cross(
        c, d, b
    ) < 0.0


def validate_dimensional_contour(
    coordinates: DimensionalSection2D, tolerance: float = 1.0e-10
) -> None:
    """Require coincident LE/TE and a simple, non-self-intersecting contour."""
    leading_gap = np.hypot(
        coordinates.suction_s[0] - coordinates.pressure_s[0],
        coordinates.suction_u[0] - coordinates.pressure_u[0],
    )
    trailing_gap = np.hypot(
        coordinates.suction_s[-1] - coordinates.pressure_s[-1],
        coordinates.suction_u[-1] - coordinates.pressure_u[-1],
    )
    if leading_gap > tolerance or trailing_gap > tolerance:
        raise ValueError(
            f"section {coordinates.index} is not closed: "
            f"LE gap={leading_gap:.6e}, TE gap={trailing_gap:.6e}"
        )

    contour = np.column_stack(
        (
            np.concatenate((coordinates.suction_s[::-1], coordinates.pressure_s[1:])),
            np.concatenate((coordinates.suction_u[::-1], coordinates.pressure_u[1:])),
        )
    )
    segment_count = len(contour) - 1
    for first in range(segment_count):
        for second in range(first + 2, segment_count):
            if first == 0 and second == segment_count - 1:
                continue
            if _properly_intersects(
                contour[first],
                contour[first + 1],
                contour[second],
                contour[second + 1],
            ):
                raise ValueError(
                    f"section {coordinates.index} has a self-intersection "
                    f"between contour segments {first} and {second}"
                )
