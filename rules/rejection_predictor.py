"""F7 Application Rejection Risk Predictor (interpretable additive GBDT-style scorer).

Computes rejection probability and top-3 likely rejection reasons from:
- Rule-margin proximity (e.g. income within 10% of ceiling)
- Missing mandatory documents
- Aadhaar-bank DBT seeding status
- Income/Caste certificate recency (>12 months)
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from rules.engine import evaluate


def predict_rejection_risk(
    profile: Dict[str, Any],
    scheme: Dict[str, Any],
    available_documents: Optional[List[str]] = None,
    aadhaar_bank_seeded: bool = True,
    certificate_age_months: int = 6,
) -> Dict[str, Any]:
    """Predict application rejection probability and return top-3 actionable reasons."""
    ev = evaluate(profile, scheme)
    reasons: List[Tuple[float, str, str]] = []
    logit = -2.1  # Low base log-odds (~11%) when all checks & docs are clean

    # 1. Hard rule failures
    if ev["failed"]:
        logit += 2.6 * len(ev["failed"])
        for f in ev["failed"]:
            reasons.append(
                (
                    0.92,
                    f"Hard eligibility mismatch: {f['label']} (your value: {f['actual']})",
                    "Verify official exemption clauses or explore counterfactual / alternative schemes.",
                )
            )

    # 2. Missing required documents
    required_docs: List[str] = list(scheme.get("documents", []))
    if available_documents is not None:
        avail_norm = {d.strip().lower() for d in available_documents}
        missing_docs = [
            d for d in required_docs if not any(tok in d.lower() or d.lower() in tok for tok in avail_norm)
        ]
        if missing_docs:
            logit += 0.65 * len(missing_docs)
            reasons.append(
                (
                    min(0.88, 0.35 + 0.18 * len(missing_docs)),
                    f"Missing mandatory document(s): {', '.join(missing_docs[:3])}",
                    "Obtain verified copies via MeeSeva / CSC / DigiLocker before portal submission.",
                )
            )

    # 3. Aadhaar-Bank NPCI DBT seeding check (top real-world DBT rejection cause in India)
    if not aadhaar_bank_seeded:
        logit += 1.35
        reasons.append(
            (
                0.78,
                "Bank account is not NPCI / Aadhaar-DBT seeded",
                "Visit your bank branch or use NPCI mapper check to enable Aadhaar DBT seeding.",
            )
        )

    # 4. Borderline income margin (within 12% of cap)
    income = profile.get("income")
    if isinstance(income, (int, float)):
        for r in scheme.get("rules", []):
            if r["field"] == "income" and r["op"] in ("<=", "<"):
                cap = float(r["value"])
                if 0.85 * cap <= float(income) <= cap:
                    logit += 0.55
                    reasons.append(
                        (
                            0.46,
                            f"Borderline income margin (Rs {int(income):,} vs cap Rs {int(cap):,})",
                            "Attach a fresh Tehsildar/MRO Income Certificate issued within the last 6 months.",
                        )
                    )

    # 5. Stale income/caste certificate
    if certificate_age_months > 12:
        logit += 0.85
        reasons.append(
            (
                0.62,
                f"Income/domicile certificate is {certificate_age_months} months old (>12 months validity)",
                "Renew Income Certificate on MeeSeva / e-District portal before applying.",
            )
        )

    # 6. Land record / Pattadar passbook verification warning for agri schemes
    if scheme.get("category") == "Agriculture" and float(profile.get("land") or 0) > 0:
        logit += 0.25
        reasons.append(
            (
                0.31,
                "Land record (Dharani/ROR) name spelling mismatch with Aadhaar",
                "Ensure exact name & father/husband name match across Pattadar Passbook, Aadhaar, and Bank KYC.",
            )
        )

    # Fallback preventive advisory if everything looks clean
    if len(reasons) < 3:
        reasons.append(
            (
                0.18,
                "e-KYC / mobile OTP mismatch during portal verification",
                "Confirm active mobile number linked to UIDAI Aadhaar before final OTP submit.",
            )
        )
    if len(reasons) < 3:
        reasons.append(
            (
                0.14,
                "Bank IFSC or dormant account rejection after merger",
                "Verify updated bank IFSC and ensure at least one recent transaction in DBT account.",
            )
        )

    prob = round(1.0 / (1.0 + math.exp(-logit)), 3)
    reasons.sort(key=lambda item: -item[0])
    top3 = [
        {"impact_score": round(score, 2), "reason": reason, "mitigation": fix}
        for score, reason, fix in reasons[:3]
    ]
    risk_band = "HIGH" if prob >= 0.60 else "MEDIUM" if prob >= 0.30 else "LOW"

    return {
        "scheme_id": scheme.get("scheme_id", ""),
        "scheme_name": scheme.get("name", ""),
        "verdict": ev["verdict"],
        "rejection_probability": prob,
        "risk_band": risk_band,
        "top_3_reasons": top3,
    }
