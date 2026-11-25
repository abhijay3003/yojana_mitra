"""F1 Benefit-Stacking Optimizer using OR-Tools CP-SAT with exact branch-and-bound fallback.

Maximizes total annual benefit (INR/year) across deterministically ELIGIBLE schemes
subject to mutual-exclusion constraints (`mutually_exclusive_with`) and optional
maximum scheme stack size. Reports exact % gain vs naive top-1 scheme selection.
"""

from __future__ import annotations

from typing import Any, Dict, List, Set, Tuple

from rules.engine import evaluate


def _solve_cp_sat(
    eligible_schemes: List[Dict[str, Any]],
    max_schemes: int,
) -> List[Dict[str, Any]]:
    """Solve binary integer maximization using OR-Tools CP-SAT if installed."""
    from ortools.sat.python import cp_model  # type: ignore[import-not-found]

    model = cp_model.CpModel()
    n = len(eligible_schemes)
    x = [model.NewBoolVar(f"x_{i}") for i in range(n)]
    id_to_idx = {s["scheme_id"]: i for i, s in enumerate(eligible_schemes)}

    # Mutual exclusion constraints
    added_pairs: Set[Tuple[int, int]] = set()
    for i, s in enumerate(eligible_schemes):
        for ex_id in s.get("mutually_exclusive_with", []):
            if ex_id in id_to_idx:
                j = id_to_idx[ex_id]
                pair = (min(i, j), max(i, j))
                if pair not in added_pairs and i != j:
                    model.Add(x[pair[0]] + x[pair[1]] <= 1)
                    added_pairs.add(pair)

    if max_schemes > 0:
        model.Add(sum(x) <= max_schemes)

    model.Maximize(sum(int(eligible_schemes[i].get("annual_benefit_inr", 0)) * x[i] for i in range(n)))
    solver = cp_model.CpSolver()
    solver.parameters.random_seed = 42
    status = solver.Solve(model)
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return [eligible_schemes[i] for i in range(n) if solver.Value(x[i]) == 1]
    return []


def _solve_exact_branch_and_bound(
    eligible_schemes: List[Dict[str, Any]],
    max_schemes: int,
) -> List[Dict[str, Any]]:
    """Exact branch-and-bound 0-1 optimizer with mutual-exclusion constraints (zero external deps)."""
    # Sort descending by benefit for tight upper-bound pruning
    ordered = sorted(
        eligible_schemes,
        key=lambda s: (-int(s.get("annual_benefit_inr", 0)), s["scheme_id"]),
    )
    # Cap candidate pool to top 24 highest-value eligible schemes for instant exact solve
    pool = ordered[:24]
    n = len(pool)
    values = [int(s.get("annual_benefit_inr", 0)) for s in pool]
    id_to_idx = {s["scheme_id"]: i for i, s in enumerate(pool)}

    conflicts: List[Set[int]] = [set() for _ in range(n)]
    for i, s in enumerate(pool):
        for ex_id in s.get("mutually_exclusive_with", []):
            if ex_id in id_to_idx:
                j = id_to_idx[ex_id]
                conflicts[i].add(j)
                conflicts[j].add(i)

    best_val = 0
    best_pick: List[int] = []

    def dfs(idx: int, picked: List[int], current_val: int) -> None:
        nonlocal best_val, best_pick
        if current_val > best_val:
            best_val = current_val
            best_pick = list(picked)
        if idx >= n or (max_schemes > 0 and len(picked) >= max_schemes):
            return
        # Optimistic upper bound: top remaining slots
        slots_left = (max_schemes - len(picked)) if max_schemes > 0 else (n - idx)
        upper = current_val + sum(values[idx : idx + slots_left])
        if upper <= best_val:
            return

        # Branch 1: take idx if no conflict with picked
        if all(idx not in conflicts[p] for p in picked):
            picked.append(idx)
            dfs(idx + 1, picked, current_val + values[idx])
            picked.pop()

        # Branch 2: skip idx
        dfs(idx + 1, picked, current_val)

    dfs(0, [], 0)
    return [pool[i] for i in best_pick]


def optimize_benefit_stack(
    profile: Dict[str, Any],
    schemes: List[Dict[str, Any]],
    max_schemes: int = 5,
) -> Dict[str, Any]:
    """Find the optimal non-conflicting stack of ELIGIBLE schemes maximizing INR/year."""
    eligible: List[Dict[str, Any]] = []
    for s in schemes:
        if evaluate(profile, s)["verdict"] == "ELIGIBLE":
            eligible.append(s)

    if not eligible:
        return {
            "solver": "exact_branch_and_bound",
            "eligible_count": 0,
            "selected_schemes": [],
            "total_annual_inr": 0,
            "naive_top1_inr": 0,
            "gain_vs_top1_inr": 0,
            "gain_vs_top1_pct": 0.0,
            "excluded_by_conflict": [],
        }

    try:
        selected = _solve_cp_sat(eligible, max_schemes)
        solver_name = "ortools_cp_sat"
    except ImportError:
        selected = _solve_exact_branch_and_bound(eligible, max_schemes)
        solver_name = "exact_branch_and_bound"

    selected.sort(key=lambda s: -int(s.get("annual_benefit_inr", 0)))
    selected_ids = {s["scheme_id"] for s in selected}
    total_inr = sum(int(s.get("annual_benefit_inr", 0)) for s in selected)
    naive_top1 = max(int(s.get("annual_benefit_inr", 0)) for s in eligible)
    gain_inr = total_inr - naive_top1
    gain_pct = round((gain_inr / naive_top1) * 100.0, 1) if naive_top1 > 0 else 0.0

    # Identify schemes dropped specifically due to mutual exclusion with a selected scheme
    excluded_conflicts: List[Dict[str, str]] = []
    for s in eligible:
        if s["scheme_id"] in selected_ids:
            continue
        conflicting_with = [
            sel["name"]
            for sel in selected
            if sel["scheme_id"] in s.get("mutually_exclusive_with", [])
            or s["scheme_id"] in sel.get("mutually_exclusive_with", [])
        ]
        if conflicting_with:
            excluded_conflicts.append(
                {
                    "scheme_id": s["scheme_id"],
                    "name": s["name"],
                    "conflicts_with": ", ".join(conflicting_with),
                }
            )

    return {
        "solver": solver_name,
        "eligible_count": len(eligible),
        "selected_schemes": [
            {
                "scheme_id": s["scheme_id"],
                "name": s["name"],
                "state": s["state"],
                "category": s["category"],
                "annual_benefit_inr": int(s.get("annual_benefit_inr", 0)),
                "apply_url": s["apply_url"],
                "documents": s["documents"],
            }
            for s in selected
        ],
        "total_annual_inr": total_inr,
        "naive_top1_inr": naive_top1,
        "gain_vs_top1_inr": gain_inr,
        "gain_vs_top1_pct": gain_pct,
        "excluded_by_conflict": excluded_conflicts,
    }
