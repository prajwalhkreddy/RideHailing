# Historical checkpoint consolidation

Completed controlled retirement of **134 intermediate V3 per-slot recovery snapshots**, deleting **938 payload files**, **235,606,589,440 allocated bytes (219.426 GiB)**. No source, test, tracked Git file, dataset, active model, current checkpoint or unique evaluation output was deleted.

## Accounting

Repository du: 343,119,500 KiB before (327.224 GiB), 112,877,012 KiB after (107.648 GiB). Filesystem available: 2,359,416 →232,602,680 KiB, an increase of approximately 219.577 GiB. Measured per-file allocation released is 219.426 GiB. The small difference reflects concurrent filesystem/Git activity and measurement timing; not all free-space change is attributable to this task. Allocation uses st_blocks/du, not apparent lengths. APFS shared extents/snapshots cannot be conclusively identified by these tools; no snapshot/system changes were made. Hardlinks are inventoried and linked candidate files were rejected. Symlinks were not followed.

The earlier “331 GB pricing” and “327 GiB repository” figures use different units: pricing was about308 GiB, routing9 GiB, within the repository total. Nested directory sizes must not be added together.

### Fifteen largest original directory consumers (nested totals overlap)

| Path | Allocated GiB |
|---|---:|
| models | 317.379 |
| models/pricing_dqn | 308.366 |
| models/pricing_dqn/source_aligned_slot_pricing_v3 | 307.796 |
| models/pricing_dqn/source_aligned_slot_pricing_v3/stage_ep02_ep10 | 236.109 |
| models/pricing_dqn/source_aligned_slot_pricing_v3/stage_ep11_ep25 | 48.218 |
| models/pricing_dqn/source_aligned_slot_pricing_v3/episode_001 | 23.469 |
| models/routing_policy | 9.009 |
| models/routing_policy/mar01_mar12_2026_final_behavioral_169x64x32x9_seed42 | 3.469 |
| models/routing_policy/mar01_mar12_2026_reachability_169x64x32x9_seed42 | 3.440 |
| data | 3.086 |
| data/processed | 2.649 |
| .git | 2.428 |
| .git/objects | 2.427 |
| .git/objects/pack | 2.381 |
| results_v2 | 2.290 |

## Deletion evidence and retained replacements

Scope: `models/pricing_dqn/source_aligned_slot_pricing_v3/stage_ep02_ep10/episode_NNN_slot_NNN` only, excluding `episode_010_slot_015`.

The generating `scripts/train_v3_stage2.py` writes a self-contained checkpoint each slot and a completed checkpoint after slot16. Its compact slot/learning/reward/fleet/action metrics persist independently. `v3_stage2_checkpoint.py` loads components of the supplied checkpoint, not chains of earlier snapshots. Each removed snapshot has a retained completed-episode replacement. The stage LATEST pointer and current review designate Episode10. The cumulative Episode10 audit underpins the retained Episode1–10 review. A narrow literal reference scan found no active source/config/script/test consumer of the 134 selected payload sets; historical per-slot receipt references are retained as provenance.

All completed `episode_002`–`episode_010` checkpoints remain. Episode10, previous Episode1 evidence, all post-Episode10 material and all current results_v2 evidence remain. `episode_010_slot_015` is retained conservatively because a handoff test names it (as an invalid checkpoint-path fixture).

Deleted payload types: runtime.json, learner/inactive learner replay.npz and online/target.keras. Every original manifest, status and small learner metadata JSON remains in place. Each retired directory now contains RETIRED_CHECKPOINT.json identifying its retained replacement. These directories are **metadata records, not loadable checkpoints**; the recorded historical component hashes describe removed payloads. Historical receipt JSON paths intentionally resolve to these tombstones. Do not attempt slot-level resume from retired snapshots. Completed episode resume points remain available; exact intermediate learner/runtime states are not claimed reconstructible without rerunning the historical protocol.

The new explicit retention instruction supersedes the previous blanket “preserve all checkpoint artifacts” recommendation. No deleted payload appeared in the 2,279-file register, but candidates were checked regardless. Retiring unneeded recovery payloads does not imply their neural weights were byte-identical. No duplicate-content claim or regeneration-based deletion was used. No active training process or open model handle was found. Every payload was checked for repository containment, regular file type, hardlink count, Git status, open use and unchanged measured size before unlinking. No broad wildcard deletion was used.

## Integrity

262 source/test/config/master files had unchanged SHA256 values after deletion. Twelve focused tests passed (Softplus CNN, online routing provenance/checkpoint integration and historical V3 handoff), zero failed. Smoke loading passed for both causal ReLU/Softplus CNN checkpoints, Episode10 online DQN, and the retained behavioral central routing model. All weights were finite. Existing prospective OD manifest dependencies—sensitivity, fresh routing initialization, January OD mask, historical forecast, popularity, profiles and operational prior—exist. Episode10 component paths remain complete. No full historical runtime resume or training was attempted; historical code-lineage compatibility beyond the tested interfaces is not newly certified.

## Remaining storage and approvals

Largest remaining top-level allocation: pricing93,260,984 KiB (88.941 GiB), routing9,446,880 KiB (9.009 GiB), data3,236,392 KiB (3.086 GiB), Git2,545,844 KiB (2.428 GiB), results_v2 2,401,668 KiB (2.290 GiB), results1,935,540 KiB (1.846 GiB).

Further review candidates, not deletion approvals:

- `models/pricing_dqn/source_aligned_slot_pricing_v3/stage_ep11_ep25`:48.218 GiB; latest recovery pointer and unique unreviewed continuation evidence remain. Requires explicit retention decision.
- `models/pricing_dqn/source_aligned_slot_pricing_v3/episode_001`:23.469 GiB; distinct earlier protocol/recovery evidence; retain pending dependency review.
- `models/routing_policy`:9.009 GiB; required models plus validated caches; no specific safe further deletion established.

The first two families total71.687 GiB gross, but achievable savings will be lower after required checkpoints/metadata are retained. Approved additional recovery is zero. `remaining_classification.json` records classifications and reasons. No further investigation is needed to meet the substantial-recovery objective.

## Retention convention and reproduction

Keep authoritative final/best/current checkpoints and documented resume/evaluation dependencies. Intermediate recovery checkpoints are not permanent scientific outputs by default, but must pass reference, active-use and tracked-file checks before retirement. Preserve compact metrics, configuration, seeds, lineage and tombstones. Do not interpret historical audit registers as automatically permanent or silently override them. Do not change Git history or migrate data for naming consistency.

Authoritative V3 checkpoint: `models/pricing_dqn/source_aligned_slot_pricing_v3/stage_ep02_ep10/episode_010`. Review: `results/analysis/2026-11-15_source_aligned_slot_pricing_v3/review_ep01_ep10/`. Current CNNs: `models/cnn/causal_persistence_120min_2026_seed42_v1/best.keras` and `models/cnn/causal_persistence_120min_2026_seed42_softplus_v1/best.keras`. Current research dependency paths are recorded in smoke_checks.json; no current config pointer was changed.

Recheck without training: `python -B -m unittest tests.test_softplus_cnn tests.test_online_routing_provenance tests.test_v3_ep25_handoff -q`. Reproduce historical compact review from the retained Episode10 using the existing reporting script only when needed; this task did not rerun historical reporting.

Machine-readable evidence: inventory.json, plan.json, manifest.json, deletion_summary.json, source_integrity.json, smoke_checks.json, remaining_classification.json. Manifest entries contain exact deleted paths, original recorded hashes, allocated/apparent sizes, references, retained replacements, classification and deletion status. Git HEAD is recorded in inventory.json. Original metadata hashes are retained, not falsely described as newly recomputed large-file hashes.
