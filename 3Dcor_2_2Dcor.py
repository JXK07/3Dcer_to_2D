#!/usr/bin/env python3

from cli import main
from geometry import (
    NP_MAX,
    align_chord_to_x,
    convert_section,
    dimensional_coordinates,
    meridional_coordinate,
    normalize_chord,
    redistribute,
)
from models import (
    BladeSection,
    ChordAlignedSection2D,
    ConvertedSection,
    DimensionalSection2D,
    IsesBoundaryResult,
    NormalizedSection2D,
    OperatingCondition,
)
from readers import read_geomturbo, read_legacy_geom, read_operating_condition, read_xyz_section
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


if __name__ == "__main__":
    raise SystemExit(main())
