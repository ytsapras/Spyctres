# Proposed external benchmark inventory

Date: 2026-11-13

Status: proposed for scientific approval; not locked, downloaded, or fitted

Machine-readable inventory:
`examples/data/validation_cohorts/proposed_cohort_v1.json`

## Summary

The requested star-level inventory is complete.

- The primary candidate cohort contains 60 unique, ordinary PHOENIX-supported
  Gaia FGK Benchmark Stars.
- A separate 12-star sensitivity set contains six conditionally supported
  targets and six demonstrably unsupported targets.
- None of the 72 targets is in the immutable bundled GBS or XSL development
  samples.
- No proposed spectrum was downloaded and no holdout fit, residual, parameter
  difference, or recovery result was inspected.
- The estimated download is 257.71 MiB. Checksums remain explicitly pending
  until the list is approved.

This is an inventory, not a locked benchmark. Nine identity records still
require manual confirmation before locking: eight bright GBS stars without a
Gaia DR3 best-neighbour row, and one XSL source whose historical identification
is questioned by XSL itself.

## How the referee's amendments were applied

### Benchmark eligibility and automatic classification are separate

`benchmark_candidate_audit()` now records two independent decisions.

1. `benchmark_eligibility_gate` may use independently established reference
   information to decide whether a star belongs in an ordinary, conditional,
   or unsupported benchmark track.
2. `automatic_classification_decision` accepts only a decision produced by the
   pre-registered spectrum workflow. It receives no catalogue temperature or
   reference label. A decision that records any reference-value use is invalid
   for automatic-acceptance and false-confidence statistics.

Thus an independently known hot or peculiar star can be assigned to the
correct benchmark track without helping Spyctres decide whether an ordinary
user's spectrum should be accepted or rejected.

### Identity checks use catalogue IDs and positions

The manifest audit now checks aliases, release-qualified Gaia IDs, Hipparcos
IDs, and sky coordinates. Coordinates are linearly propagated to a common
epoch when proper motions are available, then compared with a 2 arcsec
duplicate threshold.

For the GBS candidates, 52 of the 60 ordinary stars have an official Gaia DR3
Hipparcos-2 best-neighbour match. The remaining eight have positions and proper
motions from the official Hipparcos new reduction but no Gaia DR3
best-neighbour row; they remain `manual_review_required`. The XSL Gaia DR2 IDs
were resolved through the official Gaia DR2-to-DR3 neighbourhood table using
the nearest match. X0587 remains manually reviewable because the XSL catalogue
questions the historical source identification even though a Gaia match is
available.

Sources: [Gaia archive](https://gea.esac.esa.int/archive/),
[GBSv3 fundamental parameters](https://doi.org/10.1051/0004-6361/202347136),
and the [XSL DR2 catalogue](https://xsl.u-strasbg.fr/page_dr2_all.html).

### Model-support tracks remain visible

The 60-star primary proposal now contains ordinary supported stars only.
Conditional and unsupported cases are not discarded; they are retained in the
separate 12-star set and must be reported independently. This set explicitly
includes a cool giant, a metal-poor giant, an A star, a late-M active dwarf,
chemically peculiar stars, an S star, a carbon/composite spectrum, a
long-period variable, and a compact-star case.

### Example 9 is an acceptance criterion

Example 9 is no longer an optional later illustration. Its acceptance criteria
are specified below under “Next implementation gates.” It will use development
stars only and must be complete before the holdout is locked.

## Primary 60-star proposal

The GBS products are the normalized common-resolution R=42,000 spectra over
480–680 nm. The instrument column is the source spectrograph recorded by the
GBS library; the evaluated product is still the homogenized GBS product, not
the native-resolution observation.

An asterisk marks a Hipparcos-secure target for which the Gaia DR3
best-neighbour lookup was empty. These eight cases need manual confirmation
before locking.

| Target | Common alias | Stratum | Source instrument |
|---|---|---|---|
| HIP32851 | HD49933 | F dwarf | FEROS |
| HIP78072 | HD142860 | F dwarf | HARPS |
| HIP61317 | HD109358 | F dwarf | NARVAL |
| HIP93427 | HD177153 | F dwarf | ELODIE |
| HIP70497 | HD126660 | F dwarf | NARVAL |
| HIP96441 | HD185395 | F dwarf | ESPADONS |
| HIP22449 | HD30652 | F dwarf | FEROS |
| HIP63584 | HD113337 | F dwarf | FIES |
| HIP112447 | HD215648 | F subgiant | ESPADONS |
| HIP94755 | HD181096 | F subgiant | ESPADONS |
| HIP92043 | HD173667 | F subgiant | ESPADONS |
| HIP108535 | HD209369 | F subgiant | CAFE |
| HIP67927* | HD121370 | F subgiant | ESPADONS |
| HIP5336* | HD6582 | G dwarf | FIES |
| HIP27435 | HD38858 | G dwarf | ESPADONS |
| HIP56997 | HD101501 | G dwarf | ESPADONS |
| HIP16852 | HD22484 | G dwarf | FEROS |
| HIP544 | HD166 | G dwarf | NARVAL |
| HIP77052 | HD140538 | G dwarf | ESPADONS |
| HIP81300 | HD149661 | G dwarf | FEROS |
| HIP3093 | HD3651 | G dwarf | ESPADONS |
| HIP71681 | HD128621 | G dwarf | HARPS |
| HIP86974* | HD161797 | G dwarf | ELODIE |
| HIP47908 | HD84441 | G giant | FIES |
| HIP15776* | HD21019 | G subgiant | ESPADONS |
| HIP74975 | HD136202 | G subgiant | NARVAL |
| HIP65721 | HD117176 | G subgiant | ESPADONS |
| HIP8159 | HD10697 | G subgiant | HERMES |
| HIP14954 | HD19994 | G subgiant | ESPADONS |
| HIP104217 | HD201092 | K dwarf | ESPADONS |
| HIP85235 | HD158633 | K dwarf | NARVAL |
| HIP19849* | HD26965 | K dwarf | ESPADONS |
| HIP49908 | HD88230 | K dwarf | ESPADONS |
| HIP12114* | HD16160 | K dwarf | ESPADONS |
| HIP16537* | HD22049 | K dwarf | FEROS |
| HIP73184 | HD131977 | K dwarf | FEROS |
| HIP114622 | HD219134 | K dwarf | ESPADONS |
| HIP3031 | HD3546 | K giant | HERMES |
| HIP4257 | HD5268 | K giant | HERMES |
| HIP12486 | HD16815 | K giant | HARPS |
| HIP17738 | HD23940 | K giant | HARPS |
| HIP30565 | HD46116 | K giant | HARPS |
| HIP17595 | HD23526 | K giant | HARPS |
| HIP671 | HD360 | K giant | HARPS |
| HIP27621 | HD39640 | K giant | HARPS |
| HIP36444 | HD60060 | K giant | HARPS |
| HIP26019 | HD36874 | K giant | HARPS |
| HIP112748 | HD216131 | K giant | NARVAL |
| HIP29575 | HD43023 | K giant | HARPS |
| HIP112440 | HD215665 | K giant | NARVAL |
| HIP27530* | HD39523 | K giant | HARPS |
| HIP63608 | HD113226 | K giant | ESPADONS |
| HIP115620 | HD220572 | K giant | HARPS |
| HIP96837 | HD185958 | K giant | HERMES |
| HIP25993 | HD36848 | K giant | HARPS |
| HIP102422 | HD198149 | K subgiant | NARVAL |
| HIP98036 | HD188512 | K subgiant | HARPS |
| HIP50887 | HD90043 | K subgiant | ESPADONS |
| HIP89047 | HD167042 | K subgiant | CAFE |
| HIP17378 | HD23249 | K subgiant | FEROS |

The fixed stratum counts are:

| Stratum | Stars |
|---|---:|
| F dwarf | 8 |
| F subgiant | 5 |
| G dwarf | 10 |
| G subgiant | 5 |
| G giant | 1 |
| K dwarf | 8 |
| K subgiant | 5 |
| K giant | 18 |
| Total | 60 |

The source-instrument distribution across all 72 proposed products is
ESPADONS 19, HARPS 16, X-SHOOTER 10, NARVAL 8, FEROS 7, HERMES 5, FIES 3,
ELODIE 2, and CAFE 2.

## Conditional and unsupported 12-star proposal

| Target | Alias | Track | Reason for inclusion |
|---|---|---|---|
| HIP115227 | HD220009 | Conditional | Cool K giant; hydrostatic/LTE and continuum sensitivity |
| HIP2413 | HD2665 | Conditional | Metal-poor K giant; composition mismatch sensitivity |
| X0133 | HD 96446 | Conditional | He-rich late-B/early-type abundance peculiarity |
| X0653 | HD 172488 | Conditional | Possibly He-rich; UVB is unavailable |
| X0131 | LHS 2065 | Conditional | Late-M active dwarf; UVB lacks usable signal |
| X0163 | HD 174240 | Conditional | Normal A1V coverage with all three arms |
| X0420 | SV* HV 11223 | Unsupported | S-star with confirmed ZrO |
| X0248 | HD 190073 | Unsupported | Herbig Ae/Be emission and cool-component NIR continuum |
| X0513 | CL* NGC 419 LE 35 | Unsupported | Carbon star contaminated by a hotter neighbour |
| X0675 | V874 Aql | Unsupported | O-rich long-period variable |
| X0587* | IRAS 10151-6008? | Unsupported | O-rich source with an explicitly uncertain historical identity |
| X0790 | Feige 110 | Unsupported | Compact/hot-subdwarf physics and poor individual-visit NIR S/N |

The XSL product notes and identifiers come from the
[official DR2 catalogue](https://xsl.u-strasbg.fr/page_dr2_all.html) and
[ESO release description](https://www.eso.org/rm/api/v1/public/releaseDescriptions/150).
The proposed DR2 products remain separate-arm data.

## Reference tiers

For all GBS targets, Teff and log(g) are primary independent references.
[Fe/H] remains a secondary spectroscopic comparison. The GBS selection excludes
the source table's indirect-angular-diameter and SB2 flags from the ordinary
60-star cohort. The reference policy follows
[Soubiran et al. (2024)](https://doi.org/10.1051/0004-6361/202347136) and
[Casamiquela et al. (2026)](https://doi.org/10.1051/0004-6361/202555211).

XSL atmospheric parameters are secondary spectroscopic comparisons and its
spectral types are morphology labels. They must not be presented as
independent atmospheric-parameter truth. The XSL stress records are intended
primarily to test correct conditional reporting and abstention.

Numeric reference values are deliberately absent from the fitting manifest.
They can be held in a separate scoring input after the cohort, code, automatic
decision rule, and statistical analysis are frozen.

## Download footprint and readiness

| Product family | Stars | Estimated bytes | Estimated MiB | Current gate |
|---|---:|---:|---:|---|
| GBSv3 R42KNorm | 62 | 260,901,348 | 248.81 | Candidate inventory ready; manual identity review remains for eight stars |
| XSL DR2 three-arm sets | 10 | 9,331,200 | 8.90 | Blocked pending the product-specific reader |
| Total | 72 | 270,232,548 | 257.71 | Not approved for holdout execution |

The estimates use the mean sizes of the already bundled same-format products.
They are not archive promises. After approval, every downloaded file must have
its actual byte count, stable archive identifier, source URL, and SHA-256
recorded.

The primary 60-star set is deliberately high-resolution. Low-resolution
MaStar/SDSS products have not been admitted merely to manufacture resolution
coverage. MaStar publishes a wavelength-dependent LSF, including for its
homogenized products, and remains blocked until Spyctres can apply a fixed
supplied LSF curve without fitting new broadening parameters. See the
[MaStar data-access documentation](https://www.sdss4.org/dr17/mastar/mastar-data-access/)
and [caveats](https://www.sdss4.org/dr17/mastar/mastar-caveats/).

## Example 9 acceptance criteria

Example 9 must be implemented on development stars before the holdout is
locked. It passes only if it demonstrates all of the following:

1. Load an immutable automatic result for one flagged case and one apparently
   clean case.
2. Present observations, model, residuals, continuum diagnostics, masks, and
   automatic quality flags while hiding published reference parameters during
   the initial review.
3. Let the reviewer identify suspect lines or continuum regions and specify
   revised masks or diagnostic windows without mutating the automatic result.
4. Save the intervention in a versioned JSON sidecar containing the base-result
   hash, changed regions, scientific rationale, and schema version.
5. Run the controlled refit as a separate human-assisted result and retain both
   outputs.
6. After unblinding, report whether the intervention improved independent
   parameter recovery, residuals only, both, or neither.
7. Include regression tests for sidecar round-tripping, provenance, immutable
   baselines, invalid windows, and deterministic refits, plus a no-download
   example smoke test.

Procyon and HD 16765 remain suitable development cases because their automatic
fits can look superficially acceptable despite incorrect parameters. The
apparently clean audit case should be selected from the existing development
set before reference values are shown to the reviewer.

## Engineering verification

All verification used the `spyctres-dev-py312` conda environment.

| Command | Result |
|---|---|
| `python -m py_compile Spyctres/benchmarking.py tests/test_benchmarking.py` | Passed |
| `python -m pytest tests/test_benchmarking.py -q` | 12 passed |
| `python -m pytest tests/test_benchmarking.py tests/test_gaia_benchmark_validation.py tests/test_defaults.py tests/test_external_spectra_validation.py tests/test_io_canonical.py -q` | 61 passed; 10 existing warnings |
| `python scripts/phoenix_smoketest.py` | Passed |
| `python scripts/fitting_smoketest.py` | Passed |
| `python scripts/pepsi_fit_smoketest.py --fast --no-show examples/data/pepsir.20230603.010.dxt.nor` | Passed with the expected science-quality warnings for this smoke dataset |
| `python -m pytest -q` | 487 passed; two failures confined to user-modified notebooks with saved outputs/execution counts and embedded local paths |

The source, inventory, and benchmark-audit tests passed. The two full-suite
failures do not involve the changes described here, and the notebooks were not
modified or normalized because they are existing user work.

## Decision requested before downloads

The reviewer should approve or amend:

1. the 60-star GBS stratum balance;
2. the 12 conditional/unsupported cases;
3. whether the eight Hipparcos-only GBS records should be retained after manual
   identity checks or replaced with Gaia-matched stars; and
4. whether the current high-resolution primary cohort is acceptable for the
   first accuracy release, with low-resolution admission deferred to the fixed
   supplied-LSF milestone.

After approval, the next actions are to resolve the nine manual identity
reviews, download and checksum the approved products, implement the narrow XSL
DR2 reader, complete the fixed wavelength-dependent LSF prerequisite, and
build Example 9. Holdout fitting remains prohibited until those gates and the
scoring rules are independently frozen.
