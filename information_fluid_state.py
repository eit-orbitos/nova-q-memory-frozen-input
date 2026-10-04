"""Deterministic information-fluid state abstraction for D13 V0.1.

"Fluid" is a model abstraction, not a physical-fluid claim.  All raw and
retained records are explicit.  No random initialization or automatic X12
aggregation is permitted.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from dataclasses import dataclass, replace
from typing import Mapping, Sequence

from .d13_semantic_contract import (
    StructuredInformationRecord,
    X12CouplingReceipt,
    validate_x12_coupling_receipt,
)

_TOKEN_PATTERN = re.compile(r"[^\W_]+(?:['’-][^\W_]+)*", flags=re.UNICODE)


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return " ".join(normalized.split())


def tokenize(text: str) -> tuple[str, ...]:
    return tuple(_TOKEN_PATTERN.findall(normalize_text(text)))


def record_semantic_text(record: StructuredInformationRecord) -> str:
    parts = (
        record.content_type,
        record.raw_text,
        *record.claims,
        *record.definitions,
        *record.equations,
    )
    return "\n".join(part for part in parts if part.strip())


@dataclass(frozen=True)
class StructuredProjection:
    source_id: str
    normalized_text: str
    tokens: tuple[str, ...]
    deterministic_sha256: str


@dataclass(frozen=True)
class TransformationEvent:
    event_id: str
    operator_id: str
    input_source_ids: tuple[str, ...]
    output_source_ids: tuple[str, ...]
    model_timestamp: str

    def __post_init__(self) -> None:
        values = (self.event_id, self.operator_id, self.model_timestamp)
        if any(not value.strip() for value in values):
            raise ValueError("event_id, operator_id, and explicit model_timestamp are required")
        if not self.input_source_ids or not self.output_source_ids:
            raise ValueError("transformation event requires explicit input and output IDs")


@dataclass(frozen=True)
class InformationFluidState:
    i_raw: tuple[StructuredInformationRecord, ...]
    i_mem: tuple[StructuredInformationRecord, ...]
    i_struct: tuple[StructuredProjection, ...]
    transformation_history: tuple[TransformationEvent, ...]
    x12_context: tuple[tuple[str, float], ...] = ()
    x12_coupling_law: str | None = None
    abstraction_status: str = "MODEL_INTERNAL_INFORMATION_STATE_NOT_PHYSICAL_FLUID"
    deterministic: bool = True
    random_initialization_used: bool = False


@dataclass(frozen=True)
class X12CouplingResult:
    accepted: bool
    state: InformationFluidState | None
    reason: str


def derive_structured_projection(record: StructuredInformationRecord) -> StructuredProjection:
    normalized = normalize_text(record_semantic_text(record))
    canonical = json.dumps(
        {
            "source_id": record.source_id,
            "normalized_text": normalized,
            "tokens": tokenize(normalized),
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return StructuredProjection(
        source_id=record.source_id,
        normalized_text=normalized,
        tokens=tokenize(normalized),
        deterministic_sha256=hashlib.sha256(canonical).hexdigest(),
    )


def build_information_fluid_state(
    *,
    i_raw: Sequence[StructuredInformationRecord],
    i_mem: Sequence[StructuredInformationRecord],
    transformation_history: Sequence[TransformationEvent] = (),
) -> InformationFluidState:
    """Build I_struct deterministically from explicit I_raw and I_mem records."""
    raw = tuple(i_raw)
    memory = tuple(i_mem)
    if not raw:
        raise ValueError("I_raw must contain at least one explicit structured record")
    if any(not isinstance(record, StructuredInformationRecord) for record in raw + memory):
        raise TypeError("I_raw and I_mem may contain only StructuredInformationRecord values")
    source_ids = tuple(record.source_id for record in raw + memory)
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("source_id values must be unique across I_raw and I_mem")
    history = tuple(transformation_history)
    if any(not isinstance(event, TransformationEvent) for event in history):
        raise TypeError("transformation_history contains an invalid event")
    structured = tuple(derive_structured_projection(record) for record in raw + memory)
    return InformationFluidState(
        i_raw=raw,
        i_mem=memory,
        i_struct=structured,
        transformation_history=history,
    )


def apply_x12_coupling(
    state: InformationFluidState,
    x12_state: Mapping[str, float],
    receipt: X12CouplingReceipt | None,
) -> X12CouplingResult:
    """Attach only explicitly whitelisted read-only X12 values; default deny."""
    valid, reason = validate_x12_coupling_receipt(receipt)
    if not valid:
        return X12CouplingResult(False, None, reason)
    assert receipt is not None
    missing = [name for name in receipt.allowed_fields if name not in x12_state]
    if missing:
        return X12CouplingResult(False, None, f"missing receipted X12 fields: {missing}")
    context: list[tuple[str, float]] = []
    for name in receipt.allowed_fields:
        value = x12_state[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            return X12CouplingResult(False, None, f"X12 field {name} must be finite numeric data")
        context.append((name, float(value)))
    coupled = replace(
        state,
        x12_context=tuple(context),
        x12_coupling_law=receipt.law_identifier,
    )
    return X12CouplingResult(True, coupled, "VALID_READ_ONLY_NAMED_COUPLING")
