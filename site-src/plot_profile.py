"""Render the profile, block, and validation figures used by the documentation."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

root = Path(__file__).resolve().parent
plt.style.use(root / "scientific.mplstyle")
profile = np.genfromtxt(root / "roll-profile.csv", delimiter=",", names=True)
ink, border = "#35413a", "#8f9b92"
green, marker, rust = "#276647", "#5f766a", "#a65d23"
fig, ax = plt.subplots(figsize=(4.6, 3.05), dpi=200)
fig.subplots_adjust(left=0.19, right=0.96, top=0.84, bottom=0.21)
ax.set_facecolor("none")
for spine in ax.spines.values():
    spine.set_color(border)
ax.tick_params(colors=ink, direction="in")
ax.set(xlim=(-0.52, 0.52), ylim=(-0.02, 0.60), xticks=[-0.5, -0.25, 0, 0.25, 0.5])
ax.set_xlabel("Reduced coordinate, z/H", color=ink)
ax.set_ylabel(r"$\rho / \rho_\mathrm{bulk}$", color=ink)
ax.plot(profile["z_over_H"], profile["fit_over_bulk"], color=green,
        label="Analytical fit")
ax.plot(profile["z_over_H"], profile["rho_over_bulk"], "o", mfc="white", mec=marker,
        mew=0.7, ms=2.8,
        label="Synthetic profile")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.20), ncol=2,
          frameon=False, labelcolor=ink, fontsize=9)
fig.savefig(root / "profile-light.png", transparent=True)
plt.close(fig)


def fit_panel(ax, data, coordinate, angle, legend_location):
    x = data[coordinate]
    ax.plot(x, data["rho_over_bulk"], "o", mfc="white", mec=marker, mew=0.7, ms=3.2,
            label="Synthetic profile")
    ax.plot(x, data["fit_over_bulk"], color=green,
            label=f"Fit, θ = {angle:.2f}°")
    ax.set_ylabel(r"$\rho / \rho_\mathrm{bulk}$")
    ax.legend(frameon=False, loc=legend_location)


roll_fig, (fit_ax, residual_ax) = plt.subplots(
    2, 1, sharex=True, height_ratios=(2, 1), figsize=(6.5, 4.8), layout="constrained"
)
fit_panel(fit_ax, profile, "z_over_H", 120.61, "lower center")
residual_ax.axhline(0, color="#697278", linewidth=0.8)
residual_ax.plot(profile["z_over_H"], profile["rho_over_bulk"] - profile["fit_over_bulk"],
                 ".", color=marker, ms=3.3)
residual_ax.set(xlim=(-0.5, 0.5), xlabel="$z/H$", ylabel="Data − fit")
roll_fig.savefig(root / "roll-fit-residuals.png", dpi=180)
plt.close(roll_fig)

triangle = np.genfromtxt(root / "triangle-profile.csv", delimiter=",", names=True)
triangle_fig, triangle_ax = plt.subplots(figsize=(6.5, 3.6), layout="constrained")
fit_panel(triangle_ax, triangle, "z_over_a", 149.83, "upper right")
triangle_ax.set_xlabel("$z/a$")
triangle_fig.savefig(root / "triangle-fit.png", dpi=180)
plt.close(triangle_fig)

blocks = np.genfromtxt(root / "synthetic-block-angles.csv", delimiter=",", names=True)
block_fig, block_ax = plt.subplots(figsize=(6.5, 3.3), layout="constrained")
block_ax.plot(blocks["block"], blocks["theta_deg"], "o", color=green,
              lw=1.4, ms=5, label="Individual block fits")
block_ax.axhline(120, color=rust, linestyle="--", lw=1.2, label="Input angle")
block_ax.set(xlabel="Synthetic block", ylabel="Contact angle (deg)", xticks=blocks["block"],
             ylim=(119.45, 120.65))
block_ax.grid(axis="y", alpha=0.22)
block_ax.legend(frameon=False, loc="upper left", ncol=2, fontsize=9)
block_ax.tick_params(direction="in")
block_fig.savefig(root / "synthetic-block-angles.png", dpi=180)
plt.close(block_fig)

noise = np.genfromtxt(root / "validation-roll-noise.csv", delimiter=",", names=True)
angles = np.genfromtxt(root / "validation-roll-angle.csv", delimiter=",", names=True)
validation_fig, axes = plt.subplots(1, 2, figsize=(7, 3.5), sharey=True, layout="constrained")
for ax, data, xkey, panel, xlabel in (
    (axes[0], noise, "noise_percent", "(a)", r"Noise (% of $\rho_\mathrm{bulk}$)"),
    (axes[1], angles, "input_theta_deg", "(b)", "Input angle (deg)"),
):
    ax.plot(data[xkey], data["mae_deg"], "o-", color=green, ms=4, lw=1.4,
            label="Mean absolute error")
    ax.plot(data[xkey], data["max_abs_deg"], "s--", color=rust, ms=4, lw=1.4,
            label="Maximum absolute error")
    ax.set_title(panel, loc="left", pad=6)
    ax.set(xlabel=xlabel, ylim=(0, 3.15))
    ax.grid(axis="y", alpha=0.22)
    ax.tick_params(direction="in")
axes[0].set_ylabel("Absolute angle error (deg)")
axes[0].legend(loc="upper left", frameon=False, fontsize=8)
validation_fig.savefig(root / "roll-validation.png", dpi=180)
plt.close(validation_fig)
