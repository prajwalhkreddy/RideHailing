"""Bounded analysis only. Date-filtered historical input; no runtime or model imports."""
from pathlib import Path
import json,hashlib
import numpy as np,pandas as pd
from scipy.stats import skew,kurtosis
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).parent;V=R.parent/'2026-11-07_passenger_sensitive_pricing_v1';D=Path('data/processed/price_distance_sensitivity_record029')
for n in ['fare_distance','sensitivity_distribution','acceptable_price','counterfactual_acceptance','action_space_validation','reference_value_review','academic_review_summary']: (R/n).mkdir(exist_ok=True)
P=21.34586956773507;L=4.856998243316242;LO=.017809913104763053;HI=27.324599740032788;A=np.array([.85,.9,.95,1,1.05,1.1,1.15]);master=[];charts=[]
def save(df,path):df.to_csv(R/path,index=False)
def dump(n,x):(R/n).write_text(json.dumps(x,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+'\n')
def metric(section,key,val,unit,pop,source,status='DESCRIPTIVE'):
 master.append(dict(analysis_section=section,metric=key,value=val,unit=unit,population=pop,source_file=source,interpretation_status=status))
def chart(path,question,pop,takeaway,lim='Descriptive, not causal; no values discarded from calculations.'):
 plt.tight_layout();plt.savefig(R/path,dpi=150);plt.close();charts.append(dict(file=path,question=question,population=pop,main_takeaway=takeaway,limitations=lim))
def stats(a):
 a=np.asarray(a);q=np.quantile(a,[0,.01,.05,.1,.25,.5,.75,.9,.95,.99,1]);return dict(N=len(a),mean=float(a.mean()),population_SD=float(a.std()),sample_SD=float(a.std(ddof=1)),**dict(zip(['min','P1','P5','P10','P25','median','P75','P90','P95','P99','max'],q)))
def checkpoint(name):dump('progress.json',dict(completed=name,no_training=True,no_methodology_change=True,protected_rows_in_analysis=0))
# Predicate applied at Parquet read, not post-hoc full-period loading. No protected-date rows returned/accessed by analysis.
filters=[('pickup_timestamp','>=',pd.Timestamp('2026-01-01')),('pickup_timestamp','<',pd.Timestamp('2026-03-16'))]
cache=R/'jan01_mar15_analysis_cache.parquet'
if cache.exists():f=pd.read_parquet(cache)
else:
 f=pd.read_parquet(D/'authoritative_epsilon_jan_mar_2026.parquet',columns=['source_row_index','pickup_timestamp','fare','trip_distance','epsilon','epsilon_status','relative_price_deviation','relative_distance_deviation'],filters=filters)
 assert f.pickup_timestamp.ge('2026-01-01').all() and f.pickup_timestamp.lt('2026-03-16').all();f.to_parquet(cache,index=False)
assert len(f)==8692819 and f.trip_distance.gt(0).all() and f.trip_distance.le(100).all()
dist=f.trip_distance.to_numpy()*1.609344;fare=f.fare.to_numpy();factor=fare/P
coverage=(factor>=.85)&(factor<=1.15)
prior=pd.read_csv(V/'review_feedback_reconciliation/pricing_factor_dataset_justification.csv');pr=prior[prior.metric=='within_0.85_1.15'].iloc[0]
assert int(coverage.sum())==int(pr.N) and np.isclose(100*coverage.mean(),pr.value,rtol=0,atol=1e-12),'STOP: coverage discrepancy'
fs,ds=stats(fare),stats(dist);save(pd.DataFrame([dict(variable='fare_amount',units='USD',**fs),dict(variable='trip_distance',units='km',**ds)]),'fare_distance/population_statistics.csv')
for key in ['N','min','max','mean','median','population_SD']:
 metric('fare_distance','fare_'+key,fs[key],'USD' if key!='N' else 'trips','cleaned Jan1–Mar15','fare_distance/population_statistics.csv')
 metric('fare_distance','distance_'+key,ds[key],'km' if key!='N' else 'trips','cleaned Jan1–Mar15','fare_distance/population_statistics.csv')
def binfare(width):
 out=[];ids=np.floor(dist/width).astype(int)
 for k in np.unique(ids):
  a=fare[ids==k];q=np.quantile(a,[0,.05,.25,.5,.75,.95,1]);out.append(dict(lower_distance_km=k*width,upper_distance_km=(k+1)*width,N=len(a),mean_fare=a.mean(),**dict(zip(['min_fare','P5_fare','P25_fare','median_fare','P75_fare','P95_fare','max_fare'],q))))
 return pd.DataFrame(out)
bins={}
for w,label in [(.5,'0p5'),(1,'1')]:bins[w]=binfare(w);save(bins[w],f'fare_distance/fare_by_distance_{label}km.csv');assert bins[w].N.sum()==len(f)
band_edges=[0,5,10,15,20,30,40,np.inf];br=[]
for lo,hi in zip(band_edges[:-1],band_edges[1:]):
 m=(dist>=lo)&(dist<hi);a=fare[m];q=np.quantile(a,[.05,.25,.5,.75,.95]);br.append(dict(lower_km=lo,upper_km=hi,N=m.sum(),percentage=100*m.mean(),mean_fare=a.mean(),**dict(zip(['P5_fare','P25_fare','median_fare','P75_fare','P95_fare'],q)),mean_fare_per_km=np.mean(a/dist[m]),median_fare_per_km=np.median(a/dist[m])))
save(pd.DataFrame(br),'fare_distance/distance_band_summary.csv')
plt.figure(figsize=(9,5));plt.hexbin(dist,fare,gridsize=80,bins='log',mincnt=1);plt.colorbar(label='log10 trip count');plt.xlabel('Trip distance (km)');plt.ylabel('TLC fare_amount (USD)');chart('fare_distance/fare_vs_distance_hexbin.png','How do recorded fares vary with distance?','All cleaned Jan1–Mar15','Full-range density; extremes retained.')
b=bins[.5];x=(b.lower_distance_km+b.upper_distance_km)/2
for name,band in [('median_fare_by_distance',False),('fare_quantile_band_by_distance',True)]:
 plt.figure(figsize=(9,5));plt.plot(x,b.median_fare,label='Median');
 if band:plt.fill_between(x,b.P5_fare,b.P95_fare,alpha=.2,label='P5–P95');plt.fill_between(x,b.P25_fare,b.P75_fare,alpha=.3,label='P25–P75')
 plt.xlabel('Distance bin centre (km)');plt.ylabel('Fare (USD)');plt.legend();chart('fare_distance/'+name+'.png','Fare level/spread across distance?','All cleaned Jan1–Mar15','Quantiles computed in 0.5-km bins; sparse tail bins can be unstable.')
plt.figure(figsize=(9,4));plt.hist(dist,bins=120);plt.yscale('log');plt.xlabel('Distance (km)');plt.ylabel('Trip count (log scale)');chart('fare_distance/trip_distance_distribution.png','Distance population shape?','All cleaned Jan1–Mar15','Full distance support retained.')
mins=[]
for label,upper in [('exact_minimum',fs['min']),('minimum_plus_0p50',fs['min']+.5),('minimum_plus_1p00',fs['min']+1),('fare_P1',fs['P1']),('fare_P5',fs['P5'])]:
 a=dist[fare<=upper];q=np.quantile(a,[0,.5,.75,.9,.95,.99,1]);mins.append(dict(candidate=label,fare_lower=fs['min'],fare_upper=upper,N=len(a),population_pct=100*len(a)/len(f),**dict(zip(['distance_min','distance_median','distance_P75','L_flat_P90','L_flat_P95','L_flat_P99','distance_max'],q))))
minimum=pd.DataFrame(mins);save(minimum,'fare_distance/minimum_fare_distance_analysis.csv');checkpoint('A fare-distance complete')
valid=f.epsilon_status.eq('VALID')&np.isfinite(f.epsilon)&f.epsilon.ne(0);signed=f.loc[valid,'epsilon'].to_numpy();absolute=np.abs(signed);supported=(absolute>=LO)&(absolute<=HI);positive=absolute[supported]
assert len(signed)==8685488 and len(positive)==8598805
assert np.allclose(np.quantile(absolute,[.005,.995]),[LO,HI],rtol=0,atol=1e-14)
summ=[];interval=[];shapes=[]
for name,a in [('signed',signed),('absolute_pre_support',absolute),('positive_supported_T0',positive)]:
 ss=stats(a);ss.update(distribution=name,positive_N=int((a>0).sum()),positive_pct=100*np.mean(a>0),negative_N=int((a<0).sum()),negative_pct=100*np.mean(a<0),zero_N=int((a==0).sum()))
 for cut in [.001,.005,.01]:ss['abs_lt_'+str(cut)+'_N']=int((np.abs(a)<cut).sum())
 summ.append(ss);shapes.append(dict(distribution=name,skewness=skew(a,bias=True),excess_kurtosis=kurtosis(a,fisher=True,bias=True),P95_minus_median_over_median_minus_P5=(ss['P95']-ss['median'])/(ss['median']-ss['P5']),P99_over_P50=ss['P99']/ss['median']))
 if name!='absolute_pre_support':
  for label,lo,hi in [('mean_plusminus_1SD',ss['mean']-ss['population_SD'],ss['mean']+ss['population_SD']),('mean_plusminus_2SD',ss['mean']-2*ss['population_SD'],ss['mean']+2*ss['population_SD']),('P5_P95',ss['P5'],ss['P95']),('P10_P90',ss['P10'],ss['P90']),('P25_P75',ss['P25'],ss['P75']),('current_T0_positive_bounds',LO,HI)]:
   within=(a>=lo)&(a<=hi);interval.append(dict(distribution=name,interval=label,lower=lo,upper=hi,N=int(within.sum()),percentage=100*within.mean(),interpretation='Literal positive bounds applied to signed epsilon; not signed 99% interval' if name=='signed' and label.startswith('current') else 'Inclusive endpoints'))
  if name=='signed':interval.append(dict(distribution=name,interval='current_T0_magnitude_membership',lower=LO,upper=HI,N=int(supported.sum()),percentage=100*supported.mean(),interpretation='LO <= abs(signed epsilon) <= HI; distinct from literal positive interval'))
save(pd.DataFrame(summ),'sensitivity_distribution/epsilon_distribution_statistics.csv');save(pd.DataFrame(shapes),'sensitivity_distribution/epsilon_shape_statistics.csv');save(pd.DataFrame(interval),'sensitivity_distribution/central_interval_analysis.csv')
for name,a in [('signed',signed),('absolute',absolute)]:
 for width,lbl in [(.05,'0p05'),(.1,'0p10')]:
  edges=np.arange(np.floor(a.min()/width)*width,np.ceil(a.max()/width)*width+width*1.01,width);counts,edges=np.histogram(a,bins=edges)
  plt.figure(figsize=(10,4));plt.stairs(counts,edges);plt.yscale('symlog',linthresh=1);plt.xlabel(name+' epsilon');plt.ylabel('Count (symlog)');chart(f'sensitivity_distribution/{name}_epsilon_hist_bin_{lbl}.png','Full support histogram at requested resolution?',name+' Jan1–Mar15','Full tails retained; symlog count axis improves visibility.')
lo,hi=np.quantile(signed,[.01,.99]);plt.figure(figsize=(9,4));plt.hist(signed[(signed>=lo)&(signed<=hi)],bins=np.arange(lo,hi+.05,.05));plt.xlabel('Signed epsilon');plt.ylabel('Count');plt.title('Central P1–P99 view; full tails retained in other figures');chart('sensitivity_distribution/signed_epsilon_hist_central.png','Central signed distribution?','Signed Jan1–Mar15 P1–P99 display only',f'Window [{lo}, {hi}]','Display-only percentile restriction; no methodology exclusion.')
plt.figure(figsize=(9,4));plt.hist(absolute,bins=np.geomspace(absolute.min(),absolute.max()*1.000001,150));plt.xscale('log');plt.yscale('log');plt.xlabel('Absolute epsilon (log)');plt.ylabel('Count (log)');chart('sensitivity_distribution/absolute_epsilon_log_tail.png','Positive magnitude tail extent?','All pre-support magnitudes','Log axes expose small and extreme values.')
plt.figure(figsize=(9,4))
for name,a in [('signed',signed),('absolute',absolute),('T0',positive)]:
 probs=np.linspace(0,1,2001);plt.plot(np.quantile(a,probs),probs,label=name)
plt.xscale('symlog',linthresh=1);plt.xlabel('Epsilon (symlog)');plt.ylabel('Empirical cumulative probability');plt.legend();chart('sensitivity_distribution/epsilon_ecdf.png','How does truncation change distribution shape?','Jan1–Mar15','ECDF plotted at 2001 quantiles; not a fitted distribution.')
ranges=[];edges=[0,.25,.5,1,2,3,5,10,20,np.inf]
for name,a in [('absolute_pre_support',absolute),('positive_supported_T0',positive)]:
 for l,h in zip(edges[:-1],edges[1:]):ranges.append(dict(distribution=name,lower=l,upper=h,N=int(((a>=l)&(a<h)).sum()),percentage=100*np.mean((a>=l)&(a<h))))
save(pd.DataFrame(ranges),'sensitivity_distribution/epsilon_range_counts.csv')
# Bounded actual examples, no invented observations.
idx=np.flatnonzero(valid);examples=[]
for label,values in [('largest_positive',-signed),('most_negative',signed),('smallest_absolute_nonzero',absolute)]:
 chosen=np.argsort(values,kind='stable')[:20];g=f.iloc[idx[chosen]].copy();g['selection']=label;g['distance_km']=g.trip_distance*1.609344;examples.append(g)
save(pd.concat(examples,ignore_index=True),'sensitivity_distribution/epsilon_extreme_examples.csv');checkpoint('B distributions complete')
# Illustrative grid, explicitly not actual same-distance passenger observations.
eq={str(int(q*100)):float(np.quantile(positive,q)) for q in [.01,.05,.1,.25,.5,.75,.9,.95,.99]};dd=[('distance_P'+str(int(q*100)),float(np.quantile(dist,q))) for q in [.1,.25,.5,.75,.9]]+[(f'illustrative_{k}km',k) for k in [2,5,10,20] if ds['min']<=k<=ds['max']]
rows=[]
for dn,di in dd:
 for en,e in eq.items():
  raw=P+(P/e)*((di-L)/L);acc=max(.85*P,raw);mask=A*P<=acc;rows.append(dict(distance_source=dn,distance_km=di,epsilon_quantile='P'+en,epsilon=e,P_raw_c=raw,P_accept_c=acc,feasible_action_count=int(mask.sum()),highest_feasible_action=A[mask].max(),lowest_feasible_action=A[mask].min(),record_type='FORMULA_ILLUSTRATION_NOT_OBSERVED_PASSENGER'))
save(pd.DataFrame(rows),'acceptable_price/acceptable_price_by_distance_and_epsilon.csv');save(pd.DataFrame(rows)[pd.DataFrame(rows).distance_source.str.startswith('illustrative')],'acceptable_price/same_distance_passenger_examples.csv')
fig,axs=plt.subplots(1,2,figsize=(12,4));xx=np.linspace(ds['P10'],ds['P90'],250)
for en,e in eq.items():
 raw=P+(P/e)*((xx-L)/L);axs[0].plot(xx,raw,label='P'+en);axs[1].plot(xx,np.maximum(.85*P,raw),label='P'+en)
for ax,title in zip(axs,['Raw preference','Effective threshold']):ax.set(xlabel='Distance (km)',ylabel='USD',title=title);ax.set_yscale('symlog',linthresh=P)
axs[1].legend(ncol=3,fontsize=7);chart('acceptable_price/acceptable_price_curves.png','Same distance, different empirical epsilon quantiles?','Formula illustrations using T0 quantiles','Below L_base the adjustment is negative; above it positive.','Not observed passengers; symlog price axis; shown distance P10–P90 only.')
sd=dist[valid.to_numpy()][supported];raw=P+(P/positive)*((sd-L)/L);cats=np.select([raw<=0,raw<.85*P,raw<=1.15*P],['RAW_NONPOSITIVE','RAW_POSITIVE_BELOW_PLATFORM_MIN','RAW_WITHIN_PLATFORM_RANGE'],default='RAW_ABOVE_PLATFORM_MAX');rr=[]
for cat in ['RAW_NONPOSITIVE','RAW_POSITIVE_BELOW_PLATFORM_MIN','RAW_WITHIN_PLATFORM_RANGE','RAW_ABOVE_PLATFORM_MAX']:rr.append(dict(category=cat,N=int((cats==cat).sum()),percentage=100*np.mean(cats==cat)))
rr.append(dict(category='EFFECTIVE_MIN_PROTECTION_APPLIED',N=int((raw<.85*P).sum()),percentage=100*np.mean(raw<.85*P)))
save(pd.DataFrame(rr),'acceptable_price/raw_preference_categories.csv');checkpoint('C acceptable-price complete')
# Saved development rows, not simulator execution.
devpath=V/'staged_training_002/professor_review/episode25_march16_request_level_acceptance.csv';dev=pd.read_csv(devpath,float_precision='round_trip');assert len(dev)==2838 and dev.forced_request.sum()==1559 and dev.choice_request.sum()==1279
assert pd.to_datetime(dev.request_timestamp).ge('2026-03-16').all() and pd.to_datetime(dev.request_timestamp).lt('2026-03-16 02:00').all()
long=pd.DataFrame({'request_sequence':np.repeat(dev.request_sequence.to_numpy(),7),'request_id':np.repeat(dev.request_id.to_numpy(),7),'factor':np.tile(A,len(dev)),'P_base':np.repeat(dev.P_base.to_numpy(),7),'P_accept_c':np.repeat(dev.P_accept_c.to_numpy(),7),'distance_km':np.repeat(dev.L_gg_prime_km.to_numpy(),7),'epsilon_c':np.repeat(dev.epsilon_c.to_numpy(),7),'raw_preference_category':np.repeat(dev.raw_preference_category.to_numpy(),7)})
long['P_offer']=long.factor*long.P_base;long['counterfactual_accept']=long.P_offer<=long.P_accept_c;assert len(long)==19866
save(long,'counterfactual_acceptance/march16_counterfactual_acceptance_request_action.csv')
def acceptance_table(df,group):
 rows=[]
 for keys,g in df.groupby(group,observed=True,sort=True):
  keys=(keys,) if not isinstance(keys,tuple) else keys;rows.append(dict(zip(group,keys))|dict(N=len(g),offer_price=float(g.P_offer.iloc[0]),accepted_N=int(g.counterfactual_accept.sum()),rejected_N=int((~g.counterfactual_accept).sum()),acceptance_pct=100*g.counterfactual_accept.mean(),rejection_pct=100*(~g.counterfactual_accept).mean()))
 return pd.DataFrame(rows)
curve=acceptance_table(long,['factor']);save(curve,'counterfactual_acceptance/march16_acceptance_curve.csv')
long['distance_band']=pd.cut(long.distance_km,[0,5,10,15,20,np.inf],right=False);long['epsilon_band']=pd.cut(long.epsilon_c,[0,.5,1,2,3,5,np.inf],right=False)
for col,file in [('distance_band','distance'),('epsilon_band','epsilon'),('raw_preference_category','raw_preference')]:save(acceptance_table(long,[col,'factor']),f'counterfactual_acceptance/march16_acceptance_by_{file}.csv')
plt.figure(figsize=(8,4));plt.plot(curve.factor,curve.acceptance_pct,'o-');plt.ylim(0,105);plt.xticks(A);plt.xlabel('Offered factor before masking');plt.ylabel('Counterfactual acceptance (%)');chart('counterfactual_acceptance/march16_acceptance_curve.png','Would offers be rejected before masking?','2838 saved March16 requests','Deterministic model acceptance falls as offered price rises.','Offline acceptance only; no driver dispatch or fleet-response simulation.')
checkpoint('D counterfactual complete')
facstats=stats(factor);save(pd.DataFrame([facstats]),'action_space_validation/historical_factor_statistics.csv');cov=[]
for label,m in [('below_0p85',factor<.85),('inside_0p85_1p15',coverage),('above_1p15',factor>1.15)]:cov.append(dict(category=label,N=int(m.sum()),percentage=100*m.mean()))
save(pd.DataFrame(cov),'action_space_validation/action_range_coverage.csv');cr=[]
for lo,hi in zip([0,5,10,15,20,30],[5,10,15,20,30,np.inf]):
 m=(dist>=lo)&(dist<hi);a=fare[m];ff=factor[m];cr.append(dict(lower_km=lo,upper_km=hi,N=int(m.sum()),median_fare=np.median(a),P5_fare=np.quantile(a,.05),P95_fare=np.quantile(a,.95),median_historical_factor=np.median(ff),below_pct=100*np.mean(ff<.85),inside_pct=100*np.mean((ff>=.85)&(ff<=1.15)),above_pct=100*np.mean(ff>1.15)))
covdist=pd.DataFrame(cr);save(covdist,'action_space_validation/action_range_coverage_by_distance.csv')
plt.figure(figsize=(10,5));plt.plot(x,b.median_fare,label='Median fare');plt.fill_between(x,b.P5_fare,b.P95_fare,alpha=.2,label='P5–P95')
for a in A:plt.axhline(a*P,linewidth=.8,label=f'{a:.2f} × P_base')
plt.legend(ncol=3,fontsize=7);plt.xlabel('Distance bin centre (km)');plt.ylabel('Fare (USD)');chart('action_space_validation/current_action_prices_vs_fare_distance.png','How does global action pricing compare with fares?','Cleaned Jan1–Mar15','Fixed horizontal action prices span only a narrow slice of fare levels.')
plt.figure(figsize=(9,4));plt.hist(factor,bins=150);plt.yscale('log');plt.axvspan(.85,1.15,color='red',alpha=.3,label='Current range');plt.legend();plt.xlabel('Observed fare / P_base');plt.ylabel('Count (log)');chart('action_space_validation/historical_factor_distribution.png','Observed factor support and current range?','Cleaned Jan1–Mar15','Full observed support shown; current range is narrow.')
plt.figure(figsize=(9,4));plt.bar(np.arange(len(cr)),covdist.inside_pct);plt.xticks(np.arange(len(cr)),['0–5','5–10','10–15','15–20','20–30','30+']);plt.ylabel('Inside current range (%)');plt.xlabel('Distance band (km)');chart('action_space_validation/action_range_coverage_by_distance.png','Does coverage depend on distance?','Cleaned Jan1–Mar15','Coverage varies substantially across distance bands.')
near=[]
for width in [.25,.5,1.]:
 m=np.abs(dist-L)<=width;a=fare[m];near.append(dict(window_halfwidth_km=width,N=int(m.sum()),mean_fare=a.mean(),median_fare=np.median(a),P25_fare=np.quantile(a,.25),P75_fare=np.quantile(a,.75),status='DIAGNOSTIC_WINDOW_NOT_NEW_REFERENCE'))
save(pd.DataFrame(near),'reference_value_review/fare_near_Lbase.csv')
refs=pd.DataFrame([dict(reference='P_base',frozen_value=P,unit='USD',restricted_mean=fs['mean'],restricted_median=fs['median'],restricted_P25=fs['P25'],restricted_P75=fs['P75'],provenance='Full cleaned Jan–Mar global mean fare; fixed reference exception preserved'),dict(reference='L_base',frozen_value=L,unit='km',restricted_mean=ds['mean'],restricted_median=ds['median'],restricted_P25=ds['P25'],restricted_P75=ds['P75'],provenance='Full cleaned Jan–Mar mean distance conditioned on fare within ±1 USD of P_base; converted miles to km')]);save(refs,'reference_value_review/reference_value_comparison.csv')
for name,a in [('signed',summ[0]),('absolute',summ[1]),('T0',summ[2])]:
 for key in ['N','mean','population_SD','median','negative_pct']:metric('sensitivity',name+'_'+key,a[key],'count' if key=='N' else 'dimensionless','Jan1–Mar15','sensitivity_distribution/epsilon_distribution_statistics.csv')
for row in curve.to_dict('records'):metric('counterfactual','acceptance_factor_'+str(row['factor']),row['acceptance_pct'],'percent','March16 saved development','counterfactual_acceptance/march16_acceptance_curve.csv')
metric('action_space','current_range_coverage',100*coverage.mean(),'percent','Jan1–Mar15','action_space_validation/action_range_coverage.csv')
save(pd.DataFrame(master),'academic_review_summary/master_results.csv');save(pd.DataFrame(charts),'academic_review_summary/chart_index.csv')
dump('analysis_results.json',dict(fare=fs,distance=ds,minimum_fare=mins,sensitivity=summ,shapes=shapes,raw_categories=rr,coverage=cov,coverage_by_distance=cr,reference_near=near,counterfactual=curve.to_dict('records'),charts=charts,source=str(D/'authoritative_epsilon_jan_mar_2026.parquet'),filter='2026-01-01 <= pickup_timestamp < 2026-03-16',fare_source='TLC fare_amount',coverage_reconciled=True,support_reconciled=True,development_reconciled=True,protected_final_hierarchical_evaluation_untouched=True,methodology_changed=False,training_performed=False))
checkpoint('ALL_NUMERICAL_ANALYSES_COMPLETE');print(json.dumps({'N':len(f),'fare':fs,'distance':ds,'minimum':mins,'coverage':cov,'counterfactual':curve.to_dict('records')}))
