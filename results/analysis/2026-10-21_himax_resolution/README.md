# Production H_i_max baseline

**H_I_MAX_RESOLVED = YES**  
**FINAL_HIERARCHICAL_RUNNER_READY = YES**

## Frozen project calibration

Every current EV-capable production driver explicitly has **H_i_max = 10.0 minutes**. This is **PROJECT_CALIBRATION**, not manuscript-derived and not an authoritative source value. Source status remains **VARIABLE_ONLY_NO_CALIBRATION**.

The methodology defines the variable but supplies no numerical calibration. A constant is deliberately preferred over unsupported driver-level heterogeneity. Future final sensitivity experiments must evaluate **[5, 10, 20] minutes**, with 10 as baseline. Those experiments were not run.

## Persisted profiles and runtime contract

`data/processed/driver_preferences_seed42.parquet`: **5,000 examined, 5,000 populated, 0 rejected**. Minimum/mean/maximum allowance are all 10.0 minutes. Original driver identifiers, price preferences, dispatch-wait preferences and row order were preserved and checked by exact DataFrame comparison.

Both `H_i_max_minutes` and the existing runner input `charging_wait_preference_minutes` are explicitly persisted with equal values. The latter is an explicit compatibility copy of the same approved allowance, allowing the runner to remain unchanged. Production reads that persisted runtime column; it does not create a value or fall back to 10. Missing/invalid runtime allowances still fail closed. The canonical named column and runtime copy must remain equal in any future profile update.

The profile metadata records project classification, rationale, units, future sensitivity values and the updated Parquet SHA-256. The profile generator was not rerun or changed; any future regeneration must explicitly preserve this frozen calibration and both columns, otherwise startup remains fail-closed.

## Validation

Nine focused tests passed; zero failed:

```sh
PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/tmp/final_cnn_matplotlib /Users/prajwalhk/miniconda3/envs/ridehailing-phd/bin/python -B -m unittest tests.test_himax_contract tests.test_himax_baseline
```

Coverage includes persistence/reload, explicit 10-minute baseline, missing/null/non-finite/nonpositive rejection, U3 profile-value forwarding, and actual final-runner startup with the default 5,000-driver fleet.

U3 and its existing H_hat safeguard are unchanged. With both H_i_max and H_hat equal to 10 minutes, **U3 = 0.6321205588285577**.

Startup accepted the 142-grid, 16×16 environment, operational state, 169-input/9-output routing policy, timed charging and 13-input/7-output pricing DQN. All 142 pricing states could be constructed. All driver allowances were accepted. **Zero slots executed; zero optimizer updates.** No March episode, sensitivity experiment, model retraining, U3 change, charging change or runner change occurred.

## Evidence and interpretation

The available sources define charging utility but do not provide a defensible numerical calibration of the driver's maximum acceptable charging wait. This conclusion is limited to the methodology/reference documents listed in `h_i_max_source_resolution.json`; it is not a claim about unavailable manuscripts.

| Source | Location | Finding |
|---|---|---|
| `notebooks/plan/ImplementationPlan/Complete_Hierarchical_RL_Implementation_Roadmap_CNN_Updated.docx` | Module 8, paragraphs 173–176 | `U3 = 1 − exp(−H_i_max / H_hat)`; variable/formula only, without a constant, distribution, generation rule or numerical bounds. |
| Same roadmap | Paragraphs 514–517 | Charging assumptions require calibration and are not numerically specified. This supports, but does not replace, the direct absence of H_i_max calibration in Module 8. |
| `notebooks/plan/Final_Module_Wise_Algorithm_Input_Output_Document.pdf` | M14, PDF pages 4 and 18 | Requires public charging availability/waiting statistics and private preferences; supplies no numerical charging-wait preference. |
| `notebooks/plan/Charging_Implementation_Step_by_Step.docx` | Paragraphs 42, 48, 135 and 159 | Describes station selection, waiting and charging progression, without calibrating acceptable queue wait. |
| `notebooks/plan/supervisor/Record-019.pdf` | PDF page 2 | Discusses charging-completion duration relative to maximum charging duration, depending on SOC and charger power. This is a different quantity and utility formulation, not a queue-wait allowance. |

DOCX paragraph positions are one-based extracted XML paragraph positions, including table paragraphs. PDF page numbers are one-based physical pages. The roadmap equation requires matching time units for H_i_max and H_hat; the current implementation expresses both in minutes. The equation alone does not choose a numerical value or time unit.

## Review artifacts

- `h_i_max_source_resolution.json`: preserved source evidence and newly approved project calibration; absence of manuscript calibration remains explicit.
- `driver_profile_contract.json`: persisted names, equality contract, baseline, profile counts, preservation checks and current/previous hashes.
- `startup_validation.json`: successful final-interface startup and nine focused tests.
- `data/processed/driver_preferences_seed42_metadata.json`: provenance and future sensitivity plan beside the populated Parquet.

The former H_i_max blocker is resolved. This readiness result supersedes the earlier blocked status in the historical runner-migration report; that historical report was not rewritten. Running the March episode remains a separate task.
