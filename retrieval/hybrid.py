"""Hybrid Retrieval Pipeline (P4): BM25 + BGE-M3 + ColBERT -> RRF -> Reranker."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from retrieval.bge_m3 import BGEM3HybridEncoder
from retrieval.bm25 import BM25Retriever
from retrieval.colbert import ColBERTRetriever
from retrieval.reranker import CrossEncoderReranker
from retrieval.rrf import reciprocal_rank_fusion


class HybridRetriever:
    """Unified 4-stage retrieval stack with layer-wise ablation support."""

    def __init__(self, schemes: List[Dict[str, Any]]) -> None:
        self.schemes = schemes
        self.bm25 = BM25Retriever(schemes)
        self.bge_m3 = BGEM3HybridEncoder(schemes)
        self.colbert = ColBERTRetriever(schemes)
        self.reranker = CrossEncoderReranker()

    def search(
        self,
        query: str,
        top_k: int = 5,
        state: Optional[str] = None,
        category: Optional[str] = None,
        mode: str = "full",
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Retrieve top-k schemes under chosen ablation mode: bm25 | bge_m3 | rrf | full."""
        if mode == "bm25":
            return self.bm25.search(query, top_k=top_k, state=state, category=category)
        if mode == "bge_m3":
            return self.bge_m3.search(query, top_k=top_k, state=state, category=category)

        r_bm25 = self.bm25.search(query, top_k=20, state=state, category=category)
        r_bge = self.bge_m3.search(query, top_k=20, state=state, category=category)
        r_col = self.colbert.search(query, top_k=20, state=state, category=category)
        fused = reciprocal_rank_fusion([r_bm25, r_bge, r_col], weights=[1.1, 1.0, 1.0], top_k=15)

        if mode == "rrf":
            return fused[:top_k]
        return self.reranker.rerank(query, fused, top_k=top_k)
