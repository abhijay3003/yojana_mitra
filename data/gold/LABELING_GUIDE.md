# Yojana Mitra Gold Set Labeling & Human Verification Guide (P2)

## Datasets Generated (SEED=42)
1. `questions_100.jsonl`: 100 multilingual queries (20 each: English, Telugu, Hindi, Kannada, Tamil) mapped to canonical `scheme_id` and `intent`.
2. `profiles_50.jsonl`: 50 diverse Indian citizen profiles balanced across states, SC/ST/OBC/GEN/EWS, and gender with deterministic verdict labels.
3. `multihop_40.jsonl`: 40 multi-hop GraphRAG questions spanning `supersedes`, `complementary_to`, `mutually_exclusive_with`, and `requires_document`.
4. `telugu_utterances_50.jsonl`: 50 spoken-style Telugu farmer/welfare transcripts for IndicWhisper/IndicConformer WER evaluation.
5. `scam_messages_100.jsonl`: 50 realistic Indian welfare scams + 50 legitimate `.gov.in` notices.

## 20% Human Verification Protocol (`verify.csv`)
- Open `data/gold/verify.csv` (68 stratified rows = 20% of questions, profiles, multi-hop, and scams).
- Cross-check each `auto_label` against the official `.gov.in` notification.
- Mark `human_verified` as `APPROVED` or `CORRECTED` and add justification in `reviewer_notes`.
