"""End-to-end integration tests for P4-P9 (Retrieval, GraphRAG, Agents, IVR, OCR, Fieldworker, Notebooks)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from agents.graph import YojanaMitraAgentGraph
from agents.scam_checker import analyze_scam_message
from app.fieldworker import match_diff_alerts, screen_families_csv
from graph.graph_retriever import GraphRAGRetriever
from ocr.doc_scan import extract_profile_from_document_text
from pipeline.indexer import load_cached_schemes
from retrieval.hybrid import HybridRetriever
from speech.asr import word_error_rate
from speech.ivr import handle_ivr_webhook


class TestEndToEndSystems(unittest.TestCase):
    """Verify P4, P5, P6, P7, P8, and P9 gates."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.schemes = load_cached_schemes()
        cls.demo_profile = {
            "age": 38, "income": 140000, "state": "Telangana", "category": "SC",
            "gender": "Female", "occupation": "Farmer", "land": 2.0,
            "disability": False, "bpl": True, "residence": "Rural",
        }

    def test_p4_hybrid_multilingual_retrieval(self) -> None:
        ret = HybridRetriever(self.schemes)
        te_res = ret.search("తెలంగాణ రైతు భరోసా అర్హతలు ఏమిటి?", top_k=5)
        self.assertIn("TS_RYTHU_BHAROSA", [s["scheme_id"] for s, _ in te_res])
        hi_res = ret.search("पीएम किसान सम्मान निधि 6000", top_k=5)
        self.assertIn("IN_PM_KISAN", [s["scheme_id"] for s, _ in hi_res])
        kn_res = ret.search("ಗೃಹ ಲಕ್ಷ್ಮಿ ಯೋಜನೆ ಕರ್ನಾಟಕ", top_k=5)
        self.assertIn("KA_GRUHA_LAKSHMI", [s["scheme_id"] for s, _ in kn_res])
        ta_res = ret.search("கலைஞர் மகளிர் உரிமைத் தொகை", top_k=5)
        self.assertIn("TN_KALAIGNAR_MAGALIR", [s["scheme_id"] for s, _ in ta_res])

    def test_p5_graphrag_supersedes_and_complementary(self) -> None:
        gr = GraphRAGRetriever(self.schemes)
        res = gr.multi_hop_retrieve(
            "Which scheme superseded Rythu Bandhu and complements it?",
            hop_hint="supersedes",
            anchor_hint="TS_RYTHU_BANDHU_LEGACY",
        )
        self.assertIn("TS_RYTHU_BHAROSA", res["scheme_ids"])
        self.assertIn("IN_PM_KISAN", res["scheme_ids"])

    def test_p6_agent_graph_pii_masked_trace_and_latency(self) -> None:
        agent = YojanaMitraAgentGraph(self.schemes)
        res = agent.run(
            "My Aadhaar is 2345 6789 0123. Am I eligible for Telangana Rythu Bharosa?",
            profile=self.demo_profile,
        )
        self.assertNotIn("2345 6789 0123", res["safe_query"])
        self.assertIn("aadhaar", res["pii_redacted"])
        self.assertGreaterEqual(res["faithfulness"], 0.80)
        self.assertLess(res["latency_ms"], 8000.0)

    def test_p6_scam_shield_detection(self) -> None:
        scam = analyze_scam_message("CONGRATULATIONS! Pay Rs 499 UPI fee at http://pm-free-cash.xyz now!")
        self.assertEqual(scam["verdict"], "SCAM")
        real = analyze_scam_message("Verify PM-KISAN status free at https://pmkisan.gov.in. No registration fee is charged.")
        self.assertEqual(real["verdict"], "LEGITIMATE")

    def test_p7_six_valid_notebooks_and_model_cards_exist(self) -> None:
        nbs = list(Path("notebooks").glob("N*.ipynb"))
        cards = list(Path("docs/model_cards").glob("N*.md"))
        self.assertEqual(len(nbs), 6)
        self.assertEqual(len(cards), 6)
        for nb in nbs:
            parsed = json.loads(nb.read_text(encoding="utf-8"))
            self.assertIn("cells", parsed)
            self.assertGreaterEqual(len(parsed["cells"]), 3)

    def test_p8_speech_wer_and_ivr_webhook(self) -> None:
        self.assertEqual(word_error_rate("రైతు భరోసా పథకం", "రైతు భరోసా పథకం"), 0.0)
        self.assertAlmostEqual(word_error_rate("a b c d", "a b x d"), 0.25)
        menu = handle_ivr_webhook(digit="1", transcript="")
        self.assertEqual(menu["stage"], "LANGUAGE_MENU")
        self.assertEqual(menu["lang"], "te")
        ans = handle_ivr_webhook(digit="1", transcript="తెలంగాణ రైతు భరోసా", profile=self.demo_profile)
        self.assertEqual(ans["stage"], "VOICE_ANSWER")

    def test_p9_ocr_autofill_masks_aadhaar(self) -> None:
        out = extract_profile_from_document_text(
            "Telangana MeeSeva Income Certificate. Aadhaar: 4567 8901 2345. Annual Income: Rs 1,40,000. SC Category. Village Warangal."
        )
        self.assertFalse(out["aadhaar_stored"])
        self.assertTrue(out["raw_document_deleted"])
        self.assertNotIn("4567 8901 2345", out["masked_ocr_preview"])
        self.assertEqual(out["extracted_profile"]["income"], 140000)

    def test_p9_fieldworker_50_families_batch_csv(self) -> None:
        header = "family_id,age,income,state,category,gender,occupation,land,disability,bpl,residence\n"
        rows = [f"FAM_{i:03d},38,140000,Telangana,SC,Female,Farmer,2.0,false,true,Rural" for i in range(1, 51)]
        res = screen_families_csv(header + "\n".join(rows))
        self.assertEqual(res["families_screened"], 50)
        self.assertGreater(res["aggregate_annual_welfare_inr"], 1000000)

    def test_p9_proactive_diff_alerts(self) -> None:
        diff_log = json.loads(Path("data/processed/diff_log.json").read_text(encoding="utf-8"))
        alerts = match_diff_alerts([{"label": "Lakshmi (Warangal)", "profile": self.demo_profile, "channel": "whatsapp"}], diff_log)
        self.assertGreaterEqual(len(alerts), 1)


if __name__ == "__main__":
    unittest.main()
