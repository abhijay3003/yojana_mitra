# Model Card: N3: Eligibility Rule Extractor (ai4bharat/indic-bert / mBERT Token Classification)

## Model Overview
- **Artifact ID**: `N3_extractor_ft`
- **Base Checkpoint**: `bert-base-multilingual-cased`
- **Target HF Hub Repo**: `yojana-mitra/mbert-eligibility-extractor-v1`
- **Training Notebook**: `notebooks/N3_extractor_ft.ipynb`
- **Deterministic Seed**: `42`

## Training Data & Privacy (DPDP Act 2023)
- **Dataset**: 500 labeled welfare scheme eligibility clauses mapped to 10-field /rules/schema.json
- **PII Safeguard**: All citizen-style queries and OCR fixtures pass through `/privacy/pii_masker.py` prior to tokenization; zero Aadhaar numbers or personal identifiers enter training corpora.

## Objective & Target Metrics
- **Loss / Recipe**: CrossEntropyLoss over BIO slot tags (AGE, INCOME, STATE, CATEGORY, GENDER, LAND, BPL)
- **Target Gate**: Field-level F1 >= 0.85
- **Current Status**: Notebook validated syntactically; full Kaggle T4 GPU training listed under `HUMAN TODO` in `docs/PROGRESS.md`.

## Intended Use & Limitations
- Used strictly for retrieval, routing, extraction, scam screening, or grounded multilingual explanation.
- **Hard Architectural Guardrail**: Never authorized to override deterministic eligibility verdicts produced by `/rules/engine.py`.
