"""Langfuse observability and PII-masked trace logging for Yojana Mitra."""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from privacy.pii_masker import mask_dict, mask_pii

TRACE_LOG_PATH = Path("data/processed/langfuse_traces.jsonl")


@dataclass
class TraceSpan:
    """Single node span inside an agentic LangGraph execution trace."""

    node: str
    latency_ms: float
    input_masked: Dict[str, Any]
    output_summary: Dict[str, Any]
    status: str = "ok"


@dataclass
class MaskedTrace:
    """End-to-end PII-masked execution trace."""

    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    query_masked: str = ""
    spans: List[TraceSpan] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def add_span(
        self,
        node: str,
        latency_ms: float,
        input_data: Dict[str, Any],
        output_summary: Dict[str, Any],
        status: str = "ok",
    ) -> None:
        """Append a PII-masked span to this trace."""
        self.spans.append(
            TraceSpan(
                node=node,
                latency_ms=round(latency_ms, 2),
                input_masked=mask_dict(input_data),
                output_summary=mask_dict(output_summary),
                status=status,
            )
        )

    def flush(self) -> Dict[str, Any]:
        """Persist PII-masked trace locally and emit to Langfuse if configured."""
        payload: Dict[str, Any] = {
            "trace_id": self.trace_id,
            "query_masked": mask_pii(self.query_masked).masked_text,
            "created_at": self.created_at,
            "total_latency_ms": round(sum(s.latency_ms for s in self.spans), 2),
            "spans": [
                {
                    "node": s.node,
                    "latency_ms": s.latency_ms,
                    "input_masked": s.input_masked,
                    "output_summary": s.output_summary,
                    "status": s.status,
                }
                for s in self.spans
            ],
        }
        TRACE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with TRACE_LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=False) + "\n")

        if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
            try:
                from langfuse import Langfuse  # type: ignore[import-not-found]

                lf = Langfuse()
                lf.trace(id=self.trace_id, name="yojana_mitra_query", input=payload["query_masked"], metadata=payload)
            except ImportError:
                pass
        return payload
