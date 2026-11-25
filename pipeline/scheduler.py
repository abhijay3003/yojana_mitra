"""Daily pipeline scheduler entrypoint invoked by GitHub Actions cron."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pipeline.cleaner import dedupe_schemes, validate_scheme_schema
from pipeline.diff_log import write_diff_log
from pipeline.indexer import build_index_metadata, load_cached_schemes


def run_scheduler(mode: str = "cached") -> int:
    """Run daily scheme verification, deduplication, indexing, and diff logging."""
    schemes = load_cached_schemes()
    cleaned = dedupe_schemes(schemes)
    invalid = [s["scheme_id"] for s in cleaned if validate_scheme_schema(s)]
    if invalid:
        raise ValueError(f"Schema validation failed for schemes: {invalid[:5]}")

    stats = build_index_metadata(cleaned)
    # Simulate snapshot diff against baseline v1 snapshot if present
    prev_path = Path("data/processed/prev_schemes_snapshot.json")
    prev = json.loads(prev_path.read_text(encoding="utf-8")) if prev_path.exists() else cleaned[:-3]
    diff = write_diff_log(prev, cleaned)
    print(
        f"[scheduler:{mode}] validated={len(cleaned)} states={len(stats['states'])} "
        f"diff_added={diff['summary']['added']} diff_changed={diff['summary']['changed']} "
        f"diff_removed={diff['summary']['removed']}"
    )
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Yojana Mitra daily scheme pipeline scheduler")
    parser.add_argument("--mode", choices=["cached", "live"], default="cached")
    args = parser.parse_args()
    raise SystemExit(run_scheduler(args.mode))
