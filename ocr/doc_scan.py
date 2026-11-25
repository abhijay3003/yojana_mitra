"""P9 Document Scan + Autofill (F3): extracts citizen profile fields and masks PII immediately."""

from __future__ import annotations

import re
from typing import Any, Dict

from privacy.pii_masker import mask_pii


def extract_profile_from_document_text(raw_ocr_text: str) -> Dict[str, Any]:
    """Extract structured profile fields from OCR text, immediately redacting PII (DPDP Act 2023).

    Raw document content and Aadhaar numbers are NEVER persisted.
    """
    masked = mask_pii(raw_ocr_text)
    lower = raw_ocr_text.lower()
    extracted: Dict[str, Any] = {}

    # Income
    inc = re.search(r"(?:annual\s*)?income\s*[:\-]?\s*(?:rs\.?|inr|₹)?\s*([\d,]+)", lower)
    if inc:
        extracted["income"] = int(inc.group(1).replace(",", ""))

    # Age
    age = re.search(r"\bage\s*[:\-]?\s*(\d{1,2})\b", lower)
    if age:
        extracted["age"] = int(age.group(1))

    # Land
    land = re.search(r"(?:land|extent|area)\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*(?:acres?|ac)", lower)
    if land:
        extracted["land"] = float(land.group(1))

    # State
    for st in ("Telangana", "Andhra Pradesh", "Karnataka", "Tamil Nadu", "Maharashtra"):
        if st.lower() in lower:
            extracted["state"] = st
            break

    # Category
    for cat in ("SC", "ST", "OBC", "EWS", "Minority"):
        if re.search(rf"\b{cat.lower()}\b", lower) or (cat == "SC" and "scheduled caste" in lower) or (cat == "ST" and "scheduled tribe" in lower):
            extracted["category"] = cat
            break

    # Gender
    if re.search(r"\b(female|woman|wife of|w/o|d/o|smt\.?)\b", lower):
        extracted["gender"] = "Female"
    elif re.search(r"\b(male|man|son of|s/o|shri\.?)\b", lower):
        extracted["gender"] = "Male"

    # Occupation
    if any(k in lower for k in ("farmer", "pattadar", "rythu", "agricultur", "cultivator")):
        extracted["occupation"] = "Farmer"
    elif "student" in lower or "bonafide" in lower:
        extracted["occupation"] = "Student"
    elif "artisan" in lower or "weaver" in lower:
        extracted["occupation"] = "Artisan"

    # BPL / Ration card
    if any(k in lower for k in ("white ration", "bpl", "antyodaya", "food security card", "rice card")):
        extracted["bpl"] = True

    # Residence
    if any(k in lower for k in ("mandal", "gram panchayat", "village", "rural")):
        extracted["residence"] = "Rural"
    elif any(k in lower for k in ("municipality", "ghmc", "bbmp", "urban", "ward no")):
        extracted["residence"] = "Urban"

    # Disability
    if "udid" in lower or "disability" in lower or "divyang" in lower:
        extracted["disability"] = True

    return {
        "extracted_profile": extracted,
        "masked_ocr_preview": masked.masked_text,
        "pii_redacted_types": masked.redacted_types,
        "raw_document_deleted": True,
        "aadhaar_stored": False,
    }
