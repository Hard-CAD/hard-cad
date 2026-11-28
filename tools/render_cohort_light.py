"""Render a publication-grade light-theme SVG for the 41-pair revision cohort.

Uses the exact published aggregate coordinates from tools/render_readme_cohort.py
(https://doi.org/10.1016/j.cag.2026.104824), styled for a crisp light academic
webpage without dark boxes or purple clipart accents.
"""

from io import StringIO
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FuncFormatter

OUT = Path(__file__).resolve().parents[1] / "assets" / "renders" / "cohort-light.svg"

INK = "#16242b"
MUTED = "#52626b"
GRID = "#e5ebef"
SPINE = "#64748b"
TEAL = "#1f5f5b"
SLATE = "#365973"
CRIMSON = "#b43f35"

ORIGIN = (0.0, 0.0)
POINTS = {
    "cad06": (0.5195861049519583, 596.9026041820603),
    "cad15": (0.0001261056538965355, -28.27433388231293),
    "cad30": (0.03042817358163505, 1987.300888156923),
}


def style_axes(ax, xticks, yticks):
    ax.set_facecolor("#ffffff")
    ax.xaxis.set_major_locator(FixedLocator(xticks))
    ax.yaxis.set_major_locator(FixedLocator(yticks))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}".replace("-", "−")))
    ax.tick_params(colors=MUTED, labelsize=10.5, length=4, width=0.8, pad=6)
    for side, spine in ax.spines.items():
        spine.set_visible(side in ("left", "bottom"))
        spine.set_color(SPINE)
        spine.set_linewidth(0.9)
    ax.grid(True, linewidth=0.7, color=GRID)
    ax.set_axisbelow(True)
    ax.axhline(0, color="#94a3b8", linewidth=0.85, linestyle="--", zorder=1)
    ax.axvline(0, color="#94a3b8", linewidth=0.85, linestyle="--", zorder=1)
    ax.set_ylabel("Δ extra material (mm³)", fontsize=10.5, color=INK, labelpad=8)


def add_point(ax, coords, color, marker, size=72):
    ax.scatter(
        *coords,
        marker=marker,
        s=size,
        facecolor=color,
        edgecolor="#ffffff",
        linewidth=1.2,
        zorder=5,
    )


def add_label(ax, text, coords, offset, color, ha="left"):
    ax.annotate(
        text,
        coords,
        xytext=offset,
        textcoords="offset points",
        ha=ha,
        va="center",
        color=color,
        fontsize=10.5,
        fontweight="medium",
        zorder=6,
        arrowprops={
            "arrowstyle": "-",
            "color": color,
            "alpha": 0.6,
            "linewidth": 0.85,
            "shrinkA": 3,
            "shrinkB": 6,
        },
    )


def main():
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "svg.fonttype": "path",
        "svg.hashsalt": "hardcad-cohort-light-v1",
    })

    fig = plt.figure(figsize=(11.6, 4.15), facecolor="#ffffff")

    # Left panel: All 41 eligible revision pairs
    ax_full = fig.add_axes((0.085, 0.17, 0.445, 0.68))
    style_axes(ax_full, (0, 0.2, 0.4, 0.6), (0, 1000, 2000))
    ax_full.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:g}"))
    ax_full.set(xlim=(-0.05, 0.63), ylim=(-340, 2320))
    ax_full.set_xlabel("Δ IoU (revised − initial)", fontsize=10.5, color=INK, labelpad=7)
    ax_full.set_title("(a) All 41 eligible revision pairs", loc="left", fontsize=11.5, fontweight="bold", color=INK, pad=12)

    add_point(ax_full, ORIGIN, TEAL, "o", 95)
    add_point(ax_full, POINTS["cad15"], CRIMSON, "^", 46)
    add_point(ax_full, POINTS["cad30"], SLATE, "D", 72)
    add_point(ax_full, POINTS["cad06"], SLATE, "D", 72)

    add_label(ax_full, "38 pairs at origin (0, 0)", ORIGIN, (26, 26), TEAL, ha="left")
    add_label(ax_full, "cad30  (+1,987 mm³, void clears)", POINTS["cad30"], (24, 0), SLATE, ha="left")
    add_label(ax_full, "cad06", POINTS["cad06"], (-22, 22), SLATE, ha="right")

    # Right panel: Origin enlargement isolating cad15
    ax_zoom = fig.add_axes((0.625, 0.17, 0.345, 0.68))
    style_axes(ax_zoom, (0, 0.0001, 0.0002), (-40, -20, 0))
    ax_zoom.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x * 1e4:g}"))
    ax_zoom.set(xlim=(-0.000022, 0.00023), ylim=(-44, 9))
    ax_zoom.set_xlabel("Δ IoU (×10⁻⁴)", fontsize=10.5, color=INK, labelpad=7)
    ax_zoom.set_title("(b) Origin enlargement (cad15 regression)", loc="left", fontsize=11.5, fontweight="bold", color=INK, pad=12)

    add_point(ax_zoom, ORIGIN, TEAL, "o", 95)
    add_point(ax_zoom, POINTS["cad15"], CRIMSON, "^", 92)
    add_label(ax_zoom, "38 pairs", ORIGIN, (22, -16), TEAL, ha="left")
    add_label(ax_zoom, "cad15\nΔIoU +1.26×10⁻⁴\nΔE_V −28.27 mm³\n(side bore blocked)", POINTS["cad15"], (22, 6), CRIMSON, ha="left")

    buf = StringIO()
    fig.savefig(buf, format="svg", metadata={"Date": None, "Title": "Hard-CAD revision cohort"})
    plt.close(fig)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    clean = "\n".join(line.rstrip() for line in buf.getvalue().splitlines())
    OUT.write_text(clean + "\n", encoding="utf-8", newline="\n")
    print(f"[rendered] {OUT}")


if __name__ == "__main__":
    main()
