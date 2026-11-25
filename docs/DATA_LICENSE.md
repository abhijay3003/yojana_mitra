# Yojana Mitra — Data License, Scraping Governance & ToS Review

**Compliance Framework**: Digital Personal Data Protection (DPDP) Act 2023 + Ethical Public-Data Harvesting Policy.

## 1. Scraping & Rate-Limiting Policy
- Every scraper in `/pipeline/` executes a `robots.txt` check (`urllib.robotparser`) prior to requesting any URL.
- Strict polite rate limit: **maximum 1 request/second** per domain with exponential backoff on HTTP 429/503.
- All raw HTTP responses are cached under `/data/raw/` with SHA-256 content hashes so unchanged pages are never re-fetched unnecessarily.
- Cached offline demo bundle (`/data/cached_schemes.json`) enables full zero-internet demo operation.

## 2. Source-by-Source ToS & Licensing Review

| Source | Access Method | License / Terms Review | Personal Data Handled? |
| :--- | :--- | :--- | :--- |
| `myscheme.gov.in` | Public JSON API discovery first; Playwright fallback only if no JSON endpoint responds | National Portal of India / MeitY public informational welfare catalog. Non-commercial educational/informational attribution required; links always point back to official `.gov.in` apply portals. | None (public scheme rules only) |
| `data.gov.in` | Official Open Government Data (OGD) API with `DATA_GOV_IN_API_KEY` | Government Open Data License – India (GODL). Attribution to respective Ministry/Department required. | None |
| `pib.gov.in` RSS | Official Press Information Bureau RSS feeds | Public government press releases; attributed with publication date and URL. | None |
| KA / AP / TS State Portals (`sevasindhu.karnataka.gov.in`, `telangana.gov.in`, `ap.gov.in`) | Polite Scrapy/Playwright crawler (`1 req/s`, `robots.txt` respected) | Public state welfare scheme notifications; informational redistribution with disclaimer & direct links to state portals. | None |
| AI4Bharat Samanantar / IndicTrans2 | Public research models & parallel corpora (CC-BY-4.0 / MIT) | Open research license; attribution to AI4Bharat. | None |

## 3. Citizen Data & Privacy Guarantees (DPDP Act 2023)
1. **Purpose Limitation & Informed Consent**: Citizens are presented with an explicit DPDP Act 2023 consent notice before uploading documents or saving profiles for proactive alerts.
2. **Zero Aadhaar Persistence**: Raw Aadhaar numbers are redacted by `/privacy/pii_masker.py` and `src/lib/piiMasker.ts` before any log write or LLM invocation, and are never stored in SQLite or disk.
3. **Ephemeral Document Processing**: Uploaded income/caste/ration documents are processed in memory for structured field extraction and deleted immediately after extraction.
4. **Mandatory Informational Disclaimer**: Displayed persistently in the Web UI, Streamlit app, WhatsApp bot, and IVR transcripts:
   > *"Informational only. Verify on the official portal."*
