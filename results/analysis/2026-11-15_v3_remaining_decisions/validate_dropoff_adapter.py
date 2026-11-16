import sys,json,hashlib
from pathlib import Path
import numpy as np,pandas as pd
O=Path('results/analysis/2026-11-15_v3_remaining_decisions');sys.path.insert(0,str(O.resolve()));from technical_helpers import DropoffAdapter,FEATURES
source=Path('data/processed/spatial_3km_jan_mar_2026/destination_popularity.parquet')
f=pd.read_parquet(source,columns=['TimeSlot','GridID','dropoff_ma_3h','dropoff_count'],filters=[('TimeSlot','>=',pd.Timestamp('2026-01-01')),('TimeSlot','<',pd.Timestamp('2026-03-16'))])
pre=f[f.TimeSlot<pd.Timestamp('2026-03-01')];counts=pre.groupby('GridID').dropoff_count.sum().reindex(range(142));assert counts.notna().all() and counts.sum()>0
init=counts.to_numpy()/counts.sum();adapter=DropoffAdapter(init,'2026-02-28 23:59:59.999999999');rows=[]
for t,g in f[f.TimeSlot>=pd.Timestamp('2026-03-01')].groupby('TimeSlot',sort=True):
 assert len(g)==142 and g.GridID.nunique()==142
 g=g.set_index('GridID').reindex(range(142));v,level=adapter.build(g.dropoff_ma_3h.to_numpy(),t,t-pd.Timedelta(minutes=30))
 rows.append(dict(slot=t,grids=142,total_D=g.dropoff_ma_3h.sum(),probability_sum=v.sum(),minimum=v.min(),maximum=v.max(),finite=np.isfinite(v).all(),fallback=level,observed_through=t-pd.Timedelta(minutes=30)))
assert len(rows)==720
pd.DataFrame(rows).to_csv(O/'dropoff_probability_validation.csv',index=False)
c=dict(status='FROZEN',adapter='technical_helpers.py:DropoffAdapter offline only',source=str(source),measure='dropoff_ma_3h: shift1 trailing6 completed slots',normalization='D_lag / sum valid142 grids',zero_total='carry latest valid vector, else preMarch initialization, else fail closed',initialization_source='Jan1–Feb28 historical dropoff_count summed by destination; complete beforeMar1',initialization=init.tolist(),initialization_available_before='2026-03-01',validation_slots=720,validation_scope='March1–15; preMarch data used only for initialization',zero_total_count=sum(x['total_D']==0 for x in rows),carry_count=sum(x['fallback']=='CARRY_FORWARD' for x in rows),initialization_count=sum(x['fallback']=='HISTORICAL_INITIALIZATION' for x in rows),no_uniform_fallback=True,upstream_modified=False)
(O/'dropoff_probability_contract.json').write_text(json.dumps(c,indent=2,default=int)+'\n')
d=pd.read_csv(O/'destination_state_mapping.csv');d.loc[d.source_feature=='dropoff probabilities',['normalization','status','existing_signal']]=['lag / sum142; causal carry/init on zero','FROZEN','dropoff_ma_3h via offline DropoffAdapter'];d.to_csv(O/'final_destination_state.csv',index=False)
# exact ordered scalar contract alongside family mapping
with (O/'final_destination_state.csv').open('a'):pass
(O/'final_state_order.json').write_text(json.dumps({'features':FEATURES,'dimension':15,'timestamp':'before requests at slot boundary','destination':'all signals indexed at destination context grid d','weather_time_appended':False},indent=2)+'\n')
print(c['validation_slots'],c['zero_total_count'])
