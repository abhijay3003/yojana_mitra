# Model Card: N5: Welfare Scam Message Classifier (XLM-RoBERTa / DistilBERT-multilingual)

## Model Overview
- **Artifact ID**: `N5_scam_clf`
- **Base Checkpoint**: `distilbert-base-multilingual-cased`
- **Target HF Hub Repo**: `yojana-mitra/welfare-scam-detector-v1`
- **Training Notebook**: `notebooks/N5_scam_clf.ipynb`
- **Deterministic Seed**: `42`

## Training Data & Privacy (DPDP Act 2023)
- **Dataset**: 2,000 WhatsApp/SMS welfare scam & legitimate .gov.in notice examples
- **PII Safeguard**: All citizen-style queries and OCR fixtures pass through `/privacy/pii_masker.py` prior to tokenization; zero Aadhaar numbers or personal identifiers enter training corpora.

## Objective & Target Metrics
- **Loss / Recipe**: Binary CrossEntropyLoss with class weighting
- **Target Gate**: Scam F1 >= 0.92
- **Current Status**: Notebook validated syntactically; full Kaggle T4 GPU training listed under `HUMAN TODO` in `docs/PROGRESS.md`.

## Intended Use & Limitations
- Used strictly for retrieval, routing, extraction, scam screening, or grounded multilingual explanation.
- **Hard Architectural Guardrail**: Never authorized to override deterministic eligibility verdicts produced by `/rules/engine.py`.
