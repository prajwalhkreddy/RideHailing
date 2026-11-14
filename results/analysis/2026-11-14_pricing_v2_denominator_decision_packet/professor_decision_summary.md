# Passenger elasticity: denominator methodology decision

## Executive summary

Current V2 diagnostics calculate epsilon=delta_L/delta_P, using P_base=$22.354198442390455 and L_base=4.616983790655043km. These remain candidate reference values awaiting final approval. When an observed fare is close to P_base, delta_P becomes very small. Dividing even a moderate distance deviation by that number produces a very large epsilon. A valid, ordinary fare can therefore generate an extreme ratio without being a source-data error.

Across211 observed Weather×Hour scenarios, **0 signed-valid and4 positive-valid scenarios satisfy SD<4**. Differences between hourly means account for less than0.5% of variance in every previously aggregated Weather×T group. The largest1% of squared deviations contributes over50% in every hourly scenario. Small denominators explain much, but not all, of this tail concentration.

Fares occur on a **$0.01 grid**, while the reference is a continuous mean. The nearest fare,$22.35, occurs408 times and differs by only$0.004198442390455, giving abs(delta_P)=0.000187814490476 and approximately5324.40-fold amplification of delta_L. The next cent,$22.36, gives abs(delta_P)=0.000259528769260. These numerical sensitivities do not establish that the fares are erroneous.

Diagnostic thresholds reduce SD, but show no clear plateau. At abs(delta_P)>=0.01 (equivalent to about$0.223542 from P_base),0.481839% of positive observations are excluded; their mean falls about17.3%, although the median changes little. Median positive hourly SD remains4.71197 and only56/211 scenarios pass4. Signed outcomes differ and are reported separately. These are trade-offs, not threshold recommendations.

The governing professor-analysis rule is **combined population SD strictly below4; exactly4 is rejected**. Clustering cannot substitute for resolving unstable scenario statistics. An explicit decision is needed about the valid ratio population or estimator before further processing. This is not a blanket claim that the professor's criterion is impossible under all approved methodologies.

Three options are presented neutrally: **A**, an identification/resolution rule for small denominators; **B**, approved robust/truncated support; **C**, a scenario-level relationship estimator. None is selected. A and B require principled rules rather than choosing a cutoff just to pass4; C is a material estimator change requiring approval.

No methodology, threshold, production code or model was changed. No clustering or training was performed.

## Questions for professor

**Q1.** For valid trips where observed price is very close to global P_base, should epsilon = delta_L/delta_P still be treated as a valid observation even though the ratio becomes extremely large?

**Q2.** If not, should a minimum meaningful abs(delta_P), or equivalently minimum absolute price deviation from P_base, be defined?

**Q3.** If a minimum denominator is required, should it be based on fare measurement/resolution, an empirical distribution criterion, or another rule?

**Q4.** Alternatively, should the elasticity population be truncated/robustly bounded before calculating scenario mean and SD?

**Q5.** Would a scenario-level elasticity estimator be acceptable instead of calculating and averaging individual delta_L/delta_P ratios?

**Q6.** Should negative epsilon observations remain part of the final elasticity population?

**Q7.** Once the valid elasticity population is resolved, confirm that weather/time combinations should be accepted only when their combined population SD is strictly below 4.
