"""P5 GraphRAG Multi-Hop Retriever over the Welfare Knowledge Graph."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from graph.builder import WelfareKnowledgeGraph, build_knowledge_graph
from retrieval.bm25 import tokenize


class GraphRAGRetriever:
    """Multi-hop graph traversal retriever for complementary, superseded, exclusive, and shared-document queries."""

    def __init__(self, schemes: List[Dict[str, Any]]) -> None:
        self.schemes = schemes
        self.by_id = {s["scheme_id"]: s for s in schemes}
        self.graph: WelfareKnowledgeGraph = build_knowledge_graph(schemes)

    def _find_anchor_schemes(self, query: str) -> List[str]:
        q_lower = query.lower()
        q_tokens = set(tokenize(query))
        scored: List[Tuple[str, float]] = []
        for s in self.schemes:
            sid = s["scheme_id"]
            name_lower = s["name"].lower()
            score = 0.0
            if name_lower in q_lower:
                score += 5.0
            for kw in s.get("keywords", []):
                if kw.lower() in q_lower and len(kw) >= 4:
                    score += 3.0
            name_toks = set(tokenize(name_lower))
            overlap = len(q_tokens & name_toks)
            score += overlap * 0.8
            if score > 0:
                scored.append((sid, score))
        scored.sort(key=lambda x: (-x[1], x[0]))
        return [sid for sid, _ in scored[:3]]

    def _find_anchor_documents(self, query: str) -> List[str]:
        q_lower = query.lower()
        matched: List[Tuple[str, int]] = []
        for nid, node in self.graph.nodes.items():
            if node["type"] != "Document":
                continue
            label_lower = node["label"].lower()
            if label_lower in q_lower:
                matched.append((nid, 10))
            else:
                dtoks = set(tokenize(label_lower))
                qtoks = set(tokenize(query))
                inter = len(dtoks & qtoks)
                if inter >= 2:
                    matched.append((nid, inter))
        matched.sort(key=lambda x: (-x[1], x[0]))
        return [nid for nid, _ in matched[:2]]

    def multi_hop_retrieve(
        self,
        query: str,
        hop_hint: Optional[str] = None,
        anchor_hint: Optional[str] = None,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """Traverse 1–2 hops across the Knowledge Graph to answer relational welfare queries."""
        q_lower = query.lower()
        results: List[str] = []
        paths: List[str] = []

        # Determine target relation intent
        relation = hop_hint
        if not relation:
            if any(w in q_lower for w in ("supersed", "replac", "old version", "legacy")):
                relation = "supersedes"
            elif any(w in q_lower for w in ("mutually exclusive", "cannot be stacked", "conflict")):
                relation = "mutually_exclusive_with"
            elif any(w in q_lower for w in ("share", "require", "document", "passbook", "ration card", "udid", "certificate")):
                relation = "requires_document"
            elif any(w in q_lower for w in ("ministry", "department")):
                relation = "ministry_document"
            else:
                relation = "complementary_to"

        # Route 1: Document -> Schemes sharing that document
        if relation == "requires_document":
            doc_nodes = [f"doc:{anchor_hint}"] if (anchor_hint and f"doc:{anchor_hint}" in self.graph.nodes) else self._find_anchor_documents(query)
            for dnode in doc_nodes:
                linked = self.graph.neighbors(dnode, relation="requires_document", direction="in")
                for snode in linked:
                    sid = snode.replace("scheme:", "")
                    if sid not in results:
                        results.append(sid)
                        paths.append(f"{self.graph.nodes[dnode]['label']} <-[requires_document]- {self.by_id[sid]['name']}")

        # Route 2: Ministry + Document intersection
        elif relation == "ministry_document":
            min_node = f"ministry:{anchor_hint}" if anchor_hint else None
            if not min_node or min_node not in self.graph.nodes:
                for nid, n in self.graph.nodes.items():
                    if n["type"] == "Ministry" and any(t in n["label"].lower() for t in tokenize(query)):
                        min_node = nid
                        break
            if min_node and min_node in self.graph.nodes:
                for snode in self.graph.neighbors(min_node, relation="administered_by", direction="in"):
                    sid = snode.replace("scheme:", "")
                    results.append(sid)
                    paths.append(f"{self.graph.nodes[min_node]['label']} <-[administered_by]- {self.by_id[sid]['name']}")

        # Route 3: Scheme-to-Scheme multi-hop (supersedes + complementary_to + mutually_exclusive_with)
        else:
            anchors = [anchor_hint] if (anchor_hint and anchor_hint in self.by_id) else self._find_anchor_schemes(query)
            for aid in anchors:
                snode = f"scheme:{aid}"
                if relation == "supersedes":
                    # Find who supersedes this legacy scheme (in-edge), then 2nd-hop complementary schemes!
                    replacers = self.graph.neighbors(snode, relation="supersedes", direction="in")
                    if not replacers:
                        replacers = self.graph.neighbors(snode, relation="supersedes", direction="out")
                    for rep in replacers:
                        rsid = rep.replace("scheme:", "")
                        if rsid not in results:
                            results.append(rsid)
                            paths.append(f"{self.by_id[rsid]['name']} -[supersedes]-> {self.by_id[aid]['name']}")
                        for comp in self.graph.neighbors(rep, relation="complementary_to", direction="both"):
                            csid = comp.replace("scheme:", "")
                            if csid not in results and csid != aid:
                                results.append(csid)
                                paths.append(f"{self.by_id[rsid]['name']} -[complementary_to]-> {self.by_id[csid]['name']}")
                else:
                    neighbors = self.graph.neighbors(snode, relation=relation, direction="both")
                    for nb in neighbors:
                        nsid = nb.replace("scheme:", "")
                        if nsid not in results and nsid != aid:
                            results.append(nsid)
                            paths.append(f"{self.by_id[aid]['name']} -[{relation}]-> {self.by_id[nsid]['name']}")

        matched_schemes = [self.by_id[sid] for sid in results[:top_k] if sid in self.by_id]
        return {
            "relation": relation,
            "scheme_ids": [s["scheme_id"] for s in matched_schemes],
            "schemes": matched_schemes,
            "paths": paths[:8],
        }
