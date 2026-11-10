# Spyctres 0.5.0a1 user-manual erratum

## PHOENIX model-library layout

Date: 14 September 2026

This erratum supersedes the directory trees shown in sections 2.5 and B.1 of
the Spyctres 0.5.0a1 user manual.

Configure `phoenix_dir` as the `HiResFITS` library root containing the native
wavelength file. In the standard Göttingen layout, the stellar templates are
one level deeper:

```text
HiResFITS/
├── WAVE_PHOENIX-ACES-AGSS-COND-2011.fits
└── PHOENIX-ACES-AGSS-COND-2011/
    ├── Z-1.0/
    ├── Z-0.5/
    ├── Z-0.0/
    └── Z+0.5/
```

For example:

```toml
[paths]
phoenix_dir = "/path/to/HiResFITS"
```

Spyctres prefers this standard nested template tree. For backward
compatibility, it also accepts a flat installation whose ordinary `Z-*`
directories are directly under `HiResFITS`. If both trees are usable, they are
not merged: the nested tree wins deterministically.

Directories such as `Z-0.0.Alpha=+0.40` are alpha-enhanced grids. They are
excluded from the current ordinary `(Teff, [Fe/H], logg)` interpolator because
Spyctres does not yet expose `[alpha/Fe]` as an interpolation dimension.

Verify the complete installation, including template discovery, with:

```bash
spyctres doctor --require-phoenix
```

The `--skip-phoenix-scan` option deliberately checks only the configured root
and wavelength grid; it does not verify that templates can be discovered.

## Multi-segment continuum and X-SHOOTER masks

Date: 10 November 2026

In a joint `SpectrumCollection` PHOENIX fit, Spyctres shares
`Teff`, `[Fe/H]`, `logg`, and `rv_kms` across retained segments. It profiles a
separate multiplicative Legendre polynomial in every segment. For `J` retained
segments the complete fitted-parameter count is therefore:

| `mdeg` | Continuum freedom per segment | Total parameter count |
|---:|---|---:|
| 0 | normalization | `4 + J` |
| 1 | normalization and tilt | `4 + 2J` |
| 2 | normalization, tilt, and curvature | `4 + 3J` |
| 3 | normalization through cubic shape | `4 + 4J` |

The public `continuum_degree` argument is an alias for `mdeg`; do not pass both.
Fit reports now include per-segment continuum diagnostics under
`diagnostics.continuum_model`. The pivot factor, logarithmic slope/curvature,
factor range, and weighted residual contribution are evaluated from the full
polynomial. Individual Legendre coefficients should not be interpreted as
physical arm scales, particularly for degree 2 and above. These polynomials
correct continuum/model mismatch and do not determine an absolute SED or
angular radius. The absolute pivot factor is allowed to absorb arbitrary
observed/model flux normalization; scale-invariant shape excursions and
controlled relative-arm comparisons are more informative. Collection weights
alter the statistical likelihood; they are not flux-calibration factors.

The X-SHOOTER UVB/VIS and VIS/NIR dichroic regions are product-specific and are
not silently masked by readers. Use:

```python
import Spyctres as sp

mask = sp.build_mask(
    spectrum,
    xshooter_dichroics="warn",  # inspect first
    tellurics="warn",
)
```

Use `xshooter_dichroics="mask"` only when wavelength-frame provenance permits
an exact or recorded frame mapping. `"conservative"` explicitly accepts a
wider velocity-margin envelope when the mapping is unresolved and records that
choice as a quality flag. XSL DR3 is already arm-combined and corrected to the
stellar rest frame. Spyctres maps its warning/mask envelopes using the recorded
`REST_UVB`, `REST_VIS`, and `REST_NIR` corrections; the three effective-LSF
segments returned by the reader are not original independent arms.
