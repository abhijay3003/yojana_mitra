"""Deterministic Neurosymbolic Eligibility Rule Engine (P3).

HARD ARCHITECTURAL INVARIANT:
Eligibility verdicts come ONLY from this deterministic engine.
LLMs explain verdicts and guide applications; they NEVER decide eligibility.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

ALLOWED_FIELDS = frozenset(
    {"age", "income", "state", "category", "gender", "occupation", "land", "disability", "bpl", "residence"}
)
ALLOWED_OPS = frozenset({"==", "!=", "<=", ">=", "<", ">", "in", "not_in"})


def validate_rules_against_schema(rules: List[Dict[str, Any]]) -> List[str]:
    """Validate extracted rule list against /rules/schema.json constraints."""
    errors: List[str] = []
    for idx, rule in enumerate(rules):
        field = rule.get("field")
        op = rule.get("op")
        if field not in ALLOWED_FIELDS:
            errors.append(f"Rule[{idx}] invalid field: {field}")
        if op not in ALLOWED_OPS:
            errors.append(f"Rule[{idx}] invalid operator: {op}")
        if "value" not in rule:
            errors.append(f"Rule[{idx}] missing value")
        if op in ("in", "not_in") and not isinstance(rule.get("value"), list):
            errors.append(f"Rule[{idx}] operator '{op}' requires list value")
    return errors


def _compare(actual: Any, op: str, expected: Any) -> bool:
    if op == "==":
        if isinstance(actual, str) and isinstance(expected, str):
            return actual.strip().lower() == expected.strip().lower()
        return actual == expected
    if op == "!=":
        if isinstance(actual, str) and isinstance(expected, str):
            return actual.strip().lower() != expected.strip().lower()
        return actual != expected
    if op == "<=":
        return float(actual) <= float(expected)
    if op == ">=":
        return float(actual) >= float(expected)
    if op == "<":
        return float(actual) < float(expected)
    if op == ">":
        return float(actual) > float(expected)
    if op == "in":
        norm_expected = [str(v).strip().lower() for v in expected]
        return str(actual).strip().lower() in norm_expected
    if op == "not_in":
        norm_expected = [str(v).strip().lower() for v in expected]
        return str(actual).strip().lower() not in norm_expected
    raise ValueError(f"Unsupported operator: {op}")


def evaluate(profile: Dict[str, Any], scheme: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministically evaluate a citizen profile against a scheme's structured rules.

    Args:
        profile: Citizen profile dict over the 10 schema fields.
        scheme: Scheme record containing `scheme_id`, `name`, and `rules`.

    Returns:
        Dict with `verdict` ("ELIGIBLE" | "NOT_ELIGIBLE" | "NEEDS_INFO"),
        `passed`, `failed`, `missing`, `trace`, and `match_score`.
    """
    rules: List[Dict[str, Any]] = list(scheme.get("rules", []))
    passed: List[Dict[str, Any]] = []
    failed: List[Dict[str, Any]] = []
    missing: List[Dict[str, Any]] = []
    trace: List[str] = []

    for rule in rules:
        field = str(rule["field"])
        op = str(rule["op"])
        expected = rule["value"]
        label = str(rule.get("label") or f"{field} {op} {expected}")

        if field not in profile or profile[field] is None or profile[field] == "":
            entry = {
                "field": field,
                "op": op,
                "expected": expected,
                "actual": None,
                "label": label,
                "status": "MISSING",
            }
            missing.append(entry)
            trace.append(f"[MISSING] {label}: profile.{field} not provided")
            continue

        actual = profile[field]
        try:
            ok = _compare(actual, op, expected)
        except (TypeError, ValueError):
            ok = False

        entry = {
            "field": field,
            "op": op,
            "expected": expected,
            "actual": actual,
            "label": label,
            "status": "PASS" if ok else "FAIL",
        }
        if ok:
            passed.append(entry)
            trace.append(f"[PASS] {label} (actual={actual})")
        else:
            failed.append(entry)
            trace.append(f"[FAIL] {label} (actual={actual}, required {op} {expected})")

    if failed:
        verdict = "NOT_ELIGIBLE"
    elif missing:
        verdict = "NEEDS_INFO"
    else:
        verdict = "ELIGIBLE"

    total = max(len(rules), 1)
    match_score = round((len(passed) / total) * 100.0, 1)

    return {
        "scheme_id": scheme.get("scheme_id", ""),
        "scheme_name": scheme.get("name", ""),
        "verdict": verdict,
        "passed": passed,
        "failed": failed,
        "missing": missing,
        "trace": trace,
        "match_score": match_score,
    }


def evaluate_all(
    profile: Dict[str, Any],
    schemes: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Evaluate a profile against all schemes and rank by verdict + benefit value."""
    order = {"ELIGIBLE": 0, "NEEDS_INFO": 1, "NOT_ELIGIBLE": 2}
    results: List[Dict[str, Any]] = []
    for s in schemes:
        ev = evaluate(profile, s)
        ev["annual_benefit_inr"] = int(s.get("annual_benefit_inr", 0))
        ev["state"] = s.get("state", "All India")
        ev["category"] = s.get("category", "")
        results.append(ev)
    results.sort(
        key=lambda r: (
            order[r["verdict"]],
            -r["match_score"],
            -r["annual_benefit_inr"],
            r["scheme_id"],
        )
    )
    return results


def load_schema(path: Path = Path("rules/schema.json")) -> Dict[str, Any]:
    """Load /rules/schema.json from disk."""
    return json.loads(path.read_text(encoding="utf-8"))
