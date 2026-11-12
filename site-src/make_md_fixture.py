"""Create equivalent synthetic slit-pore trajectories in GROMACS and LAMMPS formats."""

import argparse
from pathlib import Path

import MDAnalysis as mda
import numpy as np

from panda_md import SlitPore


def make_fixture(folder):
    folder.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(2026)
    pore = SlitPore(width_nm=8, length_nm=16)
    roll = pore.interface("roll")
    truth = {"theta": 120.0, "delta": 0.03, "phi": 0.40}
    box = np.array([16.0, 16.0, 14.0])
    reference_density = 3.0
    fluid_count = round(reference_density * pore.volume_nm3() * truth["phi"])

    xy = np.array([(x, y) for x in (2, 6, 10, 14) for y in (2, 6, 10, 14)])
    walls = np.vstack([np.column_stack((xy, np.full(len(xy), z))) for z in (3.0, 11.0)])
    count = len(walls) + fluid_count
    atom_types = np.repeat([1, 2], [len(walls), fluid_count])
    atom_ids = np.arange(1, count + 1)
    universe = mda.Universe.empty(count, n_residues=2, atom_resindex=atom_types - 1, trajectory=True)
    universe.add_TopologyAttr("names", np.where(atom_types == 1, "C", "O"))
    universe.add_TopologyAttr("resnames", ["WALL", "LIQ"])
    universe.add_TopologyAttr("resids", [1, 2])
    universe.dimensions = [*box * 10, 90, 90, 90]
    box_lines = "".join(f"0.0 {value * 10:g}\n" for value in box)
    bounds = "".join(f"0.0 {value * 10:g} {axis}lo {axis}hi\n" for value, axis in zip(box, "xyz"))

    with mda.Writer(str(folder / "slit.xtc"), n_atoms=count, precision=5) as writer, \
            (folder / "slit.lammpstrj").open("w", encoding="ascii", newline="\n") as dump:
        for frame in range(201):
            trial = rng.uniform([0, 0, 3], [16, 16, 11], (3 * fluid_count, 3))
            half_width = 8 * roll.profile((trial[:, 2] - 7) / 8, **truth)
            liquid = trial[abs(trial[:, 0] - 8) < half_width][:fluid_count]
            if len(liquid) != fluid_count:
                raise RuntimeError("Insufficient accepted particles")
            positions_angstrom = np.vstack((walls, liquid)) * 10
            universe.atoms.positions = positions_angstrom
            universe.trajectory.ts.frame = frame
            universe.trajectory.ts.time = frame * 50
            writer.write(universe.atoms)
            records = np.column_stack((atom_ids, atom_types, positions_angstrom))
            if frame == 0:
                universe.atoms.write(str(folder / "slit.gro"))
                with (folder / "slit.data").open("w", encoding="ascii", newline="\n") as data:
                    data.write(f"Synthetic slit pore\n\n{count} atoms\n2 atom types\n\n{bounds}")
                    data.write("\nMasses\n\n1 12.011\n2 15.999\n\nAtoms # atomic\n\n")
                    np.savetxt(data, records, fmt="%d %d %.5f %.5f %.5f")
            dump.write(f"ITEM: TIMESTEP\n{frame * 25000}\nITEM: NUMBER OF ATOMS\n{count}\n")
            dump.write(f"ITEM: BOX BOUNDS pp pp pp\n{box_lines}ITEM: ATOMS id type x y z\n")
            np.savetxt(dump, records, fmt="%d %d %.5f %.5f %.5f")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    make_fixture(parser.parse_args().output)
