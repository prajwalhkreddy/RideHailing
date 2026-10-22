# First short hierarchical DQN episode — blocked before execution

**SHORT_HIERARCHICAL_EPISODE_READY = NO.** The requested March 16, 2026 00:00–02:00 episode (seed 42, four slots) did not begin. No requests were processed, no transitions collected, no optimizer/FedAvg updates executed and no checkpoint saved. No episode performance or conservation results are available.

## Reproduced startup blocker

Calling `ProductionExperiment(project_root, seed=42)` raises:

> Legacy January/5-action production runner is superseded. New 16x16 CNN and 9-action routing models must be trained before running the migrated environment.

The guard is at `src/simulation/production.py:185–186`. Its wording is stale: the final CNN and structurally valid routing checkpoint already exist. Additional model training is **not** the prerequisite identified by this check.

The full runner still requires the legacy 1,213-grid domain behind that guard (`production.py:244–245`). Its main-slot loop uses legacy routing features/state and utility selection (`main_slot.py:207–222`), rather than the final operational-state interface. It also calls `ChargingInfrastructure.present_vehicle` for low-energy vehicles (`main_slot.py:95–96`); that method explicitly transfers vehicles to stations with zero travel time/energy. Removing the guard alone would therefore not satisfy the frozen final routing/charging and timing contracts.

The preceding bounded pricing-DQN fixture directly connected selected new interfaces. It did not replace the full hierarchical production orchestrator. The general multi-slot runner calls the same legacy main-slot function, so it is not an alternative final episode path.

## Scope respected

The request explicitly requires stopping on a genuine integration blocker. No guard was bypassed, no synthetic request fixture substituted for real flow, no real episode partially executed, and no unrelated migration undertaken. Only this blocked-attempt README/configuration/validation record was created. Models, calibration, DQN hyperparameters, existing results and simulator code remain unchanged.

The startup guard was reproduced; unit suites were not rerun after the blocking condition. Slot metrics, action distributions, loss/reward/fleet summaries and a short-run checkpoint are deliberately absent because no episode generated them.

## Prerequisite

Migrate/wire the full hierarchical main-slot runner to the final 142-grid operational-state, 169-feature routing, timed charging-navigation and 13D pricing-DQN interfaces, preserving real request flow and the established temporal/update cadence. Validate that orchestration before retrying this same four-slot episode. This migration was not executed here, in accordance with the stop instruction.
