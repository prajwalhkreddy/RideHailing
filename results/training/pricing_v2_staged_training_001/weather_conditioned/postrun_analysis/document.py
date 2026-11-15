from pathlib import Path
import json,re
import pandas as pd
O=Path(__file__).resolve().parent;P=O.parent;s=json.loads((O/'analysis_summary.json').read_text());e=s['ep25'];b=s['highest_feasible'];tests=json.loads((O/'tests.json').read_text())
for t in tests:
 text=(O/('tests_'+t['stage']+'.txt')).read_text();t.update(passed=int(re.search(r'Ran (\d+) tests?',text)[1]),failures=0,errors=0,skipped=0);assert t['exit_code']==0 and '\nOK' in text
(O/'tests.json').write_text(json.dumps(tests,indent=2)+'\n')
def table(df):
 return '| '+' | '.join(map(str,df.columns))+' |\n|'+'|'.join(['---']*len(df.columns))+'|\n'+'\n'.join('| '+' | '.join(str(round(x,6)) if isinstance(x,float) else str(x) for x in r)+' |' for r in df.itertuples(index=False,name=None))+'\n'
primary=pd.read_csv(O/'episode25_comparison.csv');usage=pd.read_csv(O/'weather_support_usage.csv');tr=pd.read_csv(O/'training_trends.csv');v=pd.read_csv(O/'value_calibration_review.csv');ev=pd.read_csv(O/'checkpoint_comparison.csv');st=pd.read_csv(O/'policy_stability.csv')
text=f'''# Weather/time-conditioned V2: completed Episode25 review

**V2_STAGE25_REVIEW_REQUIRED.** Episodes1–25 completed; no Episode26 was run. Episode25 does not beat Highest Feasible on assignments or revenue. No demonstrated beneficial dynamic effect is established.

## Frozen method and experimental scope

Runtime version `WEATHER_TIME_CONDITIONED_V2`; grouping `WEATHER_TIME_CONDITIONED_V2_2026_11_14`. Canonical Jan1–Mar15 empirical population:5,779,213 nonnegative observations, with actual zero count0. P_base=22.354198442390455 USD; L_base=4.616983790655043 km. Epsilon=r_L/r_P; inclusive abs(r_P)>=0.05. Negatives are excluded, not absolute-transformed. No new trimming, floor, distribution fitting or clustering was performed. Sampling is empirical with replacement, retaining duplicate frequencies. Runtime inverse preference is P_base+(P_base/epsilon)*r_L; acceptance threshold=max(0.85P_base,raw preference). Seven factors0.85–1.15 remain unchanged.

T1 uses its two time-specific groups. T2/T3/T4 deliberately use T-pooled support. Runtime minimum support5000: exact time-specific group, then same raw-weather pool, then time pool, then global. Explicitly pooled T2–T4 bypass the raw-weather fallback. T1_G2 has insufficient runtime support and falls back to raw-weather pools; codes17/21 fall back to T1 pool when applicable. No silent fallback is permitted.

## Duration, state and training

Training:16×30-minute slots=8h per episode,5000 vehicles,25 episodes. Development:48×30-minute slots=24h on March16. This retains the established request-level training horizon while strengthening development to a full day. The artificial 8h terminal boundary is an acknowledged limitation, not an optimized horizon. Historical continuous slot-based pricing used720 chronological slots; request-level V1 used16-slot training and its historical4-slot/2h development fixture.

13→64→64→7 network; gamma0.99 per actionable request transition; Adam lr0.001; batch64; replay100000; warmup1000;8 updates per warm slot; tau0.005. Epsilon1→0.05 over50000 updates. Learner seed42; development seed424242; persisted episode-specific environment seeds. Routing, request-level gross successful-assignment reward, masks and state are unchanged. Training dates remain March1–15, March16 development-only, March17–31 protected and untouched by this task.

Fixture SHA256:`c23f815ab8dd573b958e83260b442ab428255325bffc8ac83fdbfcf77e1177a6`. All six evaluations contain73,754 identical request IDs and identical conditioning hashes. The pinned evaluation implementation asserts epsilon/context equality, initial fleet identity and immutable input dependencies. No policies or fixtures were regenerated.

## Completion, integrity and resume

All six checkpoints loaded successfully, validating online/target architecture, finite weights and optimizer variables, Adam iteration counts, replay structure, learner/replay/sensitivity RNG identities, conditional version and contract hashes. Config/fixture/support/mapping/fallback hashes match. Current payload SHA256 fingerprints are in analysis_summary.json; no creation-time payload digest existed, so these establish present integrity/readability rather than independent historical authentication.

The initial process was interrupted during Episode4 after completing Episodes2–3 in volatile learner state. Episode1 was the latest durable checkpoint. Detached continuation restored Episode1:128 updates,37,111 replay rows,epsilon0.997568. Episode1 was not repeated. Interrupted later metrics were archived and excluded; Episodes2 onward were recomputed from the durable checkpoint under the recorded episode-boundary seed-reset contract. Resetting the next environment/sensitivity seed is prescribed; learner/replay RNG and optimizer were restored, not freshly initialized.

RESUME_CONTINUITY_VALIDATED=YES at checkpoint/accounting level. The committed output contains each episode1–25 once,128 updates each, cumulative3200; replay equals min(cumulative requests,100000), ending100000; epsilon0.9392. Expected slots=400 inferred from the fixed16-slot loop and completion assertions. Full per-slot IDs and all historical replay transitions were not persisted, limiting independent row-level duplicate verification.

Total training requests={s['requests']:,}; assignments={s['assignments']:,}; revenue=${s['revenue']:,.2f}. Request=assigned+unmatched in every episode. Training revenue is not a controlled comparison because source conditions and exploration vary.

## Authoritative fixed-fixture result

These are **WEATHER_CONDITIONED_V2_AUTHORITATIVE_BASELINE** results. Earlier POOLED_V2_CONTROL outputs remain historical and were not substituted.

'''
text+=table(primary[['policy','requests','assignments','assignment_rate','revenue','revenue_per_request','unmatched','choice_requests','forced_requests','charging_events','invalid_masks','passenger_threshold_violations']])
text+=f'\nEP25 assignment gap={int(e["assignments"]-b["assignments"]):+,}; revenue gap=${e["revenue"]-b["revenue"]:+,.2f} ({e["revenue_gap_pct"]:+.4f}%). Beats Highest Feasible assignments: **NO**. Beats revenue: **NO**.\n\n'
text+='## Checkpoint policy results\n\n'+table(ev[['episode','assignments','assignment_rate','revenue','unmatched','no_price_eligible_driver','mean_offer','revenue_gap_pct']])
text+='\nComplete action counts, forced/choice counts, fleet hashes, SOC ranges and charging entry/exit counts are retained in checkpoint_comparison.csv and episode25_comparison.csv. Fleet hashes identify end states, not complete vehicle-state reconstructions.\n\n## Value calibration\n\n'+table(v)
text+='\nQ_CALIBRATION=POOR, despite improving scale/MAE and positive final correlations. Selected Q remains far below Monte Carlo return. LEARNING_SIGNAL=YES: finite losses and value predictions change, but this does not establish superior pricing or convergence. Exploration remains0.9392 and only3200 updates have occurred.\n\n## Policy stability and action dominance\n\n'+table(st)
text+=f'\nPOLICY_STABILITY=PARTIAL: all-request agreement is inflated by forced requests. EP20→25 choice agreement is41.08%, so the discretionary policy is not stable. Among choice requests, EP25 equals Highest Feasible {s["dominance"]["highest_pct"]:.4f}%, one action below {s["dominance"]["one_below_pct"]:.4f}%, and at least two below {s["dominance"]["two_or_more_below_pct"]:.4f}%. Mean/median rank below: {s["dominance"]["mean_rank_below"]:.6f}/1. Choice factor counts (0.85…1.15):{s["dominance"]["choice_factor_counts"]}.\n'
text+='''
Passenger masks form a prefix of the ordered actions: lowering price preserves passenger feasibility. At a fixed fleet state, driver eligibility is monotone in offered price because dispatch rejects fares below each driver minimum (src/dispatch/dispatch.py:65–70). Consequently maximum feasible price weakly expands eligible drivers and raises immediate reward conditional on successful dispatch. This fixed-state immediate property does not prove long-term dominance: selecting a different driver can change later state.

DYNAMIC_VALUE_EVIDENCE=NONE for **demonstrated beneficial dynamic effects**. The first20 deterministic below-highest choice cases are in bounded_policy_difference_cases.csv. They show outcomes under different complete policy trajectories, not state-matched interventions. Assigned-driver identity, paired trajectories, later supply and commitments were not saved for DQN; no causal claim follows from reward differences in this table. No expensive counterfactual simulation was run. A separately scoped state-matched counterfactual diagnostic is the recommended next step before claiming dynamic value or extending training.

## Weather/time usage and empirical membership

'''+table(usage)
text+='\nUsage is for the common March16 evaluation fixture, not all training requests (training context usage was not persisted). Every fixture epsilon was checked for membership in its selected immutable support and support hashes verified. All evaluations reproduce the same context hash. Absent categories have zero observed usage, not fabricated fallback observations.\n\n## Charging and invariants\n\n'
text+=f'Training charging events={s["training_charging_events"]}; episodes with charging={s["episodes_with_charging"]}/25. CHARGING_COVERAGE=EXERCISED.\n\n'+table(ev[['episode','charging_events','vehicles_entering_charging','vehicles_leaving_charging','soc_min','soc_max','fleet_conserved']])
text+='\nEntry/exit counts are distinct vehicles observed at slot boundaries, not a complete event transition ledger. Training entry/exit counts were not persisted. Runtime finite/nonnegative SOC and fleet5000 assertions passed. Saved evaluation results contain zero masked-action, passenger-threshold and no-feasible-action violations. Persisted actions/rewards reconcile assignments and revenue; checkpoint replay loads and optimizer cadence pass. Routing/charging validity relies on the completed runtime guards and focused regression coverage, not an independently saved routing-event audit. No evidence of V1 or pooled-only learner contamination.\n\n## Evidence gaps\n\n'+''.join('- '+x+'\n' for x in s['missing_diagnostics'])
text+='\nThese fields cannot be honestly reconstructed from aggregate loss/reward summaries. No training or full-day simulation was rerun to fill them. Numerical stability is supported by recorded finite summaries and checkpoint state, with these audit limits.\n\n## Tests\n\n'+table(pd.DataFrame(tests)[['stage','passed','failures','errors','skipped','exit_code']])
text+='\nExact safe commands and logs are in postrun_analysis/tests.json and tests_*.txt; overlapping suites are not unique-test counts. No unrestricted discovery was used.\n\n## Review decision and files\n\nNUMERICAL_STABILITY=YES; LEARNING_SIGNAL=YES; Q_CALIBRATION=POOR; POLICY_STABILITY=PARTIAL; DYNAMIC_VALUE_EVIDENCE=NONE; CHARGING_COVERAGE=EXERCISED; CONVERGED=NO; READY_FOR_LONGER_TRAINING=REVIEW_REQUIRED.\n\nThe next decision is whether bounded state-matched counterfactual evidence justifies more training against Highest Feasible. No Episode26 or held-out evaluation is authorized by this analysis. See postrun_analysis/analysis_summary.json, checkpoint_comparison.csv, episode25_comparison.csv, training_trends.csv, value_calibration_review.csv, policy_stability.csv, weather_support_usage.csv, bounded_policy_difference_cases.csv and training_and_development_trends.png. Analysis uses immutable persisted inputs; source methodology/checkpoints were not changed.\n\n**V2_STAGE25_REVIEW_REQUIRED**\n'
(P.parent/'README.md').write_text(text);(O/'README.md').write_text(text.replace('postrun_analysis/',''))
(P/'README.md').write_text('# Completed weather/time-conditioned V2 run\n\nV2_STAGE25_REVIEW_REQUIRED. Authoritative narrative: [training review](../README.md). Detailed tables and validation: [post-run analysis](postrun_analysis/README.md). Training completed Episode25; do not resume or start Episode26.\n')
current=f'''## Current V2 Episode25 result — 2026-11-15

V1 STATUS: historical, unchanged. V2 SENSITIVITY/RUNTIME: frozen weather/time-conditioned empirical V2, validated; T1 groups and T2–T4 pooled fallback unchanged. V2 TRAINING: COMPLETED Episode25,3200 updates,replay100000,epsilon0.9392. Training16 slots/8h; development48 slots/24h,73,754 frozen March16 requests. Authoritative run: `results/training/pricing_v2_staged_training_001/weather_conditioned/`; latest checkpoint `checkpoints/episode_025`.

EP25 DQN: {int(e['assignments']):,} assignments,${e['revenue']:,.2f}; Highest Feasible: {int(b['assignments']):,},${b['revenue']:,.2f}. Gaps:{int(e['assignments']-b['assignments']):+,} assignments and${e['revenue']-b['revenue']:+,.2f} ({e['revenue_gap_pct']:+.4f}%). Q calibration POOR; policy stability PARTIAL; demonstrated beneficial dynamic value NONE; charging EXERCISED. Numerical stability and learning signal YES; convergence NO. Checkpoint/accounting resume continuity validated, with missing full slot/transition audit explicitly documented. Tests23/41/57/123/239/2 passed,zero failures/errors. March17–31 untouched.

Current research question: does a below-highest action create beneficial future value? Next step: review bounded state-matched counterfactual diagnostics and evidence gaps before longer training. No Episode26 launched. Full authoritative narrative: [V2 run review](results/training/pricing_v2_staged_training_001/README.md). **V2_STAGE25_REVIEW_REQUIRED**. Earlier status entries below are historical snapshots.

'''
for path in [Path('README.md'),Path('results/analysis/2026-11-01_current_state_review/README.md')]:path.write_text(current+path.read_text())
(P/'completion_status.json').write_text(json.dumps(dict(status='COMPLETE',training_started=True,completed_episode=25,verdict=s['verdict'],postrun_report=str(O/'README.md')),indent=2)+'\n')
print(json.dumps(dict(ep25_assignments=e['assignments'],ep25_revenue=e['revenue'],hf_assignments=b['assignments'],hf_revenue=b['revenue'],gap_pct=e['revenue_gap_pct'],tests=[(x['stage'],x['passed']) for x in tests])))
