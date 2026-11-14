# Professor decision packet — denominator/data resolution

Reporting only. Start with [professor_decision_summary.md](professor_decision_summary.md): a concise executive summary followed by the seven requested academic questions. No option or threshold is selected.

## Files and interpretation

- denominator_methodology_tradeoff.csv:16 rows (eight existing thresholds × two explicitly labelled sign populations). Counts, SD and global moments refer to the `population` column; positive/signed scenario pass counts are provided together for comparison. Mean/median percentage changes are relative to the matching population's threshold0 baseline. Equivalent absolute USD deviation=threshold×22.354198442390455. No source statistic was recalculated for this table.
- representative_denominator_examples.csv:419 example rows: one Light Rain T1 dominant positive row; five Fog T3 positive rows; five Heavy Rain hour05 positive rows; all408 closest-price rows at$22.35. Repeated underlying observations across categories are intentional. Each row states its variance-reference scenario and sign population. Squared deviation is (epsilon−reference mean)²; percentage divides by N×population_SD². Contributions across unrelated scenarios/populations must not be added. A/B use prior T-group references; C uses hour05 (the only observed Heavy Rain T2 hour); D uses each row's signed hourly reference.
- methodology_options.csv: neutral A/B/C comparison, all NOT_SELECTED.
- verification.json: reporting formulas, provenance, row counts and preservation checks.

## Fare resolution and provenance

The completed hourly audit verified cent-aligned fares and smallest adjacent unique-price increment$0.01. P_base is not itself an observed cent-level price. Closest fare22.35 differs by−0.004198442390455USD; abs(delta_P)=0.00018781449047585653. Fare22.36 differs by+0.005801557609545USD; abs(delta_P)=0.0002595287692598594. Epsilon amplification is1/delta_P, with sign retained. This is ratio identification/measurement sensitivity, not automatic evidence of erroneous source observations.

Reused `results/analysis/2026-11-14_pricing_v2_hourly_denominator_audit/` threshold tables, hourly statistics, resolution results and verification. Earlier T-group means/SDs came from `2026-11-14_pricing_v2_sd4_population_audit/scenario_statistics.csv`. Missing example timestamps/deltas were reconstructed from the already-safe Jan1–Mar15 cache, current1.5–75km filter and restricted processed weather join. Only requested example subsets were evaluated; no full audit, threshold analysis or clustering was rerun. All408 closest-price rows retained.

References remain candidates, unchanged. No original source cleaning, sign handling, support rule, runtime sampler, V1, production, DQN, checkpoints or freeze registry was modified. March16 and March17–31 were not reporting inputs. Six files only; earlier audit files verified byte-identical.
