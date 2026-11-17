# Feasible OD pricing validation — 17 November 2026

Methodology: `FEASIBLE_OD_PRICING_V1`; reward: `SUCCESSFUL_DISPATCH_REWARD_V1`.
Authority: master document §§5.1, 5.2, 5.4 and 10. Scope: bounded OD identity and
full-runtime persistence correction, without training or historical migration.

## Established results

- One shared 13→64→64→7 pricing DQN, independent decisions over supported OD pairs.
- January support: 3,699,644 input rows; 3,616,239 generator-eligible rows;
  9,572 observed pairs. `od_feasibility.json` records exact counts, source path,
  cutoff and deterministic support hash. Existing generator validation excludes
  83,405 rows from its eligible sampling population; no data artifact is rewritten.
- Successful assignments alone determine OD/environment/replay rewards.
- Nine focused tests pass. Seventy-six bounded historical/reward regression tests
  pass; no failures or errors. The older 181-test suite was not rerun.
- Checkpoint/resume yields exact fixture audit, replay, state, fleet, charging,
  operational, learner/target weight and RNG equality. Optimizer persistence uses
  nonzero synthetic state; no gradient updates or experiment training are performed.
- Historical `results/`, model files, production engine, passenger distributions,
  grid, CNN, routing and historical V3 source remain unchanged.

## Review files

- `final_validation/validation.json`: final source/configuration hashes, Git state,
  seed, numerical reward reconciliation, command and test results.
- `final_validation/test_results.txt`: individual focused tests.
- `regression_results.txt`: bounded 76-test regression result.
- `od_feasibility.json`: January feasibility evidence.
- `preservation.json`: historical preservation checks.
- `focused_validation/`: preceding successful focused test evidence, retained.

Configuration: `config/od_pricing_validation.json`. Implementation/state/checkpoint
schema and execution instructions: `src/pricing/README.md`.
New checkpoints are versioned `FEASIBLE_OD_FULL_RUNTIME_1`; test checkpoints are
created only in temporary directories and not duplicated into this report.

## Limits and next decisions

Observed support is conservative, not a significance claim. Any stricter OD
threshold needs a research decision. The provisional price-action bounds remain
unchanged and require later master reconciliation. Forecast/demand generation,
sensitivity estimation, price-deviation EWMA, loss selection and full hierarchy/
privacy alignment are not resolved here. No full-population simulation or new
model training was performed. March17–31 observations were not used for support,
calibration, selection or evaluation.
