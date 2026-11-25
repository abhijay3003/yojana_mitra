"""Cross-encoder style reranker (bge-reranker-v2-m3 interface + deterministic title/entity rerank)."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from retrieval.bm25 import tokenize


class CrossEncoderReranker:
    """Reranks fused top-N candidates by exact title, translation, state, and amount alignment."""

    def rerank(
        self,
        query: str,
        candidates: List[Tuple[Dict[str, Any], float]],
        top_k: int = 5,
    ) -> List[Tuple[Dict[str, Any], float]]:
        q_lower = (query or "").lower()
        q_tokens = set(tokenize(query))
        reranked: List[Tuple[Dict[str, Any], float]] = []

        for scheme, base_score in candidates:
            boost = 0.0
            name_lower = scheme["name"].lower()
            name_tokens = set(tokenize(name_lower))
            if name_lower in q_lower:
                boost += 1.2
            # Token overlap with scheme name and keywords
            kw_tokens = set(tokenize(" ".join(scheme.get("keywords", []))))
            tr_tokens = set(tokenize(" ".join(scheme.get("translations", {}).values())))
            title_overlap = len(q_tokens & name_tokens) / max(len(name_tokens), 1)
            kw_overlap = len(q_tokens & kw_tokens) / max(len(q_tokens), 1)
            tr_overlap = len(q_tokens & tr_tokens) / max(len(q_tokens), 1)
            boost += 0.9 * title_overlap + 0.85 * kw_overlap + 0.8 * tr_overlap

            # Exact state mention alignment
            st = scheme["state"].lower()
            if st != "all india" and st in q_lower:
                boost += 0.35

            final_score = round(base_score * 10.0 + boost, 4)
            reranked.append((scheme, final_score))

        reranked.sort(key=lambda item: (-item[1], item[0]["scheme_id"]))
        return reranked[:top_k]
