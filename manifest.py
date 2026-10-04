"""Deterministic content and source-tree manifests for D13 V0.1.

ZIP identity is deliberately separate and remains unset until a later release
build.  This module does not freeze bytes or authorize promotion.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .audit import run_audit
from .d13_semantic_contract import ARTIFACT_ID, PARENT_ARTIFACT

DECLARED_SOURCE_FILES = (
    "d13_semantic_contract.py",
    "information_fluid_state.py",
    "novelty_operator.py",
    "validation_operator.py",
    "autonomy_gate.py",
    "provenance_graph.py",
    "falsification_gate.py",
    "aev_frequency.py",
    "counterexample_families.py",
    "audit.py",
    "manifest.py",
    "test_d13_full.py",
)


@dataclass(frozen=True)
class SourceFileIdentity:
    path: str
    sha256: str
    size_bytes: int


@dataclass(frozen=True)
class D13ManifestReport:
    content_manifest_sha256: str
    source_tree_manifest_sha256: str
    zip_sha256: str | None
    zip_status: str
    source_count: int
    source_tree_complete: bool
    freeze_authorized: bool
    promotion_authority: bool
    content_manifest: dict[str, Any]
    source_tree_manifest: dict[str, Any]


def _canonical_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")


def _sha256(payload: Any) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def build_content_manifest() -> dict[str, Any]:
    audit = run_audit()
    return {
        "metadata": {
            "artifact_id": ARTIFACT_ID,
            "version": "0.1",
            "status": "AUTHOR_PROPOSED_NON_NORMATIVE_MODEL",
            "d13_status": "EXTENSION_CANDIDATE",
            "promotion_status": "NOT_YET_PROMOTED",
            "freeze_status": "NOT_FROZEN",
        },
        "parent_lineage": {
            "declared_parent": PARENT_ARTIFACT,
            "parent_byte_identity_verified_here": False,
        },
        "semantic_contract": {
            "symbol": "nu_AEV_star",
            "role": "MODEL_INTERNAL_GENERATIVE_TRANSFORMATION_COORDINATE_CANDIDATE",
            "current_promoted_model_coordinate_count": 12,
            "d_int_contribution": "UNRESOLVED",
            "input_format": "STRUCTURED_JSON_FIRST",
            "x12_coupling": "DEFAULT_DENY_TYPED_NAMED_RECEIPT_REQUIRED",
        },
        "information_fluid_state": {
            "status": "DETERMINISTIC_MODEL_ABSTRACTION",
            "explicit_i_raw": True,
            "explicit_i_mem": True,
            "random_initialization": "PROHIBITED_BY_DEFAULT",
            "physical_fluid_claim": False,
        },
        "novelty_metrics": {
            "n_novel_range": [0.0, 1.0],
            "r_exact": "DEFINED",
            "r_struct_lexical": "DEFINED_DETERMINISTIC_TOKEN_BIGRAM_JACCARD",
            "truth_inference": False,
        },
        "validation_metrics": {
            "c_coh": "INTERNAL_COHERENCE_SCORE",
            "v_valid": "PASSED_DECLARED_INTERNAL_VALIDATION_GATES",
            "coherence_implies_validation": False,
            "validation_implies_scientific_truth": False,
        },
        "autonomy_boundary": {
            "model_internal_autonomy": "DEFINED",
            "consciousness": "NOT_ESTABLISHED",
            "independent_will": "NOT_ESTABLISHED",
            "multi_candidate_generation": "DEFERRED",
            "seeded_variation_schema": "DEFINED",
            "seeded_variation_runtime": "INACTIVE_IN_V0.1",
        },
        "provenance": {
            "deterministic_dag": "DEFINED",
            "source_truth_inference": False,
        },
        "falsification": {
            "scientific_candidate_requires_path": True,
            "path_implies_truth": False,
        },
        "aev_frequency": {
            "formula": "N_novel*C_coh*V_valid/(delta_t*(1+R_red))",
            "status": "EXECUTABLE_NORMALIZED_MODEL_INTERNAL_RATE_CANDIDATE",
            "units": "NORMALIZED_MODEL_INTERNAL_RATE",
            "physical_hz": "PROHIBITED",
        },
        "counterexample_families": {
            "exact_copy_zero": True,
            "random_garbage_zero": True,
            "high_novelty_low_validity_continuously_suppressed": True,
            "known_fact_rephrase_lexically_reduced": True,
            "untestable_candidate_zero": True,
            "coherent_testable_positive": True,
        },
        "known_limitations": {
            "semantic_paraphrase_detection": "NOT_YET_SOLVED",
            "embeddings": "DEFERRED",
            "multi_candidate_generation": "DEFERRED",
            "seeded_variation_runtime": "INACTIVE_IN_V0.1",
            "external_network_reads": "NOT_REQUIRED_FOR_CORE_V0.1",
        },
        "non_claims": {
            "scientific_truth": "NOT_ESTABLISHED",
            "physical_frequency": "PROHIBITED",
            "ai_consciousness": "NOT_ESTABLISHED",
            "physical_dimension": "NOT_ESTABLISHED",
            "promotion_authority": False,
        },
        "audit_summary": {
            "canonical_verdict": audit.canonical_verdict,
            "passed": audit.passed_count,
            "total": audit.total_count,
            "model_status": audit.d13_model,
        },
        "test_summary": {
            "full_suite_required": True,
            "result_is_runtime_generated_not_embedded": True,
            "independent_reexecution": "NOT_PERFORMED",
        },
    }


def build_source_tree_manifest(root: Path | None = None) -> dict[str, Any]:
    base = root if root is not None else Path(__file__).resolve().parent
    identities: list[SourceFileIdentity] = []
    missing: list[str] = []
    for name in DECLARED_SOURCE_FILES:
        path = base / name
        if not path.is_file():
            missing.append(name)
            continue
        data = path.read_bytes()
        identities.append(SourceFileIdentity(
            name, hashlib.sha256(data).hexdigest(), len(data)
        ))
    return {
        "artifact_id": ARTIFACT_ID,
        "inventory_policy": "DECLARED_PYTHON_SOURCES_ONLY_NO_CACHE_BYTECODE",
        "declared_files": list(DECLARED_SOURCE_FILES),
        "files": [asdict(item) for item in identities],
        "missing_files": missing,
        "complete": not missing and len(identities) == len(DECLARED_SOURCE_FILES),
    }


def build_manifest(
    *, root: Path | None = None, zip_sha256: str | None = None
) -> D13ManifestReport:
    if zip_sha256 is not None and (
        len(zip_sha256) != 64
        or any(char not in "0123456789abcdef" for char in zip_sha256)
    ):
        raise ValueError("zip_sha256 must be a lowercase SHA-256 digest")
    content = build_content_manifest()
    source_tree = build_source_tree_manifest(root)
    return D13ManifestReport(
        content_manifest_sha256=_sha256(content),
        source_tree_manifest_sha256=_sha256(source_tree),
        zip_sha256=zip_sha256,
        zip_status="IDENTIFIED" if zip_sha256 else "NOT_BUILT_SEPARATE_RELEASE_STEP",
        source_count=len(source_tree["files"]),
        source_tree_complete=bool(source_tree["complete"]),
        freeze_authorized=False,
        promotion_authority=False,
        content_manifest=content,
        source_tree_manifest=source_tree,
    )
