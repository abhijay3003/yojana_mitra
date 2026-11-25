# Model Card: N2: Cross-Encoder Reranker Fine-Tuning (BAAI/bge-reranker-v2-m3 on Hard Negatives)

## Model Overview
- **Artifact ID**: `N2_reranker_ft`
- **Base Checkpoint**: `BAAI/bge-reranker-v2-m3`
- **Target HF Hub Repo**: `yojana-mitra/bge-reranker-v2-m3-welfare-v1`
- **Training Notebook**: `notebooks/N2_reranker_ft.ipynb`
- **Deterministic Seed**: `42`

## Training Data & Privacy (DPDP Act 2023)
- **Dataset**: Hard negatives mined from SQLite thumbs-down feedback logs + cross-state confusers
- **PII Safeguard**: All citizen-style queries and OCR fixtures pass through `/privacy/pii_masker.py` prior to tokenization; zero Aadhaar numbers or personal identifiers enter training corpora.

## Objective & Target Metrics
- **Loss / Recipe**: BCEWithLogitsLoss over (query, positive_scheme, hard_negative_scheme) triples
- **Target Gate**: MRR@5 improvement on multilingual cross-state disambiguation
- **Current Status**: Notebook validated syntactically; full Kaggle T4 GPU training listed under `HUMAN TODO` in `docs/PROGRESS.md`.

## Intended Use & Limitations
- Used strictly for retrieval, routing, extraction, scam screening, or grounded multilingual explanation.
- **Hard Architectural Guardrail**: Never authorized to override deterministic eligibility verdicts produced by `/rules/engine.py`.
