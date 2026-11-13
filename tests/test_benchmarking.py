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
