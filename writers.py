"""MISES blade, streamtube, and operating-condition writers."""

from __future__ import annotations

import math
import csv
from pathlib import Path
from typing import Iterable

from models import (
    ChordAlignedSection2D,
    ConvertedSection,
    DimensionalSection2D,
    IsesBoundaryResult,
    NormalizedSection2D,
    OperatingCondition,
)


def _write_rows(path: Path, header: Iterable[str], rows: Iterable[Iterable[float]]) -> None:
    with path.open("w", encoding="ascii", newline="\n") as handle:
        for line in header:
            handle.write(f"{line}\n")
        for row in rows:
            handle.write(" ".join(f"{value: .9e}" for value in row) + "\n")


def write_blade(
    path: Path,
    case_name: str,
    converted: ConvertedSection,
    nblade: int,
    ndel: tuple[int, int],
) -> None:
    n_suction, n_pressure = len(converted.suction_mp), len(converted.pressure_mp)
    if not (0 <= ndel[0] < n_suction - 1 and 0 <= ndel[1] < n_pressure - 1):
        raise ValueError("ndel must leave at least two points on each surface")
    chord = converted.suction_mp[-1] - converted.suction_mp[0]
    suction_rows = zip(
        converted.suction_mp[n_suction - ndel[0] - 1 :: -1],
        converted.suction_theta[n_suction - ndel[0] - 1 :: -1],
    )
    pressure_rows = zip(
        converted.pressure_mp[1 : n_pressure - ndel[1]],
        converted.pressure_theta[1 : n_pressure - ndel[1]],
    )
    metadata = (
        f"{converted.sinl: .9e} {converted.sout: .9e} {chord: .9e} "
        f"{chord: .9e} {2.0 * math.pi / nblade: .9e}"
    )
    _write_rows(
        path,
        [f"{case_name} cascade S1 analysis", metadata],
        [*suction_rows, *pressure_rows],
    )


def write_stream(path: Path, converted: ConvertedSection) -> None:
    m1, m2 = converted.suction_mp[0], converted.suction_mp[-1]
    chord = m2 - m1
    r1 = converted.suction_radius[0] / converted.chord_m
    r2 = converted.suction_radius[-1] / converted.chord_m
    rows = (
        (m1 - 5.0 * chord, r1, 1.0),
        (m1, r1, 1.0),
        (m2, r2, 1.0),
        (m2 + 5.0 * chord, r2, 1.0),
    )
    _write_rows(path, [f"{0.0: .9e}"], rows)


def write_dimensional_blade(
    path: Path,
    case_name: str,
    coordinates: DimensionalSection2D,
    ndel: tuple[int, int],
) -> None:
    """Write the alternative (s, u) blade walk in the input length unit."""
    n_suction, n_pressure = len(coordinates.suction_s), len(coordinates.pressure_s)
    if not (0 <= ndel[0] < n_suction - 1 and 0 <= ndel[1] < n_pressure - 1):
        raise ValueError("ndel must leave at least two points on each surface")
    suction_rows = zip(
        coordinates.suction_s[n_suction - ndel[0] - 1 :: -1],
        coordinates.suction_u[n_suction - ndel[0] - 1 :: -1],
    )
    pressure_rows = zip(
        coordinates.pressure_s[1 : n_pressure - ndel[1]],
        coordinates.pressure_u[1 : n_pressure - ndel[1]],
    )
    header = (
        f"{case_name} dimensional S-U blade coordinates",
        f"# theta_reference_rad {coordinates.theta_reference:.12e}",
        "# columns: s u (same length unit as input XYZ)",
    )
    _write_rows(path, header, [*suction_rows, *pressure_rows])


def write_chord_aligned_blade(
    path: Path,
    case_name: str,
    coordinates: ChordAlignedSection2D,
    ndel: tuple[int, int],
) -> None:
    """Write rigidly rotated dimensional coordinates with chord on x-axis."""
    n_suction, n_pressure = len(coordinates.suction_x), len(coordinates.pressure_x)
    if not (0 <= ndel[0] < n_suction - 1 and 0 <= ndel[1] < n_pressure - 1):
        raise ValueError("ndel must leave at least two points on each surface")
    suction_rows = zip(
        coordinates.suction_x[n_suction - ndel[0] - 1 :: -1],
        coordinates.suction_y[n_suction - ndel[0] - 1 :: -1],
    )
    pressure_rows = zip(
        coordinates.pressure_x[1 : n_pressure - ndel[1]],
        coordinates.pressure_y[1 : n_pressure - ndel[1]],
    )
    header = (
        f"{case_name} chord-aligned dimensional blade coordinates",
        f"# rotation_angle_rad {coordinates.rotation_angle:.12e}",
        f"# chord_length {coordinates.chord_length:.12e}",
        "# columns: x_chord y_normal (same length unit as input XYZ)",
    )
    _write_rows(path, header, [*suction_rows, *pressure_rows])


def write_normalized_blade(
    path: Path,
    case_name: str,
    coordinates: NormalizedSection2D,
    ndel: tuple[int, int],
) -> None:
    """Write the complete uncut unit-chord contour, including LE and TE."""
    n_suction, n_pressure = len(coordinates.suction_x), len(coordinates.pressure_x)
    if not (0 <= ndel[0] < n_suction - 1 and 0 <= ndel[1] < n_pressure - 1):
        raise ValueError("ndel must leave at least two points on each surface")
    suction_rows = zip(
        coordinates.suction_x[::-1],
        coordinates.suction_y[::-1],
    )
    pressure_rows = zip(
        coordinates.pressure_x[1:],
        coordinates.pressure_y[1:],
    )
    header = (
        f"{case_name} unit-chord blade coordinates",
        f"# rotation_angle_rad {coordinates.rotation_angle:.12e}",
        f"# original_chord_length {coordinates.original_chord_length:.12e}",
        f"# scale_factor {coordinates.scale_factor:.12e}",
        "# leading_edge 0.0 0.0",
        "# trailing_edge 1.0 0.0",
        "# point_set full_uncut_contour",
        "# columns: x_over_c y_over_c",
    )
    _write_rows(path, header, [*suction_rows, *pressure_rows])


def write_normalization_summary(
    path: Path, sections: Iterable[NormalizedSection2D]
) -> None:
    """Write per-section transformation metadata and normalized bounds."""
    fields = (
        "section",
        "rotation_angle_rad",
        "rotation_angle_deg",
        "original_chord_length",
        "scale_factor",
        "leading_edge_x",
        "leading_edge_y",
        "trailing_edge_x",
        "trailing_edge_y",
        "x_min",
        "x_max",
        "y_min",
        "y_max",
        "point_count_per_surface",
    )
    with path.open("w", encoding="ascii", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for section in sections:
            all_x = [*section.suction_x, *section.pressure_x]
            all_y = [*section.suction_y, *section.pressure_y]
            writer.writerow(
                {
                    "section": section.index,
                    "rotation_angle_rad": f"{section.rotation_angle:.12e}",
                    "rotation_angle_deg": f"{math.degrees(section.rotation_angle):.12e}",
                    "original_chord_length": f"{section.original_chord_length:.12e}",
                    "scale_factor": f"{section.scale_factor:.12e}",
                    "leading_edge_x": f"{section.suction_x[0]:.12e}",
                    "leading_edge_y": f"{section.suction_y[0]:.12e}",
                    "trailing_edge_x": f"{section.suction_x[-1]:.12e}",
                    "trailing_edge_y": f"{section.suction_y[-1]:.12e}",
                    "x_min": f"{min(all_x):.12e}",
                    "x_max": f"{max(all_x):.12e}",
                    "y_min": f"{min(all_y):.12e}",
                    "y_max": f"{max(all_y):.12e}",
                    "point_count_per_surface": len(section.suction_x),
                }
            )


def sutherland(temperature: float) -> float:
    return 1.7161e-5 * (temperature / 273.16) ** 1.5 * (273.16 + 124.0) / (
        temperature + 124.0
    )


def write_ises(
    path: Path, converted: ConvertedSection, condition: OperatingCondition
) -> IsesBoundaryResult:
    gamma, gas_constant = 1.4, 287.0
    cp = gamma / (gamma - 1.0) * gas_constant
    radius1 = converted.suction_radius[0] * condition.length_scale
    radius2 = converted.suction_radius[-1] * condition.length_scale
    omega = 2.0 * math.pi * condition.rpm / 60.0
    u1, u2 = radius1 * omega, radius2 * omega
    area1, area2 = 2.0 * math.pi * radius1, 2.0 * math.pi * radius2
    ht1 = cp * condition.inlet_total_temperature
    t2 = condition.inlet_total_temperature * (
        condition.outlet_static_pressure / condition.inlet_total_pressure
    ) ** ((gamma - 1.0) / gamma)
    rho2 = condition.outlet_static_pressure / (gas_constant * t2)
    c2 = math.sqrt(gamma * gas_constant * t2)
    beta2 = math.atan(converted.sout)
    v2m = 0.3 * c2
    for iteration in range(1, 52):
        mass = rho2 * area2 * v2m
        # Preserve the active write_ises3.f90 single inlet-density update.
        rho1 = condition.inlet_total_pressure / (
            gas_constant * condition.inlet_total_temperature
        )
        v1m = mass / (rho1 * area1)
        inlet_angle = math.radians(condition.inlet_absolute_angle)
        v1u = v1m * math.tan(inlet_angle)
        t1 = condition.inlet_total_temperature - 0.5 * (v1u**2 + v1m**2) / cp
        p1 = condition.inlet_total_pressure * (
            t1 / condition.inlet_total_temperature
        ) ** (gamma / (gamma - 1.0))
        rho1 = p1 / (gas_constant * t1)
        ht1r = cp * t1 + 0.5 * (v1m**2 + (v1u - u1) ** 2)
        ht2r = ht1r - 0.5 * (u1**2 - u2**2)
        outlet_relative_energy = ht2r - cp * t2
        if outlet_relative_energy <= 0.0:
            raise ValueError(
                "operating condition is incompatible with section "
                f"{converted.index}: computed outlet relative kinetic energy "
                f"is {outlet_relative_energy:.6g} J/kg; check length_scale, rpm, "
                "pressures, and temperatures"
            )
        w2 = math.sqrt(2.0 * outlet_relative_energy)
        next_v2m = w2 * math.cos(beta2)
        error = abs(v2m - next_v2m) / next_v2m
        v2m += 0.4 * (next_v2m - v2m)
        if error <= 1.0e-4:
            break
    else:
        raise RuntimeError("MISES boundary-condition iteration did not converge")

    m1, m2 = converted.suction_mp[0], converted.suction_mp[-1]
    xinl, xout = m1 - 0.5 * (m2 - m1), m2 + 0.5 * (m2 - m1)
    w1u = v1m * math.tan(inlet_angle) - u1
    w1 = math.hypot(w1u, v1m)
    inlet_mach = w1 / math.sqrt(gamma * gas_constant * t1)
    relative_total_pressure = condition.inlet_total_pressure * (ht1r / ht1) ** (
        gamma / (gamma - 1.0)
    )
    reynolds = rho1 * w1 * converted.chord_m / sutherland(t1)
    with path.open("w", encoding="ascii", newline="\n") as handle:
        if inlet_mach > 1.0:
            handle.write("  1  2  5 15  6\n 15  4  3 18  6\n")
            inlet = (inlet_mach, 0.0, 0.0, xinl, 0.0)
            outlet = (
                0.0,
                condition.outlet_static_pressure / relative_total_pressure,
                0.0,
                xout,
                0.0,
            )
        else:
            handle.write("  1  2  5\n  1  4  3\n")
            inlet = (inlet_mach, 0.0, w1u / v1m, xinl, 0.0)
            outlet = (0.0, 0.0, 0.0, xout, 0.0)
        handle.write("".join(f"{value:12.4g}" for value in inlet) + " |MINLin, P1PTin, SINLin, XINL, V1ATin\n")
        handle.write("".join(f"{value:12.4g}" for value in outlet) + " |MOUTin, P2PTin, SOUTin, XOUT, V2ATin\n")
        handle.write(f"{0.0:12.4g}{0.0:12.4g} |MFRin, HWRATin\n")
        handle.write(f"{reynolds:12.4g}{9.0:12.4g} |REYNin, NCRIT\n")
        handle.write(f"{0.02:12.4g}{0.02:12.4g} |TRANS1, TRANS2\n")
        handle.write(f"{4:4d}{0.95:12.4g}{1.0:12.4g} |ISMOM, MCRIT, MUCON\n")
        handle.write(f"{0.0:12.4g}{0.0:12.4g} |BVR1in, BVR2in\n")

    return IsesBoundaryResult(
        section=converted.index,
        inlet_regime="supersonic" if inlet_mach > 1.0 else "subsonic",
        inlet_relative_mach=inlet_mach,
        outlet_relative_mach=w2 / c2,
        outlet_pressure_ratio=condition.outlet_static_pressure
        / relative_total_pressure,
        inlet_slope=w1u / v1m,
        outlet_slope=math.tan(beta2),
        inlet_plane=xinl,
        outlet_plane=xout,
        reynolds_number=reynolds,
        iterations=iteration,
    )


def write_ises_summary(
    path: Path,
    condition: OperatingCondition,
    results: Iterable[IsesBoundaryResult],
) -> None:
    """Write operating conditions and derived MISES values for all sections."""
    fields = (
        "section",
        "inlet_regime",
        "length_scale",
        "rpm",
        "inlet_total_pressure",
        "inlet_total_temperature",
        "inlet_absolute_angle_deg",
        "outlet_static_pressure",
        "inlet_relative_mach",
        "outlet_relative_mach",
        "outlet_pressure_ratio",
        "inlet_slope",
        "outlet_slope",
        "inlet_plane",
        "outlet_plane",
        "reynolds_number",
        "iterations",
    )
    with path.open("w", encoding="ascii", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "section": result.section,
                    "inlet_regime": result.inlet_regime,
                    "length_scale": f"{condition.length_scale:.12e}",
                    "rpm": f"{condition.rpm:.12e}",
                    "inlet_total_pressure": f"{condition.inlet_total_pressure:.12e}",
                    "inlet_total_temperature": (
                        f"{condition.inlet_total_temperature:.12e}"
                    ),
                    "inlet_absolute_angle_deg": (
                        f"{condition.inlet_absolute_angle:.12e}"
                    ),
                    "outlet_static_pressure": (
                        f"{condition.outlet_static_pressure:.12e}"
                    ),
                    "inlet_relative_mach": f"{result.inlet_relative_mach:.12e}",
                    "outlet_relative_mach": f"{result.outlet_relative_mach:.12e}",
                    "outlet_pressure_ratio": f"{result.outlet_pressure_ratio:.12e}",
                    "inlet_slope": f"{result.inlet_slope:.12e}",
                    "outlet_slope": f"{result.outlet_slope:.12e}",
                    "inlet_plane": f"{result.inlet_plane:.12e}",
                    "outlet_plane": f"{result.outlet_plane:.12e}",
                    "reynolds_number": f"{result.reynolds_number:.12e}",
                    "iterations": result.iterations,
                }
            )
