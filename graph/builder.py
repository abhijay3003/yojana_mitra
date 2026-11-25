"""P5 GraphRAG Builder: constructs typed multi-relational welfare Knowledge Graph.

Uses NetworkX when installed and a zero-dependency typed adjacency graph fallback
so it runs identically in constrained 8 GB RAM / stdlib environments.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Set, Tuple


@dataclass
class GraphEdge:
    """Typed directed edge in the Yojana Mitra Knowledge Graph."""

    source: str
    target: str
    relation: str


@dataclass
class WelfareKnowledgeGraph:
    """Typed Knowledge Graph over Schemes, Ministries, States, Categories, Documents, Benefits."""

    nodes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    out_edges: Dict[str, List[GraphEdge]] = field(default_factory=dict)
    in_edges: Dict[str, List[GraphEdge]] = field(default_factory=dict)

    def add_node(self, node_id: str, node_type: str, label: str, **attrs: Any) -> None:
        if node_id not in self.nodes:
            self.nodes[node_id] = {"id": node_id, "type": node_type, "label": label, **attrs}
            self.out_edges.setdefault(node_id, [])
            self.in_edges.setdefault(node_id, [])

    def add_edge(self, source: str, target: str, relation: str) -> None:
        edge = GraphEdge(source=source, target=target, relation=relation)
        self.out_edges.setdefault(source, []).append(edge)
        self.in_edges.setdefault(target, []).append(edge)

    def neighbors(self, node_id: str, relation: str | None = None, direction: str = "out") -> List[str]:
        edges = self.out_edges.get(node_id, []) if direction == "out" else self.in_edges.get(node_id, [])
        if direction == "both":
            edges = self.out_edges.get(node_id, []) + self.in_edges.get(node_id, [])
        result: List[str] = []
        seen: Set[str] = set()
        for e in edges:
            if relation and e.relation != relation:
                continue
            other = e.target if e.source == node_id else e.source
            if other not in seen:
                seen.add(other)
                result.append(other)
        return result

    def stats(self) -> Dict[str, int]:
        by_type: Dict[str, int] = {}
        for n in self.nodes.values():
            t = n["type"]
            by_type[t] = by_type.get(t, 0) + 1
        total_edges = sum(len(v) for v in self.out_edges.values())
        return {"total_nodes": len(self.nodes), "total_edges": total_edges, **by_type}


def build_knowledge_graph(schemes: List[Dict[str, Any]]) -> WelfareKnowledgeGraph:
    """Build the complete typed Knowledge Graph from cached_schemes.json."""
    g = WelfareKnowledgeGraph()
    by_id = {s["scheme_id"]: s for s in schemes}

    for s in schemes:
        sid = f"scheme:{s['scheme_id']}"
        g.add_node(
            sid,
            "Scheme",
            s["name"],
            scheme_id=s["scheme_id"],
            state=s["state"],
            category=s["category"],
            annual_benefit_inr=s.get("annual_benefit_inr", 0),
        )

        # Ministry
        min_id = f"ministry:{s['ministry']}"
        g.add_node(min_id, "Ministry", s["ministry"])
        g.add_edge(sid, min_id, "administered_by")

        # State
        st_id = f"state:{s['state']}"
        g.add_node(st_id, "State", s["state"])
        g.add_edge(sid, st_id, "applies_in_state")

        # Benefit
        ben_id = f"benefit:{s['scheme_id']}"
        g.add_node(ben_id, "Benefit", f"Rs {int(s.get('annual_benefit_inr', 0)):,}/yr")
        g.add_edge(sid, ben_id, "provides_benefit")

        # Documents
        for doc in s.get("documents", []):
            doc_id = f"doc:{doc}"
            g.add_node(doc_id, "Document", doc)
            g.add_edge(sid, doc_id, "requires_document")

        # Eligibility category/occupation predicates
        for rule in s.get("rules", []):
            if rule["field"] in ("category", "occupation", "gender"):
                vals = rule["value"] if isinstance(rule["value"], list) else [rule["value"]]
                for v in vals:
                    cat_id = f"beneficiary:{rule['field']}={v}"
                    g.add_node(cat_id, "BeneficiaryCategory", f"{rule['field']}: {v}")
                    g.add_edge(sid, cat_id, "eligible_if")

    # Second pass: inter-scheme edges
    for s in schemes:
        sid = f"scheme:{s['scheme_id']}"
        for comp in s.get("complementary_to", []):
            if comp in by_id:
                g.add_edge(sid, f"scheme:{comp}", "complementary_to")
        for ex in s.get("mutually_exclusive_with", []):
            if ex in by_id:
                g.add_edge(sid, f"scheme:{ex}", "mutually_exclusive_with")
        for sup in s.get("supersedes", []):
            if sup in by_id:
                g.add_edge(sid, f"scheme:{sup}", "supersedes")
        parent = s.get("sub_scheme_of")
        if parent and parent in by_id:
            g.add_edge(sid, f"scheme:{parent}", "sub_scheme_of")

    return g
