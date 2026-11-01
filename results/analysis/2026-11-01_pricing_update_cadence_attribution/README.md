# Read-only pricing update-cadence attribution

**Q_INFLATION_ATTRIBUTION = ACCELERATED_CADENCE_DOMINANT**  
**FINAL_PRICING_RUN_RECOMMENDATION = SAFE_TO_RESUME_WITH_MONITORING**

This is a conditional assessment of the available early checkpoint, not proof of future stability or convergence. No training, optimizer calls, simulator execution, environment regeneration or checkpoint mutation occurred. Models were loaded with compile=False for pure inference. The authoritative500×16×8 protocol remains unchanged and paused. March17–31 untouched.

## Exact preserved state and scale

Episode5/slot2,66 environment slots,30,039 replay entries,520 optimizer updates, epsilon0.99012. Checkpoint: `models/pricing_dqn/final_nonprivate_multiepisode_seed42/episode_0005/checkpoint_0002_c73ba1cf`.

Using a seed42 sample of4,096 saved replay states, all-action Q mean87.57, median43.11, maximum494.27; action spread10.86. Reward mean27.56, P9593.94, maximum750.03. The16-slot discounted empirical mean/P95/maximum-reward references are409.40/1,395.42/11,141.13. These are descriptive scenarios, not hard bounds. Current Q magnitudes are compatible with these early finite-horizon scales.

For all1,907 terminal rows: reward mean26.50/median19.00; chosen-action Q mean93.64/median42.66; absolute error mean73.48/P95281.08. Terminal overprediction is **MODERATE**, not absent. Review episode25 terminal mean Q7,475.14 versus reward24.68 and MAE7,450.46 is vastly worse.

Final sample mean absolute reward/bootstrapped contribution/Bellman target:28.42/65.81/94.24; average bootstrap fraction67.31%, versus95.46% in review episode25. Final mean absolute TD error26.42 and snapshot Huber25.93 are close to the saved partial-episode loss25.04. The final online/target mean absolute gap is22.30; target lags early learning, rather than tracking review-level inflated values. Replay structural checks and payload hashes pass; Bellman/terminal semantics remain as previously verified. No structural implementation bug was found.

## All available authoritative checkpoint boundaries

Forward-pass Q probes are consistent seed42 samples, not the historical last512-state probes. Loss is the saved mean of slot losses within that episode up to the checkpoint. Duplicate commits at a boundary appear separately in JSON but are deduplicated below.

|Episode|Slot|Replay|Updates|Epsilon|Mean abs Q|Median abs Q|Spread|Q min|Q max|Loss|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|1|8|4872|56|0.99894|29.11286|5.14366|12.77613|0.27018|224.99260|23.60688|
|1|16|7662|120|0.99772|43.88586|12.67079|10.43126|0.95865|238.34561|22.49213|
|2|8|10739|184|0.99650|49.67593|17.47410|14.42384|1.62036|254.96652|21.83800|
|2|16|13735|248|0.99529|60.33033|24.82938|11.65089|3.25636|294.03152|21.63820|
|3|8|18253|312|0.99407|76.95436|32.00081|14.44760|5.30231|495.16217|23.25804|
|3|16|23014|376|0.99286|74.10728|32.89120|8.53934|7.06688|444.39337|24.05406|
|4|8|25841|440|0.99164|79.04038|37.04163|11.97725|9.54157|461.60678|23.88936|
|4|16|29572|504|0.99042|86.10421|41.27993|9.95635|12.77004|467.63443|24.04899|
|5|2|30039|520|0.99012|87.56631|43.10978|10.85789|13.88244|494.26813|25.03559|

## Matched environment exposure

Both checkpoints at episode4/slot16 have64 slots and29,572 replay entries. Final:504 updates, mean Q86.10, maximum467.63, spread9.96, loss24.05. Review:8,064 updates, mean Q984.37, maximum3,525.48, spread31.82, loss82.51. Exact comparisons at episodes1–4 are in cadence_comparison.json. Same source windows and replay counts do not imply identical policies, rewards or states; trajectories can diverge.

Episode1→4 growth per100 optimizer updates:

|Cadence|Mean Q growth|Q-max growth|Loss growth|
|---|---:|---:|---:|
|8/slot|10.99|59.71|0.405|
|128/slot|12.20|47.76|1.016|

These endpoint slopes are not a linear-growth assumption. Similar Q growth per optimizer update is a major limitation: accumulated update exposure plausibly explains much of the fixed-environment difference. This comparison does not prove that low cadence prevents eventual inflation after many more updates.

## Replay exposure and interpretation

Final520×64=33,280 sampled examples,1.108× current replay size. Review51,072×64=3,268,608,32.686× final replay capacity. Growth and FIFO mean individual observations have unequal reuse. The review imposes much greater replay reuse at a given simulator exposure.

Under the requested descriptive classification, acceleration dominates observed inflation: final terminal error, Q scale and bootstrap dominance are materially healthier. This does **not** erase terminal miscalibration or previously identified state/horizon representation risks. It supports only a monitored continuation, not an unconditional declaration of stability.

## Monitoring plan — not executed

At episodes10/25/50/100 inspect only mean_abs_Q, q_max, mean_loss, terminal_Q/terminal_reward, bootstrap_fraction, fixed March16 greedy revenue and action distribution. Use a consistent replay probe and distinguish its composition from historical last512 probes. No new thresholds or methodology changes are imposed. Episode10 diagnostics require authorization in the later execution task; this report does not alter the existing every25-episode evaluator. No run was resumed.

## Files

cadence_comparison.json contains all saved checkpoint metrics, historical episode summaries, matched comparisons and update-normalized slopes. final_checkpoint_q_analysis.json contains reward/Q/target/TD/horizon statistics. terminal_comparison.json, bootstrap_comparison.json and replay_reuse_comparison.json separate the comparisons. attribution_verdict.json records the conditional decision and monitoring plan. Prior accelerated episode25 diagnostics were reused rather than recomputed.
