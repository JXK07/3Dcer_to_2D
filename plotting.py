"""Matplotlib result plots; no Tecplot files are produced."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import numpy as np

from models import (
    ChordAlignedSection2D,
    ConvertedSection,
    DimensionalSection2D,
    NormalizedSection2D,
)


def plot_check(
    path: Path | None,
    converted: ConvertedSection,
    ndel: tuple[int, int],
    *,
    show: bool = False,
) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 6), dpi=120)
    ax.plot(converted.suction_mp, converted.suction_theta, color="#d1495b", label="No cut")
    ax.plot(converted.pressure_mp[::-1], converted.pressure_theta[::-1], color="#d1495b")
    n_suction, n_pressure = len(converted.suction_mp), len(converted.pressure_mp)
    cut_mp = np.concatenate(
        (
            converted.suction_mp[n_suction - ndel[0] - 1 :: -1],
            converted.pressure_mp[1 : n_pressure - ndel[1]],
        )
    )
    cut_theta = np.concatenate(
        (
            converted.suction_theta[n_suction - ndel[0] - 1 :: -1],
            converted.pressure_theta[1 : n_pressure - ndel[1]],
        )
    )
    ax.plot(cut_mp, cut_theta, color="#00798c", label="With cut")
    ax.set(xlabel="m'", ylabel="theta", title=f"Section {converted.index} MISES geometry")
    ax.axis("equal")
    ax.grid(linestyle="--", alpha=0.35)
    ax.legend()
    fig.tight_layout()
    if path is not None:
        fig.savefig(path, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(fig)


def plot_overview(path: Path, sections: Sequence[ConvertedSection]) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(11, 7), dpi=140)
    colors = plt.colormaps["viridis"](np.linspace(0.05, 0.95, len(sections)))
    for section, color in zip(sections, colors):
        ax.plot(section.suction_mp, section.suction_theta, color=color, linewidth=1.1)
        ax.plot(section.pressure_mp, section.pressure_theta, color=color, linewidth=1.1)
    ax.set(xlabel="m'", ylabel="theta", title="All converted blade sections")
    ax.grid(linestyle="--", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def plot_dimensional_check(
    path: Path | None,
    coordinates: DimensionalSection2D,
    ndel: tuple[int, int],
    *,
    show: bool = False,
) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 6), dpi=120)
    ax.plot(coordinates.suction_s, coordinates.suction_u, color="#d1495b", label="No cut")
    ax.plot(coordinates.pressure_s[::-1], coordinates.pressure_u[::-1], color="#d1495b")
    n_suction, n_pressure = len(coordinates.suction_s), len(coordinates.pressure_s)
    cut_s = np.concatenate(
        (
            coordinates.suction_s[n_suction - ndel[0] - 1 :: -1],
            coordinates.pressure_s[1 : n_pressure - ndel[1]],
        )
    )
    cut_u = np.concatenate(
        (
            coordinates.suction_u[n_suction - ndel[0] - 1 :: -1],
            coordinates.pressure_u[1 : n_pressure - ndel[1]],
        )
    )
    ax.plot(cut_s, cut_u, color="#00798c", label="With cut")
    ax.set(
        xlabel="Meridional arc length s",
        ylabel="Circumferential arc length u",
        title=f"Section {coordinates.index} dimensional S-U coordinates",
    )
    ax.axis("equal")
    ax.grid(linestyle="--", alpha=0.35)
    ax.legend()
    fig.tight_layout()
    if path is not None:
        fig.savefig(path, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(fig)


def plot_dimensional_overview(
    path: Path, sections: Sequence[DimensionalSection2D]
) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(11, 7), dpi=140)
    colors = plt.colormaps["plasma"](np.linspace(0.05, 0.9, len(sections)))
    for section, color in zip(sections, colors):
        ax.plot(section.suction_s, section.suction_u, color=color, linewidth=1.1)
        ax.plot(section.pressure_s, section.pressure_u, color=color, linewidth=1.1)
    ax.set(
        xlabel="Meridional arc length s",
        ylabel="Circumferential arc length u",
        title="All blade sections in dimensional S-U coordinates",
    )
    ax.grid(linestyle="--", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def plot_chord_aligned_check(
    path: Path | None,
    coordinates: ChordAlignedSection2D,
    ndel: tuple[int, int],
    *,
    show: bool = False,
) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 6), dpi=120)
    ax.plot(coordinates.suction_x, coordinates.suction_y, color="#d1495b", label="No cut")
    ax.plot(coordinates.pressure_x[::-1], coordinates.pressure_y[::-1], color="#d1495b")
    n_suction, n_pressure = len(coordinates.suction_x), len(coordinates.pressure_x)
    cut_x = np.concatenate(
        (
            coordinates.suction_x[n_suction - ndel[0] - 1 :: -1],
            coordinates.pressure_x[1 : n_pressure - ndel[1]],
        )
    )
    cut_y = np.concatenate(
        (
            coordinates.suction_y[n_suction - ndel[0] - 1 :: -1],
            coordinates.pressure_y[1 : n_pressure - ndel[1]],
        )
    )
    ax.plot(cut_x, cut_y, color="#00798c", label="With cut")
    ax.axhline(0.0, color="#777777", linewidth=0.8, linestyle="--")
    ax.set(
        xlabel="Chordwise x",
        ylabel="Chord-normal y",
        title=f"Section {coordinates.index} chord-aligned coordinates",
    )
    ax.axis("equal")
    ax.grid(linestyle="--", alpha=0.35)
    ax.legend()
    fig.tight_layout()
    if path is not None:
        fig.savefig(path, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(fig)


def plot_chord_aligned_overview(
    path: Path, sections: Sequence[ChordAlignedSection2D]
) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(11, 7), dpi=140)
    colors = plt.colormaps["cividis"](np.linspace(0.05, 0.95, len(sections)))
    for section, color in zip(sections, colors):
        ax.plot(section.suction_x, section.suction_y, color=color, linewidth=1.1)
        ax.plot(section.pressure_x, section.pressure_y, color=color, linewidth=1.1)
    ax.axhline(0.0, color="#777777", linewidth=0.8, linestyle="--")
    ax.set(
        xlabel="Chordwise x",
        ylabel="Chord-normal y",
        title="All blade sections with LE-TE chord aligned to x-axis",
    )
    ax.axis("equal")
    ax.grid(linestyle="--", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def plot_normalized_check(
    path: Path | None,
    coordinates: NormalizedSection2D,
    ndel: tuple[int, int],
    *,
    show: bool = False,
) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 6), dpi=120)
    ax.plot(coordinates.suction_x, coordinates.suction_y, color="#d1495b", label="No cut")
    ax.plot(coordinates.pressure_x[::-1], coordinates.pressure_y[::-1], color="#d1495b")
    n_suction, n_pressure = len(coordinates.suction_x), len(coordinates.pressure_x)
    cut_x = np.concatenate(
        (
            coordinates.suction_x[n_suction - ndel[0] - 1 :: -1],
            coordinates.pressure_x[1 : n_pressure - ndel[1]],
        )
    )
    cut_y = np.concatenate(
        (
            coordinates.suction_y[n_suction - ndel[0] - 1 :: -1],
            coordinates.pressure_y[1 : n_pressure - ndel[1]],
        )
    )
    ax.plot(cut_x, cut_y, color="#00798c", label="With cut")
    ax.axhline(0.0, color="#777777", linewidth=0.8, linestyle="--")
    ax.scatter([0.0, 1.0], [0.0, 0.0], color="#222222", s=18, zorder=5)
    ax.set(
        xlabel="x / chord",
        ylabel="y / chord",
        title=f"Section {coordinates.index} normalized to unit chord",
    )
    ax.axis("equal")
    ax.grid(linestyle="--", alpha=0.35)
    ax.legend()
    fig.tight_layout()
    if path is not None:
        fig.savefig(path, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(fig)


def plot_normalized_overview(
    path: Path, sections: Sequence[NormalizedSection2D]
) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(11, 7), dpi=140)
    colors = plt.colormaps["turbo"](np.linspace(0.05, 0.95, len(sections)))
    for section, color in zip(sections, colors):
        ax.plot(section.suction_x, section.suction_y, color=color, linewidth=1.1)
        ax.plot(section.pressure_x, section.pressure_y, color=color, linewidth=1.1)
    ax.axhline(0.0, color="#777777", linewidth=0.8, linestyle="--")
    ax.scatter([0.0, 1.0], [0.0, 0.0], color="#222222", s=20, zorder=5)
    ax.set(
        xlabel="x / chord",
        ylabel="y / chord",
        title="All blade sections normalized to unit chord",
    )
    ax.axis("equal")
    ax.grid(linestyle="--", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
