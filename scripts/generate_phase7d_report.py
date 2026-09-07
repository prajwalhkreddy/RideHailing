#!/usr/bin/env python3
"""Generate the dated human-readable Phase 7D package from frozen artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "results/validation/phase7d_48slot_final_integrated_seed42"
OUTPUT = ROOT / "results/validation/2026-09-08_48slot_run"
CHARTS, TABLES = OUTPUT / "charts", OUTPUT / "tables"
ARMS = ["arm_085", "arm_090", "arm_095", "arm_100", "arm_105", "arm_110", "arm_115"]
FACTORS = ["0.85", "0.90", "0.95", "1.00", "1.05", "1.10", "1.15"]
ACTIONS = ["action_stay", "action_north", "action_east", "action_south", "action_west"]
COLORS = ["#35618f", "#d17a22", "#438b68", "#a64b5d", "#7768ae", "#55a6a6", "#9a7248"]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(fig, name: str, source: str, columns: list[str], rows: str, manifest: list[dict]) -> None:
    fig.tight_layout()
    outputs = []
    for suffix in ("png", "pdf"):
        path = CHARTS / f"{name}.{suffix}"
        fig.savefig(path, dpi=240 if suffix == "png" else None, bbox_inches="tight")
        outputs.append({"file": str(path.relative_to(OUTPUT)), "sha256": sha(path)})
    plt.close(fig)
    manifest.append({"chart": name, "source_file": source, "source_columns": columns, "rows_or_aggregation": rows, "outputs": outputs})


def bars(labels, values, title, ylabel):
    fig, ax = plt.subplots(figsize=(8, 4.8))
    rects = ax.bar(labels, values, color=COLORS[:len(values)])
    ax.set(title=title, ylabel=ylabel)
    ax.bar_label(rects, fmt="{:,.0f}", padding=3)
    ax.set_ylim(0, max(values) * 1.16)
    ax.grid(axis="y", alpha=.25)
    return fig


def main() -> int:
    CHARTS.mkdir(parents=True, exist_ok=True); TABLES.mkdir(parents=True, exist_ok=True)
    summary = json.loads((SOURCE / "summary.json").read_text())
    slot = pd.read_csv(SOURCE / "per_slot.csv")
    period = pd.read_csv(SOURCE / "per_period.csv")
    rounds = pd.read_csv(SOURCE / "routing_rounds.csv")
    wait = pd.read_csv(SOURCE / "nb9_wait.csv")
    fleet = pd.read_csv(SOURCE / "fleet_states.csv")
    fare = pd.read_csv(SOURCE / "nb9_fare_representative.csv")
    routing_grid = pd.read_csv(SOURCE / "routing_grid_representative.csv")
    totals = summary["totals"]
    expected = {"generated": 106729, "accepted": 61863, "rejected": 44866, "served": 27967, "accepted_unserved": 33896}
    actual = {k: int(slot[k].sum()) for k in expected}
    if actual != expected or len(slot) != 48 or set(slot.period) != set(range(48)):
        raise ValueError(f"Phase 7D source identity failed: {actual}, rows={len(slot)}")
    if slot.timestamp.iloc[0] != "2026-01-25T19:00:00" or slot.timestamp.iloc[-1] != "2026-01-26T18:30:00":
        raise ValueError("Phase 7D timestamp coverage failed.")
    if not ((fleet.fleet_idle + fleet.busy_passenger + fleet.busy_repositioning + fleet.fleet_charging) == 5000).all():
        raise ValueError("Fleet state does not reconcile to 5,000.")

    accepted_rate = actual["accepted"] / actual["generated"]
    served_generated = actual["served"] / actual["generated"]
    served_accepted = actual["served"] / actual["accepted"]
    arm_counts = slot[ARMS].sum().astype(int); arm_shares = arm_counts / arm_counts.sum()
    action_counts = slot[ACTIONS].sum().astype(int); action_shares = action_counts / action_counts.sum()
    wait_summary = summary["driver_wait_minutes"]
    contention = {
        "eligible_evaluations": int(slot.eligible_evaluations.sum()), "contenders": int(slot.contenders.sum()),
        "zero_eligible_accepted": int(slot.zero_eligible_requests.sum()),
        "eligible_zero_contender": int(slot.eligible_zero_contender_requests.sum()), "served": actual["served"],
    }

    core = pd.DataFrame([{**actual, "acceptance_rate": accepted_rate, "served_generated_rate": served_generated,
                          "served_accepted_rate": served_accepted, "raw_served_revenue": totals["raw_served_revenue"],
                          "scaled_learning_reward": totals["scaled_learning_reward"], "slots": 48, "fleet": 5000}])
    table_map = {
        "core_summary.csv": core,
        "linucb_arm_summary.csv": pd.DataFrame({"pricing_factor": FACTORS, "count": arm_counts.values, "share": arm_shares.values}),
        "routing_action_summary.csv": pd.DataFrame({"action": [x.removeprefix("action_").upper() for x in ACTIONS], "count": action_counts.values, "share": action_shares.values}),
        "routing_p5_by_slot.csv": slot[["slot_index", "timestamp", "mean_p_stay", "mean_p_north", "mean_p_east", "mean_p_south", "mean_p_west"]],
        "federated_learning_rounds.csv": rounds,
        "wait_summary.csv": pd.DataFrame([wait_summary]),
        "contention_summary.csv": pd.DataFrame([{**contention, "contender_rate": contention["contenders"] / contention["eligible_evaluations"], "served_accepted_rate": served_accepted}]),
        "fleet_state_by_slot.csv": fleet,
        "per_period_summary.csv": period,
        "representative_fare_history.csv": fare,
        "representative_routing_probabilities.csv": routing_grid,
    }
    for name, frame in table_map.items(): frame.to_csv(TABLES / name, index=False, float_format="%.12g")

    manifest = []
    save(bars(["Generated", "Accepted", "Served"], [actual["generated"], actual["accepted"], actual["served"]], "Request funnel", "Requests"), "01_request_funnel", "summary.json + per_slot.csv", ["generated", "accepted", "served"], "48-slot sums", manifest)
    save(bars(["Rejected", "Served", "Accepted–unserved"], [actual["rejected"], actual["served"], actual["accepted_unserved"]], "Final request outcomes", "Requests"), "02_request_outcomes", "summary.json + per_slot.csv", ["rejected", "served", "accepted_unserved"], "48-slot sums", manifest)
    save(bars(FACTORS, arm_counts.values, "LinUCB pricing-factor selections", "Selections"), "03_linucb_arm_distribution", "per_slot.csv", ARMS, "48-slot sums", manifest)

    shares = slot[ARMS].div(slot[ARMS].sum(axis=1), axis=0)
    fig, ax = plt.subplots(figsize=(11, 5)); ax.stackplot(np.arange(1,49), *[shares[c] for c in ARMS], labels=FACTORS, colors=COLORS)
    ax.set(title="LinUCB pricing-factor share by slot", xlabel="Slot", ylabel="Selection share", xlim=(1,48), ylim=(0,1)); ax.legend(ncol=7, loc="upper center", bbox_to_anchor=(.5,-.14)); ax.grid(axis="y", alpha=.2)
    save(fig, "04_linucb_arm_evolution", "per_slot.csv", ARMS, "48 rows; within-slot shares", manifest)

    fig, axes = plt.subplots(2,1,figsize=(10,7),sharex=True); x=np.arange(1,49)
    axes[0].plot(x,slot.raw_served_revenue,color=COLORS[0]); axes[0].set(ylabel="Revenue",title="Served revenue by slot"); axes[0].grid(alpha=.25)
    axes[1].plot(x,slot.scaled_learning_reward,color=COLORS[1]); axes[1].set(xlabel="Slot",ylabel="Scaled reward",title="LinUCB learning reward by slot"); axes[1].grid(alpha=.25)
    save(fig,"05_revenue_reward_over_time","per_slot.csv",["raw_served_revenue","scaled_learning_reward"],"48 rows",manifest)

    fig,ax=plt.subplots(figsize=(10,4.5)); ax.plot(x,slot.raw_served_revenue.cumsum(),color=COLORS[0]); ax.set(title="Cumulative served revenue",xlabel="Slot",ylabel="Cumulative revenue"); ax.grid(alpha=.25)
    save(fig,"05b_cumulative_revenue","per_slot.csv",["raw_served_revenue"],"48-row cumulative sum",manifest)
    save(bars([a.removeprefix("action_").upper() for a in ACTIONS], action_counts.values,"NB11 routing-action distribution","Actions"),"06_nb11_action_distribution","per_slot.csv",ACTIONS,"48-slot sums",manifest)

    fig,ax=plt.subplots(figsize=(10,5)); pcols=["mean_p_stay","mean_p_north","mean_p_east","mean_p_south","mean_p_west"]
    for c,color in zip(pcols,COLORS): ax.plot(x,slot[c],label=c.removeprefix("mean_p_").upper(),color=color)
    ax.set(title="Mean global routing probability over time",xlabel="Slot",ylabel="Mean probability",xlim=(1,48),ylim=(0,1)); ax.legend(ncol=5); ax.grid(alpha=.25)
    save(fig,"07_routing_p5_evolution","routing_rounds.csv",pcols,"48 rows",manifest)

    fig,ax=plt.subplots(figsize=(10,4.5)); ax.plot(x,rounds.global_parameter_change_norm,color=COLORS[0]); ax.set(title="Global parameter-update magnitude over federated rounds",xlabel="Federated round",ylabel="L2 change norm"); ax.grid(alpha=.25)
    save(fig,"08_nb13_parameter_change","routing_rounds.csv",["global_parameter_change_norm"],"48 rows",manifest)
    fig,ax=plt.subplots(figsize=(10,4.5)); ax.plot(x,rounds.nb12_participants,label="Participating clients",color=COLORS[0]); ax.plot(x,rounds.zero_observation_clients,label="Zero-observation clients",color=COLORS[1]); ax.axhline(5000,color="0.45",lw=.8); ax.set(title="NB12 participation by federated round",xlabel="Round",ylabel="Vehicles",ylim=(0,5200)); ax.legend(); ax.grid(alpha=.25)
    save(fig,"09_nb12_participation","routing_rounds.csv",["nb12_participants","zero_observation_clients"],"48 rows",manifest)

    qs=["min","p25","median","mean","p75","p90","p95","p99","max"]; vals=[wait_summary[q] for q in qs]
    fig,ax=plt.subplots(figsize=(9,4.8)); rects=ax.bar([q.upper() for q in qs],vals,color=COLORS[0]); ax.bar_label(rects,fmt="%.1f",padding=2); ax.set(title="Completed driver idle-wait statistics",ylabel="Minutes"); ax.grid(axis="y",alpha=.25)
    save(fig,"10_driver_wait_statistics","summary.json",qs,"27,967 waits; aggregate statistics (not a histogram)",manifest)

    fallback=wait.wait_neutral_candidates/(wait.wait_real_candidates+wait.wait_neutral_candidates)
    fig,axes=plt.subplots(2,1,figsize=(10,7),sharex=True); axes[0].plot(x,wait.real_wait_history_grids,color=COLORS[0]); axes[0].set(title="Causal wait-history grid coverage",ylabel="Grids"); axes[0].grid(alpha=.25); axes[1].plot(x,fallback*100,color=COLORS[1]); axes[1].set(title="Neutral wait-utility fallback",xlabel="Slot",ylabel="Candidate share (%)"); axes[1].grid(alpha=.25)
    save(fig,"11_wait_history_coverage","nb9_wait.csv",["real_wait_history_grids","wait_real_candidates","wait_neutral_candidates"],"48 rows",manifest)
    save(bars(["Eligible evals","Contenders","Zero eligible","Eligible/no contender","Served"],list(contention.values()),"Driver contention and service","Count"),"12_contention_service","per_slot.csv",["eligible_evaluations","contenders","zero_eligible_requests","eligible_zero_contender_requests","served"],"48-slot sums",manifest)

    fig,ax=plt.subplots(figsize=(10,5));
    for c,color in zip(["reposition_starts","reposition_completions","repositioning_at_boundary"],COLORS): ax.plot(x,slot[c],label=c.replace("_"," ").title(),color=color)
    ax.set(title="Repositioning state over time",xlabel="Slot",ylabel="Vehicles"); ax.legend(); ax.grid(alpha=.25)
    save(fig,"13_repositioning","per_slot.csv",["reposition_starts","reposition_completions","repositioning_at_boundary"],"48 rows",manifest)

    states=["fleet_idle","busy_passenger","busy_repositioning","fleet_charging"]
    fig,ax=plt.subplots(figsize=(11,5)); ax.stackplot(x,*[fleet[c] for c in states],labels=["IDLE","PASSENGER_BUSY","REPOSITIONING","CHARGING"],colors=COLORS[:4]); ax.set(title="5,000-vehicle fleet composition",xlabel="Slot",ylabel="Vehicles",xlim=(1,48),ylim=(0,5000)); ax.legend(ncol=4,loc="upper center",bbox_to_anchor=(.5,-.14))
    save(fig,"14_fleet_state_evolution","fleet_states.csv",states,"48 rows; each row sums to 5,000",manifest)
    fig,ax=plt.subplots(figsize=(10,5));
    charging=["charging_active","charging_entered","charging_completed","charging_queued"]
    for c,color in zip(charging,COLORS): ax.plot(x,fleet[c],label=c.replace("charging_","").title(),color=color)
    ax.set(title="Charging activity",xlabel="Slot",ylabel="Vehicles"); ax.legend(); ax.grid(alpha=.25)
    save(fig,"15_charging_activity","fleet_states.csv",charging,"48 rows",manifest)
    fig,ax=plt.subplots(figsize=(10,5)); energy=["energy_min","energy_median","energy_mean","energy_p95","energy_max"]
    for c,color in zip(energy,COLORS): ax.plot(x,fleet[c],label=c.replace("energy_","").upper(),color=color)
    ax.set(title="Fleet energy health",xlabel="Slot",ylabel="Energy (kWh)",ylim=(0,75)); ax.legend(ncol=5); ax.grid(alpha=.25)
    save(fig,"16_energy_health","fleet_states.csv",energy,"48 rows",manifest)
    ordered=period.sort_values("period")
    fig,axes=plt.subplots(2,1,figsize=(11,7),sharex=True); axes[0].plot(ordered.period,ordered.generated,label="Generated",color=COLORS[0]); axes[0].plot(ordered.period,ordered.served,label="Served",color=COLORS[1]); axes[0].set(title="Time-of-day request volume",ylabel="Requests"); axes[0].legend(); axes[0].grid(alpha=.25); rate=ordered.served/ordered.accepted; axes[1].plot(ordered.period,rate*100,color=COLORS[2]); axes[1].set(title="Time-of-day served/accepted rate",xlabel="Half-hour Period (0–47)",ylabel="Rate (%)",xlim=(0,47),ylim=(0,100)); axes[1].grid(alpha=.25)
    save(fig,"17_time_of_day_performance","per_period.csv",["period","generated","accepted","served"],"48 Period rows",manifest)

    package_summary = {"run_date":"2026-09-08","source":str(SOURCE.relative_to(ROOT)),"window":{"start":"2026-01-25T19:00:00","end_exclusive":"2026-01-26T19:00:00"},"seed":42,"fleet":5000,"slots":48,"totals":actual,"rates":{"acceptance":accepted_rate,"served_generated":served_generated,"served_accepted":served_accepted},"revenue":totals["raw_served_revenue"],"scaled_reward":totals["scaled_learning_reward"],"verdict":"READY_FOR_PHASE_8A"}
    (OUTPUT/"summary.json").write_text(json.dumps(package_summary,indent=2,sort_keys=True)+"\n")
    pd.DataFrame([package_summary["totals"]|package_summary["rates"]|{"revenue":package_summary["revenue"],"scaled_reward":package_summary["scaled_reward"]}]).to_csv(OUTPUT/"summary.csv",index=False)
    chart_manifest={"source_directory":str(SOURCE.relative_to(ROOT)),"source_artifacts":{p.name:sha(p) for p in SOURCE.iterdir() if p.is_file()},"charts":manifest}
    (OUTPUT/"chart_manifest.json").write_text(json.dumps(chart_manifest,indent=2,sort_keys=True)+"\n")
    return 0


if __name__ == "__main__": raise SystemExit(main())
