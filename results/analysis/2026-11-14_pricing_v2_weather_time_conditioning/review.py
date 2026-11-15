"""Review saved grouping diagnostics without re-reading the calibration population."""
from analyze import *
def main():
 stats=pd.read_csv(O/'weather_code_time_statistics.csv');stats['weather_code']=stats.weather_code.astype(int)
 support=json.loads((O/'preclustering_support_rule.json').read_text())['support'];v=json.loads((O/'analysis_verification.json').read_text())
 candidates=pd.read_csv(O/'weather_cluster_candidates.csv');stability=pd.read_csv(O/'weather_cluster_stability.csv')
 best=candidates.dropna(subset=['silhouette']).sort_values(['silhouette','K'],ascending=[False,True]).iloc[0];k=int(best.K);members=json.loads(best.memberships);mapping={c:i+1 for i,cs in enumerate(members) for c in cs}
 ss={int(c):{r.T_group:r._asdict() for r in g.itertuples(index=False)} for c,g in stats.groupby('weather_code')}
 hourly=pd.read_csv(O/'reused_weather_hour_diagnostics.csv');names=dict(zip(hourly.weather_code.astype(int),hourly.weather_name))
 low=[]
 for code in sorted(set(ss)-set(mapping)):
  for group,cs in enumerate(members,1):
   distances=[];shared=[]
   for other in cs:
    t,raw,norm=pair(ss[code],ss[other]);shared.append(len(t))
    if norm is not None:distances.append(norm)
   low.append(dict(weather_code=code,candidate_group=group,N=support[str(code)]['N'],distinct_dates=support[str(code)]['dates'],supported_T_groups='|'.join(support[str(code)]['T_groups']),minimum_pair_shared_T_groups=min(shared),mean_available_distance=np.mean(distances) if distances else None,membership_evidence_sufficient=False,handling='FALLBACK_POOLED_NOT_ACTIVATED'))
 pd.DataFrame(low).to_csv(O/'low_support_nearest_group_diagnostics.csv',index=False)
 hourly_pairs=[]
 for a,b in itertools.combinations(mapping,2):
  aa=hourly.loc[hourly.weather_code.eq(a)].set_index('hour');bb=hourly.loc[hourly.weather_code.eq(b)].set_index('hour');hours=aa.index.intersection(bb.index);hours=[h for h in hours if min(aa.loc[h,'N'],bb.loc[h,'N'])>=100]
  if hours:
   md=np.array([aa.loc[h,'mean']-bb.loc[h,'mean'] for h in hours]);sd=np.array([aa.loc[h,'SD']-bb.loc[h,'SD'] for h in hours])
   hourly_pairs.append(dict(code_a=a,code_b=b,candidate_same_group=mapping[a]==mapping[b],shared_hours=len(hours),hourly_normalized_distance=float(np.sqrt(np.mean(np.r_[md**2,sd**2]))),maximum_abs_hourly_mean_difference=float(abs(md).max()),maximum_abs_hourly_SD_difference=float(abs(sd).max()),hours_a_mean_greater=int((md>0).sum()),hours_b_mean_greater=int((md<0).sum())))
 pd.DataFrame(hourly_pairs).to_csv(O/'hourly_candidate_consistency.csv',index=False)
 contributions=[]
 for a,b in itertools.combinations(mapping,2):
  shared=pair(ss[a],ss[b])[0];m=sum((ss[a][t]['mean']-ss[b][t]['mean'])**2 for t in shared);s=sum((ss[a][t]['SD']-ss[b][t]['SD'])**2 for t in shared)
  contributions.append(dict(code_a=a,code_b=b,mean_squared_component=m,SD_squared_component=s,SD_share=s/(m+s) if m+s else 0))
 pd.DataFrame(contributions).to_csv(O/'feature_family_distance_contribution.csv',index=False)
 # Comparisons are diagnostic. Stability is not replaced by an invented hard ARI threshold.
 loo=stability.loc[(stability.K==k)&stability.check.str.startswith('omit_')].copy();changes=[]
 for r in loo.itertuples():
  alternate={int(c):g for c,g in json.loads(r.membership).items()};pairs=list(itertools.combinations(sorted(set(mapping)&set(alternate)),2));flips=sum((mapping[a]==mapping[b])!=(alternate[a]==alternate[b]) for a,b in pairs)
  changes.append(dict(check=r.check,ARI=r.ARI,compared_pairs=len(pairs),co_membership_changes=flips,change_percentage=100*flips/len(pairs)))
 pd.DataFrame(changes).to_csv(O/'candidate_temporal_membership_changes.csv',index=False)
 rows=[]
 for code in sorted(ss):
  rows.append(dict(raw_weather_code=code,weather_name_if_available=names[code],weather_group='',candidate_weather_group=mapping.get(code,''),assignment_type='UNFROZEN_CANDIDATE' if code in mapping else 'LOW_SUPPORT_WEATHER_CODE',N=support[str(code)]['N'],distinct_dates=support[str(code)]['dates'],supported_T_groups='|'.join(support[str(code)]['T_groups']),support_status='SUPPORTED_FEATURES' if code in mapping else 'INSUFFICIENT_TEMPORAL_OVERLAP',mapping_status='NOT_APPROVED_FOR_RUNTIME',proposed_runtime_handling='PENDING_STABLE_MAPPING' if code in mapping else 'FALLBACK_POOLED'))
 pd.DataFrame(rows).to_csv(O/'weather_code_group_mapping.csv',index=False)
 c=json.loads(C.read_text());contract=dict(methodology_version='WEATHER_TIME_CONDITIONED_V2_PROPOSED_NOT_FROZEN',status='BLOCKED_TEMPORAL_CLUSTER_INSTABILITY',population_version=c['methodology_version'],denominator_rule=c['denominator_rule'],epsilon_policy=c['negative_epsilon_policy'],T_group_definitions=T,feature_definition='[mean_T1, SD_T1, ..., mean_T4, SD_T4]; unscaled; N diagnostic only',missing_feature_rule='No imputation; require >=100 observations in each shared group and >=3 shared groups; low-overlap codes excluded from clustering',distance_metric='Euclidean over shared features',distance_normalization='sqrt(sum squared differences / compared feature count)',clustering_method='deterministic average linkage',cluster_selection_rule='Evaluate all feasible cuts, separation, cluster sizes, threshold/date-support stability and leave-one-T-out temporal sensitivity. No scalar-only selection, forced K, or SD gate. No cut accepted due to unstable temporal membership; no new numerical stability cutoff invented.',number_of_groups=None,mapping={},best_diagnostic_K=k,best_diagnostic_memberships=members,low_support_policy='13,17,21 proposed explicit pooled fallback, not normal group assignment; runtime not activated',fallback_policy={'status':'RETAINED_EXISTING_NOT_ACTIVATED','minimum_support_N':5000,'levels':['weather_group_time_group','weather_group','time_group','global'],'source':'results/analysis/2026-11-14_pricing_v2_weather_clustering_resolved/WEATHER_CLUSTER_VALIDATION.md','note':'Existing stronger four-level hierarchy preserved under task exception; N100 is grouping feature diagnostic, not replacement runtime support threshold.'},source_artifacts=list(v['source_hashes']),source_hashes=v['source_hashes'],sd4_role='INTERNAL_STABILITY_DIAGNOSTIC')
 js(O/'weather_grouping_contract.json',contract)
 verdict='V2_TRAINING_BLOCKED_WEATHER_CONDITIONING_TEMPORAL_CLUSTER_INSTABILITY'
 status=dict(verdict=verdict,training_started=False,weather_mapping_frozen=False,conditional_supports_created=False,runtime_modified=False,baseline_run=False,March17_31_untouched=True,best_diagnostic_K=k,silhouette=float(best.silhouette),leave_one_T_out=changes,source_hashes_verified=True,reason='Best-separated nontrivial cut changes materially under removal of individual T groups; larger cuts have lower separation and singleton groups. Do not silently promote a scalar-score winner to a stable authoritative mapping.')
 for name in ['runtime_conditioning_verification.json','prelaunch_verification.json','verification.json']:js(O/name,status)
 print(json.dumps({'best_K':k,'temporal_changes':changes,'SD_component_share':sum(r['SD_squared_component'] for r in contributions)/sum(r['SD_squared_component']+r['mean_squared_component'] for r in contributions)},indent=2))
if __name__=='__main__':main()
