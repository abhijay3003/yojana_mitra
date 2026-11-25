"""P3 Gate Test Suite: 42 deterministic rule engine, counterfactual, optimizer, and rejection tests."""

from __future__ import annotations

import unittest
from typing import Any, Dict

from pipeline.indexer import load_cached_schemes
from rules.counterfactual import generate_counterfactual
from rules.engine import evaluate, validate_rules_against_schema
from rules.optimizer import optimize_benefit_stack
from rules.rejection_predictor import predict_rejection_risk


class TestRuleEngineAndCounterfactuals(unittest.TestCase):
    """42 comprehensive tests verifying P3 gates and F1/F7 correctness."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.schemes = load_cached_schemes()
        cls.by_id = {s["scheme_id"]: s for s in cls.schemes}
        cls.ts_sc_woman_farmer: Dict[str, Any] = {
            "age": 38,
            "income": 140000,
            "state": "Telangana",
            "category": "SC",
            "gender": "Female",
            "occupation": "Farmer",
            "land": 2.0,
            "disability": False,
            "bpl": True,
            "residence": "Rural",
        }

    # --- Schema validation (4 cases) ---
    def test_01_all_cached_scheme_rules_valid(self) -> None:
        for s in self.schemes:
            errs = validate_rules_against_schema(s["rules"])
            self.assertEqual(errs, [], f"Invalid rules in {s['scheme_id']}: {errs}")

    def test_02_reject_invalid_field(self) -> None:
        errs = validate_rules_against_schema([{"field": "zodiac", "op": "==", "value": "Leo"}])
        self.assertTrue(len(errs) > 0)

    def test_03_reject_invalid_operator(self) -> None:
        errs = validate_rules_against_schema([{"field": "age", "op": "LIKE", "value": 20}])
        self.assertTrue(len(errs) > 0)

    def test_04_reject_in_without_list(self) -> None:
        errs = validate_rules_against_schema([{"field": "category", "op": "in", "value": "SC"}])
        self.assertTrue(len(errs) > 0)

    # --- Telangana SC Woman Farmer core eligibility (8 cases) ---
    def test_05_ts_rythu_bharosa_eligible(self) -> None:
        res = evaluate(self.ts_sc_woman_farmer, self.by_id["TS_RYTHU_BHAROSA"])
        self.assertEqual(res["verdict"], "ELIGIBLE")
        self.assertEqual(res["match_score"], 100.0)

    def test_06_pm_kisan_eligible(self) -> None:
        res = evaluate(self.ts_sc_woman_farmer, self.by_id["IN_PM_KISAN"])
        self.assertEqual(res["verdict"], "ELIGIBLE")

    def test_07_ts_mahalakshmi_eligible(self) -> None:
        res = evaluate(self.ts_sc_woman_farmer, self.by_id["TS_MAHALAKSHMI"])
        self.assertEqual(res["verdict"], "ELIGIBLE")

    def test_08_ts_dalit_bandhu_eligible(self) -> None:
        res = evaluate(self.ts_sc_woman_farmer, self.by_id["TS_DALIT_BANDHU"])
        self.assertEqual(res["verdict"], "ELIGIBLE")

    def test_09_ts_rythu_bima_eligible(self) -> None:
        res = evaluate(self.ts_sc_woman_farmer, self.by_id["TS_RYTHU_BIMA"])
        self.assertEqual(res["verdict"], "ELIGIBLE")

    def test_10_ts_griha_jyothi_eligible(self) -> None:
        res = evaluate(self.ts_sc_woman_farmer, self.by_id["TS_GRIHA_JYOTHI"])
        self.assertEqual(res["verdict"], "ELIGIBLE")

    def test_11_ts_aasara_pension_not_eligible_age(self) -> None:
        res = evaluate(self.ts_sc_woman_farmer, self.by_id["TS_AASARA_PENSION"])
        self.assertEqual(res["verdict"], "NOT_ELIGIBLE")
        self.assertEqual(res["failed"][0]["field"], "age")

    def test_12_ka_gruha_lakshmi_not_eligible_state(self) -> None:
        res = evaluate(self.ts_sc_woman_farmer, self.by_id["KA_GRUHA_LAKSHMI"])
        self.assertEqual(res["verdict"], "NOT_ELIGIBLE")
        self.assertEqual(res["failed"][0]["field"], "state")

    # --- Boundary conditions across all 10 profile fields (14 cases) ---
    def test_13_income_exact_boundary_pass(self) -> None:
        p = dict(self.ts_sc_woman_farmer, income=200000)
        self.assertEqual(evaluate(p, self.by_id["TS_MAHALAKSHMI"])["verdict"], "ELIGIBLE")

    def test_14_income_one_rupee_over_fail(self) -> None:
        p = dict(self.ts_sc_woman_farmer, income=200001)
        self.assertEqual(evaluate(p, self.by_id["TS_MAHALAKSHMI"])["verdict"], "NOT_ELIGIBLE")

    def test_15_age_lower_boundary_pass(self) -> None:
        p = dict(self.ts_sc_woman_farmer, age=18)
        self.assertEqual(evaluate(p, self.by_id["TS_RYTHU_BHAROSA"])["verdict"], "ELIGIBLE")

    def test_16_age_under_18_fail(self) -> None:
        p = dict(self.ts_sc_woman_farmer, age=17)
        self.assertEqual(evaluate(p, self.by_id["TS_RYTHU_BHAROSA"])["verdict"], "NOT_ELIGIBLE")

    def test_17_age_upper_boundary_rythu_bima(self) -> None:
        p59 = dict(self.ts_sc_woman_farmer, age=59)
        p60 = dict(self.ts_sc_woman_farmer, age=60)
        self.assertEqual(evaluate(p59, self.by_id["TS_RYTHU_BIMA"])["verdict"], "ELIGIBLE")
        self.assertEqual(evaluate(p60, self.by_id["TS_RYTHU_BIMA"])["verdict"], "NOT_ELIGIBLE")

    def test_18_land_boundary_pass_and_fail(self) -> None:
        p_ok = dict(self.ts_sc_woman_farmer, land=0.5)
        p_fail = dict(self.ts_sc_woman_farmer, land=0.4)
        self.assertEqual(evaluate(p_ok, self.by_id["TS_RYTHU_BHAROSA"])["verdict"], "ELIGIBLE")
        self.assertEqual(evaluate(p_fail, self.by_id["TS_RYTHU_BHAROSA"])["verdict"], "NOT_ELIGIBLE")

    def test_19_gender_male_fails_mahalakshmi(self) -> None:
        p = dict(self.ts_sc_woman_farmer, gender="Male")
        self.assertEqual(evaluate(p, self.by_id["TS_MAHALAKSHMI"])["verdict"], "NOT_ELIGIBLE")

    def test_20_bpl_false_fails_ujjwala(self) -> None:
        p = dict(self.ts_sc_woman_farmer, bpl=False)
        self.assertEqual(evaluate(p, self.by_id["IN_UJJWALA"])["verdict"], "NOT_ELIGIBLE")

    def test_21_residence_urban_fails_pmay_gramin(self) -> None:
        p = dict(self.ts_sc_woman_farmer, residence="Urban")
        self.assertEqual(evaluate(p, self.by_id["IN_PMAY_GRAMIN"])["verdict"], "NOT_ELIGIBLE")

    def test_22_residence_urban_passes_pmay_urban(self) -> None:
        p = dict(self.ts_sc_woman_farmer, residence="Urban", income=250000)
        self.assertEqual(evaluate(p, self.by_id["IN_PMAY_URBAN"])["verdict"], "ELIGIBLE")

    def test_23_disability_true_passes_adip(self) -> None:
        p = dict(self.ts_sc_woman_farmer, disability=True, income=200000)
        self.assertEqual(evaluate(p, self.by_id["IN_ADIP_AIDS"])["verdict"], "ELIGIBLE")

    def test_24_disability_false_fails_igndps(self) -> None:
        self.assertEqual(evaluate(self.ts_sc_woman_farmer, self.by_id["IN_IGNDPS"])["verdict"], "NOT_ELIGIBLE")

    def test_25_category_sc_student_passes_nsp_sc(self) -> None:
        p = dict(self.ts_sc_woman_farmer, age=20, occupation="Student", income=180000)
        self.assertEqual(evaluate(p, self.by_id["IN_NSP_POST_MATRIC_SC"])["verdict"], "ELIGIBLE")

    def test_26_category_gen_fails_nsp_sc(self) -> None:
        p = dict(self.ts_sc_woman_farmer, age=20, occupation="Student", category="GEN")
        self.assertEqual(evaluate(p, self.by_id["IN_NSP_POST_MATRIC_SC"])["verdict"], "NOT_ELIGIBLE")

    # --- Missing fields / NEEDS_INFO (4 cases) ---
    def test_27_missing_income_returns_needs_info(self) -> None:
        p = dict(self.ts_sc_woman_farmer)
        del p["income"]
        res = evaluate(p, self.by_id["TS_MAHALAKSHMI"])
        self.assertEqual(res["verdict"], "NEEDS_INFO")
        self.assertEqual(res["missing"][0]["field"], "income")

    def test_28_missing_plus_failure_returns_not_eligible(self) -> None:
        p = dict(self.ts_sc_woman_farmer, gender="Male")
        del p["income"]
        res = evaluate(p, self.by_id["TS_MAHALAKSHMI"])
        self.assertEqual(res["verdict"], "NOT_ELIGIBLE")

    def test_29_empty_profile_returns_needs_info(self) -> None:
        res = evaluate({}, self.by_id["IN_PM_KISAN"])
        self.assertEqual(res["verdict"], "NEEDS_INFO")

    def test_30_case_insensitive_string_matching(self) -> None:
        p = dict(self.ts_sc_woman_farmer, state="telangana", gender="female")
        self.assertEqual(evaluate(p, self.by_id["TS_MAHALAKSHMI"])["verdict"], "ELIGIBLE")

    # --- Counterfactual correctness (6 cases) ---
    def test_31_counterfactual_income_reduction(self) -> None:
        p = dict(self.ts_sc_woman_farmer, income=260000)
        cf = generate_counterfactual(p, self.by_id["TS_MAHALAKSHMI"])
        self.assertFalse(cf["already_eligible"])
        self.assertTrue(cf["verified_eligible"])
        self.assertIn("200,000", cf["summary"])

    def test_32_counterfactual_already_eligible(self) -> None:
        cf = generate_counterfactual(self.ts_sc_woman_farmer, self.by_id["TS_RYTHU_BHAROSA"])
        self.assertTrue(cf["already_eligible"])
        self.assertTrue(cf["verified_eligible"])

    def test_33_counterfactual_multi_field_age_and_income(self) -> None:
        p = dict(self.ts_sc_woman_farmer, age=38, income=250000)
        cf = generate_counterfactual(p, self.by_id["TS_AASARA_PENSION"])
        self.assertTrue(cf["verified_eligible"])
        self.assertEqual(len(cf["changes"]), 2)

    def test_34_counterfactual_missing_fields_filled(self) -> None:
        p = {"state": "Telangana", "gender": "Female"}
        cf = generate_counterfactual(p, self.by_id["TS_MAHALAKSHMI"])
        self.assertTrue(cf["verified_eligible"])

    def test_35_counterfactual_land_increase(self) -> None:
        p = dict(self.ts_sc_woman_farmer, land=0.2)
        cf = generate_counterfactual(p, self.by_id["IN_PM_KUSUM"])
        self.assertTrue(cf["verified_eligible"])
        self.assertIn("land >= 1.0", cf["summary"])

    def test_36_counterfactual_state_karnataka(self) -> None:
        cf = generate_counterfactual(self.ts_sc_woman_farmer, self.by_id["KA_GRUHA_LAKSHMI"])
        self.assertTrue(cf["verified_eligible"])

    # --- Benefit-Stacking Optimizer & Rejection Predictor (6 cases) ---
    def test_37_optimizer_respects_mutual_exclusion(self) -> None:
        stack = optimize_benefit_stack(self.ts_sc_woman_farmer, self.schemes, max_schemes=5)
        ids = {s["scheme_id"] for s in stack["selected_schemes"]}
        # Rythu Bharosa and Rythu Bandhu Legacy are mutually exclusive
        self.assertFalse({"TS_RYTHU_BHAROSA", "TS_RYTHU_BANDHU_LEGACY"}.issubset(ids))
        # Dalit Bandhu and SC Subsidy Loan are mutually exclusive
        self.assertFalse({"TS_DALIT_BANDHU", "TS_SC_SUBSIDY_LOAN"}.issubset(ids))
        # Indiramma Indlu and PMAY Gramin are mutually exclusive
        self.assertFalse({"TS_INDIRAMMA_INDLU", "IN_PMAY_GRAMIN"}.issubset(ids))

    def test_38_optimizer_beats_naive_top1(self) -> None:
        stack = optimize_benefit_stack(self.ts_sc_woman_farmer, self.schemes, max_schemes=5)
        self.assertGreater(stack["total_annual_inr"], stack["naive_top1_inr"])
        self.assertGreater(stack["gain_vs_top1_pct"], 50.0)

    def test_39_optimizer_handles_zero_eligible(self) -> None:
        rich = {
            "age": 45, "income": 5000000, "state": "Other", "category": "GEN",
            "gender": "Male", "occupation": "Salaried", "land": 0.0,
            "disability": False, "bpl": False, "residence": "Urban",
        }
        stack = optimize_benefit_stack(rich, self.schemes, max_schemes=5)
        self.assertEqual(stack["total_annual_inr"], 0)

    def test_40_rejection_predictor_unseeded_bank_high_risk(self) -> None:
        pred = predict_rejection_risk(
            self.ts_sc_woman_farmer,
            self.by_id["TS_RYTHU_BHAROSA"],
            available_documents=["Aadhaar Card"],
            aadhaar_bank_seeded=False,
            certificate_age_months=18,
        )
        self.assertGreater(pred["rejection_probability"], 0.6)
        self.assertEqual(len(pred["top_3_reasons"]), 3)

    def test_41_rejection_predictor_clean_application_low_risk(self) -> None:
        scheme = self.by_id["IN_PM_KISAN"]
        pred = predict_rejection_risk(
            self.ts_sc_woman_farmer,
            scheme,
            available_documents=scheme["documents"],
            aadhaar_bank_seeded=True,
            certificate_age_months=3,
        )
        self.assertLess(pred["rejection_probability"], 0.30)

    def test_42_karnataka_and_tamil_nadu_state_isolation(self) -> None:
        ka_woman = dict(self.ts_sc_woman_farmer, state="Karnataka")
        tn_woman = dict(self.ts_sc_woman_farmer, state="Tamil Nadu")
        self.assertEqual(evaluate(ka_woman, self.by_id["KA_GRUHA_LAKSHMI"])["verdict"], "ELIGIBLE")
        self.assertEqual(evaluate(ka_woman, self.by_id["TN_KALAIGNAR_MAGALIR"])["verdict"], "NOT_ELIGIBLE")
        self.assertEqual(evaluate(tn_woman, self.by_id["TN_KALAIGNAR_MAGALIR"])["verdict"], "ELIGIBLE")


if __name__ == "__main__":
    unittest.main()
