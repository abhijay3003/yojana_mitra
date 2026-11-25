"""Pipeline helper modules: diff_log, extractor, translate, indexer, scheduler."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from pipeline.cleaner import compute_diff_log


def write_diff_log(
    previous_schemes: List[Dict[str, Any]],
    current_schemes: List[Dict[str, Any]],
    out_path: Path = Path("data/processed/diff_log.json"),
) -> Dict[str, Any]:
    """Compute and persist scheme diff log (new/changed/removed)."""
    diff = compute_diff_log(previous_schemes, current_schemes)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(diff, indent=2, ensure_ascii=False), encoding="utf-8")
    return diff
