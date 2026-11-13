"""Benchmark-cohort safeguards for Spyctres validation workflows.

This module is intentionally internal during the alpha cycle.  It keeps three
questions separate before a spectrum can contribute to an accuracy claim:

1. can Spyctres model the product's wavelength/frame/LSF metadata;
2. is the target inside the selected PHOENIX model family; and
3. is the comparison parameter genuinely independent of spectral modelling.

The helpers do not fit spectra and do not expose reference values to fitting
code.  Validation runners may serialize their JSON-safe output as provenance.
"""

from __future__ import annotations

import re

from .preprocessing import analysis_readiness_audit


BENCHMARK_AUDIT_SCHEMA_VERSION = 1
PHOENIX_HIRES_TEFF_RANGE_K = (2300.0, 12000.0)

COHORT_ROLES = frozenset(
    {
        "development",
        "holdout_candidate",
        "holdout_locked",
        "stress",
    }
)

REFERENCE_TIERS = frozenset(
    {
        "primary_independent",
        "secondary_spectroscopic",
        "secondary_catalogue",
        "secondary_indirect",
        "morphology_only",
        "unavailable",
        "unspecified",
    }
)

PRIMARY_REFERENCE_TIERS = frozenset({"primary_independent"})
SECONDARY_REFERENCE_TIERS = frozenset(
    {
        "secondary_spectroscopic",
        "secondary_catalogue",
        "secondary_indirect",
        "morphology_only",
    }
)

_UNSUPPORTED_PHYSICS_FLAGS = frozenset(
    {
        "o_star",
        "early_b",
        "white_dwarf",
        "wolf_rayet",
        "carbon_star",
        "s_star",
        "strong_emission",
        "composite_spectrum",
    }
)

_CONDITIONAL_PHYSICS_FLAGS = frozenset(
    {
        "late_b",
        "a_star",
        "rapid_rotation",
        "activity",
        "peculiar_abundances",
        "cool_giant",
        "metal_poor",
    }
)


def _normalize_token(value):
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def normalize_reference_tiers(reference_tiers=None):
    """Return a complete, validated per-parameter reference-tier mapping."""
    supplied = dict(reference_tiers or {})
    normalized = {}
    for parameter in ("teff", "logg", "feh", "rv_kms", "spectral_type"):
        raw = supplied.get(parameter, "unspecified")
        if isinstance(raw, dict):
            raw = raw.get("tier", "unspecified")
        tier = _normalize_token(raw) or "unspecified"
        if tier not in REFERENCE_TIERS:
            raise ValueError(
                "Unknown reference tier for {0}: {1!r}. Expected one of {2}.".format(
                    parameter,
                    raw,
                    ", ".join(sorted(REFERENCE_TIERS)),
                )
            )
        normalized[parameter] = tier
    return normalized


def phoenix_model_support(teff_K=None, physics_flags=None):
    """Classify target support by the current PHOENIX HiRes model family.

    The result is a capability statement, not a claim that every target inside
    the numerical grid is accurately represented.
    """
    flags = sorted({_normalize_token(flag) for flag in (physics_flags or ()) if flag})
    unsupported_flags = sorted(set(flags) & _UNSUPPORTED_PHYSICS_FLAGS)
    conditional_flags = sorted(set(flags) & _CONDITIONAL_PHYSICS_FLAGS)

    value = None
    if teff_K is not None:
        try:
            value = float(teff_K)
        except (TypeError, ValueError):
            value = None

    blockers = []
    warnings = []
    if value is not None:
        lower, upper = PHOENIX_HIRES_TEFF_RANGE_K
        if value < lower or value > upper:
            blockers.append("teff_outside_phoenix_hires_grid")
    else:
        warnings.append("teff_support_not_assessed")
    if unsupported_flags:
        blockers.append("physics_outside_selected_phoenix_family")
    if conditional_flags:
        warnings.append("model_suitability_requires_scientific_review")

    if blockers:
        status = "unsupported"
    elif warnings:
        status = "conditional"
    else:
        status = "supported"
    return {
        "status": status,
        "supported_for_main_accuracy": status == "supported",
        "teff_K_used_for_gate": value,
        "phoenix_hires_teff_range_K": list(PHOENIX_HIRES_TEFF_RANGE_K),
        "physics_flags": flags,
        "unsupported_physics_flags": unsupported_flags,
        "conditional_physics_flags": conditional_flags,
        "blockers": blockers,
        "warnings": warnings,
    }


def benchmark_candidate_audit(
    spectrum,
    *,
    target_id,
    cohort_role="development",
    reference_tiers=None,
    teff_K=None,
    physics_flags=None,
    fit_windows=None,
    reference_values_visible_to_fitting=False,
    inspected_for_method_tuning=False,
):
    """Audit whether one target may contribute to benchmark statistics.

    ``holdout_candidate`` records are inventory-only.  Only a locked holdout
    with no leakage blockers can contribute to the primary external-accuracy
    report, and then only for parameters in ``primary_independent`` reference
    tier.
    """
    role = _normalize_token(cohort_role)
    if role not in COHORT_ROLES:
        raise ValueError(
            "cohort_role must be one of {0}.".format(", ".join(sorted(COHORT_ROLES)))
        )
    tiers = normalize_reference_tiers(reference_tiers)
    readiness = analysis_readiness_audit(
        spectrum,
        fit_windows=fit_windows,
        intended_use="benchmark_atmospheric_parameters",
    )
    model_support = phoenix_model_support(teff_K=teff_K, physics_flags=physics_flags)

    leakage_blockers = []
    if role in {"holdout_candidate", "holdout_locked"}:
        if reference_values_visible_to_fitting:
            leakage_blockers.append("holdout_reference_values_visible_to_fitting")
        if inspected_for_method_tuning:
            leakage_blockers.append("holdout_inspected_for_method_tuning")

    instrument_model_ready = bool(
        readiness.get("analysis_ready")
        and model_support.get("supported_for_main_accuracy")
    )
    primary_parameters = sorted(
        parameter
        for parameter, tier in tiers.items()
        if tier in PRIMARY_REFERENCE_TIERS
    )
    secondary_parameters = sorted(
        parameter
        for parameter, tier in tiers.items()
        if tier in SECONDARY_REFERENCE_TIERS
    )
    holdout_locked = role == "holdout_locked"
    main_accuracy_eligible = bool(
        instrument_model_ready
        and holdout_locked
        and primary_parameters
        and not leakage_blockers
    )

    eligibility_blockers = []
    if not readiness.get("analysis_ready"):
        eligibility_blockers.append("instrument_product_not_ready")
    if not model_support.get("supported_for_main_accuracy"):
        eligibility_blockers.append("model_capability_not_established")
    if not holdout_locked:
        eligibility_blockers.append("target_is_not_in_locked_holdout")
    if not primary_parameters:
        eligibility_blockers.append("no_primary_independent_reference_parameter")
    eligibility_blockers.extend(leakage_blockers)

    return {
        "schema_version": BENCHMARK_AUDIT_SCHEMA_VERSION,
        "target_id": str(target_id),
        "cohort_role": role,
        "instrument_product_gate": {
            "passed": bool(readiness.get("analysis_ready")),
            "blockers": list(readiness.get("blockers") or []),
            "warnings": list(readiness.get("warnings") or []),
            "readiness": readiness,
        },
        "model_capability_gate": model_support,
        "reference_tiers": tiers,
        "primary_accuracy_parameters": primary_parameters,
        "secondary_comparison_parameters": secondary_parameters,
        "leakage_gate": {
            "passed": not leakage_blockers,
            "blockers": leakage_blockers,
            "reference_values_visible_to_fitting": bool(
                reference_values_visible_to_fitting
            ),
            "inspected_for_method_tuning": bool(inspected_for_method_tuning),
        },
        "instrument_model_ready": instrument_model_ready,
        "main_accuracy_eligible": main_accuracy_eligible,
        "main_accuracy_eligibility_blockers": sorted(set(eligibility_blockers)),
    }


def normalize_star_alias(value):
    """Normalize a catalog alias for conservative star-level overlap checks."""
    return re.sub(r"[^a-z0-9]+", "", str(value or "").strip().lower())


def audit_cohort_manifest(payload):
    """Check star-level grouping and holdout leakage in a cohort manifest."""
    targets = list((payload or {}).get("targets") or [])
    errors = []
    warnings = []
    alias_owner = {}
    role_counts = {}
    for index, target in enumerate(targets):
        target_id = str(target.get("target_id") or "").strip()
        role = _normalize_token(target.get("cohort_role"))
        if not target_id:
            errors.append("target_{0}_missing_target_id".format(index))
            continue
        if role not in COHORT_ROLES:
            errors.append("{0}:invalid_cohort_role".format(target_id))
        role_counts[role or "missing"] = role_counts.get(role or "missing", 0) + 1
        aliases = [target_id] + list(target.get("aliases") or [])
        normalized_aliases = {normalize_star_alias(alias) for alias in aliases}
        normalized_aliases.discard("")
        for alias in normalized_aliases:
            previous = alias_owner.get(alias)
            if previous is not None and previous != target_id:
                errors.append(
                    "star_alias_overlap:{0}:{1}:{2}".format(alias, previous, target_id)
                )
            alias_owner[alias] = target_id
        if role in {"holdout_candidate", "holdout_locked"}:
            forbidden = {
                "fit",
                "fit_result",
                "reference_delta",
                "human_review",
                "tuning_notes",
            }
            present = sorted(forbidden & set(target))
            if present:
                errors.append(
                    "{0}:holdout_contains_postfit_fields:{1}".format(
                        target_id,
                        ",".join(present),
                    )
                )
            if target.get("reference_values_visible_to_fitting") is True:
                errors.append("{0}:holdout_reference_leakage".format(target_id))
        if not target.get("observations"):
            warnings.append("{0}:no_observations_inventoried".format(target_id))

    return {
        "schema_version": BENCHMARK_AUDIT_SCHEMA_VERSION,
        "valid": not errors,
        "n_targets": len(targets),
        "n_unique_aliases": len(alias_owner),
        "cohort_role_counts": dict(sorted(role_counts.items())),
        "errors": sorted(set(errors)),
        "warnings": sorted(set(warnings)),
    }
