"""Deterministic exact-copy, structural-similarity, and novelty operators.

The scores are model-internal V0.1 metrics.  They make no truth, validity,
scientific-discovery, consciousness, or promotion claim.  Embeddings are not
used.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Sequence

from .d13_semantic_contract import StructuredInformationRecord
from .information_fluid_state import normalize_text, record_semantic_text, tokenize


class NoveltyStatus(str, Enum):
    EVALUATED = "EVALUATED"
    BLOCKED_EMPTY_CANDIDATE = "BLOCKED_EMPTY_CANDIDATE"
    EXACT_COPY_BLOCKED = "EXACT_COPY_BLOCKED"


@dataclass(frozen=True)
class PairSimilarity:
    reference_source_id: str
    exact_similarity: float
    token_jaccard: float
    bigram_jaccard: float
    structural_similarity: float


@dataclass(frozen=True)
class NoveltyReport:
    status: NoveltyStatus
    candidate_source_id: str
    exact_redundancy: float
    structural_redundancy: float
    redundancy_score: float
    novelty_score: float
    closest_reference_source_id: str | None
    comparisons: tuple[PairSimilarity, ...]
    truth_claim: bool
    validity_claim: bool
    embeddings_used: bool
    detail: str


def _jaccard(left: Iterable[object], right: Iterable[object]) -> float:
    a, b = set(left), set(right)
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _bigrams(tokens: Sequence[str]) -> tuple[tuple[str, str], ...]:
    return tuple(zip(tokens, tokens[1:]))


def exact_duplicate_score(candidate_text: str, reference_text: str) -> float:
    """Return 1 only for exact equality after deterministic NFKC/case/space normalization."""
    candidate = normalize_text(candidate_text)
    reference = normalize_text(reference_text)
    return 1.0 if candidate and candidate == reference else 0.0


def structural_similarity_score(candidate_text: str, reference_text: str) -> tuple[float, float, float]:
    """Return deterministic lexical structural similarity without embeddings.

    V0.1 combines token-set Jaccard (60%) and adjacent-token-bigram Jaccard
    (40%).  This detects lexical rephrasing only; it is not semantic equivalence.
    """
    candidate_tokens = tokenize(candidate_text)
    reference_tokens = tokenize(reference_text)
    token_score = _jaccard(candidate_tokens, reference_tokens)
    bigram_score = _jaccard(_bigrams(candidate_tokens), _bigrams(reference_tokens))
    score = 0.6 * token_score + 0.4 * bigram_score
    return token_score, bigram_score, min(1.0, max(0.0, score))


def evaluate_novelty(
    candidate: StructuredInformationRecord,
    *,
    memory: Sequence[StructuredInformationRecord] = (),
    sources: Sequence[StructuredInformationRecord] = (),
) -> NoveltyReport:
    """Evaluate N_novel=1-R_red against explicit memory and source records.

    R_exact is the maximum normalized exact-copy score.  R_struct is the
    maximum deterministic lexical structural score.  R_red=max(R_exact,
    R_struct).  No validation or scientific-truth inference is performed.
    """
    candidate_text = record_semantic_text(candidate)
    if not normalize_text(candidate_text):
        return NoveltyReport(
            NoveltyStatus.BLOCKED_EMPTY_CANDIDATE, candidate.source_id,
            0.0, 0.0, 0.0, 0.0, None, (), False, False, False,
            "candidate has no normalized semantic content",
        )
    references = tuple(memory) + tuple(sources)
    seen_ids: set[str] = set()
    comparisons: list[PairSimilarity] = []
    for reference in references:
        if reference.source_id in seen_ids:
            raise ValueError("reference source_id values must be unique")
        seen_ids.add(reference.source_id)
        reference_text = record_semantic_text(reference)
        exact = exact_duplicate_score(candidate_text, reference_text)
        token_score, bigram_score, structural = structural_similarity_score(
            candidate_text, reference_text
        )
        comparisons.append(
            PairSimilarity(
                reference.source_id, exact, token_score, bigram_score, structural
            )
        )
    exact_redundancy = max((item.exact_similarity for item in comparisons), default=0.0)
    structural_redundancy = max(
        (item.structural_similarity for item in comparisons), default=0.0
    )
    redundancy = max(exact_redundancy, structural_redundancy)
    novelty = 1.0 - redundancy
    closest = max(comparisons, key=lambda item: item.structural_similarity, default=None)
    status = (
        NoveltyStatus.EXACT_COPY_BLOCKED
        if exact_redundancy == 1.0
        else NoveltyStatus.EVALUATED
    )
    detail = (
        "verbatim normalized duplicate detected; novelty blocked"
        if status == NoveltyStatus.EXACT_COPY_BLOCKED
        else "deterministic lexical novelty evaluated; validity remains unevaluated"
    )
    return NoveltyReport(
        status=status,
        candidate_source_id=candidate.source_id,
        exact_redundancy=exact_redundancy,
        structural_redundancy=structural_redundancy,
        redundancy_score=redundancy,
        novelty_score=novelty,
        closest_reference_source_id=(closest.reference_source_id if closest else None),
        comparisons=tuple(comparisons),
        truth_claim=False,
        validity_claim=False,
        embeddings_used=False,
        detail=detail,
    )
