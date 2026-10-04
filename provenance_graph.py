"""Deterministic provenance DAG for D13 V0.1 generated structures."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Sequence


class NodeKind(str, Enum):
    INPUT = "INPUT"
    MEMORY = "MEMORY"
    OPERATOR = "OPERATOR"
    OUTPUT = "OUTPUT"
    VALIDATION = "VALIDATION"


class ProvenanceStatus(str, Enum):
    VALID_PROVENANCE_DAG = "VALID_PROVENANCE_DAG"
    BLOCKED_INVALID_GRAPH = "BLOCKED_INVALID_GRAPH"
    BLOCKED_UNPROVENANCED_OUTPUT = "BLOCKED_UNPROVENANCED_OUTPUT"


@dataclass(frozen=True)
class ProvenanceNode:
    node_id: str
    kind: NodeKind
    artifact_ref: str
    content_sha256: str

    def __post_init__(self) -> None:
        if any(not value.strip() for value in (
            self.node_id, self.artifact_ref, self.content_sha256
        )):
            raise ValueError("node ID, artifact reference, and hash are required")
        if len(self.content_sha256) != 64 or any(
            char not in "0123456789abcdef" for char in self.content_sha256
        ):
            raise ValueError("content_sha256 must be a lowercase SHA-256 digest")


@dataclass(frozen=True)
class ProvenanceEdge:
    source_id: str
    target_id: str
    relation: str

    def __post_init__(self) -> None:
        if any(not value.strip() for value in (
            self.source_id, self.target_id, self.relation
        )):
            raise ValueError("edge source, target, and relation are required")


@dataclass(frozen=True)
class ProvenanceReport:
    status: ProvenanceStatus
    node_count: int
    edge_count: int
    graph_sha256: str | None
    acyclic: bool
    all_outputs_provenanced: bool
    source_truth_established: bool
    detail: str


def _has_cycle(node_ids: set[str], edges: tuple[ProvenanceEdge, ...]) -> bool:
    adjacency = {node_id: [] for node_id in node_ids}
    indegree = {node_id: 0 for node_id in node_ids}
    for edge in edges:
        adjacency[edge.source_id].append(edge.target_id)
        indegree[edge.target_id] += 1
    queue = sorted(node_id for node_id, degree in indegree.items() if degree == 0)
    visited = 0
    while queue:
        current = queue.pop(0)
        visited += 1
        for target in sorted(adjacency[current]):
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
                queue.sort()
    return visited != len(node_ids)


def validate_provenance_graph(
    nodes: Sequence[ProvenanceNode], edges: Sequence[ProvenanceEdge]
) -> ProvenanceReport:
    node_tuple, edge_tuple = tuple(nodes), tuple(edges)
    if not node_tuple or any(not isinstance(node, ProvenanceNode) for node in node_tuple):
        return ProvenanceReport(
            ProvenanceStatus.BLOCKED_INVALID_GRAPH, len(node_tuple), len(edge_tuple),
            None, False, False, False, "valid explicit nodes are required",
        )
    node_ids = tuple(node.node_id for node in node_tuple)
    if len(node_ids) != len(set(node_ids)):
        return ProvenanceReport(
            ProvenanceStatus.BLOCKED_INVALID_GRAPH, len(node_tuple), len(edge_tuple),
            None, False, False, False, "node IDs must be unique",
        )
    known = set(node_ids)
    if any(
        not isinstance(edge, ProvenanceEdge)
        or edge.source_id not in known or edge.target_id not in known
        or edge.source_id == edge.target_id
        for edge in edge_tuple
    ):
        return ProvenanceReport(
            ProvenanceStatus.BLOCKED_INVALID_GRAPH, len(node_tuple), len(edge_tuple),
            None, False, False, False, "edges must connect distinct known nodes",
        )
    cyclic = _has_cycle(known, edge_tuple)
    if cyclic:
        return ProvenanceReport(
            ProvenanceStatus.BLOCKED_INVALID_GRAPH, len(node_tuple), len(edge_tuple),
            None, False, False, False, "provenance graph contains a cycle",
        )
    incoming = {edge.target_id for edge in edge_tuple}
    output_ids = {node.node_id for node in node_tuple if node.kind == NodeKind.OUTPUT}
    outputs_provenanced = bool(output_ids) and output_ids <= incoming
    if not outputs_provenanced:
        return ProvenanceReport(
            ProvenanceStatus.BLOCKED_UNPROVENANCED_OUTPUT,
            len(node_tuple), len(edge_tuple), None, True, False, False,
            "every output must have at least one incoming provenance edge",
        )
    canonical = json.dumps(
        {
            "nodes": sorted((n.node_id, n.kind.value, n.artifact_ref, n.content_sha256) for n in node_tuple),
            "edges": sorted((e.source_id, e.target_id, e.relation) for e in edge_tuple),
        }, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8")
    return ProvenanceReport(
        ProvenanceStatus.VALID_PROVENANCE_DAG, len(node_tuple), len(edge_tuple),
        hashlib.sha256(canonical).hexdigest(), True, True, False,
        "deterministic lineage established; source truth is not inferred",
    )
