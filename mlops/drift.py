"""Query-language and intent distribution drift detector (Population Stability Index + TVD)."""

from __future__ import annotations

import math
from typing import Dict, List


def compute_psi(expected: Dict[str, float], actual: Dict[str, float], eps: float = 1e-6) -> float:
    """Compute Population Stability Index between reference and production distributions."""
    keys = set(expected.keys()) | set(actual.keys())
    psi = 0.0
    for k in keys:
        e = max(expected.get(k, 0.0), eps)
        a = max(actual.get(k, 0.0), eps)
        psi += (a - e) * math.log(a / e)
    return round(psi, 4)


def detect_distribution_drift(
    reference_counts: Dict[str, int],
    current_counts: Dict[str, int],
    psi_threshold: float = 0.20,
) -> Dict[str, object]:
    """Detect significant language or intent shift and emit actionable alert payload."""
    ref_total = max(sum(reference_counts.values()), 1)
    cur_total = max(sum(current_counts.values()), 1)
    ref_dist = {k: v / ref_total for k, v in reference_counts.items()}
    cur_dist = {k: v / cur_total for k, v in current_counts.items()}
    psi = compute_psi(ref_dist, cur_dist)

    shifted_slices: List[Dict[str, object]] = []
    for k in sorted(set(ref_dist) | set(cur_dist)):
        delta = round((cur_dist.get(k, 0.0) - ref_dist.get(k, 0.0)) * 100.0, 2)
        if abs(delta) >= 8.0:
            shifted_slices.append({"slice": k, "delta_pct_pts": delta})

    return {
        "psi": psi,
        "threshold": psi_threshold,
        "alert": psi >= psi_threshold,
        "severity": "HIGH" if psi >= 0.35 else "MEDIUM" if psi >= psi_threshold else "OK",
        "shifted_slices": shifted_slices,
    }
