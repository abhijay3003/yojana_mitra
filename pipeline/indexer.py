"""Catalog indexing and daily GitHub Actions scheduler."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

CACHED_SCHEMES_PATH = Path("data/cached_schemes.json")
INDEX_STATS_PATH = Path("data/processed/index_stats.json")


def load_cached_schemes(path: Path = CACHED_SCHEMES_PATH) -> List[Dict[str, Any]]:
    """Load the cached scheme catalog from disk."""
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def build_index_metadata(schemes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute summary index stats across states, ministries, and categories."""
    by_state: Dict[str, int] = {}
    by_category: Dict[str, int] = {}
    for s in schemes:
        by_state[s["state"]] = by_state.get(s["state"], 0) + 1
        by_category[s["category"]] = by_category.get(s["category"], 0) + 1
    stats = {
        "total_schemes": len(schemes),
        "states": by_state,
        "categories": by_category,
    }
    INDEX_STATS_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_STATS_PATH.write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")
    return stats
