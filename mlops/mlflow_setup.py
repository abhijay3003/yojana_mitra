"""MLflow experiment tracking setup with local JSON fallback when mlflow pkg is absent."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

MLFLOW_LOCAL_LOG = Path("data/processed/mlflow_runs.jsonl")


def init_mlflow(experiment_name: str = "yojana-mitra") -> Dict[str, str]:
    """Initialize MLflow tracking URI and experiment name."""
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
    try:
        import mlflow  # type: ignore[import-not-found]

        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment(experiment_name)
        return {"backend": "mlflow", "tracking_uri": tracking_uri, "experiment": experiment_name}
    except ImportError:
        MLFLOW_LOCAL_LOG.parent.mkdir(parents=True, exist_ok=True)
        return {
            "backend": "local_jsonl_fallback",
            "tracking_uri": str(MLFLOW_LOCAL_LOG),
            "experiment": experiment_name,
        }


def log_run(
    run_name: str,
    params: Dict[str, Any],
    metrics: Dict[str, float],
    tags: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Log an evaluation or baseline run to MLflow (or local JSONL mirror)."""
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_name": run_name,
        "params": params,
        "metrics": metrics,
        "tags": tags or {},
    }
    try:
        import mlflow  # type: ignore[import-not-found]

        with mlflow.start_run(run_name=run_name):
            mlflow.log_params(params)
            mlflow.log_metrics(metrics)
            if tags:
                mlflow.set_tags(tags)
    except ImportError:
        pass

    MLFLOW_LOCAL_LOG.parent.mkdir(parents=True, exist_ok=True)
    with MLFLOW_LOCAL_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record
