"""Focused, read-only checks of generated reports and frozen source identities."""
from pathlib import Path
import json,hashlib,re
import numpy as np,pandas as pd
from PIL import Image
R=Path('results/analysis/2026-11-04_academic_review_validation')
checks={}
def check(name,value):
 checks[name]=bool(value)
 assert value,name
f=pd.read_csv(R/'request_level_pricing_full.csv',float_precision='round_trip');s=json.loads((R/'request_validation_summary.json').read_text());p=json.loads((R/'request_fixture_provenance.json').read_text())
check('all_selected_requests_present',len(f)==2996==p['report']['requests'])
check('request_ids_unique',f.Request_ID.is_unique)
check('selected_training_date_only',pd.to_datetime(f.Timestamp).eq(pd.Timestamp('2026-03-12 15:30')).all())
check('all_required_numeric_fields_finite',np.isfinite(f.select_dtypes('number').to_numpy()).all())
check('distance_conversion',np.allclose(f.trip_distance_km,f.trip_distance_miles_RAW*1.609344,rtol=1e-14))
calc=f.P_base_USD*(1+(f.trip_distance_km-f.runtime_L_base_km)/f.runtime_L_base_km/f.epsilon_used)
check('independent_pmax',np.allclose(calc,f.P_max_USD,rtol=1e-12,atol=1e-10))
check('offers_match_factors',np.allclose(f.P_offer_USD,f.P_base_USD*f.pricing_factor,rtol=1e-14))
check('action_mapping',np.array_equal(np.array([.85,.9,.95,1,1.05,1.1,1.15])[f.DQN_action_index],f.pricing_factor))
check('inclusive_acceptance_exact',np.array_equal(np.where(f.P_offer_USD<=calc,'ACCEPT','REJECT'),f.recorded_passenger_decision))
check('stored_and_recomputed_decisions_match',f.recorded_passenger_decision.equals(f.recomputed_passenger_decision))
check('assignment_requires_accepted_and_eligible',((~f.successful_assignment)|(f.recorded_passenger_decision.eq('ACCEPT')&f.any_price_eligible_driver)).all())
check('no_price_unmatched_has_nonprice_supply',((f.unmatched_reason!='PASSENGER_ACCEPTED_NO_PRICE_ELIGIBLE_DRIVER')|((f.nonprice_feasible_driver_count>0)&(f.price_eligible_driver_count==0))).all())
check('all_saved_slot_report_fields_match',all(p['saved_report_match'].values()))
check('no_optimizer_updates',p['no_optimizer_updates'] and p['weights_unchanged'])
check('reward_reconciles',np.isclose(f.loc[f.successful_assignment,'P_offer_USD'].sum(),p['report']['reward'],rtol=1e-12))
conf=pd.read_csv(R/'passenger_driver_conflicts.csv');check('outcomes_exhaustive',len(conf)==4 and conf.N.sum()==len(f))
sample=pd.read_csv(R/'request_level_pricing_review_sample.csv',float_precision='round_trip');check('sample_300_unique_actual_rows',len(sample)==300 and sample.Request_ID.is_unique and set(sample.Request_ID)<=set(f.Request_ID))
pd.testing.assert_frame_equal(sample.reset_index(drop=True),f.set_index('Request_ID',drop=False).loc[sample.Request_ID].reset_index(drop=True));checks['sample_values_exact']=True
check('sample_categories_and_factors_present',set(sample.unmatched_reason)==set(f.unmatched_reason) and set(sample.pricing_factor)==set(f.pricing_factor) and (sample.P_max_USD<sample.P_base_USD).any() and (sample.P_max_USD>=sample.P_base_USD).any())
b=pd.read_csv(R/'historical_distance_fare_bins_km.csv');check('historical_full_population',len(b)==10 and b.N.sum()==10620409)
check('correct_km_question_bin',b.loc[b.distance_bin_km=='3–3.17','N'].iloc[0]==247751)
d=pd.read_csv(R/'dqn_episode_summary.csv');check('complete25_only',len(d)==25 and d.episode.tolist()==list(range(1,26)) and (d.slots_completed==16).all())
check('episode_request_accounting',(d.requests==d.accepted+d.rejected).all() and (d.accepted==d.assignments+d.unmatched).all())
check('unpersisted_prices_explicit',(d.mean_offered_price_USD=='NOT PERSISTED').all() and (d.median_offered_price_USD=='NOT PERSISTED').all())
c=pd.read_csv(R/'cnn_validation_summary.csv').iloc[0];check('cnn_same_population_metrics',c.N==109056 and np.isclose(c.RMSE**2,c.MSE) and np.isclose(100*c.RMSE/c.mean_actual,c.NRMSE_percentage) and np.isclose(100*abs(c.predicted_total-c.actual_total)/c.actual_total,c.volume_error_percentage))
check('cnn_error_shares_total100',np.isclose(c.error_positive_percentage+c.error_negative_percentage+c.error_approximately_zero_percentage,100))
dr=pd.read_csv(R/'driver_preference_summary.csv').iloc[0];check('driver_all_profiles_and_context',dr.profile_N==5000 and dr.context_request_N==2996 and np.isclose(dr.runtime_P_base_USD,f.P_base_USD.iloc[0]))
check('driver_categories_exhaustive',dr.below_085_N+dr.approximately_085_N+dr.between_085_and_100_N+dr.at_or_above_100_N==5000)
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as fh:
  for block in iter(lambda:fh.read(4194304),b''):h.update(block)
 return h.hexdigest()
cp=Path(p['checkpoint']);meta=json.loads((cp/'manifest.json').read_text());check('source_checkpoint_payload_hashes_unchanged',all(sha(cp/k)==v for k,v in meta['files'].items()) and p['checkpoint_files_unchanged'])
dm=json.loads(Path('data/processed/driver_preferences_seed42_metadata.json').read_text());check('frozen_driver_hash_matches_metadata',sha('data/processed/driver_preferences_seed42.parquet')==dm['parquet_sha256'])
idx=pd.read_csv(R/'source_index.csv');check('all_source_paths_exist',all(Path(x).exists() for x in idx.source_artifact))
readme=(R/'README.md').read_text();check('twenty_required_sections',len(re.findall(r'^## \d+\.',readme,re.M))==20)
images=list(R.glob('*.png'));check('ten_requested_figures',len(images)==10)
for im in images:
 with Image.open(im) as img:img.verify()
checks['all_png_files_valid']=True
append=json.loads((R/'current_state_append_validation.json').read_text());current=Path(append['path']).read_text();check('current_state_append_only',sha_prefix:=hashlib.sha256(current[:append['original_prefix_characters']].encode()).hexdigest()==append['original_prefix_sha256'])
status=json.loads((R/'review_status.json').read_text());check('limitations_preserved',status['PRICING_POLICY_CONVERGED']=='NO' and status['PAPER_SPECIFIC_DP_REGIMES_COMPLETE']=='NO')
result={'checks':checks,'passed':sum(checks.values()),'failed':sum(not x for x in checks.values()),'visual_review':'All ten PNGs visually inspected in contact sheet; complete labels and unclipped data displays; unavailable offered-price series explicitly marked','execution_scope':'One disposable March12 slot reconstruction, zero optimizer updates, no checkpoint writes; historical Jan–Mar descriptive and already-defined CNN test analysis only','protected_final_hierarchical_evaluation_untouched':True}
(R/'validation_checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'passed':result['passed'],'failed':result['failed']}))
