## Storage maintenance and final-Softplus CNN — 2026-11-18

Controlled cleanup removed only 180 untracked unopened bytecode files (2.35 MiB); protected research artifacts remain. Large V3 checkpoint families require an explicit retention decision. One fresh seed42 output-only Softplus run selected epoch42 and stopped at52. Validation MAE/RMSE 7.013677/26.027186 modestly improves ReLU 7.107571/26.145924 but remains worse than historical-average 3.518426/18.226779. Thirty-two focused tests passed. Weather availability remains assumed; March17–31 untouched; no March12 prospective promotion or DQN training. Evidence: `results_v2/cnn_demand/2026-11-18_softplus_causal_research_training/README.md` and `results_v2/repository_maintenance/2026-11-18_safe_cleanup/README.md`. Next: bounded no-training near-zero/feature-scale diagnosis.

## Corrected causal-research CNN — 2026-11-18

One bounded seed-42 run completed: best epoch 50, early stopping at 60. CNN validation MAE/RMSE 7.107571/26.145924 versus causal historical-average 3.518426/18.226779. March16 development also favors the baseline. The new checkpoint is research-only under the assumed 120-minute weather protocol; March17–31 remains protected. Its March1–15 model-selection lineage is incompatible with the February28-cutoff prospective March12 run. No runtime behavior was changed. See `results_v2/cnn_demand/2026-11-18_causal_research_training/README.md`. Next: bounded residual diagnosis, not DQN training.

# Demand forecasting protocols

Historical `final_cnn.py` and saved CNN artifacts are unchanged. The versioned
`causal_timing.py` builder corrects expanding historical-demand information timing
and explicitly labels retrospective target weather as oracle-only. It excludes
nonexistent NYC civil slots and rejects operational export.

See [timing protocol, validation and limitations](../../results_v2/cnn_demand/2026-11-17_causal_timing/README.md). No training was performed.

`persistence_weather.py` adds an assumption-based observation-persistence research
baseline, checkpoint fingerprint checks and opt-in OD export validation. It does
not certify operational weather availability or relabel oracle models.
[Evidence and limitations](../../results_v2/cnn_demand/2026-11-17_observation_persistence/README.md).
