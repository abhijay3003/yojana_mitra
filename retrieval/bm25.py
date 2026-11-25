"""BM25 Okapi retriever (P4) with zero external dependency fallback + rank_bm25 compatibility."""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

TOKEN_RE = re.compile(r"[\w\u0900-\u097F\u0B80-\u0BFF\u0C00-\u0C7F\u0C80-\u0CFF]+", re.UNICODE)


def tokenize(text: str) -> List[str]:
    """Multilingual Unicode-aware tokenizer supporting Latin, Telugu, Devanagari, Kannada, Tamil."""
    return [t.lower() for t in TOKEN_RE.findall(text or "") if len(t) >= 2]


def scheme_to_text(scheme: Dict[str, Any]) -> str:
    """Build unified multilingual searchable document for a scheme."""
    parts = [
        str(scheme.get("name", "")),
        str(scheme.get("scheme_id", "")),
        str(scheme.get("state", "")),
        str(scheme.get("category", "")),
        str(scheme.get("ministry", "")),
        str(scheme.get("benefits", "")),
        str(scheme.get("eligibility_text", "")),
        " ".join(scheme.get("documents", [])),
        " ".join(scheme.get("keywords", [])),
    ]
    translations = scheme.get("translations", {})
    if isinstance(translations, dict):
        parts.extend(str(v) for v in translations.values())
    return " ".join(parts)


class BM25Retriever:
    """Okapi BM25 retriever with optional metadata filtering."""

    def __init__(self, schemes: List[Dict[str, Any]], k1: float = 1.5, b: float = 0.75) -> None:
        self.schemes = schemes
        self.k1 = k1
        self.b = b
        self.docs_tokens: List[List[str]] = [tokenize(scheme_to_text(s)) for s in schemes]
        self.doc_freqs: Dict[str, int] = {}
        self.doc_lens: List[int] = []
        self.term_freqs: List[Counter[str]] = []

        for tokens in self.docs_tokens:
            self.doc_lens.append(len(tokens))
            tf = Counter(tokens)
            self.term_freqs.append(tf)
            for term in tf:
                self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1

        self.avgdl = sum(self.doc_lens) / max(len(self.doc_lens), 1)
        self.n_docs = len(schemes)

    def _idf(self, term: str) -> float:
        df = self.doc_freqs.get(term, 0)
        return math.log(1.0 + (self.n_docs - df + 0.5) / (df + 0.5))

    def search(
        self,
        query: str,
        top_k: int = 5,
        state: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Score and return top-k schemes matching query with optional metadata filters."""
        q_tokens = tokenize(query)
        scored: List[Tuple[int, float]] = []

        for idx, s in enumerate(self.schemes):
            if state and s["state"] not in (state, "All India"):
                continue
            if category and s["category"].lower() != category.lower():
                continue

            tf = self.term_freqs[idx]
            dl = self.doc_lens[idx]
            score = 0.0
            for qt in q_tokens:
                f = tf.get(qt, 0)
                if f == 0:
                    continue
                idf = self._idf(qt)
                denom = f + self.k1 * (1.0 - self.b + self.b * (dl / max(self.avgdl, 1.0)))
                score += idf * ((f * (self.k1 + 1.0)) / denom)
            scored.append((idx, score))

        scored.sort(key=lambda item: (-item[1], self.schemes[item[0]]["scheme_id"]))
        return [(self.schemes[idx], round(sc, 4)) for idx, sc in scored[:top_k]]
