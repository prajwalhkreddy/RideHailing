#!/usr/bin/env python3
"""Print compact decision diagnostics from the completed Phase 7D artifacts."""

from pathlib import Path
import json
import numpy as np
import pandas as pd

P = Path("results/validation/phase7d_48slot_final_integrated_seed42")
d = pd.read_csv(P / "per_slot.csv")
f = pd.read_csv(P / "nb9_fare_representative.csv")
g = pd.read_csv(P / "routing_grid_representative.csv")
arms = ["arm_085", "arm_090", "arm_095", "arm_100", "arm_105", "arm_110", "arm_115"]
out = {"summary": json.loads((P / "summary.json").read_text())}
out["summary"]["configuration"]["evaluation_end_exclusive"] = "2026-01-26T19:00:00"
out["coverage"] = {"rows": len(d), "first": d.timestamp.iloc[0], "last": d.timestamp.iloc[-1], "periods": sorted(d.period.tolist())}
out["totals"] = {c: float(d[c].sum()) for c in ["generated", "accepted", "rejected", "served", "accepted_unserved", "linucb_selections", "linucb_updates", "raw_served_revenue", "scaled_learning_reward"]}
out["arm_windows"] = {}
for name, x in [("first8", d.iloc[:8]), ("middle8", d.iloc[20:28]), ("last8", d.iloc[-8:]), ("all", d)]:
    counts = x[arms].sum()
    out["arm_windows"][name] = {"counts": counts.astype(int).to_dict(), "shares": (counts / counts.sum()).to_dict()}
out["wait_checkpoints"] = {}
for i in [1, 2, 8, 16, 24, 32, 40, 48]:
    r = d.iloc[i - 1]
    total = r.wait_real_candidates + r.wait_neutral_candidates
    out["wait_checkpoints"][str(i)] = {"completed": int(r.completed_waits), "nonzero": int(r.nonzero_waits), "history_grids": int(r.real_wait_history_grids), "real": int(r.wait_real_candidates), "neutral": int(r.wait_neutral_candidates), "fallback_share": float(r.wait_neutral_candidates / total) if total else None}
norm = d.global_parameter_change_norm
out["learning"] = {"first": norm.iloc[0], "median": norm.median(), "mean": norm.mean(), "last": norm.iloc[-1], "p95": norm.quantile(.95), "max": norm.max(), "zero_participant_rounds": int((d.nb12_participants == 0).sum()), "zero_change_with_participants": int(((d.nb12_participants > 0) & (norm == 0)).sum())}
out["contention"] = d[["eligible_evaluations", "contenders", "zero_eligible_requests", "eligible_zero_contender_requests", "same_grid_assignments", "neighbour_assignments"]].sum().astype(int).to_dict()
out["fleet"] = {"reconciliation_failures": int(((d.fleet_idle + d.busy_passenger + d.busy_repositioning + d.fleet_charging) != 5000).sum()), "charging_max": d[["charging_active", "charging_queued", "charging_entered", "charging_completed"]].max().to_dict(), "energy_extrema": d[["energy_min", "energy_median", "energy_mean", "energy_p5", "energy_p95", "energy_max"]].agg(["min", "max"]).to_dict()}
actions = d[["action_stay", "action_north", "action_east", "action_south", "action_west"]].sum()
out["routing"] = {"counts": actions.astype(int).to_dict(), "shares": (actions / actions.sum()).to_dict(), "selected_mean_p5": d.iloc[[0, 1, 7, 23, 47]][["slot_index", "timestamp", "mean_p_stay", "mean_p_north", "mean_p_east", "mean_p_south", "mean_p_west"]].to_dict("records")}
out["fare"] = {"grids": f.grid_id.unique().astype(int).tolist(), "finite": bool(np.isfinite(f.select_dtypes("number")).all().all()), "ewma_min": f.ewma_mean.min(), "ewma_max": f.ewma_mean.max(), "observations": int(f.observed_count.sum())}
prob = g.filter(like="p_")
out["probability_health"] = {"finite": bool(np.isfinite(prob).all().all()), "out_of_bounds": int(((prob < 0) | (prob > 1)).sum().sum()), "max_sum_error": float(np.abs(prob.sum(axis=1) - 1).max())}
out["reposition"] = {"starts": int(d.reposition_starts.sum()), "completions": int(d.reposition_completions.sum()), "boundary": int(d.repositioning_at_boundary.sum()), "boundary_equals_starts_failures": int((d.repositioning_at_boundary != d.reposition_starts).sum())}
out["per_period"] = d[["period", "generated", "accepted", "served", "raw_served_revenue", "wait_mean", "action_stay", "action_north", "action_east", "action_south", "action_west"] + arms].to_dict("records")
(P / "analysis.json").write_text(json.dumps(out, indent=2, default=float) + "\n")
(P / "summary.json").write_text(json.dumps(out["summary"], indent=2, sort_keys=True) + "\n")
pd.DataFrame(out["per_period"]).to_csv(P / "per_period.csv", index=False)
print(json.dumps(out, indent=2, default=float))
