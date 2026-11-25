"""P0 Gate Test Suite: 30 unit tests for Yojana Mitra PII Masker.

Compatible with both `pytest` and `python3 -m unittest`.
"""

from __future__ import annotations

import unittest

from privacy.pii_masker import (
    AADHAAR_TOKEN,
    EMAIL_TOKEN,
    NAME_TOKEN,
    PAN_TOKEN,
    PHONE_TOKEN,
    mask_dict,
    mask_pii,
)


class TestPIIMasker(unittest.TestCase):
    """30 strict test cases covering Aadhaar, Phone, PAN, Email, Name, and safe non-PII."""

    # --- Aadhaar (7 cases) ---
    def test_01_aadhaar_spaced(self) -> None:
        res = mask_pii("My Aadhaar is 2345 6789 0123.")
        self.assertIn(AADHAAR_TOKEN, res.masked_text)
        self.assertNotIn("2345 6789 0123", res.masked_text)

    def test_02_aadhaar_hyphenated(self) -> None:
        res = mask_pii("UID: 9876-5432-1098 verified")
        self.assertIn(AADHAAR_TOKEN, res.masked_text)
        self.assertNotIn("9876-5432-1098", res.masked_text)

    def test_03_aadhaar_compact(self) -> None:
        res = mask_pii("Check eligibility for 456789012345")
        self.assertIn(AADHAAR_TOKEN, res.masked_text)
        self.assertEqual(res.counts.get("aadhaar"), 1)

    def test_04_aadhaar_telugu_label(self) -> None:
        res = mask_pii("నా ఆధార్: 3456 7890 1234 ఉంది")
        self.assertIn(AADHAAR_TOKEN, res.masked_text)
        self.assertNotIn("3456", res.masked_text)

    def test_05_aadhaar_hindi_label(self) -> None:
        res = mask_pii("मेरा आधार नंबर 5678 1234 9012 है")
        self.assertIn(AADHAAR_TOKEN, res.masked_text)
        self.assertNotIn("5678", res.masked_text)

    def test_06_aadhaar_labeled_leading_one(self) -> None:
        res = mask_pii("Aadhaar No: 1234 5678 9012")
        self.assertIn(AADHAAR_TOKEN, res.masked_text)
        self.assertNotIn("1234 5678 9012", res.masked_text)

    def test_07_multiple_aadhaar_numbers(self) -> None:
        res = mask_pii("Husband 2233 4455 6677 and wife 3344 5566 7788")
        self.assertEqual(res.masked_text.count(AADHAAR_TOKEN), 2)

    # --- Phone (6 cases) ---
    def test_08_phone_plain_10_digit(self) -> None:
        res = mask_pii("Call me on 9876543210 for status")
        self.assertIn(PHONE_TOKEN, res.masked_text)
        self.assertNotIn("9876543210", res.masked_text)

    def test_09_phone_plus91_hyphen(self) -> None:
        res = mask_pii("WhatsApp +91-9123456789")
        self.assertIn(PHONE_TOKEN, res.masked_text)
        self.assertNotIn("9123456789", res.masked_text)

    def test_10_phone_plus91_space(self) -> None:
        res = mask_pii("Mobile: +91 87654 32109")
        self.assertIn(PHONE_TOKEN, res.masked_text)
        self.assertNotIn("87654", res.masked_text)

    def test_11_phone_leading_zero(self) -> None:
        res = mask_pii("Dial 07890123456 immediately")
        self.assertIn(PHONE_TOKEN, res.masked_text)
        self.assertNotIn("7890123456", res.masked_text)

    def test_12_phone_6_series(self) -> None:
        res = mask_pii("Contact 6301234567")
        self.assertIn(PHONE_TOKEN, res.masked_text)
        self.assertEqual(res.counts.get("phone"), 1)

    def test_13_phone_spaced_3_3_4(self) -> None:
        res = mask_pii("Number 998 877 6655")
        self.assertIn(PHONE_TOKEN, res.masked_text)

    # --- PAN (4 cases) ---
    def test_14_pan_standard(self) -> None:
        res = mask_pii("My PAN is ABCDE1234F")
        self.assertIn(PAN_TOKEN, res.masked_text)
        self.assertNotIn("ABCDE1234F", res.masked_text)

    def test_15_pan_in_sentence(self) -> None:
        res = mask_pii("Submitted BNZAA2318J for KYC verification")
        self.assertIn(PAN_TOKEN, res.masked_text)
        self.assertEqual(res.counts.get("pan"), 1)

    def test_16_pan_lowercase_not_false_positive(self) -> None:
        res = mask_pii("scheme code abcde1234f is not uppercase PAN")
        self.assertNotIn(PAN_TOKEN, res.masked_text)

    def test_17_two_pans(self) -> None:
        res = mask_pii("PAN1: AAAAA1111A, PAN2: BBBBB2222B")
        self.assertEqual(res.masked_text.count(PAN_TOKEN), 2)

    # --- Email (4 cases) ---
    def test_18_email_gmail(self) -> None:
        res = mask_pii("Send PDF to lakshmi.devi@gmail.com")
        self.assertIn(EMAIL_TOKEN, res.masked_text)
        self.assertNotIn("lakshmi.devi@gmail.com", res.masked_text)

    def test_19_email_gov_in(self) -> None:
        res = mask_pii("Forwarded to officer_ts@telangana.gov.in")
        self.assertIn(EMAIL_TOKEN, res.masked_text)

    def test_20_email_with_digits_no_phone_leak(self) -> None:
        res = mask_pii("user9876543210@example.org")
        self.assertEqual(res.masked_text, EMAIL_TOKEN)
        self.assertEqual(res.counts.get("email"), 1)
        self.assertNotIn("phone", res.counts)

    def test_21_email_plus_tag(self) -> None:
        res = mask_pii("ravi+kisan@yahoo.co.in")
        self.assertEqual(res.masked_text, EMAIL_TOKEN)

    # --- Multilingual Names (4 cases) ---
    def test_22_name_english_my_name_is(self) -> None:
        res = mask_pii("My name is Lakshmi Devi and I farm in Warangal.")
        self.assertIn(NAME_TOKEN, res.masked_text)
        self.assertNotIn("Lakshmi Devi", res.masked_text)

    def test_23_name_applicant_label(self) -> None:
        res = mask_pii("Applicant Name: Ramesh Kumar, Income 120000")
        self.assertIn(NAME_TOKEN, res.masked_text)
        self.assertNotIn("Ramesh Kumar", res.masked_text)

    def test_24_name_telugu(self) -> None:
        res = mask_pii("నా పేరు లక్ష్మి దేవి నేను రైతును")
        self.assertIn(NAME_TOKEN, res.masked_text)
        self.assertNotIn("లక్ష్మి", res.masked_text)

    def test_25_name_hindi(self) -> None:
        res = mask_pii("मेरा नाम सीता देवी है")
        self.assertIn(NAME_TOKEN, res.masked_text)
        self.assertNotIn("सीता", res.masked_text)

    # --- Safe non-PII preservation & compound inputs (5 cases) ---
    def test_26_preserve_income_and_land_numbers(self) -> None:
        text = "Annual income Rs 180000, land 2.5 acres, age 42, SC category"
        res = mask_pii(text)
        self.assertEqual(res.masked_text, text)
        self.assertFalse(res.had_pii)

    def test_27_preserve_scheme_year_and_pin(self) -> None:
        text = "Telangana PIN 506001 PM-KISAN 2026 Rs 6000 per year"
        res = mask_pii(text)
        self.assertEqual(res.masked_text, text)
        self.assertFalse(res.had_pii)

    def test_28_compound_all_five_pii_types(self) -> None:
        text = (
            "My name is Kiran Rao, Aadhaar 3456 7890 1234, PAN ABCDE1234F, "
            "phone +91 9876543210, email kiran@example.com."
        )
        res = mask_pii(text)
        for token in (NAME_TOKEN, AADHAAR_TOKEN, PAN_TOKEN, PHONE_TOKEN, EMAIL_TOKEN):
            self.assertIn(token, res.masked_text)
        self.assertEqual(len(res.redacted_types), 5)

    def test_29_empty_string_handling(self) -> None:
        res = mask_pii("")
        self.assertEqual(res.masked_text, "")
        self.assertFalse(res.had_pii)

    def test_30_mask_dict_never_stores_aadhaar_key(self) -> None:
        payload = {
            "aadhaar_number": "2345 6789 0123",
            "query": "Call 9876543210",
            "nested": {"email": "farmer@test.in", "income": 150000},
        }
        cleaned = mask_dict(payload)
        self.assertEqual(cleaned["aadhaar_number"], AADHAAR_TOKEN)
        self.assertEqual(cleaned["query"], f"Call {PHONE_TOKEN}")
        self.assertEqual(cleaned["nested"]["email"], EMAIL_TOKEN)  # type: ignore[index]
        self.assertEqual(cleaned["nested"]["income"], 150000)  # type: ignore[index]


if __name__ == "__main__":
    unittest.main()
