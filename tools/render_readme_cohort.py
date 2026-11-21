"""Redraw the published cohort scatter for the GitHub README.

Run with matplotlib installed: python tools/render_readme_cohort.py
Only the plotted aggregates from the article are included.
https://doi.org/10.1016/j.cag.2026.104824
"""

from io import StringIO
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.ticker import FixedLocator, FuncFormatter


OUT = Path(__file__).resolve().parents[1] / "assets" / "readme" / "cohort.svg"
BACKGROUND = "#111F29"
PANEL = "#182D39"
BORDER = "#31505F"
TEXT = "#F1FAFA"
SECONDARY = "#BDCFD7"
MINT = "#84DDC3"
PEACH = "#F7AE86"
PURPLE = "#D6B3F6"
ORIGIN = (0.0, 0.0)
# Change in IoU and change in extra material (mm³), revised minus initial.
POINTS = {
    "cad06": (0.5195861049519583, 596.9026041820603),
    "cad15": (0.0001261056538965355, -28.27433388231293),
    "cad30": (0.03042817358163505, 1987.300888156923),
}


def card(fig, x, y, width, height):
    patch = FancyBboxPatch(
        (x, y), width, height, transform=fig.transFigure, zorder=-1,
        boxstyle="round,pad=0,rounding_size=0.014",
        facecolor=PANEL, edgecolor=BORDER, linewidth=0.8,
    )
    fig.add_artist(patch)


def style(ax, xticks, yticks):
    ax.set_facecolor(PANEL)
    ax.xaxis.set_major_locator(FixedLocator(xticks))
    ax.yaxis.set_major_locator(FixedLocator(yticks))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}".replace("-", "−")))
    ax.tick_params(colors=SECONDARY, labelsize=11.5, length=0, pad=8)
    for side, spine in ax.spines.items():
        spine.set_visible(side in ("left", "bottom"))
        spine.set_color(BORDER)
    ax.grid(alpha=0.8, linewidth=0.7, color=BORDER)
    ax.set_axisbelow(True)
    ax.axhline(0, color="#7B9BA9", linewidth=0.85, alpha=0.85)
    ax.axvline(0, color="#7B9BA9", linewidth=0.85, alpha=0.85)
    ax.set_ylabel("Δ extra material (mm³)", fontsize=11.5, color=SECONDARY, labelpad=8)


def point(ax, coordinates, color, shape, size=78):
    ax.scatter(
        *coordinates, marker=shape, s=size, facecolor=color, edgecolor=BACKGROUND,
        linewidth=1.1, zorder=4,
    )


def label(ax, text, coordinates, offset, color=SECONDARY, *, align="left"):
    ax.annotate(
        text, coordinates, xytext=offset, textcoords="offset points",
        ha=align, va="center", color=color, fontsize=11.5, zorder=5,
        arrowprops={"arrowstyle": "-", "color": color, "alpha": 0.7,
                    "linewidth": 0.8, "shrinkA": 4, "shrinkB": 7},
    )


def render():
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "svg.fonttype": "path",
        "svg.hashsalt": "hardcad-cohort-readme",
    })
    fig = plt.figure(figsize=(12.8, 5.35), facecolor=BACKGROUND)
    fig.text(0.034, 0.905, "What changed after feedback?", color=TEXT,
             fontsize=24, fontweight="bold")
    fig.text(0.035, 0.838, "Each coordinate compares the revised geometry with its initial version.",
             color=SECONDARY, fontsize=12)
    fig.text(0.964, 0.905, "41 paired revisions", ha="right", color=MINT,
             fontsize=12, fontweight="bold")

    card(fig, 0.034, 0.075, 0.534, 0.692)
    card(fig, 0.584, 0.075, 0.382, 0.692)
    fig.text(0.057, 0.699, "All eligible pairs", color=TEXT, fontsize=15, fontweight="bold")
    fig.text(0.606, 0.699, "Origin detail", color=TEXT, fontsize=15, fontweight="bold")

    full = fig.add_axes((0.107, 0.212, 0.429, 0.420))
    style(full, (0, 0.2, 0.4, 0.6), (0, 1000, 2000))
    full.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:g}"))
    full.set(xlim=(-0.04, 0.63), ylim=(-360, 2290))
    full.set_xlabel("Δ IoU", fontsize=12, color=SECONDARY, labelpad=8)
    point(full, ORIGIN, MINT, "o", 108)
    point(full, POINTS["cad15"], PURPLE, "s", 35)
    for case, offset, align in (("cad30", (39, 6), "left"), ("cad06", (-27, 22), "right")):
        point(full, POINTS[case], PEACH, "D")
        label(full, case, POINTS[case], offset, PEACH, align=align)
    label(full, "38 pairs at the origin", ORIGIN, (30, 23), MINT)

    detail = fig.add_axes((0.652, 0.212, 0.278, 0.420))
    style(detail, (0, 0.0001, 0.0002), (-40, -20, 0))
    detail.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x * 1e4:g}"))
    detail.set(xlim=(-0.000016, 0.000225), ylim=(-45, 7))
    detail.set_xlabel("Δ IoU (×10⁻⁴)", fontsize=12, color=SECONDARY, labelpad=8)
    point(detail, ORIGIN, MINT, "o", 108)
    point(detail, POINTS["cad15"], PURPLE, "s", 92)
    label(detail, "38 pairs", ORIGIN, (28, -17), MINT)
    label(detail, "cad15\n−28.27 mm³", POINTS["cad15"], (30, 12), PURPLE)

    svg = StringIO()
    fig.savefig(svg, format="svg", metadata={
        "Date": None,
        "Title": "Hard-CAD revision cohort",
        "Description": "41 pairs with 38 at the origin and three changed pairs.",
    })
    plt.close(fig)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    clean_svg = "\n".join(line.rstrip() for line in svg.getvalue().splitlines())
    OUT.write_text(clean_svg + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    render()
