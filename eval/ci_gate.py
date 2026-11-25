"""P11 CI Evaluation Gate: fails build if Hit@5 drops below baseline or Verdict Accuracy < 95%."""

from __future__ import annotations

import sys

from eval.run_all_evals import run_all


def main() -> int:
    report = run_all()
    hit5 = report["retrieval"]["ablations"][-1]["hit_at_5"]
    verdict_acc = report["rules"]["verdict_acc"]
    cf_acc = report["rules"]["counterfactual_acc"]
    mh_acc = report["multihop"]["graphrag_acc"]

    failures = []
    if hit5 < 92.0:
        failures.append(f"Hit@5 {hit5}% < 92.0% threshold")
    if verdict_acc < 95.0:
        failures.append(f"Verdict accuracy {verdict_acc}% < 95.0% threshold")
    if cf_acc < 100.0:
        failures.append(f"Counterfactual correctness {cf_acc}% < 100.0% threshold")
    if mh_acc < 80.0:
        failures.append(f"GraphRAG multi-hop accuracy {mh_acc}% < 80.0% threshold")

    if failures:
        print("CI EVAL GATE FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1

    print(
        f"CI EVAL GATE PASSED: Hit@5={hit5}%, VerdictAcc={verdict_acc}%, "
        f"Counterfactual={cf_acc}%, MultiHop={mh_acc}%"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
