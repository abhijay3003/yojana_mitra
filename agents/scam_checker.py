"""P6 Agent Node: Scam Checker (F6) with deterministic red-flag analyzer + official portal resolver."""

from __future__ import annotations

import re
from typing import Any, Dict, List

SUSPICIOUS_TLDS = (".xyz", ".top", ".click", ".online", ".shop", ".club", ".buzz", ".apk", "tinyurl.com", "bit.ly")
OFFICIAL_DOMAINS = (".gov.in", ".nic.in", "myscheme.gov.in", "udyamimitra.in", "standupmitra.in", "maandhan.in")

SCAM_KEYWORDS = (
    ("pay ", "Requests upfront payment / registration fee (real government schemes never charge UPI/processing fees)."),
    ("registration fee", "Requests a registration or processing fee."),
    ("processing fee", "Requests a processing fee or agent commission."),
    ("agent commission", "Mentions unofficial agent commission."),
    ("stamp duty", "Asks for advance stamp duty via UPI."),
    ("upi", "Asks to transfer money to a private UPI handle."),
    ("gpay", "Asks for Google Pay transfer."),
    ("phonepe", "Asks for PhonePe transfer."),
    ("otp", "Requests sensitive Aadhaar/bank OTP."),
    ("cvv", "Requests ATM/debit card CVV or PIN."),
    ("bank pin", "Requests bank PIN."),
    ("debit card", "Requests debit card credentials."),
    (".apk", "Distributes an unofficial Android .apk file over WhatsApp."),
    ("forward to", "Uses chain-message forwarding pressure ('forward to 10 groups')."),
    ("free laptop", "Uses known 'Free Laptop/5G Phone' viral hoax lure."),
    ("free 5g", "Uses known 'Free 5G Smartphone' hoax lure."),
    ("lottery winner", "Uses fake lottery/jackpot claim language."),
    ("within 2 hours", "Uses artificial urgency/account-suspension threat."),
    ("blocked", "Threatens benefit suspension to force click on phishing link."),
    ("diwali bonus", "Uses fake seasonal cash-bonus lure."),
)

OFFICIAL_PORTAL_HINTS = {
    "pm-kisan": ("PM-KISAN Samman Nidhi", "https://pmkisan.gov.in"),
    "pmkisan": ("PM-KISAN Samman Nidhi", "https://pmkisan.gov.in"),
    "rythu": ("Telangana Rythu Bharosa", "https://rythubharosa.telangana.gov.in"),
    "mahalakshmi": ("Telangana Mahalakshmi", "https://prajapalana.telangana.gov.in"),
    "gruha lakshmi": ("Karnataka Gruha Lakshmi", "https://sevasindhugs.karnataka.gov.in"),
    "awas": ("PM Awas Yojana", "https://pmayg.nic.in"),
    "pmay": ("PM Awas Yojana", "https://pmayg.nic.in"),
    "ayushman": ("Ayushman Bharat PM-JAY", "https://pmjay.gov.in"),
    "vishwakarma": ("PM Vishwakarma", "https://pmvishwakarma.gov.in"),
    "ujjwala": ("PM Ujjwala Yojana", "https://pmuy.gov.in"),
    "surya": ("PM Surya Ghar", "https://pmsuryaghar.gov.in"),
    "scholarship": ("National Scholarship Portal", "https://scholarships.gov.in"),
}


def analyze_scam_message(message: str) -> Dict[str, Any]:
    """Deterministically classify a forwarded message as SCAM or LEGITIMATE with red flags and official portal."""
    lower = (message or "").lower()
    red_flags: List[str] = []
    score = 0.0

    urls = re.findall(r"https?://[^\s]+|www\.[^\s]+|tinyurl\.com/[^\s]+|bit\.ly/[^\s]+", lower)
    has_official_url = any(any(od in u for od in OFFICIAL_DOMAINS) for u in urls)
    has_suspicious_url = any(any(tld in u for tld in SUSPICIOUS_TLDS) for u in urls)

    if has_suspicious_url:
        score += 0.55
        red_flags.append("Contains an unofficial or shortened URL/APK instead of a verified .gov.in / .nic.in portal.")

    for kw, reason in SCAM_KEYWORDS:
        if kw in lower:
            # Exclude safe advisories like "Never share your OTP" or "No registration fee is charged"
            if kw == "otp" and ("never share" in lower or "do not share" in lower):
                continue
            if kw == "registration fee" and ("no registration fee" in lower or "completely free" in lower):
                continue
            score += 0.28
            if reason not in red_flags:
                red_flags.append(reason)

    if has_official_url and not has_suspicious_url and score < 0.3:
        score = max(0.0, score - 0.35)

    confidence = round(min(0.99, max(0.02, score if score >= 0.4 else 1.0 - score)), 3)
    verdict = "SCAM" if score >= 0.40 else "LEGITIMATE"

    official_scheme = "MyScheme National Welfare Portal"
    official_url = "https://www.myscheme.gov.in"
    for hint, (sname, surl) in OFFICIAL_PORTAL_HINTS.items():
        if hint in lower:
            official_scheme, official_url = sname, surl
            break

    return {
        "verdict": verdict,
        "risk_score": round(min(1.0, score), 3),
        "confidence": confidence,
        "red_flags": red_flags,
        "official_scheme": official_scheme,
        "official_url": official_url,
        "disclaimer": "Informational only. Verify on the official portal.",
    }
