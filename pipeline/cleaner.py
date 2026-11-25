"""Scheme cleaning, deduplication, structured rule extraction, translation, indexing, and diff log."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

REQUIRED_SCHEME_FIELDS: Tuple[str, ...] = (
    "scheme_id",
    "name",
    "ministry",
    "state",
    "category",
    "benefits",
    "eligibility_text",
    "documents",
    "apply_url",
    "source_url",
    "last_updated",
    "lang",
)


def clean_text(text: str) -> str:
    """Normalize whitespace and strip stray HTML tags."""
    no_html = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", no_html).strip()


def dedupe_schemes(schemes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate schemes deterministically by scheme_id and normalized name+state."""
    seen_ids: set[str] = set()
    seen_keys: set[str] = set()
    unique: List[Dict[str, Any]] = []
    for s in schemes:
        sid = str(s.get("scheme_id", "")).strip()
        key = f"{clean_text(str(s.get('name', ''))).lower()}::{str(s.get('state', '')).lower()}"
        if not sid or sid in seen_ids or key in seen_keys:
            continue
        seen_ids.add(sid)
        seen_keys.add(key)
        unique.append(s)
    return unique


def validate_scheme_schema(scheme: Dict[str, Any]) -> List[str]:
    """Validate a single scheme dict against the P1 required schema."""
    errors: List[str] = []
    for field in REQUIRED_SCHEME_FIELDS:
        if field not in scheme or scheme[field] in (None, ""):
            errors.append(f"Missing required field: {field}")
    if "documents" in scheme and not isinstance(scheme["documents"], list):
        errors.append("Field 'documents' must be a list")
    if "apply_url" in scheme and not str(scheme["apply_url"]).startswith("https://"):
        errors.append("Field 'apply_url' must be an HTTPS URL")
    return errors


def _scheme_hash(scheme: Dict[str, Any]) -> str:
    canonical = json.dumps(
        {k: scheme.get(k) for k in ("name", "benefits", "eligibility_text", "annual_benefit_inr", "documents", "rules")},
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def compute_diff_log(
    previous: List[Dict[str, Any]],
    current: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Compute added, changed, and removed schemes between two catalog snapshots."""
    prev_map = {s["scheme_id"]: s for s in previous}
    curr_map = {s["scheme_id"]: s for s in current}

    added: List[Dict[str, Any]] = []
    changed: List[Dict[str, Any]] = []
    removed: List[Dict[str, Any]] = []

    for sid, item in curr_map.items():
        if sid not in prev_map:
            added.append({"scheme_id": sid, "name": item["name"], "state": item["state"], "change": "NEW_SCHEME"})
        elif _scheme_hash(prev_map[sid]) != _scheme_hash(item):
            changed.append(
                {
                    "scheme_id": sid,
                    "name": item["name"],
                    "state": item["state"],
                    "old_benefit_inr": prev_map[sid].get("annual_benefit_inr", 0),
                    "new_benefit_inr": item.get("annual_benefit_inr", 0),
                    "change": "UPDATED_RULES_OR_BENEFITS",
                }
            )

    for sid, item in prev_map.items():
        if sid not in curr_map:
            removed.append({"scheme_id": sid, "name": item["name"], "state": item["state"], "change": "REMOVED"})

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_schemes": len(current),
        "summary": {
            "added": len(added),
            "changed": len(changed),
            "removed": len(removed),
        },
        "added": added,
        "changed": changed,
        "removed": removed,
    }
