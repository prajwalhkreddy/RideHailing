# Canonical operational-state lifecycle trace

Inspected before production edits; no production edits were made.

ProductionExperiment owns operational/routing objects created once by configured_interfaces. OperationalGridState covers142 EPSG32118 grids with3000m cells. Approved fare-bootstrap priors precede the first decision; F_hat/H_hat initial values and smoothing coefficients come from routing_configuration.json. Historical prior cutoff is2026-01-25 18:30; the configured historical initializer rejects earlier starts. Explicit test priors are supported by the real producer.

_state_sources and route_idle use RoutingState.from_producer -> OperationalRouting.encode. It encodes candidate mu/sigma/F_hat in STAY,N,NE,E,SE,S,SW,W,NW order then H_hat for Grid_ID0..141. Vector169, mask9; no normalization; invalid candidate triples alone are zero placeholders.

run_slot dispatches actual requests, advances fleet/charging, reconciles assignment revenue, calls route_idle with current published state, then completes the operational slot. complete_slot receives requests plus charging_grid_observations(self.charging). Only ASSIGNED requests with assigned vehicle and finite offered fare contribute, attributed to origin grid. F_hat = delta*(assigned_count/30)+(1-delta)*previous. mu/sigma use alpha/beta EWMAs of assigned fare mean/population SD. With no fares mu/sigma carry forward and F_hat decays. H_hat uses kappa and grid queue waits; grids without observations carry forward. charging_grid_observations pools elapsed waits across station queues within each grid; observed empty queues yield0, nonstation grids are absent. These rules remain unchanged.

After completion the timestamp advances30minutes; next-state sources consume the updated producer. Producer timestamp guards reject future/stale access. New ProductionExperiment initializes a new producer; deterministic mid-run resume needs producer timestamp, _state, _observations, parameters, plus associated fleet/charging/request/RNG/runtime state. No V3 checkpoint lifecycle was implemented.

## Independent blocker (stop rule36)

main_slot returns nine-action grid-policy probabilities. multi_slot.py passes them unchanged to PricingContextInput for the next slot. pricing_dispatch.py calls build_pricing_context, whose frozen legacy contract requires FIVE probabilities and an eight-feature LinUCB context. A valid nine-action STAY-only vector reproduces ValueError: Routing probabilities must be five finite non-negative values.

This remains even with a valid OperationalGridState; a producer cannot reconcile incompatible pricing dimensions. No projection, diagonal dropping, renormalization, pricing migration, or test bypass is authorized here. Stop before production edits. A separate decision must specify how the legacy pricing mode is to coexist with nine-action routing. The separate V3 implementation is not implicated.

Versioned integration: main_slot/multi_slot now delegate explicit V3 execution to the existing SlotPricingV3 runtime. Its ProductionExperiment owns one OperationalGridState, updates it using existing semantics, and builds states with RoutingState.from_producer. A three-slot/three-request test retained object identity, checked142 current states each slot, legitimate F_hat recurrence and absent-fare mu/sigma carry-forward, rejected stale timestamps, and produced426 transitions without optimization. Historical five-action production execution is explicitly unavailable with the current router.
