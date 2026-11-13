"""Draw dimensioned cross-section schematics for the pore guide."""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle

ROOT = Path(__file__).resolve().parent
EDGE = "#32664b"
FILL = "#e8f1e9"


def dimension(ax, start, end, label, at):
    ax.annotate("", end, start, arrowprops={"arrowstyle": "<->", "color": EDGE, "lw": 1})
    ax.text(*at, label, color=EDGE, ha="center", va="center")


def draw(name):
    fig = plt.figure(figsize=(3.6, 2.3), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1], xlim=(-1.8, 1.8), ylim=(-1.15, 1.15), aspect="equal")
    ax.axis("off")
    style = {"facecolor": FILL, "edgecolor": EDGE, "linewidth": 1.6}
    if name == "slit":
        ax.add_patch(Rectangle((-1.24, -0.47), 2.48, 0.94, color=FILL))
        for y in (-0.47, 0.47):
            ax.plot([-1.24, 1.24], [y, y], color=EDGE, linewidth=1.6)
        dimension(ax, (0, -0.46), (0, 0.46), r"$H$", (0.18, 0))
    elif name in {"triangle", "square"}:
        if name == "triangle":
            ax.add_patch(Polygon([(-0.84, -0.36), (0.84, -0.36), (0, 1.095)],
                                 **style))
            y = -0.36
        else:
            ax.add_patch(Rectangle((-0.70, -0.52), 1.40, 1.40, **style))
            y = -0.52
        half = 0.84 if name == "triangle" else 0.70
        for x in (-half, half):
            ax.plot([x, x], [y, -0.83], color=EDGE, linewidth=0.75)
        dimension(ax, (-half, -0.78), (half, -0.78), r"$a$", (0, -0.98))
    else:
        ax.add_patch(Circle((0, 0), 0.79, **style))
        dimension(ax, (-0.79, 0), (0.79, 0), r"$D$", (0, 0.21))
    fig.savefig(ROOT / f"pore-{name}.png", dpi=100)
    plt.close(fig)


if __name__ == "__main__":
    with plt.style.context(ROOT / "scientific.mplstyle"):
        for name in ("slit", "triangle", "square", "cylinder"):
            draw(name)
