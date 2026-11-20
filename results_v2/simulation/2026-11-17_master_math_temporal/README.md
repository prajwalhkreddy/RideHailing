# OD mathematical correction and temporal boundary

## Completion status

**Mathematical correction implemented and tested; full temporal integration incomplete.**
Use `ODPricingRuntime(..., master_math=True)` only as an explicitly non-operational
bounded research mode. Historical/default OD fixtures and V3 retain their former
semantics. `operational=True` fails before artifact loading. No experiment training
or production simulation was launched. Unit tests perform small synthetic optimizer
updates and bounded fixture transitions only.

## Master mathematics

Authority: `notebooks/plan/masterdocument/MASTER DOCUMENT1.docx`, §6 (5)–(8), §10.3.
For successful fares p within a completed 30-minute slot:

- μ_new = α mean(p) + (1−α) μ_previous.
- σ_new = β mean(abs(p−μ_previous)) + (1−β) σ_previous.
- F_new = δ N/30 + (1−δ) F_previous, stored in dispatches/minute.
- H_new = κ H_observed + (1−κ) H_previous, stored in minutes.

The original state class remains unchanged. The new `MasterOperationalGridState`
uses a distinct contract `MASTER_PREVIOUS_MEAN_ABSOLUTE_DEVIATION_V1` and reports
observed previous-mean absolute deviation separately; it does not relabel this
quantity as population SD. With no dispatch, retain μ and σ and decay frequency
using the observed zero count. Missing wait observations retain H; an observed
empty charging queue is a zero wait observation. Raw zero deviation is preserved;
existing positive `sigma_floor` applies only to downstream denominator consumption.

The existing explicit project α=β=δ=κ=0.3 values are retained, not presented as
manuscript calibrations. Master meeting guidance suggests 0.1–0.2/0.125; that
hyperparameter discrepancy remains documented for a separate decision. No tuning
was performed. Waits can be converted to the master's slot units by dividing both
H and driver tolerance by 30; the existing minute-based utility ratio is unchanged.
The existing queue-weighted elapsed-wait observation definition is retained.

A diagnostic previous state [10 USD, 2 USD, 1 dispatch/minute, 4 minutes], fares
[20,30] and observed wait10 produces [14.5,5.9,0.72,5.8]. An empty slot with no wait
observation produces [10,2,0.7,4].

## Bellman contract

Opt-in `MASTER_HALF_SQUARED_BELLMAN_V1` computes
`y = reward + gamma * (1-terminal) * max_a Q_target(next_state,a)` and
`loss = mean((y-Q_online(state,collected_action))**2)/2`.
The target is gradient-stopped; Adam updates the primary weights, then
`target = (1−tau)*target + tau*online`. Epsilon-greedy still collects actions;
no epsilon-random action enters bootstrap calculation. Successful-dispatch rewards
remain unchanged. The seven-action 13→64→64→7 architecture is unchanged.

Retained defaults: γ0.99, Adam learning rate0.001, batch64, capacity100000,
warm-up1000, tau0.005, epsilon1→0.05 over50000 optimizer updates, seed42.
The mathematical mode accepts validated `DQNConfig`, including warm-up. These are
project hyperparameters, not numerical requirements imposed by the equations.
The illustrative 1.5×batch warm-up is not silently substituted for the validated1000.

## UTC boundary and remaining integration work

`master_od_contract.py` provides explicit UTC conversion from verified NY civil
labels, half-hour boundaries, elapsed arrival/arrival-slot mapping, and stable
request ordering by UTC pickup plus source identity. Invalid/ambiguous civil times
raise rather than dropping rows. March8 01:55 EST plus10 minutes is03:05 EDT;
01:30 EST plus30 minutes is03:00 EDT. Mini-slots use elapsed120-second offsets.

**These helpers do not yet replace the production engine's clocks.**
`final_production.py` requires naive starts; `_state_sources` loads legacy artifacts;
`historical_request_replay.py` filters naive civil intervals and calculates naive
pickup/dropoff differences; `dqn_contract` timestamp/ledger/commitment consumers
also require naive timestamps. Replacing only the outer clock would either fail or
misinterpret DST and fleet events. The UTC helpers therefore are not represented
as demonstrated end-to-end charging/repositioning or episode-termination corrections.
The existing16-slot research horizon is unchanged. Request counts are not altered.

## Forecast boundary and sensitivity

The existing versioned persistence adapter checks forecast target/issuance, grid IDs,
fractional nonnegative demand and checkpoint/weather fingerprint. It rejects oracle
or mismatched checkpoint contracts, and rejects operational use because weather
publication/vintage provenance is unverified. Its seven-channel/142-grid protocol
remains unchanged. The new OD operational-start gate prevents claiming that the old
forecast loader satisfies this boundary. No causal forecast is newly generated.

Weighted sensitivity, successful-dispatch reward, observed OD support and historical
request replay contracts are preserved. No sensitivity, CNN or routing model changes.

## Checkpoint/resume

OD runtime schema4 records mathematical mode, the explicit **legacy temporal blocker**
and **unverified forecast provenance**, rather than falsely recording UTC/causal
integration. The new operational state is serialized by an explicit OD-only conversion
to the existing value codec and restored to its versioned class; V3 codec is unchanged.
Source hashes include the mathematical and temporal helpers. Loads require an explicit
matching `master_math` mode; older/mismatched schemas and loss contracts are rejected.
Learner config, optimizer, RNG and replay are persisted. Synthetic resumed optimizer
updates match exactly; bounded runtime continuation matches operational state,
pricing states and replay identities. Full UTC-runtime resume is not claimed.

## Evidence and next task

See `tests.txt` and `validation.json` for bounded results, fingerprints and preservation.
Tests cover exact recurrences, empty/zero cases, squared loss, max-Q/terminal targets,
soft updates, configurable warm-up, DST helper arithmetic, request ordering, reward
consistency, metadata rejection, mode rejection and deterministic fixture resume.
Legacy tests were not weakened. Historical files/models/results remain untouched.

**Next single task:** migrate the OD-only production adapter, ledger/commitments,
request-source boundaries and checkpoint reconstruction together to aware UTC, using
explicit research-only validated forecast fixtures until genuine operational weather
provenance exists. Include fleet movement/charging/DST resume and terminal tests.
Do not call the present package full master or operational compliance.
