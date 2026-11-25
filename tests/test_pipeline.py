"""P1 Gate Tests: Scheme catalog validation (>=100 valid schemes), deduplication, and diff log."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from pipeline.cleaner import compute_diff_log, dedupe_schemes, validate_scheme_schema
from pipeline.indexer import load_cached_schemes
from pipeline.translate import detect_language


class TestDataPipeline(unittest.TestCase):
    """Verify P1 data pipeline gates."""

    def test_cached_schemes_count_and_schema(self) -> None:
        schemes = load_cached_schemes()
        self.assertGreaterEqual(len(schemes), 100, "Must cache at least 100 schemes on day 1")
        for s in schemes:
            errs = validate_scheme_schema(s)
            self.assertEqual(errs, [], f"Schema errors for {s.get('scheme_id')}: {errs}")

    def test_no_duplicate_scheme_ids(self) -> None:
        schemes = load_cached_schemes()
        ids = [s["scheme_id"] for s in schemes]
        self.assertEqual(len(ids), len(set(ids)))
        doubled = dedupe_schemes(schemes + schemes[:5])
        self.assertEqual(len(doubled), len(schemes))

    def test_diff_log_detects_new_changed_removed(self) -> None:
        schemes = load_cached_schemes()
        prev = schemes[:5]
        curr = [dict(s) for s in schemes[1:6]]
        curr[0]["annual_benefit_inr"] = int(curr[0]["annual_benefit_inr"]) + 500
        diff = compute_diff_log(prev, curr)
        self.assertEqual(diff["summary"]["added"], 1)
        self.assertEqual(diff["summary"]["changed"], 1)
        self.assertEqual(diff["summary"]["removed"], 1)

    def test_diff_log_artifact_exists(self) -> None:
        path = Path("data/processed/diff_log.json")
        self.assertTrue(path.exists())
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertGreaterEqual(data["total_schemes"], 100)

    def test_language_detection_five_languages(self) -> None:
        self.assertEqual(detect_language("తెలంగాణ రైతు భరోసా అర్హతలు ఏమిటి?"), "te")
        self.assertEqual(detect_language("पीएम किसान योजना की पात्रता क्या है?"), "hi")
        self.assertEqual(detect_language("ಗೃಹ ಲಕ್ಷ್ಮಿ ಯೋಜನೆಗೆ ಅರ್ಜಿ ಹೇಗೆ?"), "kn")
        self.assertEqual(detect_language("கலைஞர் மகளிர் உரிமைத் தொகை தகுதி என்ன?"), "ta")
        self.assertEqual(detect_language("Am I eligible for PM-KISAN?"), "en")


if __name__ == "__main__":
    unittest.main()
