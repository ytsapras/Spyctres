# PHOENIX local-grid recovery: problem, fix, and validation

Date: 2026-11-11

Development branch: `feature/phoenix-backend`

Starting branch head for this work: `f5f2f92` (`Expand reference spectra for validation`)

## Executive summary

The PHOENIX fitter built a compact interpolation grid around the coarse starting
point but passed the broader user-requested physical bounds directly to the
optimizer. The optimizer could therefore request parameters outside the actual
interpolator domain. Those evaluations raised `ValueError`, were converted to a
large residual vector, and created artificial local-grid boundaries. The
diagnostics reported exact grid-edge hits but the fitter could not enlarge an
internally selected grid and restart.

The implementation now:

- keeps requested physical bounds, effective interpolation axes, installed
  PHOENIX axes, and active optimizer bounds distinct;
- intersects active physical optimizer bounds with the current effective
  interpolation cube, preventing out-of-grid optimizer evaluations;
- detects solutions within a configurable fraction of a grid-node spacing from
  an expandable edge;
- expands only internally selected grids, one installed node layer at a time;
- uses bounded stopping rules: two expansions and 300 rectangular templates by
  default, plus a minimum relative objective-improvement check;
- preserves explicit `teff_grid`, `feh_grid`, and `logg_grid` arguments exactly;
- records the requested/active bounds, initial/final axes, each solution and
  expansion, the selected iteration, and the stopping reason in
  `result["search_coverage"]`; and
- emits quality flags when expansion occurred or search coverage remains
  restricted or unresolved.

The fix removes the invalid-evaluation failure mode and automatically recovers
the low-gravity Arcturus solution when the broad metal-window experiment is
used. It does **not** make the default Arcturus windows recover the correct
parameters, and it does **not** solve the line-profile/model mismatch seen for
HD 16765. Those are separate scientific issues.

## Original problem

`fit_phoenix_full_spectrum()` previously performed these steps:

1. Select a sparse coarse physical starting point.
2. Build one compact local PHOENIX interpolator around that point.
3. Pass the original, often much broader, parameter bounds to
   `scipy.optimize.least_squares()`.
4. Catch out-of-grid `PhoenixLibrary.evaluate()` failures and return residuals
   of `1e6`.

The local interpolator and optimizer therefore did not share the same valid
domain. In the Arcturus broad-metal case, the internally chosen grid covered
only `logg = 2.5, 3.0, 3.5`, while the scientific bounds extended down to
`logg = 1.0`. The best local solution landed at `logg = 2.5`, and attempts to
move lower generated invalid model evaluations rather than a larger valid
interpolation grid.

This was a genuine engineering bug, but it was not the only source of the
Arcturus discrepancy. The fitted wavelength windows also had a strong and
independent effect.

## Pre-fix 2 x 2 Arcturus diagnosis

Reference parameters used only for post-fit comparison were:

- `Teff = 4277 K`
- `logg = 1.58`
- `[Fe/H] = -0.55`

| Window set | Grid policy | Teff (K) | logg | [Fe/H] | delta Teff (K) | delta logg | delta [Fe/H] | Reduced chi-square | Invalid model evaluations |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Default diagnostic windows | Automatic compact grid | 4876.4 | 2.642 | -0.006 | +599.4 | +1.062 | +0.544 | 5442.64 | 0 |
| Default diagnostic windows | Manually expanded low-gravity grid | 4876.1 | 2.641 | -0.007 | +599.1 | +1.061 | +0.543 | 5442.64 | 0 |
| Broad metal forest | Automatic compact grid | 4553.0 | 2.500 | -0.300 | +276.0 | +0.920 | +0.250 | 1742.67 | 36 |
| Broad metal forest | Manually expanded low-gravity grid | 4347.5 | 1.837 | -0.655 | +70.5 | +0.257 | -0.105 | 1651.29 | 0 |

Interpretation:

- Expanding the grid alone did not change the default-window solution.
- Changing to the broad metal windows improved the physical basin but exposed
  the artificial lower-logg grid boundary.
- Broad metal windows plus a valid low-gravity grid recovered Arcturus within
  the existing first-pass per-star tolerances.
- The raw or reduced chi-square values must not be compared directly between
  window families because the retained pixels and fitted wavelength domains
  differ.
- The manually expanded Arcturus run was a diagnosis, not an unbiased
  validation pass.

## Implemented behavior

### Bounds and grid-domain handling

The fitter now distinguishes:

- **Requested bounds**: the user's intended scientific search box.
- **Installed axes**: axes found in the local PHOENIX installation when an
  expansion is needed. If no expansion is needed, the filesystem scan is
  skipped and this is recorded explicitly.
- **Effective axes**: the rectangular grid used by the current interpolator.
- **Active optimizer bounds**: requested physical bounds intersected with the
  effective axes; RV bounds are unchanged.

The optimizer can no longer leave the current interpolation cube. This removes
the former dependence on large penalty residuals for ordinary boundary
handling.

### Bounded automatic expansion

The default `local_grid_policy="auto"` applies only when all three PHOENIX axes
were selected internally. After a local fit, an edge is considered for
expansion when the solution lies within `0.25` adjacent node spacings and the
requested physical bounds extend beyond that edge.

One installed node layer is added in each required direction. The candidate
axes must remain a complete rectangular subgrid, preserve the existing axes,
and remain within the default 300-template budget. The optimizer is restarted
from the preceding best solution. Expansion stops when:

- the solution is interior;
- the solution reaches a requested scientific bound;
- the installed grid has no farther node;
- no complete expanded rectangular subgrid exists;
- the template budget would be exceeded;
- the maximum of two expansion cycles is reached; or
- the relative objective improvement is below the configured threshold.

Explicit axes always have fixed-grid semantics and are never silently changed.
If broader requested bounds are supplied with an explicit smaller grid, the
active bounds are safely restricted and the result is flagged as incomplete
search coverage.

### Diagnostics and quality flags

`result["search_coverage"]` now records:

- requested and active bounds;
- initial and final effective axes;
- installed axes and their source when scanned;
- initial and final bound restrictions;
- per-iteration solution, chi-square, relative improvement, boundary distances,
  multistart results, and attempted nodes;
- selected iteration, expansion count, and stopping reason; and
- whether the final search is incomplete or an installed boundary remains.

New quality flags include:

- `local_grid_expanded`
- `local_grid_boundary_near`
- `explicit_grid_restricts_requested_bounds`
- `installed_grid_boundary`
- `incomplete_search_coverage`
- `local_grid_boundary_unresolved`

Descriptions, severity classifications, and recommended actions were added to
the public result-reporting layer.

## Synthetic and regression tests

Focused fast tests were added for:

1. intersecting requested bounds with effective interpolation axes;
2. distinguishing exact grid-edge hits from near-edge solutions;
3. two-step automatic expansion and recovery of a planted low-gravity
   synthetic spectrum;
4. zero invalid model evaluations during bounded recovery;
5. preserving explicit grids and flagging their restricted coverage;
6. avoiding expansion for an interior planted solution; and
7. stopping and flagging a true installed-grid boundary.

The planted recovery test begins with `logg = 2.5, 3.0, 3.5`, adds `2.0` and
then `1.5`, and recovers a planted `logg = 1.8` to within `0.03 dex`. The
explicit-grid version stays at `logg = 2.5`, does not rebuild the grid, and is
flagged instead of silently expanding.

Verification results:

| Command | Result |
|---|---|
| `conda run -n spyctres-dev-py312 python -m pytest -q tests/test_fitting_initialization.py` | 37 passed |
| `conda run -n spyctres-dev-py312 python -m pytest -q tests/test_phoenix_synthetic_recovery.py tests/test_recipes.py tests/test_public_api.py tests/test_serialization_helpers.py` | 62 passed, 1 expected sampling warning |
| `conda run -n spyctres-dev-py312 python -m pytest -q tests/test_fitting_initialization.py tests/test_phoenix_synthetic_recovery.py tests/test_public_api.py` | 84 passed, 1 expected sampling warning |
| `python -m py_compile Spyctres/fitting.py Spyctres/results.py` | Passed |
| `git diff --check` | Passed |
| `conda run -n spyctres-dev-py312 python -m pytest -q` | 467 passed, 2 failed, 15 warnings |

The two full-suite failures are unrelated to this patch. They are both in
`tests/test_numbered_examples.py` and are caused by pre-existing modified
notebooks that contain executed cell counts/output and absolute `/home/...`
warning paths. Those user-owned notebook changes were deliberately preserved.

## Required smoke tests

| Command | Result |
|---|---|
| `conda run -n spyctres-dev-py312 python scripts/phoenix_smoketest.py` | Passed; template load, 2 x 2 x 2 interpolation cube, cache rebuild/load, and identical cached output verified |
| `conda run -n spyctres-dev-py312 python scripts/fitting_smoketest.py` | Passed; recovered the planted synthetic parameters (`Teff=5044 K`, `[Fe/H]=-0.297`, `logg=4.296`, `RV=12.322 km/s`) with `chi2_red=1.184` |
| `conda run -n spyctres-dev-py312 python scripts/pepsi_fit_smoketest.py` | Not directly runnable because the current script requires an input file |
| `conda run -n spyctres-dev-py312 python scripts/pepsi_fit_smoketest.py --fast --no-show examples/data/pepsir.20230603.010.dxt.nor` | Passed as the input-file fallback; the workflow completed fitting, reconstruction, and quality reporting |

## Post-fix Arcturus validation

### Default-window negative control

The post-fix default-window run produced:

- `Teff = 4876.18 K`
- `logg = 2.6412`
- `[Fe/H] = -0.0064`
- `chi2_red = 5442.64`
- zero expansions
- zero invalid model evaluations
- stopping reason: `interior_solution`

This is intentionally important: the algorithm did not expand a grid merely
because the external reference disagreed. The optimizer was interior to the
effective grid, so the wrong default-window physical basin remains visible as a
window/model issue.

### Broad-metal automatic recovery

The same general automatic policy, without an explicit Arcturus grid, produced:

- `Teff = 4347.44 K` (`delta = +70.44 K`)
- `logg = 1.8372` (`delta = +0.2572 dex`)
- `[Fe/H] = -0.6553` (`delta = -0.1053 dex`)
- `chi2_red = 1651.29`
- two expansion cycles
- zero invalid model evaluations
- stopping reason: `interior_solution`
- no incomplete-coverage flag

The expansion history was:

| Iteration | Teff (K) | [Fe/H] | logg | Chi-square | Action |
|---:|---:|---:|---:|---:|---|
| 0 | 4526.83 | -0.3586 | 2.5000 | 133,274,150 | Add `logg=2.0` |
| 1 | 4428.80 | -0.5000 | 2.0923 | 128,233,513 | Add `[Fe/H]=-1.0` and `logg=1.5` |
| 2 | 4347.44 | -0.6553 | 1.8372 | 126,650,405 | Interior solution; stop |

The effective grid changed from:

- `Teff: 4300--5100 K` (9 nodes)
- `[Fe/H]: -0.5--+0.5` (3 nodes)
- `logg: 2.5--3.5` (3 nodes)

to:

- `Teff: 4300--5100 K` (9 nodes)
- `[Fe/H]: -1.0--+0.5` (4 nodes)
- `logg: 1.5--3.5` (5 nodes)

This reproduces the successful manually expanded diagnosis through a general,
bounded rule.

## Twelve-star Gaia benchmark run

The general automatic policy was then run on all 12 bundled Gaia benchmark
targets using the `broad_metal_forest` sensitivity window set. Literature
parameters were used only after fitting to calculate deltas. No target-specific
grid or initialization was used.

| Target | Validation role | Teff (K) | delta Teff (K) | logg | delta logg | [Fe/H] | delta [Fe/H] | Assessment | Expansions | Stop reason | Incomplete | Invalid evals |
|---|---|---:|---:|---:|---:|---:|---:|---|---:|---|---|---:|
| Procyon | standard | 6163.6 | -418.4 | 2.790 | -1.190 | -0.718 | -0.688 | review | 1 | interior solution | no | 0 |
| Arcturus | standard | 4347.4 | +70.4 | 1.837 | +0.257 | -0.655 | -0.105 | within first-pass tolerance | 2 | interior solution | no | 0 |
| HD 140283 | metal-poor stress | 6393.6 | +605.6 | 5.080 | +1.330 | -2.000 | +0.410 | outside review tolerance | 1 | interior solution | no | 0 |
| 18 Sco | standard | 5900.0 | +76.0 | 4.633 | +0.213 | -0.136 | -0.196 | within first-pass tolerance | 2 | maximum expansions | **yes** | 0 |
| HD 195564 | standard | 5800.0 | +286.0 | 4.147 | +0.197 | -0.121 | -0.081 | within first-pass tolerance | 2 | maximum expansions | **yes** | 0 |
| HD 16765 | standard | 6453.9 | +143.9 | 5.500 | +1.140 | -1.000 | -0.890 | review | 1 | requested boundary | no | 0 |
| Epsilon Fornacis | reference flagged | 5300.0 | +157.0 | 4.136 | +0.606 | -0.622 | -0.062 | review | 2 | maximum expansions | **yes** | 0 |
| 55 Cancri | standard | 5232.6 | +63.6 | 4.556 | +0.146 | +0.149 | -0.131 | within first-pass tolerance | 0 | interior solution | no | 0 |
| HD 79210 | cool-edge stress | 4007.0 | +10.0 | 5.000 | +0.310 | -0.601 | -0.071 | within first-pass tolerance | 1 | requested boundary | no | 0 |
| Mu Leonis | standard | 4616.7 | +97.7 | 2.597 | +0.167 | +0.158 | -0.032 | within first-pass tolerance | 0 | interior solution | no | 0 |
| HD 102200 | metal-poor stress | 6100.0 | -105.0 | 4.504 | +0.234 | -1.275 | -0.135 | within first-pass tolerance | 0 | interior solution | no | 0 |
| HD 182572 | standard | 5551.8 | -121.2 | 4.334 | +0.114 | +0.048 | -0.332 | within first-pass tolerance | 0 | interior solution | no | 0 |

All 12 workflows completed and all had zero invalid model evaluations. Of the
eight ordinary standards, six met the current first-pass per-star tolerances and
two required review. `status="ok"` in the runner means that optimization and
report generation completed; it is not itself a statement of scientific
accuracy.

For the eight ordinary standards, the original runner reported the following
legacy aggregate quantities. The column originally called `median_abs_bias`
is the absolute value of the median signed error, not the median absolute
error; the label is corrected here to avoid that ambiguity.

| Parameter | Absolute median signed error | Median absolute error | Robust scatter | Reporting target status |
|---|---:|---:|---:|---|
| Teff | 73.2 K | 109.5 K | 70.5 K | Meets target |
| logg | 0.182 dex | 0.205 dex | 0.078 dex | Median signed-error target not met |
| [Fe/H] | 0.164 dex | 0.164 dex | 0.159 dex | Median signed-error target not met |

The complete corrected statistics and reliability cross-tab are documented in
`reliable_fitting_followup_2026-11-12.md`.

The stress and reference-flagged targets remain separate from ordinary
aggregate statistics. In particular, HD 140283 remains outside review
tolerance, and the expansion-capped results for 18 Sco, HD 195564, and Epsilon
Fornacis must retain their incomplete-coverage warnings even when their
parameter deltas look acceptable.

Reduced chi-square remains very high for most high-S/N standards. Parameter
recovery and formal fit quality are therefore reported separately; the current
local covariance errors do not include model, continuum, line-list, abundance,
LSF, or reduction systematics.

## HD 16765 follow-up

The default-window result before this fix was:

- `Teff = 6234.3 K`
- `logg = 5.0000`
- `[Fe/H] = -0.9530`
- `chi2_red = 40.73`
- 23 invalid model evaluations

After the fix, the default-window run expanded once from `logg = 4.0--5.0` to
`4.0--5.5` and produced:

- `Teff = 6364.4 K` (`delta = +54.4 K`)
- `logg = 5.5000` (`delta = +1.14 dex`)
- `[Fe/H] = -0.9242` (`delta = -0.8142 dex`)
- `chi2_red = 35.90`
- zero invalid model evaluations
- stopping reason: requested upper boundary

This fixes the domain error and modestly lowers chi-square, but it does not
resolve the scientific failure. The result remains flagged with
`grid_edge_logg_high`, `fit_bound_hit`, high chi-square, structured residuals,
and a near-grid-boundary warning.

The line-window diagnostic confirms the earlier visual assessment:

- the Na I D model profiles are too sharp/deep relative to the observations;
- the Ca I 6162 and 6439 windows have no model trace in the default fit because
  they are outside the retained default fit pixels, so they cannot constrain
  that solution;
- H-alpha still shows coherent profile/continuum mismatch; and
- broad metal windows include the Ca regions but do not solve the Ca profile
  mismatch or recover the reference gravity/metallicity.

Increasing the grid blindly beyond the requested `logg=5.5` bound is therefore
not justified. The next HD 16765 tests should separate rotational/macroturbulent
broadening and LSF mismatch from abundance/line-list limitations, then compare
parameter recovery on common held-out wavelength pixels.

## Scientific conclusions and remaining work

1. **The local-grid domain bug is fixed.** Optimizers no longer leave the
   effective interpolation cube, and all post-fix real-spectrum runs reported
   zero invalid PHOENIX evaluations.
2. **Bounded expansion is useful and appropriately selective.** It recovers the
   broad-window Arcturus solution while leaving the wrong-but-interior default
   solution unchanged.
3. **Window selection remains scientifically important.** Grid recovery alone
   cannot repair the default Arcturus basin.
4. **A successful optimizer is not an accuracy validation.** Procyon and
   HD 16765 remain review cases; HD 140283 remains a stress-case failure; three
   targets hit the expansion cap.
5. **Line-profile systematics remain.** Continuum underestimation, Ca mismatch,
   overly sharp Na profiles, and Balmer-wing mismatch require tests of LSF,
   rotation/macroturbulence, continuum assumptions, masks, and PHOENIX model
   limitations.
6. **Raw chi-square across different masks/windows is not a model-selection
   statistic.** Future comparisons should report retained pixels, degrees of
   freedom, per-region residual structure, and prediction on a common held-out
   wavelength set.
7. **The manually tailored Arcturus grid must not be counted as an independent
   benchmark pass.** The post-fix automatic broad-window result is the relevant
   general-algorithm demonstration, and the 12-star run is the broader check.

The evidence supports retaining the validation-first approach. It does not yet
justify linked-arm continuum constraints, automatic stitching, or physical SED
fitting. Those additions should outperform the current independent per-segment
Legendre treatment on predefined held-out prediction or external-parameter
recovery tests, not merely lower in-sample chi-square.

## Generated validation artifacts

The one-off validation artifacts were intentionally kept outside the repository:

- `/tmp/spyctres_arcturus_auto_default_postfix.json`
- `/tmp/spyctres_arcturus_auto_expand.json`
- `/tmp/spyctres_gbs_auto_expand_broad.json`
- `/tmp/spyctres_gbs_auto_expand_broad.csv`
- `/tmp/spyctres_gbs_auto_expand_broad.png`
- `/tmp/spyctres_hd16765_auto_default.json`
- `/tmp/spyctres_hd16765_auto_default_lines/HIP12530_default_line_windows.png`

The maintained validation runner and package tests are sufficient to reproduce
the analyses; no target-specific temporary script was added to the repository.
