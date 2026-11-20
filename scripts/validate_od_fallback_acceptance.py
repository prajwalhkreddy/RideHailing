"""Four-slot research acceptance only: no optimizer, training or mask expansion."""
import hashlib,json,time,tempfile,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np,pandas as pd
from src.demand.causal_timing import CHANNELS,timing
from src.demand.persistence_weather import contract,fingerprint,select_weather
from src.simulation.utc_od_inputs import BASELINE
from src.simulation.master_od_contract import utc
from src.simulation.od_pricing_runtime import ODPricingRuntime
from src.simulation.od_pricing_checkpoint import save_od_checkpoint,load_od_checkpoint
from src.simulation.v3_checkpoint_codec import encode
from src.pricing.unseen_od import VERSION
OUT=Path('results_v2/simulation/2026-11-17_end_to_end_acceptance')
BASE=Path('data/processed/spatial_3km_jan_mar_2026')
POLICY={'version':VERSION,'factor':1.0}
ROUTING='models/routing_policy/mar01_mar12_2026_temporal_fedavg_169x64x32x9_seed42/global_after_slot_528.keras'
CAL='results_v2/passenger_sensitivity/2026-11-17_request_weighted_calibration/sampling_contract.json'
SUPPORT='results_v2/pricing_dqn/2026-11-17_feasible_od_validation/od_feasibility.json'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def make_inputs():
 d=pd.read_parquet(BASE/'demand_master_jan_mar_2026.parquet',columns=['TimeSlot','GridID','Demand'],filters=[('TimeSlot','>=',pd.Timestamp('2026-01-01')),('TimeSlot','<',pd.Timestamp('2026-02-01'))])
 assert len(d)==31*48*142 and not d[['TimeSlot','GridID']].duplicated().any()
 d['period']=d.TimeSlot.dt.hour*2+d.TimeSlot.dt.minute//30
 means=d.groupby(['period','GridID']).Demand.mean().rename('predicted_demand').reset_index().rename(columns={'GridID':'Grid_ID'})
 artifact=OUT/'january_historical_average.csv';means.to_csv(artifact,index=False)
 targets=pd.date_range(utc('2026-03-12'),periods=5,freq='30min')
 w=pd.read_parquet(BASE/'weather_jan_mar_2026.parquet',filters=[('Datetime','>=',pd.Timestamp('2026-03-11')),('Datetime','<',pd.Timestamp('2026-03-12 07:00'))])
 m=contract(120);selected=select_weather(w,targets,m)
 frames={};realized={}
 for t,row in zip(targets,selected.to_dict('records')):
  local=t.tz_convert('America/New_York');f=means[means.period==local.hour*2+local.minute//30][['Grid_ID','predicted_demand']].copy()
  for key in list(timing(t))+['observation_time','assumed_available_at']:f[key]=row[key]
  frames[str(t)]=f
  # Retain the existing retrospective weather conditioning; no decision-time claim.
  old=pd.read_parquet(BASE/'demand_master_jan_mar_2026.parquet',columns=['WeatherCode'],filters=[('TimeSlot','==',local.tz_localize(None))])
  assert len(old)==142 and old.WeatherCode.nunique()==1
  realized[str(t)]=int(old.WeatherCode.iloc[0])
 totals=d.groupby('GridID').Demand.sum();pop=(pd.qcut(totals.rank(method='first'),5,labels=False)/4).to_dict()
 provenance=dict(method='January grid/local-half-hour arithmetic mean',training_start='2026-01-01',training_end_exclusive='2026-02-01',available_at=str(utc('2026-02-01')),artifact_path=str(artifact.resolve()),artifact_sha256=sha(artifact),source=str(BASE/'demand_master_jan_mar_2026.parquet'),selected_source_sha256=hashlib.sha256(d.to_csv(index=False).encode()).hexdigest())
 bundle=dict(forecast_protocol=BASELINE,baseline_provenance=provenance,weather_contract=m,checkpoint_metadata=dict(version=BASELINE,weather_contract_sha256=fingerprint(m)),channels=list(CHANNELS),grid_ids=list(range(142)),forecasts=frames,realized_weather=realized,popularity=pop,popularity_available_at=utc('2026-02-01'))
 (OUT/'fallback_run_config.json').write_text(json.dumps(dict(fallback=POLICY,forecast=provenance,routing_checkpoint=ROUTING,routing_sha256=sha(ROUTING),routing_available_local='2026-03-12 00:00',routing_source_end_local='2026-03-11 23:30',sensitivity=CAL,sensitivity_sha256=sha(CAL),support_sha256=sha(SUPPORT),seed=42,fleet_size=5000,interval=['2026-03-12 00:00','2026-03-12 02:00'],research_limitations=['Frozen sensitivity calibrated through March15; not a prospectively fitted March12 model.','Retrospective passenger weather preserves current calibration semantics.','Weather availability remains a 120-minute assumption.','Historical average is not a trained CNN.','Routing fixed throughout; no online federated updates.']),indent=2)+'\n')
 return bundle

def digest_state(r):
 e=r.engine
 data=dict(audit=r.audit,slots=r.slot_audit,fallback=r.fallback_audit,fleet=e.fleet,passengers=e.passengers,missions=e.missions,operational=e.operational.state_for(e.timestamp),provider_rng=r.provider.rng.bit_generator.state,learner_rng=r.learner.rng.bit_generator.state,replay=list(r.learner.replay),states=r.states)
 return hashlib.sha256(json.dumps(encode(data),sort_keys=True).encode()).hexdigest()

def run():
 inputs=make_inputs();support=json.loads(Path(SUPPORT).read_text());checks=[];metrics=[]
 def new():return ODPricingRuntime(start='2026-03-12',routing_checkpoint=ROUTING,seed=42,utc_inputs=inputs,od_support=support,sensitivity_contract=CAL,fallback_contract=POLICY)
 r=new()
 for i in range(4):
  start=time.perf_counter();rows=r.run_slot();elapsed=time.perf_counter()-start
  assert all(x['accepted']==(x['P_offer']<=x['P_max']) for x in rows)
  assert np.isclose(sum(x['P_offer'] for x in rows if x['dispatch_outcome']=='ACCEPTED_AND_ASSIGNED'),r.system_revenue)
  assert len(r.engine.fleet.vehicles)==5000
  assert all(np.isfinite(v.energy_level) and v.energy_level>=0 for v in r.engine.fleet.vehicles)
  assert all(np.isfinite(s).all() for s in r.states.values())
  checks.append(digest_state(r));metrics.append(dict(r.fallback_audit[-1],slot_number=i+1,total_requests=len(rows),total_accepted=sum(x['accepted'] for x in rows),total_assigned=sum(x['dispatch_outcome']=='ACCEPTED_AND_ASSIGNED' for x in rows),seconds=elapsed))
  pd.DataFrame(metrics).to_csv(OUT/'fallback_slot_metrics.csv',index=False)
  pd.DataFrame([x for x in r.audit if x['is_fallback']]).to_csv(OUT/'fallback_request_outcomes.csv',index=False)
  print('completed',i+1,'requests',len(rows),flush=True)
 pd.DataFrame(metrics).to_csv(OUT/'fallback_slot_metrics.csv',index=False)
 pd.DataFrame([x for x in r.audit if x['is_fallback']]).to_csv(OUT/'fallback_request_outcomes.csv',index=False)
 assert len(r.audit)==4137 and sum(x['is_fallback'] for x in r.audit)==2
 # Full repeat plus branch from slot-two checkpoint. Checkpoint is temporary.
 repeat=new();repeat_checks=[]
 with tempfile.TemporaryDirectory(prefix='od_acceptance_') as tmp:
  resumed=None
  for i in range(4):
   repeat.run_slot();repeat_checks.append(digest_state(repeat))
   assert checks[i]==repeat_checks[i]
   if i==1:
    path=Path(tmp)/'checkpoint';save_od_checkpoint(repeat,path)
    resumed=load_od_checkpoint(path,master_math=True,utc_mode=True,fallback_contract=POLICY)
  for i in range(2,4):
   resumed.run_slot();assert checks[i]==digest_state(resumed)
 result=dict(status='BOUNDED_RESEARCH_ACCEPTANCE_PASSED',slots=4,requests=len(r.audit),supported_requests=4135,fallback_requests=2,deterministic_repeat=True,checkpoint_resume=True,checks=checks,metrics=metrics,scope='Frozen retrospective research components; not a prospective full-system no-lookahead claim',training=False)
 (OUT/'fallback_validation.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':
 try:run()
 except Exception as e:
  import traceback
  (OUT/'fallback_run_blocker.json').write_text(json.dumps(dict(status='BLOCKED',exception=type(e).__name__,message=str(e)),indent=2)+'\n')
  traceback.print_exc();raise
