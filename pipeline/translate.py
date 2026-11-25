"""Multilingual translation helper (IndicTrans2 API wrapper + precomputed vernacular catalog)."""

from __future__ import annotations

from typing import Dict

SUPPORTED_LANGUAGES: Dict[str, str] = {
    "en": "English",
    "te": "Telugu (తెలుగు)",
    "hi": "Hindi (हिन्दी)",
    "kn": "Kannada (ಕನ್ನಡ)",
    "ta": "Tamil (தமிழ்)",
}

SCRIPT_RANGES = {
    "te": (0x0C00, 0x0C7F),
    "hi": (0x0900, 0x097F),
    "kn": (0x0C80, 0x0CFF),
    "ta": (0x0B80, 0x0BFF),
}


def detect_language(text: str) -> str:
    """Detect language across en, te, hi, kn, ta via Unicode script + romanized cues."""
    if not text:
        return "en"
    counts = {lang: 0 for lang in SCRIPT_RANGES}
    for ch in text:
        cp = ord(ch)
        for lang, (lo, hi) in SCRIPT_RANGES.items():
            if lo <= cp <= hi:
                counts[lang] += 1
    best_lang, best_count = max(counts.items(), key=lambda kv: kv[1])
    if best_count >= 2:
        return best_lang

    lower = text.lower()
    if any(w in lower for w in ("rythu", "telangana", "naku", "pathakam", "arhatalu", "bharosa")):
        if any(w in lower for w in ("naku", "pathakam", "arhatalu", "enti", "kavali")):
            return "te"
    if any(w in lower for w in ("yojana", "kisan", "mujhe", "patrata", "kaise", "milega")):
        if any(w in lower for w in ("mujhe", "patrata", "kaise", "milega", "kya")):
            return "hi"
    return "en"
