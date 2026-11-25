"""Generate /data/cached_schemes.json with 110 validated Indian welfare schemes.

Deterministic (SEED=42). Includes flagship Central, Telangana, Andhra Pradesh,
Karnataka, and Tamil Nadu schemes with structured neurosymbolic eligibility rules,
GraphRAG relations, mutual-exclusion pairs, and multilingual metadata (en/te/hi/kn/ta).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from pipeline.cleaner import dedupe_schemes, validate_scheme_schema
from pipeline.diff_log import write_diff_log
from pipeline.indexer import build_index_metadata

SEED = 42


def _make_scheme(
    scheme_id: str,
    name: str,
    ministry: str,
    state: str,
    category: str,
    benefits: str,
    annual_benefit_inr: int,
    eligibility_text: str,
    rules: List[Dict[str, Any]],
    documents: List[str],
    apply_url: str,
    source_url: str,
    translations: Dict[str, str],
    keywords: List[str],
    mutually_exclusive_with: List[str] | None = None,
    complementary_to: List[str] | None = None,
    supersedes: List[str] | None = None,
    sub_scheme_of: str | None = None,
    last_updated: str = "2026-11-15",
) -> Dict[str, Any]:
    return {
        "scheme_id": scheme_id,
        "name": name,
        "ministry": ministry,
        "state": state,
        "category": category,
        "benefits": benefits,
        "annual_benefit_inr": annual_benefit_inr,
        "eligibility_text": eligibility_text,
        "rules": rules,
        "documents": documents,
        "apply_url": apply_url,
        "source_url": source_url,
        "last_updated": last_updated,
        "lang": "en",
        "translations": translations,
        "keywords": keywords,
        "mutually_exclusive_with": mutually_exclusive_with or [],
        "complementary_to": complementary_to or [],
        "supersedes": supersedes or [],
        "sub_scheme_of": sub_scheme_of,
    }


def build_core_schemes() -> List[Dict[str, Any]]:
    """Return 35 deeply authored flagship schemes across Central, TS, AP, KA, and TN."""
    return [
        # --- TELANGANA FLAGSHIP SCHEMES (core to Telangana SC Woman Farmer demo) ---
        _make_scheme(
            "TS_RYTHU_BHAROSA",
            "Telangana Rythu Bharosa",
            "Department of Agriculture, Govt of Telangana",
            "Telangana",
            "Agriculture",
            "Rs 12,000 per acre per year (Rs 6,000 per season) direct investment support to land-owning farmers.",
            15000,
            "Resident of Telangana; occupation Farmer; cultivable land >= 0.5 acres; age >= 18; annual family income <= Rs 5,00,000.",
            [
                {"field": "state", "op": "==", "value": "Telangana", "label": "Resident of Telangana"},
                {"field": "occupation", "op": "in", "value": ["Farmer", "Agricultural Laborer"], "label": "Farmer occupation"},
                {"field": "land", "op": ">=", "value": 0.5, "label": "Cultivable land >= 0.5 acres"},
                {"field": "age", "op": ">=", "value": 18, "label": "Age >= 18 years"},
                {"field": "income", "op": "<=", "value": 500000, "label": "Annual income <= Rs 5,00,000"},
            ],
            ["Pattadar Passbook (Dharani)", "Aadhaar Card", "Bank Account Passbook (Aadhaar-seeded)", "Telangana Domicile / Ration Card"],
            "https://rythubharosa.telangana.gov.in",
            "https://agri.telangana.gov.in",
            {
                "te": "తెలంగాణ రైతు భరోసా — ఎకరాకు సంవత్సరానికి రూ. 12,000 పంట పెట్టుబడి సహాయం.",
                "hi": "तेलंगाना रैतु भरोसा — किसानों को प्रति एकड़ ₹12,000 वार्षिक निवेश सहायता।",
                "kn": "ತೆಲಂಗಾಣ ರೈತು ಭರೋಸಾ — ರೈತರಿಗೆ ಪ್ರತಿ ಎಕರೆಗೆ ವಾರ್ಷಿಕ ರೂ. 12,000 ಹೂಡಿಕೆ ನೆರವು.",
                "ta": "தெலங்கானா ரைத்து பரோசா — விவசாயிகளுக்கு ஏக்கருக்கு ஆண்டு ரூ.12,000 உதவி.",
            },
            ["rythu bharosa", "rythu bandhu", "telangana farmer", "రైతు భరోసా", "తెలంగాణ రైతు", "వ్యవసాయం", "investment support"],
            mutually_exclusive_with=["TS_RYTHU_BANDHU_LEGACY"],
            complementary_to=["IN_PM_KISAN", "TS_RYTHU_BIMA", "TS_MAHALAKSHMI", "IN_PMFBY"],
            supersedes=["TS_RYTHU_BANDHU_LEGACY"],
        ),
        _make_scheme(
            "TS_RYTHU_BANDHU_LEGACY",
            "Rythu Bandhu (Legacy Superseded)",
            "Department of Agriculture, Govt of Telangana",
            "Telangana",
            "Agriculture",
            "Rs 10,000 per acre per year investment support (superseded by Rythu Bharosa).",
            10000,
            "Resident of Telangana; Farmer with land >= 0.5 acres; age >= 18.",
            [
                {"field": "state", "op": "==", "value": "Telangana", "label": "Resident of Telangana"},
                {"field": "occupation", "op": "in", "value": ["Farmer"], "label": "Farmer occupation"},
                {"field": "land", "op": ">=", "value": 0.5, "label": "Cultivable land >= 0.5 acres"},
                {"field": "age", "op": ">=", "value": 18, "label": "Age >= 18 years"},
            ],
            ["Pattadar Passbook (Dharani)", "Aadhaar Card", "Bank Account Passbook"],
            "https://agri.telangana.gov.in",
            "https://agri.telangana.gov.in",
            {
                "te": "రైతు బంధు (పాత పథకం — రైతు భరోసా ద్వారా భర్తీ చేయబడింది).",
                "hi": "रैतु बंधु (पुराना संस्करण — रैतु भरोसा द्वारा प्रतिस्थापित)।",
                "kn": "ರೈತು ಬಂಧು (ಹಳೆಯ ಯೋಜನೆ).",
                "ta": "ரைத்து பந்து (பழைய திட்டம்).",
            },
            ["rythu bandhu", "రైతు బంధు", "legacy farmer telangana"],
            mutually_exclusive_with=["TS_RYTHU_BHAROSA"],
            complementary_to=["IN_PM_KISAN"],
        ),
        _make_scheme(
            "TS_MAHALAKSHMI",
            "Telangana Mahalakshmi Scheme",
            "Dept of Women Development & Child Welfare, Telangana",
            "Telangana",
            "Women & Social Welfare",
            "Rs 2,500/month (Rs 30,000/year) financial assistance to women heads of household + Rs 500 LPG cylinder + free TSRTC bus travel.",
            30000,
            "Resident of Telangana; Female; age 18 to 65; annual family income <= Rs 2,00,000; BPL / White Ration Card holder.",
            [
                {"field": "state", "op": "==", "value": "Telangana", "label": "Resident of Telangana"},
                {"field": "gender", "op": "==", "value": "Female", "label": "Female beneficiary"},
                {"field": "age", "op": ">=", "value": 18, "label": "Age >= 18 years"},
                {"field": "age", "op": "<=", "value": 65, "label": "Age <= 65 years"},
                {"field": "income", "op": "<=", "value": 200000, "label": "Annual income <= Rs 2,00,000"},
                {"field": "bpl", "op": "==", "value": True, "label": "White Ration Card / BPL"},
            ],
            ["Telangana Food Security (White Ration) Card", "Aadhaar Card", "Income Certificate", "Bank Account Passbook (Aadhaar-seeded)", "LPG Consumer Book"],
            "https://prajapalana.telangana.gov.in",
            "https://telangana.gov.in",
            {
                "te": "మహాలక్ష్మి పథకం — మహిళలకు నెలకు రూ. 2,500 ఆర్థిక సహాయం, రూ. 500 గ్యాస్ సిలిండర్ మరియు ఉచిత ఆర్టీసీ బస్సు ప్రయాణం.",
                "hi": "महालक्ष्मी योजना — तेलंगाना की महिलाओं को ₹2,500/माह वित्तीय सहायता और ₹500 गैस सिलेंडर।",
                "kn": "ಮಹಾಲಕ್ಷ್ಮಿ ಯೋಜನೆ — ತೆಲಂಗಾಣ ಮಹಿಳೆಯರಿಗೆ ಮಾಸಿಕ ರೂ. 2,500 ಸಹಾಯ.",
                "ta": "மகாலட்சுமி திட்டம் — தெலங்கானா பெண்களுக்கு மாதம் ரூ.2,500 உதவி.",
            },
            ["mahalakshmi", "మహాలక్ష్మి", "telangana women", "మహిళా పథకం", "free bus", "lpg 500", "2500 monthly"],
            mutually_exclusive_with=["TS_AASARA_PENSION"],
            complementary_to=["TS_RYTHU_BHAROSA", "IN_PM_KISAN", "TS_GRIHA_JYOTHI"],
        ),
        _make_scheme(
            "TS_RYTHU_BIMA",
            "Telangana Rythu Bima (Farmer Life Insurance)",
            "Department of Agriculture, Govt of Telangana",
            "Telangana",
            "Insurance",
            "Rs 5,00,000 life insurance cover paid by Govt of Telangana (zero premium for farmer, annual actuarial value Rs 4,500).",
            4500,
            "Resident of Telangana; Farmer with Pattadar Passbook (land >= 0.1 acres); age 18 to 59.",
            [
                {"field": "state", "op": "==", "value": "Telangana", "label": "Resident of Telangana"},
                {"field": "occupation", "op": "in", "value": ["Farmer"], "label": "Farmer occupation"},
                {"field": "land", "op": ">=", "value": 0.1, "label": "Pattadar land >= 0.1 acres"},
                {"field": "age", "op": ">=", "value": 18, "label": "Age >= 18 years"},
                {"field": "age", "op": "<=", "value": 59, "label": "Age <= 59 years"},
            ],
            ["Pattadar Passbook (Dharani)", "Aadhaar Card", "Nominee Aadhaar Card"],
            "https://rythubima.telangana.gov.in",
            "https://agri.telangana.gov.in",
            {
                "te": "రైతు బీమా — తెలంగాణ రైతులకు రూ. 5 లక్షల ఉచిత జీవిత బీమా.",
                "hi": "रैतु बीमा — तेलंगाना किसानों के लिए ₹5 लाख का निःशुल्क जीवन बीमा।",
                "kn": "ರೈತು ಬೀಮಾ — ರೈತರಿಗೆ ರೂ. 5 ಲಕ್ಷ ಉಚಿತ ಜೀವ ವಿಮೆ.",
                "ta": "ரைத்து பீமா — விவசாயிகளுக்கு ரூ.5 லட்சம் இலவச காப்பீடு.",
            },
            ["rythu bima", "రైతు బీమా", "farmer insurance telangana", "5 lakh insurance"],
            complementary_to=["TS_RYTHU_BHAROSA", "IN_PM_KISAN"],
        ),
        _make_scheme(
            "TS_DALIT_BANDHU",
            "Telangana Dalit Bandhu Enterprise Grant",
            "Scheduled Castes Development Dept, Telangana",
            "Telangana",
            "SC/ST Welfare",
            "One-time Rs 10,00,000 non-repayable capital grant (annualized Rs 1,00,000 over 10 yrs) for SC self-employment unit.",
            100000,
            "Resident of Telangana; Category SC; age 21 to 55; annual income <= Rs 1,50,000; BPL household.",
            [
                {"field": "state", "op": "==", "value": "Telangana", "label": "Resident of Telangana"},
                {"field": "category", "op": "in", "value": ["SC"], "label": "Scheduled Caste (SC)"},
                {"field": "age", "op": ">=", "value": 21, "label": "Age >= 21 years"},
                {"field": "age", "op": "<=", "value": 55, "label": "Age <= 55 years"},
                {"field": "income", "op": "<=", "value": 150000, "label": "Annual income <= Rs 1,50,000"},
                {"field": "bpl", "op": "==", "value": True, "label": "BPL household"},
            ],
            ["SC Caste Certificate (MeeSeva)", "Income Certificate", "Telangana Food Security (White Ration) Card", "Aadhaar Card", "Bank Account Passbook (Aadhaar-seeded)"],
            "https://dalitbandhu.telangana.gov.in",
            "https://scdd.telangana.gov.in",
            {
                "te": "దళిత బంధు — తెలంగాణ ఎస్సీ కుటుంబాలకు స్వయం ఉపాధి కోసం రూ. 10 లక్షల ఆర్థిక సహాయం.",
                "hi": "दलित बंधु — तेलंगाना एससी परिवारों को स्वरोजगार हेतु ₹10 लाख का अनुदान।",
                "kn": "ದಲಿತ ಬಂಧು — ಎಸ್‌ಸಿ ಕುಟುಂಬಗಳಿಗೆ ಸ್ವಯಂ ಉದ್ಯೋಗ ಅನುದಾನ.",
                "ta": "தலித் பந்து — பட்டியலின குடும்பங்களுக்கு சுயதொழில் மானியம்.",
            },
            ["dalit bandhu", "దళిత బంధు", "sc grant telangana", "10 lakh sc"],
            mutually_exclusive_with=["TS_SC_SUBSIDY_LOAN"],
            complementary_to=["TS_RYTHU_BHAROSA", "IN_PM_KISAN"],
        ),
        _make_scheme(
            "TS_SC_SUBSIDY_LOAN",
            "TS SC Corporation Economic Support Subsidy",
            "Telangana SC Cooperative Development Corp",
            "Telangana",
            "SC/ST Welfare",
            "Up to Rs 80,000 subsidy (80% on Rs 1L unit) for SC agriculture allied or micro-business unit.",
            25000,
            "Resident of Telangana; Category SC; age 21 to 55; annual income <= Rs 2,00,000.",
            [
                {"field": "state", "op": "==", "value": "Telangana", "label": "Resident of Telangana"},
                {"field": "category", "op": "in", "value": ["SC"], "label": "Scheduled Caste (SC)"},
                {"field": "age", "op": ">=", "value": 21, "label": "Age >= 21 years"},
                {"field": "age", "op": "<=", "value": 55, "label": "Age <= 55 years"},
                {"field": "income", "op": "<=", "value": 200000, "label": "Annual income <= Rs 2,00,000"},
            ],
            ["SC Caste Certificate (MeeSeva)", "Income Certificate", "Aadhaar Card", "Bank Account Passbook (Aadhaar-seeded)"],
            "https://tsobmms.cgg.gov.in",
            "https://scdd.telangana.gov.in",
            {
                "te": "తెలంగాణ ఎస్సీ కార్పొరేషన్ సబ్సిడీ రుణం — రూ. 80,000 వరకు సబ్సిడీ.",
                "hi": "तेलंगाना एससी कॉर्पोरेशन सब्सिडी ऋण — ₹80,000 तक अनुदान।",
                "kn": "ತೆಲಂಗಾಣ ಎಸ್‌ಸಿ ಕಾರ್ಪೊರೇಷನ್ ಸಬ್ಸಿಡಿ ಸಾಲ.",
                "ta": "தெலங்கானா எஸ்சி கழகம் மானியக் கடன்.",
            },
            ["sc corporation", "tsobmms", "ఎస్సీ రుణం", "sc subsidy telangana"],
            mutually_exclusive_with=["TS_DALIT_BANDHU"],
            complementary_to=["TS_RYTHU_BHAROSA"],
        ),
        _make_scheme(
            "TS_GRIHA_JYOTHI",
            "Telangana Gruha Jyothi (200 Units Free Power)",
            "Energy Department, Govt of Telangana",
            "Telangana",
            "Housing & Utilities",
            "Up to 200 units free domestic electricity per month (annual savings ~Rs 14,400).",
            14400,
            "Resident of Telangana; BPL / White Ration Card holder; annual income <= Rs 2,50,000.",
            [
                {"field": "state", "op": "==", "value": "Telangana", "label": "Resident of Telangana"},
                {"field": "bpl", "op": "==", "value": True, "label": "White Ration Card / BPL"},
                {"field": "income", "op": "<=", "value": 250000, "label": "Annual income <= Rs 2,50,000"},
            ],
            ["Telangana Food Security (White Ration) Card", "Aadhaar Card", "Electricity Service Connection Number"],
            "https://prajapalana.telangana.gov.in",
            "https://telangana.gov.in",
            {
                "te": "గృహ జ్యోతి — నెలకు 200 యూనిట్ల వరకు ఉచిత విద్యుత్.",
                "hi": "गृह ज्योति — प्रति माह 200 यूनिट तक निःशुल्क बिजली।",
                "kn": "ಗೃಹ ಜ್ಯೋತಿ — ಮಾಸಿಕ 200 ಯೂನಿಟ್ ಉಚಿತ ವಿದ್ಯುತ್.",
                "ta": "கிரஹ ஜோதி — மாதம் 200 யூனிட் இலவச மின்சாரம்.",
            },
            ["gruha jyothi", "griha jyothi", "గృహ జ్యోతి", "free electricity telangana", "200 units"],
            complementary_to=["TS_MAHALAKSHMI", "TS_RYTHU_BHAROSA"],
        ),
        _make_scheme(
            "TS_INDIRAMMA_INDLU",
            "Indiramma Indlu Housing Scheme",
            "Telangana State Housing Corporation",
            "Telangana",
            "Housing & Utilities",
            "Rs 5,00,000 grant for house construction (annualized Rs 50,000) for homeless BPL families; priority for SC/ST.",
            50000,
            "Resident of Telangana; BPL household; annual income <= Rs 2,00,000; age >= 18; priority SC/ST/OBC.",
            [
                {"field": "state", "op": "==", "value": "Telangana", "label": "Resident of Telangana"},
                {"field": "bpl", "op": "==", "value": True, "label": "BPL / White Ration Card"},
                {"field": "income", "op": "<=", "value": 200000, "label": "Annual income <= Rs 2,00,000"},
                {"field": "age", "op": ">=", "value": 18, "label": "Age >= 18 years"},
            ],
            ["Telangana Food Security (White Ration) Card", "Aadhaar Card", "Income Certificate", "House Site Patta / Land Document"],
            "https://indirammaindlu.telangana.gov.in",
            "https://housing.telangana.gov.in",
            {
                "te": "ఇందిరమ్మ ఇండ్లు — పేద కుటుంబాలకు ఇంటి నిర్మాణం కోసం రూ. 5 లక్షల సహాయం.",
                "hi": "इंदिरम्मा इंद्लु — बेघर परिवारों को घर निर्माण हेतु ₹5 लाख सहायता।",
                "kn": "ಇಂದಿರಮ್ಮ ಇಂಡ್ಲು ವಸತಿ ಯೋಜನೆ.",
                "ta": "இந்திரம்மா வீட்டு வசதித் திட்டம்.",
            },
            ["indiramma indlu", "ఇందిరమ్మ ఇండ్లు", "telangana housing", "5 lakh house"],
            mutually_exclusive_with=["IN_PMAY_GRAMIN", "IN_PMAY_URBAN"],
            complementary_to=["TS_GRIHA_JYOTHI", "TS_MAHALAKSHMI"],
        ),
        _make_scheme(
            "TS_AASARA_PENSION",
            "Telangana Cheyutha / Aasara Social Security Pension",
            "SERP, Govt of Telangana",
            "Telangana",
            "Social Security",
            "Rs 4,000/month (Rs 48,000/year) pension for elderly (57+), widows, or persons with disabilities.",
            48000,
            "Resident of Telangana; BPL household; annual income <= Rs 1,50,000; age >= 57.",
            [
                {"field": "state", "op": "==", "value": "Telangana", "label": "Resident of Telangana"},
                {"field": "bpl", "op": "==", "value": True, "label": "BPL household"},
                {"field": "income", "op": "<=", "value": 150000, "label": "Annual income <= Rs 1,50,000"},
                {"field": "age", "op": ">=", "value": 57, "label": "Age >= 57 years"},
            ],
            ["Telangana Food Security (White Ration) Card", "Aadhaar Card", "Age Proof Certificate", "Bank Account Passbook (Aadhaar-seeded)"],
            "https://aasara.telangana.gov.in",
            "https://telangana.gov.in",
            {
                "te": "ఆసరా / చేయూత పింఛను — వృద్ధులు మరియు వితంతువులకు నెలకు రూ. 4,000 పింఛను.",
                "hi": "आसरा / चेयुता पेंशन — बुजुर्गों और विधवाओं को ₹4,000/माह पेंशन।",
                "kn": "ಆಸರಾ ಪಿಂಚಣಿ ಯೋಜನೆ.",
                "ta": "ஆசரா ஓய்வூதியத் திட்டம்.",
            },
            ["aasara", "cheyutha pension", "ఆసరా పింఛను", "telangana pension"],
            mutually_exclusive_with=["TS_MAHALAKSHMI", "IN_IGNOAPS"],
            complementary_to=["TS_GRIHA_JYOTHI"],
        ),
        _make_scheme(
            "TS_KALYANA_LAKSHMI",
            "Telangana Kalyana Lakshmi / Shaadi Mubarak",
            "SC/ST/BC/Minority Welfare Dept, Telangana",
            "Telangana",
            "Women & Social Welfare",
            "Rs 1,00,116 marriage financial assistance grant for brides from SC/ST/BC/Minority families.",
            100116,
            "Resident of Telangana; Female; age 18 to 35; Category SC/ST/OBC/Minority; annual income <= Rs 2,00,000.",
            [
                {"field": "state", "op": "==", "value": "Telangana", "label": "Resident of Telangana"},
                {"field": "gender", "op": "==", "value": "Female", "label": "Female bride"},
                {"field": "age", "op": ">=", "value": 18, "label": "Age >= 18 years"},
                {"field": "age", "op": "<=", "value": 35, "label": "Age <= 35 years"},
                {"field": "category", "op": "in", "value": ["SC", "ST", "OBC", "Minority"], "label": "SC/ST/OBC/Minority category"},
                {"field": "income", "op": "<=", "value": 200000, "label": "Annual income <= Rs 2,00,000"},
            ],
            ["Caste Certificate (MeeSeva)", "Income Certificate", "Bride Age Proof (18+)", "Aadhaar Card", "Bank Account Passbook (Aadhaar-seeded)"],
            "https://telanganaepass.cgg.gov.in",
            "https://telangana.gov.in",
            {
                "te": "కళ్యాణ లక్ష్మి / షాదీ ముబారక్ — వధువు వివాహానికి రూ. 1,00,116 ఆర్థిక సహాయం.",
                "hi": "कल्याण लक्ष्मी / शादी मुबारक — विवाह हेतु ₹1,00,116 सहायता।",
                "kn": "ಕಲ್ಯಾಣ ಲಕ್ಷ್ಮಿ ಯೋಜನೆ.",
                "ta": "கல்யாண லட்சுமி திட்டம்.",
            },
            ["kalyana lakshmi", "shaadi mubarak", "కళ్యాణ లక్ష్మి", "marriage grant telangana"],
            complementary_to=["TS_MAHALAKSHMI"],
        ),
        _make_scheme(
            "TS_AROGYASRI",
            "Rajiv Aarogyasri Health Insurance (Telangana)",
            "Aarogyasri Health Care Trust, Telangana",
            "Telangana",
            "Health",
            "Cashless tertiary medical treatment cover up to Rs 10,00,000 per family/year (annualized premium value Rs 6,000).",
            6000,
            "Resident of Telangana; BPL / White Ration Card holder; annual income <= Rs 2,00,000.",
            [
                {"field": "state", "op": "==", "value": "Telangana", "label": "Resident of Telangana"},
                {"field": "bpl", "op": "==", "value": True, "label": "White Ration Card / BPL"},
                {"field": "income", "op": "<=", "value": 200000, "label": "Annual income <= Rs 2,00,000"},
            ],
            ["Telangana Food Security (White Ration) Card", "Aadhaar Card", "Aarogyasri Health Card"],
            "https://aarogyasri.telangana.gov.in",
            "https://telangana.gov.in",
            {
                "te": "రాజీవ్ ఆరోగ్యశ్రీ — సంవత్సరానికి రూ. 10 లక్షల వరకు ఉచిత వైద్యం.",
                "hi": "राजीव आरोग्यश्री — ₹10 लाख तक निःशुल्क कैशलेस चिकित्सा।",
                "kn": "ರಾಜೀವ್ ಆರೋಗ್ಯಶ್ರೀ ಆರೋಗ್ಯ ವಿಮೆ.",
                "ta": "ராஜீவ் ஆரோக்கியஸ்ரீ மருத்துவ காப்பீடு.",
            },
            ["aarogyasri", "ఆరోగ్యశ్రీ", "telangana health", "10 lakh hospital"],
            complementary_to=["IN_PMJAY", "TS_RYTHU_BHAROSA"],
        ),

        # --- CENTRAL GOVERNMENT FLAGSHIP SCHEMES ---
        _make_scheme(
            "IN_PM_KISAN",
            "PM-KISAN Samman Nidhi",
            "Ministry of Agriculture & Farmers Welfare",
            "All India",
            "Agriculture",
            "Rs 6,000 per year paid in three equal installments of Rs 2,000 via Direct Benefit Transfer.",
            6000,
            "All India resident; Occupation Farmer; cultivable land >= 0.1 acres; age >= 18; annual family income <= Rs 4,00,000 (non-income-tax-payer).",
            [
                {"field": "occupation", "op": "in", "value": ["Farmer"], "label": "Farmer occupation"},
                {"field": "land", "op": ">=", "value": 0.1, "label": "Cultivable land >= 0.1 acres"},
                {"field": "age", "op": ">=", "value": 18, "label": "Age >= 18 years"},
                {"field": "income", "op": "<=", "value": 400000, "label": "Non-taxpayer income <= Rs 4,00,000"},
            ],
            ["Aadhaar Card", "Land Ownership Record (ROR / Pattadar Passbook)", "Bank Account Passbook (Aadhaar-seeded)"],
            "https://pmkisan.gov.in",
            "https://myscheme.gov.in/schemes/pm-kisan",
            {
                "te": "పీఎం-కిసాన్ సమ్మాన్ నిధి — రైతులకు సంవత్సరానికి రూ. 6,000 నేరుగా బ్యాంకు ఖాతాలో జమ.",
                "hi": "पीएम-किसान सम्मान निधि — पात्र किसानों को प्रति वर्ष ₹6,000 प्रत्यक्ष लाभ अंतरण।",
                "kn": "ಪಿಎಂ-ಕಿಸಾನ್ ಸಮ್ಮಾನ್ ನಿಧಿ — ರೈತರಿಗೆ ವಾರ್ಷಿಕ ರೂ. 6,000 ನೇರ ನಗದು ವರ್ಗಾವಣೆ.",
                "ta": "பிஎம்-கிசான் சம்மான் நிதி — விவசாயிகளுக்கு ஆண்டுக்கு ரூ.6,000 நேரடி நிதி உதவி.",
            },
            ["pm kisan", "pm-kisan", "kisan samman nidhi", "పీఎం కిసాన్", "पीएम किसान", "ಪಿಎಂ ಕಿಸಾನ್", "பிஎம் கிசான்", "6000 farmer"],
            complementary_to=["TS_RYTHU_BHAROSA", "AP_ANNADATA_SUKHIBHAVA", "IN_PMFBY", "IN_KCC", "TS_RYTHU_BIMA"],
        ),
        _make_scheme(
            "IN_PMFBY",
            "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
            "Ministry of Agriculture & Farmers Welfare",
            "All India",
            "Agriculture",
            "Subsidized crop insurance (farmer pays max 2% Kharif / 1.5% Rabi; avg claim protection value Rs 12,000/yr).",
            12000,
            "All India; Occupation Farmer; cultivable land >= 0.2 acres; age >= 18.",
            [
                {"field": "occupation", "op": "in", "value": ["Farmer"], "label": "Farmer occupation"},
                {"field": "land", "op": ">=", "value": 0.2, "label": "Cultivable land >= 0.2 acres"},
                {"field": "age", "op": ">=", "value": 18, "label": "Age >= 18 years"},
            ],
            ["Aadhaar Card", "Land Ownership Record (ROR / Pattadar Passbook)", "Sowing Certificate", "Bank Account Passbook (Aadhaar-seeded)"],
            "https://pmfby.gov.in",
            "https://myscheme.gov.in/schemes/pmfby",
            {
                "te": "ప్రధాన మంత్రి ఫసల్ బీమా యోజన — పంట నష్టానికి తక్కువ ప్రీమియంతో పంట బీమా.",
                "hi": "प्रधानमंत्री फसल बीमा योजना — कम प्रीमियम पर फसल नुकसान से सुरक्षा।",
                "kn": "ಪ್ರಧಾನ ಮಂತ್ರಿ ಫಸಲ್ ಬಿಮಾ ಯೋಜನೆ — ಬೆಳೆ ವಿಮೆ ರಕ್ಷಣೆ.",
                "ta": "பிரதமர் பயிர் காப்பீட்டுத் திட்டம் — குறைந்த பிரிமியத்தில் பயிர் காப்பீடு.",
            },
            ["pmfby", "fasal bima", "crop insurance", "పంట బీమా", "फसल बीमा", "ಬೆಳೆ ವಿಮೆ", "பயிர் காப்பீடு"],
            complementary_to=["IN_PM_KISAN", "TS_RYTHU_BHAROSA", "IN_KCC"],
        ),
        _make_scheme(
            "IN_KCC",
            "Kisan Credit Card (KCC) Interest Subvention",
            "Ministry of Agriculture & Farmers Welfare",
            "All India",
            "Agriculture",
            "Short-term crop credit up to Rs 3,00,000 at 4% effective interest (annual interest subsidy value ~Rs 9,000).",
            9000,
            "All India; Occupation Farmer; cultivable land >= 0.5 acres; age 18 to 75.",
            [
                {"field": "occupation", "op": "in", "value": ["Farmer"], "label": "Farmer occupation"},
                {"field": "land", "op": ">=", "value": 0.5, "label": "Cultivable land >= 0.5 acres"},
                {"field": "age", "op": ">=", "value": 18, "label": "Age >= 18 years"},
                {"field": "age", "op": "<=", "value": 75, "label": "Age <= 75 years"},
            ],
            ["Aadhaar Card", "Land Ownership Record (ROR / Pattadar Passbook)", "PAN Card / Form 60", "Bank Account Passbook (Aadhaar-seeded)"],
            "https://www.myscheme.gov.in/schemes/kcc",
            "https://myscheme.gov.in/schemes/kcc",
            {
                "te": "కిసాన్ క్రెడిట్ కార్డ్ — 4% వడ్డీతో రూ. 3 లక్షల వరకు పంట రుణం.",
                "hi": "किसान क्रेडिट कार्ड — 4% प्रभावी ब्याज पर ₹3 लाख तक फसल ऋण।",
                "kn": "ಕಿಸಾನ್ ಕ್ರೆಡಿಟ್ ಕಾರ್ಡ್ — 4% ಬಡ್ಡಿದರದಲ್ಲಿ ಬೆಳೆ ಸಾಲ.",
                "ta": "கிசான் கிரெடிட் கார்டு — 4% வட்டியில் பயிர்க்கடன்.",
            },
            ["kcc", "kisan credit card", "crop loan", "పంట రుణం", "किसान क्रेडिट कार्ड"],
            complementary_to=["IN_PM_KISAN", "IN_PMFBY"],
        ),
        _make_scheme(
            "IN_PM_KUSUM",
            "PM-KUSUM Solar Pump Subsidy (Component B)",
            "Ministry of New and Renewable Energy",
            "All India",
            "Agriculture",
            "60% combined Central+State subsidy on standalone solar agricultural pumps (annualized savings Rs 24,000).",
            24000,
            "All India; Occupation Farmer; cultivable land >= 1.0 acres; age >= 18; Rural residence.",
            [
                {"field": "occupation", "op": "in", "value": ["Farmer"], "label": "Farmer occupation"},
                {"field": "land", "op": ">=", "value": 1.0, "label": "Cultivable land >= 1.0 acre"},
                {"field": "age", "op": ">=", "value": 18, "label": "Age >= 18 years"},
                {"field": "residence", "op": "==", "value": "Rural", "label": "Rural agricultural area"},
            ],
            ["Aadhaar Card", "Land Ownership Record (ROR / Pattadar Passbook)", "Bank Account Passbook (Aadhaar-seeded)"],
            "https://pmkusum.mnre.gov.in",
            "https://myscheme.gov.in/schemes/pm-kusum",
            {
                "te": "పీఎం-కుసుమ్ — రైతులకు 60% సబ్సిడీతో సోలార్ పంప్ సెట్.",
                "hi": "पीएम-कुसुम — किसानों को सोलर पंप पर 60% सब्सिडी।",
                "kn": "ಪಿಎಂ-ಕುಸುಮ್ — ಸೌರ ಪಂಪ್‌ಸೆಟ್‌ಗೆ 60% ಸಬ್ಸಿಡಿ.",
                "ta": "பிஎம்-குசும் — சூரிய சக்தி பம்ப்செட்டுக்கு 60% மானியம்.",
            },
            ["pm kusum", "solar pump", "సోలార్ పంప్", "सोलर पंप"],
            complementary_to=["IN_PM_KISAN", "TS_RYTHU_BHAROSA"],
        ),
        _make_scheme(
            "IN_PMJAY",
            "Ayushman Bharat PM-JAY Health Assurance",
            "Ministry of Health & Family Welfare (NHA)",
            "All India",
            "Health",
            "Rs 5,00,000 cashless hospitalization cover per family per year across empanelled hospitals (value Rs 5,000/yr).",
            5000,
            "All India; BPL / SECC-2011 deprived household; annual income <= Rs 2,50,000.",
            [
                {"field": "bpl", "op": "==", "value": True, "label": "BPL / SECC eligible household"},
                {"field": "income", "op": "<=", "value": 250000, "label": "Annual income <= Rs 2,50,000"},
            ],
            ["Aadhaar Card", "Ration Card / SECC Family ID", "Income Certificate"],
            "https://pmjay.gov.in",
            "https://myscheme.gov.in/schemes/ab-pmjay",
            {
                "te": "ఆయుష్మాన్ భారత్ పీఎం-జెఎవై — కుటుంబానికి రూ. 5 లక్షల ఉచిత వైద్య బీమా.",
                "hi": "आयुष्मान भारत पीएम-जय — प्रति परिवार ₹5 लाख का निःशुल्क स्वास्थ्य बीमा।",
                "kn": "ಆಯುಷ್ಮಾನ್ ಭಾರತ್ ಪಿಎಂ-ಜಯ — ಪ್ರತಿ ಕುಟುಂಬಕ್ಕೆ ರೂ. 5 ಲಕ್ಷ ಆರೋಗ್ಯ ವಿಮೆ.",
                "ta": "ஆயுஷ்மான் பாரத் — குடும்பத்திற்கு ரூ.5 லட்சம் மருத்துவ காப்பீடு.",
            },
            ["ayushman bharat", "pmjay", "pm-jay", "ఆయుష్మాన్", "आयुष्मान भारत", "ಆಯುಷ್ಮಾನ್", "ஆயுஷ்மான்"],
            complementary_to=["TS_AROGYASRI", "IN_PM_KISAN"],
        ),
        _make_scheme(
            "IN_PMAY_GRAMIN",
            "Pradhan Mantri Awaas Yojana - Gramin (PMAY-G)",
            "Ministry of Rural Development",
            "All India",
            "Housing & Utilities",
            "Rs 1,20,000 (plains) / Rs 1,30,000 (hilly) pucca house grant + 90 days MGNREGA wages (annualized Rs 28,000).",
            28000,
            "All India; Rural residence; BPL household; annual income <= Rs 1,50,000; age >= 18.",
            [
                {"field": "residence", "op": "==", "value": "Rural", "label": "Rural residence"},
                {"field": "bpl", "op": "==", "value": True, "label": "BPL / SECC houseless"},
                {"field": "income", "op": "<=", "value": 150000, "label": "Annual income <= Rs 1,50,000"},
                {"field": "age", "op": ">=", "value": 18, "label": "Age >= 18 years"},
            ],
            ["Aadhaar Card", "MGNREGA Job Card", "BPL / Ration Card", "Bank Account Passbook (Aadhaar-seeded)"],
            "https://pmayg.nic.in",
            "https://myscheme.gov.in/schemes/pmay-g",
            {
                "te": "పీఎం ఆవాస్ యోజన గ్రామీణ — గ్రామీణ పేదలకు పక్కా ఇల్లు నిర్మాణానికి రూ. 1.20 లక్షల సహాయం.",
                "hi": "प्रधानमंत्री आवास योजना ग्रामीण — ग्रामीण गरीबों को पक्का मकान हेतु ₹1.20 लाख सहायता।",
                "kn": "ಪ್ರಧಾನ ಮಂತ್ರಿ ಆವಾಸ್ ಯೋಜನೆ ಗ್ರಾಮೀಣ — ಮನೆ ನಿರ್ಮಾಣ ಸಹಾಯ.",
                "ta": "பிரதமர் ஊரக வீட்டு வசதித் திட்டம் — வீடு கட்ட ரூ.1.20 லட்சம் மானியம்.",
            },
            ["pmay gramin", "pmay-g", "awas yojana", "ఆవాస్ యోజన", "आवास योजना", "rural house"],
            mutually_exclusive_with=["IN_PMAY_URBAN", "TS_INDIRAMMA_INDLU"],
            complementary_to=["IN_UJJWALA", "IN_MGNREGA"],
        ),
        _make_scheme(
            "IN_PMAY_URBAN",
            "Pradhan Mantri Awas Yojana - Urban (PMAY-U 2.0)",
            "Ministry of Housing & Urban Affairs",
            "All India",
            "Housing & Utilities",
            "Up to Rs 2,50,000 interest subsidy / BLC construction grant for EWS/LIG urban families (annualized Rs 32,000).",
            32000,
            "All India; Urban residence; annual income <= Rs 3,00,000 (EWS); age >= 18.",
            [
                {"field": "residence", "op": "==", "value": "Urban", "label": "Urban residence"},
                {"field": "income", "op": "<=", "value": 300000, "label": "EWS annual income <= Rs 3,00,000"},
                {"field": "age", "op": ">=", "value": 18, "label": "Age >= 18 years"},
            ],
            ["Aadhaar Card", "Income Certificate", "Urban Domicile Proof", "Bank Account Passbook (Aadhaar-seeded)"],
            "https://pmaymis.gov.in",
            "https://myscheme.gov.in/schemes/pmay-u",
            {
                "te": "పీఎం ఆవాస్ యోజన అర్బన్ — పట్టణ పేదలకు రూ. 2.5 లక్షల వరకు గృహ సబ్సిడీ.",
                "hi": "प्रधानमंत्री आवास योजना शहरी — शहरी परिवारों को ₹2.5 लाख तक आवास सब्सिडी।",
                "kn": "ಪಿಎಂ ಆವಾಸ್ ಯೋಜನೆ ನಗರ — ವಸತಿ ಸಹಾಯಧನ.",
                "ta": "பிரதமர் நகர்ப்புற வீட்டு வசதித் திட்டம்.",
            },
            ["pmay urban", "pmay-u", "urban housing", "शहरी आवास"],
            mutually_exclusive_with=["IN_PMAY_GRAMIN", "TS_INDIRAMMA_INDLU"],
            complementary_to=["IN_PM_SVANIDHI"],
        ),
        _make_scheme(
            "IN_UJJWALA",
            "Pradhan Mantri Ujjwala Yojana 2.0",
            "Ministry of Petroleum & Natural Gas",
            "All India",
            "Women & Social Welfare",
            "Deposit-free LPG connection + Rs 300/cylinder targeted subsidy (12 cylinders = Rs 3,600/yr + Rs 1,600 kit).",
            5200,
            "All India; Female; age >= 18; BPL household; annual income <= Rs 2,00,000.",
            [
                {"field": "gender", "op": "==", "value": "Female", "label": "Adult woman applicant"},
                {"field": "age", "op": ">=", "value": 18, "label": "Age >= 18 years"},
                {"field": "bpl", "op": "==", "value": True, "label": "BPL / SC / ST / SECC household"},
                {"field": "income", "op": "<=", "value": 200000, "label": "Annual income <= Rs 2,00,000"},
            ],
            ["Aadhaar Card", "Ration Card", "Bank Account Passbook (Aadhaar-seeded)", "Caste Certificate (if SC/ST)"],
            "https://pmuy.gov.in",
            "https://myscheme.gov.in/schemes/pmuy",
            {
                "te": "ఉజ్వల యోజన — బీపీఎల్ మహిళలకు ఉచిత గ్యాస్ కనెక్షన్ మరియు సిలిండర్ సబ్సిడీ.",
                "hi": "प्रधानमंत्री उज्ज्वला योजना — बीपीएल महिलाओं को निःशुल्क एलपीजी कनेक्शन और ₹300 सब्सिडी।",
                "kn": "ಉಜ್ವಲ ಯೋಜನೆ — ಮಹಿಳೆಯರಿಗೆ ಉಚಿತ ಎಲ್‌ಪಿಜಿ ಸಂಪರ್ಕ.",
                "ta": "உஜ்வாலா திட்டம் — பெண்களுக்கு இலவச சமையல் எரிவாயு இணைப்பு.",
            },
            ["ujjwala", "pmuy", "free lpg", "గ్యాస్ కనెక్షన్", "उज्ज्वला", "எரிவாயு"],
            complementary_to=["IN_PMAY_GRAMIN", "IN_PM_KISAN"],
        ),
        _make_scheme(
            "IN_MGNREGA",
            "Mahatma Gandhi NREGA (100 Days Wage Guarantee)",
            "Ministry of Rural Development",
            "All India",
            "Employment & Skill",
            "100 days guaranteed rural unskilled wage employment (~Rs 300/day = Rs 30,000/year per rural household).",
            30000,
            "All India; Rural residence; age >= 18; occupation Farmer / Agricultural Laborer / Unemployed / Artisan.",
            [
                {"field": "residence", "op": "==", "value": "Rural", "label": "Rural household"},
                {"field": "age", "op": ">=", "value": 18, "label": "Adult age >= 18"},
                {"field": "occupation", "op": "in", "value": ["Farmer", "Agricultural Laborer", "Unemployed", "Artisan", "Self-Employed"], "label": "Manual rural work seeker"},
            ],
            ["Aadhaar Card", "MGNREGA Job Card", "Bank Account Passbook (Aadhaar-seeded)"],
            "https://nrega.nic.in",
            "https://myscheme.gov.in/schemes/mgnrega",
            {
                "te": "ఉపాధి హామీ (MGNREGA) — గ్రామీణ కుటుంబాలకు సంవత్సరానికి 100 రోజుల పని హామీ.",
                "hi": "मनरेगा (MGNREGA) — ग्रामीण परिवारों को वर्ष में 100 दिन का गारंटीकृत रोजगार।",
                "kn": "ನರೇಗಾ (MGNREGA) — ಗ್ರಾಮೀಣ ಕುಟುಂಬಗಳಿಗೆ 100 ದಿನಗಳ ಉದ್ಯೋಗ ಖಾತರಿ.",
                "ta": "மகாத்மா காந்தி தேசிய ஊரக வேலை உறுதித் திட்டம் (100 நாள் வேலை).",
            },
            ["mgnrega", "nrega", "100 days work", "ఉపాధి హామీ", "मनरेगा", "ನರೇಗಾ", "100 நாள் வேலை"],
            complementary_to=["IN_PM_KISAN", "IN_PMAY_GRAMIN", "TS_RYTHU_BHAROSA"],
        ),
        _make_scheme(
            "IN_PM_VISHWAKARMA",
            "PM Vishwakarma Artisan Support Scheme",
            "Ministry of Micro, Small & Medium Enterprises",
            "All India",
            "Employment & Skill",
            "Rs 15,000 toolkit e-voucher + Rs 500/day skill stipend + collateral-free loan up to Rs 3 lakh at 5% interest.",
            22500,
            "All India; Occupation Artisan / Self-Employed; age >= 18; annual income <= Rs 3,00,000.",
            [
                {"field": "occupation", "op": "in", "value": ["Artisan", "Self-Employed"], "label": "Traditional artisan / craftsperson"},
                {"field": "age", "op": ">=", "value": 18, "label": "Age >= 18 years"},
                {"field": "income", "op": "<=", "value": 300000, "label": "Annual income <= Rs 3,00,000"},
            ],
            ["Aadhaar Card", "Ration Card", "Bank Account Passbook (Aadhaar-seeded)", "Mobile Linked to Aadhaar"],
            "https://pmvishwakarma.gov.in",
            "https://myscheme.gov.in/schemes/pm-vishwakarma",
            {
                "te": "పీఎం విశ్వకర్మ — చేతివృత్తుల వారికి రూ. 15,000 టూల్ కిట్ మరియు 5% వడ్డీతో రుణం.",
                "hi": "पीएम विश्वकर्मा — कारीगरों को ₹15,000 टूलकिट और 5% ब्याज पर ऋण।",
                "kn": "ಪಿಎಂ ವಿಶ್ವಕರ್ಮ — ಕುಶಲಕರ್ಮಿಗಳಿಗೆ ರೂ. 15,000 ಟೂಲ್‌ಕಿಟ್ ಸಹಾಯ.",
                "ta": "பிஎம் விஸ்வகர்மா — கைவினைஞர்களுக்கு ரூ.15,000 கருவித்தொகுப்பு உதவி.",
            },
            ["vishwakarma", "artisan", "carpenter", "potter", "విశ్వకర్మ", "विश्वकर्मा", "ವಿಶ್ವಕರ್ಮ", "விஸ்வகர்மா"],
            complementary_to=["IN_MUDRA_SHISHU", "IN_PMJAY"],
        ),
        _make_scheme(
            "IN_STANDUP_INDIA",
            "Stand-Up India SC/ST/Women Enterprise Scheme",
            "Ministry of Finance (DFS)",
            "All India",
            "SC/ST Welfare",
            "Bank loan Rs 10 lakh to Rs 1 crore with credit guarantee & handholding for greenfield enterprise (interest subsidy eq. Rs 45,000/yr).",
            45000,
            "All India; Age >= 18; Category SC or ST (or Female entrepreneur); Occupation Self-Employed / Farmer / Artisan / Unemployed.",
            [
                {"field": "age", "op": ">=", "value": 18, "label": "Age >= 18 years"},
                {"field": "category", "op": "in", "value": ["SC", "ST"], "label": "SC or ST entrepreneur"},
            ],
            ["Aadhaar Card", "PAN Card", "SC/ST Caste Certificate", "Business Project Report", "Bank Account Passbook (Aadhaar-seeded)"],
            "https://www.standupmitra.in",
            "https://myscheme.gov.in/schemes/sui",
            {
                "te": "స్టాండ్-అప్ ఇండియా — ఎస్సీ/ఎస్టీ మరియు మహిళా పారిశ్రామికవేత్తలకు రూ. 10 లక్షల నుండి రూ. 1 కోటి వరకు రుణం.",
                "hi": "स्टैंड-अप इंडिया — एससी/एसटी और महिला उद्यमियों के लिए ₹10 लाख से ₹1 करोड़ ऋण।",
                "kn": "ಸ್ಟ್ಯಾಂಡ್-ಅಪ್ ಇಂಡಿಯಾ — ಎಸ್‌ಸಿ/ಎಸ್‌ಟಿ ಮತ್ತು ಮಹಿಳಾ ಉದ್ಯಮಿಗಳಿಗೆ ಸಾಲ.",
                "ta": "ஸ்டாண்ட்-அப் இந்தியா — பட்டியலின மற்றும் பெண் தொழில்முனைவோர் கடன்.",
            },
            ["standup india", "sc business loan", "women entrepreneur", "స్టాండ్ అప్ ఇండియా", "स्टैंड अप इंडिया"],
            complementary_to=["IN_MUDRA_SHISHU"],
        ),
        _make_scheme(
            "IN_NSP_POST_MATRIC_SC",
            "Central Sector Post-Matric Scholarship for SC Students",
            "Ministry of Social Justice & Empowerment",
            "All India",
            "Education & Scholarship",
            "Full tuition fee reimbursement + academic allowance up to Rs 13,500/year directly to student bank account.",
            18000,
            "All India; Category SC; Occupation Student; age 15 to 30; annual family income <= Rs 2,50,000.",
            [
                {"field": "category", "op": "in", "value": ["SC"], "label": "Scheduled Caste (SC)"},
                {"field": "occupation", "op": "in", "value": ["Student"], "label": "Enrolled Student"},
                {"field": "age", "op": ">=", "value": 15, "label": "Age >= 15 years"},
                {"field": "age", "op": "<=", "value": 30, "label": "Age <= 30 years"},
                {"field": "income", "op": "<=", "value": 250000, "label": "Family income <= Rs 2,50,000"},
            ],
            ["SC Caste Certificate", "Income Certificate", "Previous Year Marksheet", "Bonafide Student Certificate", "Aadhaar Card", "Bank Account Passbook (Aadhaar-seeded)"],
            "https://scholarships.gov.in",
            "https://myscheme.gov.in/schemes/pms-sc",
            {
                "te": "ఎస్సీ పోస్ట్-మెట్రిక్ స్కాలర్‌షిప్ — ట్యూషన్ ఫీజు మరియు సంవత్సరానికి రూ. 13,500 వరకు భత్యం.",
                "hi": "अनुसूचित जाति पोस्ट-मैट्रिक छात्रवृत्ति — ट्यूशन शुल्क प्रतिपूर्ति और ₹13,500 वार्षिक भत्ता।",
                "kn": "ಎಸ್‌ಸಿ ಪೋಸ್ಟ್-ಮೆಟ್ರಿಕ್ ವಿದ್ಯಾರ್ಥಿವೇತನ — ಶುಲ್ಕ ಮರುಪಾವತಿ.",
                "ta": "பட்டியலின மாணவர் மேனிலை கல்வி உதவித்தொகை.",
            },
            ["post matric scholarship", "sc scholarship", "nsp", "స్కాలర్‌షిప్", "छात्रवृत्ति", "ವಿದ್ಯಾರ್ಥಿವೇತನ", "உதவித்தொகை"],
            mutually_exclusive_with=["IN_NSP_OBC_SCHOLARSHIP"],
            complementary_to=["IN_PMJAY"],
        ),
        _make_scheme(
            "IN_NSP_OBC_SCHOLARSHIP",
            "PM-YASASVI Post-Matric Scholarship for OBC/EBC/DNT",
            "Ministry of Social Justice & Empowerment",
            "All India",
            "Education & Scholarship",
            "Academic allowance up to Rs 20,000/year for OBC/EBC students in post-matric and professional courses.",
            15000,
            "All India; Category OBC or EWS; Occupation Student; age 15 to 28; annual family income <= Rs 2,50,000.",
            [
                {"field": "category", "op": "in", "value": ["OBC", "EWS"], "label": "OBC / EWS category"},
                {"field": "occupation", "op": "in", "value": ["Student"], "label": "Enrolled Student"},
                {"field": "age", "op": ">=", "value": 15, "label": "Age >= 15 years"},
                {"field": "age", "op": "<=", "value": 28, "label": "Age <= 28 years"},
                {"field": "income", "op": "<=", "value": 250000, "label": "Family income <= Rs 2,50,000"},
            ],
            ["OBC/EWS Certificate", "Income Certificate", "Previous Year Marksheet", "Aadhaar Card", "Bank Account Passbook (Aadhaar-seeded)"],
            "https://scholarships.gov.in",
            "https://myscheme.gov.in/schemes/pm-yasasvi",
            {
                "te": "పీఎం-యశస్వి ఓబీసీ స్కాలర్‌షిప్ — విద్యార్థులకు సంవత్సరానికి రూ. 20,000 వరకు సహాయం.",
                "hi": "पीएम-यशस्वी ओबीसी छात्रवृत्ति — छात्रों को ₹20,000 प्रति वर्ष तक सहायता।",
                "kn": "ಪಿಎಂ-ಯಶಸ್ವಿ ಒಬಿಸಿ ವಿದ್ಯಾರ್ಥಿವೇತನ.",
                "ta": "பிஎம்-யசஸ்வி பிற்படுத்தப்பட்டோர் கல்வி உதவித்தொகை.",
            },
            ["pm yasasvi", "obc scholarship", "nsp scholarship", "ओबीसी छात्रवृत्ति"],
            mutually_exclusive_with=["IN_NSP_POST_MATRIC_SC"],
        ),
        _make_scheme(
            "IN_IGNOAPS",
            "Indira Gandhi National Old Age Pension (NSAP)",
            "Ministry of Rural Development",
            "All India",
            "Social Security",
            "Monthly central pension Rs 200-500/month + state top-up (avg Rs 12,000/year) for BPL seniors aged 60+.",
            12000,
            "All India; Age >= 60; BPL household; annual income <= Rs 1,00,000.",
            [
                {"field": "age", "op": ">=", "value": 60, "label": "Senior citizen age >= 60"},
                {"field": "bpl", "op": "==", "value": True, "label": "BPL household"},
                {"field": "income", "op": "<=", "value": 100000, "label": "Annual income <= Rs 1,00,000"},
            ],
            ["Aadhaar Card", "Age Proof Certificate", "BPL / Ration Card", "Bank Account Passbook (Aadhaar-seeded)"],
            "https://nsap.nic.in",
            "https://myscheme.gov.in/schemes/ignoaps",
            {
                "te": "ఇందిరా గాంధీ జాతీయ వృద్ధాప్య పింఛను — 60 ఏళ్లు పైబడిన బీపీఎల్ వృద్ధులకు నెలవారీ పింఛను.",
                "hi": "इंदिरा गांधी राष्ट्रीय वृद्धावस्था पेंशन — 60+ बीपीएल वरिष्ठ नागरिकों को मासिक पेंशन।",
                "kn": "ಇಂದಿರಾ ಗಾಂಧಿ ರಾಷ್ಟ್ರೀಯ ವೃದ್ಧಾಪ್ಯ ಪಿಂಚಣಿ.",
                "ta": "இந்திரா காந்தி தேசிய முதியோர் ஓய்வூதியத் திட்டம்.",
            },
            ["old age pension", "ignoaps", "nsap", "वृद्धावस्था पेंशन", "వృద్ధాప్య పింఛను", "முதியோர் ஓய்வூதியம்"],
            mutually_exclusive_with=["TS_AASARA_PENSION", "IN_IGNDPS"],
        ),
        _make_scheme(
            "IN_IGNDPS",
            "Indira Gandhi National Disability Pension Scheme",
            "Ministry of Rural Development",
            "All India",
            "Disability Support",
            "Monthly disability pension + assistive aid support (avg Rs 18,000/year with state matching).",
            18000,
            "All India; Person with benchmark disability (>=80% severe); age 18 to 79; BPL household; annual income <= Rs 1,50,000.",
            [
                {"field": "disability", "op": "==", "value": True, "label": "Benchmark disability certified"},
                {"field": "age", "op": ">=", "value": 18, "label": "Age >= 18 years"},
                {"field": "age", "op": "<=", "value": 79, "label": "Age <= 79 years"},
                {"field": "bpl", "op": "==", "value": True, "label": "BPL household"},
                {"field": "income", "op": "<=", "value": 150000, "label": "Annual income <= Rs 1,50,000"},
            ],
            ["UDID / Disability Certificate", "Aadhaar Card", "BPL / Ration Card", "Bank Account Passbook (Aadhaar-seeded)"],
            "https://nsap.nic.in",
            "https://myscheme.gov.in/schemes/igndps",
            {
                "te": "జాతీయ దివ్యాంగుల పింఛను పథకం — దివ్యాంగులకు నెలవారీ ఆర్థిక సహాయం.",
                "hi": "राष्ट्रीय दिव्यांग पेंशन योजना — दिव्यांगजनों को मासिक पेंशन।",
                "kn": "ರಾಷ್ಟ್ರೀಯ ಅಂಗವಿಕಲರ ಪಿಂಚಣಿ ಯೋಜನೆ.",
                "ta": "தேசிய மாற்றுத்திறனாளிகள் ஓய்வூதியத் திட்டம்.",
            },
            ["disability pension", "divyang", "udid", "దివ్యాంగుల పింఛను", "दिव्यांग पेंशन", "மாற்றுத்திறனாளி"],
            mutually_exclusive_with=["IN_IGNOAPS"],
            complementary_to=["IN_ADIP_AIDS"],
        ),
        _make_scheme(
            "IN_ADIP_AIDS",
            "ADIP Scheme for Assistive Devices (Divyangjan)",
            "Ministry of Social Justice & Empowerment",
            "All India",
            "Disability Support",
            "Free motorized tricycle, hearing aids, or prosthetics up to Rs 25,000 (annualized Rs 12,500).",
            12500,
            "All India; Person with benchmark disability (>=40%); annual family income <= Rs 2,70,000.",
            [
                {"field": "disability", "op": "==", "value": True, "label": "Benchmark disability (>=40%)"},
                {"field": "income", "op": "<=", "value": 270000, "label": "Annual income <= Rs 2,70,000"},
            ],
            ["UDID / Disability Certificate", "Income Certificate", "Aadhaar Card"],
            "https://disabilityaffairs.gov.in",
            "https://myscheme.gov.in/schemes/adip",
            {
                "te": "ADIP పథకం — దివ్యాంగులకు ఉచిత సహాయక పరికరాలు.",
                "hi": "एडिप योजना — दिव्यांगजनों को निःशुल्क सहायक उपकरण।",
                "kn": "ಎಡಿಐಪಿ — ಅಂಗವಿಕಲರಿಗೆ ಉಚಿತ ಸಾಧನಗಳು.",
                "ta": "மாற்றுத்திறனாளிகளுக்கான இலவச உதவி உபகரணத் திட்டம்.",
            },
            ["adip", "wheelchair", "tricycle", "assistive device", "divyang"],
            complementary_to=["IN_IGNDPS"],
        ),
        _make_scheme(
            "IN_PM_MATRU_VANDANA",
            "Pradhan Mantri Matru Vandana Yojana (PMMVY 2.0)",
            "Ministry of Women & Child Development",
            "All India",
            "Women & Social Welfare",
            "Rs 5,000 maternity cash incentive for first child and Rs 6,000 for second girl child.",
            6000,
            "All India; Female; age 19 to 45; annual family income <= Rs 8,00,000.",
            [
                {"field": "gender", "op": "==", "value": "Female", "label": "Pregnant/lactating woman"},
                {"field": "age", "op": ">=", "value": 19, "label": "Age >= 19 years"},
                {"field": "age", "op": "<=", "value": 45, "label": "Age <= 45 years"},
                {"field": "income", "op": "<=", "value": 800000, "label": "Annual income <= Rs 8,00,000"},
            ],
            ["Aadhaar Card", "MCP Card (Anganwadi)", "Bank Account Passbook (Aadhaar-seeded)"],
            "https://pmmvy.wcd.gov.in",
            "https://myscheme.gov.in/schemes/pmmvy",
            {
                "te": "ప్రధాన మంత్రి మాతృ వందన యోజన — గర్భిణీ మహిళలకు రూ. 5,000–6,000 సహాయం.",
                "hi": "प्रधानमंत्री मातृ वंदना योजना — गर्भवती महिलाओं को ₹5,000–₹6,000 मातृत्व लाभ।",
                "kn": "ಪ್ರಧಾನ ಮಂತ್ರಿ ಮಾತೃ ವಂದನಾ ಯೋಜನೆ.",
                "ta": "பிரதமர் மாத்ரு வந்தனா மகப்பேறு உதவித்தொகை.",
            },
            ["pmmvy", "matru vandana", "maternity", "మాతృ వందన", "मातृ वंदना"],
            complementary_to=["IN_PMJAY", "IN_UJJWALA"],
        ),
        _make_scheme(
            "IN_MUDRA_SHISHU",
            "PM Mudra Yojana (Shishu/Kishor Micro-Enterprise Loan)",
            "Ministry of Finance (DFS)",
            "All India",
            "Employment & Skill",
            "Collateral-free micro-business loan up to Rs 5,00,000 with credit guarantee (annual credit benefit ~Rs 18,000).",
            18000,
            "All India; Age 18 to 65; Occupation Self-Employed / Artisan / Unemployed; annual income <= Rs 6,00,000.",
            [
                {"field": "age", "op": ">=", "value": 18, "label": "Age >= 18 years"},
                {"field": "age", "op": "<=", "value": 65, "label": "Age <= 65 years"},
                {"field": "occupation", "op": "in", "value": ["Self-Employed", "Artisan", "Unemployed"], "label": "Non-farm micro-enterprise"},
                {"field": "income", "op": "<=", "value": 600000, "label": "Annual income <= Rs 6,00,000"},
            ],
            ["Aadhaar Card", "PAN Card", "Business Address / Udyam Registration", "Bank Account Passbook (Aadhaar-seeded)"],
            "https://www.udyamimitra.in",
            "https://myscheme.gov.in/schemes/pmmy",
            {
                "te": "పీఎం ముద్ర లోన్ — చిన్న వ్యాపారులకు హామీ లేకుండా రూ. 5 లక్షల వరకు రుణం.",
                "hi": "पीएम मुद्रा योजना — सूक्ष्म व्यवसाय हेतु बिना गारंटी ₹5 लाख तक ऋण।",
                "kn": "ಪಿಎಂ ಮುದ್ರಾ ಯೋಜನೆ — ಸಣ್ಣ ಉದ್ಯಮ ಸಾಲ.",
                "ta": "பிரதமர் முத்ரா கடன் திட்டம் — சிறு தொழில் கடன்.",
            },
            ["mudra", "pmmy", "business loan", "ముద్ర రుణం", "मुद्रा लोन"],
            complementary_to=["IN_PM_VISHWAKARMA"],
        ),
        _make_scheme(
            "IN_PM_SVANIDHI",
            "PM SVANidhi Street Vendor Micro-Credit",
            "Ministry of Housing & Urban Affairs",
            "All India",
            "Employment & Skill",
            "Working capital loan Rs 10k-50k + 7% interest subsidy + Rs 1,200/yr digital cashback.",
            10000,
            "All India; Urban residence; Occupation Self-Employed / Artisan; age >= 18; annual income <= Rs 2,50,000.",
            [
                {"field": "residence", "op": "==", "value": "Urban", "label": "Urban street vendor"},
                {"field": "occupation", "op": "in", "value": ["Self-Employed", "Artisan"], "label": "Vendor / Self-Employed"},
                {"field": "age", "op": ">=", "value": 18, "label": "Age >= 18 years"},
                {"field": "income", "op": "<=", "value": 250000, "label": "Annual income <= Rs 2,50,000"},
            ],
            ["Aadhaar Card", "Certificate of Vending / ULB Letter", "Bank Account Passbook (Aadhaar-seeded)"],
            "https://pmsvanidhi.mohua.gov.in",
            "https://myscheme.gov.in/schemes/pm-svanidhi",
            {
                "te": "పీఎం స్వనిధి — వీధి వ్యాపారులకు 7% వడ్డీ సబ్సిడీతో వర్కింగ్ క్యాపిటల్ రుణం.",
                "hi": "पीएम स्वनिधि — रेहड़ी-पटरी विक्रेताओं के लिए 7% ब्याज सब्सिडी ऋण।",
                "kn": "ಪಿಎಂ ಸ್ವನಿಧಿ — ಬೀದಿ ಬದಿ ವ್ಯಾಪಾರಿಗಳಿಗೆ ಸಾಲ.",
                "ta": "பிஎம் ஸ்வநிதி — தெருவோர வியாபாரிகள் கடன் திட்டம்.",
            },
            ["svanidhi", "street vendor", "स्वनिधि", "వీధి వ్యాపారులు"],
            complementary_to=["IN_PMAY_URBAN"],
        ),

        # --- ANDHRA PRADESH FLAGSHIP SCHEMES ---
        _make_scheme(
            "AP_ANNADATA_SUKHIBHAVA",
            "Andhra Pradesh Annadata Sukhibhava",
            "Department of Agriculture, Govt of Andhra Pradesh",
            "Andhra Pradesh",
            "Agriculture",
            "Rs 20,000 per year investment assistance to AP farmer families (inclusive of PM-KISAN top-up; state share Rs 14,000).",
            14000,
            "Resident of Andhra Pradesh; Occupation Farmer; cultivable land >= 0.2 acres; age >= 18; annual income <= Rs 4,00,000.",
            [
                {"field": "state", "op": "==", "value": "Andhra Pradesh", "label": "Resident of Andhra Pradesh"},
                {"field": "occupation", "op": "in", "value": ["Farmer"], "label": "Farmer occupation"},
                {"field": "land", "op": ">=", "value": 0.2, "label": "Cultivable land >= 0.2 acres"},
                {"field": "age", "op": ">=", "value": 18, "label": "Age >= 18 years"},
                {"field": "income", "op": "<=", "value": 400000, "label": "Annual income <= Rs 4,00,000"},
            ],
            ["AP Webland / Pattadar Passbook", "Aadhaar Card", "AP Rice Card", "Bank Account Passbook (Aadhaar-seeded)"],
            "https://annadatasukhibhava.ap.gov.in",
            "https://ap.gov.in",
            {
                "te": "అన్నదాత సుఖీభవ — ఆంధ్రప్రదేశ్ రైతులకు సంవత్సరానికి రూ. 20,000 పంట పెట్టుబడి సహాయం.",
                "hi": "अन्नदाता सुखीभव — आंध्र प्रदेश किसानों को ₹20,000 वार्षिक निवेश सहायता।",
                "kn": "ಅನ್ನದಾತ ಸುಖೀಭವ — ಆಂಧ್ರಪ್ರದೇಶ ರೈತರ ನೆರವು.",
                "ta": "அன்னதாதா சுகிபவா — ஆந்திர விவசாயிகள் உதவித்தொகை.",
            },
            ["annadata sukhibhava", "ysr rythu bharosa", "అన్నదాత సుఖీభవ", "andhra farmer"],
            complementary_to=["IN_PM_KISAN", "IN_PMFBY"],
        ),
        _make_scheme(
            "AP_TALLIKI_VANDANAM",
            "Andhra Pradesh Talliki Vandanam",
            "School Education Dept, Govt of Andhra Pradesh",
            "Andhra Pradesh",
            "Education & Scholarship",
            "Rs 15,000 per year per school-going child deposited to mother's bank account.",
            15000,
            "Resident of Andhra Pradesh; Female mother/guardian; BPL / Rice Card holder; annual income <= Rs 2,50,000.",
            [
                {"field": "state", "op": "==", "value": "Andhra Pradesh", "label": "Resident of Andhra Pradesh"},
                {"field": "gender", "op": "==", "value": "Female", "label": "Mother/Female guardian"},
                {"field": "bpl", "op": "==", "value": True, "label": "AP White Rice Card / BPL"},
                {"field": "income", "op": "<=", "value": 250000, "label": "Annual income <= Rs 2,50,000"},
            ],
            ["AP Rice Card", "Mother Aadhaar Card", "Child School Enrollment (75% Attendance)", "Bank Account Passbook (Aadhaar-seeded)"],
            "https://gramawardsachivalayam.ap.gov.in",
            "https://ap.gov.in",
            {
                "te": "తల్లికి వందనం — పాఠశాలకు వెళ్లే ప్రతి బిడ్డకు తల్లి ఖాతాలో రూ. 15,000.",
                "hi": "तल्लिकी वंदनम — आंध्र प्रदेश में प्रति छात्र ₹15,000 वार्षिक सहायता।",
                "kn": "ತಲ್ಲಿಕಿ ವಂದನಂ — ಶಾಲಾ ಮಕ್ಕಳಿಗೆ ವಾರ್ಷಿಕ ರೂ. 15,000.",
                "ta": "தல்லிகி வந்தனம் — பள்ளி மாணவர் கல்வி உதவித்தொகை.",
            },
            ["talliki vandanam", "amma vodi", "తల్లికి వందనం", "andhra education"],
            complementary_to=["AP_ANNADATA_SUKHIBHAVA"],
        ),

        # --- KARNATAKA FLAGSHIP SCHEMES ---
        _make_scheme(
            "KA_GRUHA_LAKSHMI",
            "Karnataka Gruha Lakshmi Guarantee Scheme",
            "Dept of Women & Child Development, Karnataka",
            "Karnataka",
            "Women & Social Welfare",
            "Rs 2,000/month (Rs 24,000/year) direct benefit transfer to women heads of BPL/APL non-taxpayer families.",
            24000,
            "Resident of Karnataka; Female head of household; age >= 18; annual family income <= Rs 2,00,000; BPL/Antyodaya card.",
            [
                {"field": "state", "op": "==", "value": "Karnataka", "label": "Resident of Karnataka"},
                {"field": "gender", "op": "==", "value": "Female", "label": "Female head of family"},
                {"field": "age", "op": ">=", "value": 18, "label": "Age >= 18 years"},
                {"field": "income", "op": "<=", "value": 200000, "label": "Annual income <= Rs 2,00,000"},
                {"field": "bpl", "op": "==", "value": True, "label": "BPL / Antyodaya Ration Card"},
            ],
            ["Karnataka BPL/APL Ration Card", "Aadhaar Card", "Bank Account Passbook (Aadhaar-seeded)"],
            "https://sevasindhugs.karnataka.gov.in",
            "https://sevasindhu.karnataka.gov.in",
            {
                "te": "కర్ణాటక గృహ లక్ష్మి — మహిళా కుటుంబ పెద్దలకు నెలకు రూ. 2,000.",
                "hi": "कर्नाटक गृह लक्ष्मी — महिला मुखिया को ₹2,000/माह सीधे खाते में।",
                "kn": "ಗೃಹ ಲಕ್ಷ್ಮಿ ಯೋಜನೆ — ಕುಟುಂಬದ ಯಜಮಾನಿಗೆ ಪ್ರತಿ ತಿಂಗಳು ರೂ. 2,000 ನೇರ ನಗದು ವರ್ಗಾವಣೆ.",
                "ta": "கர்நாடகா கிரஹ லட்சுமி — குடும்பத் தலைவிகளுக்கு மாதம் ரூ.2,000.",
            },
            ["gruha lakshmi", "ಗೃಹ ಲಕ್ಷ್ಮಿ", "karnataka women 2000", "seva sindhu"],
            complementary_to=["KA_GRUHA_JYOTHI", "KA_SHAKTI", "IN_PM_KISAN"],
        ),
        _make_scheme(
            "KA_GRUHA_JYOTHI",
            "Karnataka Gruha Jyothi Free Electricity",
            "Energy Department, Govt of Karnataka",
            "Karnataka",
            "Housing & Utilities",
            "Up to 200 units free domestic electricity per month (annual savings ~Rs 14,400).",
            14400,
            "Resident of Karnataka; age >= 18; domestic electricity consumer; annual income <= Rs 5,00,000.",
            [
                {"field": "state", "op": "==", "value": "Karnataka", "label": "Resident of Karnataka"},
                {"field": "age", "op": ">=", "value": 18, "label": "Age >= 18 years"},
                {"field": "income", "op": "<=", "value": 500000, "label": "Annual income <= Rs 5,00,000"},
            ],
            ["Aadhaar Card", "ESCOM Electricity Account ID", "Karnataka Residence Proof"],
            "https://sevasindhugs.karnataka.gov.in",
            "https://sevasindhu.karnataka.gov.in",
            {
                "te": "కర్ణాటక గృహ జ్యోతి — 200 యూనిట్ల ఉచిత విద్యుత్.",
                "hi": "कर्नाटक गृह ज्योति — 200 यूनिट निःशुल्क घरेलू बिजली।",
                "kn": "ಗೃಹ ಜ್ಯೋತಿ ಯೋಜನೆ — ಪ್ರತಿ ತಿಂಗಳು 200 ಯೂನಿಟ್ ವರೆಗೆ ಉಚಿತ ವಿದ್ಯುತ್.",
                "ta": "கர்நாடகா கிரஹ ஜோதி — 200 யூனிட் இலவச மின்சாரம்.",
            },
            ["karnataka gruha jyothi", "ಗೃಹ ಜ್ಯೋತಿ", "200 units karnataka"],
            complementary_to=["KA_GRUHA_LAKSHMI", "KA_SHAKTI"],
        ),
        _make_scheme(
            "KA_SHAKTI",
            "Karnataka Shakti Free Bus Travel for Women",
            "Transport Department, Govt of Karnataka",
            "Karnataka",
            "Women & Social Welfare",
            "Zero-ticket travel in KSRTC/BMTC/NWKRTC/KKRTC non-luxury buses across Karnataka (~Rs 12,000/yr savings).",
            12000,
            "Resident of Karnataka; Female; age >= 6.",
            [
                {"field": "state", "op": "==", "value": "Karnataka", "label": "Resident of Karnataka"},
                {"field": "gender", "op": "==", "value": "Female", "label": "Female resident"},
                {"field": "age", "op": ">=", "value": 6, "label": "Age >= 6 years"},
            ],
            ["Aadhaar Card / Karnataka Domicile ID"],
            "https://sevasindhu.karnataka.gov.in",
            "https://sevasindhu.karnataka.gov.in",
            {
                "te": "కర్ణాటక శక్తి పథకం — మహిళలకు ఉచిత బస్సు ప్రయాణం.",
                "hi": "कर्नाटक शक्ति योजना — महिलाओं के लिए निःशुल्क बस यात्रा।",
                "kn": "ಶಕ್ತಿ ಯೋಜನೆ — ಕರ್ನಾಟಕದ ಮಹಿಳೆಯರಿಗೆ ಸರ್ಕಾರಿ ಬಸ್‌ಗಳಲ್ಲಿ ಉಚಿತ ಪ್ರಯಾಣ.",
                "ta": "கர்நாடகா சக்தி திட்டம் — பெண்களுக்கு இலவச பேருந்து பயணம்.",
            },
            ["shakti karnataka", "ಶಕ್ತಿ ಯೋಜನೆ", "free bus karnataka"],
            complementary_to=["KA_GRUHA_LAKSHMI", "KA_GRUHA_JYOTHI"],
        ),
        _make_scheme(
            "KA_YUVA_NIDHI",
            "Karnataka Yuva Nidhi Unemployment Assistance",
            "Skill Development Dept, Govt of Karnataka",
            "Karnataka",
            "Employment & Skill",
            "Rs 3,000/month for unemployed graduates (Rs 36,000/yr) and Rs 1,500/month for diploma holders for 2 years.",
            36000,
            "Resident of Karnataka; Occupation Unemployed; age 20 to 30; annual income <= Rs 3,00,000.",
            [
                {"field": "state", "op": "==", "value": "Karnataka", "label": "Resident of Karnataka"},
                {"field": "occupation", "op": "in", "value": ["Unemployed"], "label": "Unemployed recent graduate"},
                {"field": "age", "op": ">=", "value": 20, "label": "Age >= 20 years"},
                {"field": "age", "op": "<=", "value": 30, "label": "Age <= 30 years"},
                {"field": "income", "op": "<=", "value": 300000, "label": "Annual income <= Rs 3,00,000"},
            ],
            ["Aadhaar Card", "Degree/Diploma Certificate", "Karnataka Domicile Proof", "Bank Account Passbook (Aadhaar-seeded)"],
            "https://sevasindhugs.karnataka.gov.in",
            "https://sevasindhu.karnataka.gov.in",
            {
                "te": "కర్ణాటక యువ నిధి — నిరుద్యోగ గ్రాడ్యుయేట్లకు నెలకు రూ. 3,000.",
                "hi": "कर्नाटक युवा निधि — बेरोजगार स्नातकों को ₹3,000/माह भत्ता।",
                "kn": "ಯುವ ನಿಧಿ ಯೋಜನೆ — ನಿರುದ್ಯೋಗಿ ಪದವೀಧರರಿಗೆ ಮಾಸಿಕ ರೂ. 3,000 ಭತ್ಯೆ.",
                "ta": "கர்நாடகா யுவ நிதி — வேலையில்லா பட்டதாரிகளுக்கு மாதம் ரூ.3,000.",
            },
            ["yuva nidhi", "ಯುವ ನಿಧಿ", "unemployment karnataka"],
            complementary_to=["KA_GRUHA_JYOTHI"],
        ),

        # --- TAMIL NADU FLAGSHIP SCHEMES ---
        _make_scheme(
            "TN_KALAIGNAR_MAGALIR",
            "Kalaignar Magalir Urimai Thogai (Tamil Nadu)",
            "Special Programme Implementation Dept, Tamil Nadu",
            "Tamil Nadu",
            "Women & Social Welfare",
            "Rs 1,000/month (Rs 12,000/year) basic rights grant deposited to women heads of eligible families.",
            12000,
            "Resident of Tamil Nadu; Female; age >= 21; annual family income <= Rs 2,50,000; land <= 5 acres.",
            [
                {"field": "state", "op": "==", "value": "Tamil Nadu", "label": "Resident of Tamil Nadu"},
                {"field": "gender", "op": "==", "value": "Female", "label": "Female head of household"},
                {"field": "age", "op": ">=", "value": 21, "label": "Age >= 21 years"},
                {"field": "income", "op": "<=", "value": 250000, "label": "Annual income <= Rs 2,50,000"},
                {"field": "land", "op": "<=", "value": 5.0, "label": "Wetland/dryland <= 5 acres"},
            ],
            ["Tamil Nadu Smart Family Card", "Aadhaar Card", "Bank Account Passbook (Aadhaar-seeded)"],
            "https://kmut.tn.gov.in",
            "https://www.tn.gov.in",
            {
                "te": "కళైஞర్ మగళిర్ ఉరిమై తొగై — తమిళనాడు మహిళలకు నెలకు రూ. 1,000.",
                "hi": "कलैगनार मगलिर उरिमई थोगई — तमिलनाडु की महिलाओं को ₹1,000/माह।",
                "kn": "ಕಲೈஞರ್ ಮಗಳಿರ್ ಉರಿಮೈ ತೊಗೈ — ಮಹಿಳೆಯರಿಗೆ ರೂ. 1,000.",
                "ta": "கலைஞர் மகளிர் உரிமைத் தொகை — குடும்பத் தலைவிகளுக்கு மாதம் ரூ.1,000 நேரடி உதவி.",
            },
            ["magalir urimai", "கலைஞர் மகளிர் உரிமை", "tamil nadu 1000 women", "kmut"],
            complementary_to=["TN_PUDHUMAI_PENN", "IN_PM_KISAN"],
        ),
        _make_scheme(
            "TN_PUDHUMAI_PENN",
            "Moovalur Ramamirtham Pudhumai Penn Scheme",
            "Social Welfare & Women Empowerment Dept, TN",
            "Tamil Nadu",
            "Education & Scholarship",
            "Rs 1,000/month (Rs 12,000/year) scholarship to girl students pursuing higher education after govt school.",
            12000,
            "Resident of Tamil Nadu; Female; Occupation Student; age 17 to 25; annual income <= Rs 3,00,000.",
            [
                {"field": "state", "op": "==", "value": "Tamil Nadu", "label": "Resident of Tamil Nadu"},
                {"field": "gender", "op": "==", "value": "Female", "label": "Female student"},
                {"field": "occupation", "op": "in", "value": ["Student"], "label": "Higher education student"},
                {"field": "age", "op": ">=", "value": 17, "label": "Age >= 17 years"},
                {"field": "age", "op": "<=", "value": 25, "label": "Age <= 25 years"},
                {"field": "income", "op": "<=", "value": 300000, "label": "Annual income <= Rs 3,00,000"},
            ],
            ["Aadhaar Card", "EMIS Govt School Study Certificate", "College Bonafide Certificate", "Bank Account Passbook (Aadhaar-seeded)"],
            "https://www.pudhumaipenn.tn.gov.in",
            "https://www.tn.gov.in",
            {
                "te": "పుదుమై పెన్ — తమిళనాడు కళాశాల విద్యార్థినులకు నెలకు రూ. 1,000.",
                "hi": "पुदुमई पेन — तमिलनाडु की कॉलेज छात्राओं को ₹1,000/माह।",
                "kn": "ಪುದುಮೈ ಪೆನ್ — ಕಾಲೇಜು ವಿದ್ಯಾರ್ಥಿನಿಯರಿಗೆ ಮಾಸಿಕ ರೂ. 1,000.",
                "ta": "புதுமைப் பெண் திட்டம் — அரசுப் பள்ளி கல்லூரி மாணவிகளுக்கு மாதம் ரூ.1,000 உதவித்தொகை.",
            },
            ["pudhumai penn", "புதுமைப் பெண்", "tamil nadu girl scholarship"],
            complementary_to=["TN_KALAIGNAR_MAGALIR"],
        ),
    ]


def build_extended_schemes() -> List[Dict[str, Any]]:
    """Generate 75 additional grounded Indian Central & State welfare schemes (total = 110)."""
    templates = [
        # Central Agriculture & Allied
        ("IN_SOIL_HEALTH", "Soil Health Card & Micronutrient Subsidy", "Ministry of Agriculture", "All India", "Agriculture", 3500, ["Farmer"], 0.1, None, 18, 80, 500000, None, None, False, None, "https://soilhealth.dac.gov.in"),
        ("IN_PM_SYMY", "PM Kisan Maandhan Yojana (Farmer Pension)", "Ministry of Agriculture", "All India", "Agriculture", 36000, ["Farmer"], 0.1, 5.0, 18, 40, 300000, None, None, False, None, "https://maandhan.in"),
        ("IN_PKVY_ORGANIC", "Paramparagat Krishi Vikas Yojana (Organic Farming)", "Ministry of Agriculture", "All India", "Agriculture", 16000, ["Farmer"], 0.5, None, 18, 75, 500000, None, None, False, "Rural", "https://pgsindia-ncof.gov.in"),
        ("IN_PMKSY_DRIP", "PM Krishi Sinchayee Yojana (Micro-Irrigation Drip)", "Ministry of Agriculture", "All India", "Agriculture", 22000, ["Farmer"], 0.5, None, 18, 75, 500000, None, None, False, "Rural", "https://pmksy.gov.in"),
        ("IN_E_NAM", "e-NAM National Agriculture Market Logistics Grant", "Ministry of Agriculture", "All India", "Agriculture", 5000, ["Farmer"], 0.2, None, 18, 80, 600000, None, None, False, None, "https://enam.gov.in"),
        ("IN_DAIRY_EDEG", "National Livestock Mission Dairy Entrepreneurship", "Ministry of Fisheries & Animal Husbandry", "All India", "Agriculture", 25000, ["Farmer", "Self-Employed"], 0.0, None, 18, 65, 400000, None, None, False, "Rural", "https://nlm.udyamimitra.in"),
        ("IN_PMMSY_FISH", "Pradhan Mantri Matsya Sampada Yojana", "Ministry of Fisheries & Animal Husbandry", "All India", "Agriculture", 30000, ["Farmer", "Self-Employed"], 0.0, None, 18, 65, 400000, None, None, False, None, "https://pmmsy.dof.gov.in"),
        ("IN_BEEKEEPING_NBHM", "National Beekeeping & Honey Mission Grant", "Ministry of Agriculture", "All India", "Agriculture", 14000, ["Farmer", "Self-Employed"], 0.0, None, 18, 65, 350000, None, None, False, "Rural", "https://nbb.gov.in"),
        # Central Insurance & Social Security
        ("IN_PMJJBY", "Pradhan Mantri Jeevan Jyoti Bima Yojana", "Ministry of Finance", "All India", "Insurance", 4000, None, None, None, 18, 50, 800000, None, None, False, None, "https://jansuraksha.gov.in"),
        ("IN_PMSBY", "Pradhan Mantri Suraksha Bima Yojana (Accident Cover)", "Ministry of Finance", "All India", "Insurance", 2500, None, None, None, 18, 70, 800000, None, None, False, None, "https://jansuraksha.gov.in"),
        ("IN_APY", "Atal Pension Yojana (Guaranteed Pension)", "Ministry of Finance (PFRDA)", "All India", "Social Security", 12000, None, None, None, 18, 40, 500000, None, None, False, None, "https://npscra.nsdl.co.in"),
        ("IN_PM_SYM_LABOR", "PM Shram Yogi Maandhan (Unorganised Workers)", "Ministry of Labour & Employment", "All India", "Social Security", 36000, ["Agricultural Laborer", "Artisan", "Self-Employed"], None, None, 18, 40, 180000, None, None, False, None, "https://maandhan.in"),
        ("IN_IGNWPS", "Indira Gandhi National Widow Pension Scheme", "Ministry of Rural Development", "All India", "Social Security", 14400, None, None, None, 40, 79, 120000, None, "Female", True, None, "https://nsap.nic.in"),
        ("IN_ESHRAM_INS", "e-Shram Unorganised Worker Accident Benefit", "Ministry of Labour & Employment", "All India", "Insurance", 3000, ["Agricultural Laborer", "Artisan", "Self-Employed"], None, None, 16, 59, 250000, None, None, False, None, "https://eshram.gov.in"),
        # Central Women, Child & Education
        ("IN_SUKANYA", "Sukanya Samriddhi Yojana (Girl Child Savings Bonus)", "Ministry of Finance", "All India", "Women & Social Welfare", 9500, None, None, None, 0, 10, 1000000, None, "Female", False, None, "https://www.nsiindia.gov.in"),
        ("IN_MAHILA_SAMMAN", "Mahila Samman Savings Certificate Bonus", "Ministry of Finance", "All India", "Women & Social Welfare", 15000, None, None, None, 18, 80, 1000000, None, "Female", False, None, "https://www.indiapost.gov.in"),
        ("IN_LAKHPATI_DIDI", "Lakhpati Didi SHG Women Enterprise Support", "Ministry of Rural Development", "All India", "Women & Social Welfare", 24000, ["Self-Employed", "Farmer", "Artisan"], None, None, 18, 60, 250000, None, "Female", False, "Rural", "https://aajeevika.gov.in"),
        ("IN_NSP_ST_POST", "Post-Matric Scholarship for ST Students", "Ministry of Tribal Affairs", "All India", "Education & Scholarship", 18000, ["Student"], None, None, 15, 30, 250000, ["ST"], None, False, None, "https://scholarships.gov.in"),
        ("IN_NSP_MINORITY", "Merit-cum-Means Scholarship for Minority Students", "Ministry of Minority Affairs", "All India", "Education & Scholarship", 20000, ["Student"], None, None, 16, 30, 250000, ["Minority"], None, False, None, "https://scholarships.gov.in"),
        ("IN_PRAGATI_AICTE", "AICTE Pragati Scholarship for Girl Technical Students", "Ministry of Education", "All India", "Education & Scholarship", 50000, ["Student"], None, None, 17, 26, 800000, None, "Female", False, None, "https://scholarships.gov.in"),
        ("IN_SAKSHAM_AICTE", "AICTE Saksham Scholarship for Divyang Students", "Ministry of Education", "All India", "Disability Support", 50000, ["Student"], None, None, 17, 28, 800000, None, None, False, None, "https://scholarships.gov.in"),
        ("IN_NMMS_MERIT", "National Means-cum-Merit Scholarship (Class 9-12)", "Ministry of Education", "All India", "Education & Scholarship", 12000, ["Student"], None, None, 13, 18, 350000, None, None, False, None, "https://scholarships.gov.in"),
        ("IN_PMKVY_4", "Pradhan Mantri Kaushal Vikas Yojana 4.0 Stipend", "Ministry of Skill Development", "All India", "Employment & Skill", 12000, ["Unemployed", "Student"], None, None, 15, 45, 400000, None, None, False, None, "https://www.skillindiadigital.gov.in"),
        ("IN_NAPS_APPRENTICE", "National Apprenticeship Promotion Scheme Stipend", "Ministry of Skill Development", "All India", "Employment & Skill", 18000, ["Unemployed", "Student"], None, None, 18, 32, 500000, None, None, False, None, "https://www.apprenticeshipindia.gov.in"),
        ("IN_PMEGP_MICRO", "Prime Minister Employment Generation Programme (PMEGP)", "Ministry of MSME (KVIC)", "All India", "Employment & Skill", 40000, ["Self-Employed", "Unemployed", "Artisan"], None, None, 18, 55, 600000, None, None, False, None, "https://www.kviconline.gov.in/pmegpeportal"),
        ("IN_PM_SURYA_GHAR", "PM Surya Ghar Muft Bijli Rooftop Solar Subsidy", "Ministry of New & Renewable Energy", "All India", "Housing & Utilities", 18000, None, None, None, 18, 80, 1000000, None, None, False, None, "https://pmsuryaghar.gov.in"),
        ("IN_SBM_TOILET", "Swachh Bharat Mission Gramin IHHL Toilet Grant", "Ministry of Jal Shakti", "All India", "Housing & Utilities", 12000, None, None, None, 18, 80, 200000, None, None, True, "Rural", "https://swachhbharatmission.ddws.gov.in"),
        ("IN_PM_JAN_AUSHADHI", "PM Bhartiya Janaushadhi Generic Medicine Savings", "Ministry of Chemicals & Fertilizers", "All India", "Health", 6000, None, None, None, 0, 99, 1000000, None, None, False, None, "https://janaushadhi.gov.in"),
        ("IN_NIKSHAY_POSHAN", "Ni-kshay Poshan Yojana Nutritional Support", "Ministry of Health & Family Welfare", "All India", "Health", 12000, None, None, None, 0, 99, 400000, None, None, False, None, "https://nikshay.in"),
        ("IN_SC_VENTURE", "Ambedkar Social Innovation & Incubation Mission (SC)", "Ministry of Social Justice & Empowerment", "All India", "SC/ST Welfare", 35000, ["Self-Employed", "Student"], None, None, 18, 45, 500000, ["SC"], None, False, None, "https://www.ifcivcf.com"),
        ("IN_NSFDC_TERM", "NSFDC Micro-Credit Finance for SC Families", "Ministry of Social Justice & Empowerment", "All India", "SC/ST Welfare", 20000, ["Self-Employed", "Farmer", "Artisan"], None, None, 18, 55, 300000, ["SC"], None, False, None, "https://nsfdc.nic.in"),
        ("IN_NSTFDC_ADIVASI", "NSTFDC Adivasi Mahila Sashaktikaran Yojana", "Ministry of Tribal Affairs", "All India", "SC/ST Welfare", 24000, ["Self-Employed", "Farmer", "Artisan"], None, None, 18, 55, 300000, ["ST"], "Female", False, None, "https://nstfdc.tribal.gov.in"),
        ("IN_NBCFDC_SWARNIMA", "NBCFDC New Swarnima Loan for Backward Class Women", "Ministry of Social Justice & Empowerment", "All India", "Women & Social Welfare", 20000, ["Self-Employed", "Artisan"], None, None, 18, 55, 300000, ["OBC"], "Female", False, None, "https://nbcfdc.gov.in"),
        ("IN_DAY_NULM", "DAY-NULM Urban Self-Employment Interest Subsidy", "Ministry of Housing & Urban Affairs", "All India", "Employment & Skill", 16000, ["Self-Employed", "Unemployed"], None, None, 18, 55, 250000, None, None, True, "Urban", "https://nulm.gov.in"),
        ("IN_PM_DAKSH", "PM-DAKSH Skill Training & Stipend (SC/OBC/EWS)", "Ministry of Social Justice & Empowerment", "All India", "Employment & Skill", 14000, ["Unemployed", "Student", "Artisan"], None, None, 18, 45, 300000, ["SC", "OBC", "EWS"], None, False, None, "https://pmdaksh.dosje.gov.in"),
        # Telangana Additional Schemes
        ("TS_EPASS_SC", "Telangana ePASS Post-Matric Scholarship (SC/ST/BC)", "Welfare Departments, Govt of Telangana", "Telangana", "Education & Scholarship", 20000, ["Student"], None, None, 15, 30, 200000, ["SC", "ST", "OBC"], None, False, None, "https://telanganaepass.cgg.gov.in"),
        ("TS_AMBEDKAR_OVERSEAS", "Ambedkar Overseas Vidya Nidhi (Telangana SC/ST)", "SC Development Dept, Telangana", "Telangana", "Education & Scholarship", 100000, ["Student"], None, None, 20, 35, 500000, ["SC", "ST"], None, False, None, "https://telanganaepass.cgg.gov.in"),
        ("TS_INDIRAMMA_ATMIYA", "Indiramma Atmiya Bharosa (Landless Farm Laborers)", "Agriculture Dept, Govt of Telangana", "Telangana", "Agriculture", 12000, ["Agricultural Laborer"], 0.0, 0.0, 18, 65, 200000, None, None, True, "Rural", "https://agri.telangana.gov.in"),
        ("TS_KCR_KIT_NUTRITION", "Telangana Maternal & Child Nutrition Kit", "Health & Family Welfare Dept, Telangana", "Telangana", "Health", 13000, None, None, None, 18, 45, 250000, None, "Female", True, None, "https://chfw.telangana.gov.in"),
        ("TS_WEAVER_CHENETHA", "Telangana Chenetha Mithra Handloom Weaver Subsidy", "Handlooms & Textiles Dept, Telangana", "Telangana", "Employment & Skill", 18000, ["Artisan"], None, None, 18, 65, 250000, None, None, False, None, "https://handlooms.telangana.gov.in"),
        ("TS_BC_BANDHU", "Telangana BC Artisan & Vishwakarma Rs 1 Lakh Grant", "BC Welfare Dept, Telangana", "Telangana", "Employment & Skill", 33000, ["Artisan", "Self-Employed"], None, None, 21, 55, 200000, ["OBC"], None, False, None, "https://tsobmms.cgg.gov.in"),
        ("TS_GIRIJANA_VIKAS", "Telangana Girijana Vikasam Tribal Land Irrigation", "Tribal Welfare Dept, Telangana", "Telangana", "SC/ST Welfare", 28000, ["Farmer"], 0.5, None, 18, 65, 250000, ["ST"], None, False, "Rural", "https://twd.telangana.gov.in"),
        ("TS_MINORITY_OVERSEAS", "Chief Minister's Overseas Scholarship (Minorities TS)", "Minorities Welfare Dept, Telangana", "Telangana", "Education & Scholarship", 100000, ["Student"], None, None, 20, 35, 500000, ["Minority"], None, False, None, "https://telanganaepass.cgg.gov.in"),
        ("TS_SHG_VADDILENI", "Telangana Stree Nidhi / Interest-Free SHG Loan", "SERP, Govt of Telangana", "Telangana", "Women & Social Welfare", 15000, ["Self-Employed", "Farmer", "Artisan"], None, None, 18, 60, 250000, None, "Female", False, "Rural", "https://streenidhi.telangana.gov.in"),
        ("TS_DIVYANG_PENSION", "Telangana Cheyutha Disability Pension (Rs 4,016/mo)", "SERP, Govt of Telangana", "Telangana", "Disability Support", 48192, None, None, None, 5, 85, 200000, None, None, True, None, "https://aasara.telangana.gov.in"),
        # Andhra Pradesh Additional Schemes
        ("AP_DEEPAM_2", "Andhra Pradesh Deepam 2.0 (3 Free LPG Cylinders)", "Civil Supplies Dept, Andhra Pradesh", "Andhra Pradesh", "Women & Social Welfare", 2700, None, None, None, 18, 80, 250000, None, "Female", True, None, "https://civilsupplies.ap.gov.in"),
        ("AP_NTR_BHAROSA_OLD", "AP NTR Bharosa Old Age Pension (Rs 4,000/month)", "SERP, Govt of Andhra Pradesh", "Andhra Pradesh", "Social Security", 48000, None, None, None, 60, 99, 150000, None, None, True, None, "https://sspensions.ap.gov.in"),
        ("AP_NTR_BHAROSA_DIS", "AP NTR Bharosa Disability Pension (Rs 6,000/month)", "SERP, Govt of Andhra Pradesh", "Andhra Pradesh", "Disability Support", 72000, None, None, None, 5, 99, 200000, None, None, True, None, "https://sspensions.ap.gov.in"),
        ("AP_NTR_VAIDYA_SEVA", "Dr. NTR Vaidya Seva Health Cover (Rs 25 Lakh)", "Health Dept, Govt of Andhra Pradesh", "Andhra Pradesh", "Health", 8000, None, None, None, 0, 99, 500000, None, None, True, None, "https://drntrvaidyaseva.ap.gov.in"),
        ("AP_JAGANANNA_VIDYA", "AP Post-Matric Fee Reimbursement (RTF & MTF)", "Social Welfare Dept, Andhra Pradesh", "Andhra Pradesh", "Education & Scholarship", 22000, ["Student"], None, None, 16, 30, 250000, ["SC", "ST", "OBC", "EWS"], None, False, None, "https://jnanabhumi.ap.gov.in"),
        ("AP_AADABIDDA_NIDHI", "Andhra Pradesh Aadabidda Nidhi Women Support", "Women Development Dept, Andhra Pradesh", "Andhra Pradesh", "Women & Social Welfare", 18000, None, None, None, 18, 59, 250000, None, "Female", True, None, "https://ap.gov.in"),
        ("AP_YUVA_GALAM", "Andhra Pradesh Youth Unemployment Allowance", "Youth Services Dept, Andhra Pradesh", "Andhra Pradesh", "Employment & Skill", 36000, ["Unemployed"], None, None, 20, 35, 300000, None, None, False, None, "https://ap.gov.in"),
        ("AP_CHENETHA_POWER", "AP Handloom Weaver Free Power & Capital Support", "Handlooms Dept, Andhra Pradesh", "Andhra Pradesh", "Employment & Skill", 24000, ["Artisan"], None, None, 18, 65, 250000, None, None, False, None, "https://ap.gov.in"),
        ("AP_MATSYAKARA", "AP Matsyakara Bharosa Marine Ban Relief", "Fisheries Dept, Andhra Pradesh", "Andhra Pradesh", "Agriculture", 10000, ["Farmer", "Self-Employed"], None, None, 18, 60, 250000, None, None, True, None, "https://fisheries.ap.gov.in"),
        ("AP_SC_CORP_SELF", "AP SC Cooperative Corporation Self-Employment Grant", "SC Welfare Dept, Andhra Pradesh", "Andhra Pradesh", "SC/ST Welfare", 35000, ["Self-Employed", "Unemployed"], None, None, 21, 55, 200000, ["SC"], None, False, None, "https://apobmms.apcfss.in"),
        # Karnataka Additional Schemes
        ("KA_ANNA_BHAGYA", "Karnataka Anna Bhagya Free Foodgrain DBT", "Food & Civil Supplies Dept, Karnataka", "Karnataka", "Social Security", 8160, None, None, None, 18, 99, 200000, None, None, True, None, "https://ahara.kar.nic.in"),
        ("KA_RAITHA_SHAKTI", "Karnataka Raitha Shakti Diesel & Farm Mechanization", "Agriculture Dept, Govt of Karnataka", "Karnataka", "Agriculture", 5000, ["Farmer"], 0.5, None, 18, 75, 400000, None, None, False, "Rural", "https://raitamitra.karnataka.gov.in"),
        ("KA_VIDYASIRI", "Karnataka Vidyasiri Food & Accommodation Scholarship", "Backward Classes Welfare Dept, Karnataka", "Karnataka", "Education & Scholarship", 15000, ["Student"], None, None, 16, 30, 250000, ["SC", "ST", "OBC"], None, False, None, "https://ssp.postmatric.karnataka.gov.in"),
        ("KA_SANDHYA_SURAKSHA", "Karnataka Sandhya Suraksha Senior Citizen Pension", "Revenue Dept, Govt of Karnataka", "Karnataka", "Social Security", 14400, None, None, None, 65, 99, 150000, None, None, True, None, "https://nadakacheri.karnataka.gov.in"),
        ("KA_UDYOGINI", "Karnataka Udyogini Women Micro-Business Subsidy", "KSWDC, Govt of Karnataka", "Karnataka", "Women & Social Welfare", 30000, ["Self-Employed", "Artisan"], None, None, 18, 55, 200000, None, "Female", False, None, "https://kswdc.karnataka.gov.in"),
        ("KA_AIRAVATA_SC", "Karnataka Airavata SC/ST Youth Taxi Enterprise", "Social Welfare Dept, Karnataka", "Karnataka", "SC/ST Welfare", 50000, ["Self-Employed", "Unemployed"], None, None, 21, 45, 300000, ["SC", "ST"], None, False, None, "https://kalyanakendra.karnataka.gov.in"),
        ("KA_GANGA_KALYANA", "Karnataka Ganga Kalyana Borewell & Irrigation (SC/ST)", "Dr. B.R. Ambedkar Dev Corp, Karnataka", "Karnataka", "Agriculture", 45000, ["Farmer"], 1.0, 5.0, 18, 65, 200000, ["SC", "ST"], None, False, "Rural", "https://adcl.karnataka.gov.in"),
        ("KA_ASHRAYA_HOUSING", "Karnataka Basava Vasati / Ashraya Rural Housing", "Rajiv Gandhi Housing Corp, Karnataka", "Karnataka", "Housing & Utilities", 30000, None, None, None, 18, 75, 150000, None, None, True, "Rural", "https://ashraya.karnataka.gov.in"),
        ("KA_DIVYANG_ADHARA", "Karnataka Adhara Monthly Disability Pension", "Dept for Empowerment of Differently Abled, KA", "Karnataka", "Disability Support", 16800, None, None, None, 5, 99, 200000, None, None, True, None, "https://dwdsc.karnataka.gov.in"),
        ("KA_BHAGYALAKSHMI", "Karnataka Bhagyalakshmi Girl Child Bond", "Women & Child Dev Dept, Karnataka", "Karnataka", "Women & Social Welfare", 10000, None, None, None, 0, 12, 200000, None, "Female", True, None, "https://blakshmi.kar.nic.in"),
        # Tamil Nadu Additional Schemes
        ("TN_TAMIL_PUDHALVAN", "Tamil Pudhalvan Boys College Monthly Stipend", "Social Welfare Dept, Tamil Nadu", "Tamil Nadu", "Education & Scholarship", 12000, ["Student"], None, None, 17, 25, 300000, None, "Male", False, None, "https://www.tn.gov.in"),
        ("TN_CMCHIS", "Chief Minister's Comprehensive Health Insurance (TN)", "Health & Family Welfare Dept, Tamil Nadu", "Tamil Nadu", "Health", 6000, None, None, None, 0, 99, 120000, None, None, True, None, "https://www.cmchistn.com"),
        ("TN_FREE_FARM_POWER", "Tamil Nadu Free Agricultural Electricity Supply", "TANGEDCO / Agriculture Dept, Tamil Nadu", "Tamil Nadu", "Agriculture", 18000, ["Farmer"], 0.5, None, 18, 80, 500000, None, None, False, "Rural", "https://www.tnagrisnet.tn.gov.in"),
        ("TN_KALAIGNAR_KANAVU", "Kalaignar Kanavu Illam Rural Housing Scheme", "Rural Development Dept, Tamil Nadu", "Tamil Nadu", "Housing & Utilities", 35000, None, None, None, 18, 75, 150000, None, None, True, "Rural", "https://tnrd.tn.gov.in"),
        ("TN_VIDIYAL_PAYANAM", "Tamil Nadu Vidiyal Payanam Free Town Bus for Women", "Transport Dept, Govt of Tamil Nadu", "Tamil Nadu", "Women & Social Welfare", 10800, None, None, None, 6, 99, 1000000, None, "Female", False, None, "https://www.tn.gov.in"),
        ("TN_OAP_PENSION", "Tamil Nadu Old Age / Widow Social Security Pension", "Revenue Dept, Govt of Tamil Nadu", "Tamil Nadu", "Social Security", 14400, None, None, None, 60, 99, 120000, None, None, True, None, "https://www.tnesevai.tn.gov.in"),
        ("TN_DISABILITY_MAINT", "Tamil Nadu Differently Abled Maintenance Allowance", "Welfare of Differently Abled Dept, TN", "Tamil Nadu", "Disability Support", 24000, None, None, None, 5, 99, 250000, None, None, False, None, "https://scd.tn.gov.in"),
        ("TN_TAHDCO_SC", "TAHDCO SC/ST Entrepreneur Subsidy (Tamil Nadu)", "TAHDCO, Govt of Tamil Nadu", "Tamil Nadu", "SC/ST Welfare", 35000, ["Self-Employed", "Farmer", "Artisan"], None, None, 18, 55, 300000, ["SC", "ST"], None, False, None, "https://tahdco.com"),
        ("TN_NAAN_MUDHALVAN", "Naan Mudhalvan Youth Upskilling & Placement", "TN Skill Development Corporation", "Tamil Nadu", "Employment & Skill", 12000, ["Student", "Unemployed"], None, None, 17, 28, 500000, None, None, False, None, "https://www.naanmudhalvan.tn.gov.in"),
        ("TN_MUTHULAKSHMI_MAT", "Dr. Muthulakshmi Reddy Maternity Assistance", "Health Dept, Govt of Tamil Nadu", "Tamil Nadu", "Women & Social Welfare", 18000, None, None, None, 19, 45, 250000, None, "Female", True, None, "https://picme.tn.gov.in"),
    ]

    result: List[Dict[str, Any]] = []
    for (
        sid,
        name,
        ministry,
        state,
        category,
        benefit_inr,
        occupations,
        min_land,
        max_land,
        min_age,
        max_age,
        max_income,
        cats,
        gender,
        bpl_req,
        residence,
        url,
    ) in templates:
        rules: List[Dict[str, Any]] = []
        clauses: List[str] = []
        if state != "All India":
            rules.append({"field": "state", "op": "==", "value": state, "label": f"Resident of {state}"})
            clauses.append(f"Resident of {state}")
        if gender:
            rules.append({"field": "gender", "op": "==", "value": gender, "label": f"Gender is {gender}"})
            clauses.append(f"{gender} applicant")
        if cats:
            rules.append({"field": "category", "op": "in", "value": cats, "label": f"Category in {'/'.join(cats)}"})
            clauses.append(f"Category {'/'.join(cats)}")
        if occupations:
            rules.append({"field": "occupation", "op": "in", "value": occupations, "label": f"Occupation in {', '.join(occupations)}"})
            clauses.append(f"Occupation {', '.join(occupations)}")
        if min_age > 0:
            rules.append({"field": "age", "op": ">=", "value": min_age, "label": f"Age >= {min_age} years"})
        if max_age < 99:
            rules.append({"field": "age", "op": "<=", "value": max_age, "label": f"Age <= {max_age} years"})
        clauses.append(f"age {min_age} to {max_age}")
        rules.append({"field": "income", "op": "<=", "value": max_income, "label": f"Annual income <= Rs {max_income:,}"})
        clauses.append(f"annual income <= Rs {max_income:,}")
        if min_land is not None and min_land > 0:
            rules.append({"field": "land", "op": ">=", "value": min_land, "label": f"Cultivable land >= {min_land} acres"})
            clauses.append(f"land >= {min_land} acres")
        if max_land is not None:
            rules.append({"field": "land", "op": "<=", "value": max_land, "label": f"Land <= {max_land} acres"})
            clauses.append(f"land <= {max_land} acres")
        if bpl_req:
            rules.append({"field": "bpl", "op": "==", "value": True, "label": "BPL / Ration Card household"})
            clauses.append("BPL household")
        if residence:
            rules.append({"field": "residence", "op": "==", "value": residence, "label": f"{residence} residence"})
            clauses.append(f"{residence} resident")
        if category == "Disability Support" or "DIVYANG" in sid or "DISABILITY" in sid or "SAKSHAM" in sid:
            rules.append({"field": "disability", "op": "==", "value": True, "label": "Benchmark disability certified"})
            clauses.append("certified benchmark disability")

        docs = ["Aadhaar Card", "Bank Account Passbook (Aadhaar-seeded)"]
        if bpl_req:
            docs.append("BPL / Ration Card")
        if max_income <= 300000:
            docs.append("Income Certificate")
        if cats:
            docs.append("Caste Certificate")
        if occupations and "Farmer" in occupations:
            docs.append("Land Ownership Record (ROR / Pattadar Passbook)")
        if occupations and "Student" in occupations:
            docs.append("Bonafide Student Certificate")
        if category == "Disability Support":
            docs.append("UDID / Disability Certificate")

        complementary = []
        if category == "Agriculture" and sid != "IN_PM_KISAN":
            complementary.append("IN_PM_KISAN")
        if category == "Health" and sid != "IN_PMJAY":
            complementary.append("IN_PMJAY")

        native_tr = {
            "KA_ANNA_BHAGYA": ("అన్న భాగ్య కర్ణాటక", "कर्नाटक अन्न भाग्य मुफ्त अनाज", "ಕರ್ನಾಟಕ ಅನ್ನ ಭಾಗ್ಯ ಉಚಿತ ಆಹಾರ ಧಾನ್ಯ ಡಿಬಿಟಿ ಯೋಜನೆ", "கர்நாடகா அன்ன பாக்யா இலவச உணவு தானியம்"),
            "KA_RAITHA_SHAKTI": ("రైత శక్తి కర్ణాటక", "कर्नाटक रैत शक्ति डीजल सब्सिडी", "ಕರ್ನಾಟಕ ರೈತ ಶಕ್ತಿ ಡೀಸೆಲ್ ಸಬ್ಸಿಡಿ ರೈತರು ಕೃಷಿ ಯಂತ್ರೋಪಕರಣ", "கர்நாடகா ரைத்த சக்தி விவசாயிகள் டீசல் மானியம்"),
            "KA_VIDYASIRI": ("విద్యాసిరి స్కాలర్‌షిప్", "कर्नाटक विद्यासिरी छात्रवृत्ति", "ಕರ್ನಾಟಕ ವಿದ್ಯಾಸಿರಿ ವಿದ್ಯಾರ್ಥಿವೇತನ ಒಬಿಸಿ ಎಸ್‌ಸಿ ಎಸ್‌ಟಿ ವಿದ್ಯಾರ್ಥಿಗಳು", "கர்நாடகா வித்யாசிறி கல்வி உதவித்தொகை"),
            "KA_SANDHYA_SURAKSHA": ("సంధ్య సురక్ష పింఛను", "कर्नाटक संध्या सुरक्षा वृद्धावस्था पेंशन", "ಕರ್ನಾಟಕ ಸಂಧ್ಯಾ ಸುರಕ್ಷಾ ವೃದ್ಧಾಪ್ಯ ಪಿಂಚಣಿ ಯೋಜನೆ", "கர்நாடகா சந்தியா சுரக்ஷா முதியோர் ஓய்வூதியம்"),
            "KA_UDYOGINI": ("ఉద్యోగిని మహిళా రుణం", "कर्नाटक उद्योगिनी महिला उद्यम ऋण", "ಕರ್ನಾಟಕ ಉದ್ಯೋಗಿನಿ ಮಹಿಳಾ ಉದ್ಯಮ ಸಬ್ಸಿಡಿ ಸಾಲ ಯೋಜನೆ", "கர்நாடகா உத்யோகினி பெண் தொழில்முனைவோர் கடன்"),
            "KA_GANGA_KALYANA": ("గంగ కళ్యాణ బోర్‌వెల్", "कर्नाटक गंगा कल्याण बोरवेल सिंचाई", "ಕರ್ನಾಟಕ ಗಂಗಾ ಕಲ್ಯಾಣ ಬೋರ್‌ವೆಲ್ ನೀರಾವರಿ ಎಸ್‌ಸಿ ಎಸ್‌ಟಿ ರೈತರು", "கர்நாடகா கங்கா கல்யாண ஆழ்துளை கிணறு நீர்ப்பாசனம்"),
            "TN_TAMIL_PUDHALVAN": ("తమిళ్ పుదల్వన్ స్కాలర్‌షిప్", "तमिल पुधलवन छात्र छात्रवृत्ति", "ತಮಿಳು ಪುದಲ್ವನ್ ವಿದ್ಯಾರ್ಥಿವೇತನ", "தமிழ் புதல்வன் கல்லூரி மாணவர் உதவித்தொகை மாதம் 1000"),
            "TN_CMCHIS": ("తమిళనాడు సీఎం ఆరోగ్య బీమా", "तमिलनाडु मुख्यमंत्री स्वास्थ्य बीमा", "ತಮಿಳುನಾಡು ಮುಖ್ಯಮಂತ್ರಿ ಆರೋಗ್ಯ ವಿಮೆ", "முதலமைச்சரின் விரிவான மருத்துவ காப்பீட்டுத் திட்டம் தமிழ்நாடு CMCHIS"),
            "TN_VIDIYAL_PAYANAM": ("విడియల్ పయనం ఉచిత బస్సు", "तमिलनाडु विडियल पयनम मुफ्त बस", "ತಮಿಳುನಾಡು ವಿಡಿಯಲ್ ಪಯಣಂ ಉಚಿತ ಬಸ್", "விடியல் பயணம் பெண்களுக்கு இலவச பேருந்து பயணம் தமிழ்நாடு"),
            "TN_KALAIGNAR_KANAVU": ("కళైஞర్ కనవు ఇల్లం", "कलैगनार कनवु इल्लम ग्रामीण आवास", "ಕಲೈஞರ್ ಕನವು ಇಲ್ಲಂ ಮನೆ ಯೋಜನೆ", "கலைஞர் கனவு இல்லம் கிராமப்புற வீட்டு வசதித் திட்டம் தமிழ்நாடு"),
            "TN_MUTHULAKSHMI_MAT": ("ముత్తులక్ష్మి మాతృత్వ సహాయం", "डॉ मुथुलक्ष्मी रेड्डी मातृत्व सहायता", "ಡಾ ಮುತ್ತುಲಕ್ಷ್ಮಿ ರೆಡ್ಡಿ ಮಾತೃತ್ವ ನೆರವು", "டாக்டர் முத்துலட்சுமி ரெட்டி மகப்பேறு நிதி உதவி திட்டம் தமிழ்நாடு"),
            "TN_NAAN_MUDHALVAN": ("నాన్ ముదల్వన్ నైపుణ్య పథకం", "नान मुधलवन युवा कौशल योजना", "ನಾನ್ ಮುದಲ್ವನ್ ಯುವ ಕೌಶಲ್ಯ", "நான் முதல்வன் இளைஞர் திறன் மேம்பாட்டுத் திட்டம் தமிழ்நாடு"),
            "TN_TAHDCO_SC": ("తాడ్కో ఎస్సీ సబ్సిడీ", "ताडको एससी उद्यमी सब्सिडी", "ತಾಡ್ಕೊ ಎಸ್‌ಸಿ ಉದ್ಯಮ ಸಹಾಯಧನ", "தாட்கோ TAHDCO பட்டியலின தொழில்முனைவோர் மானியம் தமிழ்நாடு"),
            "TN_OAP_PENSION": ("తమిళనాడు వృద్ధాప్య పింఛను", "तमिलनाडु वृद्धावस्था विधवा पेंशन", "ತಮಿಳುನಾಡು ವೃದ್ಧಾಪ್ಯ ಪಿಂಚಣಿ", "தமிழ்நாடு முதியோர் விதவை ஓய்வூதியம் ஆவணங்கள்"),
            "TN_FREE_FARM_POWER": ("తమిళనాడు ఉచిత వ్యవసాయ విద్యుత్", "तमिलनाडु मुफ्त कृषि बिजली", "ತಮಿಳುನಾಡು ಉಚಿತ ಕೃಷಿ ವಿದ್ಯುತ್", "தமிழ்நாடு விவசாயிகளுக்கு இலவச மின்சாரம்"),
            "TN_DISABILITY_MAINT": ("తమిళనాడు దివ్యాంగుల భత్యం", "तमिलनाडु दिव्यांग भत्ता", "ತಮಿಳುನಾಡು ಅಂಗವಿಕಲರ ಭತ್ಯೆ", "தமிழ்நாடு மாற்றுத்திறனாளிகள் பராமரிப்பு உதவித்தொகை"),
        }
        tr_tuple = native_tr.get(sid)
        translations_dict = (
            {"te": tr_tuple[0], "hi": tr_tuple[1], "kn": tr_tuple[2], "ta": tr_tuple[3]}
            if tr_tuple
            else {
                "te": f"{name} ({state}) — సంవత్సరానికి సుమారు రూ. {benefit_inr:,} లబ్ధి.",
                "hi": f"{name} ({state}) — अनुमानित वार्षिक लाभ ₹{benefit_inr:,}।",
                "kn": f"{name} ({state}) — ವಾರ್ಷಿಕ ಅಂದಾಜು ಲಾಭ ರೂ. {benefit_inr:,}.",
                "ta": f"{name} ({state}) — ஆண்டு மதிப்பிடப்பட்ட பலன் ரூ.{benefit_inr:,}.",
            }
        )

        result.append(
            _make_scheme(
                scheme_id=sid,
                name=name,
                ministry=ministry,
                state=state,
                category=category,
                benefits=f"Estimated annual welfare value Rs {benefit_inr:,}/year under {name}.",
                annual_benefit_inr=benefit_inr,
                eligibility_text="; ".join(clauses) + ".",
                rules=rules,
                documents=docs,
                apply_url=url,
                source_url=url,
                translations=translations_dict,
                keywords=[name.lower(), state.lower(), category.lower(), sid.lower()] + (list(tr_tuple) if tr_tuple else []),
                complementary_to=complementary,
            )
        )
    return result


def main() -> int:
    """Build, validate, deduplicate, and save /data/cached_schemes.json + diff log."""
    all_schemes = dedupe_schemes(build_core_schemes() + build_extended_schemes())
    for s in all_schemes:
        errs = validate_scheme_schema(s)
        if errs:
            raise ValueError(f"Invalid scheme {s.get('scheme_id')}: {errs}")

    out_path = Path("data/cached_schemes.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(all_schemes, indent=2, ensure_ascii=False), encoding="utf-8")

    # Create a baseline snapshot (v1) so daily diff log shows realistic added + updated schemes
    prev_snapshot = []
    for s in all_schemes[:-2]:
        copy_s = dict(s)
        if copy_s["scheme_id"] == "TS_RYTHU_BHAROSA":
            copy_s["annual_benefit_inr"] = 12000
            copy_s["benefits"] = "Rs 10,000 per acre/year (previous rate)."
        prev_snapshot.append(copy_s)

    snap_path = Path("data/processed/prev_schemes_snapshot.json")
    snap_path.parent.mkdir(parents=True, exist_ok=True)
    snap_path.write_text(json.dumps(prev_snapshot, indent=2, ensure_ascii=False), encoding="utf-8")

    diff = write_diff_log(prev_snapshot, all_schemes)
    stats = build_index_metadata(all_schemes)
    print(
        f"Built {len(all_schemes)} valid schemes across {len(stats['states'])} jurisdictions. "
        f"Diff log: added={diff['summary']['added']}, changed={diff['summary']['changed']}, removed={diff['summary']['removed']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
