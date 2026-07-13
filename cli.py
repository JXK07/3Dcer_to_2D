"""Command-line orchestration for AG5-Cascade2D."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from geometry import (
    align_chord_to_x,
    convert_section,
    dimensional_coordinates,
    normalize_chord,
)
from plotting import (
    plot_check,
    plot_chord_aligned_check,
    plot_chord_aligned_overview,
    plot_dimensional_check,
    plot_dimensional_overview,
    plot_overview,
    plot_normalized_check,
    plot_normalized_overview,
)
from readers import (
    read_geomturbo,
    read_legacy_geom,
    read_operating_condition,
    read_xyz_section,
)
from validation import validate_dimensional_contour
from writers import (
    write_blade,
    write_chord_aligned_blade,
    write_dimensional_blade,
    write_ises,
    write_ises_summary,
    write_normalization_summary,
    write_normalized_blade,
    write_stream,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ag5-cascade2d",
        description=(
            "Convert AutoGrid5 3D Cartesian blade sections to MISES, "
            "arc-length, chord-aligned, and unit-chord 2D coordinates."
        ),
    )
    parser.add_argument("input", type=Path, help="input geometry file")
    parser.add_argument(
        "--input-format",
        choices=("geomturbo", "xyz", "legacy"),
        default="geomturbo",
        help="input layout; default keeps the existing geomTurbo behavior",
    )
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    parser.add_argument("--case", help="output case prefix (default: input stem)")
    parser.add_argument(
        "--ndel", type=int, nargs=2, metavar=("SUCTION", "PRESSURE"), default=(7, 7)
    )
    parser.add_argument(
        "--opr",
        "--operating-condition",
        dest="operating_condition",
        type=Path,
        help="MISES operating conditions: named fields or legacy six-number opr file",
    )
    parser.add_argument("--plot", choices=("save", "show", "none"), default="save")
    parser.add_argument(
        "--align-su-chord",
        action="store_true",
        help="also rotate dimensional S-U coordinates so the LE-TE chord lies on x-axis",
    )
    parser.add_argument(
        "--normalize-chord",
        action="store_true",
        help="also uniformly scale chord-aligned coordinates to LE=(0,0), TE=(1,0)",
    )
    parser.add_argument(
        "--legacy",
        action="store_true",
        help="compatibility alias for --input-format legacy",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    input_format = "legacy" if args.legacy else args.input_format
    readers = {
        "geomturbo": read_geomturbo,
        "xyz": read_xyz_section,
        "legacy": read_legacy_geom,
    }
    sections, nblade = readers[input_format](args.input)
    if not nblade or nblade <= 0:
        raise ValueError(
            f"blade count is missing or invalid in {input_format!r} input"
        )
    condition = (
        read_operating_condition(args.operating_condition)
        if args.operating_condition
        else None
    )
    case = args.case or args.input.stem
    ndel = tuple(args.ndel)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    converted_sections = []
    dimensional_sections = []
    aligned_sections = []
    normalized_sections = []
    ises_results = []
    width = max(2, len(str(len(sections))))
    print(f"Read {len(sections)} section(s), blade count={nblade}")
    for section in sections:
        converted = convert_section(section)
        dimensional = dimensional_coordinates(section)
        validate_dimensional_contour(dimensional)
        needs_alignment = args.align_su_chord or args.normalize_chord
        aligned = align_chord_to_x(dimensional) if needs_alignment else None
        normalized = normalize_chord(aligned) if args.normalize_chord and aligned else None
        converted_sections.append(converted)
        dimensional_sections.append(dimensional)
        if aligned is not None:
            aligned_sections.append(aligned)
        if normalized is not None:
            normalized_sections.append(normalized)
        suffix = f"{case}_section_{section.index:0{width}d}"
        write_blade(args.output_dir / f"blade.{suffix}", suffix, converted, nblade, ndel)
        write_stream(args.output_dir / f"stream.{suffix}", converted)
        write_dimensional_blade(
            args.output_dir / f"blade_su.{suffix}", suffix, dimensional, ndel
        )
        if aligned is not None:
            write_chord_aligned_blade(
                args.output_dir / f"blade_xy.{suffix}", suffix, aligned, ndel
            )
        if normalized is not None:
            write_normalized_blade(
                args.output_dir / f"blade_xyn.{suffix}", suffix, normalized, ndel
            )
        if condition is not None:
            ises_results.append(
                write_ises(args.output_dir / f"ises.{suffix}", converted, condition)
            )
        if args.plot != "none":
            plot_path = args.output_dir / f"{suffix}_check.png" if args.plot == "save" else None
            plot_check(plot_path, converted, ndel, show=args.plot == "show")
            su_plot_path = (
                args.output_dir / f"{suffix}_su_check.png" if args.plot == "save" else None
            )
            plot_dimensional_check(
                su_plot_path, dimensional, ndel, show=args.plot == "show"
            )
            if aligned is not None:
                xy_plot_path = (
                    args.output_dir / f"{suffix}_xy_check.png"
                    if args.plot == "save"
                    else None
                )
                plot_chord_aligned_check(
                    xy_plot_path, aligned, ndel, show=args.plot == "show"
                )
            if normalized is not None:
                xyn_plot_path = (
                    args.output_dir / f"{suffix}_xyn_check.png"
                    if args.plot == "save"
                    else None
                )
                plot_normalized_check(
                    xyn_plot_path, normalized, ndel, show=args.plot == "show"
                )
        print(f"Converted section {section.index}: {suffix}")
    if args.plot == "save" and len(converted_sections) > 1:
        plot_overview(args.output_dir / f"{case}_overview.png", converted_sections)
        plot_dimensional_overview(
            args.output_dir / f"{case}_su_overview.png", dimensional_sections
        )
        if aligned_sections:
            plot_chord_aligned_overview(
                args.output_dir / f"{case}_xy_overview.png", aligned_sections
            )
        if normalized_sections:
            plot_normalized_overview(
                args.output_dir / f"{case}_xyn_overview.png", normalized_sections
            )
    if normalized_sections:
        write_normalization_summary(
            args.output_dir / f"{case}_normalization_summary.csv",
            normalized_sections,
        )
    if condition is not None:
        write_ises_summary(
            args.output_dir / f"{case}_ises_summary.csv", condition, ises_results
        )
        print(
            "Generated MISES boundary conditions from "
            f"{args.operating_condition} ({len(ises_results)} section(s))"
        )
    print(f"Results saved to: {args.output_dir.resolve()}")
    return 0
