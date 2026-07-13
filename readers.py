"""Readers for geomTurbo, legacy geom, and operating-condition files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Sequence

import numpy as np

from models import BladeSection, OperatingCondition


_INT_RE = re.compile(r"^[+-]?\d+$")
_FLOAT_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][+-]?\d+)?$")


def _clean_lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8-sig").splitlines()]


def _first_integer(lines: Sequence[str], start: int) -> tuple[int, int]:
    for pos in range(start, len(lines)):
        token = lines[pos].split("!", 1)[0].strip()
        if _INT_RE.fullmatch(token):
            return int(token), pos
    raise ValueError("expected an integer after a format marker")


def _coordinate(line: str) -> list[float] | None:
    tokens = line.replace(",", " ").split()
    if len(tokens) < 3 or not all(_FLOAT_RE.fullmatch(value) for value in tokens[:3]):
        return None
    return [float(value.replace("D", "E").replace("d", "e")) for value in tokens[:3]]


def _surface_sections(lines: Sequence[str], marker: str) -> list[np.ndarray]:
    marker_pos = next(
        (
            i
            for i, line in enumerate(lines)
            if line.casefold() == marker or line.casefold().startswith(marker + " ")
        ),
        None,
    )
    if marker_pos is None:
        raise ValueError(f"missing {marker!r} surface block")
    sectional_pos = next(
        (i for i in range(marker_pos + 1, len(lines)) if lines[i].casefold() == "sectional"),
        None,
    )
    if sectional_pos is None:
        raise ValueError(f"missing SECTIONAL marker below {marker}")
    count, pos = _first_integer(lines, sectional_pos + 1)
    sections: list[np.ndarray] = []
    while len(sections) < count:
        xyz_pos = next(
            (i for i in range(pos + 1, len(lines)) if lines[i].casefold() == "xyz"),
            None,
        )
        if xyz_pos is None:
            raise ValueError(f"{marker} declares {count} sections but only {len(sections)} were found")
        point_count, count_pos = _first_integer(lines, xyz_pos + 1)
        points: list[list[float]] = []
        pos = count_pos
        while len(points) < point_count:
            pos += 1
            if pos >= len(lines):
                raise ValueError(f"unexpected end of file in {marker} section {len(sections) + 1}")
            point = _coordinate(lines[pos])
            if point is None:
                if lines[pos] and not lines[pos].startswith("#"):
                    raise ValueError(
                        f"invalid coordinate in {marker} section {len(sections) + 1}: {lines[pos]!r}"
                    )
                continue
            points.append(point)
        sections.append(np.asarray(points, dtype=float))
    return sections


def _blade_count(lines: Sequence[str]) -> int | None:
    patterns = (
        re.compile(r"\bnumber_of_blades\b\s*[:=]?\s*(\d+)", re.IGNORECASE),
        re.compile(r"\bperiodicity\b\s*[:=]?\s*(\d+)", re.IGNORECASE),
    )
    for i, line in enumerate(lines):
        for pattern in patterns:
            match = pattern.search(line)
            if match:
                return int(match.group(1))
        if line.casefold() in {"number_of_blades", "periodicity"}:
            try:
                value, _ = _first_integer(lines, i + 1)
                return value
            except ValueError:
                pass
    return None


def read_geomturbo(path: str | Path) -> tuple[list[BladeSection], int | None]:
    lines = _clean_lines(Path(path))
    suction = _surface_sections(lines, "suction")
    pressure = _surface_sections(lines, "pressure")
    if len(suction) != len(pressure):
        raise ValueError(
            f"surface section counts differ: suction={len(suction)}, pressure={len(pressure)}"
        )
    sections = [
        BladeSection(index, suction_side, pressure_side)
        for index, (suction_side, pressure_side) in enumerate(zip(suction, pressure), start=1)
    ]
    return sections, _blade_count(lines)


def read_xyz_section(path: str | Path) -> tuple[list[BladeSection], int]:
    """Read blade count and one suction/pressure section from a plain XYZ file."""
    lines = _clean_lines(Path(path))
    blade_count_pos = next(
        (i for i, line in enumerate(lines) if line and not line.startswith("#")), None
    )
    if blade_count_pos is None or not _INT_RE.fullmatch(lines[blade_count_pos]):
        raise ValueError("XYZ text must start with a positive integer blade count")
    blade_count = int(lines[blade_count_pos])
    if blade_count <= 0:
        raise ValueError("XYZ text blade count must be positive")

    surfaces: dict[str, list[list[float]]] = {"suction": [], "pressure": []}
    active_surface: str | None = None
    for line_number, line in enumerate(lines, start=1):
        if line_number - 1 == blade_count_pos:
            continue
        if not line or line.startswith("#"):
            continue
        label = line.casefold().replace("_", " ").strip()
        if label in {"suction", "suction side"}:
            active_surface = "suction"
            continue
        if label in {"pressure", "pressure side"}:
            active_surface = "pressure"
            continue
        point = _coordinate(line)
        if point is None:
            raise ValueError(f"invalid XYZ text at line {line_number}: {line!r}")
        if active_surface is None:
            raise ValueError(
                f"XYZ coordinate appears before suction/pressure label at line {line_number}"
            )
        surfaces[active_surface].append(point)

    for name, points in surfaces.items():
        if len(points) < 2:
            raise ValueError(f"XYZ text surface {name!r} must contain at least two points")
    section = BladeSection(
        1,
        np.asarray(surfaces["suction"], dtype=float),
        np.asarray(surfaces["pressure"], dtype=float),
    )
    return [section], blade_count


def read_legacy_geom(path: str | Path) -> tuple[list[BladeSection], int]:
    lines = _clean_lines(Path(path))
    first = next((line for line in lines if line and not line.startswith("#")), "")
    values = first.split()
    if len(values) < 2 or not all(_INT_RE.fullmatch(value) for value in values[:2]):
        raise ValueError("invalid legacy geom header; expected '<blade count> <max points>'")
    surfaces: list[np.ndarray] = []
    pos = lines.index(first)
    for _ in range(2):
        xyz_pos = next(i for i in range(pos + 1, len(lines)) if lines[i].casefold() == "xyz")
        count, count_pos = _first_integer(lines, xyz_pos + 1)
        points: list[list[float]] = []
        pos = count_pos
        while len(points) < count:
            pos += 1
            point = _coordinate(lines[pos])
            if point is not None:
                points.append(point)
        surfaces.append(np.asarray(points, dtype=float))
    return [BladeSection(1, surfaces[0], surfaces[1])], int(values[0])


def read_operating_condition(path: str | Path) -> OperatingCondition:
    """Read either the legacy six-number layout or a named key-value layout."""
    raw_lines = Path(path).read_text(encoding="utf-8-sig").splitlines()
    lines = []
    for raw_line in raw_lines:
        line = raw_line.split("#", 1)[0].split("!", 1)[0].strip()
        if line:
            lines.append(line)

    aliases = {
        "length_scale": "length_scale",
        "lscale": "length_scale",
        "rpm": "rpm",
        "inlet_total_pressure": "inlet_total_pressure",
        "pt1": "inlet_total_pressure",
        "inlet_total_temperature": "inlet_total_temperature",
        "tt1": "inlet_total_temperature",
        "inlet_absolute_angle": "inlet_absolute_angle",
        "alpha1": "inlet_absolute_angle",
        "outlet_static_pressure": "outlet_static_pressure",
        "p2": "outlet_static_pressure",
    }
    if any("=" in line for line in lines):
        values: dict[str, float] = {}
        for line in lines:
            if "=" not in line:
                raise ValueError(f"invalid operating-condition line: {line!r}")
            key, value = (part.strip() for part in line.split("=", 1))
            normalized_key = aliases.get(key.casefold())
            if normalized_key is None:
                raise ValueError(f"unknown operating-condition field: {key!r}")
            values[normalized_key] = float(value)
        required = tuple(OperatingCondition.__dataclass_fields__)
        missing = [field for field in required if field not in values]
        if missing:
            raise ValueError(f"missing operating-condition fields: {', '.join(missing)}")
        condition = OperatingCondition(*(values[field] for field in required))
    else:
        tokens = " ".join(lines).split()
        if len(tokens) < 6:
            raise ValueError("operating-condition file must contain six numbers")
        condition = OperatingCondition(*map(float, tokens[:6]))

    if condition.length_scale <= 0.0:
        raise ValueError("length_scale must be positive")
    if condition.inlet_total_pressure <= 0.0 or condition.outlet_static_pressure <= 0.0:
        raise ValueError("pressures must be positive")
    if condition.inlet_total_temperature <= 0.0:
        raise ValueError("inlet_total_temperature must be positive")
    return condition
