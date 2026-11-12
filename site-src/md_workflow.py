"""Analyze a slit-pore roll from a GROMACS or LAMMPS trajectory."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

from panda_md import SlitPore, density_map, density_profile, fit_blocks
from panda_md.core.timing import to_picoseconds


STYLE = Path(__file__).with_name("scientific.mplstyle")
GREEN = "#276647"
MAP_COLORS = LinearSegmentedColormap.from_list(
    "pore_density", ["#fcfdfb", "#e6f0e2", "#a5c8a8", "#589467", "#245a3a"]
)


def plot_diagnostics(density, result, width, rho_bulk, times, window, midpoint, angles, included, target):
    with plt.style.context(STYLE):
        fig = plt.figure(figsize=(6.4, 8.4))
        map_ax = fig.add_axes([0.14, 0.61, 0.80, 0.80 * 6.4 * 0.55 / 8.4])
        profile_ax = fig.add_axes([0.14, 0.35, 0.80, 0.185])
        block_ax = fig.add_axes([0.14, 0.09, 0.80, 0.185])
        for index, ax in enumerate((map_ax, profile_ax, block_ax)):
            ax.text(0, 1.025, f"({chr(97 + index)})", transform=ax.transAxes, va="bottom")

        mesh = map_ax.pcolormesh(
            density.length_edges_nm / width, density.height_edges_nm / width,
            density.density_per_nm3.T / rho_bulk, shading="flat", cmap=MAP_COLORS, vmin=0,
        )
        for lower, upper in ((-0.55, -0.5), (0.5, 0.55)):
            map_ax.axhspan(lower, upper, color="#d6d9d4", linewidth=0)
        map_ax.set(xlim=(-1, 1), ylim=(-0.55, 0.55), xlabel="$x/H$", ylabel="$z/H$",
                   xticks=np.linspace(-1, 1, 5), yticks=(-0.5, 0, 0.5))
        map_ax.set_aspect("equal")
        color_ax = map_ax.inset_axes([0.06, 0.20, 0.022, 0.55])
        colorbar = fig.colorbar(mesh, cax=color_ax, ticks=(0, 0.5, 1))
        colorbar.ax.tick_params(labelsize=8, length=2)
        colorbar.ax.text(-0.25, 1.06, r"$\rho/\rho_\mathrm{bulk}$",
                         transform=colorbar.ax.transAxes, fontsize=8)

        profile_ax.axvline(0, color="#b9c2b8", linestyle=":", linewidth=0.8)
        profile_ax.plot(result.coordinate, result.data, "o", ms=3, mfc="white",
                        mec="#5f766a", mew=0.8, label="Sampled profile")
        profile_ax.plot(result.coordinate, result.model_curve, color=GREEN, label="PANDA fit")
        profile_ax.set(xlim=(-0.5, 0.5), xlabel="$z/H$", ylabel=r"$\rho/\rho_\mathrm{bulk}$",
                       xticks=np.linspace(-0.5, 0.5, 5))
        profile_ax.legend(loc="lower center", ncol=2)

        start, end = window / 1000
        midpoint_ns = midpoint / 1000
        block_ax.axvspan(start, end, color="#e7f0df", label=f"Average: {start:g}–{end:g} ns")
        block_ax.axvline(start, color=GREEN, linestyle=":", linewidth=1)
        block_ax.plot(midpoint_ns, angles, color="#a4aca5", linewidth=0.9)
        block_ax.plot(midpoint_ns[~included], angles[~included], "o", ms=4, mfc="white", mec="#687870")
        block_ax.plot(midpoint_ns[included], angles[included], "o", ms=4, color=GREEN)
        block_ax.axhline(result.values["theta"], color="#a45d2b", linestyle="--",
                         linewidth=1.1, label="Fit of averaged profile")
        block_ax.set(xlim=np.asarray(times) / 1000, xlabel="Time (ns)", ylabel=r"$\theta$ (deg)")
        block_ax.margins(y=0.22)
        block_ax.legend(loc="upper right", ncol=2)
        fig.savefig(target, dpi=200)
        plt.close(fig)


def analyze(traj, *, walls, liquid, rho_bulk, average_from, average_to, block, prefix):
    prefix = Path(prefix)
    times = traj.times_ps()
    first_ps, last_ps = float(times[0]), float(times[-1])
    average_start = to_picoseconds(average_from)
    average_end = to_picoseconds(average_to)
    if not first_ps <= average_start < average_end <= last_ps:
        raise ValueError("The averaging window must lie within the trajectory.")
    pore = SlitPore.from_trajectory(traj, walls=walls, liquid=liquid, time=average_from)
    profiles = density_profile(
        traj, pore, liquid, start=first_ps, block=block,
        bins=80, centering="pore",
    )
    average_profile = density_profile(
        traj, pore, liquid, start=average_from, stop=average_to,
        bins=80, centering="pore",
    ).mean()
    roll = pore.interface("roll")
    result = roll.fit(average_profile, density_bulk_per_nm3=rho_bulk)
    blocks = fit_blocks(roll, profiles, result.spec)
    midpoint = (blocks.block_start_ps + blocks.block_stop_ps) / 2
    angles = blocks.values("theta")
    included = (blocks.block_start_ps >= average_start) & (blocks.block_stop_ps <= average_end)

    print(f"Pore width = {pore.width_nm:.3f} nm")
    print(f"Trajectory = {first_ps:g} to {last_ps:g} ps")
    print(f"Averaging window = {average_start:g} to {average_end:g} ps")
    print(f"Blocks plotted = {len(angles)}")
    print(f"Full blocks inside averaging window = {np.count_nonzero(included)}")
    print(f"Mean-profile theta = {result.values['theta']:.2f} deg")
    if np.count_nonzero(included) >= 2:
        print(f"Block SD inside window = {np.std(angles[included], ddof=1):.2f} deg")
    print(f"Fit flags = {result.problems()}")

    profiles.save(prefix.with_name(prefix.name + "-blocks.npz"))
    average_profile.save(prefix.with_name(prefix.name + "-average.npz"))
    density = density_map(
        traj, pore, liquid, shape="roll", start=average_from, stop=average_to, bins=(65, 40),
    )
    plot_diagnostics(
        density, result, pore.width_nm, rho_bulk, (first_ps, last_ps),
        np.array([average_start, average_end]), midpoint, angles, included,
        prefix.with_name(prefix.name + "-diagnostics.png"),
    )
