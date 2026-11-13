"""Build the PANDA documentation from the page definitions and public-facing example data."""

import argparse
import builtins
import csv
import io
import json
import keyword
import re
import shutil
import tokenize
from hashlib import sha256
from html import escape
from pathlib import Path

from api_reference import reference_pages

ROOT = Path(__file__).resolve().parent
PACKAGE = "https://github.com/Ilya-Garanov-WorkingAcc/PANDA_2.0"
THEME_VERSION = sha256((ROOT / "panda-theme.css").read_bytes()).hexdigest()[:10]
DYNAMIC = "https://vandyshge.github.io/PANDA_Dynamic/"
POLYGON = "https://vandyshge.github.io/PANDA_Polygon/"
PAGES = []
SUBPAGES = {
    "geometries": ("shape-gallery", "triangle-example"),
    "trajectories": ("trajectory-gromacs", "trajectory-lammps", "trajectory-averaging", "block-example"),
    "fitting": ("validation",),
}


def highlight_python(source):
    offsets = [0]
    for line in source.splitlines(keepends=True):
        offsets.append(offsets[-1] + len(line))
    parts = []
    cursor = 0
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        style = {
            "COMMENT": "comment",
            "STRING": "string",
            "FSTRING_START": "string",
            "FSTRING_MIDDLE": "string",
            "FSTRING_END": "string",
            "NUMBER": "number",
        }.get(tokenize.tok_name[token.type])
        if token.type == tokenize.NAME:
            if keyword.iskeyword(token.string):
                style = "keyword"
            elif token.string in vars(builtins):
                style = "builtin"
        if style:
            start = offsets[token.start[0] - 1] + token.start[1]
            end = offsets[token.end[0] - 1] + token.end[1]
            parts.append(escape(source[cursor:start]))
            parts.append(f'<span class="syntax-{style}">{escape(source[start:end])}</span>')
            cursor = end
    parts.append(escape(source[cursor:]))
    return "".join(parts)


def code(source, language="shell"):
    source = source.strip()
    content = highlight_python(source) if language == "python" else escape(source)
    label = {"python": "Python", "shell": "Shell", "toml": "TOML", "bibtex": "BibTeX"}[language]
    return f'<div class="code"><div class="cell-label">{label}</div><pre><code class="language-{language}">{content}</code></pre></div>'


def output(source):
    return f'<div class="cell-output"><div class="cell-label">Output</div><pre><code>{escape(source.strip())}</code></pre></div>'


def figure(path, alt, caption):
    version = sha256((ROOT / path).read_bytes()).hexdigest()[:10]
    return f'<figure class="cell-figure"><img src="{path}?v={version}" alt="{alt}"><figcaption>{caption}</figcaption></figure>'


def md_example(engine):
    source = (ROOT / f"md_{engine}.py").read_text(encoding="utf-8").partition("\n\n")[2]
    stdout = (ROOT / f"md-{engine}-output.txt").read_text(encoding="utf-8-sig")
    return code(source, "python") + output(stdout)


def section(title, body):
    anchor = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return f'<section><h2 id="{anchor}">{title}</h2>{body}</section>'


def page(group, slug, title, lead, body):
    PAGES.append((group, slug, title, lead, body))


QUICKSTART = """from panda_md import SlitPore, synthetic_profile

pore = SlitPore(width_nm=8.0, length_nm=16.0)
roll = pore.interface("roll")
truth = {"theta": 120.0, "delta": 0.03, "phi": 0.40}
profile = synthetic_profile(
    roll, truth, density_bulk_per_nm3=30.0,
    noise_std=0.005, seed=0,
)
result = roll.fit(
    profile, optimize=["theta", "delta"], density_bulk_per_nm3=30.0,
)
print(f"theta = {result.values['theta']:.2f} deg")
print(f"delta/H = {result.values['delta']:.4f}")
print(f"phi = {result.values['phi']:.4f}")
print(f"L1 loss = {result.loss:.5f}")
print(result.problems())"""

ROLL_OUTPUT = """theta = 120.61 deg
delta/H = 0.0301
phi = 0.4002
L1 loss = 0.00377
()"""

ROLL_PLOT = """import matplotlib.pyplot as plt
from panda_md.plotting import plot_fit

fig, (fit_ax, residual_ax) = plt.subplots(
    2, 1, sharex=True, height_ratios=(2, 1), layout="constrained"
)
plot_fit(result, ax=fit_ax)
fit_ax.set_xlabel("")
residual_ax.axhline(0, color="0.5", linewidth=1)
residual_ax.plot(result.coordinate, result.data - result.model_curve, ".", markersize=3)
residual_ax.set(xlabel="Reduced coordinate, z/H", ylabel="Data − fit")
fig.savefig("roll-fit.png", dpi=150)
plt.show()"""

TRIANGLE_EXAMPLE = """from panda_md import TrianglePore, synthetic_profile

pore = TrianglePore(side_nm=6, length_nm=12, layer_width_nm=6)
filament = pore.interface("filament_w3c0")
truth = {"theta": 150.0, "delta": 0.02, "phi": 0.5}
profile = synthetic_profile(
    filament, truth, density_bulk_per_nm3=30, noise_std=0.005, seed=0
)
result = filament.fit(profile, density_bulk_per_nm3=30)
print(f"Input theta = {truth['theta']:.2f} deg")
print(f"Fit theta = {result.values['theta']:.2f} deg")
print(f"Flags: {result.problems()}")"""

TRIANGLE_OUTPUT = """Input theta = 150.00 deg
Fit theta = 149.83 deg
Flags: ()"""

SAVED_FIT = """from panda_md import DensityProfile, SlitPore

profile = DensityProfile.load("density.csv")
pore = SlitPore(width_nm=8.0, length_nm=16.0)
result = pore.interface("roll").fit(
    profile, optimize=["theta", "delta"], density_bulk_per_nm3=30.0,
)
print(result.summary())
print(result.problems())"""

SAVED_OUTPUT = """slit/roll  regime: non_wetting  loss: 0.003774
   theta = 120.614  (free)
   delta = 0.0300547  (free)
     phi = 0.40016  (fixed)
   shift = 0  (fixed)
()"""

BLOCK_EXAMPLE = """from panda_md import ProfileSet, SlitPore, fit_blocks

profiles = ProfileSet.load("synthetic-roll-blocks.npz")
pore = SlitPore(width_nm=8.0, length_nm=16.0)
roll = pore.interface("roll")
result = roll.fit(profiles.mean(), density_bulk_per_nm3=30.0)
blocks = fit_blocks(roll, profiles, result.spec)
print(result.summary())
print(f"Block SD = {blocks.std('theta'):.3f} deg")
print(f"Block mean = {blocks.mean('theta'):.3f} deg")"""

BLOCK_OUTPUT = """slit/roll  regime: non_wetting  loss: 0.0008747
   theta = 119.985  (free)
   delta = 0.0301568  (free)
     phi = 0.400031  (fixed)
   shift = 0  (fixed)
Block SD = 0.273 deg
Block mean = 119.992 deg"""

TRIANGLE_PLOT = """import matplotlib.pyplot as plt
from panda_md.plotting import plot_fit

ax = plot_fit(result)
ax.set_xlabel("Reduced coordinate, z/a")
ax.figure.savefig("triangle-fit.png", dpi=150)
plt.show()"""

LANDING_PLOT_VERSION = sha256((ROOT / "profile-light.png").read_bytes()).hexdigest()[:10]
page("Start here", "index", "Overview", "", f"""
<div class="hero">
  <div><p class="eyebrow">Python library for molecular simulation</p>
  <h1>From density to contact angle</h1>
  <p>PANDA fits analytical models to one-dimensional density profiles of confined liquids. Estimate a contact angle, identify plausible interface shapes, and compare results across trajectory blocks.</p>
  <a class="button" href="quickstart.html">Run the quick start →</a></div>
  <figure><img src="profile-light.png?v={LANDING_PLOT_VERSION}" alt="A synthetic slit-pore roll profile and its analytical fit nearly overlap at 120.61 degrees" width="920" height="610">
  <figcaption>Synthetic slit-pore roll · fitted θ = 120.61°</figcaption></figure>
</div>
""" + section("Start with your data", """
<div class="cards">
<a class="card" href="quickstart.html"><h3>Try a synthetic profile →</h3><p>Recover a known angle in a slit pore in a few lines of Python.</p></a>
<a class="card" href="trajectories.html"><h3>Analyze a trajectory →</h3><p>Load simulation frames, compute density, and fit blocks.</p></a>
<a class="card" href="cli.html"><h3>Use the command line →</h3><p>Run the same workflow with shell commands or a TOML file.</p></a>
</div>""") + section("What PANDA supports", f"""
<p>The name stands for Predicting Angle from Nanoscale Density Analysis. The library covers slit, triangular, square, and cylindrical pores. The <a href="geometries.html">shape catalog</a> identifies which models can fit density and which supply surface terms for stability diagrams.</p>
<p>Explore the related <a href="{POLYGON}">PANDA Polygon</a> geometry models and the <a href="{DYNAMIC}">PANDA Dynamic</a> two-angle method.</p>"""))

CREATE_ENV = code("cd PANDA_2.0\npython -m venv .venv")
page("Start here", "installation", "Installation",
     "The package is named panda-md, the Python module is panda_md, and the shell command is panda.",
     section("Install from source", f"""
<p>Use Python 3.10 or newer. This manual targets the developer repository’s 0.1.0 alpha API. The source checkout requires repository access.</p>
{code(f'git clone {PACKAGE}.git')}
{CREATE_ENV}
<p>Activate the environment with <code>source .venv/bin/activate</code> on macOS or Linux, or <code>.venv\\Scripts\\Activate.ps1</code> in PowerShell.</p>
{code('python -m pip install .')}
""") + section("Optional dependencies", """
<p>From the same checkout, install the <code>md</code> extra for trajectory input and <code>plot</code> for Matplotlib figures.</p>
""" + code('python -m pip install ".[md,plot]"')) + section("Check the installation",
    code('import panda_md\n\nprint("PANDA import OK")', "python") +
    output("PANDA import OK") +
    '<p>Run <code>panda --help</code> in a shell to list the available commands.</p>'))

page("Start here", "quickstart", "Quick start",
     "Generate a noisy slit-pore roll profile with a known angle, then fit it with PANDA.",
     section("Generate and fit a profile", """
<p>The slit is 8 nm wide. The synthetic model uses θ = 120°, a layer thickness of 0.03 times the slit width, and a liquid volume fraction of 0.40.</p>
""" + code(QUICKSTART, "python") + output(ROLL_OUTPUT)) + section("Read the result", """
<p>These values come from the archived run for this example. PANDA optimizes θ and δ. It derives φ from the profile using the supplied bulk density. The last line is the list of fit flags.</p>
<p><a href="quickstart.py" download>Download the Python example</a> · <a href="roll-profile.csv" download>Download the normalized profile and fit</a></p>
""") + section("Plot the fit and residuals", """
<p>With the <code>plot</code> extra installed, run this cell after fitting. The residual is the observed normalized density minus the fitted curve at each bin.</p>
""" + code(ROLL_PLOT, "python") + figure(
    "roll-fit-residuals.png",
    "Analytical fit and synthetic slit-pore density above the signed residuals at each bin",
    'Plot from the archived synthetic roll fit. <a href="roll-fit-residuals.png" download>Download PNG</a>.'
)) + section("Use your own data", """
<p>Follow the <a href="trajectories.html">trajectory guide</a> for simulation output. If you already have a density profile, see <a href="fitting.html#fit-a-saved-profile">fitting a saved profile</a>.</p>"""))

page("User guide", "geometries", "Pores and shapes",
     "A pore defines the confinement geometry. A named shape defines the analytical interface inside it.",
     section("Set up a pore", """
<div class="pore-grid">
<figure><img src="pore-slit.png" width="360" height="230" alt="Two parallel walls separated by H"><figcaption><strong>Slit</strong><code>SlitPore</code><span>Wall-to-wall width <i>H</i></span></figcaption></figure>
<figure><img src="pore-triangle.png" width="360" height="230" alt="Equilateral triangular cross-section with side a"><figcaption><strong>Triangle</strong><code>TrianglePore</code><span>Side length <i>a</i></span></figcaption></figure>
<figure><img src="pore-square.png" width="360" height="230" alt="Square cross-section with side a"><figcaption><strong>Square</strong><code>SquarePore</code><span>Side length <i>a</i></span></figcaption></figure>
<figure><img src="pore-cylinder.png" width="360" height="230" alt="Circular cross-section with diameter D"><figcaption><strong>Cylinder</strong><code>CylinderPore</code><span>Tube diameter <i>D</i></span></figcaption></figure>
</div>
<p>Choose a pore to open its <a href="shape-gallery.html">3D shape gallery</a>.</p>
<p><code>pore.interface("roll")</code> selects an analytical model for the slit. Polygon names encode the number of walls touched (<code>w</code>) and corners occupied (<code>c</code>).</p>
""") + section("Shape catalog", """
<p>This snapshot lists 26 shapes. Of these, 18 supply a density profile and 24 supply surface terms. Availability describes the implemented formulas. Check the individual angle and volume-fraction limits before fitting.</p>
<form class="filters">
<label>Pore <select name="pore"><option value="">All pores</option><option value="slit">Slit</option><option value="triangle">Triangle</option><option value="square">Square</option><option value="cylinder">Cylinder</option></select></label>
<label>Operation <select name="operation"><option value="">All operations</option><option value="profile">Density profile</option><option value="surface">Surface terms</option></select></label>
<output aria-live="polite"></output></form>
<div class="table"><table><thead><tr><th>Pore</th><th>Shape</th><th>Density profile</th><th>Surface terms</th></tr></thead><tbody>{{shapes}}</tbody></table></div>
<p>Run <code>panda shapes --pore triangle</code> to see the installed version’s models, parameter bounds, and regimes.</p>
""") + section("Limits of the models", """
<p>Slit and cylindrical contact-angle models cover the non-wetting side of 90°. Some polygon models have narrower domains. Models such as a flat <code>layer</code> have no contact-angle parameter. Check <code>model.is_feasible(...)</code> and <code>model.phi_limits(...)</code> for the specific shape.</p>""") +
     section("Examples", '<p id="fit-a-triangular-filament"><a href="triangle-example.html">Fit a triangular filament</a></p>'))

page("User guide", "shape-gallery", "3D shape gallery",
     "Explore interface morphologies in slit, triangular, square, and cylindrical pores.",
     '<p><a href="geometries.html#shape-catalog">Check the package capabilities</a> for density fitting and surface terms. '
     'Cards marked “Formula draft” show geometries from the research formulas.</p>'
     '<p>Graphite marks the solid walls, dark brown the wetting phase, and blue the non-wetting phase. '
     'The contact angle is measured through the blue phase. The volume fraction refers to the full pore, including for cutaway views.</p>'
     '<p>For polygonal pores, <code>w</code> counts walls touched and <code>c</code> counts corners occupied by the blue phase. '
     'In a square pore, <code>filament_w2c0</code> touches opposite walls.</p>'
     '{{gallery}}')

page("User guide", "triangle-example", "Triangular filament",
     "Recover the angle from a synthetic density profile in a triangular pore.",
     section("Fit a triangular filament", """
<p>This example fits a synthetic <code>filament_w3c0</code> profile. The filament touches three walls and occupies zero corners.</p>
""" + code(TRIANGLE_EXAMPLE, "python") + output(TRIANGLE_OUTPUT) +
     "<p>With the <code>plot</code> extra, draw the fitted curve over the synthetic data.</p>" +
     code(TRIANGLE_PLOT, "python") + figure(
         "triangle-fit.png",
         "Analytical fit overlaid on a synthetic triangular filament density profile",
         'Archived synthetic fit for a triangular pore. <a href="triangle-profile.csv" download>Download CSV</a> · <a href="triangle-fit.png" download>Download PNG</a>.'
     )))

page("User guide", "trajectories", "From a trajectory",
     "Read a GROMACS or LAMMPS trajectory, inspect the contact angle across the full run, and fit a selected averaging window.",
     section("Download and run the examples", """
<p>Extract <a href="md-trajectory-examples.zip?v=10ns" download>md-trajectory-examples.zip</a> and <a href="installation.html#optional-dependencies">install PANDA with the <code>md</code> and <code>plot</code> extras</a>. Run these commands from the extracted directory. Both examples use the same 201 independently generated particle frames, spanning 0–10 ns at 50 ps intervals. The input angle is 120°. The time axis exercises the trajectory workflow on synthetic coordinates.</p>
""" + code("python md_gromacs.py\npython md_lammps.py") +
     '<p>Each script writes an NPZ with the full-run block profiles, an NPZ with the averaged profile, and a PNG with three diagnostic panels.</p>') +
     section("Choose an example", """
<ul>
<li id="gromacs"><a href="trajectory-gromacs.html">GROMACS</a> · GRO topology, XTC trajectory, and residue selections.</li>
<li id="lammps"><a href="trajectory-lammps.html">LAMMPS</a> · DATA topology, custom dump, atom types, and timestep.</li>
<li id="full-trajectory-and-averaging-window"><a id="plot-trajectory-diagnostics" href="trajectory-averaging.html">Full trajectory and averaging window</a> · profile, density map, and angle history.</li>
<li id="run-the-block-analysis-on-example-data"><a href="block-example.html">Fit saved blocks</a> · reuse existing density profiles.</li>
</ul>"""))

page("User guide", "trajectory-gromacs", "GROMACS",
     "Read a GRO or TPR topology and an XTC trajectory.",
     section("Run the GROMACS example", """
<p><a href="trajectories.html#download-and-run-the-examples">Download the example files and install the extras</a>.</p>
<p>The example reads <code>slit.gro</code> and <code>slit.xtc</code>. For a simulation, use a matching <code>.tpr</code> or <code>.gro</code> with your trajectory, and substitute the residue and atom names from that topology. The XTC stores frame times. If counting water oxygens, use the bulk <em>oxygen number density</em> in nm⁻³.</p>
""" + md_example("gromacs") +
     '<p><a href="trajectory-averaging.html">Read the diagnostic figure</a> · <a href="https://manual.gromacs.org/current/reference-manual/file-formats.html">GROMACS file formats</a> · <a href="https://userguide.mdanalysis.org/reading_and_writing.html">MDAnalysis input and topology options</a></p>'))

page("User guide", "trajectory-lammps", "LAMMPS",
     "Read a DATA topology and a custom trajectory dump.",
     section("Run the LAMMPS example", """
<p><a href="trajectories.html#download-and-run-the-examples">Download the example files and install the extras</a>.</p>
<p>The example pairs an <code>atom_style atomic</code> DATA file with a custom dump. Type 1 is the wall and type 2 is the selected liquid. For your run, substitute its atom types and set <code>atom_style</code> to the columns in the DATA file’s <code>Atoms</code> section. The dump and DATA file must have matching atom IDs.</p>
""" + md_example("lammps")) + section("Write a compatible dump", """
<p>Use the integration timestep in <strong>ps per step</strong> for Python’s <code>dt</code>. Here, 25,000 steps × 0.002 ps gives 50 ps between saved frames. With <code>units real</code>, convert the input timestep from fs to ps. With <code>units lj</code>, convert reduced distances and times consistently before using physical nm and ps labels. PANDA's MDAnalysis reader converts input Å to nm.</p>
""" + code("write_data slit.data\ndump trajectory all custom 25000 slit.lammpstrj id type x y z\ndump_modify trajectory sort id") +
     '<p><a href="trajectory-averaging.html">Read the diagnostic figure</a> · <a href="https://docs.lammps.org/dump.html">LAMMPS dump command</a> · <a href="https://docs.lammps.org/units.html">LAMMPS units</a></p>'))

page("User guide", "trajectory-averaging", "Trajectory averaging",
     "Use the full angle history to show which frames contribute to the reported fit.",
     section("Full trajectory and averaging window", """
<p>Panel (a) shows the density map centered on the roll axis and the slit midplane. Panel (b) shows the density profile and its fit, with the slit midplane at <em>z/H</em> = 0. Both panels use the same 2–10 ns averaging window.</p>
<p>Panel (c) shows all twenty 0.5 ns blocks across 0–10 ns. Open markers show the four early blocks. Green shading begins at 2 ns, and the horizontal dashed line gives the angle from fitting the averaged profile.</p>
""" + figure(
     "md-trajectory-diagnostics.png",
     "Centered green density map, centered fitted profile, and angle across twenty time blocks with averaging from 2 ns",
     'GROMACS-format example. <a href="md-trajectory-diagnostics.png" download>Download PNG</a>.'
) + """
<p>Each block marker is placed at the midpoint of its sampled frames. PANDA drops an incomplete final block. The reported standard deviation uses the complete plotted blocks whose sampled frames lie within the averaging window. For production data, inspect equilibration before choosing the averaging start and account for temporal correlation when choosing the block length.</p>
""") + section("Shared Python workflow", '<details><summary>Show the analysis and plotting code</summary>' +
     code((ROOT / "md_workflow.py").read_text(encoding="utf-8"), "python") + '</details>') +
     section("Check the profile", """
<p>Match the bulk density to the selected particle representation. Check wall selections, centering, bin width, and the periodic box geometry. Reload the full-run profiles with <code>ProfileSet.load("gromacs-blocks.npz")</code> and the averaged profile with <code>DensityProfile.load("gromacs-average.npz")</code>. Use the corresponding <code>lammps-</code> filenames for that run.</p>"""))

page("User guide", "block-example", "Fit saved blocks",
     "Estimate the spread in contact angle from a saved set of density profiles.",
     section("Run the block analysis on example data", """
<p>Download <a href="synthetic-roll-blocks.npz" download>synthetic-roll-blocks.npz</a> into the working directory. The file contains eight independent synthetic profiles generated with a 120° contact angle.</p>
""" + code(BLOCK_EXAMPLE, "python") + output(BLOCK_OUTPUT) + code("""
import matplotlib.pyplot as plt

angles = blocks.values("theta")
fig, ax = plt.subplots()
ax.plot(range(1, len(angles) + 1), angles, "o", label="Block fit")
ax.axhline(120, linestyle="--", label="Input angle")
ax.set(xlabel="Synthetic block", ylabel="Contact angle (deg)")
ax.legend()
plt.show()
""", "python") + figure(
    "synthetic-block-angles.png",
    "Eight synthetic block angle estimates scattered around the input angle of 120 degrees",
    'Each marker is a separate fit. The dashed line marks the 120° input. <a href="synthetic-block-angles.csv" download>Download the block angles</a>.'
)))

page("User guide", "fitting", "Fitting and interpretation",
     "Fit a candidate interface, inspect its diagnostics, and compare models in the physically accessible domain.",
     section("Fit a saved profile", """
<p>Download <a href="density.csv" download>density.csv</a> into the working directory. It contains the synthetic slit-pore profile from the quick start in physical units. A headerless input file contains coordinate in nm, number density in nm⁻³, and an optional uncertainty column. Center the coordinates consistently with the analytical pore.</p>
""" + code(SAVED_FIT, "python") + output(SAVED_OUTPUT) +
    '<p>An empty tuple <code>()</code> means PANDA reported no diagnostic flags for this fit.</p>') + section("Parameters and normalization", """
<p><code>theta</code> is the contact angle in degrees for the analyzed phase. <code>delta</code> is the effective wall-layer thickness as a fraction of the characteristic pore size. <code>phi</code> is the analyzed liquid’s volume fraction. <code>shift</code> is an offset along the profile coordinate in pore-size units, fixed at zero by default.</p>
<p>With bulk normalization, PANDA divides the input density by ρ<sub>bulk</sub> and can estimate φ from the profile. With mean normalization, supply the profile’s particle count and pore volume, and fix or optimize φ if the bulk density is unavailable.</p>
""") + section("Fit diagnostics", """
<p>The default L1 objective is the mean absolute deviation of the normalized profiles. PANDA runs Nelder–Mead from multiple starting points. Inspect convergence, feasibility, parameter bounds, and the <code>at_regime_boundary</code> flag. A boundary fit near 90° may indicate that the selected model’s angular range is too restrictive.</p>
<p id="how-noise-and-angle-affect-recovery"><a href="validation.html">How noise and angle affect recovery</a></p>
""") + section("Compare shapes and stability", """
<p><code>compare_shapes(pore, profile, spec)</code> ranks available profiles by fit loss. Near-ties can occur when different interfaces project to nearly the same one-dimensional density. Inspect the density map or snapshots before assigning a morphology.</p>
<p><code>stability_diagram(...)</code> ranks feasible shapes by the capillary surface term S<sub>LV</sub> − cos θ S<sub>SL</sub> at prescribed angle and layer thickness. Each operation has its own set of supported shapes in the <a href="geometries.html">catalog</a>.</p>"""))

page("User guide", "validation", "Angle recovery",
     "Compare the mean and maximum absolute errors on synthetic slit-pore rolls.",
     section("How noise and angle affect recovery", """
<p>The validation sweep used 200 bins and ten noise realizations at each setting. Panel (a) varies the noise at θ = 120°. Panel (b) varies the input angle at 0.5% noise. The maximum is the largest absolute error across the ten realizations.</p>
""" + figure(
    "roll-validation.png",
    "Mean and maximum absolute angle error increase with profile noise and near the high-angle limit",
    'Archived validation data. <a href="validation-roll-noise.csv" download>Noise sweep CSV</a> · <a href="validation-roll-angle.csv" download>Angle sweep CSV</a>.'
)))

page("User guide", "cli", "Command line",
     "Use panda to build profiles, fit a known shape, or compare candidate models from the shell.",
     section("Inspect available models", code("panda shapes --pore slit\npanda profile --help\npanda fit --help")) +
     section("Create a profile and fit it", code("""
panda profile system.tpr system.xtc --walls "resname GRAPHITE" --select "resname WATER and name OW" --start "2 ns" --block "1 ns" -o water.npz --pore-output pore.json
panda fit water.npz --pore-file pore.json --shape roll --rho-bulk 33.1 --blocks -o result.json
""") + """
<p>Use <code>--shape auto</code> to compare supported candidates and <code>--plot fit.png</code> with the plotting extra. The exit codes are 0 for success, 1 for an input error, and 2 for a completed fit with diagnostic flags.</p>
""") + section("Save the workflow in TOML", code("""
[pore]
type = "slit"
wall_selection = "resname GRAPHITE"

[profile]
topology = "system.tpr"
trajectory = ["system.xtc"]
select = "resname WATER and name OW"
start = "2 ns"
block = "1 ns"

[fit]
shape = "roll"
density_bulk_per_nm3 = 33.1
blocks = true
output = "result.json"
""", "toml") + "<p>Save as <code>panda.toml</code> and run <code>panda run panda.toml</code>. Input paths are relative to the settings file.</p>"))

API_PAGES, API_SEARCH = reference_pages(section, PACKAGE)
PAGES.append(API_PAGES[0])

PUBLICATIONS = [
    ("Kopanichuk et al.", "The shape of the liquid-liquid interface for oil/water mixtures in slit pores", "Colloids and Surfaces A 601 (2020), 124884", "https://doi.org/10.1016/j.colsurfa.2020.124884"),
    ("Semenchuk, Kondratyuk, and Kopanichuk", "PANDA: Predicting angle from nanoscale density analysis", "Colloids and Surfaces A 708 (2025), 135994", "https://doi.org/10.1016/j.colsurfa.2024.135994"),
    ("Semenchuk et al.", "Towards reproducible wetting studies: Automated contact angle determination by molecular simulations", "Colloids and Surfaces A 725 (2025), 137586", "https://doi.org/10.1016/j.colsurfa.2025.137586"),
    ("Shistko et al.", "Characterisation of the dominant liquid-liquid interface shape in confined systems during molecular simulations", "Molecular Simulation 51(16) (2025), 1071–1080", "https://doi.org/10.1080/08927022.2025.2574643"),
    ("Guskov et al.", "From nanodroplets to macroscopic wettability for rough surfaces: Combining molecular simulations and experiments", "Journal of Molecular Liquids 439 (2025), 128861", "https://doi.org/10.1016/j.molliq.2025.128861"),
    ("Semenchuk, Bakulin, Gerke, Kondratyuk, and Kopanichuk", "The Effect of Adsorption Film Thickness on the Shape of the Interface Between Immiscible Liquids in a Flat Slitlike Pore", "Colloid Journal 88(2) (2026), 211–221", "https://doi.org/10.1134/S1061933X25601441"),
    ("Guskov et al.", "Assessing density equilibration in confined liquid–liquid interfaces", "Molecular Simulation 52(7) (2026), 546–555", "https://doi.org/10.1080/08927022.2026.2650110"),
    ("Vandyshev, Kondratyuk, Gerke, and Kopanichuk", "The interface shape and contact angle determination for liquid-liquid systems in cylindrical nanopores", "Capillarity 19(3) (2026), 86–96", "https://doi.org/10.46690/capi.2026.06.03"),
]
BIBTEX = """@article{semenchuk2025panda,
  author  = {Semenchuk, A. A. and Kondratyuk, N. D. and Kopanichuk, I. V.},
  title   = {{PANDA}: Predicting angle from nanoscale density analysis},
  journal = {Colloids and Surfaces A: Physicochemical and Engineering Aspects},
  year    = {2025},
  volume  = {708},
  pages   = {135994},
  doi     = {10.1016/j.colsurfa.2024.135994}
}"""


def bibliography():
    entries = []
    for authors, title, journal, url in PUBLICATIONS:
        title = escape(title)
        if url:
            title = f'<a href="{url}">{title}</a>'
        entries.append(f"<li>{title}<span>{escape(authors)} · {escape(journal)}</span></li>")
    return '<ol class="pubs">' + "".join(entries) + "</ol>"


page("Reference", "citation", "Citing PANDA",
     "Cite the original PANDA method and the studies relevant to your geometry or analysis.",
     section("Original method", """
<p>Semenchuk, Kondratyuk, and Kopanichuk introduced PANDA in <i>Colloids and Surfaces A</i>, volume 708, article 135994. Include the package version or commit used in your methods.</p>
""" + code(BIBTEX, "bibtex") + '<p><a href="panda-method.bib" download>Download BibTeX</a></p>') +
     section("Package paper", "<p>The manuscript describing the current software package is in preparation. Its citation will be added when it is available.</p>") +
     section("Related publications", bibliography()) +
     section("Dynamic contact angles", '<p><a href="https://arxiv.org/abs/2610.21996">PANDA-D: Interface-free determination of two dynamic contact angles</a> (preprint, 2026). The two-angle extension jointly analyzes density and layerwise center-of-mass displacement.</p>'))


def gallery():
    with (ROOT / "shapes.csv").open(encoding="utf-8-sig", newline="") as source:
        registered = {(row["pore"], row["shape"]) for row in csv.DictReader(source)}
    assets = ROOT.parent / "docs" / "models"
    items = json.loads((assets / "catalog.json").read_text(encoding="utf-8"))
    groups = []
    for pore in ("slit", "triangle", "square", "cylinder"):
        cards = []
        for item in items:
            if item["pore"] != pore:
                continue
            source_name = item["shape"]
            display_name = item.get("display_name", source_name)
            name = escape(display_name)
            base = f"models/{pore}/{escape(source_name)}"
            theta = item["theta_deg"]
            params = f'θ = {theta}° · ' if theta is not None else ''
            params += f'φ = {item["phi"]:.2f}'
            status = "In package catalog" if (pore, display_name) in registered else "Formula draft"
            cut = ' · Cutaway' if source_name == "perforation" or pore == "cylinder" or name.startswith("capsule_w") else ""
            cards.append(
                f'<article class="shape-card"><img src="{base}.webp" width="760" height="589" loading="lazy" '
                f'alt="{name} in a {pore} pore"><h3><code>{name}</code></h3>'
                f'<p>{params}</p><p>{status}{cut}</p><div class="shape-actions">'
                f'<button type="button" data-model="{base}.glb" aria-haspopup="dialog" '
                f'aria-label="View {name} in 3D">View in 3D</button>'
                f'<a href="{base}.glb" download>Download GLB</a></div></article>'
            )
        groups.append(f'<h2 id="{pore}">{pore.title()}</h2><div class="shape-grid">{"".join(cards)}</div>')
    return "".join(groups) + (
        '<dialog class="shape-dialog" aria-labelledby="shape-dialog-title">'
        '<form method="dialog"><h2 id="shape-dialog-title">3D model</h2><button>Close</button></form>'
        '<p role="status"></p><div class="shape-view"></div><a download>Download GLB</a></dialog>'
        '<script type="module" src="models/gallery.js"></script>'
    )


def shape_rows():
    with (ROOT / "shapes.csv").open(encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    labels = {"0": "—", "1": "Yes"}
    return "".join(
        f'<tr data-pore="{pore}" data-profile="{profile}" data-surface="{surface}">'
        f'<td>{pore.title()}</td><td><code>{escape(shape)}</code></td>'
        f'<td>{labels[profile]}</td><td>{labels[surface]}</td></tr>'
        for pore, shape, profile, surface in (row.values() for row in rows)
    )


def sidebar(active):
    if active == "api" or active.startswith("api-"):
        links = ['<a href="geometries.html">← User guide</a><p>Python API</p>']
        for _, slug, title, _, _ in API_PAGES:
            current = ' aria-current="page"' if slug == active else ""
            label = "Reference index" if slug == "api" else title
            links.append(f'<a href="{slug}.html"{current}>{label}</a>')
        return "".join(links)
    links = []
    current_group = None
    child_pages = {child for children in SUBPAGES.values() for child in children}
    titles = {slug: title for _, slug, title, _, _ in PAGES}

    def link(slug, label=None):
        current = ' aria-current="page"' if slug == active else ""
        return f'<a href="{slug}.html"{current}>{label or titles[slug]}</a>'

    for group, slug, title, _, _ in PAGES:
        if slug in child_pages:
            continue
        menu_group = "Reference" if group == "Python API" else group
        if current_group != menu_group:
            links.append(f"<p>{menu_group}</p>")
            current_group = menu_group
        if children := SUBPAGES.get(slug):
            expanded = slug == active or active in children
            state = ' open' if expanded else ''
            links.append(
                f'<details class="nav-branch"{state}><summary>{title}</summary>'
                f'<div class="nav-children">{link(slug, "Section overview")}'
                + "".join(link(child) for child in children) + "</div></details>"
            )
        else:
            links.append(link(slug))
    return "".join(links)


def render(index, entry, sequence, search_version, script_version):
    group, slug, title, lead, body = entry
    headings = re.findall(r'<h2 id="([^"]+)">([^<]+)</h2>', body)
    toc = "".join(f'<a href="#{anchor}">{heading}</a>' for anchor, heading in headings)
    article = f'<h1>{title}</h1><p class="lead">{lead}</p>' if lead else ""
    breadcrumb = f"Documentation / {group} / {title}"
    if slug == "api":
        breadcrumb = "Documentation / Python API"
    elif group == "Python API":
        breadcrumb = f'Documentation / <a href="api.html">Python API</a> / {title}'
    previous = sequence[index - 1][1:3] if index else None
    following = sequence[index + 1][1:3] if index + 1 < len(sequence) else None
    back = f'<a href="{previous[0]}.html">← {previous[1]}</a>' if previous else "<span></span>"
    forward = f'<a href="{following[0]}.html">{following[1]} →</a>' if following else ""
    tabs = [
        ("Overview", "index", slug == "index"),
        ("Getting started", "quickstart", slug in {"installation", "quickstart"}),
        ("User guide", "geometries", group == "User guide"),
        ("Python API", "api", group == "Python API"),
        ("Citation", "citation", slug == "citation"),
    ]
    nav_links = []
    for label, target, active in tabs:
        current = f' aria-current="{"page" if slug == target else "true"}"' if active else ""
        nav_links.append(f'<a href="{target}.html"{current}>{label}</a>')
    nav = "".join(nav_links)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{escape(lead or 'PANDA documentation for contact angles and interface shapes in confined liquids.', quote=True)}">
<title>{title} · PANDA Documentation</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Orbitron:wght@600;700&display=swap">
<link rel="stylesheet" href="panda-theme.css?v={THEME_VERSION}">
<script src="search-index.js?v={search_version}" defer></script><script src="site.js?v={script_version}" defer></script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="header">
<a href="index.html" class="brand"><img src="panda-logo.png" alt="PANDA"><span>Documentation</span></a>
<nav class="header-links" aria-label="Main navigation">{nav}</nav>
<div class="actions">
<button class="search-toggle" type="button" aria-haspopup="dialog">Search <kbd>Ctrl K</kbd></button>
<a class="source" href="{PACKAGE}">Package source ↗</a>
<button class="mobile menu-toggle" type="button" aria-controls="sidebar" aria-expanded="false">Menu</button>
</div></header>
<div class="layout">
<aside class="side" id="sidebar"><nav aria-label="Documentation">{sidebar(slug)}</nav></aside>
<main id="main"><p class="crumb">{breadcrumb}</p>{article}{body}
<nav class="pager" aria-label="Adjacent pages">{back}{forward}</nav></main>
<aside class="toc"><nav aria-label="Page contents"><p>On this page</p>{toc}</nav></aside>
</div>
<footer><span>PANDA · Predicting Angle from Nanoscale Density Analysis</span><a href="citation.html">Cite PANDA</a></footer>
<dialog aria-label="Search documentation">
<form method="dialog"><input type="search" placeholder="Search by topic or API name" aria-label="Search query"><button type="submit">Close</button></form>
<p role="status"></p><ul></ul>
</dialog>
</body></html>
"""


def build(output):
    output.mkdir(parents=True, exist_ok=True)
    index = []
    rendered_pages = []
    for entry in [*PAGES, *API_PAGES[1:]]:
        group, slug, title, lead, body = entry
        if slug == "geometries":
            body = body.replace("{{shapes}}", shape_rows())
            for pore in ("slit", "triangle", "square", "cylinder"):
                body = body.replace(f'<strong>{pore.title()}</strong>',
                                    f'<strong><a href="shape-gallery.html#{pore}">{pore.title()}</a></strong>')
        if slug == "shape-gallery":
            body = body.replace("{{gallery}}", gallery())
        sequence = API_PAGES if group == "Python API" else PAGES
        order = sequence.index(entry)
        path = slug + ".html"
        rendered_pages.append((path, order, (group, slug, title, lead, body), sequence))
        index.append({"title": title, "href": path, "text": lead + " " + re.sub(r"<[^>]+>", " ", body)})
    search_index = "window.pandaSearch = " + json.dumps(index + API_SEARCH) + ";\n"
    search_version = sha256(search_index.encode()).hexdigest()[:10]
    script_version = sha256((ROOT / "site.js").read_bytes()).hexdigest()[:10]
    for path, order, entry, sequence in rendered_pages:
        html = render(order, entry, sequence, search_version, script_version)
        (output / path).write_text(html, encoding="utf-8")
    (output / "search-index.js").write_text(search_index, encoding="utf-8")
    (output / "quickstart.py").write_text(QUICKSTART + "\n", encoding="utf-8")
    (output / "panda-method.bib").write_text(BIBTEX + "\n", encoding="utf-8")
    (output / ".nojekyll").touch()
    for filename in (
        "panda-theme.css", "site.js", "panda-logo.png", "profile-light.png", "roll-profile.csv",
        "roll-fit-residuals.png", "triangle-fit.png", "triangle-profile.csv",
        "density.csv", "synthetic-roll-blocks.npz", "synthetic-block-angles.csv",
        "synthetic-block-angles.png", "roll-validation.png",
        "validation-roll-noise.csv", "validation-roll-angle.csv",
        "md-trajectory-examples.zip", "md-trajectory-diagnostics.png",
        "pore-slit.png", "pore-triangle.png", "pore-square.png", "pore-cylinder.png",
    ):
        shutil.copyfile(ROOT / filename, output / filename)
    assets = ROOT.parent / "docs" / "models"
    if (output / "models").resolve() != assets.resolve():
        shutil.copytree(assets, output / "models", dirs_exist_ok=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    build(parser.parse_args().output)
