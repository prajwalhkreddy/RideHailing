# Full-episode joint development training

Status: **PASSED — 16-slot episode and exact one-slot checkpoint continuation.** This is development integration evidence, not final policy evaluation or publication evidence.

## Frozen configuration and provenance

March 12 2026 00:00–08:00 America/New_York (04:00–12:00 UTC), 16 elapsed half-hour slots, 120-second mini-slots, 5,000 vehicles with 500 EVs. Fresh seed 42 initialization uses the validated Keras and explicit Philox global RNG setup; the four-slot pilot is not continued. Pricing is 13→64→64→7, Adam 0.001, gamma 0.99, batch 64, replay 100000, warm-up 1000, eight updates per eligible completed slot, tau 0.005, epsilon 1→0.05 over 50000 optimizer updates. Routing remains fresh 169→64→32→9, Adam 0.001, batch 32, one local epoch, memory 1000, equal-client NONPRIVATE FedAvg.

`provenance/` extends only the authorized experience end to 12:00 UTC and references that new initialization contract by hash. January support, popularity and historical-average forecasts; January–February weighted sensitivity; historical replay; successful-dispatch rewards and reference-price unseen-OD fallback are unchanged. No fallback experiences enter pricing replay. No CNN checkpoint is used. Weather availability remains assumed 120-minute persistence, not verified operational availability. Source guards and development-selected hyperparameter caveats remain.

March 12 is permitted by `src/pricing/slot_v3.py:allowed`, the earlier prospective development contracts and this task's explicit authorization. March 17–31 remains protected. `request_coverage_preflight.csv` records selected-row fingerprints and unchanged eligibility for all 16 slots;16,075 requests are eligible. Forecast metadata covers 17 boundaries including the terminal next state. No fitted source or model is backdated.

## Validation and storage

32 focused tests passed:31 existing learning/math/coupling/provenance/arrival/OD regressions plus atomic recovery-rotation failure preservation. Models are stored separately under `models/pricing_dqn/2026-11-20_full_episode_development_seed42/`. Atomic checkpoint creation precedes atomic replacement of the rolling symlink; only prior recovery generations created by this run are removed. Recovery writes occur at slots 4,8,12,15, with a separate final 16 milestone. Component hashes and complete-manifest checks reject partial/corrupt restoration. Final-slot continuation from slot 15 is the only replayed training segment; no second full episode is scheduled.

Initial available disk was approximately 221 GiB. Estimated peak memory 4–8 GiB, retained checkpoint storage 4–8 GiB plus temporary write headroom, and 40–70 minutes including recovery. Guards require 10 GiB free headroom at rotation and cap checkpoint-tree storage at 10 GiB. No historical artifacts are deleted.

Per-slot metrics include pricing gradient norms/losses, parameter changes, target-update counts, terminal flags, supported/fallback rewards, replay, routing changes, client/sample counts, charging, fleet energy, elapsed time and RSS. Full checkpoints contain private local memories and are not platform-facing outputs.

## Limitations

One seed and one eight-hour development window cannot establish policy improvement or convergence. Exploration decays only according to the inherited schedule. Charging is observed without forcing events. The historical-average baseline is explicitly labeled; the later-selected Softplus CNN and historical V 3 remain unchanged.


## Completed learning and reconciliation

All 16 slots completed at 12:00 UTC /08:00 NewYork, with terminal transitions only in slot 16 and no episode truncation. Coverage exactly matches preflight:16,329 source rows,254 unchanged-invalid exclusions,16,075 eligible requests. Of these,16,058 use supported OD contexts and 17 use the reference-price fallback. There were 4,654 acceptances,11,421 rejections,4,119 assignments and 535 accepted-unmatched requests.

Successful-dispatch revenue reconciled to$99,871.42137352064: supported reward$99,491.40 plus fallback revenue$380.0213735206398. Fallback rewards were excluded from DQN replay. The 9,572 supported OD contexts generated 153,152 transitions; replay correctly retained the latest 100,000, with identity/reward checks passing after capacity rollover.

Pricing completed 128 real optimizer and 128 soft-target updates. Losses were finite (0.0326826–452.7617493); gradient norms were finite and positive (0.6411571–1697.3811035), and parameters changed every slot. Epsilon followed the unchanged optimizer-step schedule from 1.0 to 0.997568. Routing completed 76,387 local optimizer updates,629,508 sample presentations and 16 equal-participant FedAvg rounds, with verified aggregate weights and subsequent-state response updates.

The 5,000-vehicle fleet retained 500 EVs and 4,500 non-EVs. All battery, non-EV bypass, routing mask, request/reward and boundary checks passed. There were 8,241 non-STAY private routing decisions. Final total EV energy was 19,191.10357 kWh. Charging events were zero: no claim of real-event charging coverage is made; focused charging-safety tests supplement this episode.

## Recovery, resource usage and preservation

Restoration of the slot 15 checkpoint matched the primary boundary exactly. Only slot 16 was re-executed; final runtime, replay, fleet, charging, RNG, local/global routing, pricing online/target networks and optimizer fingerprints matched. Pricing losses and gradient norms also matched exactly. No second full episode or evaluation run occurred.

Primary slot execution totaled 1,720.54 seconds (28.68 minutes). File timestamps place primary process wall time at 2,238.96 seconds (37.32 minutes), including startup, checks and serialization. Peak primary RSS was 4,583,161,856 bytes (4.58 GB). Retained recovery and final checkpoints total 2,838,797,722 bytes (2.84 GB); `checkpoint_inventory.json` records resolved model paths, manifest hashes and component hashes. Temporary generations were rotated without accumulating permanent per-slot snapshots; historical checkpoints were not deleted. Post-run free space was 231.59 GB.

32 tests passed, none failed. `validation.json` and reproducible `summarize.py` additionally verify request coverage, terminal flags, recovery equality, finite gradients and revenue partitions. New implementation files are `scripts/run_full_od_development.py` and `tests/test_full_od_development.py`; shared production/runtime methodology was not changed. The new experiment manifests explicitly extend the allowed online experience window to 08:00 local, without altering existing manifests or fitted inputs.

No bounded correctness blocker remains. This is one development episode with almost-total exploration, not convergence, policy improvement, independent evaluation or a privacy result. Weather-vintage assumptions, inherited development-selected hyperparameters and zero observed charging activity remain limitations. Historical V 3, the earlier four-slot pilot and CNN models/results are preserved; March 17–31 was not accessed.

Recommended next single task: freeze a development-learning budget and a separate evaluation protocol, including stopping/model-selection criteria, before authorizing further training. No additional episode has been launched.
