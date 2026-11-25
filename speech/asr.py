"""P8 Speech ASR (AI4Bharat IndicWhisper / IndicConformer wrapper) and WER calculation."""

from __future__ import annotations

from typing import List


def word_error_rate(reference: str, hypothesis: str) -> float:
    """Compute exact Levenshtein Word Error Rate (WER) between reference and hypothesis."""
    r = reference.strip().split()
    h = hypothesis.strip().split()
    if not r:
        return 0.0 if not h else 1.0
    dp: List[List[int]] = [[0] * (len(h) + 1) for _ in range(len(r) + 1)]
    for i in range(len(r) + 1):
        dp[i][0] = i
    for j in range(len(h) + 1):
        dp[0][j] = j
    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            cost = 0 if r[i - 1] == h[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)
    return round(dp[len(r)][len(h)] / len(r), 4)
