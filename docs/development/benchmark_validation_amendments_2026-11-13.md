# Benchmark validation amendments and implementation status

Date: 2026-11-13

Branch: `feature/phoenix-backend`

## Decision

The referee's revised work order is adopted. The sequence remains P0/P1, then
P2/P3 on development stars, then a single frozen P4 holdout evaluation. Four
safeguards are now mandatory:

1. instrument/model capability is checked before a spectrum can contribute to
   the main accuracy statistics;
2. reference quality is assigned separately for each parameter;
3. development, locked automatic holdout, and human-assisted results remain
   separate; and
4. a failure diagnosis may remain unresolved rather than being forced into one
   cause.

## Product and reference verification

The implementation choices were checked against primary publications and
official archive documentation.

- Gaia FGK Benchmark Stars v3 provides 192 stars with Teff and logg derived
  independently of spectroscopy for most of the sample. The later common
  R=42,000 library contains 202 spectra/targets when nine indirect-diameter
  stars and the Sun are included; its abundances, including [Fe/H], are
  spectroscopic measurements. Spyctres therefore treats GBSv3 Teff/logg as
  primary independent references, [Fe/H] as a secondary spectroscopic
  comparison, and indirect-angular-diameter cases as secondary/flagged.
  Sources: Soubiran et al. (2024),
  <https://doi.org/10.1051/0004-6361/202347136>; Casamiquela et al. (2026),
  <https://doi.org/10.1051/0004-6361/202555211>;
  <https://www.blancocuaresma.com/s/benchmarkstars>.
- XSL DR2 provides separate, linearly sampled UVB/VIS/NIR products in air
  wavelengths and the stellar rest frame, with product-specific resolution and
  reduction provenance. DR3 is already arm-combined/scaled and cannot serve as
  independent truth for arm stitching. XSL atmospheric parameters from ULySS
  are spectroscopic/model-dependent comparisons, not primary independent
  labels. Sources: Gonneau et al. (2020),
  <https://doi.org/10.1051/0004-6361/201936825>; Verro et al. (2022),
  <https://doi.org/10.1051/0004-6361/202142388>; Arentsen et al. (2019),
  <https://doi.org/10.1051/0004-6361/201834273>.
- MaStar spectra use vacuum wavelengths and publish uncertainty, masks, and a
  wavelength-dependent LSF dispersion. The MaStar value-added atmospheric
  parameters combine spectral-modelling methods and are therefore secondary
  comparisons. Sources:
  <https://www.sdss4.org/dr17/mastar/mastar-spectra/> and
  <https://www.sdss4.org/dr17/mastar/mastar-stellar-parameters/>.
- The current PHOENIX-ACES HiRes grid ends at 12,000 K. Targets outside the
  numerical grid, and spectra dominated by physics absent from the selected
  family, belong in the abstention/stress track rather than ordinary parameter
  recovery. Source: Husser et al. (2013),
  <https://doi.org/10.1051/0004-6361/201219058>.

## Implemented P0/P1 safeguards

- `Spyctres.benchmarking` now produces a JSON-safe benchmark capability audit
  that keeps product readiness, PHOENIX model support, reference tier, cohort
  role, and leakage status separate.
- A tabulated wavelength-dependent LSF now creates the generic readiness flag
  `variable_lsf_not_supported_by_fitter` and blocks quicklook fitting,
  atmospheric parameters, RV and reviewed analysis while that descriptor is
  active. Inspection remains possible. This prevents MaStar/SDSS products from
  entering accuracy statistics merely because the curve was recorded in
  metadata.
- The Gaia benchmark runner records the capability gate and reports primary
  independent and secondary comparison aggregates separately. Its historical
  mixed aggregate is retained for serialized-output compatibility.
- The bundled 12-star Gaia sample is marked as an immutable development cohort.
  Its manifest records parameter-specific reference policy; indirect-angular-
  diameter cases override Teff/logg to `secondary_indirect`.
- `examples/data/validation_cohorts/source_registry_v1.json` records the first
  product-family readiness matrix and the pre-registered reporting rules.
- `examples/data/validation_cohorts/proposed_cohort_v1.json` now records 60
  ordinary supported GBS candidates and a separate 12-star conditional/stress
  set. It is an un-downloaded, un-fitted proposal rather than a locked holdout.
- Alias, Gaia/Hipparcos ID, proper-motion-aware coordinate overlap and obvious
  holdout post-fit/reference leakage can be detected with
  `audit_cohort_manifest()`. Nine manual identity reviews remain open.
- Benchmark-domain eligibility and automatic classification are serialized as
  separate decisions. Only the former may use independent references; the
  latter fails closed for acceptance metrics if reference use is recorded.

Baseline inspection began at commit `5615cd3`. The eight modified numbered
notebooks and untracked `CODE_REVIEW_RECOMMENDATIONS.md` were treated as
user-owned files and were not edited, staged, cleaned or incorporated into the
implementation patch.

## Revised work order

### P0: baseline and immutable development set

Retain the existing numerical/grid and reliability-reporting corrections.
Preserve all bundled Gaia targets, Gaia21ccu and every inspected XSL/PEPSI
target as development cases. Record exact tests rerun at the end of this
document.

### P1: cohort inventory and instrument gates

The star-level inventory is now proposed without fitting or inspecting
reference discrepancies. Each target records stable
aliases, one cohort assignment, observation/product IDs, source URLs,
pending checksums/expected sizes, quality flags, reader feasibility, LSF/frame status,
and per-parameter reference tier. GBSv3 should anchor primary FGK Teff/logg;
XSL and survey catalogues extend diversity mainly in secondary tiers.

Before locking, resolve the nine manual identity reviews, obtain scientific
approval for the star/stratum list, download only the approved products, record
actual sizes and SHA-256 values, and rerun the manifest audit. The detailed
proposal and caveats are in
`docs/development/proposed_external_benchmark_inventory_2026-11-13.md`.

The immediate engineering prerequisite is a fixed, supplied
wavelength-dependent LSF convolution with synthetic constant-curve equivalence,
variable-curve recovery, edge and mask tests. It must not fit new LSF
parameters. MaStar remains blocked from the main accuracy denominator until
that path and a product-specific reader are validated.

### P2: expert review on development stars

Create Example 9 as a required pre-holdout script/notebook pair using versioned sidecars.
Demonstrate one flagged and one apparently clean development fit. Review is
blinded initially, the automatic result is immutable, and review-triggered
variants are reported separately. Acceptance requires sidecar provenance and
immutability tests and an explicit post-unblinding distinction between improved
independent parameter recovery and a residual-only improvement.

### P3: falsifiable development diagnoses

Run the frozen Procyon/Arcturus feature experiment, HD 16765 line-family/width
diagnosis and HD 140283 stress analysis. Store outcomes as
`demonstrated_cause`, `supported_unconfirmed_hypothesis`, or
`unresolved_failure`. An unresolved result is acceptable; a target-specific
correction in the public fitter is not.

### P4: frozen holdout only after independent gate review

Freeze the commit, PHOENIX identity, cohort, reader/LSF capability matrix,
automatic acceptance/review policy, class-dependent scoring and statistical
rules before any holdout spectrum or reference discrepancy informs tuning.
Report confidence intervals, star-level bootstrap estimates, accepted fraction,
severe-error-among-accepted rate and per-class/per-instrument sample sizes.

## Verification

All commands below were run through `conda run -n spyctres-dev-py312`.

| Command | Outcome |
|---|---|
| `python -m py_compile Spyctres/benchmarking.py Spyctres/preprocessing.py scripts/gaia_benchmark_validation.py tests/test_benchmarking.py tests/test_gaia_benchmark_validation.py` | Passed |
| `python -m pytest tests/test_benchmarking.py tests/test_gaia_benchmark_validation.py tests/test_defaults.py tests/test_external_spectra_validation.py tests/test_io_canonical.py -q` | 54 passed |
| `python scripts/gaia_benchmark_validation.py --output-json /tmp/spyctres_gbs_tiered_audit.json --output-csv /tmp/spyctres_gbs_tiered_audit.csv --output-summary-plot /tmp/spyctres_gbs_tiered_audit.png --force` | Passed; 12 audit-only development records written. All constant-R products passed the instrument gate; reference tiers and indirect-diameter overrides were present. |
| `python scripts/phoenix_smoketest.py` | Passed |
| `python scripts/fitting_smoketest.py` | Passed; synthetic recovery remained successful. |
| `python scripts/pepsi_fit_smoketest.py --fast --no-show examples/data/pepsir.20230603.010.dxt.nor` | Passed as an engineering smoke test; it retained the expected high-chi-square and incomplete-frame science warnings. |
| `python -m pytest -q` | 480 passed, 2 failed. Both failures are the known user-owned notebook cleanliness checks: saved execution counts/outputs and embedded `/home/...` paths. No source-code or new benchmark test failed. |
| `git diff --check` | Passed |

The full-suite notebook failures are not repaired in this patch because doing
so would overwrite unrelated user work. They should be cleared deliberately in
a separate notebook-cleaning step after those local outputs have been saved or
reviewed.
