# Response to the referee recommendations on reliable PHOENIX fitting

Date: 2026-11-13

Repository branch: `feature/phoenix-backend`

Relevant commits:

- `d01654b` — `Bound and expand local PHOENIX grids`
- `2b57361` — `Correct benchmark reliability reporting`

Pull request status: PR #3 remains a draft.

## Executive summary

The referee identified several genuine issues in the PHOENIX fitting and
validation workflow. I divided them into two categories:

1. correctness and reporting problems that should be fixed immediately; and
2. scientific extensions that require controlled experiments before they are
   included in the default fitter.

The immediate problems have now been addressed. In particular:

- the optimizer can no longer move outside the active PHOENIX interpolation
  grid;
- internally selected local grids can expand in a bounded and auditable way;
- explicit user grids remain fixed;
- incomplete local-search coverage is reported rather than hidden;
- benchmark statistics now distinguish signed bias from absolute error and
  report tail failures;
- optimizer completion, parameter recovery, grid coverage, residual quality,
  identifiability, and scientific review are treated as separate questions;
- robust-loss candidates are ranked using the objective minimized by SciPy;
  and
- the continuum treatment in robust mode is explicitly described as a hybrid
  L2-profiled continuum with a robust outer objective.

These changes resolve the engineering defects raised by the referee, but they
do not establish that the current stellar classifications are scientifically
reliable across the full parameter space. Procyon and HD 16765 remain clear
failure cases. Two otherwise acceptable benchmark results remain provisional
because their local searches reached the expansion limit. The next phase must
therefore focus on feature selection, line-profile mismatch, parameter
identifiability, and independent holdout validation rather than adding more
complexity to the public API.

## 1. Original fitting problem

The PHOENIX fitter first selected a compact interpolation grid around a coarse
starting point, but then gave the optimizer the broader user-requested
parameter bounds. The optimizer could consequently request a model outside the
interpolation domain. Those evaluations failed and were converted to large
penalty residuals.

This produced two undesirable effects:

- the local interpolation boundary behaved like an artificial physical
  boundary; and
- the fit could appear to terminate normally even though a scientifically
  relevant part of the requested search region had not been explored.

Arcturus demonstrated the problem particularly clearly. The broad-metal fit
wanted to move below the initial `logg=2.5` grid edge, but the compact
interpolator did not cover the lower-gravity region. Manually supplying a wider
grid recovered a substantially better solution, showing that the limitation
was caused by the fitting machinery rather than the requested scientific
bounds.

## 2. Bounded local-grid recovery

The grid-domain problem was corrected in commit `d01654b`.

The fitter now distinguishes four concepts:

- **requested bounds**: the scientific search region requested by the user;
- **installed axes**: the PHOENIX nodes available locally;
- **effective axes**: the nodes currently used by the interpolator; and
- **active optimizer bounds**: the intersection of the requested bounds and
  the current interpolation domain.

The optimizer therefore remains inside a valid interpolation cube. When the
grid was selected internally and the solution approaches an artificial grid
edge, the fitter can add one installed node layer and restart from the previous
solution. Expansion is bounded by:

- the requested scientific limits;
- the installed PHOENIX grid;
- rectangular-subgrid completeness;
- a template-count budget;
- a maximum number of expansions; and
- a minimum relative objective improvement.

Explicit `teff_grid`, `feh_grid`, and `logg_grid` arguments are never silently
expanded. If an explicit grid is narrower than the requested search region,
the fit proceeds safely inside that grid and reports incomplete search
coverage.

The fit result records the initial and final axes, active bounds, boundary
distances, expansion attempts, per-iteration solutions and objectives,
selected iteration, stopping reason, and whether the final coverage is
incomplete.

### Validation of the grid correction

The synthetic and regression tests cover:

- intersection of requested bounds with effective interpolation bounds;
- exact and near-edge solutions;
- two-step recovery of a planted low-gravity spectrum;
- explicit fixed-grid behavior;
- interior solutions that should not trigger expansion;
- true installed-grid boundaries;
- the maximum-expansion limit;
- the template budget;
- a requested physical boundary;
- an incomplete rectangular subgrid; and
- a wrong-but-interior solution whose external label disagrees with the fitted
  minimum.

The planted low-gravity case begins with `logg=2.5, 3.0, 3.5`, expands twice,
and recovers the planted `logg=1.8` solution to within `0.03 dex`, without an
invalid PHOENIX evaluation.

The wrong-but-interior test is equally important. It confirms that the fitter
does not expand merely because an external reference value disagrees with the
result. Grid expansion is a coverage mechanism, not a mechanism for steering a
fit toward a desired literature value.

## 3. Arcturus: what was fixed and what was not

With the bounded-grid correction, the broad-metal Arcturus fit automatically
recovered:

- `Teff = 4347 K`;
- `logg = 1.837`;
- `[Fe/H] = -0.655`;
- two grid expansions; and
- zero invalid PHOENIX evaluations.

The reference values used only after fitting were `4277 K`, `1.58`, and
`-0.55`, respectively.

However, the default-window Arcturus fit remained near:

- `Teff = 4876 K`;
- `logg = 2.64`; and
- `[Fe/H] = -0.01`.

That solution is interior to its local grid. A wider interpolation grid does
not materially alter it. This establishes that the remaining default-window
failure is not the original grid-domain bug. It is more likely related to the
information in the selected features, continuum treatment, model mismatch, or
another physical degeneracy.

The broad-metal result is therefore a successful engineering recovery and a
useful development case, but it must not be treated as independent validation
of a universal broad-metal policy. The same broad-metal selection performs
poorly for Procyon.

## 4. Correction of benchmark statistics

The referee correctly noted that the old `median_abs_bias` field was computed
as:

```text
abs(median(fit - reference))
```

This is the absolute median signed error, not the median absolute error. Large
positive and negative errors can therefore cancel and give a misleadingly
small value.

The Gaia benchmark runner now reports:

- median signed error;
- absolute median signed error;
- median absolute error;
- mean absolute error;
- RMSE;
- robust scatter;
- 90th-percentile absolute error;
- maximum absolute error;
- tail-outlier count and fraction;
- the identities and errors of tail outliers; and
- the number of records considered and missing reference values.

For backward compatibility, `median_bias` remains an alias for the median
signed error. `median_abs_bias` retains its historical numerical definition,
but is explicitly marked as a deprecated alias for
`abs_median_signed_error`. Its target metadata now states which metric is
actually being tested. Existing serialized consumers therefore do not receive
a silent change in meaning.

A regression test uses two gravity residuals of `+0.8` and `-0.8 dex`. The
median signed error is zero, while the median absolute error, mean absolute
error, RMSE, and maximum absolute error are all `0.8 dex`. Both stars are
correctly identified as tail failures.

## 5. Separation of reliability states

The previous reporting could too easily be read as though a completed fit or a
loose parameter-tolerance pass implied scientific reliability. The JSON and
CSV outputs now report the following separately:

- optimizer success;
- parameter-tolerance assessment;
- local-search coverage;
- formal residual-quality assessment;
- identifiability assessment;
- combined recovery-readiness assessment; and
- scientific-review status.

A parameter-tolerance pass with incomplete search coverage is now labeled
`provisional_within_tolerance_incomplete_search`.

The runner does not claim that a local covariance matrix establishes
identifiability. It reports either `not_assessed` or
`not_established_local_covariance_only`. It also records
`not_reviewed_by_runner` until a result has undergone an explicit scientific
review.

The historical `overall_assessment` field is retained for compatibility, but
its meaning is now clearly limited to the parameter-tolerance comparison.

## 6. Robust objective and continuum profiling

The referee also identified a real inconsistency in robust fitting. SciPy's
`least_squares` minimizes the robust objective stored as half of
`result.cost`, whereas the fitter selected multistart candidates using
`sum(result.fun**2)`. These are equivalent for the default linear loss, but
they need not rank solutions in the same order for `soft_l1`, Huber, Cauchy, or
arctangent losses.

The following decisions now use `2*result.cost`:

- selection among local multistart candidates;
- selection among expanded-grid iterations; and
- the relative objective-improvement expansion criterion.

Raw chi-square is still calculated and reported as a separate diagnostic. A
unit test constructs two candidate solutions whose ordinary L2 and robust-cost
rankings are opposite and confirms that the robust objective selects the
correct candidate.

The multiplicative Legendre continuum is still profiled using weighted linear
least squares. When a robust outer loss is requested, diagnostics now describe
the calculation as `hybrid_l2_profiled_robust_outer`. This is intentionally
conservative: the result is not presented as a fully robust likelihood, and
its local covariance is not presented as a calibrated uncertainty estimate.

The default remains ordinary linear least squares, so existing default
workflows retain their previous objective.

## 7. Revised Gaia benchmark interpretation

The existing 12 fitted benchmark records were passed through the runner's
resume path. They were not refitted or initialized from their reference
parameters. The JSON, CSV, and summary plot were regenerated using the
corrected definitions.

For the eight ordinary standards:

| Parameter | Median signed error | Median absolute error | Mean absolute error | RMSE | Robust scatter | Maximum absolute error | Tail outliers |
|---|---:|---:|---:|---:|---:|---:|---:|
| Teff | +73.2 K | 109.5 K | 159.7 K | 198.9 K | 70.5 K | 418.4 K | 0 above 500 K |
| logg | +0.182 dex | 0.205 dex | 0.428 dex | 0.605 dex | 0.078 dex | 1.190 dex | 2 above 0.5 dex |
| [Fe/H] | -0.164 dex | 0.164 dex | 0.307 dex | 0.426 dex | 0.159 dex | 0.890 dex | 2 above 0.5 dex |

The `logg` and `[Fe/H]` tail outliers are Procyon and HD 16765.

The recovery and coverage cross-tab is:

| Parameter-tolerance result | Resolved local search | Incomplete local search |
|---|---:|---:|
| Within first-pass tolerance | 4 | 2 |
| Review | 2 | 0 |

The earlier statement that six of eight ordinary standards met the first-pass
tolerance remains numerically true, but is incomplete. The more accurate
description is:

- four standards pass the current tolerance with resolved local search;
- 18 Sco and HD 195564 pass the tolerance provisionally because the expansion
  limit was reached; and
- Procyon and HD 16765 require review despite resolved local-search coverage.

The sample is too small and too involved in development to establish a general
classification-accuracy claim.

## 8. HD 16765 and the remaining line-profile problem

Removing the grid-domain failure eliminated invalid PHOENIX evaluations for
HD 16765, but did not produce a scientifically acceptable result. The fit
moves to the requested upper gravity boundary and remains strongly discrepant
in metallicity.

The observed/model comparison suggests:

- Na I D model profiles are too sharp;
- Ca I features are not reproduced adequately; and
- coherent continuum or H-alpha residuals remain.

This is not evidence that the requested gravity bounds should simply be made
wider. The next diagnostic must determine whether the mismatch is specific to
Na/Ca line physics and abundances, or is also present in weak Fe and Mg lines.
Only the latter would support adding a more general broadening term. Additional
rotation, macroturbulence, or LSF parameters should not be introduced before
this distinction is made quantitatively.

## 9. Verification performed

All verification used the `spyctres-dev-py312` conda environment.

| Command | Result |
|---|---|
| `conda run -n spyctres-dev-py312 python -m pytest tests/test_fitting_initialization.py tests/test_gaia_benchmark_validation.py -q` | 53 passed |
| `conda run -n spyctres-dev-py312 python -m pytest -q` | 474 passed, 2 failed, 15 warnings |
| `conda run -n spyctres-dev-py312 python -m py_compile Spyctres/fitting.py scripts/gaia_benchmark_validation.py tests/test_fitting_initialization.py tests/test_gaia_benchmark_validation.py` | Passed |
| `git diff --check` | Passed |
| `conda run -n spyctres-dev-py312 python scripts/phoenix_smoketest.py` | Passed |
| `conda run -n spyctres-dev-py312 python scripts/fitting_smoketest.py` | Passed; planted parameters recovered with `chi2_red=1.184` |
| `conda run -n spyctres-dev-py312 python scripts/pepsi_fit_smoketest.py --fast --no-show examples/data/pepsir.20230603.010.dxt.nor` | Passed; fitting, reconstruction, and quality reporting completed |
| `conda run -n spyctres-dev-py312 python scripts/gaia_benchmark_validation.py --run-fits --window-set broad_metal_forest --output-json /tmp/spyctres_gbs_auto_expand_broad.json --output-csv /tmp/spyctres_gbs_auto_expand_broad.csv --output-summary-plot /tmp/spyctres_gbs_auto_expand_broad.png --resume` | Passed; 12 completed records resumed and revised summaries written |

The two full-suite failures are unrelated to these changes. They are both in
`tests/test_numbered_examples.py` and are caused by pre-existing modified
notebooks containing execution counts, cell outputs, and absolute `/home/...`
warning paths. Those user-owned notebook modifications were preserved.

The regenerated benchmark artifacts are currently local, temporary products:

- `/tmp/spyctres_gbs_auto_expand_broad.json`
- `/tmp/spyctres_gbs_auto_expand_broad.csv`
- `/tmp/spyctres_gbs_auto_expand_broad.png`

## 10. What was deliberately not changed

The following were not changed because the current evidence does not yet
justify making them package defaults:

- the public diagnostic-window policy;
- the default linear least-squares loss;
- the multiplicative Legendre continuum model;
- the public classification API;
- the constant-LSF workflow;
- linked-arm continuum constraints;
- spectrum stitching or physical SED fitting;
- multi-basin optimization;
- Gaussian-process residual covariance;
- PHOENIX emulators or compression; and
- active fitting of wavelength-dependent LSF parameters.

No target-specific workaround was added to the public fitter. The development
examples and legacy compatibility layer remain in place.

## 11. Recommended next steps

### Phase 1: diagnose the current failures

#### 1. Procyon and Arcturus feature-family comparison

Run a controlled comparison of Balmer, Mg/metal, Fe-rich, and combined feature
families for Procyon and Arcturus.

Requirements:

- use identical physical bounds, initialization policy, grid-expansion policy,
  continuum degree, loss, and masks wherever possible;
- keep feature-selection pixels separate from a common held-out evaluation
  set;
- report retained pixels, degrees of freedom, residual structure, reference
  deltas, and local-search coverage;
- do not select a universal window family from in-sample chi-square alone; and
- retain both stars as development cases rather than calling the result an
  independent validation.

Decision criterion: a proposed feature policy must improve held-out prediction
and parameter recovery for both the appropriate stellar classes without
creating a new Procyon-like failure.

#### 2. HD 16765 line-family and line-width diagnosis

Measure line centers, widths or second moments, equivalent widths, and residual
morphology for Na, Ca, Fe, and Mg features in the same spectrum.

Decision criterion:

- a mismatch confined mainly to Na/Ca should be treated as a line-physics,
  abundance, blend, or interstellar-contamination problem;
- a consistent width mismatch across multiple weak metal lines would justify
  a controlled fixed-broadening sensitivity test; and
- a new fitted broadening parameter should be considered only if synthetic
  recovery and control-star tests show that it is identifiable and does not
  absorb atmospheric-parameter errors.

#### 3. Synthetic continuum and corruption tests

Extend synthetic recovery tests to include:

- multiplicative scale and tilt;
- disconnected line regions;
- unequal uncertainties;
- corrupted arm or segment edges;
- shallow and saturated lines;
- correlated residual structure; and
- deliberately incorrect line strengths.

Decision criterion: any alternative continuum treatment must improve known
parameter recovery and common held-out prediction, not only reduce in-sample
chi-square.

### Phase 2: quantify identifiability and basin sensitivity

#### 4. Profile-likelihood diagnostics

For Procyon, Arcturus, and HD 16765, calculate targeted profiles in
`(Teff, logg)` and `(logg, [Fe/H])`, re-profiling the continuum at every point.
Report one-sided or unsupported intervals at physical or grid boundaries.

Decision criterion: do not report ordinary two-sided Gaussian uncertainties
where the profile is multimodal, boundary-limited, or too flat to establish
the parameter.

#### 5. Multi-basin go/no-go experiment

Test a small number of separated coarse candidates, each with its own valid
local interpolation cube and bounded expansion.

Decision criterion: multi-basin fitting should remain opt-in unless it finds
genuinely better supported minima in synthetic or held-out tests at acceptable
runtime and memory cost. If all basins prefer the same scientifically wrong
solution, effort should return to feature selection and model physics.

### Phase 3: reserve and evaluate an independent holdout sample

Prepare a quality-audited inventory of approximately 16–24 untouched GBSv3
stars, excluding all current development targets. Record:

- target and product identifiers;
- stellar class and proposed validation role;
- reference values and uncertainties;
- spectrograph, resolution, wavelength convention, and frame;
- S/N and product-quality flags;
- rotation, activity, binarity, unusual-abundance, and reference-quality
  cautions;
- source URLs, release/version identifiers, and checksums; and
- expected download volume.

The feature/window and reliability policy should then be frozen before a
prioritized subset is downloaded and evaluated. Multiple observations of one
star must be grouped by star and must not be split between development and
holdout sets.

Decision criterion: the holdout evaluation must report parameter errors,
catastrophic-tail fractions, incomplete-search rates, residual flags,
abstention/review rates, and the fraction of incorrect but apparently secure
results. No post-hoc change based on a holdout failure should be counted as
independent validation on that same star.

### Phase 4: return to multi-arm X-SHOOTER development

Only after the single-spectrum reliability policy is better established should
the work return to linked-arm continua, arm stitching, or physical SED fitting.
The existing independent per-arm Legendre model should remain the baseline.

Decision criterion: a linked-arm model must outperform that baseline in
predefined parameter-recovery or held-out prediction tests. A smaller
in-sample chi-square is not sufficient.

## 12. Proposed development order

The recommended order is therefore:

1. Procyon/Arcturus feature-family experiment;
2. HD 16765 line-family and width diagnosis;
3. synthetic continuum and corruption tests;
4. targeted profile-likelihood analysis;
5. multi-basin go/no-go experiment, only if still warranted;
6. external GBSv3 holdout inventory and reservation;
7. freeze the candidate method;
8. run the independent holdout evaluation once; and
9. revisit linked-arm X-SHOOTER continua and stitching.

## 13. Current conclusion

The bounded-grid and robust-objective corrections should be retained. They fix
real numerical and reporting defects without changing the public default
workflow or steering fits toward literature labels.

The current evidence does not yet justify describing Spyctres as a generally
validated stellar-classification system. It does justify a more precise
statement: the fitting machinery now recognizes and reports several important
failure modes more honestly, and the remaining scientific problems are narrow
enough to test with controlled experiments.

PR #3 should remain in draft until the feature-family policy, identifiability
behavior, and independent holdout strategy have been evaluated. Further
reviewer feedback would be especially useful on:

- the proposed feature families and held-out wavelength regions;
- the diagnostic thresholds used for catastrophic errors;
- the quality criteria for the untouched GBSv3 cohort; and
- the minimum evidence required before introducing a new broadening or
  multi-basin fitting option.
