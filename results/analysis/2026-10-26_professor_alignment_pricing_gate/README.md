# Final pre-retraining professor-alignment gate

**Gate checks complete; READY_FOR_CORRECTED_PRICING_RETRAIN = NO.** No training, optimizer updates, simulator episode, protected March17–31 data access, runtime modification or model replacement occurred. Only the scoped reports and root README are updated.

## Exact blockers

- Acceptance source equation and relationship between calibration E and acceptance E remain unverified.
- Active FCFS dispatch lacks hard P_disp >= P_i_min eligibility.
- FedAvg probabilities fail held-out adequacy against the masked training-label prior.

## Active sampling and acceptance

Runtime E is dimensionless **Normal(mu,sigma) conditioned on E>0**, lower bound0 exclusive, upper infinity; a positive zero-SD group is deterministic. It uses an explicit persistent NumPy Generator (seed42 at initialization) passed to SciPy truncnorm for each request. Exact WeatherCode × half-hour period0–47 resolves first, then period, weather and global fallback. Parent Normal parameters are not truncated-output moments.

The243 exact groups have mu range0.8771867576610018–2.1425974738413394 and parent SD0.6443884498585853–16.276108873930255. Global fallback mu **1.1686292254531307**, SD **4.714371140724867**. Exact per-group values are in the immutable January calibration Parquets identified and hashed in `acceptance_equation_validation.json`; diagnostic resolved records are in `acceptance_request_diagnostics.json`. There is no single active Clear/Rain mu/SD. Professor analytical scenario values0.651731/1.440831 and0.650875/1.484481 are **not** substituted into this runtime.

Active code: `P_disp = factor*P_base`; `P_max = P_base + P_base*((L-D_base)/D_base)/E`; accept iff `P_disp <= P_max`. Prices are USD and both distances miles. Runtime P_base/D_base are resolved weather/half-hour means, not Record029 global references. The P_base multiplier is present and gives the additive term USD units.

This rearrangement corresponds to `E = relative_distance/relative_price`. However, persisted legacy calibration metadata defines `abs(relative_price/relative_distance)`. That orientation issue prevents claiming source alignment merely because the code is dimensionally consistent. The supervisor `customer sensitivity.pdf` pp1,7–8 leaves the equation/paper pending; the corrected implementation process gives only a verbal acceptance step; the module-wise document pp3,16 delegates to a paper equation without stating it. **ACCEPTANCE_SOURCE_EQUATION_REQUIRED = YES**. No alternative equation is invented or implemented.

A deterministic controlled request-level diagnostic used actual March16 00:00–02:00 weather/period combinations and distances0.5/1/1.5/2 times the resolved base with factors0.85/1/1.15. **48 checks passed**; repeated seed42 draws matched, fares/units and acceptance iff the active threshold matched. These are controlled request cases, not a new historical simulator episode or proof of source approval.

## Driver eligibility, accounting and state

`final_production.run_slot -> dispatch_requests(DISPATCH_MODEL_LEGACY) -> find_eligible_vehicle` checks idle/local/neighbor supply, energy and station reserve. It does not pass driver profiles or compare fare to `price_preference`. Isolated offered fares9/10/11 with a stated driver minimum10 all returned the idle driver; below-minimum failure is confirmed. U1's minimum-price preference does not implement a hard dispatch gate. No dispatch change was made.

Completed training totals: generated **1,705,916 = 536,483 accepted + 1,169,433 rejected**; accepted **536,483 = 395,492 assigned + 140,991 unmatched**. Revenue **$7490773.984343884** recognizes successful assignment fare. Passenger rejection and accepted-but-unserved requests remain distinct.

13D order: `[J_hat,J_disp_prev,I,p_STAY,p_N,p_NE,p_E,p_SE,p_S,p_SW,p_W,p_NW,destination_popularity]`. This maps to predicted demand, previous successful dispatch, known incoming passenger supply, nine routing probabilities, destination popularity. Incoming commitments must be made strictly before decision t, with dropoff in(t,t+30min]; a future-commitment boundary check rejects. Routing vectors must sum to1, respect topology masks and have nine finite entries; snapshots reject future availability/observation timestamps.

## Held-out routing probability gate

The selected frozen FedAvg model was evaluated on639,807 March13–15 observations. The no-learning empirical action prior uses only2,618,033 March1–12 labels, zeros invalid actions and renormalizes per observation mask. All actions have training support; no smoothing, class balancing or new fit was used. Brier is the mean **sum** of squared class-probability errors, not divided by9.

| Model | Cross-entropy | Multiclass Brier | Top-label ECE,10 bins |
|---|---:|---:|---:|
| FedAvg round5 | 0.538559742 | 0.245880986 | 0.092917392 |
| Masked training-label prior | 0.352059292 | 0.117621135 | 0.002955335 |

**ROUTING_PROBABILITIES_INFORMATIVE = NO** under this held-out gate: FedAvg is worse on both proper scores, not just classification accuracy. Calibration bins, mean probability vectors and true label frequencies are in `routing_probability_adequacy.json`. This is evidence against probabilistic value over this prior on this validation set, not proof of no possible downstream value. No replacement is selected.

## Proposed cadence: withheld pending prerequisites

Existing run:720 slots,288,181 inserted transitions, capacity100,000,718 optimizer updates, epsilon0.986358. Existing code makes one update per completed slot after replay>=1000; epsilon decays1→0.05 over50,000 optimizer updates. Prior adequacy diagnosis remains **TRAINING_SCHEDULE_MISMATCH**.

The proposed one-update-per-five-new-transitions rule is **not frozen, implemented or executed** because prerequisites fail. Under the specified arithmetic, exclude exactly the first1000 insertions, including a partial warm-up slot; then `floor((288181-1000)/5)=57,436` updates with remainder1. Epsilon would reach0.05 at update50,000. This volume-based estimate is conditional: altered pricing could change future transition counts. Exactly-once implementation would persist total committed insertions, update-eligibility counter/remainder, optimizer state/count, epsilon position, replay and RNG. All other frozen DQN settings and schedule remain unchanged. No repeated70-pass alternative, compressed epsilon schedule or replacement routing model is authorized by this report.

## Professor Discussion Requirements / Verification Status

| Requirement | Status | Evidence / next action |
|---|---|---|
| Passenger elasticity sampling | VERIFIED | Active legacy positive truncated Normal, weather/half-hour calibration; not the two analytical scenario distributions. Source alignment remains open. |
| Acceptance equation | VERIFICATION_REQUIRED | Active equation tested; exact professor/paper equation not established. |
| P_base multiplier | VERIFICATION_REQUIRED | Multiplier is present and dimensionally correct in active code; source/calibration orientation unresolved. |
| Passenger rejection vs dispatch failure | VERIFIED | Completed-run accounting identities pass; categories remain distinct. |
| P_disp >= P_i_min | IMPLEMENTATION_REQUIRED | Absent from active FCFS eligibility, independent of U1. |
| 13D DQN state / incoming supply | VERIFIED | Exact ordered13 features; commitments strictly before t, arrivals in(t,t+30min]. |
| Routing utilities / EWMA | VERIFICATION_REQUIRED | Existing frozen formulas/reports preserved; no new numerical revalidation in this narrow gate. |
| FL aggregation | VERIFIED | Existing final training report verifies five driver-client sample-weighted rounds, zero-client exclusion and reload; no new FL executed. |
| Routing convergence/probabilities | KNOWN_LIMITATION | FedAvg worse than masked training-action prior on held-out CE/Brier; informative=NO. |
| Pricing convergence | KNOWN_LIMITATION | 718 updates; schedule mismatch; two-hour development advantage is not convergence. |
| Non-private baseline before DP | VERIFICATION_REQUIRED | Completed run retained but NOT_FINAL_NONPRIVATE_BASELINE; resolve prerequisites before corrected retrain. |
| DP mechanism | FUTURE_PHASE | Specify clipping, noise, epsilon_DP, delta_DP, accounting and privacy–utility trade-off after validated non-private baseline. |
| Consistent evaluation periods/metrics | VERIFIED | Jan–Feb CNN train; Mar1–15 RL; Mar16 development; Mar17–31 protected. Development results not final evaluation. |

## Files and next step

The nine requested JSON reports accompany this README. Root README retains its numbered structure and historical sections, updates current runs/statuses/resume guidance, and links here. `root_readme_update_validation.json` records local checks of modified/additional links and explicit current model/report paths; no external-link crawl was performed.

Resolve the three exact blockers before approving/implementing cadence and resetting seed42 for corrected training. March17–31 remains protected, and DP remains a later phase requiring clipping/noise/privacy-budget specification and privacy–utility evaluation after a validated non-private baseline.
