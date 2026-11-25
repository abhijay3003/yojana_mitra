"""Reciprocal Rank Fusion (RRF) for combining BM25, BGE-M3, and ColBERT rankings."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


def reciprocal_rank_fusion(
    ranked_lists: List[List[Tuple[Dict[str, Any], float]]],
    weights: List[float] | None = None,
    k: int = 60,
    top_k: int = 10,
) -> List[Tuple[Dict[str, Any], float]]:
    """Fuse multiple ranked candidate lists using weighted Reciprocal Rank Fusion."""
    w = weights or [1.0] * len(ranked_lists)
    scores: Dict[str, float] = {}
    items: Dict[str, Dict[str, Any]] = {}

    for list_idx, rlist in enumerate(ranked_lists):
        weight = w[list_idx]
        for rank, (scheme, _) in enumerate(rlist, start=1):
            sid = scheme["scheme_id"]
            items[sid] = scheme
            scores[sid] = scores.get(sid, 0.0) + weight * (1.0 / (k + rank))

    ordered = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    return [(items[sid], round(sc, 5)) for sid, sc in ordered[:top_k]]
