"""Run the LAMMPS-format example from the extracted example directory."""

from panda_md import load_trajectory

from md_workflow import analyze


traj = load_trajectory(
    "slit.data", "slit.lammpstrj",
    atom_style="id type x y z",
    dt=0.002,  # ps per integration step; dump interval is 25000 steps
)
analyze(
    traj,
    walls="type 1",
    liquid="type 2",
    rho_bulk=3.0,
    average_from="2 ns",
    average_to="10 ns",
    block="0.5 ns",
    prefix="lammps",
)
