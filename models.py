"""Shared immutable data models."""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class BladeSection:
    index: int
    suction: np.ndarray
    pressure: np.ndarray


@dataclass(frozen=True, slots=True)
class ConvertedSection:
    index: int
    suction_mp: np.ndarray
    suction_theta: np.ndarray
    suction_radius: np.ndarray
    pressure_mp: np.ndarray
    pressure_theta: np.ndarray
    chord_m: float
    sinl: float
    sout: float


@dataclass(frozen=True, slots=True)
class DimensionalSection2D:
    """Length-dimensional meridional/circumferential coordinates (s, u)."""

    index: int
    suction_s: np.ndarray
    suction_u: np.ndarray
    pressure_s: np.ndarray
    pressure_u: np.ndarray
    theta_reference: float


@dataclass(frozen=True, slots=True)
class ChordAlignedSection2D:
    """Rigidly rotated dimensional coordinates with the LE-TE chord on x."""

    index: int
    suction_x: np.ndarray
    suction_y: np.ndarray
    pressure_x: np.ndarray
    pressure_y: np.ndarray
    rotation_angle: float
    chord_length: float


@dataclass(frozen=True, slots=True)
class NormalizedSection2D:
    """Chord-aligned coordinates uniformly scaled to unit chord."""

    index: int
    suction_x: np.ndarray
    suction_y: np.ndarray
    pressure_x: np.ndarray
    pressure_y: np.ndarray
    rotation_angle: float
    original_chord_length: float
    scale_factor: float


@dataclass(frozen=True, slots=True)
class OperatingCondition:
    length_scale: float
    rpm: float
    inlet_total_pressure: float
    inlet_total_temperature: float
    inlet_absolute_angle: float
    outlet_static_pressure: float


@dataclass(frozen=True, slots=True)
class IsesBoundaryResult:
    """Derived MISES boundary values for one blade section."""

    section: int
    inlet_regime: str
    inlet_relative_mach: float
    outlet_relative_mach: float
    outlet_pressure_ratio: float
    inlet_slope: float
    outlet_slope: float
    inlet_plane: float
    outlet_plane: float
    reynolds_number: float
    iterations: int
