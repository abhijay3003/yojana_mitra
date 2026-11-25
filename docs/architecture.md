# Yojana Mitra — Neurosymbolic System Architecture

## 1. Core Architectural Principle
**Deterministic Rules Decide. LLMs Explain.**
Every eligibility verdict (`ELIGIBLE`, `NOT_ELIGIBLE`, `NEEDS_INFO`), counterfactual boundary edit, and mutual-exclusion benefit stack is computed strictly by symbolic engines (`/rules/engine.py`, `/rules/counterfactual.py`, `/rules/optimizer.py` and mirrored in `src/lib/engine.ts`). Hosted LLMs (`gemini-4-hydrogen` via server-side proxy) are restricted strictly to multilingual synthesis, document transcription, and accessible explanation grounded on verified rule traces.

## 2. End-to-End Neurosymbolic Flow (Mermaid)

```mermaid
flowchart TD
    U[Citizen / Field Worker / IVR Caller<br/>en · te · hi · kn · ta] --> PII[P0 PII Masker<br/>Aadhaar · Phone · PAN · Email · Name]
    PII --> R[P6 Router Node<br/>Language + Intent + Mode]

    R -->|scam_check| SC[F6 Scam Shield<br/>Domain/UPI/APK Analyzer + .gov.in Resolver]
    R -->|vector| HYB[P4 Hybrid Retrieval<br/>BM25 + BGE-M3 + ColBERT -> RRF -> Reranker]
    R -->|graph| GR[P5 Knowledge GraphRAG<br/>Scheme · Ministry · State · Document · Benefit]

    HYB --> RE[P3 Deterministic Rule Engine<br/>10-Field JSON Logic /rules/schema.json]
    GR --> RE

    RE --> CF[F2 Minimal-Change Counterfactual Solver<br/>Self-Verified via engine.evaluate]
    RE --> OPT[F1 Benefit-Stacking Optimizer<br/>CP-SAT / Exact Branch-and-Bound]
    RE --> REJ[F7 Rejection Risk Predictor<br/>Rule Margin + Docs + NPCI Seeding]

    RE --> EXP[Grounded Multilingual Explainer<br/>Server-Side Gemini 4 Hydrogen Proxy]
    CF --> EXP
    OPT --> EXP
    REJ --> EXP

    EXP --> VER[P6 CRAG / Self-RAG Verifier<br/>Faithfulness >= 0.80, Max 2 Retries]
    VER --> FG[F10 Form Guide & Official .gov.in Links]
    FG --> OUT[Web UI · Streamlit · WhatsApp · Missed-Call IVR]
    OUT --> FB[F8 SQLite/JSONL Feedback -> Weekly Hard-Negative Export]
```

## 3. Privacy & Security Boundaries (DPDP Act 2023)
1. **Ingress Redaction**: All text inputs pass through `mask_pii()` before any trace span, log write, or LLM API call.
2. **Zero Aadhaar Persistence**: Keys containing `aadhaar`/`aadhar` are stripped on ingress and never stored in SQLite or JSONL logs.
3. **Ephemeral Document Processing**: Uploaded certificates in F3 Document Scan are processed strictly in memory and discarded immediately after structured field extraction.
4. **Server-Side API Isolation**: `GEMINI_API_KEY` stays strictly on the Express/FastAPI server; client bundles never access API keys or import `@google/genai`.
