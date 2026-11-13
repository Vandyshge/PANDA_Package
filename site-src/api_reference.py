"""Content and HTML for the Python API reference."""

import json
from html import escape
from pathlib import Path


# Each entry lists the public name, its description, and any documented members.
API_GROUPS = (
    ("pores", "Pores and models", "Choose a geometry, discover its shapes, and evaluate an interface.",
     "geometries.html", "Pores and shapes guide", (
        ("panda_md.SlitPore", "Parallel walls separated by width_nm. The characteristic size is the wall-to-wall gap.",
         "from_trajectory shape_names interface characteristic_size_nm volume_nm3"),
        ("panda_md.TrianglePore", "Equilateral triangular channel. The characteristic size is side_nm.",
         "shape_names interface characteristic_size_nm volume_nm3"),
        ("panda_md.SquarePore", "Square channel. The characteristic size is side_nm.",
         "shape_names interface characteristic_size_nm volume_nm3"),
        ("panda_md.CylinderPore", "Circular channel. The characteristic size is diameter_nm.",
         "from_trajectory shape_names interface characteristic_size_nm volume_nm3"),
        ("panda_md.InterfaceModel", "A named interface bound to a pore. Construct it with pore.interface(shape_name). Supply theta in degrees, delta and shift in reduced pore units, and phi as a fraction.",
         "default_optimize profile is_feasible phi_limits surface_terms capillary_energy fit"),
        ("panda_md.Parameter", "Definition of a shape parameter and its units, allowed range, and default value.", ""),
        ("panda_md.SymmetryAxis", "Orientation and location rule used to center a shape in trajectory maps.", ""),
    )),
    ("fitting", "Fitting and results", "Configure optimization, read parameters, and inspect diagnostic flags.",
     "fitting.html", "Fitting guide", (
        ("panda_md.FitSpec", "Reusable settings for a fit, shape comparison, or block analysis. Bounds narrow the model domain. The fit window uses reduced coordinates.", ""),
        ("panda_md.InterfaceModel.fit", "Fit one DensityProfile and return a FitResult. Set density_bulk_per_nm3 for bulk normalization. The default loss is mean absolute deviation.", ""),
        ("panda_md.FitResult", "Fitted values, optimizer diagnostics, normalized fit data, and model curve. Use values['theta'] for the contact angle when the shape has one.",
         "summary problems"),
    )),
    ("data", "Profiles and trajectories", "Load simulation files or arrays, then compute, store, or inspect densities.",
     "trajectories.html", "Trajectory guide", (
        ("panda_md.load_trajectory", "Open a topology and one or more trajectory files through MDAnalysis. Requires the md extra. Additional options go to MDAnalysis.Universe.", ""),
        ("panda_md.ArrayTrajectory", "In-memory trajectory. Supply particle positions and box lengths in nm, and frame times in ps.",
         "select times_ps frame_indices frames"),
        ("panda_md.density_profile", "Bin number density along the pore axis. The selection accepts an MDAnalysis selection string or atom indices. A numeric time is in ps. A block setting produces time-resolved profiles.", ""),
        ("panda_md.DensityProfile", "One number-density profile with coordinates in nm and densities in nm⁻³. Supports NPZ or CSV input and output.",
         "load save mean_density_per_nm3"),
        ("panda_md.ProfileSet", "One or more profiles on a common bin grid. The time bounds and frame counts describe the samples contributing to each block. Use NPZ to persist the set.",
         "load save mean block std sem block_count coordinate_nm"),
        ("panda_md.density_map", "Compute a two-dimensional number-density map in a slit pore. A supported shape name enables alignment on the shape symmetry axis.", ""),
        ("panda_md.DensityMap", "Binned two-dimensional number density in nm⁻³ and its bin edges in nm.", ""),
    )),
    ("analysis", "Blocks and morphology", "Compare fitted shapes, estimate block spread, and map capillary stability.",
     "trajectory-averaging.html", "Block averaging example", (
        ("panda_md.fit_blocks", "Fit each block of a ProfileSet with the same model and settings.", ""),
        ("panda_md.FitResultSet", "Per-block fits and summary statistics. Interpret SEM as uncertainty of the mean only when blocks are sufficiently independent.",
         "values mean std sem summary"),
        ("panda_md.statistical_inefficiency", "Estimate how the variance of block means changes with block length for a series.", ""),
        ("panda_md.StatisticalInefficiency", "Block lengths and estimated inefficiencies, with a plateau estimate when enough reliable lengths exist.",
         "plateau"),
        ("panda_md.compare_shapes", "Fit candidate shapes to the same profile and rank by loss. The result retains skipped shapes and records nearly indistinguishable candidates.", ""),
        ("panda_md.ShapeComparison", "Comparison of feasible fits and skipped candidates.",
         "fitted best indistinguishable summary"),
        ("panda_md.ShapeFit", "One candidate's fit result or the reason PANDA skipped it.", ""),
        ("panda_md.stability_diagram", "Find the minimum capillary energy over volume fractions and reduced pore lengths at a fixed angle and wall-layer thickness.", ""),
        ("panda_md.StabilityDiagram", "Grid of stable shape names, indexed by length ratio then volume fraction. None means no candidate exists at that point.", ""),
    )),
    ("synthetic", "Synthetic data and accuracy", "Generate known-angle test data and measure reconstruction error.",
     "validation.html", "Angle recovery example", (
        ("panda_md.synthetic_profile", "Generate a one-dimensional profile for known model parameters. Set seed for repeatable noise.", ""),
        ("panda_md.synthetic_trajectory", "Sample particle coordinates for a slit-pore shape that implements point containment. The returned trajectory includes liquid and walls groups.", ""),
        ("panda_md.analysis.accuracy.AccuracyCase", "Configuration for one synthetic recovery case, including the input parameters and noise settings.", ""),
        ("panda_md.analysis.accuracy.angle_errors", "Repeat a synthetic fit with independent seeds and collect fitted-angle errors.", ""),
        ("panda_md.analysis.accuracy.AngleErrors", "Per-seed errors in degrees (fitted minus input) and flags for fits at the angle bound.", ""),
        ("panda_md.analysis.accuracy.accuracy_study", "Run a collection of synthetic recovery cases.", ""),
        ("panda_md.analysis.accuracy.AccuracyStudy", "Collect case-by-case angle errors for tables or figures.",
         "mean_absolute maximum_absolute bias table"),
        ("panda_md.core.enums.NoiseModel", "Noise model for a synthetic density profile.", ""),
        ("panda_md.core.enums.ProfileSampling", "Use the center of each bin or average the model across the bin.", ""),
    )),
    ("plotting", "Plotting", "Draw figures from existing PANDA objects. Requires the plot extra.",
     "quickstart.html#plot-the-fit-and-residuals", "Plot a fit and residuals", (
        ("panda_md.plotting.plot_profile", "Draw one density profile or a mean with block-based standard errors.", ""),
        ("panda_md.plotting.plot_fit", "Overlay normalized data and the fitted curve on the fit coordinate.", ""),
        ("panda_md.plotting.plot_blocks", "Draw one fitted parameter at the midpoint of each time block.", ""),
        ("panda_md.plotting.plot_density_map", "Render a slit-pore number-density map with a colorbar.", ""),
        ("panda_md.plotting.plot_stability", "Render stable morphologies on the volume-fraction and reduced-length grid.", ""),
        ("panda_md.plotting.plot_accuracy", "Visualize angle errors across synthetic recovery cases.", ""),
        ("panda_md.plotting.save_fit_figure", "Export the fit figure to a file. Its extension determines the format.", ""),
        ("panda_md.plotting.supported_figure_formats", "List formats supported by the Matplotlib writer.", ""),
    )),
    ("types", "Enums and exceptions", "Look up supported values and diagnose failures.",
     "fitting.html#fit-diagnostics", "Fit diagnostics guide", (
        ("panda_md.Axis", "Cartesian axis of the rectangular simulation box.", "column"),
        ("panda_md.AxisLocator", "Rule for locating the symmetry axis within a frame.", ""),
        ("panda_md.AxisOrientation", "Direction of a shape symmetry axis relative to the walls.", ""),
        ("panda_md.Frame", "Coordinate frame in which the density profile is expressed.", ""),
        ("panda_md.LossFunction", "Mean absolute or mean squared deviation between profiles.", ""),
        ("panda_md.Normalization", "Choice of bulk or mean density normalization.", ""),
        ("panda_md.OptimizerMethod", "Local optimizer used by the fit.", ""),
        ("panda_md.Orientation", "Whether pore-frame profiles can be reflected along the normal axis.", ""),
        ("panda_md.ParameterName", "Standard keys in result values and fit settings.", ""),
        ("panda_md.ParticleGrouping", "Count selected atoms or centers of mass of molecules.", ""),
        ("panda_md.ProfileCentering", "Reference point placed at zero for each profile.", ""),
        ("panda_md.Regime", "Wetting or non-wetting regime of the selected liquid.", ""),
        ("panda_md.Unit", "Unit convention used for a model parameter.", ""),
        ("panda_md.PandaError", "Base exception for errors reported by PANDA.", ""),
        ("panda_md.PandaWarning", "Base warning emitted for diagnostic conditions.", ""),
        ("panda_md.InfeasibleParametersError", "The parameters do not admit the requested morphology.", ""),
        ("panda_md.InvalidProfileError", "The input density profile is invalid or lacks required metadata.", ""),
        ("panda_md.InvalidTrajectoryError", "The trajectory, frame selection, or box geometry is invalid for the requested operation.", ""),
        ("panda_md.MissingDependencyError", "An optional package required by the requested operation is missing.", ""),
        ("panda_md.NotDerivedError", "The requested analytical operation has no implementation for this shape or pore.", ""),
        ("panda_md.ProfileMismatchError", "The input profile and model are incompatible.", ""),
        ("panda_md.UnsupportedRegimeError", "The requested wetting regime is unavailable for the model.", ""),
        ("panda_md.__version__", "Installed package version string.", ""),
    )),
)

METADATA_PATH = Path(__file__).with_name("api-metadata.json")

PARAMETERS = {
    "panda_md.InterfaceModel.fit": (
        ("profile", "DensityProfile in physical units."),
        ("optimize, fixed", "Choose the free parameter names or assign fixed values. An omitted optimize uses the model defaults."),
        ("bounds, initial", "Optionally narrow parameter bounds and supply an extra starting point in user units."),
        ("normalization, density_bulk_per_nm3", "Auto normalization uses bulk density if supplied, otherwise the profile mean density."),
        ("window", "Fit interval on the reduced profile coordinate."),
        ("regime", "Restrict the search to a supported wetting regime."),
    ),
    "panda_md.density_profile": (
        ("bins, bin_width_nm", "Set the bin count or the width in nm."),
        ("start, stop, stride", "Select a frame interval and subsample it. Time can be numeric ps or a string such as '2 ns'."),
        ("block", "Length of a time block. The default returns a ProfileSet with one averaged profile."),
        ("centering, orientation", "Choose the coordinate origin and whether PANDA may reflect the pore-frame profile."),
        ("per", "Count atoms or molecule centers of mass."),
    ),
    "panda_md.density_map": (
        ("bins", "Number of bins along the long side and profile axis."),
        ("shape", "Optional interface name for locating the in-plane symmetry axis."),
        ("width_window_nm", "Optional strip width along the short side for a vertical symmetry axis."),
    ),
    "panda_md.compare_shapes": (
        ("spec", "Fit settings shared by the candidate shapes."),
        ("shape_names", "Optional list of shapes to compare. By default, use all registered shapes for the pore."),
    ),
    "panda_md.stability_diagram": (
        ("contact_angle_deg, wall_layer", "Fixed contact angle in degrees and effective wall-layer thickness in reduced pore units."),
        ("volume_fractions, length_ratios", "Grid coordinates. Length ratios are relative to the characteristic pore size."),
        ("shape_names", "Optional restriction to the listed morphologies."),
    ),
    "panda_md.synthetic_profile": (
        ("values", "Model parameters in user units, including theta in degrees where applicable."),
        ("noise_std, noise_model, seed", "Noise magnitude relative to bulk density, its scaling rule, and the random seed."),
        ("sampling", "Evaluate at bin centers or average within each bin."),
    ),
}


def symbol_name(qualified):
    parts = qualified.split(".")
    if len(parts) > 2 and parts[-2][:1].isupper():
        return ".".join(parts[-2:])
    return parts[-1]


def anchor(qualified):
    return symbol_name(qualified).lower().replace(".", "-")


def table(headers, rows):
    head = "".join(f"<th scope='col'>{item}</th>" for item in headers)
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    return f'<div class="table"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def details(item, description, commit, repository):
    signature = item.get("signature")
    content = f"<p>{escape(description)}</p>"
    if signature:
        content = f'<pre class="api-signature"><code>{escape(signature)}</code></pre>' + content
    if parameters := PARAMETERS.get(item["name"]):
        content += "<h3>Parameters</h3>" + table(("Argument", "Meaning"), [
            (f"<code>{escape(name)}</code>", escape(note)) for name, note in parameters
        ])
    if item.get("values"):
        content += table(("Member", "Value"), [
            (f"<code>{escape(name)}</code>", f"<code>{escape(value)}</code>")
            for name, value in item["values"]
        ])
    if item.get("fields"):
        content += "<h3>Fields</h3>" + table(("Field", "Type"), [
            (f"<code>{escape(name)}</code>", f"<code>{escape(annotation)}</code>")
            for name, annotation in item["fields"]
        ])
    if item.get("members"):
        content += "<h3>Methods and properties</h3><dl class='api-members'>"
        for name, member in item["members"].items():
            sig = member["signature"] or name
            content += (f'<dt id="{anchor(item["name"])}-{name.lower()}"><code>{escape(sig)}</code></dt>'
                        f'<dd>{escape(member["description"])}</dd>')
        content += "</dl>"
    if item.get("source"):
        content += (f'<p class="api-source"><a href="{repository}/blob/{commit}/{item["source"]}">'
                    'View definition ↗</a></p>')
    return content


def reference_pages(section, repository):
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    commit = metadata["commit"]
    pages = []
    search = []
    rows = []
    for slug, title, lead, guide, guide_title, entries in API_GROUPS:
        page_slug = f"api-{slug}"
        rows.append((f'<a href="{page_slug}.html">{title}</a>', lead))
        content = f'<p><a href="{guide}">{guide_title} →</a></p>'
        for qualified, description, _ in entries:
            item = metadata["symbols"][qualified]
            symbol_id = anchor(qualified)
            search.append({"title": symbol_name(qualified), "href": f"{page_slug}.html#{symbol_id}",
                           "text": qualified + " " + description})
            for name, member in item.get("members", {}).items():
                if qualified == "panda_md.InterfaceModel" and name == "fit":
                    continue
                search.append({
                    "title": f"{symbol_name(qualified)}.{name}",
                    "href": f"{page_slug}.html#{symbol_id}-{name.lower()}",
                    "text": f"{qualified}.{name} {member['description']}",
                })
            content += (f'<section class="api-symbol"><h2 id="{symbol_id}">{symbol_name(qualified)}</h2>'
                        f'<p class="api-path"><code>{qualified}</code></p>'
                        + details(item, description, commit, repository) + "</section>")
        pages.append(("Python API", page_slug, title, lead, content))
    body = section("Reference by topic", table(("Topic", "Description"), rows)) + section(
        "Version and imports",
        f'<p>Signatures are generated from PANDA 0.1.0 alpha at commit '
        f'<a href="{repository}/tree/{commit}"><code>{commit[:7]}</code></a>. '
        'Most entries can be imported from <code>panda_md</code>. Plotting helpers are in '
        '<code>panda_md.plotting</code>. Definition links may require access to the package repository.</p>',
    )
    index = ("Python API", "api", "Python API", "Find functions, classes, parameters, and return types by topic.", body)
    return [index, *pages], search
