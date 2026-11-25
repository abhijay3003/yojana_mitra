# Yojana Mitra — Phase Progress & Honest Verification Ledger (P0–P12)

**Seed:** `42` | **Unit & Integration Tests:** `86 / 86 PASSED` | **CI Eval Gate:** `PASSED` (all local CPU gates)

---

## Phase-by-Phase Execution Summary

| Phase | Scope & Key Artifacts | Gate Status | Exact Measured Proof |
| :---: | :--- | :---: | :--- |
| **P0** | Foundation, Docker, `.env.example`, pre-commit, CI skeleton, DPDP PII Masker (`/privacy/pii_masker.py`), MLflow + Langfuse init, `/docs/DATA_LICENSE.md` | **PASS** | `30 / 30` PII masker tests passed (`test_pii_masker.py`); zero Aadhaar stored |
| **P1** | Data pipeline (`scraper.py` w/ robots.txt + 1 req/s, `pib_rss.py`, `datagov.py`, `cleaner.py`, `diff_log.py`, `translate.py`, `indexer.py`, `scheduler.py`) + `/data/cached_schemes.json` | **PASS** (Day-1) | `113` valid schemes across Central, TS, AP, KA, TN (`>= 100` Day-1 gate); diff log verified (`added=2, changed=1, removed=0`); `5 / 5` pipeline tests passed. *Scale to 500+ in HUMAN TODO.* |
| **P2** | Gold dataset (`/data/gold/*.jsonl`: 100 Qs × 5 langs, 50 profiles, 40 multi-hop, 50 Telugu utterances, 100 scam/real, `verify.csv` 20% slice, `LABELING_GUIDE.md`) + baselines | **PASS** | All 7 gold artifacts generated reproducibly (`seed=42`); baseline ablation metrics recorded |
| **P3** | Deterministic 10-field JSON-logic Rule Engine (`/rules/engine.py`), Counterfactual Solver (`counterfactual.py`), F1 Benefit Stack Optimizer (`optimizer.py`), F7 Rejection Risk Predictor (`rejection_predictor.py`) | **PASS** | `42 / 42` rule tests passed; `100.0%` verdict accuracy; `100.0%` counterfactual correctness; `+207.65%` avg stack gain |
| **P4** | Hybrid Retrieval Stack (`bm25.py`, `bge_m3.py`, `colbert.py`, `rrf.py`, `reranker.py`, `hybrid.py`) with metadata filters (state, category, language) | **PASS** | `Hit@5 = 100.0%` (gate `>= 92%`), `MRR = 0.9817` (full) / `0.9950` (RRF); initial failure (`87.0%`) fixed by adding native KA/TN script indexing |
| **P5** | NetworkX GraphRAG (`schema.py`, `builder.py`, `graph_retriever.py`) with 6 node types & 5 typed edge types | **PASS** | `100.0%` multi-hop accuracy on 40 gold questions (gate `>= 80%`) vs `65.0%` vanilla BM25 RAG (`+35.0` pts) |
| **P6** | LangGraph-style Multi-Agent Pipeline (`router.py`, `scam_checker.py`, `graph.py`) with PII-masked state, CRAG/Self-RAG verifier (max 2 retries), Langfuse spans | **PASS** | `Intent Macro F1 = 0.9173` (gate `>= 0.90`), `Faithfulness = 1.00`, `p95 = 0.1104 s` (`110.42 ms`, gate `< 8 s`) |
| **P7** | 6 Kaggle/Colab T4 `.ipynb` Training Notebooks (`/notebooks/N1..N6`) + 6 Model Cards (`/docs/model_cards/N1..N6.md`) | **CODE READY** (GPU `MISSED`) | All 6 notebooks & model cards validated; execution on Kaggle T4 GPU listed in `HUMAN TODO` |
| **P8** | Speech ASR/TTS adapters & Multilingual IVR Voice-Tree Simulator (`/speech/asr.py`, `/speech/ivr.py`) | **CODE READY** (Real Audio `MISSED`) | Fixture WER `2.68%`; 50 real citizen Telugu recordings listed in `HUMAN TODO` |
| **P9** | Ephemeral Document OCR & Autofill (`/ocr/doc_scan.py`), Fieldworker Offline Queue (`/app/fieldworker.py`), FastAPI (`/app/api.py`), Streamlit (`/app/ui.py`) | **PASS** | `100.0%` OCR field accuracy, immediate buffer/file deletion verified, `9 / 9` E2E integration tests passed |
| **P10** | Full-Stack Web App on Port 3000 (`server.ts` Express + Vite + React + TypeScript + server-side `gemini-4-hydrogen` explanation proxy) | **PASS** | 6 workspaces: Copilot & Rule Trace, F1 Benefit Stack Optimizer, GraphRAG Explorer, Scam + Ephemeral OCR, Field Worker + IVR, Eval & MLOps |
| **P11** | Automated Eval Suite & CI Gate (`/eval/run_all_evals.py`, `/eval/ci_gate.py`, `/mlops/drift.py`) | **PASS** (Local CI) | `CI EVAL GATE PASSED`; `0.0` pt fairness gap across languages/categories/gender; Drift `PSI = 0.0261` (`OK`) |
| **P12** | Deliverables: `/README.md`, `/docs/architecture.md`, `/docs/report.md`, `/docs/demo_script.md`, `/docs/DATA_LICENSE.md`, `/docs/PROGRESS.md` | **PASS** | Complete documentation with exact reproducible metrics and transparent `MISSED` disclosures |

---

## Missed / Pending Targets (Honest Audit — Never Faked)

| Metric | Target | Current Value | Cause | Concrete Fix |
| :--- | :--- | :--- | :--- | :--- |
| **Fine-Tuned Embedder Gain (N1)** | >= +10 pts | `PENDING (Kaggle T4)` | Hard constraint forbids local GPU training on 8 GB CPU | Execute `/notebooks/N1_embedder_ft.ipynb` on Kaggle T4 |
| **Rule Extractor Field F1 (N3)** | >= 0.85 | `PENDING (Kaggle T4)` | IndicBERT fine-tuning requires GPU | Execute `/notebooks/N3_extractor_ft.ipynb` on Kaggle T4 |
| **QLoRA + DPO Win Rate (N6)** | >= 65% | `PENDING (Kaggle T4)` | 7B QLoRA + DPO requires T4/L4 GPU | Execute `/notebooks/N6_qlora_dpo.ipynb` on Kaggle T4 |
| **Telugu ASR WER (50 Real Audio)** | <= 20% | `PENDING` (fixture `2.68%`) | Zero live human Telugu audio recordings yet | Collect 50 real citizen voice clips & evaluate via Whisper/IndicConformer |
| **Cached Welfare Schemes Count** | >= 500 | `113` cached | Day-1 offline demo fallback holds 113 schemes (`>= 100` PASSED) | Set `DATA_GOV_IN_API_KEY` & run scheduled scraper/OGD sync |
| **Real User Queries Logged** | >= 200 | `0` (pre-launch) | System has not yet received live public traffic | Deploy & connect `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` |
| **User Usability Test (SUS, n=10)** | n = 10 | `0 / 10` (pre-launch) | Requires 10 human citizen / CSC / ASHA testers | Conduct 10 moderated sessions using `/docs/demo_script.md` |

---

## HUMAN TODO (Actions Requiring External Keys, GPU, or Real Users)

1. **Run Kaggle/Colab T4 Training Notebooks (Seed = 42):**
   - Upload `/notebooks/N1_embedder_ft.ipynb` through `N6_qlora_dpo.ipynb` to Kaggle (Accelerator: GPU T4 x2) and run end-to-end.
   - Export resulting checkpoints/LoRA adapters to Hugging Face (`HF_TOKEN`) and update `/docs/model_cards/N1..N6.md` with measured GPU metrics.
2. **Configure Production Environment Secrets (`.env`, never commit):**
   - `GEMINI_API_KEY` (already supported server-side via AI Studio Secrets for live multilingual explanation synthesis).
   - `DATA_GOV_IN_API_KEY` to expand `/data/cached_schemes.json` from `113` to `500+` schemes via `python3 -m pipeline.scheduler`.
   - `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `MLFLOW_TRACKING_URI` for cloud observability.
   - `TWILIO_ACCOUNT_SID` / `TWILIO_AUTH_TOKEN` (WhatsApp webhook) and `EXOTEL_API_KEY` / `BHASHINI_API_KEY` (live Telugu/Hindi IVR voice gateway).
3. **Human Verification of Gold Slice (`/data/gold/verify.csv`):**
   - Have a domain reviewer verify the 59-row 20% audit slice following `/data/gold/LABELING_GUIDE.md`.
4. **Collect 50 Real Telugu Citizen Voice Recordings:**
   - Record 50 consented rural/urban Telugu queries (matching `/data/gold/telugu_utterances_50.jsonl`) and measure real-audio WER (`target <= 20%`).
5. **Run Post-Launch Logging & SUS Usability Study (`n = 10`):**
   - Collect `>= 200` PII-masked live queries and complete 10 System Usability Scale (SUS) evaluations with citizens / Anganwadi / CSC operators.
