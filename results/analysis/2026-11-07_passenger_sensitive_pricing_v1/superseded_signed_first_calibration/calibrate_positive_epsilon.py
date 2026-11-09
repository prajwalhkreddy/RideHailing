"""Authorized Jan1–Mar15-only support recalculation and finite candidate diagnostics."""
from pathlib import Path
import json
import numpy as np,pandas as pd,pyarrow.parquet as pq
R=Path(__file__).parent
SOURCE=Path('data/processed/price_distance_sensitivity_record029/authoritative_epsilon_jan_mar_2026.parquet')
P=21.34586956773507;L=4.856998243316242

def dump(name,x):(R/name).write_text(json.dumps(x,indent=2,default=lambda v:v.item() if isinstance(v,np.generic) else str(v))+'\n')
def stats(a):
 q=np.quantile(a,[0,.01,.05,.5,.95,.99,1]);return {**dict(zip(['min','P1','P5','median','P95','P99','max'],map(float,q))),'mean':float(np.mean(a))}

def main():
 if (R/'epsilon_floor_comparison.csv').exists():print('Completed calibration reused; no repeated computation.');return
 if (R/'epsilon_positive_distribution.csv').exists():
  raw=np.load(R/'positive_epsilon_calibration.npy');distance=np.load(R/'calibration_distance_km.npy')
  prior=json.loads((R/'restricted_calibration_support.json').read_text());lower=prior['signed_support_lower'];upper=prior['signed_support_upper']
 else:
  f=pd.read_parquet(SOURCE,columns=['pickup_timestamp','epsilon','epsilon_status','trip_distance'],filters=[('pickup_timestamp','>=',pd.Timestamp('2026-01-01')),('pickup_timestamp','<',pd.Timestamp('2026-03-16'))])
  assert f.pickup_timestamp.ge('2026-01-01').all() and f.pickup_timestamp.lt('2026-03-16').all()
  valid=f.epsilon_status.eq('VALID');finite=np.isfinite(f.epsilon);v=f.loc[valid&finite,'epsilon'].to_numpy()
  lower,upper=np.quantile(v,[.005,.995])
  supported=valid&finite&f.epsilon.between(lower,upper)
  positive=supported&f.epsilon.abs().gt(0)
  raw=f.loc[positive,'epsilon'].abs().to_numpy();distance=f.loc[positive,'trip_distance'].to_numpy()*1.609344
  np.save(R/'positive_epsilon_calibration.npy',raw)
  np.save(R/'calibration_distance_km.npy',distance)
  support=dict(status='USER_AUTHORIZED_RESTRICTED_SUPPORT_RECALCULATION',calibration_start=str(f.pickup_timestamp.min()),calibration_last_timestamp=str(f.pickup_timestamp.max()),N_rows=len(f),N_valid_finite=len(v),N_positive_supported=len(raw),signed_support_lower=float(lower),signed_support_upper=float(upper),support_rule='P0.5–P99.5 of finite VALID signed Jan1–Mar15 epsilon, inclusive; then positive absolute values',quantile_method='linear',historical_support_modified=False,protected_rows_in_calibration=0,source=str(SOURCE),global_reference_exception='P_base/L_base are explicit user-frozen constants; not recalibrated.',sampling_family='EMPIRICAL_RESAMPLE',grouping='Global eligible positive pool; no new time-group selection or assumption of historical grouping validity')
  dump('restricted_calibration_support.json',support)
  qs=[0,.001,.005,.01,.025,.05,.1,.25,.5,.75,.9,.95,.99,1]
  names=['min_positive','P0.1','P0.5','P1','P2.5','P5','P10','P25','median','P75','P90','P95','P99','max']
  distribution=dict(N=len(raw),**dict(zip(names,np.quantile(raw,qs))),exact_zero_count=int((supported&f.epsilon.eq(0)).sum()),nonfinite_count=int((~finite).sum()),nonfinite_valid_count=int((valid&~finite).sum()),excluded_unsupported_count=int((valid&finite&~supported).sum()),excluded_invalid_status_count=int((~valid).sum()))
  pd.DataFrame([distribution]).to_csv(R/'epsilon_positive_distribution.csv',index=False)
 candidates={'NO_FLOOR':0.,**{name:float(np.quantile(raw,q)) for name,q in [('P0.5',.005),('P1',.01),('P2.5',.025),('P5',.05)]}}
 rows=[];arms=[];groups=[]
 for name,floor in candidates.items():
  e=np.maximum(raw,floor);pc=P+(P/e)*((distance-L)/L)
  count=np.zeros(len(e),np.int8)
  for factor in [.85,.9,.95,1,1.05,1.1,1.15]:count+=(P*factor<=pc)
  assert np.isfinite(pc).all()
  row=dict(candidate=name,epsilon_min=floor,N=len(e),fraction_floored=float(np.mean(raw<floor)),**{'epsilon_distribution_'+k:v for k,v in stats(e).items()},**{'Pc_'+k:v for k,v in stats(pc).items()},negative_Pc_count=int((pc<0).sum()),nonpositive_Pc_count=int((pc<=0).sum()),nonfinite_Pc_count=int((~np.isfinite(pc)).sum()),mean_feasible_arms=float(count.mean()),median_feasible_arms=float(np.median(count)),no_feasible_action_percentage=100*float((count==0).mean()))
  rows.append(row)
  for n in range(8):arms.append(dict(candidate=name,feasible_action_count=n,N=int((count==n).sum()),percentage=100*float((count==n).mean())))
  for label,m in [('G1',(distance<L)&(e<1)),('G2',(distance<L)&(e>=1)),('G3',(distance>=L)&(e<1)),('G4',(distance>=L)&(e>=1))]:
   groups.append(dict(candidate=name,group=label,N=int(m.sum()),epsilon_mean=float(e[m].mean()),epsilon_median=float(np.median(e[m])),distance_km_mean=float(distance[m].mean()),distance_km_median=float(np.median(distance[m])),Pc_mean=float(pc[m].mean()),Pc_median=float(np.median(pc[m])),Pc_P5=float(np.quantile(pc[m],.05)),Pc_P95=float(np.quantile(pc[m],.95)),negative_Pc_percentage=100*float((pc[m]<0).mean()),nonpositive_Pc_percentage=100*float((pc[m]<=0).mean()),no_feasible_action_percentage=100*float((count[m]==0).mean()),mean_feasible_arm_count=float(count[m].mean())))
 pd.DataFrame(rows).to_csv(R/'epsilon_floor_comparison.csv',index=False)
 pd.DataFrame(arms).to_csv(R/'feasible_arm_distribution.csv',index=False)
 pd.DataFrame(groups).to_csv(R/'epsilon_four_group_diagnostics.csv',index=False)
 dump('epsilon_min_decision.json',dict(EPSILON_MIN_RECOMMENDATION='RESEARCH_DECISION_REQUIRED',EPSILON_MIN_FROZEN=False,reason='NO_FLOOR and every permitted empirical floor produce finite P_c, without NaN/Inf/overflow. Floors progressively reduce extreme magnitudes but no specified numerical/plausibility boundary distinguishes them. No floor is selected using no-offer, assignment or revenue rates.',candidates=candidates,new_upper_cap=False,fixture_candidate='P0.5, explicitly diagnostic only; not a frozen training setting',calibration_pairing='Each eligible completed-trip distance paired with its own absolute historical epsilon for descriptive candidate comparison; no acceptance-response fit.'))
 schema=pq.ParquetFile(SOURCE).schema_arrow.names
 dump('epsilon_source_audit.json',dict(EPSILON_RESPONSE_LABELS_AVAILABLE=False,EPSILON_ESTIMATION_STATUS='CALIBRATION_ASSUMPTION',label='POSITIVE_BEHAVIOURAL_CALIBRATION_PROXY',sources=[{'path':str(SOURCE),'fields':schema,'suitability':'Completed TLC trip-derived sensitivity, no observed offers/rejections; calibration proxy only'},{'path':'results/analysis/2026-11-04_academic_review_validation/request_level_pricing_full.csv','suitability':'Simulator-generated decisions, not real response labels'},{'path':'data/processed/price_distance_sensitivity_record029/frozen_epsilon_support.json','suitability':'Historical full-period support; NOT used for V1 support values'}],scope='Targeted authoritative and review artifacts only; no real response-labelled source identified in these artifacts.',support_decision='User explicitly authorized recomputing support using Jan1–Mar15 only',proxy_used=True,protected_rows_accessed=False))
 print(json.dumps({'N':len(raw),'support':[lower,upper],'candidates':candidates,'decision':'RESEARCH_DECISION_REQUIRED'}))
if __name__=='__main__':main()
