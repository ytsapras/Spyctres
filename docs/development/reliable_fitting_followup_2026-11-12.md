# Reliable PHOENIX fitting follow-up: implemented corrections and results

Date: 2026-11-12

Development branch: `feature/phoenix-backend`

Reviewed starting head: `d01654b` (`Bound and expand local PHOENIX grids`)

## Summary

The referee recommendations were appropriate, but they divide naturally into
two groups. The benchmark-reporting error, robust-objective selection error,
and remaining bounded-grid regression cases directly affect correctness and
have been addressed now. The proposed feature-family experiments, line-width
diagnostics, profile likelihoods, multi-basin search, and untouched external
sample are scientifically useful follow-up studies; they should remain
experimental until they outperform the current method on predefined held-out
tests.

This pass made three main corrections:

1. Benchmark reports now distinguish signed bias from absolute error and show
   tail failures rather than allowing positive and negative errors to cancel.
2. Benchmark status now separates optimizer completion, parameter tolerance,
   local-grid coverage, formal residual quality, identifiability evidence, and
   scientific review.
3. Robust-loss multistart and grid-iteration selection now use the objective
   minimized by SciPy, while retaining raw chi-square as a separate diagnostic.

The existing bounded-grid implementation was retained. Its remote-state caveat
in the referee document is no longer applicable: `d01654b` was already present
both locally and on `origin/feature/phoenix-backend` before this follow-up.

## Original problem

The initial PHOENIX failure was a mismatch between the user-requested physical
bounds and the compact local interpolation grid. The optimizer could move
outside the interpolator, where model evaluation failed and returned a large
penalty residual. This produced artificial boundaries and prevented the
low-gravity Arcturus solution from being explored.

The bounded-grid fix at `d01654b` separates requested bounds, installed
PHOENIX axes, effective interpolation axes, and active optimizer bounds. It can
expand an internally selected grid by installed node layers, but preserves an
explicit user grid. It records the full search coverage and flags unresolved
coverage. The broad-metal Arcturus fit then recovers `logg=1.837` with no
invalid PHOENIX evaluations, whereas the default-window Arcturus fit remains a
wrong but interior solution. This distinction is important: grid coverage is
an engineering safeguard, not a proof that the fitted spectral information or
forward model is scientifically adequate.

## Changes made in this follow-up

### Correct benchmark statistics

The old field called `median_abs_bias` was calculated as
`abs(median(fit-reference))`. That is not the median absolute error and can be
small when large positive and negative errors cancel.

The runner now reports unambiguous quantities:

- `median_signed_error`
- `abs_median_signed_error`
- `median_absolute_error`
- `mean_absolute_error`
- `rmse`
- `robust_scatter`
- 90th-percentile absolute error
- maximum absolute error
- fixed-threshold tail counts, fractions, and named outliers
- the number of records considered and the number missing a reference value

For serialized compatibility, `median_bias` remains an alias for
`median_signed_error`, and `median_abs_bias` retains its historical meaning as
an explicitly deprecated alias for `abs_median_signed_error`. Existing
aggregate target checks therefore do not silently change semantics.

The regression fixture includes two `logg` errors of `+0.8` and `-0.8 dex`.
Their median signed error and absolute median signed error are both zero, while
the median absolute error, mean absolute error, RMSE, and maximum absolute
error are all `0.8 dex`. Both stars are correctly counted as tail outliers.

### Separate reliability states

The benchmark JSON and CSV now report the following independently:

- optimizer success;
- parameter-tolerance assessment;
- local-search coverage (`resolved`, `incomplete`, or `not_reported`);
- formal fit-quality assessment;
- identifiability assessment;
- combined recovery-readiness assessment; and
- scientific review status.

The runner deliberately labels identifiability as either `not_assessed` or
`not_established_local_covariance_only`. It does not convert a local covariance
matrix into a claim of parameter identifiability. It also labels every result
as `not_reviewed_by_runner` until a scientific review is performed.

A tolerance pass with incomplete grid coverage is now
`provisional_within_tolerance_incomplete_search`, rather than an unqualified
pass. The historical `overall_assessment` field remains available but is
documented as a parameter-tolerance assessment only.

### Correct robust-objective selection

SciPy's `least_squares` stores half of its minimized robust objective in
`result.cost`. The fitter previously ranked multistart candidates and expanded
grid iterations by `sum(result.fun**2)`. Those rankings agree for the default
linear loss but need not agree for `soft_l1`, Huber, Cauchy, or arctangent
losses.

Candidate selection, expanded-grid iteration selection, and the relative
objective-improvement stopping rule now use `2*result.cost`. This has the same
scale as chi-square for linear least squares and the correct ranking for robust
losses. Raw chi-square remains separately reported.

The diagnostics now state that robust mode is a
`hybrid_l2_profiled_robust_outer` objective: the nonlinear outer optimization
uses the requested robust loss, while the multiplicative Legendre continuum is
still profiled by weighted linear least squares. No claim is made that this is
a fully robust likelihood or that its local covariance is calibrated.

### Complete the bounded-grid stop tests

Additional synthetic regression cases now cover:

- reaching the maximum number of grid expansions;
- refusing an expansion that exceeds the template budget;
- stopping at a user-requested physical boundary without calling coverage
  incomplete;
- refusing an incomplete rectangular subgrid and flagging unresolved
  coverage; and
- retaining a wrong-but-interior solution when an external reference label
  disagrees, demonstrating that grid expansion is not driven by the label.

The pre-existing tests still cover two-step low-gravity recovery, explicit
fixed grids, no expansion for an interior solution, installed-grid boundaries,
near-edge detection, and active-bound intersection.

## Revised 12-star benchmark interpretation

The existing 12 fitted records were not refitted. They were loaded through the
runner's resume path and their JSON, CSV, and summary plot were regenerated
with the corrected metric and status definitions. The eight ordinary standards
give:

| Parameter | Median signed error | Median absolute error | Mean absolute error | RMSE | Robust scatter | Maximum absolute error | Tail outliers |
|---|---:|---:|---:|---:|---:|---:|---:|
| Teff | +73.2 K | 109.5 K | 159.7 K | 198.9 K | 70.5 K | 418.4 K | 0 above 500 K |
| logg | +0.182 dex | 0.205 dex | 0.428 dex | 0.605 dex | 0.078 dex | 1.190 dex | 2 above 0.5 dex |
| [Fe/H] | -0.164 dex | 0.164 dex | 0.307 dex | 0.426 dex | 0.159 dex | 0.890 dex | 2 above 0.5 dex |

The `logg` and `[Fe/H]` tail outliers are Procyon and HD 16765. The median
signed quantities alone substantially understate the typical and worst-case
errors, particularly for `logg`.

The status cross-tab is now:

| Parameter-tolerance result | Resolved local search | Incomplete local search |
|---|---:|---:|
| Within first-pass tolerance | 4 | 2 |
| Review | 2 | 0 |

Accordingly, the six former first-pass tolerance results should be described
as four resolved local-search passes and two provisional results. The two
provisional stars are 18 Sco and HD 195564. Procyon and HD 16765 remain review
cases even though their local search coverage is resolved.

The regenerated temporary artifacts are:

- `/tmp/spyctres_gbs_auto_expand_broad.json`
- `/tmp/spyctres_gbs_auto_expand_broad.csv`
- `/tmp/spyctres_gbs_auto_expand_broad.png`

## Verification

All commands used the `spyctres-dev-py312` conda environment.

| Command | Result |
|---|---|
| `conda run -n spyctres-dev-py312 python -m pytest tests/test_fitting_initialization.py tests/test_gaia_benchmark_validation.py -q` | 53 passed |
| `conda run -n spyctres-dev-py312 python -m pytest -q` | 474 passed, 2 failed, 15 warnings |
| `conda run -n spyctres-dev-py312 python scripts/phoenix_smoketest.py` | Passed; template loading, interpolation, cache creation/reload, and identical cached output verified |
| `conda run -n spyctres-dev-py312 python scripts/fitting_smoketest.py` | Passed; recovered the planted spectrum at `Teff=5044 K`, `[Fe/H]=-0.297`, `logg=4.296`, `RV=12.322 km/s`, with `chi2_red=1.184` |
| `conda run -n spyctres-dev-py312 python scripts/pepsi_fit_smoketest.py` | Expected command-line failure because the script requires at least one spectrum path |
| `conda run -n spyctres-dev-py312 python scripts/pepsi_fit_smoketest.py --fast --no-show examples/data/pepsir.20230603.010.dxt.nor` | Passed as the input-file fallback; fitting, reconstruction, and quality reporting completed |
| `conda run -n spyctres-dev-py312 python scripts/gaia_benchmark_validation.py --run-fits --window-set broad_metal_forest --output-json /tmp/spyctres_gbs_auto_expand_broad.json --output-csv /tmp/spyctres_gbs_auto_expand_broad.csv --output-summary-plot /tmp/spyctres_gbs_auto_expand_broad.png --resume` | Passed; all 12 completed fits were resumed and the revised outputs were written |

The two full-suite failures are unrelated to these changes. Both are in
`tests/test_numbered_examples.py` and arise from pre-existing user-owned
notebooks containing executed cell counts, outputs, and absolute `/home/...`
warning paths. Those notebook modifications were deliberately preserved.

## Recommendation assessment and next steps

The following recommendations were suitable for immediate inclusion and are
implemented in this patch:

- audit and extend the bounded-grid stopping tests;
- correct the benchmark metric definitions without silently changing old
  serialized fields;
- report tail failures and missing-reference counts;
- separate tolerance, coverage, fit quality, identifiability, and scientific
  review states; and
- use the declared SciPy objective for robust-loss selection and label the
  hybrid continuum treatment accurately.

The following recommendations are also appropriate, but are separate
scientific experiments rather than corrections to merge into the default
fitter now:

1. Compare Procyon and Arcturus feature families using common held-out
   wavelength pixels and a fixed grid policy.
2. Diagnose HD 16765 line widths across Na, Ca, Fe, and Mg before adding a new
   broadening parameter.
3. Test disconnected-region continua, model-discrepancy assumptions, and
   profile likelihoods on synthetic truth and the main failures.
4. Prototype multi-basin search only if the controlled tests demonstrate a
   missed remote minimum.
5. Prepare and reserve a quality-audited external GBSv3 cohort before any
   feature/window policy is frozen, then evaluate it only once after the method
   is fixed.

No public default window set, continuum model, broadening model, classification
API, or linked-arm continuum behavior has been changed in this pass. The pull
request should remain in draft while these scientific validation steps are
still outstanding.
