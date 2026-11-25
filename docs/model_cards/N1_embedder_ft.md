# Model Card: N1: Multilingual Embedder Fine-Tuning (intfloat/multilingual-e5-small / BGE-M3 Head)

## Model Overview
- **Artifact ID**: `N1_embedder_ft`
- **Base Checkpoint**: `intfloat/multilingual-e5-small`
- **Target HF Hub Repo**: `yojana-mitra/multilingual-e5-welfare-v1`
- **Training Notebook**: `notebooks/N1_embedder_ft.ipynb`
- **Deterministic Seed**: `42`

## Training Data & Privacy (DPDP Act 2023)
- **Dataset**: 3,000+ synthetic multilingual query-scheme pairs (20% human-verified via data/gold/verify.csv)
- **PII Safeguard**: All citizen-style queries and OCR fixtures pass through `/privacy/pii_masker.py` prior to tokenization; zero Aadhaar numbers or personal identifiers enter training corpora.

## Objective & Target Metrics
- **Loss / Recipe**: MultipleNegativesRankingLoss (sentence-transformers==3.3.1)
- **Target Gate**: Hit@5 gain >= +10 points over zero-shot base on data/gold/questions_100.jsonl
- **Current Status**: Notebook validated syntactically; full Kaggle T4 GPU training listed under `HUMAN TODO` in `docs/PROGRESS.md`.

## Intended Use & Limitations
- Used strictly for retrieval, routing, extraction, scam screening, or grounded multilingual explanation.
- **Hard Architectural Guardrail**: Never authorized to override deterministic eligibility verdicts produced by `/rules/engine.py`.
