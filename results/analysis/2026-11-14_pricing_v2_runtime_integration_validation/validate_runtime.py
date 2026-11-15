"""One bounded development slot per baseline. No optimizer updates."""
from pathlib import Path
import json,copy
import numpy as np,pandas as pd
from scipy.stats import ks_2samp
from src.pricing.passenger_sensitive_v2 import V2EmpiricalSensitivityProvider,sha256
from src.pricing.passenger_sensitive_v1 import PositiveEpsilonProvider
from src.simulation.passenger_sensitive_v1 import PassengerSensitiveExperiment
from src.rl.passenger_sensitive_dqn import PassengerSensitiveDQN
from src.rl.pricing_dqn import PricingAction
R=Path.cwd();O=Path(__file__).resolve().parent;cfg=json.loads((R/'config/passenger_sensitivity_v2_validation.json').read_text())
def write(name,obj):(O/name).write_text(json.dumps(obj,indent=2,default=lambda z:z.item() if isinstance(z,np.generic) else str(z),allow_nan=False))
p=V2EmpiricalSensitivityProvider(rng=np.random.default_rng(cfg['seed']),contract_path=cfg['contract_path'],expected_contract_sha256=cfg['expected_contract_sha256']);c=p.pricing
sample=p.sample_many(1000000);qs=[.05,.25,.5,.75,.95,.99];metrics=[]
for name,fn in [('mean',np.mean),('median',np.median),('population_SD',np.std)]+[(f'P{100*q:g}',lambda a,q=q:np.quantile(a,q)) for q in qs]:
 a=float(fn(p.values));b=float(fn(sample));metrics.append(dict(metric=name,canonical=a,runtime_sample=b,difference=b-a,difference_pct=100*(b/a-1)))
ks=float(ks_2samp(sample,p.values,method='asymp').statistic);metrics.append(dict(metric='CDF_distance',canonical=0,runtime_sample=ks,difference=ks,difference_pct=None));pd.DataFrame(metrics).to_csv(O/'runtime_distribution_reproduction.csv',index=False)
assert np.isin(sample,p.values).all() and (sample>=0).all();assert ks<.003 # declared generous deterministic MC sanity check, not a selection criterion
route=R/'models/routing_policy/mar01_mar12_2026_temporal_fedavg_169x64x32x9_seed42/final_march12.keras'
class Baseline(PassengerSensitiveDQN):
 def __init__(self,policy):super().__init__();self.policy=policy
 def select_action(self,state,mask,*,explore=True):
  ix=np.flatnonzero(mask)
  if not len(ix):return None
  a=int(ix[-1] if self.policy=='highest_feasible' else ix[0] if self.policy=='lowest_feasible' else ix[np.argmin(abs(np.array([.85,.9,.95,1,1.05,1.1,1.15])[ix]-1))])
  return PricingAction(a,float(np.array([.85,.9,.95,1,1.05,1.1,1.15])[a]),0.,False)
fixture=None;baselines=[];static=None;replay=[]
for policy in ['highest_feasible','lowest_feasible','neutral']:
 p.rng=np.random.default_rng(cfg['seed']);d=Baseline(policy)
 env=PassengerSensitiveExperiment(provider=p,learner=d,seed=cfg['seed'],start=cfg['development_start'],routing_checkpoint=route,validation_only=True,passenger_sensitivity_version=cfg['passenger_sensitivity_version'])
 if fixture is None:
  generated=env.requests_for_slot();fixture=sorted(generated,key=lambda z:(z.request_time,z.empirical_within_slot_offset_seconds or 0,z.request_id))[:cfg['maximum_fixture_requests']]
  assert len(fixture)>0
  rows=[];p.rng=np.random.default_rng(cfg['seed'])
  for req in fixture:
   draw=p.sample();raw=c.maximum_price(req.trip_distance_km,draw.value);pc=c.effective_threshold(raw);mask=c.feasible_mask(pc)
   rows.append(dict(request_id=req.request_id,timestamp=str(pd.Timestamp(cfg['development_start'])+pd.Timedelta(seconds=req.empirical_within_slot_offset_seconds or req.request_time*120)),origin=req.origin_grid,destination=req.destination_grid,trip_distance_km=req.trip_distance_km,sampled_epsilon=draw.value,raw_threshold=raw,effective_threshold=pc,mask=json.dumps(mask.tolist()),feasible_count=int(mask.sum())))
  static=pd.DataFrame(rows);static.to_csv(O/'request_level_validation.csv',index=False);assert np.isfinite(static[['sampled_epsilon','raw_threshold','effective_threshold']]).all().all() and (static.feasible_count>=1).all()
  p.rng=np.random.default_rng(cfg['seed'])
 state_before=p.state_dict();result=env.run_slot(copy.deepcopy(fixture),terminal=True,train_dqn=False,explore_pricing=False)
 df=pd.DataFrame(env.request_audit);np.testing.assert_array_equal(df.epsilon_c,static.sampled_epsilon)
 p.load_state_dict(state_before);expected=p.sample_many(len(fixture));np.testing.assert_array_equal(expected,df.epsilon_c) # exactly one draw per request
 assert d.training_steps==0 and result['optimizer_updates']==0 and len(d.replay)==len(fixture)
 assert result['assigned']+result['accepted_unmatched']==len(fixture);assert result['fleet_size']==5000
 assert np.isclose(df.reward.sum(),result['reward']) and (df.P_offer_USD<=df.P_accept_c).all()
 assert df.loc[df.assignment_status,'Request_ID'].is_unique
 assert all(np.isfinite(row[2]) for row in d.replay.items)
 counts=df.selected_factor.value_counts().to_dict();baselines.append(dict(policy=policy,requests=len(fixture),assignments=result['assigned'],assignment_rate=result['assigned']/len(fixture),revenue=result['reward'],unmatched=result['accepted_unmatched'],passenger_feasibility_violations=0,fleet_conservation=True,action_distribution=json.dumps(counts),optimizer_updates=0,replay_transitions=len(d.replay),routing_actions=json.dumps(result['routing_actions']),charging_decisions=result['charging_decisions']))
 replay.append(dict(policy=policy,**result));print(policy,result,flush=True)
 pd.DataFrame(baselines).to_csv(O/'v2_baseline_policy_comparison.csv',index=False)
# Pure sensitivity-only comparison: both use fixed V2 reference/action contract.
v=R/'results/analysis/2026-11-07_passenger_sensitive_pricing_v1';sup=json.loads((v/'restricted_calibration_support.json').read_text());v1=PositiveEpsilonProvider(np.load(v/'positive_epsilon_calibration.npy',mmap_mode='r'),sup['positive_support_lower'],rng=np.random.default_rng(cfg['seed']),provenance=sup,frozen=True)
comparison=[]
for label,es in [('V1_sensitivity_only_fixed_V2_references',np.array([v1.sample().value for _ in fixture])),('V2',static.sampled_epsilon.to_numpy())]:
 raw=np.array([c.maximum_price(z.trip_distance_km,e) for z,e in zip(fixture,es)]);eff=np.maximum(raw,c.P_PLATFORM_MIN);m=eff[:,None]>=c.CANDIDATE_PRICES[None,:];nn=m.sum(axis=1)
 row=dict(variant=label,N=len(es),epsilon_mean=es.mean(),epsilon_median=np.median(es),epsilon_SD=es.std(),raw_threshold_mean=raw.mean(),raw_threshold_median=np.median(raw),raw_threshold_SD=raw.std(),effective_threshold_mean=eff.mean(),effective_threshold_median=np.median(eff),effective_threshold_SD=eff.std(),forced_fraction=np.mean(nn==1),choice_fraction=np.mean(nn>1),no_feasible_fraction=np.mean(nn==0),feasible_count_distribution=json.dumps(dict(zip(*[a.tolist() for a in np.unique(nn,return_counts=True)]))))
 for i,a in enumerate([.85,.9,.95,1,1.05,1.1,1.15]):row[f'feasible_fraction_{a}']=float(m[:,i].mean())
 if label.startswith('V1'):v1m=m
 else:row['mask_change_fraction_vs_V1']=float(np.mean((m!=v1m).any(axis=1)))
 comparison.append(row)
pd.DataFrame(comparison).to_csv(O/'v1_v2_sensitivity_comparison.csv',index=False)
write('smoke_test_summary.json',dict(status='PASS',fixture_date=cfg['development_start'],fixture_requests=len(fixture),fixture_definition='first 64 chronological requests from existing January-empirical/CNN development-slot generator; bounded fixture, not full demand',slots_per_policy=1,policies=replay,learner_updates=0,checks=['fleet validation','request/assignment accounting','reward reconciliation','passenger mask validity','single draw per request','terminal replay','operational/routing/charging paths completed'],historical_checkpoint_loaded=False))
write('verification.json',dict(status='INTEGRATED_VALIDATED_NOT_TRAINED',verdict='READY_FOR_V2_TRAINING',runtime_sample_N=len(sample),runtime_CDF_distance=ks,source_contract_unchanged=sha256(p.contract_path)==p.contract_hash,config=cfg,empirical_support_hash=p.support_hash,one_sample_per_request=True,training_started=False,protected_period_access=False,V1_artifacts_modified=False))
