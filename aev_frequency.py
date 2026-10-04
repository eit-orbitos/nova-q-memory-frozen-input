"""Executable normalized AEV rate candidate for D13 V0.1.

C_coh and V_valid are distinct typed inputs.  Internal coherence does not
imply validation; passed internal validation does not imply scientific truth.
The result is not a physical frequency and has no promotion authority.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Sequence

from .novelty_operator import NoveltyReport
from .validation_operator import ValidationReport

UNITS = "NORMALIZED_MODEL_INTERNAL_RATE"
PHYSICAL_HZ = "PROHIBITED"


class CheckVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"


class CoherenceStatus(str, Enum):
    EVALUATED_INTERNAL_COHERENCE = "EVALUATED_INTERNAL_COHERENCE"
    BLOCKED_NO_DECLARED_CHECKS = "BLOCKED_NO_DECLARED_CHECKS"
    BLOCKED_INVALID_CHECKS = "BLOCKED_INVALID_CHECKS"


class AEVFrequencyStatus(str, Enum):
    EXECUTABLE_NORMALIZED_MODEL_INTERNAL_RATE_CANDIDATE = (
        "EXECUTABLE_NORMALIZED_MODEL_INTERNAL_RATE_CANDIDATE"
    )
    BLOCKED_NONFINITE_INPUT = "BLOCKED_NONFINITE_INPUT"
    BLOCKED_NONPOSITIVE_DELTA_T = "BLOCKED_NONPOSITIVE_DELTA_T"
    BLOCKED_METRIC_OUTSIDE_UNIT_INTERVAL = (
        "BLOCKED_METRIC_OUTSIDE_UNIT_INTERVAL"
    )
    BLOCKED_MISMATCHED_EVIDENCE = "BLOCKED_MISMATCHED_EVIDENCE"


@dataclass(frozen=True)
class CoherenceCheck:
    check_id: str
    criterion: str
    verdict: CheckVerdict
    evidence: str

    def __post_init__(self) -> None:
        if any(not value.strip() for value in (
            self.check_id, self.criterion, self.evidence
        )):
            raise ValueError("coherence check ID, criterion, and evidence are required")


@dataclass(frozen=True)
class CoherenceReport:
    status: CoherenceStatus
    candidate_source_id: str
    check_count: int
    passed_check_count: int
    coherence_score: float
    validation_inferred: bool
    scientific_truth_inferred: bool
    detail: str


@dataclass(frozen=True)
class AEVValiditySensitivityResult:
    derivative: float | None
    status: AEVFrequencyStatus
    nonnegative_on_declared_domain: bool
    evidence_scope: str
    physical_hz_claim: bool
    scientific_truth_claim: bool
    promotion_authority: bool
    detail: str


@dataclass(frozen=True)
class AEVFrequencyResult:
    nu_aev_star: float | None
    n_novel: float
    c_coh: float
    v_valid: float
    r_red: float
    delta_t: float
    status: AEVFrequencyStatus
    evidence_scope: str
    units: str
    physical_hz_claim: bool
    scientific_truth_claim: bool
    consciousness_claim: bool
    promotion_authority: bool
    detail: str


def evaluate_internal_coherence(
    candidate_source_id: str,
    checks: Sequence[CoherenceCheck],
) -> CoherenceReport:
    """Score explicit internal consistency checks independently of validation."""
    if not candidate_source_id.strip():
        raise ValueError("candidate_source_id is required")
    items = tuple(checks)
    if not items:
        return CoherenceReport(
            CoherenceStatus.BLOCKED_NO_DECLARED_CHECKS, candidate_source_id,
            0, 0, 0.0, False, False,
            "no internal coherence checks were declared",
        )
    if any(not isinstance(item, CoherenceCheck) for item in items):
        return CoherenceReport(
            CoherenceStatus.BLOCKED_INVALID_CHECKS, candidate_source_id,
            len(items), 0, 0.0, False, False,
            "invalid coherence-check object",
        )
    ids = tuple(item.check_id for item in items)
    if len(ids) != len(set(ids)):
        return CoherenceReport(
            CoherenceStatus.BLOCKED_INVALID_CHECKS, candidate_source_id,
            len(items), 0, 0.0, False, False,
            "coherence check IDs must be unique",
        )
    passed = sum(item.verdict == CheckVerdict.PASS for item in items)
    score = passed / len(items)
    return CoherenceReport(
        CoherenceStatus.EVALUATED_INTERNAL_COHERENCE, candidate_source_id,
        len(items), passed, score, False, False,
        "internal coherence evaluated separately from validation",
    )


def evaluate_aev_frequency(
    *,
    n_novel: float,
    c_coh: float,
    v_valid: float,
    r_red: float,
    delta_t: float,
    evidence_scope: str = "DECLARED_INTERNAL_V0.1_METRICS",
) -> AEVFrequencyResult:
    """Evaluate nu*=N*C*V/(dt*(1+R)) with hard domain guards."""
    values = (n_novel, c_coh, v_valid, r_red, delta_t)
    common = dict(
        n_novel=n_novel, c_coh=c_coh, v_valid=v_valid, r_red=r_red,
        delta_t=delta_t, evidence_scope=evidence_scope, units=UNITS,
        physical_hz_claim=False, scientific_truth_claim=False,
        consciousness_claim=False, promotion_authority=False,
    )
    if any(isinstance(value, bool) or not isinstance(value, (int, float))
           or not math.isfinite(float(value)) for value in values):
        return AEVFrequencyResult(
            nu_aev_star=None,
            status=AEVFrequencyStatus.BLOCKED_NONFINITE_INPUT,
            detail="all metric inputs and delta_t must be finite real numbers",
            **common,
        )
    if delta_t <= 0:
        return AEVFrequencyResult(
            nu_aev_star=None,
            status=AEVFrequencyStatus.BLOCKED_NONPOSITIVE_DELTA_T,
            detail="delta_t must be strictly positive",
            **common,
        )
    if any(not 0.0 <= float(value) <= 1.0
           for value in (n_novel, c_coh, v_valid, r_red)):
        return AEVFrequencyResult(
            nu_aev_star=None,
            status=AEVFrequencyStatus.BLOCKED_METRIC_OUTSIDE_UNIT_INTERVAL,
            detail="N_novel, C_coh, V_valid, and R_red must lie in [0,1]",
            **common,
        )
    result = (
        float(n_novel) * float(c_coh) * float(v_valid)
        / (float(delta_t) * (1.0 + float(r_red)))
    )
    return AEVFrequencyResult(
        nu_aev_star=result,
        status=AEVFrequencyStatus.EXECUTABLE_NORMALIZED_MODEL_INTERNAL_RATE_CANDIDATE,
        detail=(
            "normalized model-internal rate candidate evaluated; coherence, "
            "validation, truth, consciousness, and physical Hz remain distinct"
        ),
        **common,
    )


def evaluate_validity_sensitivity(
    *, n_novel: float, c_coh: float, r_red: float, delta_t: float,
) -> AEVValiditySensitivityResult:
    """Evaluate analytic d(nu_AEV*)/d(V_valid) on the declared domain."""
    guard = evaluate_aev_frequency(
        n_novel=n_novel, c_coh=c_coh, v_valid=0.0,
        r_red=r_red, delta_t=delta_t,
        evidence_scope="ANALYTIC_VALIDITY_SENSITIVITY_V0.1",
    )
    if guard.nu_aev_star is None:
        return AEVValiditySensitivityResult(
            None, guard.status, False, guard.evidence_scope,
            False, False, False, guard.detail,
        )
    derivative = (
        float(n_novel) * float(c_coh)
        / (float(delta_t) * (1.0 + float(r_red)))
    )
    return AEVValiditySensitivityResult(
        derivative,
        AEVFrequencyStatus.EXECUTABLE_NORMALIZED_MODEL_INTERNAL_RATE_CANDIDATE,
        derivative >= 0.0,
        "ANALYTIC_VALIDITY_SENSITIVITY_V0.1",
        False, False, False,
        "d(nu_AEV*)/d(V_valid)=N_novel*C_coh/(delta_t*(1+R_red))",
    )


def evaluate_aev_frequency_from_reports(
    novelty: NoveltyReport,
    coherence: CoherenceReport,
    validation: ValidationReport,
    *,
    delta_t: float,
) -> AEVFrequencyResult:
    """Compose typed evidence without equating coherence and validation.

    V_valid is the reported score only when every declared internal validation
    gate passed.  Otherwise its effective value is zero.
    """
    ids = {
        novelty.candidate_source_id,
        coherence.candidate_source_id,
        validation.candidate_source_id,
    }
    if len(ids) != 1:
        return AEVFrequencyResult(
            None, novelty.novelty_score, coherence.coherence_score, 0.0,
            novelty.redundancy_score, delta_t,
            AEVFrequencyStatus.BLOCKED_MISMATCHED_EVIDENCE,
            "MISMATCHED_CANDIDATE_RECORDS", UNITS, False, False, False, False,
            "novelty, coherence, and validation reports must refer to one candidate",
        )
    effective_validation = (
        validation.validation_score
        if validation.all_declared_gates_passed else 0.0
    )
    return evaluate_aev_frequency(
        n_novel=novelty.novelty_score,
        c_coh=coherence.coherence_score,
        v_valid=effective_validation,
        r_red=novelty.redundancy_score,
        delta_t=delta_t,
        evidence_scope=(
            "TYPED_NOVELTY_COHERENCE_AND_DECLARED_INTERNAL_VALIDATION_"
            "REPORTS_V0.1"
        ),
    )
