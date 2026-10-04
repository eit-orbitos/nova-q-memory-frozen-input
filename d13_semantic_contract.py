"""Semantic contract for the D13 Autonomous Evolutionary Vector candidate.

This module declares a model-internal extension candidate only.  It does not
promote D13, establish a physical frequency, or make an AI-consciousness claim.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

ARTIFACT_ID = "EIT_13D_AUTONOMOUS_EVOLUTIONARY_VECTOR_V0.1"
PARENT_ARTIFACT = "EIT_12D_PROJECTION_AND_DYNAMICS_INTEGRATION_V0.2"
STATUS = "AUTHOR_PROPOSED_NON_NORMATIVE_MODEL"

D13_SYMBOL = "nu_AEV_star"
D13_NAME = "Autonomous Evolutionary Vector Frequency Candidate"
D13_ROLE = "MODEL_INTERNAL_GENERATIVE_TRANSFORMATION_COORDINATE_CANDIDATE"
D13_STATUS = "EXTENSION_CANDIDATE"
CURRENT_PROMOTED_MODEL_COORDINATE_COUNT = 12
X13_STATUS = "CANDIDATE_EXTENDED_STATE"
D_INT_CONTRIBUTION = "UNRESOLVED"
PROMOTION_STATUS = "NOT_YET_PROMOTED"

INPUT_FORMAT = "STRUCTURED_JSON_FIRST"
PLAIN_TEXT_POLICY = "ALLOWED_ONLY_AS_RAW_PAYLOAD"
EMBEDDINGS_POLICY = "DEFERRED"
EXTERNAL_NETWORK_READS = "NOT_REQUIRED_FOR_CORE_V0.1"
RANDOM_INITIALIZATION = "PROHIBITED_BY_DEFAULT"
X12_TO_D13_COUPLING = "NOT_AUTOMATIC"
COUPLING_RECEIPT_POLICY = "REQUIRED"

NU_AEV_STAR_STATUS = "NORMALIZED_MODEL_INTERNAL_TRANSFORMATION_RATE_CANDIDATE"
PHYSICAL_HZ_CLAIM = "PROHIBITED"
AI_CONSCIOUSNESS_CLAIM = "NOT_ESTABLISHED"
PHYSICAL_DIMENSION_CLAIM = "NOT_ESTABLISHED"
VALIDATION_SEMANTICS = "PASSED_DECLARED_INTERNAL_VALIDATION_GATES"
SCIENTIFIC_TRUTH_INFERENCE = "PROHIBITED"

X12_STATE_ORDER = (
    "E_H", "E_LOCK", "Phi_H", "pi", "S_H", "T_H", "F_H",
    "Q_H", "M_H", "B_H", "C_I", "rho_H",
)


class ContractStatus(str, Enum):
    VALID = "VALID"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class RecordProvenance:
    origin: str
    timestamp: str
    transformation_history: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.origin.strip():
            raise ValueError("provenance origin is required")
        if not self.timestamp.strip():
            raise ValueError("explicit model-defined timestamp is required")
        if any(not item.strip() for item in self.transformation_history):
            raise ValueError("transformation history entries must be non-empty")


@dataclass(frozen=True)
class StructuredInformationRecord:
    source_id: str
    content_type: str
    raw_text: str
    claims: tuple[str, ...]
    definitions: tuple[str, ...]
    equations: tuple[str, ...]
    provenance: RecordProvenance

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError("source_id is required")
        if not self.content_type.strip():
            raise ValueError("content_type is required")
        if not self.raw_text.strip():
            raise ValueError("plain text is allowed only as a non-empty raw_text payload")
        for field_name in ("claims", "definitions", "equations"):
            values = getattr(self, field_name)
            if any(not isinstance(value, str) or not value.strip() for value in values):
                raise ValueError(f"{field_name} entries must be non-empty strings")

    def as_mapping(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "content_type": self.content_type,
            "raw_text": self.raw_text,
            "claims": list(self.claims),
            "definitions": list(self.definitions),
            "equations": list(self.equations),
            "provenance": {
                "origin": self.provenance.origin,
                "timestamp": self.provenance.timestamp,
                "transformation_history": list(self.provenance.transformation_history),
            },
        }


_REQUIRED_RECORD_FIELDS = {
    "source_id", "content_type", "raw_text", "claims", "definitions",
    "equations", "provenance",
}
_REQUIRED_PROVENANCE_FIELDS = {"origin", "timestamp"}


def _string_tuple(value: Any, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"{field_name} must be a JSON list of strings")
    return tuple(value)


def record_from_mapping(payload: Mapping[str, Any]) -> StructuredInformationRecord:
    """Parse a strict deterministic structured record; unknown fields are blocked."""
    keys = set(payload)
    if keys != _REQUIRED_RECORD_FIELDS:
        raise ValueError(
            f"record fields must exactly equal {sorted(_REQUIRED_RECORD_FIELDS)}; "
            f"missing={sorted(_REQUIRED_RECORD_FIELDS - keys)}, extra={sorted(keys - _REQUIRED_RECORD_FIELDS)}"
        )
    provenance_raw = payload["provenance"]
    if not isinstance(provenance_raw, Mapping):
        raise ValueError("provenance must be a JSON object")
    provenance_keys = set(provenance_raw)
    allowed_provenance = _REQUIRED_PROVENANCE_FIELDS | {"transformation_history"}
    if not _REQUIRED_PROVENANCE_FIELDS <= provenance_keys or not provenance_keys <= allowed_provenance:
        raise ValueError("provenance requires origin/timestamp and only permits transformation_history additionally")
    scalar_fields = ("source_id", "content_type", "raw_text")
    if any(not isinstance(payload[field], str) for field in scalar_fields):
        raise ValueError("source_id, content_type, and raw_text must be strings")
    history = provenance_raw.get("transformation_history", [])
    return StructuredInformationRecord(
        source_id=payload["source_id"],
        content_type=payload["content_type"],
        raw_text=payload["raw_text"],
        claims=_string_tuple(payload["claims"], "claims"),
        definitions=_string_tuple(payload["definitions"], "definitions"),
        equations=_string_tuple(payload["equations"], "equations"),
        provenance=RecordProvenance(
            origin=str(provenance_raw["origin"]),
            timestamp=str(provenance_raw["timestamp"]),
            transformation_history=_string_tuple(history, "transformation_history"),
        ),
    )


def record_from_json(payload: str) -> StructuredInformationRecord:
    decoded = json.loads(payload)
    if not isinstance(decoded, Mapping):
        raise ValueError("canonical input must be a JSON object")
    return record_from_mapping(decoded)


def canonical_record_json(record: StructuredInformationRecord) -> str:
    return json.dumps(
        record.as_mapping(), ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    )


@dataclass(frozen=True)
class X12CouplingReceipt:
    source_artifact: str
    target: str
    law_identifier: str
    allowed_fields: tuple[str, ...]
    purpose: str
    provenance: str
    version: str = "0.1"
    state_mutating_authority: str = "READ_ONLY"


def validate_x12_coupling_receipt(receipt: X12CouplingReceipt | None) -> tuple[bool, str]:
    if receipt is None:
        return False, "named X12-to-D13 coupling receipt is required"
    if not isinstance(receipt, X12CouplingReceipt):
        return False, "typed X12CouplingReceipt is required; bare authorization flags are prohibited"
    text_fields = (
        receipt.source_artifact, receipt.target, receipt.law_identifier,
        receipt.purpose, receipt.provenance, receipt.version,
        receipt.state_mutating_authority,
    )
    if any(not field.strip() for field in text_fields):
        return False, "coupling receipt has a missing semantic field"
    if receipt.target != "D13.nu_AEV_star":
        return False, "coupling target must be D13.nu_AEV_star"
    if receipt.state_mutating_authority != "READ_ONLY":
        return False, "X12 coupling must be read-only"
    if not receipt.allowed_fields:
        return False, "receipt must whitelist at least one X12 field"
    if len(set(receipt.allowed_fields)) != len(receipt.allowed_fields):
        return False, "allowed_fields contains duplicates"
    unknown = set(receipt.allowed_fields) - set(X12_STATE_ORDER)
    if unknown:
        return False, f"receipt contains unknown X12 fields: {sorted(unknown)}"
    return True, "VALID"


def canonical_status() -> dict[str, Any]:
    return {
        "artifact_id": ARTIFACT_ID,
        "parent_artifact": PARENT_ARTIFACT,
        "status": STATUS,
        "d13_symbol": D13_SYMBOL,
        "d13_status": D13_STATUS,
        "current_promoted_model_coordinate_count": CURRENT_PROMOTED_MODEL_COORDINATE_COUNT,
        "x13_status": X13_STATUS,
        "nu_aev_star_status": NU_AEV_STAR_STATUS,
        "d_int_contribution": D_INT_CONTRIBUTION,
        "promotion_status": PROMOTION_STATUS,
        "physical_hz_claim": PHYSICAL_HZ_CLAIM,
        "ai_consciousness_claim": AI_CONSCIOUSNESS_CLAIM,
        "x12_to_d13_coupling": X12_TO_D13_COUPLING,
    }
