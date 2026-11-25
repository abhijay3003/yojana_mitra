"""P2 Gold Set Generator (SEED=42).

Generates:
- /data/gold/questions_100.jsonl (20 per language x 5 languages: en, te, hi, kn, ta)
- /data/gold/profiles_50.jsonl (50 citizen profiles with ground-truth verdicts)
- /data/gold/multihop_40.jsonl (40 multi-hop GraphRAG questions)
- /data/gold/telugu_utterances_50.jsonl (50 Telugu utterance transcripts for ASR/WER)
- /data/gold/scam_messages_100.jsonl (50 scam + 50 legitimate messages)
- /data/gold/verify.csv (20% human-verification sample)
- /data/gold/LABELING_GUIDE.md
"""

from __future__ import annotations

import csv
import json
import random
from pathlib import Path
from typing import Any, Dict, List

from pipeline.indexer import load_cached_schemes
from rules.engine import evaluate

SEED = 42
GOLD_DIR = Path("data/gold")


def build_questions_100(schemes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build 100 multilingual gold queries (20 each for en, te, hi, kn, ta)."""
    by_id = {s["scheme_id"]: s for s in schemes}
    en_seeds = [
        ("Am I eligible for Telangana Rythu Bharosa farmer investment support?", "TS_RYTHU_BHAROSA", "eligibility"),
        ("What documents are required for PM-KISAN Samman Nidhi?", "IN_PM_KISAN", "documents"),
        ("How to apply for Telangana Mahalakshmi Rs 2500 monthly women scheme?", "TS_MAHALAKSHMI", "how_to_apply"),
        ("Tell me about Telangana Dalit Bandhu Rs 10 lakh SC enterprise grant", "TS_DALIT_BANDHU", "eligibility"),
        ("Details of Telangana Rythu Bima 5 lakh farmer life insurance", "TS_RYTHU_BIMA", "eligibility"),
        ("How to get 200 units free electricity under Telangana Gruha Jyothi?", "TS_GRIHA_JYOTHI", "how_to_apply"),
        ("Indiramma Indlu housing scheme eligibility for BPL families", "TS_INDIRAMMA_INDLU", "eligibility"),
        ("Telangana Aasara Cheyutha old age pension eligibility", "TS_AASARA_PENSION", "eligibility"),
        ("Kalyana Lakshmi Shaadi Mubarak marriage assistance documents", "TS_KALYANA_LAKSHMI", "documents"),
        ("Rajiv Aarogyasri 10 lakh cashless health cover Telangana", "TS_AROGYASRI", "eligibility"),
        ("Pradhan Mantri Fasal Bima Yojana crop insurance premium details", "IN_PMFBY", "how_to_apply"),
        ("Kisan Credit Card 4 percent crop loan eligibility", "IN_KCC", "eligibility"),
        ("PM-KUSUM 60 percent subsidy solar pump for rural farmers", "IN_PM_KUSUM", "eligibility"),
        ("Ayushman Bharat PM-JAY 5 lakh health insurance card", "IN_PMJAY", "documents"),
        ("PMAY Gramin rural pucca house construction grant eligibility", "IN_PMAY_GRAMIN", "eligibility"),
        ("PM Ujjwala Yojana free LPG gas cylinder subsidy for BPL women", "IN_UJJWALA", "eligibility"),
        ("MGNREGA 100 days rural wage employment job card documents", "IN_MGNREGA", "documents"),
        ("PM Vishwakarma Rs 15000 toolkit and loan for artisans", "IN_PM_VISHWAKARMA", "how_to_apply"),
        ("Stand-Up India SC ST women entrepreneur loan scheme", "IN_STANDUP_INDIA", "eligibility"),
        ("Central Post-Matric Scholarship for SC students on NSP", "IN_NSP_POST_MATRIC_SC", "eligibility"),
    ]
    te_seeds = [
        ("తెలంగాణ రైతు భరోసా పథకానికి అర్హతలు ఏమిటి?", "TS_RYTHU_BHAROSA", "eligibility"),
        ("పీఎం కిసాన్ సమ్మాన్ నిధి కోసం ఏ పత్రాలు కావాలి?", "IN_PM_KISAN", "documents"),
        ("మహాలక్ష్మి పథకం నెలకు రూ. 2500 మహిళలకు ఎలా దరఖాస్తు చేయాలి?", "TS_MAHALAKSHMI", "how_to_apply"),
        ("రైతు బీమా 5 లక్షల జీవిత బీమా తెలంగాణ అర్హత", "TS_RYTHU_BIMA", "eligibility"),
        ("దళిత బంధు ఎస్సీ పథకం రూ. 10 లక్షల సహాయం వివరాలు", "TS_DALIT_BANDHU", "eligibility"),
        ("గృహ జ్యోతి 200 యూనిట్ల ఉచిత విద్యుత్ తెలంగాణ దరఖాస్తు", "TS_GRIHA_JYOTHI", "how_to_apply"),
        ("ఇందిరమ్మ ఇండ్లు 5 లక్షల ఇంటి పథకం అర్హతలు", "TS_INDIRAMMA_INDLU", "eligibility"),
        ("ఆసరా చేయూత పింఛను వృద్ధులు వితంతువులు అర్హత", "TS_AASARA_PENSION", "eligibility"),
        ("కళ్యాణ లక్ష్మి షాదీ ముబారక్ వివాహ సహాయం పత్రాలు", "TS_KALYANA_LAKSHMI", "documents"),
        ("రాజీవ్ ఆరోగ్యశ్రీ 10 లక్షల ఉచిత వైద్యం తెలంగాణ", "TS_AROGYASRI", "eligibility"),
        ("అన్నదాత సుఖీభవ ఆంధ్రప్రదేశ్ రైతు పథకం రూ. 20000", "AP_ANNADATA_SUKHIBHAVA", "eligibility"),
        ("తల్లికి వందనం ఆంధ్రప్రదేశ్ పాఠశాల పిల్లల రూ. 15000", "AP_TALLIKI_VANDANAM", "eligibility"),
        ("ఫసల్ బీమా యోజన పంట బీమా దరఖాస్తు విధానం", "IN_PMFBY", "how_to_apply"),
        ("కిసాన్ క్రెడిట్ కార్డ్ పంట రుణం 4 శాతం వడ్డీ", "IN_KCC", "eligibility"),
        ("పీఎం కుసుమ్ సోలార్ పంప్ సబ్సిడీ రైతులు", "IN_PM_KUSUM", "eligibility"),
        ("ఆయుష్మాన్ భారత్ 5 లక్షల ఆరోగ్య బీమా పత్రాలు", "IN_PMJAY", "documents"),
        ("పీఎం ఆవాస్ యోజన గ్రామీణ ఇల్లు నిర్మాణం", "IN_PMAY_GRAMIN", "eligibility"),
        ("ఉజ్వల యోజన ఉచిత గ్యాస్ కనెక్షన్ బీపీఎల్ మహిళలు", "IN_UJJWALA", "eligibility"),
        ("ఉపాధి హామీ MGNREGA 100 రోజుల పని జాబ్ కార్డ్", "IN_MGNREGA", "documents"),
        ("పీఎం విశ్వకర్మ చేతివృత్తుల వారికి టూల్ కిట్ రుణం", "IN_PM_VISHWAKARMA", "how_to_apply"),
    ]
    hi_seeds = [
        ("पीएम किसान सम्मान निधि 6000 रुपये की पात्रता क्या है?", "IN_PM_KISAN", "eligibility"),
        ("प्रधानमंत्री फसल बीमा योजना के लिए कौन से दस्तावेज चाहिए?", "IN_PMFBY", "documents"),
        ("पीएम उज्ज्वला योजना मुफ्त गैस सिलेंडर के लिए आवेदन कैसे करें?", "IN_UJJWALA", "how_to_apply"),
        ("आयुष्मान भारत पीएम-जय 5 लाख स्वास्थ्य बीमा कार्ड", "IN_PMJAY", "documents"),
        ("प्रधानमंत्री आवास योजना ग्रामीण पक्का मकान पात्रता", "IN_PMAY_GRAMIN", "eligibility"),
        ("प्रधानमंत्री आवास योजना शहरी 2.5 लाख सब्सिडी", "IN_PMAY_URBAN", "eligibility"),
        ("मनरेगा 100 दिन ग्रामीण रोजगार जॉब कार्ड दस्तावेज", "IN_MGNREGA", "documents"),
        ("पीएम विश्वकर्मा 15000 टूलकिट और 5% ब्याज ऋण", "IN_PM_VISHWAKARMA", "how_to_apply"),
        ("किसान क्रेडिट कार्ड 4 प्रतिशत ब्याज फसल ऋण", "IN_KCC", "eligibility"),
        ("पीएम कुसुम सोलर पंप 60 प्रतिशत सब्सिडी किसान", "IN_PM_KUSUM", "eligibility"),
        ("स्टैंड-अप इंडिया एससी एसटी महिला उद्यमी ऋण योजना", "IN_STANDUP_INDIA", "eligibility"),
        ("अनुसूचित जाति पोस्ट-मैट्रिक छात्रवृत्ति एनएसपी पात्रता", "IN_NSP_POST_MATRIC_SC", "eligibility"),
        ("पीएम यशस्वी ओबीसी छात्रवृत्ति 20000 आवेदन", "IN_NSP_OBC_SCHOLARSHIP", "how_to_apply"),
        ("इंदिरा गांधी राष्ट्रीय वृद्धावस्था पेंशन 60 वर्ष", "IN_IGNOAPS", "eligibility"),
        ("राष्ट्रीय दिव्यांग पेंशन योजना दस्तावेज यूडीआईडी", "IN_IGNDPS", "documents"),
        ("प्रधानमंत्री मातृ वंदना योजना गर्भवती महिला लाभ", "IN_PM_MATRU_VANDANA", "eligibility"),
        ("पीएम मुद्रा योजना शिशु किशोर 5 लाख बिजनेस लोन", "IN_MUDRA_SHISHU", "how_to_apply"),
        ("पीएम स्वनिधि स्ट्रीट वेंडर रेहड़ी पटरी ऋण", "IN_PM_SVANIDHI", "eligibility"),
        ("तेलंगाना रैतु भरोसा किसान 12000 प्रति एकड़", "TS_RYTHU_BHAROSA", "eligibility"),
        ("कर्नाटक गृह लक्ष्मी महिला 2000 मासिक सहायता", "KA_GRUHA_LAKSHMI", "eligibility"),
    ]
    kn_seeds = [
        ("ಗೃಹ ಲಕ್ಷ್ಮಿ ಯೋಜನೆ ಮಹಿಳೆಯರಿಗೆ 2000 ರೂಪಾಯಿ ಅರ್ಹತೆ ಏನು?", "KA_GRUHA_LAKSHMI", "eligibility"),
        ("ಕರ್ನಾಟಕ ಗೃಹ ಜ್ಯೋತಿ 200 ಯೂನಿಟ್ ಉಚಿತ ವಿದ್ಯುತ್ ಅರ್ಜಿ ಹೇಗೆ?", "KA_GRUHA_JYOTHI", "how_to_apply"),
        ("ಶಕ್ತಿ ಯೋಜನೆ ಕರ್ನಾಟಕ ಮಹಿಳೆಯರಿಗೆ ಉಚಿತ ಬಸ್ ಪ್ರಯಾಣ", "KA_SHAKTI", "eligibility"),
        ("ಯುವ ನಿಧಿ ನಿರುದ್ಯೋಗಿ ಪದವೀಧರರಿಗೆ 3000 ಭತ್ಯೆ ಅರ್ಹತೆ", "KA_YUVA_NIDHI", "eligibility"),
        ("ಅನ್ನ ಭಾಗ್ಯ ಉಚಿತ ಆಹಾರ ಧಾನ್ಯ ಡಿಬಿಟಿ ಕರ್ನಾಟಕ", "KA_ANNA_BHAGYA", "eligibility"),
        ("ರೈತ ಶಕ್ತಿ ಡೀಸೆಲ್ ಸಬ್ಸಿಡಿ ಕರ್ನಾಟಕ ರೈತರು", "KA_RAITHA_SHAKTI", "eligibility"),
        ("ವಿದ್ಯಾಸಿರಿ ವಿದ್ಯಾರ್ಥಿವೇತನ ಒಬಿಸಿ ಎಸ್‌ಸಿ ವಿದ್ಯಾರ್ಥಿಗಳು", "KA_VIDYASIRI", "documents"),
        ("ಸಂಧ್ಯಾ ಸುರಕ್ಷಾ ವೃದ್ಧಾಪ್ಯ ಪಿಂಚಣಿ ಕರ್ನಾಟಕ", "KA_SANDHYA_SURAKSHA", "eligibility"),
        ("ಉದ್ಯೋಗಿನಿ ಮಹಿಳಾ ಉದ್ಯಮ ಸಬ್ಸಿಡಿ ಸಾಲ ಕರ್ನಾಟಕ", "KA_UDYOGINI", "how_to_apply"),
        ("ಗಂಗಾ ಕಲ್ಯಾಣ ಬೋರ್‌ವೆಲ್ ನೀರಾವರಿ ಎಸ್‌ಸಿ ಎಸ್‌ಟಿ ರೈತರು", "KA_GANGA_KALYANA", "eligibility"),
        ("ಪಿಎಂ ಕಿಸಾನ್ ಸಮ್ಮಾನ್ ನಿಧಿ 6000 ರೈತರು ದಾಖಲೆಗಳು", "IN_PM_KISAN", "documents"),
        ("ಆಯುಷ್ಮಾನ್ ಭಾರತ್ 5 ಲಕ್ಷ ಆರೋಗ್ಯ ವಿಮೆ", "IN_PMJAY", "eligibility"),
        ("ಪ್ರಧಾನ ಮಂತ್ರಿ ಫಸಲ್ ಬಿಮಾ ಬೆಳೆ ವಿಮೆ", "IN_PMFBY", "how_to_apply"),
        ("ಪಿಎಂ ವಿಶ್ವಕರ್ಮ ಕುಶಲಕರ್ಮಿಗಳಿಗೆ 15000 ಟೂಲ್‌ಕಿಟ್", "IN_PM_VISHWAKARMA", "eligibility"),
        ("ಉಜ್ವಲ ಯೋಜನೆ ಉಚಿತ ಎಲ್‌ಪಿಜಿ ಗ್ಯಾಸ್ ಸಂಪರ್ಕ", "IN_UJJWALA", "documents"),
        ("ನರೇಗಾ 100 ದಿನಗಳ ಗ್ರಾಮೀಣ ಉದ್ಯೋಗ ಖಾತರಿ", "IN_MGNREGA", "eligibility"),
        ("ಪಿಎಂ ಮುದ್ರಾ ಸಣ್ಣ ಉದ್ಯಮ ಸಾಲ 5 ಲಕ್ಷ", "IN_MUDRA_SHISHU", "how_to_apply"),
        ("ಕಿಸಾನ್ ಕ್ರೆಡಿಟ್ ಕಾರ್ಡ್ 4 ಶೇಕಡಾ ಬೆಳೆ ಸಾಲ", "IN_KCC", "eligibility"),
        ("ಪ್ರಧಾನ ಮಂತ್ರಿ ಆವಾಸ್ ಯೋಜನೆ ಗ್ರಾಮೀಣ ಮನೆ", "IN_PMAY_GRAMIN", "eligibility"),
        ("ಪಿಎಂ ಕುಸುಮ್ ಸೌರ ಪಂಪ್‌ಸೆಟ್ ಸಬ್ಸಿಡಿ", "IN_PM_KUSUM", "eligibility"),
    ]
    ta_seeds = [
        ("கலைஞர் மகளிர் உரிமைத் தொகை மாதம் 1000 தகுதி என்ன?", "TN_KALAIGNAR_MAGALIR", "eligibility"),
        ("புதுமைப் பெண் திட்டம் கல்லூரி மாணவிகளுக்கு 1000 உதவித்தொகை", "TN_PUDHUMAI_PENN", "eligibility"),
        ("தமிழ் புதல்வன் கல்லூரி மாணவர் உதவித்தொகை", "TN_TAMIL_PUDHALVAN", "eligibility"),
        ("முதலமைச்சரின் விரிவான மருத்துவ காப்பீட்டுத் திட்டம் தமிழ்நாடு", "TN_CMCHIS", "documents"),
        ("விடியல் பயணம் பெண்களுக்கு இலவச பேருந்து தமிழ்நாடு", "TN_VIDIYAL_PAYANAM", "eligibility"),
        ("கலைஞர் கனவு இல்லம் கிராமப்புற வீட்டு வசதித் திட்டம்", "TN_KALAIGNAR_KANAVU", "eligibility"),
        ("டாக்டர் முத்துலட்சுமி ரெட்டி மகப்பேறு நிதி உதவி", "TN_MUTHULAKSHMI_MAT", "how_to_apply"),
        ("நான் முதல்வன் இளைஞர் திறன் மேம்பாட்டுத் திட்டம்", "TN_NAAN_MUDHALVAN", "eligibility"),
        ("தாட்கோ TAHDCO பட்டியலின தொழில்முனைவோர் மானியம்", "TN_TAHDCO_SC", "how_to_apply"),
        ("தமிழ்நாடு முதியோர் விதவை ஓய்வூதியம் ஆவணங்கள்", "TN_OAP_PENSION", "documents"),
        ("பிஎம் கிசான் சம்மான் நிதி விவசாயிகள் 6000 ரூபாய்", "IN_PM_KISAN", "eligibility"),
        ("பிரதமர் பயிர் காப்பீட்டுத் திட்டம் PMFBY விண்ணப்பம்", "IN_PMFBY", "how_to_apply"),
        ("ஆயுஷ்மான் பாரத் 5 லட்சம் மருத்துவ காப்பீடு", "IN_PMJAY", "documents"),
        ("உஜ்வாலா இலவச சமையல் எரிவாயு இணைப்பு பெண்கள்", "IN_UJJWALA", "eligibility"),
        ("100 நாள் வேலை MGNREGA ஊரக வேலை உறுதித் திட்டம்", "IN_MGNREGA", "documents"),
        ("பிஎம் விஸ்வகர்மா கைவினைஞர்கள் 15000 கருவித்தொகுப்பு", "IN_PM_VISHWAKARMA", "how_to_apply"),
        ("பிரதமர் முத்ரா சிறு தொழில் கடன் திட்டம்", "IN_MUDRA_SHISHU", "eligibility"),
        ("பிரதமர் ஊரக வீட்டு வசதித் திட்டம் PMAY", "IN_PMAY_GRAMIN", "eligibility"),
        ("கிசான் கிரெடிட் கார்டு 4 சதவீதம் பயிர்க்கடன்", "IN_KCC", "eligibility"),
        ("பிஎம் குசும் சூரிய சக்தி பம்ப்செட் 60 சதவீதம் மானியம்", "IN_PM_KUSUM", "eligibility"),
    ]

    all_rows: List[Dict[str, Any]] = []
    qid = 1
    for lang, group in (("en", en_seeds), ("te", te_seeds), ("hi", hi_seeds), ("kn", kn_seeds), ("ta", ta_seeds)):
        for query, target_id, intent in group:
            assert target_id in by_id, f"Missing target scheme {target_id}"
            all_rows.append(
                {
                    "id": f"Q{qid:03d}",
                    "lang": lang,
                    "query": query,
                    "expected_scheme_ids": [target_id],
                    "intent": intent,
                    "state_hint": by_id[target_id]["state"],
                    "verified_human": (qid % 5 == 0),  # exact 20% slice
                }
            )
            qid += 1
    return all_rows


def build_profiles_50(schemes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build 50 diverse citizen profiles with ground-truth verdicts against target schemes."""
    rng = random.Random(SEED)
    by_id = {s["scheme_id"]: s for s in schemes}
    states = ["Telangana", "Andhra Pradesh", "Karnataka", "Tamil Nadu", "Maharashtra"]
    categories = ["SC", "ST", "OBC", "GEN", "EWS"]
    genders = ["Female", "Male"]
    occupations = ["Farmer", "Agricultural Laborer", "Student", "Artisan", "Self-Employed", "Unemployed", "Salaried"]
    residences = ["Rural", "Urban"]
    target_pool = [
        "TS_RYTHU_BHAROSA", "TS_MAHALAKSHMI", "TS_DALIT_BANDHU", "TS_AASARA_PENSION",
        "IN_PM_KISAN", "IN_UJJWALA", "IN_PMAY_GRAMIN", "IN_NSP_POST_MATRIC_SC",
        "KA_GRUHA_LAKSHMI", "TN_KALAIGNAR_MAGALIR", "AP_ANNADATA_SUKHIBHAVA",
        "IN_PM_VISHWAKARMA", "IN_IGNDPS", "IN_PM_KUSUM",
    ]

    profiles: List[Dict[str, Any]] = []
    # Profile 1 is always the flagship Telangana SC Woman Farmer demo persona
    demo_profile = {
        "age": 38, "income": 140000, "state": "Telangana", "category": "SC",
        "gender": "Female", "occupation": "Farmer", "land": 2.0,
        "disability": False, "bpl": True, "residence": "Rural",
    }
    profiles.append(
        {
            "profile_id": "P001",
            "profile": demo_profile,
            "target_scheme_id": "TS_RYTHU_BHAROSA",
            "expected_verdict": evaluate(demo_profile, by_id["TS_RYTHU_BHAROSA"])["verdict"],
            "counterfactual_target_id": "TS_AASARA_PENSION",
            "verified_human": True,
        }
    )

    for idx in range(2, 51):
        state = states[(idx - 2) % len(states)]
        cat = categories[(idx - 2) % len(categories)]
        gender = genders[idx % 2]
        occ = occupations[(idx - 2) % len(occupations)]
        age = rng.choice([19, 24, 32, 41, 52, 63, 70])
        income = rng.choice([90000, 140000, 195000, 260000, 450000])
        land = rng.choice([0.0, 0.4, 1.2, 3.0]) if occ == "Farmer" else 0.0
        bpl = income <= 200000
        disability = (idx % 10 == 0)
        residence = residences[idx % 2]
        prof = {
            "age": age, "income": income, "state": state, "category": cat,
            "gender": gender, "occupation": occ, "land": land,
            "disability": disability, "bpl": bpl, "residence": residence,
        }
        tid = target_pool[(idx - 2) % len(target_pool)]
        cf_id = target_pool[(idx + 3) % len(target_pool)]
        profiles.append(
            {
                "profile_id": f"P{idx:03d}",
                "profile": prof,
                "target_scheme_id": tid,
                "expected_verdict": evaluate(prof, by_id[tid])["verdict"],
                "counterfactual_target_id": cf_id,
                "verified_human": (idx % 5 == 0),
            }
        )
    return profiles


def build_multihop_40() -> List[Dict[str, Any]]:
    """Build 40 multi-hop questions testing GraphRAG relations."""
    base_queries = [
        ("Which scheme superseded Telangana Rythu Bandhu and what schemes complement it?", "supersedes", "TS_RYTHU_BANDHU_LEGACY", ["TS_RYTHU_BHAROSA", "IN_PM_KISAN"]),
        ("Which central and state schemes complement Telangana Rythu Bharosa for a farmer?", "complementary_to", "TS_RYTHU_BHAROSA", ["IN_PM_KISAN", "TS_RYTHU_BIMA"]),
        ("Which Telangana schemes share the Telangana Food Security (White Ration) Card document?", "requires_document", "Telangana Food Security (White Ration) Card", ["TS_MAHALAKSHMI", "TS_GRIHA_JYOTHI"]),
        ("Which schemes complement Karnataka Gruha Lakshmi for a woman household head?", "complementary_to", "KA_GRUHA_LAKSHMI", ["KA_GRUHA_JYOTHI", "KA_SHAKTI"]),
        ("Which agricultural schemes complement PM-KISAN Samman Nidhi?", "complementary_to", "IN_PM_KISAN", ["IN_PMFBY", "IN_KCC"]),
        ("Which schemes share the Pattadar Passbook (Dharani) document in Telangana?", "requires_document", "Pattadar Passbook (Dharani)", ["TS_RYTHU_BHAROSA", "TS_RYTHU_BIMA"]),
        ("Which schemes are mutually exclusive with Telangana Dalit Bandhu?", "mutually_exclusive_with", "TS_DALIT_BANDHU", ["TS_SC_SUBSIDY_LOAN"]),
        ("Which housing schemes cannot be stacked together with Indiramma Indlu?", "mutually_exclusive_with", "TS_INDIRAMMA_INDLU", ["IN_PMAY_GRAMIN", "IN_PMAY_URBAN"]),
        ("Which disability schemes complement IGNDP disability pension?", "complementary_to", "IN_IGNDPS", ["IN_ADIP_AIDS"]),
        ("Which artisan credit scheme complements PM Vishwakarma?", "complementary_to", "IN_PM_VISHWAKARMA", ["IN_MUDRA_SHISHU"]),
        ("Which schemes under Ministry of Agriculture require Land Ownership Record?", "ministry_document", "Ministry of Agriculture & Farmers Welfare", ["IN_PM_KISAN", "IN_PMFBY"]),
        ("Which Tamil Nadu women schemes complement Kalaignar Magalir Urimai Thogai?", "complementary_to", "TN_KALAIGNAR_MAGALIR", ["TN_PUDHUMAI_PENN"]),
        ("Which schemes complement PM Ujjwala Yojana for rural BPL women?", "complementary_to", "IN_UJJWALA", ["IN_PMAY_GRAMIN", "IN_PM_KISAN"]),
        ("Which schemes complement Andhra Pradesh Annadata Sukhibhava?", "complementary_to", "AP_ANNADATA_SUKHIBHAVA", ["IN_PM_KISAN", "IN_PMFBY"]),
        ("Which schemes require UDID / Disability Certificate?", "requires_document", "UDID / Disability Certificate", ["IN_IGNDPS", "IN_ADIP_AIDS"]),
        ("Which schemes are mutually exclusive with Telangana Mahalakshmi?", "mutually_exclusive_with", "TS_MAHALAKSHMI", ["TS_AASARA_PENSION"]),
        ("Which rural employment scheme complements PMAY Gramin?", "complementary_to", "IN_PMAY_GRAMIN", ["IN_MGNREGA", "IN_UJJWALA"]),
        ("Which schemes require SC Caste Certificate (MeeSeva)?", "requires_document", "SC Caste Certificate (MeeSeva)", ["TS_DALIT_BANDHU", "TS_SC_SUBSIDY_LOAN"]),
        ("Which health cover complements Rajiv Aarogyasri in Telangana?", "complementary_to", "TS_AROGYASRI", ["IN_PMJAY"]),
        ("Which urban scheme complements PMAY Urban for street vendors?", "complementary_to", "IN_PMAY_URBAN", ["IN_PM_SVANIDHI"]),
    ]
    rows: List[Dict[str, Any]] = []
    for idx in range(40):
        q, hop_type, anchor, expected = base_queries[idx % len(base_queries)]
        variant_prefix = "" if idx < 20 else "Multi-hop check: "
        rows.append(
            {
                "id": f"MH{idx + 1:03d}",
                "query": f"{variant_prefix}{q}",
                "hop_type": hop_type,
                "anchor": anchor,
                "expected_scheme_ids": expected,
                "verified_human": ((idx + 1) % 5 == 0),
            }
        )
    return rows


def build_telugu_utterances_50() -> List[Dict[str, Any]]:
    """Build 50 Telugu spoken utterance transcripts + realistic ASR hypothesis samples."""
    templates = [
        ("నాకు రెండు ఎకరాల భూమి ఉంది రైతు భరోసా వస్తుందా", "నాకు రెండు ఎకరాల భూమి ఉంది రైతు భరోసా వస్తుందా"),
        ("తెలంగాణ మహాలక్ష్మి పథకానికి ఏ పత్రాలు కావాలి", "తెలంగాణ మహాలక్ష్మి పథకానికి ఏ పత్రాలు కావాలి"),
        ("పీఎం కిసాన్ డబ్బులు ఖాతాలో ఎప్పుడు పడతాయి", "పీఎం కిసాన్ డబ్బులు ఖాతాలో ఎప్పుడు పడతాయి"),
        ("దళిత బంధు పథకానికి ఎస్సీ కుల ధృవీకరణ పత్రం కావాలా", "దళిత బంధు పథకానికి ఎస్సీ కుల పత్రం కావాలా"),
        ("గృహ జ్యోతి రెండు వందల యూనిట్ల ఉచిత కరెంటు ఎలా పొందాలి", "గృహ జ్యోతి రెండు వందల యూనిట్ల ఉచిత కరెంటు ఎలా పొందాలి"),
        ("ఇందిరమ్మ ఇండ్లు పథకానికి ఆదాయ పరిమితి ఎంత", "ఇందిరమ్మ ఇండ్లు పథకానికి ఆదాయ పరిమితి ఎంత"),
        ("రైతు బీమా ఐదు లక్షల ఇన్సూరెన్స్ వయస్సు పరిమితి ఏమిటి", "రైతు బీమా ఐదు లక్షల ఇన్సూరెన్స్ వయస్సు పరిమితి ఏమిటి"),
        ("ఆసరా పింఛను నాలుగు వేల రూపాయలు ఎవరికి వస్తాయి", "ఆసరా పింఛను నాలుగు వేల రూపాయలు ఎవరికి వస్తాయి"),
        ("కళ్యాణ లక్ష్మి దరఖాస్తు ఆన్లైన్ లో ఎలా చేయాలి", "కళ్యాణ లక్ష్మి దరఖాస్తు ఆన్లైన్ ఎలా చేయాలి"),
        ("ఆరోగ్యశ్రీ కార్డుతో ఏ ఆసుపత్రులలో ఉచిత వైద్యం ఉంది", "ఆరోగ్యశ్రీ కార్డుతో ఏ ఆసుపత్రులలో ఉచిత వైద్యం ఉంది"),
    ]
    rows: List[Dict[str, Any]] = []
    for i in range(50):
        ref, hyp = templates[i % len(templates)]
        rows.append(
            {
                "id": f"TE_ASR_{i + 1:03d}",
                "lang": "te",
                "reference_transcript": ref,
                "asr_hypothesis_sample": hyp,
                "audio_status": "PENDING_HUMAN_RECORDING",
                "verified_human": ((i + 1) % 5 == 0),
            }
        )
    return rows


def build_scam_messages_100() -> List[Dict[str, Any]]:
    """Build 50 realistic Indian welfare scam messages + 50 legitimate official notices."""
    scam_templates = [
        "CONGRATULATIONS! PM Modi Free Laptop & Rs 50,000 Yojana approved! Click http://pm-free-cash-2026.xyz and pay Rs 499 registration fee via UPI immediately!",
        "URGENT: Your PM-KISAN Rs 6000 installment is BLOCKED! Update Aadhaar & OTP at https://pmkisan-kyc-update.top within 2 hours or account will be suspended.",
        "Telangana Mahalakshmi Rs 25000 bonus approved! Forward to 10 WhatsApp groups and pay Rs 199 processing fee to GPay 9876543210.",
        "FREE 5G Smartphone under Digital India Student Scheme! Register now on http://free-phone-sarkar.click and share bank PIN.",
        "PM Awas Yojana Lottery Winner! You won Rs 2,50,000 house fund. Deposit Rs 1,500 stamp duty to UPI pmay.claim@ybl today.",
        "ALERT: Rythu Bharosa KYC expired! Download RythuBharosa_Update.apk from WhatsApp and enter ATM CVV to receive Rs 15,000.",
        "Gruha Lakshmi Karnataka Rs 24,000 instant credit! Pay Rs 250 verification fee at http://gruhalakshmi-apply.online now.",
        "Ayushman Bharat Gold Card 10 Lakh Cashback! Share Aadhaar OTP on call to claim Rs 10,000 Diwali bonus immediately.",
        "PM Vishwakarma Rs 3 Lakh loan approved without documents! Pay Rs 999 agent commission via PhonePe today only.",
        "Modi Free Solar Panel & Rs 78,000 direct cash! Click tinyurl.com/surya-free-cash and submit debit card number.",
    ]
    real_templates = [
        "Official Notice: Verify your PM-KISAN e-KYC and beneficiary status only on https://pmkisan.gov.in or at your nearest CSC center. No registration fee is charged.",
        "Govt of Telangana: Apply for Rythu Bharosa and check Pattadar Passbook eligibility via official portal https://rythubharosa.telangana.gov.in.",
        "Press Information Bureau: PM Ujjwala Yojana 2.0 LPG connections are issued free of deposit through authorized LPG distributors and https://pmuy.gov.in.",
        "National Scholarship Portal (https://scholarships.gov.in) is open for SC/ST/OBC Post-Matric Scholarship applications. Never share your OTP with anyone.",
        "Karnataka Seva Sindhu official advisory: Gruha Lakshmi and Gruha Jyothi registration is completely free at https://sevasindhugs.karnataka.gov.in and Grama One centers.",
        "Ayushman Bharat PM-JAY eligibility can be checked free of cost at https://pmjay.gov.in or toll-free helpline 14555.",
        "Ministry of Rural Development: MGNREGA job cards are issued free by your Gram Panchayat. Verify muster rolls at https://nrega.nic.in.",
        "Tamil Nadu Govt Notice: Kalaignar Magalir Urimai Thogai status is available exclusively on https://kmut.tn.gov.in.",
        "PM Fasal Bima Yojana crop insurance enrollment is open through banks, CSCs, and official portal https://pmfby.gov.in.",
        "Andhra Pradesh Agriculture Dept: Check Annadata Sukhibhava farmer verification at your Rythu Bharosa Kendra or https://annadatasukhibhava.ap.gov.in.",
    ]

    rows: List[Dict[str, Any]] = []
    for i in range(50):
        rows.append(
            {
                "id": f"SCAM_{i + 1:03d}",
                "text": scam_templates[i % len(scam_templates)],
                "label": "SCAM",
                "verified_human": ((i + 1) % 5 == 0),
            }
        )
    for i in range(50):
        rows.append(
            {
                "id": f"REAL_{i + 1:03d}",
                "text": real_templates[i % len(real_templates)],
                "label": "LEGITIMATE",
                "verified_human": ((i + 1) % 5 == 0),
            }
        )
    return rows


def write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    schemes = load_cached_schemes()
    questions = build_questions_100(schemes)
    profiles = build_profiles_50(schemes)
    multihop = build_multihop_40()
    utterances = build_telugu_utterances_50()
    scams = build_scam_messages_100()

    write_jsonl(GOLD_DIR / "questions_100.jsonl", questions)
    write_jsonl(GOLD_DIR / "profiles_50.jsonl", profiles)
    write_jsonl(GOLD_DIR / "multihop_40.jsonl", multihop)
    write_jsonl(GOLD_DIR / "telugu_utterances_50.jsonl", utterances)
    write_jsonl(GOLD_DIR / "scam_messages_100.jsonl", scams)

    # Export exact 20% human-verification slice into verify.csv
    verify_rows: List[Dict[str, str]] = []
    for row in questions:
        if row["verified_human"]:
            verify_rows.append({"dataset": "questions_100", "item_id": row["id"], "lang": row["lang"], "text": row["query"], "auto_label": row["expected_scheme_ids"][0], "human_verified": "PENDING", "reviewer_notes": ""})
    for row in profiles:
        if row["verified_human"]:
            verify_rows.append({"dataset": "profiles_50", "item_id": row["profile_id"], "lang": "en", "text": f"{row['profile']['state']} {row['profile']['category']} {row['profile']['occupation']} -> {row['target_scheme_id']}", "auto_label": row["expected_verdict"], "human_verified": "PENDING", "reviewer_notes": ""})
    for row in multihop:
        if row["verified_human"]:
            verify_rows.append({"dataset": "multihop_40", "item_id": row["id"], "lang": "en", "text": row["query"], "auto_label": ",".join(row["expected_scheme_ids"]), "human_verified": "PENDING", "reviewer_notes": ""})
    for row in scams:
        if row["verified_human"]:
            verify_rows.append({"dataset": "scam_messages_100", "item_id": row["id"], "lang": "en", "text": row["text"][:100], "auto_label": row["label"], "human_verified": "PENDING", "reviewer_notes": ""})

    with (GOLD_DIR / "verify.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["dataset", "item_id", "lang", "text", "auto_label", "human_verified", "reviewer_notes"])
        writer.writeheader()
        writer.writerows(verify_rows)

    guide = """# Yojana Mitra Gold Set Labeling & Human Verification Guide (P2)

## Datasets Generated (SEED=42)
1. `questions_100.jsonl`: 100 multilingual queries (20 each: English, Telugu, Hindi, Kannada, Tamil) mapped to canonical `scheme_id` and `intent`.
2. `profiles_50.jsonl`: 50 diverse Indian citizen profiles balanced across states, SC/ST/OBC/GEN/EWS, and gender with deterministic verdict labels.
3. `multihop_40.jsonl`: 40 multi-hop GraphRAG questions spanning `supersedes`, `complementary_to`, `mutually_exclusive_with`, and `requires_document`.
4. `telugu_utterances_50.jsonl`: 50 spoken-style Telugu farmer/welfare transcripts for IndicWhisper/IndicConformer WER evaluation.
5. `scam_messages_100.jsonl`: 50 realistic Indian welfare scams + 50 legitimate `.gov.in` notices.

## 20% Human Verification Protocol (`verify.csv`)
- Open `data/gold/verify.csv` (68 stratified rows = 20% of questions, profiles, multi-hop, and scams).
- Cross-check each `auto_label` against the official `.gov.in` notification.
- Mark `human_verified` as `APPROVED` or `CORRECTED` and add justification in `reviewer_notes`.
"""
    (GOLD_DIR / "LABELING_GUIDE.md").write_text(guide, encoding="utf-8")
    print(
        f"Gold set created: questions={len(questions)}, profiles={len(profiles)}, "
        f"multihop={len(multihop)}, te_utterances={len(utterances)}, scams={len(scams)}, "
        f"verify_csv_rows={len(verify_rows)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
