"""Falsification-path gate for scientific candidates in D13 V0.1."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence

from .d13_semantic_contract import StructuredInformationRecord


_SCIENTIFIC_CONTENT_TYPES = frozenset({
    "hypothesis", "scientific_hypothesis", "empirical_claim"
})


class FalsificationStatus(str, Enum):
    PASS_EXPLICIT_FALSIFICATION_PATH = "PASS_EXPLICIT_FALSIFICATION_PATH"
    FAIL_UNTESTABLE_SCIENTIFIC_CANDIDATE = "FAIL_UNTESTABLE_SCIENTIFIC_CANDIDATE"
    BLOCKED_MISMATCHED_CLAIM = "BLOCKED_MISMATCHED_CLAIM"
    NOT_APPLICABLE_NON_SCIENTIFIC_OUTPUT = "NOT_APPLICABLE_NON_SCIENTIFIC_OUTPUT"


@dataclass(frozen=True)
class FalsificationTest:
    test_id: str
    claim: str
    observation_procedure: str
    measurable_observable: str
    failure_condition: str

    def __post_init__(self) -> None:
        if any(not value.strip() for value in (
            self.test_id, self.claim, self.observation_procedure,
            self.measurable_observable, self.failure_condition,
        )):
            raise ValueError("a falsification test requires all semantic fields")


@dataclass(frozen=True)
class FalsificationReport:
    status: FalsificationStatus
    candidate_source_id: str
    scientific_candidate: bool
    declared_test_count: int
    claims_with_falsification_path: tuple[str, ...]
    eligible_as_testable_scientific_candidate: bool
    scientific_truth_established: bool
    promotion_authority: bool
    detail: str


def evaluate_falsification_path(
    candidate: StructuredInformationRecord,
    tests: Sequence[FalsificationTest],
) -> FalsificationReport:
    scientific = candidate.content_type.casefold() in _SCIENTIFIC_CONTENT_TYPES
    test_tuple = tuple(tests)
    if not scientific:
        return FalsificationReport(
            FalsificationStatus.NOT_APPLICABLE_NON_SCIENTIFIC_OUTPUT,
            candidate.source_id, False, len(test_tuple), (), False, False, False,
            "falsification gate applies only to declared scientific candidates",
        )
    if not test_tuple:
        return FalsificationReport(
            FalsificationStatus.FAIL_UNTESTABLE_SCIENTIFIC_CANDIDATE,
            candidate.source_id, True, 0, (), False, False, False,
            "scientific candidate has no explicit failure condition and test",
        )
    if any(not isinstance(test, FalsificationTest) for test in test_tuple):
        return FalsificationReport(
            FalsificationStatus.BLOCKED_MISMATCHED_CLAIM,
            candidate.source_id, True, len(test_tuple), (), False, False, False,
            "invalid falsification test object",
        )
    test_ids = tuple(test.test_id for test in test_tuple)
    if len(test_ids) != len(set(test_ids)):
        return FalsificationReport(
            FalsificationStatus.BLOCKED_MISMATCHED_CLAIM,
            candidate.source_id, True, len(test_tuple), (), False, False, False,
            "falsification test IDs must be unique",
        )
    candidate_claims = set(candidate.claims)
    tested_claims = {test.claim for test in test_tuple}
    if not candidate_claims or not tested_claims <= candidate_claims:
        return FalsificationReport(
            FalsificationStatus.BLOCKED_MISMATCHED_CLAIM,
            candidate.source_id, True, len(test_tuple), tuple(sorted(tested_claims)),
            False, False, False,
            "every falsification test must reference an exact declared claim",
        )
    missing = candidate_claims - tested_claims
    if missing:
        return FalsificationReport(
            FalsificationStatus.FAIL_UNTESTABLE_SCIENTIFIC_CANDIDATE,
            candidate.source_id, True, len(test_tuple), tuple(sorted(tested_claims)),
            False, False, False,
            f"declared claims without falsification paths: {sorted(missing)}",
        )
    return FalsificationReport(
        FalsificationStatus.PASS_EXPLICIT_FALSIFICATION_PATH,
        candidate.source_id, True, len(test_tuple), tuple(sorted(tested_claims)),
        True, False, False,
        "all declared scientific claims have explicit tests and failure conditions",
    )
