# Passenger-Sensitive Pricing V1 Methodology

## Frozen construction

Global P_base_USD=21.34586956773507 and L_base_km=4.856998243316242 are the explicitly approved constants; source provenance for L_base is3.01799878914405 raw miles×1.609344. L_gg_prime is actual passenger OD trip distance in km. No contextual bases, d_min branch or passenger-specific lower-bound function.

P_c=P_base+(P_base/epsilon_c)*((L_gg_prime-L_base)/L_base). epsilon_c is finite, positive and>=configured epsilon_min>0. P_c is passenger maximum acceptable fare; it is not clipped or forced above zero/base/platform minimum. Epsilon is a positive behavioural calibration parameter, not conventional signed price elasticity. TLC completed trips do not identify passenger acceptance elasticity.

The seven platform factors [0.85,0.90,0.95,1.00,1.05,1.10,1.15] are experimental bounds, not empirical NYC fare extrema. Candidate price=factor×global P_base. Mask price<=P_c before selection and target maximization, equality allowed. Empty mask gives no offer, no acceptance test, no dispatch, no action or replay entry; never passenger rejection. No post-selection clipping.

## Calibration source and authorization

No genuine response-labelled source was identified in targeted authoritative/review artifacts. Record-029 signed epsilon remains unchanged and serves only as a POSITIVE_BEHAVIOURAL_CALIBRATION_PROXY after taking absolute values. User explicitly authorized recomputing the existing signed P0.5–P99.5 support rule using finite VALID Jan1–Mar15 observations only. Historical full-Jan–Mar support is neither reused numerically nor overwritten. Existing global P/L references remain frozen by explicit instruction.

Restricted signed support: [-13.015243941767071, 15.578121828868387], inclusive; then positive absolute values. Eligible N=8,598,746. Proxy samples are empirical rows with replacement, preserving duplicates, caller-controlled RNG. A global eligible pool is used; no time-group model is selected or presumed valid for the transformed proxy. No new epsilon upper cap is applied beyond this explicitly authorized source-support filter.

## Floor comparisons and remaining decision

Only NO_FLOOR diagnostic and positive P0.5/P1/P2.5/P5 were evaluated. Candidate diagnostics pair each historical distance with its own proxy epsilon; they are descriptive completed-trip calculations, not observed acceptance or independent runtime resampling. All P_c values are finite already under NO_FLOOR. Candidate floors shrink extreme magnitudes, but the supplied rules provide no distinct numerical/plausibility cutoff to justify one uniquely. **EPSILON_MIN_RECOMMENDATION=RESEARCH_DECISION_REQUIRED**. No choice based on reward, acceptance or assignments. Historical zeros/nonfinite/status exclusions are reported separately; nonfinite invalid-status counts overlap, not additive populations.

The two-slot mechanics fixture uses P0.5 **diagnostically only**, not as a recommendation or frozen setting. Long training fails closed unless provider provenance explicitly marks epsilon_min FROZEN and matches the configured value. Fresh model initialization is allowed without selecting a behavioural floor; it is not a training launch.

## Decision, replay and training boundaries

Individual request decisions preserve the13D contextual state and seven outputs. Next state is next actionable request, possibly across slots; no-offer events still advance time. gamma_eff=0.99**(delta_t_minutes/30), no artificial time spacing. Terminal target=reward. Target maxima respect next masks; empty nonterminal masks fail. Reward=assigned gross fare, accepted-unmatched zero. No artificial penalties.

Slot completion performs8 updates only with finalized replay>=1000; otherwise0. Request count never triggers optimization. Adam0.001/Huber/batch64/capacity100000/tau0.005 and exploration1→0.05 over50000 optimizer updates remain. A new environment/provider RNG is required between episodes while the same trained learner/replay/counters persist. See request_level_architecture.md.

March17–31 remains excluded from all new calibration/selection/training/evaluation. No old episode25 weights, replay, optimizer or counters were loaded. Old run status is PRE_REFORMULATION_PRICING_PROVENANCE. No long training occurred.
