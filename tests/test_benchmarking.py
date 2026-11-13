import json
from collections import Counter
from pathlib import Path

import numpy as np

from Spyctres.benchmarking import (
    audit_cohort_manifest,
    benchmark_candidate_audit,
    phoenix_model_support,
)
from Spyctres.io import ResolutionDescriptor, SpectrumSegment
from Spyctres.preprocessing import analysis_readiness_audit


def _segment(resolution=None):
    wave = np.linspace(5000.0, 5100.0, 2001)
    flux = 1.0 - 0.1 * np.exp(-0.5 * ((wave - 5050.0) / 0.4) ** 2)
    return SpectrumSegment(
        wave=wave,
        flux=flux,
        err=np.full(wave.size, 0.01),
        wave_medium="air",
        observer_frame="barycentric",
        stellar_rest_status="corrected",
        resolution=resolution
        or ResolutionDescriptor(quantity="R", value=42_000.0, source="test"),
        name="benchmark-fixture",
    )


def test_locked_holdout_requires_product_model_and_primary_reference_gates():
    audit = benchmark_candidate_audit(
        _segment(),
        target_id="HIP1",
        cohort_role="holdout_locked",
        reference_tiers={
            "teff": "primary_independent",
            "logg": "primary_independent",
            "feh": "secondary_spectroscopic",
        },
        teff_K=5800.0,
    )

    assert audit["instrument_product_gate"]["passed"] is True
    assert audit["model_capability_gate"]["status"] == "supported"
    assert audit["primary_accuracy_parameters"] == ["logg", "teff"]
    assert audit["secondary_comparison_parameters"] == ["feh"]
    assert audit["main_accuracy_eligible"] is True
    assert audit["automatic_classification_decision"]["status"] == "not_run"
    assert audit["automatic_acceptance_metrics_eligible"] is False


def test_development_target_is_never_reported_as_locked_holdout_accuracy():
    audit = benchmark_candidate_audit(
        _segment(),
        target_id="HIP2",
        cohort_role="development",
        reference_tiers={"teff": "primary_independent"},
        teff_K=5000.0,
        inspected_for_method_tuning=True,
    )

    assert audit["instrument_model_ready"] is True
    assert audit["main_accuracy_eligible"] is False
    assert "target_is_not_in_locked_holdout" in audit[
        "main_accuracy_eligibility_blockers"
    ]


def test_active_tabulated_lsf_fails_closed_before_parameter_accuracy():
    wave = np.linspace(5000.0, 5100.0, 25)
    resolution = ResolutionDescriptor(
        quantity="sigma_kms",
        mode="tabulated",
        wave_A=wave,
        values=np.linspace(55.0, 70.0, wave.size),
        source="published_variable_lsf",
    )
    segment = _segment(resolution=resolution)

    readiness = analysis_readiness_audit(segment)
    audit = benchmark_candidate_audit(
        segment,
        target_id="variable-lsf",
        cohort_role="holdout_locked",
        reference_tiers={"teff": "primary_independent"},
        teff_K=5800.0,
    )

    assert readiness["analysis_ready"] is False
    assert "variable_lsf_not_supported_by_fitter" in readiness["blockers"]
    assert audit["instrument_product_gate"]["passed"] is False
    assert audit["main_accuracy_eligible"] is False


def test_phoenix_model_support_separates_grid_and_physics_limits():
    hot = phoenix_model_support(teff_K=20_000.0)
    carbon = phoenix_model_support(teff_K=4500.0, physics_flags=["carbon_star"])
    conditional = phoenix_model_support(
        teff_K=8500.0,
        physics_flags=["rapid_rotation"],
    )

    assert hot["status"] == "unsupported"
    assert "teff_outside_phoenix_hires_grid" in hot["blockers"]
    assert carbon["status"] == "unsupported"
    assert conditional["status"] == "conditional"
    assert conditional["supported_for_main_accuracy"] is False
    assert conditional["eligible_for_separate_accuracy_reporting"] is True
    assert conditional["reporting_track"] == "conditional_supported"


def test_reference_domain_gate_cannot_make_automatic_acceptance_decision():
    audit = benchmark_candidate_audit(
        _segment(),
        target_id="HIP3",
        cohort_role="holdout_locked",
        reference_tiers={"teff": "primary_independent"},
        teff_K=20_000.0,
        automatic_decision={
            "status": "accepted",
            "decision_source": "frozen_spectrum_diagnostics_v1",
        },
    )

    assert audit["model_capability_gate"]["status"] == "unsupported"
    assert audit["main_accuracy_eligible"] is False
    assert audit["automatic_classification_decision"]["status"] == "accepted"
    assert audit["automatic_acceptance_metrics_eligible"] is True


def test_automatic_decision_fails_closed_if_reference_values_were_used():
    audit = benchmark_candidate_audit(
        _segment(),
        target_id="HIP4",
        cohort_role="holdout_locked",
        reference_tiers={"teff": "primary_independent"},
        teff_K=5800.0,
        automatic_decision={
            "status": "accepted",
            "reference_values_used": True,
        },
    )

    decision = audit["automatic_classification_decision"]
    assert decision["valid_for_acceptance_metrics"] is False
    assert "automatic_decision_used_reference_values" in decision["blockers"]
    assert audit["automatic_acceptance_metrics_eligible"] is False


def test_conditional_support_is_retained_in_separate_accuracy_track():
    audit = benchmark_candidate_audit(
        _segment(),
        target_id="HIP5",
        cohort_role="holdout_locked",
        reference_tiers={"teff": "primary_independent"},
        teff_K=4200.0,
        physics_flags=["cool_giant"],
    )

    assert audit["main_accuracy_eligible"] is False
    assert audit["conditional_accuracy_eligible"] is True
    assert audit["accuracy_reporting_track"] == "conditional_supported"


def test_cohort_manifest_detects_star_alias_overlap_and_holdout_leakage():
    report = audit_cohort_manifest(
        {
            "targets": [
                {
                    "target_id": "HIP1",
                    "aliases": ["HD 123"],
                    "cohort_role": "development",
                    "observations": [{"observation_id": "dev"}],
                },
                {
                    "target_id": "Gaia-2",
                    "aliases": ["HD123"],
                    "cohort_role": "holdout_locked",
                    "reference_values_visible_to_fitting": True,
                    "fit_result": {"teff": 5000.0},
                    "observations": [{"observation_id": "holdout"}],
                },
            ]
        }
    )

    assert report["valid"] is False
    assert any(item.startswith("star_alias_overlap:hd123") for item in report["errors"])
    assert "Gaia-2:holdout_reference_leakage" in report["errors"]
    assert any("holdout_contains_postfit_fields" in item for item in report["errors"])


def test_cohort_manifest_detects_catalogue_and_proper_motion_position_overlap():
    report = audit_cohort_manifest(
        {
            "identity_crossmatch": {"match_radius_arcsec": 2.0},
            "targets": [
                {
                    "target_id": "first",
                    "cohort_role": "holdout_candidate",
                    "identity_review_status": "verified_catalogue_crossmatch",
                    "identity": {
                        "gaia_dr3_source_id": "123",
                        "ra_deg": 10.0,
                        "dec_deg": 20.0,
                        "epoch_jyear": 2000.0,
                        "pmra_mas_per_year": 100.0,
                        "pmdec_mas_per_year": 0.0,
                    },
                    "observations": [{"observation_id": "one"}],
                },
                {
                    "target_id": "second",
                    "cohort_role": "holdout_candidate",
                    "identity_review_status": "verified_catalogue_crossmatch",
                    "identity": {
                        "gaia_dr2_source_id": "456",
                        "ra_deg": 10.0002956,
                        "dec_deg": 20.0,
                        "epoch_jyear": 2010.0,
                        "pmra_mas_per_year": 0.0,
                        "pmdec_mas_per_year": 0.0,
                    },
                    "observations": [{"observation_id": "two"}],
                },
            ],
        }
    )

    assert report["valid"] is False
    assert any(
        item.startswith("coordinate_identity_overlap:first:second")
        for item in report["errors"]
    )


def test_locked_holdout_requires_completed_manual_identity_review():
    report = audit_cohort_manifest(
        {
            "targets": [
                {
                    "target_id": "ambiguous",
                    "cohort_role": "holdout_locked",
                    "identity_review_status": "manual_review_required",
                    "identity": {
                        "ra_deg": 12.0,
                        "dec_deg": -3.0,
                        "epoch_jyear": 2000.0,
                    },
                    "observations": [{"observation_id": "candidate"}],
                }
            ]
        }
    )

    assert report["valid"] is False
    assert "ambiguous:manual_identity_review_pending" in report["errors"]


def test_development_identity_cannot_reenter_candidate_cohort():
    report = audit_cohort_manifest(
        {
            "excluded_development_identities": [
                {
                    "target_id": "dev",
                    "aliases": ["HD 123"],
                    "identity": {"gaia_dr3_source_id": "999"},
                }
            ],
            "targets": [
                {
                    "target_id": "candidate",
                    "aliases": ["HD123"],
                    "cohort_role": "holdout_candidate",
                    "identity": {"gaia_dr3_source_id": "999"},
                    "observations": [{"observation_id": "candidate"}],
                }
            ],
        }
    )

    assert report["valid"] is False
    assert any(item.startswith("development_overlap:hd123") for item in report["errors"])
    assert any(
        item.startswith("development_identity_overlap:gaia_dr3_source_id:999")
        for item in report["errors"]
    )


def test_proposed_external_inventory_is_star_grouped_and_result_blind():
    path = (
        Path(__file__).parents[1]
        / "examples"
        / "data"
        / "validation_cohorts"
        / "proposed_cohort_v1.json"
    )
    payload = json.loads(path.read_text())
    report = audit_cohort_manifest(payload)
    targets = payload["targets"]

    assert report["valid"] is True
    assert len(targets) == 72
    assert Counter(target["cohort_role"] for target in targets) == {
        "holdout_candidate": 60,
        "stress": 12,
    }
    assert Counter(
        target["benchmark_domain"]["reporting_track"] for target in targets
    ) == {
        "ordinary_supported": 60,
        "conditional_supported": 6,
        "demonstrably_unsupported": 6,
    }
    assert all(
        not any(
            field in target
            for field in ("fit", "fit_result", "reference_delta", "human_review")
        )
        for target in targets
    )
    assert all(
        target.get("reference_values_visible_to_fitting") is False
        for target in targets
    )
    assert all(
        observation.get("downloaded_for_holdout") is False
        for target in targets
        for observation in target["observations"]
    )
