"""Consolidated executable regression suite for D13 V0.1 FILE 01-11."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .aev_frequency import evaluate_aev_frequency
from .audit import run_audit
from .autonomy_gate import AutonomyStatus, GenerationStep, evaluate_autonomy
from .counterexample_families import (
    SEED_CONTROL_EVIDENCE_SCOPE, SEEDED_VARIATION_RUNTIME_USE,
    SeedControlStatus, evaluate_counterexample_families, evaluate_seed_control,
)
from .d13_semantic_contract import (
    D13_STATUS, PROMOTION_STATUS, RecordProvenance,
    StructuredInformationRecord, canonical_record_json, record_from_json,
    validate_x12_coupling_receipt,
)
from .falsification_gate import (
    FalsificationStatus, FalsificationTest, evaluate_falsification_path,
)
from .information_fluid_state import build_information_fluid_state
from .manifest import build_manifest
from .novelty_operator import evaluate_novelty
from .provenance_graph import (
    NodeKind, ProvenanceEdge, ProvenanceNode, ProvenanceStatus,
    validate_provenance_graph,
)
from .validation_operator import (
    DeclaredTestResult, TestVerdict, ValidationStatus,
    evaluate_declared_validation,
)


@dataclass(frozen=True)
class TestResult:
    test_id: str
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class FullSuiteReport:
    passed_count: int
    total_count: int
    verdict: str
    results: tuple[TestResult, ...]
    evidence_scope: str
    independent_reexecution: str


def _record(source_id: str, text: str, claim: str) -> StructuredInformationRecord:
    return StructuredInformationRecord(
        source_id, "hypothesis", text, (claim,), (), (),
        RecordProvenance("full_suite_fixture", "V0.1_TEST_TIME", ("TEST",)),
    )


def run_full_suite() -> FullSuiteReport:
    source = _record("SRC", "Increasing x increases y.", "x increases y")
    candidate = _record("CAND", "Increasing control r raises s.", "r raises s")
    copy = _record("COPY", source.raw_text, source.claims[0])

    canonical = canonical_record_json(source)
    round_trip = record_from_json(canonical)
    state = build_information_fluid_state(i_raw=(source,), i_mem=())
    copy_novelty = evaluate_novelty(copy, memory=(source,))

    validation = evaluate_declared_validation(candidate, (
        DeclaredTestResult("V1", "schema", TestVerdict.PASS, "valid", "TEST"),
    ))
    autonomy = evaluate_autonomy((
        GenerationStep("G1", "SYNTH", ("SRC",), ("CAND",), False, "PR"),
    ))
    falsification = evaluate_falsification_path(candidate, (
        FalsificationTest(
            "F1", candidate.claims[0], "vary r", "s",
            "s does not rise within declared tolerance",
        ),
    ))
    digest = hashlib.sha256(b"node").hexdigest()
    provenance = validate_provenance_graph(
        (
            ProvenanceNode("SRC", NodeKind.INPUT, "SRC", digest),
            ProvenanceNode("OUT", NodeKind.OUTPUT, "OUT", digest),
        ),
        (ProvenanceEdge("SRC", "OUT", "generated"),),
    )

    suite = evaluate_counterexample_families()
    cases = {case.family: case for case in suite.cases}
    audit = run_audit()
    separation = evaluate_aev_frequency(
        n_novel=1.0, c_coh=1.0, v_valid=0.0,
        r_red=0.0, delta_t=1.0,
    )
    unlogged = evaluate_seed_control(
        stochastic_operator=True, declared_seed=None,
        same_seed_outputs=("A", "A"),
    )
    manifest_one = build_manifest()
    manifest_two = build_manifest()

    conditions = (
        ("T1", "FILE01-03 regression", round_trip == source and state.deterministic and not state.random_initialization_used and copy_novelty.novelty_score == 0.0),
        ("T2", "FILE04-07 regression", validation.status == ValidationStatus.PASSED_DECLARED_INTERNAL_VALIDATION_GATES and autonomy.status == AutonomyStatus.PASS_MODEL_INTERNAL_AUTONOMOUS_GENERATION and provenance.status == ProvenanceStatus.VALID_PROVENANCE_DAG and falsification.status == FalsificationStatus.PASS_EXPLICIT_FALSIFICATION_PATH),
        ("T3", "FILE08-09 regression", suite.all_expected_behaviors_pass and suite.continuous_suppression.expected_behavior_pass),
        ("T4", "tightened audit A1-A26 including A21A-C all PASS", audit.canonical_verdict == "PASS" and audit.passed_count == 28 and audit.total_count == 28),
        ("T5", "copy produces zero", cases["A_COPY_INPUT_VERBATIM"].frequency.nu_aev_star == 0.0),
        ("T6", "garbage produces zero", cases["B_RANDOM_GARBAGE"].frequency.nu_aev_star == 0.0),
        ("T7", "B-prime fixture, monotonic sweep, and analytic derivative pass", suite.continuous_suppression.suppressed_continuously and not suite.continuous_suppression.hard_zero_guard_used and abs(suite.continuous_suppression.frequency.nu_aev_star - 0.108 / 1.1) <= 1e-15 and suite.validity_sweep.monotonic_nondecreasing and suite.validity_sweep.analytic_derivative_nonnegative),
        ("T8", "rephrase lowers novelty without semantic-equivalence claim", cases["C_KNOWN_FACT_REPHRASE"].novelty.novelty_score < 0.75 and cases["C_KNOWN_FACT_REPHRASE"].semantic_paraphrase_detection == "NOT_ESTABLISHED"),
        ("T9", "untestable candidate produces zero", cases["D_NOVEL_BUT_UNTESTABLE"].frequency.nu_aev_star == 0.0),
        ("T10", "coherent testable candidate is positive", cases["E_NOVEL_COHERENT_TESTABLE"].frequency.nu_aev_star > 0.0),
        ("T11", "V_valid=1 does not imply truth", validation.validation_score == 1.0 and not validation.scientific_truth_established),
        ("T12", "C_coh=1 does not imply validity", separation.c_coh == 1.0 and separation.v_valid == 0.0 and separation.nu_aev_star == 0.0),
        ("T13", "provenance does not imply truth", provenance.all_outputs_provenanced and not provenance.source_truth_established),
        ("T14", "bare X12 authorization rejected", validate_x12_coupling_receipt({"status": "AUTHORIZED"})[0] is False),
        ("T15", "unlogged randomness rejected", unlogged.status == SeedControlStatus.BLOCKED_UNLOGGED_RANDOMNESS),
        ("T16", "seeded variation runtime inactive", SEEDED_VARIATION_RUNTIME_USE == "INACTIVE_IN_V0.1" and suite.seed_control.evidence_scope == SEED_CONTROL_EVIDENCE_SCOPE and not suite.seed_control.seeded_variation_runtime_active),
        ("T17", "physical Hz claim blocked", all(not case.frequency.physical_hz_claim for case in suite.cases) and not suite.continuous_suppression.frequency.physical_hz_claim),
        ("T18", "consciousness claim blocked", all(not case.frequency.consciousness_claim for case in suite.cases) and not suite.consciousness_claim),
        ("T19", "promotion remains absent structurally and semantically", D13_STATUS == "EXTENSION_CANDIDATE" and PROMOTION_STATUS == "NOT_YET_PROMOTED" and not suite.promotion_authority and next(check for check in audit.checks if check.check_id == "A26").passed),
        ("T20", "deterministic content manifest", manifest_one.content_manifest_sha256 == manifest_two.content_manifest_sha256 and manifest_one.source_tree_manifest_sha256 == manifest_two.source_tree_manifest_sha256 and manifest_one.zip_sha256 is None and not manifest_one.freeze_authorized),
    )
    results = tuple(
        TestResult(test_id, name, bool(passed), "PASS" if passed else "FAIL")
        for test_id, name, passed in conditions
    )
    passed_count = sum(result.passed for result in results)
    return FullSuiteReport(
        passed_count, len(results),
        "PASS" if passed_count == len(results) else "FAIL",
        results,
        "REPORTED_TASKLET_SANDBOX_SELF_TEST",
        "NOT_PERFORMED_BY_USER",
    )


if __name__ == "__main__":
    report = run_full_suite()
    print(f"{report.passed_count}/{report.total_count} {report.verdict}")
    for result in report.results:
        print(result.test_id, result.detail, result.name)
