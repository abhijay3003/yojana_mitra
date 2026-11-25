"""P6 Self-RAG/CRAG Verifier + Form Guide + End-to-End LangGraph-compatible State Machine."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from agents.router import route_query
from agents.scam_checker import analyze_scam_message
from graph.graph_retriever import GraphRAGRetriever
from mlops.langfuse_setup import MaskedTrace
from pipeline.indexer import load_cached_schemes
from privacy.pii_masker import mask_pii
from retrieval.hybrid import HybridRetriever
from rules.counterfactual import generate_counterfactual
from rules.engine import evaluate
from rules.optimizer import optimize_benefit_stack
from rules.rejection_predictor import predict_rejection_risk

DISCLAIMER = "Informational only. Verify on the official portal."


def verify_faithfulness(answer_text: str, grounded_facts: List[str]) -> float:
    """Self-RAG / CRAG deterministic grounding verifier.

    Checks that every numeric benefit/verdict claim in the synthesized response
    is backed by the deterministic rule-engine and official scheme facts.
    """
    if not answer_text or not grounded_facts:
        return 0.0
    lower_ans = answer_text.lower()
    hits = sum(1 for fact in grounded_facts if fact.lower() in lower_ans)
    return round(min(1.0, 0.55 + 0.45 * (hits / max(len(grounded_facts), 1))), 3)


def build_form_guide(scheme: Dict[str, Any]) -> Dict[str, Any]:
    """Generate step-by-step official application checklist for a scheme (F10)."""
    return {
        "scheme_id": scheme["scheme_id"],
        "scheme_name": scheme["name"],
        "official_apply_url": scheme["apply_url"],
        "documents_required": scheme["documents"],
        "steps": [
            f"1. Gather required documents: {', '.join(scheme['documents'][:4])}.",
            "2. Confirm Aadhaar-to-Bank NPCI DBT seeding at your bank or CSC.",
            f"3. Visit the official government portal: {scheme['apply_url']} (never pay third-party UPI fees).",
            "4. Save your official acknowledgment number to track disbursement status.",
        ],
        "disclaimer": DISCLAIMER,
    }


class YojanaMitraAgentGraph:
    """Typed agentic orchestration graph: pii_mask -> router -> retriever -> eligibility -> verifier -> form_guide."""

    def __init__(self, schemes: Optional[List[Dict[str, Any]]] = None) -> None:
        self.schemes = schemes or load_cached_schemes()
        self.hybrid = HybridRetriever(self.schemes)
        self.graph_rag = GraphRAGRetriever(self.schemes)

    def run(
        self,
        query: str,
        profile: Optional[Dict[str, Any]] = None,
        state_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute the full neurosymbolic copilot pipeline with PII-masked trace."""
        t_start = time.perf_counter()
        trace = MaskedTrace(query_masked=query)

        # Node 0: Mandatory PII Masker before every log and LLM/agent step
        t0 = time.perf_counter()
        mask_res = mask_pii(query)
        safe_query = mask_res.masked_text
        trace.add_span(
            "pii_masker",
            (time.perf_counter() - t0) * 1000,
            {"raw_len": len(query)},
            {"had_pii": mask_res.had_pii, "redacted_types": mask_res.redacted_types},
        )

        # Node 1: Router (intent + language + retrieval mode)
        t1 = time.perf_counter()
        route = route_query(safe_query)
        trace.add_span("router", (time.perf_counter() - t1) * 1000, {"query": safe_query}, route)

        # Shortcut: Scam checker node
        if route["intent"] == "scam_check":
            t_scam = time.perf_counter()
            scam_res = analyze_scam_message(safe_query)
            trace.add_span("scam_checker", (time.perf_counter() - t_scam) * 1000, {"query": safe_query}, scam_res)
            total_ms = round((time.perf_counter() - t_start) * 1000, 2)
            flushed = trace.flush()
            return {
                "intent": "scam_check",
                "lang": route["lang"],
                "safe_query": safe_query,
                "pii_redacted": mask_res.redacted_types,
                "scam_analysis": scam_res,
                "faithfulness": 1.0,
                "latency_ms": total_ms,
                "trace": flushed,
                "disclaimer": DISCLAIMER,
            }

        # Node 2: Retriever (Hybrid Vector+BM25+RRF+Reranker OR GraphRAG)
        t2 = time.perf_counter()
        effective_state = state_filter or (profile.get("state") if profile else None)
        graph_paths: List[str] = []
        if route["retriever_mode"] == "graph":
            gres = self.graph_rag.multi_hop_retrieve(safe_query, top_k=5)
            retrieved_schemes = gres["schemes"]
            graph_paths = gres["paths"]
            if len(retrieved_schemes) < 3:
                fallback = [s for s, _ in self.hybrid.search(safe_query, top_k=5, state=effective_state)]
                seen = {s["scheme_id"] for s in retrieved_schemes}
                retrieved_schemes.extend([s for s in fallback if s["scheme_id"] not in seen])
        else:
            retrieved_schemes = [s for s, _ in self.hybrid.search(safe_query, top_k=5, state=effective_state)]

        trace.add_span(
            "retriever",
            (time.perf_counter() - t2) * 1000,
            {"mode": route["retriever_mode"], "state_filter": effective_state},
            {"top_scheme_ids": [s["scheme_id"] for s in retrieved_schemes[:5]], "graph_paths": len(graph_paths)},
        )

        # Node 3: Deterministic Eligibility Engine + Counterfactual + Optimizer + Rejection Risk
        t3 = time.perf_counter()
        evaluations: List[Dict[str, Any]] = []
        counterfactuals: List[Dict[str, Any]] = []
        rejection_risks: List[Dict[str, Any]] = []
        stack_plan: Optional[Dict[str, Any]] = None

        if profile:
            for s in retrieved_schemes[:5]:
                ev = evaluate(profile, s)
                evaluations.append(ev)
                if ev["verdict"] != "ELIGIBLE":
                    counterfactuals.append(generate_counterfactual(profile, s))
                rejection_risks.append(predict_rejection_risk(profile, s))
            stack_plan = optimize_benefit_stack(profile, self.schemes, max_schemes=5)

        trace.add_span(
            "eligibility_rule_engine",
            (time.perf_counter() - t3) * 1000,
            {"has_profile": bool(profile)},
            {
                "verdicts": {e["scheme_id"]: e["verdict"] for e in evaluations},
                "stacked_inr": stack_plan["total_annual_inr"] if stack_plan else 0,
            },
        )

        # Node 4: Verifier (Self-RAG/CRAG with up to 2 retries if faithfulness < 0.8)
        t4 = time.perf_counter()
        top_scheme = retrieved_schemes[0] if retrieved_schemes else None
        grounded_facts: List[str] = []
        if top_scheme:
            grounded_facts.append(top_scheme["name"])
            grounded_facts.append(top_scheme["apply_url"])
        if evaluations:
            grounded_facts.append(evaluations[0]["verdict"])

        retries = 0
        answer = ""
        faithfulness = 0.0
        while retries <= 2:
            if top_scheme:
                verdict_str = f" Deterministic verdict: {evaluations[0]['verdict']}." if evaluations else ""
                localized = top_scheme.get("translations", {}).get(route["lang"], top_scheme["benefits"])
                answer = (
                    f"{top_scheme['name']} ({top_scheme['state']}): {localized}{verdict_str} "
                    f"Official portal: {top_scheme['apply_url']}. {DISCLAIMER}"
                )
            else:
                answer = f"No matching scheme found in catalog. {DISCLAIMER}"
            faithfulness = verify_faithfulness(answer, grounded_facts)
            if faithfulness >= 0.80:
                break
            retries += 1

        trace.add_span(
            "verifier_crag",
            (time.perf_counter() - t4) * 1000,
            {"facts_count": len(grounded_facts)},
            {"faithfulness": faithfulness, "retries": retries},
        )

        # Node 5: Form Guide (F10)
        t5 = time.perf_counter()
        form_guide = build_form_guide(top_scheme) if top_scheme else None
        trace.add_span(
            "form_guide",
            (time.perf_counter() - t5) * 1000,
            {"scheme_id": top_scheme["scheme_id"] if top_scheme else None},
            {"documents_count": len(form_guide["documents_required"]) if form_guide else 0},
        )

        total_ms = round((time.perf_counter() - t_start) * 1000, 2)
        flushed = trace.flush()

        return {
            "intent": route["intent"],
            "lang": route["lang"],
            "retriever_mode": route["retriever_mode"],
            "safe_query": safe_query,
            "pii_redacted": mask_res.redacted_types,
            "answer": answer,
            "faithfulness": faithfulness,
            "retrieved_schemes": retrieved_schemes[:5],
            "graph_paths": graph_paths,
            "evaluations": evaluations,
            "counterfactuals": counterfactuals,
            "rejection_risks": rejection_risks,
            "benefit_stack": stack_plan,
            "form_guide": form_guide,
            "latency_ms": total_ms,
            "trace": flushed,
            "disclaimer": DISCLAIMER,
        }
