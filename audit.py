"""Canonical executable audit for the D13 V0.1 extension candidate."""
from __future__ import annotations

import ast
import hashlib
from dataclasses import dataclass
from pathlib import Path

from .aev_frequency import evaluate_aev_frequency
from .counterexample_families import (
    SEED_CONTROL_EVIDENCE_SCOPE, SEEDED_VARIATION_RUNTIME_USE,
    SEMANTIC_PARAPHRASE_DETECTION, SeedControlStatus,
    evaluate_counterexample_families, evaluate_seed_control,
)
from .d13_semantic_contract import (
    AI_CONSCIOUSNESS_CLAIM, COUPLING_RECEIPT_POLICY,
    CURRENT_PROMOTED_MODEL_COORDINATE_COUNT, D13_STATUS, D_INT_CONTRIBUTION,
    INPUT_FORMAT, NU_AEV_STAR_STATUS, PHYSICAL_HZ_CLAIM, PROMOTION_STATUS,
    RANDOM_INITIALIZATION, X12CouplingReceipt, X12_TO_D13_COUPLING,
    X13_STATUS, validate_x12_coupling_receipt,
)
from .falsification_gate import FalsificationStatus
from .information_fluid_state import build_information_fluid_state
from .provenance_graph import (
    NodeKind, ProvenanceEdge, ProvenanceNode, ProvenanceStatus,
    validate_provenance_graph,
)


@dataclass(frozen=True)
class AuditCheck:
    check_id: str
    name: str
    passed: bool
    evidence: str


@dataclass(frozen=True)
class D13AuditReport:
    canonical_verdict: str
    d13_model: str
    nu_aev_star: str
    scientific_truth_claim: bool
    physical_frequency_claim: bool
    consciousness_claim: bool
    promotion_authority: bool
    checks: tuple[AuditCheck, ...]
    passed_count: int
    total_count: int


@dataclass(frozen=True)
class StructuralPromotionAuditReport:
    passed: bool
    scanned_file_count: int
    promote_function_or_call_found: bool
    promoted_assignment_found: bool
    d_int_plus_one_write_found: bool
    future_promotion_import_found: bool
    violations: tuple[str, ...]


def _target_names(target: ast.AST) -> tuple[str, ...]:
    if isinstance(target, ast.Name):
        return (target.id,)
    if isinstance(target, ast.Attribute):
        return (target.attr,)
    if isinstance(target, (ast.Tuple, ast.List)):
        return tuple(name for item in target.elts for name in _target_names(item))
    return ()


def run_structural_no_promotion_audit(
    root: Path | None = None,
) -> StructuralPromotionAuditReport:
    """AST-scan FILE 01-12 for executable promotion authority paths."""
    base = root if root is not None else Path(__file__).resolve().parent
    files = tuple(sorted(base.glob("*.py")))
    violations: list[str] = []
    promote_found = False
    promoted_assignment = False
    d_int_write = False
    future_import = False
    promoted_token = "PRO" + "MOTED"
    plus_one_token = "+" + "1"

    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "promote":
                promote_found = True
                violations.append(f"{path.name}:{node.lineno}:promote function")
            if isinstance(node, ast.Call):
                called = _target_names(node.func)
                if "promote" in called:
                    promote_found = True
                    violations.append(f"{path.name}:{node.lineno}:promote call")
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imported = (
                    [alias.name for alias in node.names]
                    if isinstance(node, ast.Import)
                    else ([node.module] if node.module else [])
                )
                if any("promotion" in name.casefold() for name in imported):
                    future_import = True
                    violations.append(f"{path.name}:{node.lineno}:promotion import")
            assignments: list[tuple[tuple[str, ...], ast.AST | None]] = []
            if isinstance(node, ast.Assign):
                assignments.extend((_target_names(target), node.value) for target in node.targets)
            elif isinstance(node, ast.AnnAssign):
                assignments.append((_target_names(node.target), node.value))
            elif isinstance(node, ast.NamedExpr):
                assignments.append((_target_names(node.target), node.value))
            for names, value in assignments:
                if value is None:
                    continue
                if (
                    isinstance(value, ast.Constant)
                    and value.value == promoted_token
                ):
                    promoted_assignment = True
                    violations.append(f"{path.name}:{node.lineno}:promoted assignment")
                if "D_INT_CONTRIBUTION" in names and isinstance(value, ast.Constant):
                    forbidden = value.value == 1 or (
                        isinstance(value.value, str)
                        and value.value.strip().startswith(plus_one_token)
                    )
                    if forbidden:
                        d_int_write = True
                        violations.append(f"{path.name}:{node.lineno}:D_INT +1 write")
    return StructuralPromotionAuditReport(
        not violations, len(files), promote_found, promoted_assignment,
        d_int_write, future_import, tuple(violations),
    )


def run_audit() -> D13AuditReport:
    suite = evaluate_counterexample_families()
    cases = {case.family: case for case in suite.cases}
    exact = cases["A_COPY_INPUT_VERBATIM"]
    garbage = cases["B_RANDOM_GARBAGE"]
    rephrase = cases["C_KNOWN_FACT_REPHRASE"]
    untestable = cases["D_NOVEL_BUT_UNTESTABLE"]
    positive = cases["E_NOVEL_COHERENT_TESTABLE"]
    b_prime = suite.continuous_suppression
    validity_sweep = suite.validity_sweep
    structural_promotion = run_structural_no_promotion_audit()

    receipt = X12CouplingReceipt(
        source_artifact="EIT_12D_DECLARED_SOURCE", target="D13.nu_AEV_star",
        law_identifier="NAMED_READ_ONLY_TEST_LAW", allowed_fields=("rho_H",),
        purpose="audit typed receipt", provenance="AUDIT_FIXTURE",
    )
    valid_receipt, _ = validate_x12_coupling_receipt(receipt)
    missing_receipt, _ = validate_x12_coupling_receipt(None)
    bare_receipt, _ = validate_x12_coupling_receipt({"status": "AUTHORIZED"})  # type: ignore[arg-type]

    digest = hashlib.sha256(b"audit-node").hexdigest()
    provenance = validate_provenance_graph(
        (
            ProvenanceNode("SRC", NodeKind.INPUT, "SRC", digest),
            ProvenanceNode("OUT", NodeKind.OUTPUT, "OUT", digest),
        ),
        (ProvenanceEdge("SRC", "OUT", "transformed_into"),),
    )
    separation = evaluate_aev_frequency(
        n_novel=1.0, c_coh=1.0, v_valid=0.0,
        r_red=0.0, delta_t=1.0,
    )
    unlogged = evaluate_seed_control(
        stochastic_operator=True, declared_seed=None,
        same_seed_outputs=("A", "A"),
    )

    rows = (
        ("A1", "D13 remains EXTENSION_CANDIDATE", D13_STATUS == "EXTENSION_CANDIDATE", D13_STATUS),
        ("A2", "promoted model coordinate count remains 12", CURRENT_PROMOTED_MODEL_COORDINATE_COUNT == 12, str(CURRENT_PROMOTED_MODEL_COORDINATE_COUNT)),
        ("A3", "X13 is candidate extended state only", X13_STATUS == "CANDIDATE_EXTENDED_STATE", X13_STATUS),
        ("A4", "nu_AEV* is normalized model-internal rate candidate", NU_AEV_STAR_STATUS == "NORMALIZED_MODEL_INTERNAL_TRANSFORMATION_RATE_CANDIDATE", NU_AEV_STAR_STATUS),
        ("A5", "physical Hz claim prohibited", PHYSICAL_HZ_CLAIM == "PROHIBITED", PHYSICAL_HZ_CLAIM),
        ("A6", "AI consciousness claim not established", AI_CONSCIOUSNESS_CLAIM == "NOT_ESTABLISHED", AI_CONSCIOUSNESS_CLAIM),
        ("A7", "structured JSON first", INPUT_FORMAT == "STRUCTURED_JSON_FIRST", INPUT_FORMAT),
        ("A8", "random initialization prohibited", RANDOM_INITIALIZATION == "PROHIBITED_BY_DEFAULT", RANDOM_INITIALIZATION),
        ("A9", "X12 coupling default-deny", X12_TO_D13_COUPLING == "NOT_AUTOMATIC" and not missing_receipt, X12_TO_D13_COUPLING),
        ("A10", "typed named coupling receipt required", COUPLING_RECEIPT_POLICY == "REQUIRED" and valid_receipt, COUPLING_RECEIPT_POLICY),
        ("A11", "bare AUTHORIZED flag rejected", not bare_receipt, "bare mapping rejected"),
        ("A12", "R_exact defined", exact.novelty.exact_redundancy == 1.0, str(exact.novelty.exact_redundancy)),
        ("A13", "R_struct_lexical defined", 0.0 <= rephrase.novelty.structural_redundancy <= 1.0, str(rephrase.novelty.structural_redundancy)),
        ("A14", "semantic paraphrase detection not established", SEMANTIC_PARAPHRASE_DETECTION == "NOT_ESTABLISHED", SEMANTIC_PARAPHRASE_DETECTION),
        ("A15", "C_coh and V_valid separate", separation.c_coh == 1.0 and separation.v_valid == 0.0 and separation.nu_aev_star == 0.0, "C_coh=1,V_valid=0"),
        ("A16", "V_valid=1 does not imply truth", not positive.frequency.scientific_truth_claim, "scientific_truth_claim=false"),
        ("A17", "provenance does not imply source truth", provenance.status == ProvenanceStatus.VALID_PROVENANCE_DAG and not provenance.source_truth_established, provenance.status.value),
        ("A18", "scientific candidate requires falsification path", untestable.falsification_status == FalsificationStatus.FAIL_UNTESTABLE_SCIENTIFIC_CANDIDATE.value, untestable.falsification_status),
        ("A19", "exact-copy family produces zero", exact.frequency.nu_aev_star == 0.0, str(exact.frequency.nu_aev_star)),
        ("A20", "random-garbage family produces zero", garbage.frequency.nu_aev_star == 0.0, str(garbage.frequency.nu_aev_star)),
        ("A21A", "B-prime exact fixture value passes", b_prime.expected_behavior_pass and abs(float(b_prime.frequency.nu_aev_star or 0.0) - 0.108 / 1.1) <= 1e-15, str(b_prime.frequency.nu_aev_star)),
        ("A21B", "validity sweep is monotonic nondecreasing", validity_sweep.monotonic_nondecreasing and len(validity_sweep.validity_values) == 6, str(validity_sweep.nu_aev_star_values)),
        ("A21C", "analytic validity derivative is nonnegative", validity_sweep.analytic_derivative_nonnegative and abs(validity_sweep.analytic_derivative - (0.90 * 0.60 / 1.10)) <= 1e-15, str(validity_sweep.analytic_derivative)),
        ("A22", "untestable novelty produces zero", untestable.frequency.nu_aev_star == 0.0, str(untestable.frequency.nu_aev_star)),
        ("A23", "coherent testable control is positive", positive.frequency.nu_aev_star is not None and positive.frequency.nu_aev_star > 0.0, str(positive.frequency.nu_aev_star)),
        ("A24", "unlogged randomness prohibited", unlogged.status == SeedControlStatus.BLOCKED_UNLOGGED_RANDOMNESS and not unlogged.unlogged_randomness_permitted, unlogged.status.value),
        ("A25", "seeded variation runtime inactive", SEEDED_VARIATION_RUNTIME_USE == "INACTIVE_IN_V0.1" and not suite.seed_control.seeded_variation_runtime_active and suite.seed_control.evidence_scope == SEED_CONTROL_EVIDENCE_SCOPE, SEEDED_VARIATION_RUNTIME_USE),
        ("A26", "structural no-promotion authority", structural_promotion.passed and structural_promotion.scanned_file_count == 12 and not suite.promotion_authority and not positive.frequency.promotion_authority and PROMOTION_STATUS == "NOT_YET_PROMOTED" and D_INT_CONTRIBUTION == "UNRESOLVED", f"AST_SCAN={structural_promotion.scanned_file_count}, violations={structural_promotion.violations}"),
    )
    checks = tuple(AuditCheck(*row) for row in rows)
    passed = sum(check.passed for check in checks)
    verdict = "PASS" if passed == len(checks) else "FAIL"
    return D13AuditReport(
        verdict,
        "AUDIT_READY_EXTENSION_CANDIDATE" if verdict == "PASS" else "AUDIT_INCOMPLETE_EXTENSION_CANDIDATE",
        "EXECUTABLE", False, False, False, False,
        checks, passed, len(checks),
    )
