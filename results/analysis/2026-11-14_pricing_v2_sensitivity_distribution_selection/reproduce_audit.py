"""Offline V2 population and held-out distribution audit; no runtime integration."""
from pathlib import Path
import json,hashlib,warnings
import numpy as np,pandas as pd
from scipy import stats,optimize,special
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[3];O=Path(__file__).resolve().parent
D=R/'data/interim/pricing_v2_sensitivity';D.mkdir(exist_ok=True,parents=True)
prior=R/'results/analysis/2026-11-14_pricing_v2_denominator_rule_selection'
ref=prior/'notation_contract.json';cfg=json.loads(ref.read_text());P=cfg['P_base'];L=cfg['L_base']
source=R/'results/analysis/2026-11-09_academic_review_followup_pricing/jan01_mar15_analysis_cache.parquet'
sources=[ref,source,prior/'candidate_population_comparison.csv',prior/'regression_sanity_validation.csv' if (prior/'regression_sanity_validation.csv').exists() else prior/'ratio_bias_validation.csv',R/'results/analysis/2026-11-13_pricing_v2_freeze_design/V2_NUMERICAL_FREEZE.md']
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as s:
  for chunk in iter(lambda:s.read(1048576),b''):h.update(chunk)
 return h.hexdigest()
hashes={str(p.relative_to(R)):sha(p) for p in sources}
f=pd.read_parquet(source,columns=['pickup_timestamp','fare','trip_distance']);cache_N=len(f)
f['source_observation_id']=np.arange(len(f),dtype=np.int64)
assert f.pickup_timestamp.ge('2026-01-01').all() and f.pickup_timestamp.lt('2026-03-16').all()
assert np.isfinite(f[['fare','trip_distance']].to_numpy()).all() and f.fare.gt(0).all() and f.trip_distance.gt(0).all() and f.trip_distance.le(100).all()
f['distance_km']=f.trip_distance*1.609344
f=f[(f.distance_km>=1.5)&(f.distance_km<75)].copy();N=len(f);assert N==6967155
weather=[]
for m in [1,2,3]:
 path=R/f'data/processed/weather/nyc_weather_processed_2026_{m:02}.parquet'
 # Read only permitted row ranges, not protected-period payloads.
 weather.append(pd.read_parquet(path,columns=['Datetime','WeatherCode'],filters=[('Datetime','>=',pd.Timestamp('2026-01-01')),('Datetime','<',pd.Timestamp('2026-03-16'))]))
f['Datetime']=f.pickup_timestamp.dt.floor('h');f=f.merge(pd.concat(weather),on='Datetime',validate='many_to_one',how='left',sort=False);assert len(f)==N and f.WeatherCode.notna().all() and f.source_observation_id.is_monotonic_increasing
f=f.rename(columns={'WeatherCode':'weather_code'}).drop(columns='Datetime');f['hour']=f.pickup_timestamp.dt.hour
f['P_deviation_abs']=abs(f.fare-P);f['r_P']=(f.fare-P)/P;f['r_L']=(f.distance_km-L)/L
ok=abs(f.r_P)>=.05;f['epsilon']=np.divide(f.r_L,f.r_P,out=np.full(N,np.nan),where=ok)
f['epsilon_status']=np.select([~ok,ok&(f.epsilon<0),ok&(f.epsilon==0)],['DENOMINATOR_UNRESOLVED','NEGATIVE_AUDITED_EXCLUDED','NONNEGATIVE_VALID'],default='POSITIVE_VALID')
f['source_valid']=True;f['denominator_resolved']=ok;f['is_runtime_candidate']=ok&(f.epsilon>=0)
valid=f.is_runtime_candidate.to_numpy();a=f.loc[valid,'epsilon'].to_numpy();rng=np.random.default_rng(42);isfit=rng.random(len(a))<.8
split=np.full(N,'NOT_CANDIDATE',dtype=object);split[np.flatnonzero(valid)]=np.where(isfit,'FIT','VALIDATION');f['distribution_split']=split
counts=dict(source_cache_N=cache_N,source_cache_outside_analysis_scope_N=cache_N-N,source_population_N=N,source_invalid_N=0,source_valid_N=N,denominator_unresolved_N=int((~ok).sum()),denominator_unresolved_pct=float(100*(~ok).mean()),denominator_resolved_N=int(ok.sum()),negative_epsilon_N=int((f.epsilon<0).sum()),negative_epsilon_pct_source=float(100*(f.epsilon<0).mean()),negative_epsilon_pct_resolved=float(100*(f.epsilon<0).sum()/ok.sum()),zero_epsilon_N=int((f.epsilon==0).sum()),positive_epsilon_N=int((f.epsilon>0).sum()),final_nonnegative_candidate_N=len(a),final_retained_pct=100*len(a)/N,fit_N=int(isfit.sum()),validation_N=int((~isfit).sum()))
old=pd.read_csv(prior/'candidate_population_comparison.csv').set_index('rule_id').loc['C']
assert counts['denominator_unresolved_N']==old.denominator_excluded_N and counts['negative_epsilon_N']==old.negative_excluded_N and len(a)==old.final_nonnegative_N
assert counts['denominator_unresolved_N']+counts['negative_epsilon_N']+len(a)==N
assert f.loc[~ok,'epsilon'].isna().all() and np.isfinite(a).all()
artifact=D/'pricing_v2_sensitivity_population_jan01_mar15_2026.parquet'
f.to_parquet(artifact,index=False,compression='zstd')
pd.DataFrame([counts]).to_csv(O/'population_reconciliation.csv',index=False)
levels=[.001,.01,.05,.10,.25,.5,.75,.90,.95,.99,.995,.999];labels=['P001','P01','P05','P10','P25','P50','P75','P90','P95','P99','P995','P999']
def describe(x):return dict(N=len(x),mean=float(x.mean()),SD=float(x.std()),median=float(np.median(x)),minimum=float(x.min()),maximum=float(x.max()),skewness=float(stats.skew(x)),excess_kurtosis=float(stats.kurtosis(x)),**dict(zip(labels,map(float,np.quantile(x,levels)))))
full=describe(a);pd.DataFrame([full]).to_csv(O/'global_sensitivity_statistics.csv',index=False)
assert np.isclose(full['mean'],old.mean_epsilon,rtol=1e-12) and np.isclose(full['SD'],old.SD_epsilon,rtol=1e-12)
weather_rows=[]
for (wc,h),g in f[valid].groupby(['weather_code','hour']):
 e=g.epsilon.to_numpy();weather_rows.append(dict(weather_code=int(wc),hour=int(h),N=len(e),mean=float(e.mean()),median=float(np.median(e)),SD=float(e.std()),P95=float(np.quantile(e,.95)),P99=float(np.quantile(e,.99)),N_ge50=len(e)>=50,N_ge100=len(e)>=100,SD_lt4=e.std()<4,diagnostic_role='INTERNAL_STABILITY_DIAGNOSTIC'))
pd.DataFrame(weather_rows).to_csv(O/'weather_hour_secondary_summary.csv',index=False)
rr=pd.read_csv(prior/'ratio_bias_validation.csv');rr=rr[rr.rule_id=='C'];rr.to_csv(O/'regression_sanity_validation.csv',index=False)
x=np.sort(a[isfit]);v=np.sort(a[~isfit]);del f,a,split
assert x.min()>0 # zero handling explicitly recorded; no arbitrary offset
print('Population persisted',counts,flush=True)
# Fixed loc=0 MLE. Weibull shape-score root avoids repeated generic optimization.
logx=np.log(x);mu=float(logx.mean());sigma=float(logx.std());shift=logx-logx.max()
def weibull_score(k):
 weights=np.exp(k*shift);return 1/k+mu-float(np.dot(weights,logx)/weights.sum())
shape=optimize.brentq(weibull_score,.01,100,xtol=1e-12);scale=float(np.exp(special.logsumexp(shape*logx)/shape-np.log(len(x))/shape))
ga=stats.gamma.fit(x,floc=0)
models={'Gamma':stats.gamma(*ga),'Weibull':stats.weibull_min(shape,loc=0,scale=scale),'Lognormal':stats.lognorm(sigma,loc=0,scale=np.exp(mu)),'Exponential':stats.expon(loc=0,scale=x.mean())}
params={'Gamma':dict(shape=float(ga[0]),loc=0.,scale=float(ga[2])),'Weibull':dict(shape=float(shape),loc=0.,scale=scale),'Lognormal':dict(log_mu=mu,log_sigma=sigma,loc=0.,scale=float(np.exp(mu))),'Exponential':dict(loc=0.,scale=float(x.mean()))}
vr=describe(v);paramsrows=[];fits=[];quantrows=[];tailrows=[];modelmetrics={}
qval=np.quantile(v,levels);tailthresholds=np.quantile(v,[.95,.99,.995,.999]);validation_empirical=np.arange(1,len(v)+1)/len(v)
u=(np.arange(20000)+.5)/20000;vq=np.quantile(v,u)
for name in ['Empirical_resampling']+list(models):
 if name=='Empirical_resampling':
  q=np.quantile(x,levels);mean=float(x.mean());sd=float(x.std());cdf=np.searchsorted(x,v,side='right')/len(x)
  # Two-sample statistic accounts for ties at all fit and validation locations.
  ks=float(stats.ks_2samp(x,v,method='asymp').statistic);w1=float(stats.wasserstein_distance(x,v));loglik=np.nan;aic=np.nan;bic=np.nan;vl=np.nan
  tails=1-np.searchsorted(x,tailthresholds,side='right')/len(x)
  pars=dict(representation='uniform row resampling with replacement; duplicate frequencies preserved',fit_rows=len(x),seed=42)
  wmethod='exact empirical one-dimensional Wasserstein';support=f'[{x[0]}, {x[-1]}] (fit empirical atoms)'
 else:
  model=models[name];q=model.ppf(levels);mean=float(model.mean());sd=float(model.std());cdf=model.cdf(v);ks=float(max(np.max(validation_empirical-cdf),np.max(cdf-(validation_empirical-1/len(v)))))
  w1=float(np.mean(abs(model.ppf(u)-vq)));wmethod='approximate quantile integral; 20000 equal-probability midpoints (extreme endpoints underweighted)'
  loglik=float(model.logpdf(x).sum());vl=float(model.logpdf(v).sum());k=1 if name=='Exponential' else 2;aic=2*k-2*loglik;bic=np.log(len(x))*k-2*loglik;tails=model.sf(tailthresholds);pars=params[name];support='(0,infinity); loc fixed 0; no epsilon_max'
 paramsrows.append(dict(candidate=name,parameters=json.dumps(pars),support=support,fitting_method='empirical counting' if name=='Empirical_resampling' else 'maximum likelihood; fixed loc=0',convergence_status='COMPLETED',fit_N=len(x),log_likelihood=loglik,AIC=aic,BIC=bic,zero_handling='zero mass observed=0; no offset; a future zero mass requires explicit atom/hurdle for strictly-positive families'))
 record=dict(candidate=name,fit_N=len(x),validation_N=len(v),mean=mean,validation_mean=vr['mean'],mean_error=mean-vr['mean'],mean_error_pct=100*(mean/vr['mean']-1),SD=sd,validation_SD=vr['SD'],SD_error=sd-vr['SD'],SD_error_pct=100*(sd/vr['SD']-1),KS_descriptive=ks,Wasserstein=w1,Wasserstein_method=wmethod,validation_log_likelihood=vl,validation_mean_log_likelihood=vl/len(v),fit_AIC=aic,fit_BIC=bic)
 for label,expected,pred in zip(labels,qval,q):
  quantrows.append(dict(candidate=name,quantile=label,probability=levels[labels.index(label)],validation_value=float(expected),model_value=float(pred),error=float(pred-expected),error_pct=float(100*(pred/expected-1))))
  record[label+'_error']=float(pred-expected)
 fits.append(record)
 for th,tail in zip(tailthresholds,tails):
  actual=float(np.mean(v>th));tailrows.append(dict(candidate=name,threshold=float(th),validation_probability_above=actual,predicted_probability_above=float(tail),error=float(tail-actual),error_percentage_points=float(100*(tail-actual))))
 modelmetrics[name]=dict(q=q,cdf=cdf)
 print('Fit evaluated',name,'KS',ks,'mean',mean,'SD',sd,flush=True)
for filename,rows in [('candidate_distribution_parameters',paramsrows),('distribution_fit_comparison',fits),('quantile_fit_comparison',quantrows),('upper_tail_probability_comparison',tailrows)]:pd.DataFrame(rows).to_csv(O/(filename+'.csv'),index=False)
# Plots use fit models and held-out empirical data; axis zoom never changes fitted populations.
plt.rcParams.update({'font.size':10,'figure.dpi':120});colors=dict(zip(['Empirical_resampling']+list(models),['black','#377eb8','#e41a1c','#4daf4a','#984ea3']))
def save(fig,name):fig.tight_layout();fig.savefig(O/'charts'/name,dpi=160);plt.close(fig)
cap=float(np.quantile(v,.995));grid=np.linspace(max(v.min(),1e-8),cap,1200)
fig,ax=plt.subplots(figsize=(9,5));bins=np.linspace(0,cap,100);hist,edges=np.histogram(v,bins=bins);ax.stairs(hist/(len(v)*np.diff(edges)),edges,label='Validation empirical',color='black');hx,_=np.histogram(x,bins=bins);ax.stairs(hx/(len(x)*np.diff(edges)),edges,label='Fit empirical',color='gray',alpha=.7)
for name,m in models.items():ax.plot(grid,m.pdf(grid),label=name,color=colors[name])
ax.set(xlabel='Epsilon',ylabel='Density (full-population normalization)',title='Held-out empirical and candidate densities\nCentral view to validation P99.5; tails retained');ax.legend();save(fig,'density_comparison.png')
fig,ax=plt.subplots(figsize=(9,5));ax.plot(grid,np.searchsorted(v,grid,side='right')/len(v),label='Validation empirical',color='black',lw=2);ax.plot(grid,np.searchsorted(x,grid,side='right')/len(x),label='Fit empirical',ls='--')
for name,m in models.items():ax.plot(grid,m.cdf(grid),label=name,color=colors[name])
ax.set(xlabel='Epsilon',ylabel='Cumulative probability',title='Empirical and fitted CDFs (central view)');ax.legend();save(fig,'cdf_comparison.png')
fig,axs=plt.subplots(2,3,figsize=(13,8));probs=np.unique(np.r_[np.linspace(.001,.99,150),np.linspace(.991,.9999,100)]);eq=np.quantile(v,probs)
for ax,name in zip(axs.flat,modelmetrics):
 mq=np.quantile(x,probs) if name=='Empirical_resampling' else models[name].ppf(probs);ax.plot(eq,mq,'.',ms=3);mx=max(eq.max(),mq.max());ax.plot([0,mx],[0,mx],'k--',lw=1);ax.set(title=name,xlabel='Validation quantile',ylabel='Candidate quantile')
axs.flat[-1].axis('off');fig.suptitle('Q-Q comparisons through P99.99 (fit set only; no tail truncation)');save(fig,'qq_comparison.png')
fig,ax=plt.subplots(figsize=(9,5));tg=np.geomspace(float(np.quantile(v,.9)),max(float(v.max()),float(x.max())),600)
ax.loglog(tg,1-np.searchsorted(v,tg,side='right')/len(v),label='Validation empirical',color='black');ax.loglog(tg,1-np.searchsorted(x,tg,side='right')/len(x),label='Fit empirical',ls='--')
for name,m in models.items():ax.loglog(tg,m.sf(tg),label=name,color=colors[name])
ax.set(xlabel='Epsilon (log scale)',ylabel='Probability above threshold (log scale)',title='Upper tails across the full observed range',ylim=(.1/len(v),.2));ax.legend();save(fig,'upper_tail_comparison.png')
fig,ax=plt.subplots(figsize=(9,5));qp=np.array([.1,.25,.5,.75,.9,.95]);ax.plot(qp,np.quantile(v,qp),'ko-',label='Validation empirical');ax.plot(qp,np.quantile(x,qp),'x--',label='Fit empirical')
for name,m in models.items():ax.plot(qp,m.ppf(qp),'o-',label=name,color=colors[name])
ax.set(xlabel='Quantile probability',ylabel='Epsilon',title='Central quantile comparison');ax.legend();save(fig,'central_quantile_comparison.png')
# Exact persisted data readback with statistics; does not alter data.
back=pd.read_parquet(artifact,columns=['source_observation_id','epsilon','epsilon_status','is_runtime_candidate','distribution_split']);assert len(back)==N and back.source_observation_id.is_unique
assert back.loc[back.epsilon_status=='DENOMINATOR_UNRESOLVED','epsilon'].isna().all()
bv=back.loc[back.is_runtime_candidate,'epsilon'].to_numpy();assert len(bv)==counts['final_nonnegative_candidate_N'] and np.isclose(bv.mean(),full['mean'],rtol=1e-14)
artifact_hash=sha(artifact);assert all(sha(R/k)==v for k,v in hashes.items())
contract=dict(methodology_version='PASSENGER_SENSITIVITY_V2_5PCT_POOLED_2026_11_14',calibration_period={'start_inclusive':'2026-01-01','end_exclusive':'2026-03-16'},P_base=P,P_norm=P,L_base=L,distance_unit='km',fare_field='fare derived from TLC fare_amount USD',distance_field='trip_distance miles converted with 1.609344',epsilon_formula='r_L/r_P; r_P=(P-P_base)/P_base; r_L=(L-L_base)/L_base',denominator_rule='abs(r_P)>=0.05 inclusive; otherwise epsilon NaN and DENOMINATOR_UNRESOLVED',denominator_relative_threshold=.05,effective_current_USD_threshold=.05*P,negative_epsilon_policy='NEGATIVE_AUDITED_EXCLUDED; historical values retained; no abs transformation',zero_epsilon_policy='NONNEGATIVE_VALID; retained; observed zero count=0',primary_population='pooled finite nonnegative denominator-resolved observations',weather_time_role='SECONDARY_DIAGNOSTICS',sd4_role='INTERNAL_STABILITY_DIAGNOSTIC',sampling_candidate='EMPIRICAL_RESAMPLING',sampling_candidate_status='REVIEWED_NOT_INTEGRATED',source_artifacts=list(hashes),source_hashes=hashes,reference_source=str(ref.relative_to(R)),reference_original_provenance=str(sources[-1].relative_to(R)),reference_scope_note='P_base originates from [1,75) km calibration; applied unchanged to current [1.5,75) km scope; values reused, not recomputed; historical approval metadata untouched',source_cleaning=cfg['source_cleaning'],population_path=str(artifact.relative_to(R)),population_sha256=artifact_hash,candidate_selector='is_runtime_candidate == True',observation_id_definition='zero-based row position in immutable source cache identified by SHA256',split={'rule':'NumPy default_rng(42), one uniform draw per candidate in source order; draw<0.8 FIT else VALIDATION','seed':42,'fit_N':len(x),'validation_N':len(v),'persisted_column':'distribution_split'},empirical_sampler_contract='uniform row index with replacement; preserve duplicate frequencies; caller-controlled RNG; reviewed final population includes all candidate rows after selection; no production integration',decision_authority='explicit current project task; 5% relative band operative; economic resolution motivates but does not add a stronger floor')
(O/'pricing_v2_sensitivity_contract.json').write_text(json.dumps(contract,indent=2))
ver=dict(population=counts,source_hashes_unchanged=True,source_date_bounds_checked=True,prior_C_counts_match=True,prior_C_moments_match=True,unresolved_epsilon_is_NaN=True,partition_reconciles=True,source_order_preserved=True,parquet_readback_pass=True,population_sha256=artifact_hash,population_bytes=artifact.stat().st_size,split_disjoint_and_complete=True,fit_uses_only_FIT=True,zero_N=0,weibull_score_residual=float(weibull_score(shape)),weather_cells=len(weather_rows),cells_N_ge50=sum(z['N_ge50'] for z in weather_rows),cells_N_ge100=sum(z['N_ge100'] for z in weather_rows),cells_SD_lt4=sum(z['SD_lt4'] for z in weather_rows),production_changes=False,V1_changes=False,registry_changes=False,training=False,clustering=False,protected_period_access=False,upper_truncation=False,epsilon_abs_transform=False,selection='EMPIRICAL_RESAMPLING_BEST_SUPPORTED')
(O/'verification.json').write_text(json.dumps(ver,indent=2,default=lambda z:z.item()));print('COMPLETE',flush=True)

# Full population figure; no fitting repeated.
a=bv

a=np.sort(a);cap=float(np.quantile(a,.995));fig,axs=plt.subplots(1,3,figsize=(15,4.5));edges=np.linspace(0,cap,100);hist,_=np.histogram(a,edges);axs[0].stairs(hist/(len(a)*np.diff(edges)),edges);axs[0].set(title='Pooled density: central P99.5 view',xlabel='Epsilon',ylabel='Density')
grid=np.linspace(0,cap,600);axs[1].plot(grid,np.searchsorted(a,grid,side='right')/len(a));axs[1].set(title='Pooled empirical CDF: central view',xlabel='Epsilon',ylabel='Cumulative probability')
t=np.geomspace(float(np.quantile(a,.9)),a[-1],600);axs[2].loglog(t,1-np.searchsorted(a,t,side='right')/len(a));axs[2].set(title='Pooled upper tail: full observed range',xlabel='Epsilon (log)',ylabel='Probability above (log)');fig.suptitle('Final nonnegative V2 population; no tail truncation');fig.tight_layout();fig.savefig(O/'charts/pooled_distribution_diagnostics.png',dpi=160);plt.close(fig)
