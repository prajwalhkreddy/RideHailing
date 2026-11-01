# Differential Privacy: Temporal Federated Routing

## Scope and release boundary

This is a conditional, central driver-level Gaussian mechanism at a trusted federated aggregator. A driver is the private unit. Neighboring inputs replace one driver's entire local history while holding the public client roster, per-slot participation, public covariates and other drivers' records fixed. Participation and membership are not protected. Persistent local optimizer history is private and included in this adjacency; composition covers every round in which the driver might participate.

Only the noisy global model transcript is covered by the model accountant. **This research report is not a DP-protected release of the underlying data.** Unnoised clipping summaries, validation/service metrics, prior non-private models, client buffers/Adam state and RNG state are outside that guarantee. These artifacts are for trusted internal review. Existing non-private disclosures cannot be undone by this experiment. Publishing data-dependent diagnostics needs a separate privacy analysis or a genuinely public evaluation dataset.

## Unchanged temporal contract

All 576 March1–12 slots use the existing 169→64→32→9 network, masked cross-entropy, latest32 observations from persistent capacity1000 local buffers, persistent per-client Adam(.001), current-slot contributors only, equal eligible-client weights and next-slot broadcast. Initialization is the exact saved seed42 construction. All646,657 March13–15 observations form the held-out routing comparison; they do not select C or noise. No experiences were regenerated. The non-private checkpoint is untouched and its saved metrics reproduced. Protected final-evaluation data was not accessed.

## Clipping, noise and accounting

Each client update is its locally trained model minus the common global model. Its concatenated global L2 norm is clipped at **C=1.0**, an experimental parameter. The aggregator averages clipped updates and adds independent Gaussian noise with coordinate SD **sigma×2C/n_t**. Replace-one-driver sensitivity is2C/n_t. No experience-count weights or local DP claim are used.

The conservative accountant uses RDP(alpha)=alpha/(2sigma²) per round, adds576 rounds, and converts using min_alpha[RDP+log(1/delta)/(alpha−1)]. Delta=1e-5 is experimental. Orders and per-round/cumulative RDP are in privacy_accounting.csv; every-round epsilon is in privacy_accounting_trajectory.csv. There is **NO_SUBSAMPLING_AMPLIFICATION**. The Gaussian RDP/composition rule follows [Mironov, Rényi Differential Privacy](https://arxiv.org/abs/1702.07476).

Training initialization remains seed42. Privacy noise is independently seeded from OS entropy and kept secret, not generated from public seed42. Restricted trusted checkpoints preserve its state for exact continuation. Public bit-for-bit regeneration of secret noise is incompatible with the stated privacy boundary. Model-only output is reproducible from trusted state; fresh runs use fresh noise. The implementation uses NumPy float64 Gaussian sampling and float32 postprocessing; no hardened finite-precision sampler audit or certified production guarantee is claimed.

Releasing all three noisy model transcripts together composes to **epsilon=9.53367213, delta=1e-5**, not to the smallest individual epsilon. Repeated viewing of the same model adds no mechanism, but independent reruns require additional composition.

## Before/after routing quality

| Metric | NON_PRIVATE | DP_EPS8 | DP_EPS4 | DP_EPS2 |
| --- | --- | --- | --- | --- |
| CE | 0.291658 | 0.830102 | 2.042319 | 19.522398 |
| Brier | 0.093054 | 0.184402 | 0.248193 | 0.550814 |
| ECE | 0.015838 | 0.049829 | 0.119384 | 0.274712 |
| accuracy | 0.949363 | 0.900448 | 0.875446 | 0.723496 |
| non_STAY_accuracy | 0.006195 | 0.005695 | 0.051128 | 0.052943 |
| non_STAY_CE | 5.140560 | 10.395219 | 29.416439 | 211.529834 |
| STAY_predicted_share | 0.997886 | 0.942913 | 0.915376 | 0.760957 |
| mean_entropy | 0.187676 | 0.233675 | 0.093404 | 0.004536 |
| epsilon | not applicable | 8.000000 | 4.000000 | 2.000000 |
| delta | not applicable | 0.000010 | 0.000010 | 0.000010 |
| noise_multiplier | 0.000000 | 16.568484 | 31.105963 | 59.983001 |
| clipping_fraction | not applicable | 0.000000 | 0.000000 | 0.000000 |

Accuracy/share values are fractions. Multiclass Brier sums nine squared errors. ECE uses ten confidence bins. All variants use identical masks and validation observations; invalid-action counts are zero. Absolute and relative changes for every metric are in routing_before_after.csv.

## Action distribution and utility interpretation

| model | UTILITY_IMPACT | PRIVACY_UTILITY_TRADEOFF | predicted_action_total_variation | CE_relative_change | Brier_relative_change |
| --- | --- | --- | --- | --- | --- |
| DP_EPS8 | SEVERE | UNFAVORABLE | 0.057087 | 1.846147 | 0.981668 |
| DP_EPS4 | SEVERE | UNFAVORABLE | 0.082511 | 6.002447 | 1.667193 |
| DP_EPS2 | SEVERE | UNFAVORABLE | 0.236929 | 65.935933 | 4.919300 |

The reporting rubric uses both relative CE and Brier degradation, predicted-action total variation, and non-STAY CE. MINIMAL requires both loss increases below10%, TV below.05 and non-STAY CE change below.5; MODERATE requires both below50% and TV below.2; other outcomes are SEVERE. These are descriptive conventions, not tuned decision thresholds. ECE, rare-action quality and probability mass must also be read alongside the categories. No universally optimal epsilon is selected. Routing action counts are argmax predictions, not simulator movements.

STAY argmax shares: NON_PRIVATE: 99.789%, DP_EPS8: 94.291%, DP_EPS4: 91.538%, DP_EPS2: 76.096%. True held-out STAY share is 95.058%. Mean total movement probability: NON_PRIVATE: 4.001%, DP_EPS8: 10.536%, DP_EPS4: 11.132%, DP_EPS2: 23.937%. The DP variants do not further collapse to STAY; stronger noise shifts probability/predictions toward movement while worsening probability quality. Increased rare-action top-1 accuracy at some budgets does not compensate for worse non-STAY CE/Brier. No invalid actions occur.

## Clipping and training diagnostics

| model | client_updates_seen | fraction_clipped | median | P90 | P95 | P99 | maximum | participants_mean | participants_min | participants_max | local_examples_mean | final_parameter_norm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DP_EPS8 | 2653963 | 0.000000 | 0.024963 | 0.047415 | 0.056212 | 0.075024 | 0.122762 | 4607.574653 | 4175.000000 | 4997.000000 | 143141.979167 | 23.381461 |
| DP_EPS4 | 2653963 | 0.000000 | 0.023053 | 0.046163 | 0.054136 | 0.070645 | 0.123254 | 4607.574653 | 4175.000000 | 4997.000000 | 143141.979167 | 39.039484 |
| DP_EPS2 | 2653963 | 0.000000 | 0.021972 | 0.048939 | 0.057827 | 0.075562 | 0.118327 | 4607.574653 | 4175.000000 | 4997.000000 | 143141.979167 | 72.877856 |

Norm summaries are pre-clipping aggregate trusted diagnostics, not individual update tensors. Near-zero clipping means C is loose and noise may dominate actual update scale; near-total clipping means substantial clipping distortion. Neither outcome authorizes changing C here. Model hashes and full participant/example summaries are in clipping_statistics.csv. No validation-driven tuning occurred.

## PRELIMINARY_END_TO_END_PRIVACY_UTILITY

| model | requests | accepted | rejected | successful_assignments | accepted_unmatched | assignment_rate | revenue | driver_price_violations | operational_invariant_failures |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DP_EPS2 | 2838 | 876 | 1962 | 876 | 0 | 0.308668 | 20436.869241 | 0 | 0 |
| DP_EPS4 | 2838 | 876 | 1962 | 876 | 0 | 0.308668 | 20682.962104 | 0 | 0 |
| DP_EPS8 | 2838 | 868 | 1970 | 868 | 0 | 0.305849 | 20625.132598 | 0 | 0 |
| NON_PRIVATE | 2838 | 887 | 1951 | 887 | 0 | 0.312544 | 20595.954943 | 0 | 0 |

Where completed, the comparison uses the same authoritative episode25 pricing checkpoint, greedy actions, seed424242, identical fleet initialization and March16 00:00–02:00. No replay insertion, optimizer update or pricing training occurs; the complete learner fingerprint is unchanged. Pricing is not converged, so these are comparative development diagnostics, not final service-quality results. Detailed action distributions and request accounting are retained in the CSV/JSON outputs. Routing movement counts include charging navigation and are not identical to routing-network argmax counts.

## Validation and remaining work

Nine focused tests cover Gaussian accounting/targets, replacement sensitivity, clipping, private RNG resume, invalid input rejection, unchanged local Adam/buffer/chronology semantics and existing temporal execution equivalence. Cross-entropy uses log-space evaluation to avoid probability underflow without clipping; the eps2 saved model was re-evaluated after this evaluation-only correction, with no retraining. Model reload predictions match, final parameters/probabilities are finite, masks remain valid, and the non-private hash is unchanged. Each run retains atomic trusted resume state every16 slots and inference snapshots; trusted state must never be distributed as a DP artifact.

**SECURE_AGGREGATION_IMPLEMENTED=NO.** DP addresses leakage through released noisy models; secure aggregation addresses the aggregator's visibility of individual updates. It remains an independent next module. Pricing convergence, robustness/attack evaluation, production-grade privacy hardening and protected final evaluation remain pending. No pricing training, utility/passenger changes, CNN training or final hierarchical-completion claim occurred.

## Reproduction and files

- `scripts/train_dp_temporal_routing.py --target {8,4,2}`: isolated training; resumes each namespace's latest trusted checkpoint. Do not rerun merely to recreate a released model: new independent runs spend additional budget.
- `scripts/evaluate_dp_routing_development.py`: bounded fixed-checkpoint development comparison only.
- `scripts/report_dp_routing.py`: assemble saved results and verify baseline.
- `privacy_contract.json`: adjacency, conditional boundary, accounting and secret-state restrictions.
- `privacy_accounting.csv`, `privacy_accounting_trajectory.csv`: RDP orders/composition and round trajectory.
- `routing_before_after.csv`, `routing_action_distribution.csv`: held-out metrics and action distributions.
- `clipping_statistics.csv`: aggregate norm/participation diagnostics and final hashes.
- `privacy_utility_summary.json`: scoped gates and descriptive tradeoffs.
- `preliminary_end_to_end_comparison.csv`, when present: fixed four-slot development results.
- `models/routing_policy/dp_temporal_fedavg_eps{8,4,2}_seed42/`: isolated models, logs, accountant and restricted trusted resume state.
