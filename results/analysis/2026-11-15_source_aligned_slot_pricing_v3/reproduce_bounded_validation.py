from pathlib import Path
import json,sys,hashlib
import numpy as np,pandas as pd
from scipy import stats
from src.simulation.slot_pricing_v3 import SlotPricingV3
from src.pricing.slot_v3 import FittedSensitivity
from src.dispatch.request import RequestState
from src.fleet.fleet import Fleet
from src.fleet.state import VehicleState,VehicleStatus
O=Path('results/analysis/2026-11-15_source_aligned_slot_pricing_v3');route='models/routing_policy/mar01_mar12_2026_temporal_fedavg_169x64x32x9_seed42/final_march12.keras'
def engine(start):
 fleet=Fleet([VehicleState(i,i,VehicleStatus.IDLE,None,0,'idle',60.) for i in range(3)],frozenset(range(142)),2)
 profiles=pd.DataFrame(dict(vehicle_id=range(3),price_preference=[0.]*3,wait_preference=[10.]*3,charging_wait_preference_minutes=[10.]*3))
 return SlotPricingV3(start=start,routing_checkpoint=route,fleet=fleet,driver_profiles=profiles)
x=engine('2026-03-12');aud=[];slots=[]
for j in range(16):
 t=x.engine.timestamp;rr=[]
 for i in range(14):
  distance=.1 if i%2==0 else 30.;rr.append(RequestState(j*100+i,0,i%3,i%7,base_fare=20.,source_trip_id=j*100+i,empirical_pickup_datetime=t.to_pydatetime(),empirical_dropoff_datetime=(t+pd.Timedelta(minutes=40)).to_pydatetime(),trip_duration_minutes=40.,trip_distance_miles=distance/1.609344,trip_distance_km=distance))
 x.run_slot(rr,policy=lambda d,s:d%7,weather_code=[1,13,15,17,21][j%5]);print('slot',j+1,flush=True)
aud+=x.audit;slots+=x.slot_audit
z=engine('2026-03-12 16:00');t=z.engine.timestamp;r=RequestState(9999,0,0,1,base_fare=20.,source_trip_id=9999,empirical_pickup_datetime=t.to_pydatetime(),empirical_dropoff_datetime=(t+pd.Timedelta(minutes=40)).to_pydatetime(),trip_duration_minutes=40.,trip_distance_miles=30/1.609344,trip_distance_km=30.);z.run_slot([r],policy=lambda d,s:d%7,weather_code=1);aud+=z.audit;slots+=z.slot_audit
f=pd.DataFrame(aud);s=pd.DataFrame(slots);assert (f.accepted==(f.P_offer<=f.P_max)).all();p=f.P_base+(f.P_base/f.epsilon)*((f.L-f.L_base)/f.L_base);assert np.allclose(p,f.P_max);assert (s.generated==s.accepted+s.rejected).all() and (s.accepted==s.assigned+s.accepted_unmatched).all();assert np.isclose(s.accepted_revenue.sum(),f.loc[f.accepted,'P_offer'].sum());assert s.groupby('slot').size().eq(142).all();assert sum(t[4] for t in x.learner.replay)==142;assert x.learner.training_steps==0
assert set(f.dispatch_outcome)=={'PASSENGER_REJECTED','ACCEPTED_AND_ASSIGNED','ACCEPTED_BUT_UNMATCHED'}
f.to_csv(O/'bounded_request_validation.csv',index=False);s.to_csv(O/'bounded_slot_validation.csv',index=False)
summary=dict(slots=17,requests=len(f),accepted=int(f.accepted.sum()),rejected=int((~f.accepted).sum()),assigned=int((f.dispatch_outcome=='ACCEPTED_AND_ASSIGNED').sum()),accepted_unmatched=int((f.dispatch_outcome=='ACCEPTED_BUT_UNMATCHED').sum()),accepted_revenue=f.reward_contribution.sum(),assignment_revenue=s.assignment_revenue.sum(),acceptance_rate=f.accepted.mean(),dispatch_success_rate=(f.dispatch_outcome=='ACCEPTED_AND_ASSIGNED').sum()/f.accepted.sum(),optimizer_updates=0,validation_type='controlled small-fleet frozen-simulator integration; not empirical demand performance')
pd.DataFrame([summary]).to_csv(O/'bounded_validation_summary.csv',index=False)
provider=FittedSensitivity(123);vr=[];q=np.array([.25,.5,.75,.95,.99]);N=200000
for sid,c in provider.contract['conditions'].items():
 d=provider.distribution(sid);a=d.rvs(size=N,random_state=np.random.default_rng(123));assert np.isfinite(a).all() and (a>0).all();theory=d.ppf(q);sample=np.quantile(a,q)
 # 99.9999% pointwise order-statistic interval, fixed before comparing.
 lo=stats.binom.ppf(.0000005,N,q).astype(int);hi=stats.binom.ppf(.9999995,N,q).astype(int);ordered=np.sort(a)
 passed=(ordered[np.maximum(lo-1,0)]<=theory)&(theory<=ordered[np.minimum(hi,N-1)])
 assert passed.all(),(sid,theory,sample)
 for quant,tv,sv,ok in zip(q,theory,sample,passed):vr.append(dict(condition=sid,family=c['family'],quantile=quant,theoretical=tv,generated=sv,passed=ok,N=N,finite_positive_rate=1.,empirical_relative_error_pct=c['empirical_fit_limitations'].get(('median' if quant==.5 else 'P'+str(int(quant*100)))+'_relative_error_pct')))
pd.DataFrame(vr).to_csv(O/'runtime_distribution_validation.csv',index=False)
print(summary)
