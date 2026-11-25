"""Yojana Mitra Privacy & DPDP Act 2023 PII Masking module.

Runs before every application log and every external LLM call.
Masks Aadhaar numbers, Indian phone numbers, PAN cards, email addresses,
and explicitly declared personal names across English, Telugu, and Hindi.
Never persists raw Aadhaar numbers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Pattern, Tuple

# Seed constant enforced across repository
SEED: int = 42

AADHAAR_TOKEN = "[REDACTED_AADHAAR]"
PHONE_TOKEN = "[REDACTED_PHONE]"
PAN_TOKEN = "[REDACTED_PAN]"
EMAIL_TOKEN = "[REDACTED_EMAIL]"
NAME_TOKEN = "[REDACTED_NAME]"

# Ordered patterns: specific identifiers first so 12-digit Aadhaar is not
# partially eaten by 10-digit phone regex.
_AADHAAR_PATTERNS: Tuple[Pattern[str], ...] = (
    # Standard 4-4-4 with spaces or hyphens (first digit 2-9 per UIDAI spec)
    re.compile(r"(?<!\d)[2-9]\d{3}[\s\-]\d{4}[\s\-]\d{4}(?!\d)"),
    # Unspaced 12-digit UIDAI number (first digit 2-9)
    re.compile(r"(?<!\d)[2-9]\d{11}(?!\d)"),
    # Explicit Aadhaar/UID label followed by 12 digits (even starting with 0/1 in test data)
    re.compile(
        r"(?i)(?:aadhaar|aadhar|uidai|uid|ఆధార్|आधार)\s*(?:no\.?|number|num|#|id|:|\-|is)?\s*[:\-]?\s*\d{4}[\s\-]?\d{4}[\s\-]?\d{4}"
    ),
)

_PAN_PATTERN: Pattern[str] = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")

_EMAIL_PATTERN: Pattern[str] = re.compile(
    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
)

_PHONE_PATTERNS: Tuple[Pattern[str], ...] = (
    # +91 or 0 prefix with optional spaces/hyphens
    re.compile(r"(?<!\d)(?:\+91[\s\-]?|0091[\s\-]?|91[\s\-]|0)[6-9]\d{4}[\s\-]?\d{5}(?!\d)"),
    # Plain 10-digit Indian mobile starting with 6-9 (optional 5-5 or 3-3-4 spacing)
    re.compile(r"(?<!\d)[6-9]\d{2}[\s\-]?\d{3}[\s\-]?\d{4}(?!\d)"),
)

# Multilingual explicit name declarations
_NAME_PATTERNS: Tuple[Pattern[str], ...] = (
    re.compile(
        r"(?i)\b(my name is|i am|applicant name|beneficiary name|name\s*:|s/o|d/o|w/o)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})"
    ),
    re.compile(r"(నా పేరు|పేరు\s*:)\s*([\u0C00-\u0C7F]+(?:\s+[\u0C00-\u0C7F]+)?)"),
    re.compile(r"(मेरा नाम|नाम\s*:)\s*([\u0900-\u097F]+(?:\s+[\u0900-\u097F]+)?)"),
)


@dataclass
class MaskResult:
    """Structured output returned by PII masking."""

    masked_text: str
    counts: Dict[str, int] = field(default_factory=dict)
    redacted_types: List[str] = field(default_factory=list)

    @property
    def had_pii(self) -> bool:
        """Return True if at least one PII entity was redacted."""
        return sum(self.counts.values()) > 0


def mask_pii(text: str) -> MaskResult:
    """Mask Aadhaar, PAN, Email, Indian Phone, and declared Names from text.

    Args:
        text: Raw user utterance, OCR output, or log string.

    Returns:
        MaskResult containing sanitized text and per-entity redaction counts.
    """
    if not text:
        return MaskResult(masked_text="", counts={}, redacted_types=[])

    counts: Dict[str, int] = {
        "aadhaar": 0,
        "pan": 0,
        "email": 0,
        "phone": 0,
        "name": 0,
    }
    sanitized = text

    # 1. Email first so local-part numbers aren't misread as phone numbers
    sanitized, n_email = _EMAIL_PATTERN.subn(EMAIL_TOKEN, sanitized)
    counts["email"] += n_email

    # 2. Aadhaar (before phone so 12 digits aren't matched as 10-digit phone)
    for pat in _AADHAAR_PATTERNS:
        sanitized, n = pat.subn(AADHAAR_TOKEN, sanitized)
        counts["aadhaar"] += n

    # 3. PAN card
    sanitized, n_pan = _PAN_PATTERN.subn(PAN_TOKEN, sanitized)
    counts["pan"] += n_pan

    # 4. Phone numbers
    for pat in _PHONE_PATTERNS:
        sanitized, n = pat.subn(PHONE_TOKEN, sanitized)
        counts["phone"] += n

    # 5. Explicitly declared names
    for pat in _NAME_PATTERNS:
        def _repl(match: re.Match[str]) -> str:
            counts["name"] += 1
            return f"{match.group(1)} {NAME_TOKEN}"

        sanitized = pat.sub(_repl, sanitized)

    redacted_types = [k for k, v in counts.items() if v > 0]
    return MaskResult(
        masked_text=sanitized,
        counts={k: v for k, v in counts.items() if v > 0},
        redacted_types=redacted_types,
    )


def mask_dict(payload: Dict[str, object]) -> Dict[str, object]:
    """Recursively mask PII strings and drop any explicit aadhaar keys.

    Ensures raw Aadhaar numbers are never stored or forwarded to logs/LLMs.
    """
    clean: Dict[str, object] = {}
    for key, val in payload.items():
        lowered = key.lower()
        if "aadhaar" in lowered or "aadhar" in lowered:
            clean[key] = AADHAAR_TOKEN
            continue
        if isinstance(val, str):
            clean[key] = mask_pii(val).masked_text
        elif isinstance(val, dict):
            clean[key] = mask_dict(val)
        elif isinstance(val, list):
            clean[key] = [
                mask_pii(item).masked_text
                if isinstance(item, str)
                else mask_dict(item)
                if isinstance(item, dict)
                else item
                for item in val
            ]
        else:
            clean[key] = val
    return clean
