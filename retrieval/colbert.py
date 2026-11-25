"""ColBERT late-interaction MaxSim scorer, RRF fusion, Cross-Encoder Reranker, and Hybrid Stack (P4)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from retrieval.bm25 import scheme_to_text, tokenize


def _token_sim(a: str, b: str) -> float:
    if a == b:
        return 1.0
    if len(a) >= 4 and len(b) >= 4 and (a in b or b in a):
        return 0.78
    # Character bigram Dice similarity for inflectional Indic suffixes
    if len(a) >= 3 and len(b) >= 3:
        ba = {a[i : i + 2] for i in range(len(a) - 1)}
        bb = {b[i : i + 2] for i in range(len(b) - 1)}
        inter = len(ba & bb)
        return (2.0 * inter) / max(len(ba) + len(bb), 1)
    return 0.0


class ColBERTRetriever:
    """ColBERT-style late-interaction MaxSim scoring over multilingual scheme tokens."""

    def __init__(self, schemes: List[Dict[str, Any]]) -> None:
        self.schemes = schemes
        self.doc_tokens = [list(set(tokenize(scheme_to_text(s)))) for s in schemes]

    def score_one(self, query_tokens: List[str], doc_idx: int) -> float:
        dtoks = self.doc_tokens[doc_idx]
        if not query_tokens or not dtoks:
            return 0.0
        total = 0.0
        for qt in query_tokens:
            best = max((_token_sim(qt, dt) for dt in dtoks), default=0.0)
            total += best
        return total / len(query_tokens)

    def search(
        self,
        query: str,
        top_k: int = 5,
        state: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[Tuple[Dict[str, Any], float]]:
        q_tokens = tokenize(query)
        scored: List[Tuple[int, float]] = []
        for idx, s in enumerate(self.schemes):
            if state and s["state"] not in (state, "All India"):
                continue
            if category and s["category"].lower() != category.lower():
                continue
            scored.append((idx, self.score_one(q_tokens, idx)))
        scored.sort(key=lambda item: (-item[1], self.schemes[item[0]]["scheme_id"]))
        return [(self.schemes[idx], round(sc, 4)) for idx, sc in scored[:top_k]]
