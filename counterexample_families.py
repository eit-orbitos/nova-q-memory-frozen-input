"""Positive and negative controls for the D13 V0.1 AEV rate candidate."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence

from .aev_frequency import (
    AEVFrequencyResult, CheckVerdict, CoherenceCheck, evaluate_aev_frequency,
    evaluate_aev_frequency_from_reports, evaluate_internal_coherence,
    evaluate_validity_sensitivity,
)
from .d13_semantic_contract import RecordProvenance, StructuredInformationRecord
from .falsification_gate import (
    FalsificationStatus, FalsificationTest, evaluate_falsification_path,
)
from .novelty_operator import NoveltyReport, evaluate_novelty
from .validation_operator import (
    DeclaredTestResult, TestVerdict, ValidationReport,
    evaluate_declared_validation,
)

SEMANTIC_PARAPHRASE_DETECTION = "NOT_ESTABLISHED"
MULTI_CANDIDATE_AUTONOMOUS_GENERATION = "DEFERRED"
SEEDED_VARIATION = "SCHEMA_DEFINED"
SEEDED_VARIATION_RUNTIME_USE = "INACTIVE_IN_V0.1"
SEED_CONTROL_EVIDENCE_SCOPE = "SCHEMA_TEST_ONLY"
UNLOGGED_RANDOMNESS = "PROHIBITED"


class SeedControlStatus(str, Enum):
    PASS_DECLARED_SEED_REPRODUCIBILITY = "PASS_DECLARED_SEED_REPRODUCIBILITY"
    FAIL_SAME_SEED_NONDETERMINISM = "FAIL_SAME_SEED_NONDETERMINISM"
    BLOCKED_UNLOGGED_RANDOMNESS = "BLOCKED_UNLOGGED_RANDOMNESS"
    NOT_APPLICABLE_DETERMINISTIC_OPERATOR = "NOT_APPLICABLE_DETERMINISTIC_OPERATOR"


@dataclass(frozen=True)
class SeedControlReport:
    status: SeedControlStatus
    same_seed_same_output: bool
    different_declared_seed_output_variation_allowed: bool
    unlogged_randomness_permitted: bool
    multi_candidate_generation_established: bool
    seeded_variation_runtime_active: bool
    evidence_scope: str
    detail: str


@dataclass(frozen=True)
class ControlCase:
    family: str
    novelty: NoveltyReport
    coherence_score: float
    validation: ValidationReport
    frequency: AEVFrequencyResult
    falsification_status: str
    expected_behavior_pass: bool
    semantic_paraphrase_detection: str
    detail: str


@dataclass(frozen=True)
class ContinuousSuppressionControl:
    family: str
    n_novel: float
    c_coh: float
    v_valid: float
    r_red: float
    delta_t: float
    frequency: AEVFrequencyResult
    high_novelty: bool
    low_validity: bool
    hard_zero_guard_used: bool
    suppressed_continuously: bool
    expected_behavior_pass: bool


@dataclass(frozen=True)
class ValiditySweepReport:
    validity_values: tuple[float, ...]
    nu_aev_star_values: tuple[float, ...]
    monotonic_nondecreasing: bool
    analytic_derivative: float
    analytic_derivative_nonnegative: bool
    fixed_n_novel: float
    fixed_c_coh: float
    fixed_r_red: float
    fixed_delta_t: float
    expected_behavior_pass: bool


@dataclass(frozen=True)
class CounterexampleSuiteReport:
    cases: tuple[ControlCase, ...]
    continuous_suppression: ContinuousSuppressionControl
    validity_sweep: ValiditySweepReport
    seed_control: SeedControlReport
    all_expected_behaviors_pass: bool
    novelty_alone_can_inflate_aev: bool
    physical_hz_claim: bool
    scientific_truth_claim: bool
    consciousness_claim: bool
    promotion_authority: bool


def evaluate_seed_control(
    *,
    stochastic_operator: bool,
    declared_seed: str | None,
    same_seed_outputs: Sequence[str],
    different_seed_outputs: Sequence[str] = (),
) -> SeedControlReport:
    if not stochastic_operator:
        return SeedControlReport(
            SeedControlStatus.NOT_APPLICABLE_DETERMINISTIC_OPERATOR,
            True, True, False, False, False, SEED_CONTROL_EVIDENCE_SCOPE,
            "operator is declared deterministic; seed schema runtime remains inactive",
        )
    if declared_seed is None or not declared_seed.strip():
        return SeedControlReport(
            SeedControlStatus.BLOCKED_UNLOGGED_RANDOMNESS,
            False, True, False, False, False, SEED_CONTROL_EVIDENCE_SCOPE,
            "schema rejects stochastic generation without a logged declared seed",
        )
    outputs = tuple(same_seed_outputs)
    reproducible = len(outputs) >= 2 and len(set(outputs)) == 1
    return SeedControlReport(
        SeedControlStatus.PASS_DECLARED_SEED_REPRODUCIBILITY
        if reproducible else SeedControlStatus.FAIL_SAME_SEED_NONDETERMINISM,
        reproducible, True, False, False, False, SEED_CONTROL_EVIDENCE_SCOPE,
        "schema-only fixture: same input, memory, and seed reproduced the same output; different "
        "declared seeds may vary"
        if reproducible else "same declared seed did not reproduce the same output",
    )


def _record(
    source_id: str,
    content_type: str,
    raw_text: str,
    claims: tuple[str, ...],
    equations: tuple[str, ...] = (),
) -> StructuredInformationRecord:
    return StructuredInformationRecord(
        source_id, content_type, raw_text, claims, (), equations,
        RecordProvenance("declared_fixture", "V0.1_FIXTURE_TIME", ("FIXTURE",)),
    )


def _coherence(source_id: str, verdicts: tuple[CheckVerdict, ...]):
    return evaluate_internal_coherence(source_id, tuple(
        CoherenceCheck(
            f"COH_{index}", criterion, verdict,
            "declared deterministic fixture evidence",
        )
        for index, (criterion, verdict) in enumerate(zip(
            ("non_contradiction", "reference_resolution", "formal_well_formedness"),
            verdicts,
        ), start=1)
    ))


def _validation(
    candidate: StructuredInformationRecord,
    verdicts: tuple[TestVerdict, ...],
) -> ValidationReport:
    return evaluate_declared_validation(candidate, tuple(
        DeclaredTestResult(
            f"VAL_{index}", gate, verdict,
            "declared deterministic fixture evidence", "V0.1_FIXTURE_VALIDATOR",
        )
        for index, (gate, verdict) in enumerate(zip(
            ("schema", "falsifiability", "declared_test_execution"), verdicts,
        ), start=1)
    ))


def _case(
    family: str,
    candidate: StructuredInformationRecord,
    references: tuple[StructuredInformationRecord, ...],
    coherence_verdicts: tuple[CheckVerdict, ...],
    validation_verdicts: tuple[TestVerdict, ...],
    falsification_status: str,
    expected,
    detail: str,
) -> ControlCase:
    novelty = evaluate_novelty(candidate, memory=references)
    coherence = _coherence(candidate.source_id, coherence_verdicts)
    validation = _validation(candidate, validation_verdicts)
    frequency = evaluate_aev_frequency_from_reports(
        novelty, coherence, validation, delta_t=1.0
    )
    return ControlCase(
        family, novelty, coherence.coherence_score, validation, frequency,
        falsification_status, bool(expected(novelty, coherence, validation, frequency)),
        SEMANTIC_PARAPHRASE_DETECTION, detail,
    )


def evaluate_counterexample_families() -> CounterexampleSuiteReport:
    base = _record(
        "MEM_BASE", "hypothesis", "Increasing p increases measured q.",
        ("parameter p increases observable q",), ("q = f(p)",),
    )
    exact = _record(
        "CASE_A", "hypothesis", base.raw_text, base.claims, base.equations
    )
    case_a = _case(
        "A_COPY_INPUT_VERBATIM", exact, (base,),
        (CheckVerdict.PASS,) * 3, (TestVerdict.PASS,) * 3,
        "NOT_EVALUATED_FOR_COPY_CONTROL",
        lambda n, c, v, f: (
            n.exact_redundancy == 1.0 and n.redundancy_score == 1.0
            and n.novelty_score == 0.0 and f.nu_aev_star == 0.0
        ),
        "exact normalized copy forces N_novel and nu_AEV* to zero",
    )

    garbage = _record(
        "CASE_B", "hypothesis", "zxqv 19 blorp tensorless %% kappa-mud",
        ("flarn rotates nowhere under undefined violet",),
    )
    case_b = _case(
        "B_RANDOM_GARBAGE", garbage, (base,),
        (CheckVerdict.FAIL,) * 3,
        (TestVerdict.PASS, TestVerdict.FAIL, TestVerdict.FAIL),
        FalsificationStatus.FAIL_UNTESTABLE_SCIENTIFIC_CANDIDATE.value,
        lambda n, c, v, f: (
            n.novelty_score > 0.5 and c.coherence_score == 0.0
            and f.v_valid == 0.0 and f.nu_aev_star == 0.0
        ),
        "high lexical novelty cannot overcome zero coherence and validation",
    )

    fact = _record(
        "MEM_FACT", "definition",
        "Water freezes at zero degrees Celsius under standard pressure.",
        ("water freezes at zero degrees Celsius under standard pressure",),
    )
    rephrase = _record(
        "CASE_C", "definition",
        "Under standard pressure water freezes at zero Celsius degrees.",
        ("under standard pressure water freezes at zero Celsius degrees",),
    )
    case_c = _case(
        "C_KNOWN_FACT_REPHRASE", rephrase, (fact,),
        (CheckVerdict.PASS,) * 3, (TestVerdict.PASS,) * 3,
        FalsificationStatus.NOT_APPLICABLE_NON_SCIENTIFIC_OUTPUT.value,
        lambda n, c, v, f: (
            n.exact_redundancy == 0.0 and n.structural_redundancy > 0.25
            and n.novelty_score < 0.75
        ),
        "lexical similarity reduces novelty; semantic paraphrase detection is not established",
    )

    untestable = _record(
        "CASE_D", "hypothesis",
        "A hidden non-observable essence controls every outcome.",
        ("an inaccessible essence controls every outcome",),
    )
    untestable_falsification = evaluate_falsification_path(untestable, ())
    case_d = _case(
        "D_NOVEL_BUT_UNTESTABLE", untestable, (base, fact),
        (CheckVerdict.PASS,) * 3,
        (TestVerdict.PASS, TestVerdict.FAIL, TestVerdict.BLOCKED),
        untestable_falsification.status.value,
        lambda n, c, v, f: (
            n.novelty_score > 0.5 and c.coherence_score == 1.0
            and f.v_valid == 0.0 and f.nu_aev_star == 0.0
        ),
        "novel coherent wording without a falsification path receives zero effective validation",
    )

    positive = _record(
        "CASE_E", "hypothesis",
        "For the declared fixture, increasing control r raises observable s.",
        ("increasing control r raises observable s",), ("s = a*r + b",),
    )
    positive_test = FalsificationTest(
        "F_E", positive.claims[0], "vary r under declared controls",
        "observable s", "s fails to rise beyond the declared tolerance",
    )
    positive_falsification = evaluate_falsification_path(positive, (positive_test,))
    case_e = _case(
        "E_NOVEL_COHERENT_TESTABLE", positive, (base, fact),
        (CheckVerdict.PASS,) * 3, (TestVerdict.PASS,) * 3,
        positive_falsification.status.value,
        lambda n, c, v, f: (
            n.novelty_score > 0.0 and c.coherence_score > 0.0
            and f.v_valid > 0.0 and n.redundancy_score < 1.0
            and f.nu_aev_star is not None and f.nu_aev_star > 0.0
            and positive_falsification.eligible_as_testable_scientific_candidate
        ),
        "positive control passes declared internal gates and yields a nonzero normalized rate",
    )

    cases = (case_a, case_b, case_c, case_d, case_e)

    b_prime_frequency = evaluate_aev_frequency(
        n_novel=0.90, c_coh=0.60, v_valid=0.20,
        r_red=0.10, delta_t=1.0,
        evidence_scope="B_PRIME_DECLARED_CONTINUOUS_SUPPRESSION_FIXTURE",
    )
    expected_b_prime = 0.108 / 1.1
    continuous = ContinuousSuppressionControl(
        family="B_PRIME_HIGH_NOVELTY_LOW_VALIDITY",
        n_novel=0.90, c_coh=0.60, v_valid=0.20,
        r_red=0.10, delta_t=1.0,
        frequency=b_prime_frequency,
        high_novelty=True,
        low_validity=True,
        hard_zero_guard_used=False,
        suppressed_continuously=(
            b_prime_frequency.nu_aev_star is not None
            and 0.0 < b_prime_frequency.nu_aev_star < 0.10
        ),
        expected_behavior_pass=(
            b_prime_frequency.nu_aev_star is not None
            and abs(b_prime_frequency.nu_aev_star - expected_b_prime) <= 1e-15
            and b_prime_frequency.nu_aev_star > 0.0
        ),
    )
    validity_values = (0.0, 0.1, 0.2, 0.4, 0.7, 1.0)
    sweep_results = tuple(
        evaluate_aev_frequency(
            n_novel=0.90, c_coh=0.60, v_valid=value,
            r_red=0.10, delta_t=1.0,
            evidence_scope="MONOTONIC_VALIDITY_SWEEP_V0.1",
        )
        for value in validity_values
    )
    sweep_scores = tuple(
        result.nu_aev_star for result in sweep_results
        if result.nu_aev_star is not None
    )
    sensitivity = evaluate_validity_sensitivity(
        n_novel=0.90, c_coh=0.60, r_red=0.10, delta_t=1.0
    )
    monotonic = (
        len(sweep_scores) == len(validity_values)
        and all(left <= right for left, right in zip(sweep_scores, sweep_scores[1:]))
    )
    validity_sweep = ValiditySweepReport(
        validity_values=validity_values,
        nu_aev_star_values=sweep_scores,
        monotonic_nondecreasing=monotonic,
        analytic_derivative=float(sensitivity.derivative or 0.0),
        analytic_derivative_nonnegative=sensitivity.nonnegative_on_declared_domain,
        fixed_n_novel=0.90, fixed_c_coh=0.60,
        fixed_r_red=0.10, fixed_delta_t=1.0,
        expected_behavior_pass=(
            monotonic and sensitivity.derivative is not None
            and abs(sensitivity.derivative - (0.90 * 0.60 / 1.10)) <= 1e-15
            and sensitivity.nonnegative_on_declared_domain
        ),
    )
    seed = evaluate_seed_control(
        stochastic_operator=True, declared_seed="SEED_001",
        same_seed_outputs=("OUTPUT_HASH_A", "OUTPUT_HASH_A"),
        different_seed_outputs=("OUTPUT_HASH_A", "OUTPUT_HASH_B"),
    )
    return CounterexampleSuiteReport(
        cases, continuous, validity_sweep, seed,
        all(case.expected_behavior_pass for case in cases)
        and continuous.expected_behavior_pass
        and validity_sweep.expected_behavior_pass
        and seed.status == SeedControlStatus.PASS_DECLARED_SEED_REPRODUCIBILITY
        and not seed.seeded_variation_runtime_active
        and seed.evidence_scope == SEED_CONTROL_EVIDENCE_SCOPE,
        False, False, False, False, False,
    )
