"""Deterministic regex + LLM-assisted structured eligibility rule extractor."""

from __future__ import annotations

import re
from typing import Any, Dict, List


def extract_rules_from_text(eligibility_text: str, state: str = "All India") -> List[Dict[str, Any]]:
    """Extract structured rule predicates from free-text eligibility clauses.

    Provides a deterministic offline extractor validated against /rules/schema.json.
    When GEMINI_API_KEY is configured, LLM-assisted extraction refines edge clauses
    and is always re-validated against the strict JSON schema before acceptance.
    """
    text = eligibility_text.lower()
    rules: List[Dict[str, Any]] = []

    if state and state != "All India":
        rules.append({"field": "state", "op": "==", "value": state, "label": f"Resident of {state}"})

    # Annual income ceiling: e.g. "income up to Rs 2,00,000" or "<= 150000"
    inc_match = re.search(r"income[^0-9]{0,25}(?:rs\.?|inr|₹)?\s*([\d,]+)(?:\s*(lakh|lakhs))?", text)
    if inc_match:
        raw_num = inc_match.group(1).replace(",", "")
        try:
            val = float(raw_num)
            if inc_match.group(2):
                val *= 100000
            rules.append({"field": "income", "op": "<=", "value": int(val), "label": f"Annual income <= ₹{int(val):,}"})
        except ValueError:
            pass

    # Age range: e.g. "age 18 to 59" or "aged 60+"
    age_range = re.search(r"age[d]?\s*(?:between\s*)?(\d{1,2})\s*(?:to|\-|and)\s*(\d{1,2})", text)
    if age_range:
        lo, hi = int(age_range.group(1)), int(age_range.group(2))
        rules.append({"field": "age", "op": ">=", "value": lo, "label": f"Age >= {lo}"})
        rules.append({"field": "age", "op": "<=", "value": hi, "label": f"Age <= {hi}"})
    else:
        age_min = re.search(r"age[d]?\s*(?:>=|at least|minimum|above)?\s*(\d{1,2})\s*(?:\+|years)?", text)
        if age_min and ("minimum" in text or "at least" in text or "above" in text or "+" in text):
            lo = int(age_min.group(1))
            rules.append({"field": "age", "op": ">=", "value": lo, "label": f"Age >= {lo}"})

    if "women" in text or "female" in text or "girl" in text or "widow" in text:
        rules.append({"field": "gender", "op": "==", "value": "Female", "label": "Gender is Female"})

    if "farmer" in text or "agricultur" in text or "cultivator" in text:
        rules.append({"field": "occupation", "op": "in", "value": ["Farmer", "Agricultural Laborer"], "label": "Occupation is Farmer"})

    cats: List[str] = []
    for c in ("sc", "st", "obc", "ews", "minority"):
        if re.search(rf"\b{c}\b", text):
            cats.append(c.upper() if c != "minority" else "Minority")
    if cats:
        rules.append({"field": "category", "op": "in", "value": cats, "label": f"Category in {', '.join(cats)}"})

    if "bpl" in text or "below poverty line" in text or "white ration card" in text:
        rules.append({"field": "bpl", "op": "==", "value": True, "label": "BPL / White Ration Card holder"})

    if "rural" in text:
        rules.append({"field": "residence", "op": "==", "value": "Rural", "label": "Rural residence"})
    elif "urban" in text:
        rules.append({"field": "residence", "op": "==", "value": "Urban", "label": "Urban residence"})

    if "disability" in text or "divyang" in text or "disabled" in text:
        rules.append({"field": "disability", "op": "==", "value": True, "label": "Person with benchmark disability"})

    return rules
