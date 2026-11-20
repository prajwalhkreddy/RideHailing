# Controlled repository storage maintenance

Only 180 untracked, unopened Python bytecode files outside data/models/results/results_v2/.git were removed: **2,465,792 allocated bytes (2.35 MiB)**. Exact paths and measured allocation are in cleanup_manifest.json. Candidate paths were checked against Git, the preservation register, literal references in bounded text files and open-file listings. No model, data, result, manifest, environment or Git object was deleted. Empty cache directories were left in place.

Initial du allocation: 343,468,620 KiB (327.56 GiB). After cleanup: 343,022,444 KiB (327.13 GiB). The larger net reduction is NOT attributed to our cleanup: an independent Git push/pack operation was active. Per-file verified recovery is only 2.35 MiB. APFS shared/cloned extents cannot be resolved by st_blocks; counts are allocated-block estimates, not proof of exclusive physical extents. The inventory deduplicates inode identities; symlinks were not followed. Hardlink records are in inventory.json.

Initial top-level allocated KiB: models 333,123,784; data 3,236,392; .git 2,726,700; results_v2 2,398,528; results 1,935,540; notebooks 41,996; src 2,636; tests 1,556; scripts 884; outputs 356; config 44. The inode inventory occurred later during concurrent Git activity and therefore differs from initial du. Largest 40 files and 30 directory totals are recorded there (directory totals overlap and must not be summed).

External storage, read-only measurements: project conda environment 2,507,784 KiB; ~/.cache 1,583,124 KiB; /private/tmp 4,388 KiB. No environment or external cache was removed. Git count-objects reported 2,486,542 KiB packed, 26,276 KiB loose and a 21,100 KiB temporary object; all were preserved, particularly because Git was active.

## Approval-required opportunities

The dominant family is models/pricing_dqn/source_aligned_slot_pricing_v3: approximately 330.83 GB allocated, including stage_ep02_ep10 253.81 GB and stage_ep11_ep25 51.80 GB. These are historical checkpoint/resume artifacts, not disposable caches. Episode10 authoritative state and all validated/resume evidence must remain protected. A future retention review may identify non-authoritative intermediate copies, but no byte-identical duplication or deterministic regeneration is established here. Recoverable approved space is currently **zero**; individual sizes in the candidate CSV are upper bounds, not promised savings.

Two routing validated_cache/X.npy files occupy 2.233 GB and 2.202 GB. They belong to different behavioral/reachability datasets and have different apparent sizes; they are not byte-identical copies. Preserve both pending a dependency and deterministic-regeneration review. Large JSON snapshots also differ in size. No promising same-size duplicate was established among the dominant files, so expensive duplicate hashing was not undertaken. Smaller processed Parquet/tensor/log artifacts are not the primary storage driver; no speculative deletion recommendation is made.

approval_required_candidates.csv provides exact large-file paths, sizes, purpose, unresolved dependencies, disposition and maximum potential savings. This is a preliminary retention review list, not a certified deletion list. Existing research and configuration references make automatic deletion inappropriate.

## CNN storage gate

After cleanup df reported 2,409,316 KiB available. The new CNN has a small checkpoint and <50 MiB expected outputs; training requires a conservative 512 MiB free reserve and keeps tensors in memory. Existing CNN sources/checkpoint/data fingerprints are checked by the reused preflight. No large tensor duplication is authorized. The new experiment and model use separate versioned directories.
