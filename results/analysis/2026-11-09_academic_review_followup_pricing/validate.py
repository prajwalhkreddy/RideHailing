from pathlib import Path
import json,pandas as pd,numpy as np,hashlib,re
R=Path(__file__).parent;V=R.parent/'2026-11-07_passenger_sensitive_pricing_v1';j=json.loads((R/'analysis_results.json').read_text());checks={}
def check(k,b):checks[k]=bool(b);assert b,k
old=pd.read_csv(V/'review_feedback_reconciliation/sensitivity_distribution_summary.csv');new=pd.read_csv(R/'sensitivity_distribution/epsilon_distribution_statistics.csv')
for i in range(3):
 for k in ['N','mean','median','min','max']:check(f'distribution_{i}_{k}',np.isclose(new.iloc[i][k],old.iloc[i][k],rtol=1e-12,atol=1e-12))
 check(f'distribution_{i}_SD',np.isclose(new.iloc[i].population_SD,old.iloc[i].SD,rtol=1e-12,atol=1e-12))
for w in ['0p5','1']:check('fare_bins_'+w,pd.read_csv(R/f'fare_distance/fare_by_distance_{w}km.csv').N.sum()==8692819)
check('distance_band_total',pd.read_csv(R/'fare_distance/distance_band_summary.csv').N.sum()==8692819)
check('coverage_band_total',pd.read_csv(R/'action_space_validation/action_range_coverage_by_distance.csv').N.sum()==8692819)
cover=pd.read_csv(R/'action_space_validation/action_range_coverage.csv');check('coverage_exact_count',int(cover.loc[cover.category=='inside_0p85_1p15','N'].iloc[0])==1250025)
check('coverage_reconciled',np.isclose(cover.loc[cover.category=='inside_0p85_1p15','percentage'].iloc[0],14.379972710808772,atol=1e-12,rtol=0))
devpath=V/'staged_training_002/professor_review/episode25_march16_request_level_acceptance.csv';dev=pd.read_csv(devpath,float_precision='round_trip');long=pd.read_csv(R/'counterfactual_acceptance/march16_counterfactual_acceptance_request_action.csv',float_precision='round_trip')
check('development_rows',len(dev)==2838);check('long_rows',len(long)==19866);check('one_row_per_request_action',not long.duplicated(['request_sequence','factor']).any());check('forced',dev.forced_request.sum()==1559);check('choice',dev.choice_request.sum()==1279)
check('counterfactual_exact_formula',np.array_equal(long.P_offer<=long.P_accept_c,long.counterfactual_accept))
check('mask_counts_match',np.array_equal(long.groupby('request_sequence').counterfactual_accept.sum().to_numpy(),dev.feasible_action_count.to_numpy()))
check('monotone_acceptance',np.all(np.diff(long.counterfactual_accept.to_numpy(int).reshape(-1,7),axis=1)<=0))
for key in ['distance','epsilon','raw_preference']:
 g=pd.read_csv(R/f'counterfactual_acceptance/march16_acceptance_by_{key}.csv');check('group_totals_'+key,g.groupby('factor').N.sum().eq(2838).all());check('group_accepted_'+key,np.array_equal(g.groupby('factor').accepted_N.sum().to_numpy(),long.groupby('factor').counterfactual_accept.sum().to_numpy()))
raw=pd.read_csv(R/'acceptable_price/raw_preference_categories.csv');check('raw_exclusive_total',raw.iloc[:4].N.sum()==8598805)
prior=pd.read_csv(V/'review_feedback_reconciliation/raw_vs_effective_preference_summary.csv');prior=prior[prior.candidate=='T0'];check('raw_negative_matches',raw.iloc[0].N==prior[prior.category=='raw_le_0'].N.iloc[0]);check('raw_positive_below_matches',raw.iloc[1].N==prior[prior.category=='raw_positive_below_min'].N.iloc[0])
source=Path('data/processed/price_distance_sensitivity_record029/authoritative_epsilon_jan_mar_2026.parquet');refs=json.loads((V/'pricing_v1_spec.json').read_text());check('frozen_reference_constants',refs['P_base_USD']==21.34586956773507 and refs['L_base_km']==4.856998243316242)
check('all_charts_present',all((R/x['file']).is_file() for x in j['charts']))
# Add exact observed ratio examples without new selection or new calculation.
e=pd.read_csv(R/'sensitivity_distribution/epsilon_extreme_examples.csv');examples=e.groupby('selection',sort=False).head(1)
p=R/'academic_review_summary/ACADEMIC_REVIEW_FOLLOWUP.md';text=p.read_text();insertion='\nThe leading saved examples make the ratio mechanism concrete:\n\n| Selection | Fare USD | Distance miles | Relative price deviation | Relative distance deviation | Signed epsilon |\n| --- | --- | --- | --- | --- | --- |\n'
for row in examples.itertuples():insertion+=f'| {row.selection} | {row.fare} | {row.trip_distance} | {row.relative_price_deviation} | {row.relative_distance_deviation} | {row.epsilon} |\n'
insertion+='\nThese examples are consistent with a ratio becoming large when its denominator is small or its numerator large, and becoming near zero when the numerator is small relative to the denominator. This algebraic description does not identify a source error.\n\n'
text=text.replace('## 6. Current V1 epsilon support',insertion+'## 6. Current V1 epsilon support');p.write_text(text)
# Add only the authorized new evidence link, keeping current decisions intact.
canon=V/'README.md';before=canon.read_text();heading='### Post-Episode25 Academic Review Follow-up Analysis'
assert heading not in before
section=heading+'\n\nSee the [analysis-only academic review follow-up](../2026-11-09_academic_review_followup_pricing/README.md) for fare-distance, sensitivity, counterfactual acceptance and action-coverage evidence.\n\n`NO_METHODOLOGY_CHANGE_YET`\n\n`FURTHER_TRAINING_REMAINS_PAUSED`\n\n'
after=before.replace('## Original Formulation Coverage Checklist',section+'## Original Formulation Coverage Checklist');check('canonical_only_link_added',after.replace(section,'')==before);canon.write_text(after)
files=[p for sub in R.iterdir() if sub.is_dir() for p in sub.iterdir() if p.is_file()];csvcount=sum(p.suffix=='.csv' for p in files)
validation=dict(status='PASS',checks=checks,checks_passed=len(checks),charts=len(j['charts']),csv_outputs=csvcount,calibration_read_predicate='2026-01-01 <= pickup_timestamp < 2026-03-16',calibration_rows=8692819,development_source=str(devpath),source_parquet=str(source),protected_period_rows_selected=0,checkpoint_accessed=False,training_performed=False,simulation_performed=False,methodology_changed=False,canonical_readme_change='Added only follow-up heading/link/status',source_write_operations=False,known_limitation='Parquet reader applies the date predicate to historical files; no protected-date rows are selected into any analysis. Original full-period reference constants are reused by explicit instruction.')
(R/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
for p in [R/'README.md',R/'academic_review_summary/ACADEMIC_REVIEW_FOLLOWUP.md',R/'academic_review_summary/CHART_INDEX.md']:
 for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):assert (p.parent/target).exists(),target
print(json.dumps({'checks':len(checks),'charts':len(j['charts']),'csv_outputs':csvcount,'report_words':len(text.split()),'status':'PASS'}))
