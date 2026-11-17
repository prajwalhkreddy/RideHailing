"""Versioned causal demand history with explicitly non-operational oracle weather."""
import numpy as np
import pandas as pd

VERSION='CNN_CAUSAL_HISTORY_ORACLE_WEATHER_V1'
ZONE='America/New_York'
STEP=pd.Timedelta(minutes=30)
CHANNELS=('DayOfWeek','Hour','PeriodWithinHour','WeatherType','Temperature','WindSpeed','HistoricalAverageDemandDistribution')

def civil(value):
 t=pd.Timestamp(value)
 if pd.isna(t):raise ValueError('Missing timestamp')
 if t.tz is None:t=t.tz_localize(ZONE,ambiguous='raise',nonexistent='raise')
 else:t=t.tz_convert(ZONE)
 if t.minute not in (0,30) or t.second or t.microsecond or t.nanosecond:raise ValueError('Half-hour alignment required')
 return t

def timing(target):
 t=civil(target)
 return dict(issued_at=t-STEP,target_start=t,target_end=t+STEP,feature_cutoff=t-STEP)

def build_oracle(source,grid):
 """Demand intervals ending <= issue; only Jan-Feb targets update statistics.

 Zero-history samples are flagged ineligible, not fabricated warm-up training.
 Prior weather moments normalize oracle weather, never future training moments.
 """
 d=source.copy();naive=pd.DatetimeIndex(d.TimeSlot)
 if naive.tz is not None:raise ValueError('Expected documented naive source')
 localized=naive.tz_localize(ZONE,ambiguous='raise',nonexistent='NaT')
 invalid=d.loc[localized.isna()].copy();d=d.loc[~localized.isna()].copy();d['aware']=localized[~localized.isna()]
 g=grid.sort_values('GridID');ids=g.GridID.to_numpy();r=g.Row.to_numpy(int);c=g.Column.to_numpy(int)
 if len(g)!=142 or not np.array_equal(ids,np.arange(142)) or len(set(zip(r,c)))!=142 or min(r.min(),c.min())<0 or max(r.max(),c.max())>=16:raise ValueError('Invalid grid')
 if d[['aware','GridID']].duplicated().any() or not (d.groupby('aware').GridID.nunique()==142).all():raise ValueError('Incomplete demand slots')
 if not set(d.GridID)==set(ids):raise ValueError('Invalid grid IDs')
 for key,expected in [('Row',r),('Column',c)]:
  if not np.array_equal(d[key].to_numpy(),expected[d.GridID.to_numpy(int)]):raise ValueError('Grid geometry mapping mismatch')
 d=d.sort_values(['aware','GridID']);times=pd.DatetimeIndex(d.aware.unique())
 if any(civil(t)!=t for t in times):raise ValueError('Invalid slots')
 if not (times>=civil('2026-01-01')).all():raise ValueError('Unexpected source period')
 demands=d.Demand.to_numpy(float).reshape(-1,142)
 if not np.isfinite(demands).all() or (demands<0).any():raise ValueError('Invalid demand')
 cols=['WeatherCode','Temperature','WindSpeed']
 if not (d.groupby('aware')[cols].nunique(dropna=False)==1).all().all():raise ValueError('Weather inconsistent within slot')
 weather=d.groupby('aware')[cols].first().to_numpy(float)
 if not np.isfinite(weather).all():raise ValueError('Missing oracle weather')
 x=np.zeros((len(times),7,16,16),np.float32);y=np.zeros((len(times),1,16,16),np.float32)
 sums={};counts={};slot_sums={};slot_counts={};total=np.zeros(142);squares=0.;n=0;cursor=0;ws=np.zeros(2);wss=np.zeros(2);rows=[]
 train_end=civil('2026-03-01')
 for i,t in enumerate(times):
  info=timing(t);origin=info['issued_at'];last=None
  while cursor<len(times) and times[cursor]+STEP<=origin:
   past=times[cursor]
   if past<train_end:
    k=(past.dayofweek,past.hour*2+past.minute//30);s=k[1];v=demands[cursor]
    sums[k]=sums.get(k,np.zeros(142))+v;counts[k]=counts.get(k,0)+1
    slot_sums[s]=slot_sums.get(s,np.zeros(142))+v;slot_counts[s]=slot_counts.get(s,0)+1
    total+=v;squares+=float(v@v);ws+=weather[cursor,1:];wss+=weather[cursor,1:]**2;n+=1
   cursor+=1
  k=(t.dayofweek,t.hour*2+t.minute//30);s=k[1]
  if k in sums:h=sums[k]/counts[k];level='WEEKDAY_SLOT'
  elif s in slot_sums:h=slot_sums[s]/slot_counts[s];level='SLOT'
  elif n:h=total/n;level='GRID'
  else:h=np.zeros(142);level='NO_HISTORY'
  mean=ws/n if n else np.zeros(2);std=np.sqrt(np.maximum(wss/n-mean**2,0)) if n else np.ones(2);std=np.where(std>0,std,1)
  demand_scale=np.sqrt(max(squares/(n*142)-(total.sum()/(n*142))**2,0)) if n else 1.;demand_scale=demand_scale or 1.
  features=np.column_stack([np.full(142,t.dayofweek/6),np.full(142,t.hour/23),np.full(142,t.minute//30),np.full(142,weather[i,0]/27),np.full(142,(weather[i,1]-mean[0])/std[0]),np.full(142,(weather[i,2]-mean[1])/std[1]),h/demand_scale])
  x[i,:,r,c]=features;y[i,0,r,c]=demands[i]
  split='train' if t<train_end else 'validation' if t<civil('2026-03-16') else 'test'
  rows.append(dict(**info,split=split,history_training_slots=n,history_level=level,eligible=n>0,weather_mode='ORACLE_OBSERVED_TARGET_WEATHER',operational_available=False))
 if not np.isfinite(x).all():raise ValueError('Nonfinite tensor')
 return x,y,pd.DataFrame(rows),invalid

def validate_forecast(frame,metadata,decision_time,*,operational=True):
 """Explicit new export boundary; never relabel historical predictions."""
 if metadata.get('version')!=VERSION or metadata.get('timezone')!=ZONE:raise ValueError('Incompatible timing metadata')
 if operational:raise ValueError('Oracle weather and source timezone provenance not operationally verified')
 t=civil(decision_time);expected=timing(t)
 if len(frame)!=142 or set(frame.Grid_ID)!=set(range(142)):raise ValueError('Incomplete forecast grids')
 for field,value in expected.items():
  if not (pd.to_datetime(frame[field],utc=True)==value.tz_convert('UTC')).all():raise ValueError('Forecast timestamp mismatch: '+field)
 p=frame.predicted_demand.to_numpy(float)
 if not np.isfinite(p).all() or (p<0).any():raise ValueError('Invalid demand predictions')
 # Legacy OD clocks are naive: do not conceal DST-crossing interval arithmetic.
 if t.tz_localize(None)-expected['issued_at'].tz_localize(None)!=STEP:raise ValueError('Legacy OD clock cannot represent DST boundary')
 return dict(zip(frame.Grid_ID,p))
