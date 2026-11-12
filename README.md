<p align="center">
  <a href="https://vandyshge.github.io/PANDA_Package/">
    <img src="https://vandyshge.github.io/PANDA_Package/panda-logo.png" alt="PANDA" width="350">
  </a>
</p>

# PANDA documentation

PANDA (Predicting Angle from Nanoscale Density Analysis) estimates contact angles and compares interface shapes of confined liquids by fitting analytical models to one-dimensional density profiles from molecular simulations.

**[Read the documentation](https://vandyshge.github.io/PANDA_Package/)** · **[Python package source](https://github.com/Ilya-Garanov-WorkingAcc/PANDA_2.0)** · **[How to cite PANDA](https://vandyshge.github.io/PANDA_Package/citation.html)**

## Start here

| Goal | Guide |
| --- | --- |
| Install PANDA and its optional dependencies | [Installation](https://vandyshge.github.io/PANDA_Package/installation.html) |
| Recover a known angle from a synthetic slit-pore profile | [Quick start](https://vandyshge.github.io/PANDA_Package/quickstart.html) |
| Analyze a molecular-dynamics trajectory | [GROMACS](https://vandyshge.github.io/PANDA_Package/trajectory-gromacs.html) · [LAMMPS](https://vandyshge.github.io/PANDA_Package/trajectory-lammps.html) |
| Choose a pore geometry or interface shape | [Pores and shapes](https://vandyshge.github.io/PANDA_Package/geometries.html) |
| Fit a saved density profile and interpret the result | [Fitting](https://vandyshge.github.io/PANDA_Package/fitting.html) · [Angle recovery](https://vandyshge.github.io/PANDA_Package/validation.html) |
| Look up functions or commands | [Python API](https://vandyshge.github.io/PANDA_Package/api.html) · [Command line](https://vandyshge.github.io/PANDA_Package/cli.html) |

## Run the trajectory examples

Follow the [installation guide](https://vandyshge.github.io/PANDA_Package/installation.html#optional-dependencies) to install PANDA with the `md` and `plot` extras. Extract the [example archive](https://vandyshge.github.io/PANDA_Package/md-trajectory-examples.zip?v=10ns), then run either script from the extracted directory.

```sh
python md_gromacs.py
python md_lammps.py
```

Both scripts analyze the same 201 synthetic frames in different file formats. They write the full-trajectory block profiles, the averaged density profile, and a figure showing the density map, profile fit, and angle history. The [averaging guide](https://vandyshge.github.io/PANDA_Package/trajectory-averaging.html) explains the 2–10 ns window used in the example.

## Repository scope

This repository publishes the documentation site and its example data. The Python implementation and its installation requirements are in [PANDA_2.0](https://github.com/Ilya-Garanov-WorkingAcc/PANDA_2.0). The documentation targets the 0.1.0 alpha API. See the [citation page](https://vandyshge.github.io/PANDA_Package/citation.html) for the original method and related publications.

## Repository layout

| Path | Contents |
| --- | --- |
| [`docs/`](docs/) | Generated site published by GitHub Pages, including example downloads. |
| [`site-src/`](site-src/) | Page generator, stylesheet, figures, and example sources. |

To update the site, edit the files in `site-src/` and rebuild from the repository root.

```sh
python site-src/build.py --output docs
```

The site build uses the Python standard library. To regenerate the profile and validation figures, run `python site-src/plot_profile.py` with NumPy and Matplotlib installed, then rebuild the site. GitHub Pages publishes `main:/docs`.
