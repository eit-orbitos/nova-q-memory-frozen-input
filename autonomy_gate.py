"""Model-internal autonomy gate for D13 V0.1.

Autonomy here means proposal generation without manual specification of every
output step.  It does not establish consciousness, agency, will, or promotion.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence


class AutonomyStatus(str, Enum):
    PASS_MODEL_INTERNAL_AUTONOMOUS_GENERATION = (
        "PASS_MODEL_INTERNAL_AUTONOMOUS_GENERATION"
    )
    FAIL_FULLY_MANUAL_OUTPUT = "FAIL_FULLY_MANUAL_OUTPUT"
    BLOCKED_INCOMPLETE_TRACE = "BLOCKED_INCOMPLETE_TRACE"


@dataclass(frozen=True)
class GenerationStep:
    step_id: str
    operator_id: str
    input_ids: tuple[str, ...]
    output_ids: tuple[str, ...]
    manually_specified_output: bool
    provenance_receipt: str

    def __post_init__(self) -> None:
        if any(not value.strip() for value in (
            self.step_id, self.operator_id, self.provenance_receipt
        )):
            raise ValueError("step, operator, and provenance receipt are required")
        if not self.input_ids or not self.output_ids:
            raise ValueError("generation step requires input and output IDs")
        if any(not value.strip() for value in self.input_ids + self.output_ids):
            raise ValueError("generation IDs must be non-empty")


@dataclass(frozen=True)
class AutonomyReport:
    status: AutonomyStatus
    step_count: int
    operator_ids: tuple[str, ...]
    manually_specified_step_count: int
    model_internal_autonomy_established: bool
    consciousness_established: bool
    independent_will_established: bool
    physical_agency_established: bool
    promotion_authority: bool
    detail: str


def evaluate_autonomy(trace: Sequence[GenerationStep]) -> AutonomyReport:
    steps = tuple(trace)
    if not steps or any(not isinstance(step, GenerationStep) for step in steps):
        return AutonomyReport(
            AutonomyStatus.BLOCKED_INCOMPLETE_TRACE, len(steps), (), 0,
            False, False, False, False, False,
            "an explicit generation trace is required",
        )
    step_ids = tuple(step.step_id for step in steps)
    if len(step_ids) != len(set(step_ids)):
        return AutonomyReport(
            AutonomyStatus.BLOCKED_INCOMPLETE_TRACE, len(steps),
            tuple(step.operator_id for step in steps), 0,
            False, False, False, False, False,
            "generation step IDs must be unique",
        )
    produced: set[str] = set()
    for step in steps:
        if produced and not (set(step.input_ids) & produced):
            return AutonomyReport(
                AutonomyStatus.BLOCKED_INCOMPLETE_TRACE, len(steps),
                tuple(item.operator_id for item in steps),
                sum(item.manually_specified_output for item in steps),
                False, False, False, False, False,
                "trace is disconnected from prior generated outputs",
            )
        produced.update(step.output_ids)
    manual = sum(step.manually_specified_output for step in steps)
    autonomous = manual < len(steps)
    status = (
        AutonomyStatus.PASS_MODEL_INTERNAL_AUTONOMOUS_GENERATION
        if autonomous else AutonomyStatus.FAIL_FULLY_MANUAL_OUTPUT
    )
    return AutonomyReport(
        status, len(steps), tuple(step.operator_id for step in steps), manual,
        autonomous, False, False, False, False,
        "at least one traced transformation was not manually output-specified"
        if autonomous else "every output transformation was manually specified",
    )
