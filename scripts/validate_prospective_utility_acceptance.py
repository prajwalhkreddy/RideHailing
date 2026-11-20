"""Bounded prospective engineering acceptance; no training."""
import sys,json,time,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np,pandas as pd
import scripts.validate_od_fallback_acceptance as old
from src.simulation.research_utility_routing import VERSION
from src.simulation.information_cutoff import validate_manifest
from src.simulation.od_pricing_checkpoint import save_od_checkpoint,load_od_checkpoint
OUT=Path('results_v2/simulation/2026-11-17_prospective_utility_acceptance')
OUT.mkdir(parents=True,exist_ok=True)
CAL='results_v2/simulation/2026-11-17_prospective_acceptance_v1/sampling_contract.json'
ROUTING=OUT/'routing_contract.json'
def setup():
 ROUTING.write_text(json.dumps(dict(version=VERSION,learned=False,probabilities='idle-fleet deterministic-action frequencies; empty-grid STAY',utility='existing operational_interface.decide'),indent=2)+'\n')
 old.OUT=OUT;old.CAL=CAL;old.ROUTING=str(ROUTING)
 inputs=old.make_inputs()
 # Persist/reuse January popularity, not the inherited full-period artifact.
 pop=OUT/'january_popularity.json';pop.write_text(json.dumps(inputs['popularity'],sort_keys=True))
 def rec(path,start,end,last,version):return dict(path=str(Path(path).resolve()),sha256=old.sha(path),source_start=start,source_end_exclusive=end,latest_observation=last,fitting_cutoff=end,methodology_version=version)
 prior=pd.read_parquet('data/processed/cleaned_trips.parquet',columns=['tpep_pickup_datetime','fare_amount'],filters=[('tpep_pickup_datetime','>=',pd.Timestamp('2026-01-01')),('tpep_pickup_datetime','<',pd.Timestamp('2026-01-25 18:30'))])
 prior=prior[np.isfinite(prior.fare_amount)&(prior.fare_amount>0)]
 assert len(prior)==2898376 and np.isclose(prior.fare_amount.mean(),20.233906794701575,rtol=0,atol=1e-10)
 last=str(prior.tpep_pickup_datetime.max().tz_localize('America/New_York'))
 january=pd.read_parquet(old.BASE/'trips_jan_mar_2026.parquet',columns=['tpep_pickup_datetime'],filters=[('tpep_pickup_datetime','>=',pd.Timestamp('2026-01-01')),('tpep_pickup_datetime','<',pd.Timestamp('2026-02-01'))])
 janlast=str(january.tpep_pickup_datetime.max().tz_localize('America/New_York'))
 a={'sensitivity':json.loads(Path('results_v2/simulation/2026-11-17_prospective_acceptance_v1/information_contract.json').read_text())['artifacts']['sensitivity']}
 start='2026-01-01T00:00:00-05:00';feb='2026-02-01T00:00:00-05:00';mar='2026-03-01T00:00:00-05:00'
 a['routing']=dict(kind='NONLEARNED',path=str(ROUTING.resolve()),sha256=old.sha(ROUTING),methodology_version=VERSION,fitted_observations=0)
 a['od_support']=rec(old.SUPPORT,start,feb,janlast,'POSITIVE_OBSERVED_JANUARY_SUPPORT')
 for role,path in [('forecast',OUT/'january_historical_average.csv'),('popularity',pop)]:a[role]=rec(path,start,feb,'2026-01-31T23:30:00-05:00','JANUARY_HISTORICAL_STATISTICS_V1')
 for role,path in [('driver_profiles','data/processed/driver_preferences_seed42.parquet'),('operational_prior',old.BASE/'fare_bootstrap_legacy_cutoff.parquet')]:a[role]=rec(path,start,'2026-01-25T18:30:00-05:00',last,'VERIFIED_JAN25_PRIORS_V1')
 m=dict(version='PROSPECTIVE_INFORMATION_CUTOFF_V1',artifacts=a,permitted_cutoffs=dict(sensitivity=mar,od_support=feb,routing='2026-03-12T00:00:00-04:00',forecast='2026-03-11T23:30:00-04:00',popularity=feb,operational_prior=mar,driver_profiles=mar))
 validate_manifest(m);(OUT/'information_contract.json').write_text(json.dumps(m,indent=2)+'\n')
 config=json.loads((OUT/'fallback_run_config.json').read_text());config.update(routing_available_local=None,routing_source_end_local=None,research_limitations=['Non-learned routing; no federated learning or DP.','References/grouping/action design remain development-tuned; not independent model selection.','Weather availability is assumed 120 minutes; realized passenger weather is retrospective environmental context.','Untrained pricing; no performance claims.'],routing_contract=VERSION)
 (OUT/'fallback_run_config.json').write_text(json.dumps(config,indent=2)+'\n')
 return inputs,m

def run():
 inputs,m=setup();support=json.loads(Path(old.SUPPORT).read_text())
 def new():return old.ODPricingRuntime(start='2026-03-12',routing_checkpoint=str(ROUTING),research_routing=True,information_contract=m,seed=42,utc_inputs=inputs,od_support=support,sensitivity_contract=CAL,fallback_contract=old.POLICY)
 r=new();checks=[];metrics=[]
 for i in range(4):
  begin=time.perf_counter();rows=r.run_slot();checks.append(old.digest_state(r))
  assert all(x['accepted']==(x['P_offer']<=x['P_max']) for x in rows)
  assert np.isclose(sum(x['reward_contribution'] for x in rows),r.system_revenue)
  assert len(r.engine.fleet.vehicles)==5000 and all(np.isfinite(v.energy_level) and v.energy_level>=0 for v in r.engine.fleet.vehicles)
  metrics.append(dict(r.fallback_audit[-1],total_requests=len(rows),accepted=sum(x['accepted'] for x in rows),assigned=sum(x['dispatch_outcome']=='ACCEPTED_AND_ASSIGNED' for x in rows),seconds=time.perf_counter()-begin))
  pd.DataFrame(metrics).to_csv(OUT/'slot_metrics.csv',index=False);print('primary slot',i+1,flush=True)
 assert len(r.audit)==4137 and sum(x['is_fallback'] for x in r.audit)==2
 repeat=new()
 with tempfile.TemporaryDirectory(prefix='prospective_utility_') as tmp:
  for i in range(4):
   repeat.run_slot();assert old.digest_state(repeat)==checks[i]
   if i==1:
    save_od_checkpoint(repeat,Path(tmp)/'checkpoint')
    resumed=load_od_checkpoint(Path(tmp)/'checkpoint',master_math=True,utc_mode=True,fallback_contract=old.POLICY,information_contract=m)
   print('repeat slot',i+1,flush=True)
  for i in range(2,4):resumed.run_slot();assert old.digest_state(resumed)==checks[i];print('resume slot',i+1,flush=True)
 pd.DataFrame(r.demand_audit).to_csv(OUT/'request_reconciliation.csv',index=False)
 pd.DataFrame(r.audit).to_csv(OUT/'request_outcomes.csv',index=False)
 (OUT/'validation.json').write_text(json.dumps(dict(status='PROSPECTIVE_ENGINEERING_ACCEPTANCE_PASSED',slots=4,requests=len(r.audit),metrics=metrics,repeat=True,resume=True,checks=checks,training=False,optimizer_updates=0,charging_events=len(r.engine.charging_events),fleet=5000),indent=2)+'\n')
if __name__=='__main__':
 try:run()
 except Exception as e:
  (OUT/'blocker.json').write_text(json.dumps(dict(error=type(e).__name__,message=str(e)),indent=2));raise
