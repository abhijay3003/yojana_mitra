"""Minimal-change Counterfactual Generator for Yojana Mitra (P3 + F2).

Given a citizen profile and a scheme for which verdict != ELIGIBLE, computes
the minimal set of field changes required to flip the deterministic engine
verdict to ELIGIBLE, and self-verifies every counterfactual via engine.evaluate().
"""

from __future__ import annotations

from typing import Any, Dict, List

from rules.engine import evaluate

IMMUTABLE_NOTE_FIELDS = frozenset({"category", "gender"})


def _minimal_target_value(op: str, expected: Any, actual: Any) -> Any:
    """Compute the closest valid value satisfying `val <op> expected`."""
    if op == "==":
        return expected
    if op == "<=":
        return expected
    if op == ">=":
        return expected
    if op == "<":
        return expected - 1 if isinstance(expected, int) else round(float(expected) - 0.1, 2)
    if op == ">":
        return expected + 1 if isinstance(expected, int) else round(float(expected) + 0.1, 2)
    if op == "in" and isinstance(expected, list) and expected:
        return expected[0]
    if op == "!=":
        return f"not_{expected}"
    if op == "not_in":
        return "EligibleOther"
    return expected


def _format_human_change(field: str, op: str, expected: Any, actual: Any) -> str:
    if field == "income" and op in ("<=", "<"):
        diff = int(float(actual or 0) - float(expected)) if actual is not None else 0
        if diff > 0:
            return f"Eligible if income <= {int(expected):,} (reduce by Rs {diff:,})"
        return f"Eligible if income <= {int(expected):,}"
    if field == "land" and op in (">=", ">"):
        return f"Eligible if land >= {expected} acres (currently {actual} acres)"
    if field == "land" and op in ("<=", "<"):
        return f"Eligible if land <= {expected} acres (currently {actual} acres)"
    if field == "age":
        return f"Eligible if age {op} {expected} (currently {actual})"
    if field == "bpl":
        return "Eligible if household holds a valid BPL / White Ration Card"
    if field == "state":
        return f"Scheme restricted to {expected} residents (currently {actual})"
    if field == "in" or op == "in":
        opts = ", ".join(str(x) for x in expected) if isinstance(expected, list) else str(expected)
        return f"Eligible if {field} is in [{opts}] (currently {actual})"
    return f"Eligible if {field} {op} {expected} (currently {actual})"


def generate_counterfactual(
    profile: Dict[str, Any],
    scheme: Dict[str, Any],
) -> Dict[str, Any]:
    """Compute minimal-change counterfactual explanation and verify exactness.

    Returns:
        Dict with `already_eligible`, `changes`, `summary`, `modified_profile`,
        and `verified_eligible` (guaranteed True when rules are satisfiable).
    """
    initial = evaluate(profile, scheme)
    if initial["verdict"] == "ELIGIBLE":
        return {
            "scheme_id": scheme.get("scheme_id", ""),
            "already_eligible": True,
            "changes": [],
            "summary": "Already eligible under all deterministic rules.",
            "modified_profile": dict(profile),
            "verified_eligible": True,
        }

    modified = dict(profile)
    changes: List[Dict[str, Any]] = []

    # Group constraints per field so range constraints (e.g. age >= 18 and age <= 35)
    # are satisfied simultaneously without overwriting each other.
    failing_items = list(initial["failed"]) + list(initial["missing"])
    by_field: Dict[str, List[Dict[str, Any]]] = {}
    for item in failing_items:
        by_field.setdefault(item["field"], []).append(item)

    for field, items in by_field.items():
        actual = profile.get(field)
        # Apply each failing predicate for this field
        target = actual
        for item in items:
            target = _minimal_target_value(item["op"], item["expected"], target)
            changes.append(
                {
                    "field": field,
                    "op": item["op"],
                    "current": actual,
                    "required": item["expected"],
                    "suggested_value": target,
                    "actionable": field not in IMMUTABLE_NOTE_FIELDS,
                    "explanation": _format_human_change(field, item["op"], item["expected"], actual),
                }
            )
        modified[field] = target

    # Self-verify against the deterministic rule engine
    recheck = evaluate(modified, scheme)
    summary_parts = [c["explanation"] for c in changes]
    return {
        "scheme_id": scheme.get("scheme_id", ""),
        "already_eligible": False,
        "changes": changes,
        "summary": "; ".join(summary_parts),
        "modified_profile": modified,
        "verified_eligible": recheck["verdict"] == "ELIGIBLE",
    }
