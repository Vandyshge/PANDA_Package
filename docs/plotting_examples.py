"""Generate six figures with the public PANDA plotting API."""

# %% Setup
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from panda_md import (
    FitSpec, SlitPore, density_map, density_profile, fit_blocks,
    stability_diagram, synthetic_trajectory,
)
from panda_md.analysis.accuracy import AccuracyCase, accuracy_study
from panda_md.plotting import (
    plot_accuracy, plot_blocks, plot_density_map, plot_fit, plot_profile, plot_stability,
)

output = Path(__file__).resolve().parent
plt.style.use(output / "scientific.mplstyle")
mpl.rcParams["image.cmap"] = "Greens"
mpl.rcParams["axes.prop_cycle"] = mpl.cycler(color=["#276647", "#a45d2b", "#465b73"])


def panel():
    return plt.subplots(figsize=(5.3, 3.4), layout="constrained")


def save(fig, name):
    fig.savefig(output / f"plot-example-{name}.png", dpi=180)
    plt.close(fig)


pore = SlitPore(width_nm=4, length_nm=8, base_aspect_ratio=0.5)
roll = pore.interface("roll")
truth = {"theta": 120.0, "delta": 0.03, "phi": 0.4}
bulk = 30.0
trajectory = synthetic_trajectory(
    roll, truth, density_bulk_per_nm3=bulk, frame_count=201,
    time_step_ps=50, seed=5,
)
measured_pore = SlitPore.from_trajectory(trajectory, walls="walls", liquid="liquid")
roll = measured_pore.interface("roll")
profiles = density_profile(trajectory, measured_pore, "liquid", bins=64, block="1 ns")
production = density_profile(
    trajectory, measured_pore, "liquid", bins=64, start="2 ns", stop="10 ns", block="1 ns",
)

# %% Profile
fig, ax = panel()
plot_profile(production, ax=ax)
save(fig, "profile")

# %% Fit
result = roll.fit(production.mean(), density_bulk_per_nm3=bulk)
fig, ax = panel()
plot_fit(result, ax=ax)
save(fig, "fit")

# %% Blocks
blocks = fit_blocks(roll, profiles, FitSpec(density_bulk_per_nm3=bulk))
fig, ax = panel()
plot_blocks(blocks, ax=ax)
ax.axvspan(2, 10, color="#e7f0df", zorder=0, label="Profile averaging: 2–10 ns")
ax.set(xlim=(0, 10), ylabel="θ (°)")
ax.legend()
save(fig, "blocks")

# %% Density map
density = density_map(
    trajectory, measured_pore, "liquid", shape="roll", bins=(64, 36), start="2 ns", stop="10 ns",
)
fig, ax = panel()
plot_density_map(density, ax=ax)
save(fig, "density-map")

# %% Stability
diagram = stability_diagram(
    pore, contact_angle_deg=150, wall_layer=0.02,
    volume_fractions=np.linspace(0.01, 0.99, 100),
    length_ratios=np.linspace(0.5, 4, 90),
)
fig, ax = panel()
plot_stability(diagram, ax=ax)
ax.set_title("")
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles, labels, loc="upper left", bbox_to_anchor=(1, 1))
save(fig, "stability")

# %% Accuracy
cases = {
    f"{noise:g}": (noise, AccuracyCase(truth=truth, noise_std=noise / 100))
    for noise in (0.5, 1, 2, 4)
}
study = accuracy_study(roll, "Noise amplitude (% of bulk density)", cases,
                       density_bulk_per_nm3=bulk, seeds=range(8))
fig, ax = panel()
plot_accuracy(study, ax=ax)
ax.set_title("")
save(fig, "accuracy")
