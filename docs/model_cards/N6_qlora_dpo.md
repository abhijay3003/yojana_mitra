# Model Card: N6: QLoRA SFT + DPO Alignment (Qwen/Qwen2.5-7B-Instruct / Airavata)

## Model Overview
- **Artifact ID**: `N6_qlora_dpo`
- **Base Checkpoint**: `Qwen/Qwen2.5-7B-Instruct`
- **Target HF Hub Repo**: `yojana-mitra/qwen25-7b-welfare-explainer-dpo`
- **Training Notebook**: `notebooks/N6_qlora_dpo.ipynb`
- **Deterministic Seed**: `42`

## Training Data & Privacy (DPDP Act 2023)
- **Dataset**: 5,000+ trilingual (te/hi/en) grounded explanation pairs + DPO chosen (rule-faithful) vs rejected (hallucinated verdict) pairs
- **PII Safeguard**: All citizen-style queries and OCR fixtures pass through `/privacy/pii_masker.py` prior to tokenization; zero Aadhaar numbers or personal identifiers enter training corpora.

## Objective & Target Metrics
- **Loss / Recipe**: 4-bit NF4 QLoRA SFT (r=16, alpha=32) followed by DPO (beta=0.1)
- **Target Gate**: Win rate >= 65% vs base model on 200 prompts (LLM-as-judge) with 0 verdict overrides
- **Current Status**: Notebook validated syntactically; full Kaggle T4 GPU training listed under `HUMAN TODO` in `docs/PROGRESS.md`.

## Intended Use & Limitations
- Used strictly for retrieval, routing, extraction, scam screening, or grounded multilingual explanation.
- **Hard Architectural Guardrail**: Never authorized to override deterministic eligibility verdicts produced by `/rules/engine.py`.
