# Demand forecasting protocols

Historical `final_cnn.py` and saved CNN artifacts are unchanged. The versioned
`causal_timing.py` builder corrects expanding historical-demand information timing
and explicitly labels retrospective target weather as oracle-only. It excludes
nonexistent NYC civil slots and rejects operational export.

See [timing protocol, validation and limitations](../../results_v2/cnn_demand/2026-11-17_causal_timing/README.md). No training was performed.
