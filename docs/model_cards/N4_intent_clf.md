# Model Card: N4: Multilingual Intent Classifier (distilbert-base-multilingual-cased)

## Model Overview
- **Artifact ID**: `N4_intent_clf`
- **Base Checkpoint**: `distilbert-base-multilingual-cased`
- **Target HF Hub Repo**: `yojana-mitra/distilbert-welfare-intent-v1`
- **Training Notebook**: `notebooks/N4_intent_clf.ipynb`
- **Deterministic Seed**: `42`

## Training Data & Privacy (DPDP Act 2023)
- **Dataset**: 1,500 multilingual queries across 5 classes {eligibility, documents, how_to_apply, status, scam_check}
- **PII Safeguard**: All citizen-style queries and OCR fixtures pass through `/privacy/pii_masker.py` prior to tokenization; zero Aadhaar numbers or personal identifiers enter training corpora.

## Objective & Target Metrics
- **Loss / Recipe**: CrossEntropyLoss (5-class classification)
- **Target Gate**: Macro F1 >= 0.90 across all 5 languages
- **Current Status**: Notebook validated syntactically; full Kaggle T4 GPU training listed under `HUMAN TODO` in `docs/PROGRESS.md`.

## Intended Use & Limitations
- Used strictly for retrieval, routing, extraction, scam screening, or grounded multilingual explanation.
- **Hard Architectural Guardrail**: Never authorized to override deterministic eligibility verdicts produced by `/rules/engine.py`.
