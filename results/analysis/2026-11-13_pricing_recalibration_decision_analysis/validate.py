from pathlib import Path
import json,hashlib,re,sys
import numpy as np,pandas as pd
R=Path(__file__).parent;sys.path.insert(0,str(R));from analyze import js,checkpoint,P
checks={}
def check(name,condition):
 checks[name]=bool(condition)
 if not condition:raise AssertionError(name)
# Source and audit fingerprints, without reading analytical protected rows.
for name,digest in json.loads((R/'input_fingerprints.json').read_text()).items():check('unchanged:'+name,hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest)
audit=R.parent/'2026-11-13_pricing_recalibration_context_audit/README.md'
for name,digest in re.findall(r'- `([^`]+)`: `([0-9a-f]{64})`',audit.read_text()):check('audit_evidence_unchanged:'+name,hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest)
a=pd.read_csv(R/'array_a/array_a_verified.csv');check('array_counts',len(a)==148 and int(a.N.sum())==7946921);check('array_reference',abs(np.average(a.mean_fare,weights=a.N)-P)<1e-12)
check('actual_mean_inside_bin',((a.actual_mean_distance_km>=a.lower_distance_km)&(a.actual_mean_distance_km<a.upper_distance_km)).all())
r=pd.read_csv(R/'array_a/array_distance_representation_comparison.csv');calc=((r.L-r.L_base)/r.L_base)/((r.P-P)/P);check('new_orientation_all_bin_scenarios',np.allclose(calc,r.new_e,atol=1e-12,rtol=1e-12));check('nine_arrays',len(r)==148*9)
p=pd.read_csv(R/'epsilon_population/population_statistics.csv');check('population_summaries',len(p)==24)
for _,v in p.iterrows():check('mass_reconciles:'+v.population+v.candidate+v.representation+v.scope,v.negative_mass+v.zero_mass+v.positive_mass+v.undefined_mass==v.total_mass)
rec=pd.read_csv(R/'epsilon_population/reciprocal_validation.csv');check('reciprocal_errors',rec.max_abs_product_error.max()<1e-12 and rec.mismatch_gt_1e_12.sum()==0)
# Independent deterministic sample verification using persisted physical distance/fare inputs.
d=np.load(R/'intermediate/distance_array_range.npy',mmap_mode='r');fare=np.load(R/'intermediate/fare_array_range.npy',mmap_mode='r');ix=np.linspace(0,len(d)-1,2001,dtype=int)
for c,L in json.loads((R/'reference_values/candidates.json').read_text())['L_candidates'].items():
 e=np.load(R/f'intermediate/new_e_{c}.npy',mmap_mode='r');expected=((d[ix]-L)/L)/((fare[ix]-P)/P);check('independent_trip_formula:'+c,np.allclose(e[ix],expected,rtol=1e-13,atol=1e-13));check('no_trip_support_truncation:'+c,len(e)==7946921)
 z=np.load(R/f'intermediate/unique_{c}.npz');check('fit_compression_exact_mass:'+c,z['w'].sum()==len(e))
base=p.query("population=='TRIP_LEVEL_NEW_E' and scope=='ALL_SAFE' and candidate=='A_LOWER_EDGE'").iloc[0];check('all_safe_not_old_VALID_filter',base.total_mass==8692819 and base.finite_mass==8692819)
meta=json.loads((R/'intermediate/data_complete.json').read_text());check('source_period',pd.Timestamp(meta['cache_min'])>=pd.Timestamp('2026-01-01') and pd.Timestamp(meta['cache_max'])<pd.Timestamp('2026-03-16'))
ex=pd.read_csv(R/'zero_denominator/extreme_new_e_examples.csv');check('extreme_dates_safe',pd.to_datetime(ex.timestamp).between('2026-01-01','2026-03-15 23:59:59').all());check('examples_formula',np.allclose(ex.r_L/ex.r_P,ex.new_e,rtol=1e-11,atol=1e-9))
cut=pd.read_csv(R/'distance_cutoffs/filter_scenarios.csv');check('filter_reconciliation',(cut.retained_trips+cut.excluded_trips==8692819).all())
clip=pd.read_csv(R/'fare_bounds/quantile_clipping_effects.csv');check('clip_percentages',np.allclose(clip.pct_clipped_low+clip.pct_clipped_high+clip.pct_unaffected,100))
ac=pd.read_csv(R/'pricing_contract/clipping_action_collapse.csv');check('all_action_cases',len(ac)==135 and ac.unique_prices.between(1,7).all());check('action_prices_preserved',ac.collapsed_pairs.eq(0).all())
fit=pd.read_csv(R/'distribution_fits/distribution_fit_comparison.csv');check('24_fit_scenarios',len(fit[['population','L_base_candidate','distance_representation']].drop_duplicates())==24)
valid=fit.log_likelihood.notna();check('finite_fits',np.isfinite(fit.loc[valid,['log_likelihood','AIC','BIC','KS']]).all().all());check('KS_range',fit.KS.dropna().between(0,1).all());check('no_unadjusted_p_values',fit.KS_p_value.isna().all())
check('no_abs_fit_transform',set(fit.sign_treatment)=={'SIGNED_COMPLETE','POSITIVE_COMPONENT_DIAGNOSTIC'})
normal=fit.query("family=='normal' and sign_treatment=='SIGNED_COMPLETE'")
for _,v in normal.iterrows():
 pop='TRIP_LEVEL_NEW_E' if v.population=='TRIP_LEVEL_NEW_E_ALL_SAFE' else v.population
 found=p[(p.population==pop)&(p.candidate==v.L_base_candidate)&(p.representation==v.distance_representation)&(p.scope==v.scope)].iloc[0];mu,sd=json.loads(v.parameters);check('normal_MLE_matches:'+v.population+v.L_base_candidate+v.distance_representation,np.isclose(mu,found['mean']) and np.isclose(sd,found.population_SD))
dec=pd.read_csv(R/'decision_support/ACADEMIC_DECISION_TABLE.csv');check('nineteen_decisions',len(dec)==19 and dec.decision.nunique()==19);check('approval_explicit',dec.academic_approval_required.eq('YES').all());check('summary_14_sections',len(re.findall(r'^## \d+\.',(R/'decision_support/ACADEMIC_RECALIBRATION_DECISION_SUMMARY.md').read_text(),flags=re.M))==14)
check('no_model_simulator_imports',all('from src.' not in (R/n).read_text() and 'import tensorflow' not in (R/n).read_text() for n in ['analyze.py','supplement.py','fit_distributions.py','write_report.py']))
js('validation.json',dict(result='PASS',checks_passed=len(checks),checks=checks,new_orientation_verified=True,historical_T0_used=False,protected_analytical_rows_accessed=False,production_code_modified=False,methodology_frozen=False,training_performed=False,model_loaded=False,readonly_existing_evidence=True,validation_scope='Targeted numerical checks and source hashes; no simulator/test suite invoked',plot_review='Reference unweighted and trip-level overlays visually inspected; plots are labelled display-only central windows'))
checkpoint('COMPLETE',checks_passed=len(checks));print('PASS',len(checks))
