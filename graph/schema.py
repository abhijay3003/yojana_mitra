"""P5 GraphRAG Schema: Node types and Edge types for Indian Welfare Knowledge Graph."""

from __future__ import annotations

from typing import Tuple

NODE_TYPES: Tuple[str, ...] = (
    "Scheme",
    "Ministry",
    "State",
    "BeneficiaryCategory",
    "Document",
    "Benefit",
)

EDGE_TYPES: Tuple[str, ...] = (
    "requires_document",
    "eligible_if",
    "supersedes",
    "sub_scheme_of",
    "complementary_to",
    "mutually_exclusive_with",
    "administered_by",
    "applies_in_state",
    "provides_benefit",
)
