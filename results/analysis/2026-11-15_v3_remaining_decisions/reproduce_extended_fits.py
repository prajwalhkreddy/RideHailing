from pathlib import Path
import numpy as np,pandas as pd,json,hashlib
from scipy import stats,optimize,special
O=Path('results/analysis/2026-11-15_v3_remaining_decisions')
source='data/interim/pricing_v2_sensitivity/pricing_v2_sensitivity_population_jan01_mar15_2026.parquet'
f=pd.read_parquet(source,columns=['pickup_timestamp','weather_code','epsilon','is_runtime_candidate','distribution_split','source_observation_id'],filters=[('pickup_timestamp','>=',pd.Timestamp('2026-01-01')),('pickup_timestamp','<',pd.Timestamp('2026-03-16'))]);f=f[f.is_runtime_candidate].copy();assert len(f)==5779213
h=f.pickup_timestamp.dt.hour;f['T']=np.select([h<4,h<6,h<16],['T1','T2','T3'],default='T4')
manifest=pd.read_csv('results/analysis/2026-11-14_pricing_v2_time_specific_weather/conditional_support_manifest.csv');ids=pd.read_csv(O/'conditional_distribution_recommendations.csv').condition_id.tolist()
rows=[];splitinfo=[];qs=np.array([.25,.5,.75,.9,.95,.99]);
for sid in ids:
 if sid=='GLOBAL':g=f
 elif sid.startswith('RAW_'):g=f[f.weather_code==int(sid[4:])]
 elif sid=='T1_G1':g=f[(f['T']=='T1')&f.weather_code.isin([1,2,3,5,7,8,9,12,14,16])]
 else:g=f[f['T']==sid[:2]]
 assert len(g)==int(manifest.set_index('support_id').loc[sid,'N'])
 fit=g.distribution_split.eq('FIT');x=g.loc[fit,'epsilon'].to_numpy();v=np.sort(g.loc[~fit,'epsilon'].to_numpy());assert (x>0).all() and (v>0).all();n=len(x);logx=np.log(x);mu=logx.mean();sig=logx.std()
 splitinfo.append(dict(condition=sid,fit_N=n,validation_N=len(v),fit_ids_hash=hashlib.sha256(g.loc[fit,'source_observation_id'].to_numpy().tobytes()).hexdigest(),validation_ids_hash=hashlib.sha256(g.loc[~fit,'source_observation_id'].to_numpy().tobytes()).hexdigest()))
 # exact duplicate weighting makes likelihood optimization cheaper without sampling.
 u,c=np.unique(x,return_counts=True);w=c/n;lu=np.log(u)
 models=[]
 ga=stats.gamma.fit(x,floc=0);models.append(('Gamma',stats.gamma,ga,True,2))
 models.append(('Lognormal',stats.lognorm,(sig,0,np.exp(mu)),True,2))
 def ws(k):
  a=np.exp(k*(lu-lu.max()))*w;return 1/k+mu-np.dot(a,lu)/a.sum()
 k=optimize.brentq(ws,.01,100);scale=np.exp(special.logsumexp(k*lu,b=w)/k);models.append(('Weibull',stats.weibull_min,(k,0,scale),True,2))
 ex=x.mean();ex2=np.mean(x*x)
 def tn(a):
  z,ls=a;s=np.exp(ls);m=z*s;return ls+.5*np.log(2*np.pi)+.5*(ex2-2*m*ex+m*m)/s**2+special.log_ndtr(z)
 res=min([optimize.minimize(tn,[z,np.log(x.std())],bounds=[(-100,100),(-15,15)],method='L-BFGS-B') for z in [-2,0,2]],key=lambda r:r.fun);z,ls=res.x;s=np.exp(ls);models.append(('Truncated_normal',stats.truncnorm,(-z,np.inf,z*s,s),bool(res.success and abs(z)<99.9 and abs(ls)<14.99),2))
 def fisk(a):
  shape=np.exp(a[0]);ls=a[1];t=shape*(lu-ls);return -np.dot(w,np.log(shape)-ls+(shape-1)*(lu-ls)-2*np.logaddexp(0,t))
 res=optimize.minimize(fisk,[0,mu],method='L-BFGS-B',bounds=[(-6,6),(-15,15)]);models.append(('Fisk',stats.fisk,(np.exp(res.x[0]),0,np.exp(res.x[1])),bool(res.success),2))
 def gg(a):
  aa,cc,ls=np.exp(a[0]),np.exp(a[1]),a[2];t=lu-ls
  if np.max(cc*t)>700:return 1e100
  return -np.dot(w,np.log(cc)-ls-special.gammaln(aa)+(aa*cc-1)*t-np.exp(cc*t))
 res=min([optimize.minimize(gg,[np.log(a),np.log(c0),mu],method='L-BFGS-B',bounds=[(-8,10),(-6,6),(-15,15)],options={'maxiter':600}) for a,c0 in [(1,1),(2,.5),(.5,2)]],key=lambda r:r.fun)
 ok=bool(res.success and -7.99<res.x[0]<9.99 and -5.99<res.x[1]<5.99 and abs(res.x[2])<14.99);models.append(('Generalized_gamma',stats.gengamma,(np.exp(res.x[0]),np.exp(res.x[1]),0,np.exp(res.x[2])),ok,3))
 eq=np.quantile(v,qs);ec=np.arange(1,len(v)+1)/len(v)
 for name,dist,pars,ok,k in models:
  cdf=dist.cdf(v,*pars);q=dist.ppf(qs,*pars);ll=float(np.dot(c,dist.logpdf(u,*pars)));ks=max(np.max(ec-cdf),np.max(cdf-ec+1/len(v)));rr=dict(condition=sid,N=len(g),fit_N=n,validation_N=len(v),candidate=name,parameters=json.dumps(list(pars)),support='(0,infinity)',lower=0,upper='infinity',convergence=ok,support_valid=bool(np.isfinite(q).all() and (q>0).all()),log_likelihood=ll,AIC=2*k-2*ll,BIC=k*np.log(n)-2*ll,heldout_log_likelihood=float(np.sum(dist.logpdf(v,*pars))),KS=ks,tail_probability_error=float(dist.sf(eq[-1],*pars)-.01))
  for p,e,a in zip(qs,eq,q):rr.update({f'P{p*100:g}_empirical':e,f'P{p*100:g}_fitted':a,f'P{p*100:g}_error':a-e,f'P{p*100:g}_abs_error':abs(a-e),f'P{p*100:g}_relative_error':(a-e)/e})
  rows.append(rr)
 q=np.quantile(x,qs);rr=dict(condition=sid,N=len(g),fit_N=n,validation_N=len(v),candidate='Empirical_reference',parameters='fit rows only; preserve duplicate frequencies',support='observed fit values',convergence=True,support_valid=True,KS=stats.ks_2samp(x,v,method='asymp').statistic,tail_probability_error=float(np.mean(x>eq[-1])-.01))
 for p,e,a in zip(qs,eq,q):rr.update({f'P{p*100:g}_error':a-e,f'P{p*100:g}_abs_error':abs(a-e),f'P{p*100:g}_relative_error':(a-e)/e})
 rows.append(rr);pd.DataFrame(rows).to_csv(O/'extended_conditional_distribution_fits.csv',index=False)
 (O/'fit_split_hashes.json').write_text(json.dumps({'seed':42,'split':'persisted canonical FIT/VALIDATION, Bernoulli0.8; identical rows across families','source':source,'conditions':splitinfo},indent=2));print(sid,'done',flush=True)
