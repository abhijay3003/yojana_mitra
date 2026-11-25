"""P10 Standalone FastAPI Application (runs via `uvicorn app.api:app --port 8000`)."""

from __future__ import annotations

from typing import Any, Dict, Optional

try:
    from fastapi import FastAPI
    from pydantic import BaseModel

    from app.fieldworker import (
        YojanaMitraAgentGraph,
        analyze_scam_message,
        extract_profile_from_document_text,
        handle_ivr_webhook,
        init_sqlite_db,
        optimize_benefit_stack,
        screen_families_csv,
    )
    from pipeline.indexer import load_cached_schemes

    init_sqlite_db()
    app = FastAPI(title="Yojana Mitra Neurosymbolic API", version="1.0.0")
    agent = YojanaMitraAgentGraph()

    class QueryRequest(BaseModel):
        query: str
        profile: Optional[Dict[str, Any]] = None
        state_filter: Optional[str] = None

    class ScamRequest(BaseModel):
        message: str

    class OcrRequest(BaseModel):
        text: str

    @app.get("/health")
    def health() -> Dict[str, Any]:
        return {"status": "ok", "schemes": len(load_cached_schemes())}

    @app.post("/v1/query")
    def query_copilot(req: QueryRequest) -> Dict[str, Any]:
        return agent.run(req.query, profile=req.profile, state_filter=req.state_filter)

    @app.post("/v1/scam-check")
    def scam_check(req: ScamRequest) -> Dict[str, Any]:
        return analyze_scam_message(req.message)

    @app.post("/v1/optimize-stack")
    def optimize(profile: Dict[str, Any]) -> Dict[str, Any]:
        return optimize_benefit_stack(profile, load_cached_schemes(), max_schemes=5)

    @app.post("/v1/ocr-autofill")
    def ocr_autofill(req: OcrRequest) -> Dict[str, Any]:
        return extract_profile_from_document_text(req.text)

    @app.post("/v1/ivr/webhook")
    def ivr_webhook(digit: str = "1", transcript: str = "") -> Dict[str, Any]:
        return handle_ivr_webhook(digit=digit, transcript=transcript)

    @app.post("/v1/fieldworker/batch")
    def fieldworker_batch(csv_text: str) -> Dict[str, Any]:
        return screen_families_csv(csv_text)

except ImportError:
    app = None  # FastAPI optional when running Node/Express preview server
