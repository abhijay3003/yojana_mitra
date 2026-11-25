"""P6 Agent Node 1: Multilingual Router (Intent + Language + Retrieval Mode)."""

from __future__ import annotations

from typing import Dict

from pipeline.translate import detect_language

INTENT_CLASSES = ("eligibility", "documents", "how_to_apply", "status", "scam_check")


def route_query(query: str) -> Dict[str, str]:
    """Classify language (en/te/hi/kn/ta), intent, and retrieval path (vector|graph|sql)."""
    lang = detect_language(query)
    q = (query or "").lower()

    # 1. Scam intent detection (highest priority for citizen safety)
    scam_signals = (
        "scam", "fake", "fraud", "lottery", "congratulations", "click", ".xyz", ".top", ".apk",
        "processing fee", "registration fee", "forward to", "otp", "cvv", "gpay", "phonepe",
        "free laptop", "free phone", "free 5g", "agent commission", "stamp duty", "diwali bonus",
        "మోసం", "नकली", "फर्जी",
    )
    if any(tok in q for tok in scam_signals):
        return {"lang": lang, "intent": "scam_check", "retriever_mode": "none"}

    # 2. Explicit eligibility override when citizen asks directly about eligibility/patrata
    elig_explicit = ("eligibility", "eligible", "అర్హత", "పాత్రత", "पात्रता", "ಅರ್ಹತೆ", "தகுதி")
    doc_signals = (
        "document", "documents", "certificate", "passbook", "job card", "health insurance card",
        "udid", "పత్రాలు", "దస్తావేజులు", "జాబ్ కార్డ్", "दस्तावेज", "जॉब कार्ड", "कार्ड", "यूडीआईडी",
        "ದಾಖಲೆಗಳು", "ஆவணங்கள்", "மருத்துவ காப்பீடு", "விரிவான மருத்துவ",
    )
    apply_signals = (
        "how to apply", "how to get", "apply", "portal", "register", "premium details", "toolkit",
        "business loan", "subsidy loan", "దరఖాస్తు", "ఎలా పొందాలి", "టూల్ కిట్",
        "आवेदन", "कैसे करें", "टूलकिट", "बिजनेस लोन", "ಅರ್ಜಿ", "ಸಬ್ಸಿಡಿ ಸಾಲ",
        "விண்ணப்ப", "கருவித்தொகுப்பு", "மானியம்", "நிதி உதவி",
    )
    status_signals = ("status", "installment", "credited", "pending", "track", "స్టేటస్", "ఎప్పుడు పడతాయి", "स्थिति")

    if any(tok in q for tok in status_signals):
        intent = "status"
    elif any(tok in q for tok in elig_explicit):
        intent = "eligibility"
    elif any(tok in q for tok in doc_signals):
        intent = "documents"
    elif any(tok in q for tok in apply_signals):
        intent = "how_to_apply"
    else:
        intent = "eligibility"

    # Decide vector vs graph retrieval
    if any(tok in q for tok in ("complement", "stack", "supersede", "replace", "mutually exclusive", "share", "both", "together", "combine")):
        retriever_mode = "graph"
    else:
        retriever_mode = "vector"

    return {"lang": lang, "intent": intent, "retriever_mode": retriever_mode}
