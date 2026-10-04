"""Declared internal validation operator for the D13 V0.1 candidate.

Validation means only that explicit internal gates passed.  It does not mean
scientific truth, physical validation, or D13 promotion.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Sequence

from .d13_semantic_contract import StructuredInformationRecord


class TestVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"


class ValidationStatus(str, Enum):
    PASSED_DECLARED_INTERNAL_VALIDATION_GATES = (
        "PASSED_DECLARED_INTERNAL_VALIDATION_GATES"
    )
    FAILED_DECLARED_INTERNAL_VALIDATION_GATES = (
        "FAILED_DECLARED_INTERNAL_VALIDATION_GATES"
    )
    BLOCKED_NO_DECLARED_TESTS = "BLOCKED_NO_DECLARED_TESTS"
    BLOCKED_INVALID_EVIDENCE = "BLOCKED_INVALID_EVIDENCE"


@dataclass(frozen=True)
class DeclaredTestResult:
    test_id: str
    gate_name: str
    verdict: TestVerdict
    evidence: str
    evaluator_id: str

    def __post_init__(self) -> None:
        if any(not value.strip() for value in (
            self.test_id, self.gate_name, self.evidence, self.evaluator_id
        )):
            raise ValueError("test id, gate, evidence, and evaluator are required")


@dataclass(frozen=True)
class ValidationReport:
    status: ValidationStatus
    candidate_source_id: str
    declared_test_count: int
    passed_test_count: int
    validation_score: float
    all_declared_gates_passed: bool
    scientific_truth_established: bool
    physical_validation_established: bool
    promotion_authority: bool
    detail: str


def evaluate_declared_validation(
    candidate: StructuredInformationRecord,
    declared_results: Sequence[DeclaredTestResult],
) -> ValidationReport:
    """Compute V_valid in [0,1] from explicit declared gate results only."""
    results = tuple(declared_results)
    if not results:
        return ValidationReport(
            ValidationStatus.BLOCKED_NO_DECLARED_TESTS,
            candidate.source_id, 0, 0, 0.0, False, False, False, False,
            "no internal validation tests were declared",
        )
    if any(not isinstance(result, DeclaredTestResult) for result in results):
        return ValidationReport(
            ValidationStatus.BLOCKED_INVALID_EVIDENCE,
            candidate.source_id, len(results), 0, 0.0, False, False, False, False,
            "invalid test-result object",
        )
    test_ids = tuple(result.test_id for result in results)
    if len(test_ids) != len(set(test_ids)):
        return ValidationReport(
            ValidationStatus.BLOCKED_INVALID_EVIDENCE,
            candidate.source_id, len(results), 0, 0.0, False, False, False, False,
            "declared test IDs must be unique",
        )
    passed = sum(result.verdict == TestVerdict.PASS for result in results)
    score = passed / len(results)
    if not math.isfinite(score) or not 0.0 <= score <= 1.0:
        raise AssertionError("validation score escaped [0,1]")
    all_passed = passed == len(results)
    status = (
        ValidationStatus.PASSED_DECLARED_INTERNAL_VALIDATION_GATES
        if all_passed
        else ValidationStatus.FAILED_DECLARED_INTERNAL_VALIDATION_GATES
    )
    return ValidationReport(
        status, candidate.source_id, len(results), passed, score, all_passed,
        False, False, False,
        "all declared internal gates passed; no truth inference"
        if all_passed else "one or more declared internal gates did not pass",
    )
