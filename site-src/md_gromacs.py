"""Run the GROMACS-format example from the extracted example directory."""

from panda_md import load_trajectory

from md_workflow import analyze


traj = load_trajectory("slit.gro", "slit.xtc")
analyze(
    traj,
    walls="resname WALL",
    liquid="resname LIQ and name O",
    rho_bulk=3.0,
    average_from="2 ns",
    average_to="10 ns",
    block="0.5 ns",
    prefix="gromacs",
)
