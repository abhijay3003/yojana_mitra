"""BGE-M3 dense+sparse char-ngram & semantic cross-lingual encoder (CPU 8GB-safe)."""

from __future__ import annotations

import math
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

from retrieval.bm25 import scheme_to_text, tokenize

# Cross-lingual anchor dictionary mapping Indic welfare terms to canonical concepts
CROSS_LINGUAL_CONCEPTS: Dict[str, Tuple[str, ...]] = {
    "farmer_agri": ("farmer", "rythu", "kisan", "raitha", "రైతు", "కిసాన్", "किसान", "रैतु", "ರೈತ", "ಕಿಸಾನ್", "விவசாய", "கிசான்", "agriculture", "crop", "fasal", "పంట", "फसल", "ಬೆಳೆ", "பயிர்"),
    "women_welfare": ("women", "mahalakshmi", "gruha lakshmi", "magalir", "మహిళ", "మహాలక్ష్మి", "महिला", "महालक्ष्मी", "ಮಹಿಳೆ", "ಗೃಹ ಲಕ್ಷ್ಮಿ", "பெண்", "மகளிர்", "girl", "mother", "bride", "maternity"),
    "electricity_power": ("electricity", "power", "gruha jyothi", "griha jyothi", "200", "కరెంటు", "విద్యుత్", "గృహ జ్యోతి", "बिजली", "गृह ज्योति", "ವಿದ್ಯುತ್", "ಗೃಹ ಜ್ಯೋತಿ", "மின்சாரம்"),
    "housing": ("house", "housing", "awas", "pmay", "indiramma", "ఇల్లు", "ఇండ్లు", "ఇందిరమ్మ", "आवास", "मकान", "ಮನೆ", "ಆವಾಸ್", "வீடு", "இல்லம்"),
    "health": ("health", "hospital", "ayushman", "pmjay", "aarogyasri", "cmchis", "వైద్యం", "ఆరోగ్యశ్రీ", "ఆయుష్మాన్", "स्वास्थ्य", "आयुष्मान", "ಆರೋಗ್ಯ", "ಆಯುಷ್ಮಾನ್", "மருத்துவ"),
    "pension": ("pension", "aasara", "old age", "widow", "senior", "పింఛను", "ఆసరా", "पेंशन", "वृद्धावस्था", "ಪಿಂಚಣಿ", "ಸಂಧ್ಯಾ", "ஓய்வூதியம்"),
    "scholarship": ("scholarship", "student", "post-matric", "nsp", "pudhumai", "vidyasiri", "స్కాలర్", "విద్యార్థి", "छात्रवृत्ति", "ವಿದ್ಯಾರ್ಥಿವೇತನ", "உதவித்தொகை", "மாணவ"),
    "lpg_gas": ("lpg", "gas", "cylinder", "ujjwala", "pmuy", "గ్యాస్", "ఉజ్వల", "गैस", "उज्ज्वला", "ಎಲ್‌ಪಿಜಿ", "ಉಜ್ವಲ", "எரிவாயு", "உஜ்வாலா"),
    "employment": ("mgnrega", "nrega", "employment", "100 days", "yuva", "vishwakarma", "mudra", "artisan", "ఉపాధి", "విశ్వకర్మ", "मनरेगा", "रोजगार", "विश्वकर्मा", "ನರೇಗಾ", "ಯುವ", "வேலை"),
    "sc_st": ("dalit", "sc", "st", "scheduled", "ambedkar", "tahdco", "దళిత", "ఎస్సీ", "दलित", "अनुसूचित", "ದಲಿತ", "ಎಸ್‌ಸಿ", "பட்டியலின"),
    "disability": ("disability", "divyang", "udid", "wheelchair", "దివ్యాంగ", "दिव्यांग", "ಅಂಗವಿಕಲ", "மாற்றுத்திறனாளி"),
    "solar": ("solar", "kusum", "pump", "సోలార్", "కుసుమ్", "सोलर", "कुसुम", "ಸೌರ", "சூரிய"),
    "telangana": ("telangana", "dharani", "meeseva", "తెలంగాణ", "तेलंगाना", "ತೆಲಂಗಾಣ", "தெலங்கானா"),
    "karnataka": ("karnataka", "seva sindhu", "కర్ణాటక", "कर्नाटक", "ಕರ್ನಾಟಕ", "கர்நாடகா"),
    "tamil_nadu": ("tamil nadu", "kalaignar", "தమిళనాడు", "తమిళనాడు", "तमिलनाडु", "ತಮಿಳುನಾಡು", "தமிழ்நாடு", "கலைஞர்"),
    "andhra": ("andhra", "annadata", "talliki", "ఆంధ్రప్రదేశ్", "అన్నదాత", "తల్లికి", "आंध्र", "अन्नदाता"),
}


def _char_ngrams(text: str, n: int = 3) -> Counter[str]:
    clean = " ".join(tokenize(text))
    if len(clean) < n:
        return Counter({clean: 1.0}) if clean else Counter()
    return Counter(clean[i : i + n] for i in range(len(clean) - n + 1))


def _concept_vector(text: str) -> Dict[str, float]:
    lower = (text or "").lower()
    vec: Dict[str, float] = {}
    for concept, triggers in CROSS_LINGUAL_CONCEPTS.items():
        hits = sum(1 for t in triggers if t in lower)
        if hits > 0:
            vec[concept] = 1.0 + math.log(hits)
    return vec


def _cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(v * b.get(k, 0.0) for k, v in a.items())
    if dot == 0.0:
        return 0.0
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / max(na * nb, 1e-9)


class BGEM3HybridEncoder:
    """CPU-efficient BGE-M3 dense + lexical-sparse representation with cross-lingual concept bridge."""

    def __init__(self, schemes: List[Dict[str, Any]]) -> None:
        self.schemes = schemes
        self.ngrams = [_char_ngrams(scheme_to_text(s)) for s in schemes]
        self.concepts = [_concept_vector(scheme_to_text(s)) for s in schemes]

    def search(
        self,
        query: str,
        top_k: int = 5,
        state: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[Tuple[Dict[str, Any], float]]:
        q_ng = _char_ngrams(query)
        q_con = _concept_vector(query)
        scored: List[Tuple[int, float]] = []
        for idx, s in enumerate(self.schemes):
            if state and s["state"] not in (state, "All India"):
                continue
            if category and s["category"].lower() != category.lower():
                continue
            ng_sim = _cosine(q_ng, self.ngrams[idx])
            con_sim = _cosine(q_con, self.concepts[idx])
            score = 0.65 * ng_sim + 0.35 * con_sim
            scored.append((idx, score))
        scored.sort(key=lambda item: (-item[1], self.schemes[item[0]]["scheme_id"]))
        return [(self.schemes[idx], round(sc, 4)) for idx, sc in scored[:top_k]]
