"""P9/P10 Standalone FastAPI + Field-Worker Batch Screener + Proactive Diff Alerts + WhatsApp Bot."""

from __future__ import annotations

import csv
import io
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

from agents.graph import YojanaMitraAgentGraph
from agents.scam_checker import analyze_scam_message
from ocr.doc_scan import extract_profile_from_document_text
from pipeline.indexer import load_cached_schemes
from rules.counterfactual import generate_counterfactual
from rules.engine import evaluate, evaluate_all
from rules.optimizer import optimize_benefit_stack
from rules.rejection_predictor import predict_rejection_risk
from speech.ivr import handle_ivr_webhook

DB_PATH = Path("data/yojana_mitra.db")


def init_sqlite_db(db_path: Path = DB_PATH) -> None:
    """Initialize SQLite schema for feedback loop (F8) and saved profiles (F5 alerts)."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                query_masked TEXT NOT NULL,
                scheme_id TEXT,
                lang TEXT,
                rating INTEGER NOT NULL,
                comment_masked TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS saved_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                label TEXT NOT NULL,
                state TEXT NOT NULL,
                profile_json TEXT NOT NULL,
                channel TEXT DEFAULT 'whatsapp'
            )
            """
        )
        conn.commit()


def screen_families_csv(csv_text: str) -> Dict[str, Any]:
    """F4 Field-Worker Batch Screener: screens 50+ families CSV in/out in < 1 second."""
    schemes = load_cached_schemes()
    reader = csv.DictReader(io.StringIO(csv_text))
    rows_out: List[Dict[str, Any]] = []
    total_welfare_inr = 0

    for row in reader:
        prof = {
            "age": int(float(row.get("age", 35) or 35)),
            "income": float(row.get("income", 150000) or 150000),
            "state": (row.get("state") or "Telangana").strip(),
            "category": (row.get("category") or "SC").strip(),
            "gender": (row.get("gender") or "Female").strip(),
            "occupation": (row.get("occupation") or "Farmer").strip(),
            "land": float(row.get("land", 0) or 0),
            "disability": str(row.get("disability", "false")).strip().lower() in ("true", "1", "yes"),
            "bpl": str(row.get("bpl", "true")).strip().lower() in ("true", "1", "yes"),
            "residence": (row.get("residence") or "Rural").strip(),
        }
        stack = optimize_benefit_stack(prof, schemes, max_schemes=4)
        total_welfare_inr += stack["total_annual_inr"]
        rows_out.append(
            {
                "family_id": row.get("family_id", f"FAM_{len(rows_out) + 1:03d}"),
                "state": prof["state"],
                "category": prof["category"],
                "eligible_count": stack["eligible_count"],
                "top_stacked_schemes": " | ".join(s["name"] for s in stack["selected_schemes"]),
                "total_annual_inr": stack["total_annual_inr"],
                "gain_vs_top1_pct": stack["gain_vs_top1_pct"],
            }
        )

    out_buf = io.StringIO()
    if rows_out:
        writer = csv.DictWriter(out_buf, fieldnames=list(rows_out[0].keys()))
        writer.writeheader()
        writer.writerows(rows_out)

    return {
        "families_screened": len(rows_out),
        "aggregate_annual_welfare_inr": total_welfare_inr,
        "results": rows_out,
        "csv_output": out_buf.getvalue(),
    }


def match_diff_alerts(profiles: List[Dict[str, Any]], diff_log: Dict[str, Any]) -> List[Dict[str, Any]]:
    """F5 Proactive Alerts: match newly added/changed schemes against saved citizen profiles."""
    schemes_by_id = {s["scheme_id"]: s for s in load_cached_schemes()}
    changed_ids = [item["scheme_id"] for item in diff_log.get("added", []) + diff_log.get("changed", [])]
    alerts: List[Dict[str, Any]] = []
    for p in profiles:
        for sid in changed_ids:
            scheme = schemes_by_id.get(sid)
            if not scheme:
                continue
            ev = evaluate(p["profile"], scheme)
            if ev["verdict"] == "ELIGIBLE":
                alerts.append(
                    {
                        "profile_label": p.get("label", "Citizen"),
                        "scheme_id": sid,
                        "scheme_name": scheme["name"],
                        "annual_benefit_inr": scheme["annual_benefit_inr"],
                        "channel": p.get("channel", "whatsapp"),
                        "message": (
                            f"Yojana Mitra Alert: {scheme['name']} was recently updated/added and matches your profile "
                            f"(Est. Rs {scheme['annual_benefit_inr']:,}/yr). Verify & apply: {scheme['apply_url']}. "
                            "Informational only. Verify on the official portal."
                        ),
                    }
                )
    return alerts


__all__ = [
    "YojanaMitraAgentGraph",
    "analyze_scam_message",
    "evaluate",
    "evaluate_all",
    "extract_profile_from_document_text",
    "generate_counterfactual",
    "handle_ivr_webhook",
    "init_sqlite_db",
    "match_diff_alerts",
    "optimize_benefit_stack",
    "predict_rejection_risk",
    "screen_families_csv",
]
