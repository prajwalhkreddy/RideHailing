"""Weighted full-population likelihood fits; no runtime model or training imports."""
from pathlib import Path
import json,sys
import numpy as np,pandas as pd
from scipy import stats,optimize,special
R=Path(__file__).parent
sys.path.insert(0,str(R));from analyze import checkpoint,js,save

def fit_parameters(family,x,w):
 w=w/w.sum();mean=np.dot(w,x)
 if family=='normal':return [mean,np.sqrt(np.dot(w,(x-mean)**2))]
 if family=='exponential':return [0.,mean]
 logx=np.log(x);ml=np.dot(w,logx)
 if family=='lognormal':return [np.sqrt(np.dot(w,(logx-ml)**2)),0.,np.exp(ml)]
 if family=='gamma':
  gap=np.log(mean)-ml
  k=optimize.brentq(lambda k:np.log(k)-special.digamma(k)-gap,1e-6,1e8)
  return [k,0.,mean/k]
 if family=='weibull':
  def equation(k):
   z=k*logx;v=w*np.exp(z-z.max());return 1/k+ml-np.dot(v,logx)/v.sum()
  k=optimize.brentq(equation,1e-5,1e5)
  scale=np.exp((special.logsumexp(np.log(w)+k*logx))/k)
  return [k,0.,scale]
 raise ValueError(family)
D={'normal':stats.norm,'exponential':stats.expon,'gamma':stats.gamma,'lognormal':stats.lognorm,'weibull':stats.weibull_min}
def go():
 assert (R/'intermediate/data_complete.json').exists()
 frame=pd.read_csv(R/'array_a/array_distance_representation_comparison.csv');scenarios=[]
 for (c,r),g in frame.groupby(['candidate','representation'],sort=True):
  for pop,w in [('BIN_UNWEIGHTED',np.ones(len(g))),('BIN_COUNT_WEIGHTED',g.N.to_numpy())]:scenarios.append((pop,c,r,g.new_e.to_numpy(),w))
 candidates=json.loads((R/'reference_values/candidates.json').read_text())['L_candidates']
 for c in candidates:
  fn=R/f'intermediate/unique_{c}.npz'
  if not fn.exists():
   e=np.load(R/f'intermediate/new_e_{c}.npy',mmap_mode='r');x,w=np.unique(e[np.isfinite(e)],return_counts=True);np.savez_compressed(fn,x=x,w=w)
  z=np.load(fn);scenarios.append(('TRIP_LEVEL_NEW_E',c,'ACTUAL_TRIP',z['x'],z['w']))
 for c in candidates:
  fn=R/f'intermediate/unique_ALL_SAFE_{c}.npz'
  if not fn.exists():
   e=np.load(R/f'intermediate/new_e_ALL_SAFE_{c}.npy',mmap_mode='r');x,w=np.unique(e[np.isfinite(e)],return_counts=True);np.savez_compressed(fn,x=x,w=w)
  z=np.load(fn);scenarios.append(('TRIP_LEVEL_NEW_E_ALL_SAFE',c,'ACTUAL_TRIP',z['x'],z['w']))
 allrows=[];qq=[];curves=[]
 for pop,c,rep,values,weights in scenarios:
  key=f'{pop}_{c}_{rep}';dest=R/f'distribution_fits/{key}.json'
  if dest.exists() and json.loads(dest.read_text()).get('version')==3:
   prior=json.loads(dest.read_text());allrows+=prior['rows'];qq+=prior['qq'];curves+=prior['curves'];continue
  order=np.argsort(values);xx=values[order];ww=np.asarray(weights[order],float);good=np.isfinite(xx);xx=xx[good];ww=ww[good]
  rows=[];qs=[];cs=[];n=ww.sum();negative=float(ww[xx<0].sum());zero=float(ww[xx==0].sum())
  for treatment in ['SIGNED_COMPLETE','POSITIVE_COMPONENT_DIAGNOSTIC']:
   x=xx if treatment=='SIGNED_COMPLETE' else xx[xx>0];w=ww if treatment=='SIGNED_COMPLETE' else ww[xx>0]
   mass=w.sum();prob=w/mass;cum=np.cumsum(prob);left=cum-prob
   kish=1/np.sum(prob**2) if not pop.startswith('TRIP_LEVEL_NEW_E') else mass
   # Weighted-bin likelihood is a frequency-weighted descriptive objective, not millions of independent bin observations.
   pqs=np.linspace(.01,.99,99);empq=x[np.minimum(np.searchsorted(cum,pqs),len(x)-1)]
   low,high=empq[0],empq[-1];grid=np.linspace(low,high,250)
   indices=np.searchsorted(x,grid,side='right')-1;empirical=np.where(indices>=0,cum[np.maximum(indices,0)],0.)
   for family in ['normal','gamma','lognormal','weibull','exponential','empirical']:
    base=dict(population=pop,L_base_candidate=c,distance_representation=rep,scope='ALL_SAFE' if pop.endswith('ALL_SAFE') else 'ARRAY_RANGE',sign_treatment=treatment,zero_treatment='Retained in full; positive component excludes zero explicitly' if treatment=='SIGNED_COMPLETE' else 'Conditional e>0 ONLY; omitted negative/zero mass separately reported; NOT a full-population replacement',N_mass=mass,N_distinct_support_points=len(x),effective_N_Kish=kish,original_negative_mass=negative,original_zero_mass=zero,component_pct=100*mass/n,support='real line' if family=='normal' else 'empirical support' if family=='empirical' else 'positive',family=family,parameters=None,log_likelihood=None,AIC=None,BIC=None,AIC_effective_N=None,BIC_effective_N=None,KS=None,KS_p_value=None,KS_interpretation='Descriptive fitted-CDF discrepancy only. No unadjusted KS p-value: parameters estimated; bin proxies not IID passengers; trip records dependent. No calibrated hypothesis rejection claimed.')
    if family=='empirical':
     base.update(parameters='All empirical values with original probability masses; no fitted finite-dimensional parameterization',KS=0.,support_compatibility='COMPATIBLE',qualitative_fit='Exact in-sample empirical baseline; KS=0 is tautological, not out-of-sample validation; AIC/BIC not comparable')
     rows.append(base);continue
    if family!='normal' and ((x<0).any() or (family!='exponential' and (x==0).any())):
     base.update(support_compatibility='INCOMPATIBLE_WITH_NEGATIVES' if (x<0).any() else 'ZERO_BOUNDARY_TREATMENT_REQUIRED',qualitative_fit='No abs, shift or deletion applied to full population. See explicit positive-component diagnostic.')
     rows.append(base);continue
    params=fit_parameters(family,x,w);dist=D[family](*params);lp=dist.logpdf(x);ll=float(np.dot(w,lp));k=1 if family=='exponential' else 2
    cdf=dist.cdf(x);ks=float(max(np.max(cum-cdf),np.max(cdf-left)))
    score=float(np.dot(prob,lp));aic=2*k-2*ll;bic=k*np.log(mass)-2*ll
    base.update(parameters=json.dumps(params),log_likelihood=ll,mean_log_score=score,AIC=aic,BIC=bic,AIC_effective_N=2*k-2*kish*score,BIC_effective_N=k*np.log(kish)-2*kish*score,KS=ks,support_compatibility='COMPATIBLE_BASELINE_ALLOWS_NEGATIVE' if family=='normal' and treatment!='SIGNED_COMPLETE' else 'COMPATIBLE',qualitative_fit='Descriptive KS='+format(ks,'.4f')+'; ranking only within identical population/component; no final family selected',fit_method='Full weighted MLE; loc=0 for positive families; normal unrestricted; no subsampling')
    rows.append(base)
    for q,observed,theory in zip(pqs,empq,dist.ppf(pqs)):qs.append(dict(scenario=key,treatment=treatment,family=family,probability=q,empirical_quantile=observed,fitted_quantile=theory))
    if c=='A_LOWER_EDGE' and rep in ['LOWER_EDGE','ACTUAL_TRIP']:
     for g,ec,fc,pdf in zip(grid,empirical,dist.cdf(grid),dist.pdf(grid)):cs.append(dict(scenario=key,treatment=treatment,family=family,e=g,empirical_cdf=ec,fitted_cdf=fc,fitted_density=pdf))
   # plot only designated reference scenarios, all candidate metrics persisted
   if c=='A_LOWER_EDGE' and rep in ['LOWER_EDGE','ACTUAL_TRIP']:
    import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
    fig,ax=plt.subplots(1,3,figsize=(15,4.4));edges=np.linspace(low,high,70);h,_=np.histogram(x,bins=edges,weights=prob);ax[0].stairs(h/np.diff(edges),edges,label='Empirical',color='black')
    ax[1].plot(grid,empirical,color='black',label='Empirical')
    for rr in rows:
     if rr['sign_treatment']!=treatment or rr['parameters'] is None or rr['family']=='empirical':continue
     family=rr['family'];dd=D[family](*json.loads(rr['parameters']));ax[0].plot(grid,dd.pdf(grid),label=family);ax[1].plot(grid,dd.cdf(grid),label=family);ax[2].plot(dd.ppf(pqs),empq,label=family,linewidth=1)
    ax[2].plot([low,high],[low,high],'k--',label='Identity');ax[2].set_xlabel('Fitted quantile');ax[2].set_ylabel('Empirical quantile')
    for axis,title in zip(ax,['Histogram and density','CDF','Q–Q (P1–P99)']):axis.set_title(title);axis.grid(alpha=.2)
    ax[0].set_xlabel('new e');ax[1].set_xlabel('new e');ax[0].set_ylabel('Density; full component mass (display subset)');ax[1].set_ylabel('Cumulative probability');ax[0].legend(fontsize=7)
    fig.suptitle(f'{pop}, L_base=4.5 km, {rep}\n{treatment}; P1–P99 display only; full tails retained in fits/statistics',fontsize=10);fig.tight_layout();fig.savefig(R/f'distribution_fits/{key}_{treatment}.png',dpi=160);plt.close(fig)
  js(f'distribution_fits/{key}.json',dict(version=3,rows=rows,qq=qs,curves=cs));allrows+=rows;qq+=qs;curves+=cs;checkpoint('FIT_SCENARIO_COMPLETE',scenario=key)
 save('distribution_fits/distribution_fit_comparison.csv',allrows);save('distribution_fits/qq_diagnostics.csv',qq);save('distribution_fits/cdf_density_overlays.csv',curves)
 df=pd.DataFrame(allrows);valid=df[df.family.ne('empirical')&df.AIC.notna()];best=valid.sort_values(['AIC','KS']).groupby(['population','L_base_candidate','distance_representation','sign_treatment'],sort=False).first().reset_index();save('distribution_fits/best_within_scenario.csv',best)
 js('intermediate/fits_complete.json',dict(scenarios=len(scenarios),fit_rows=len(allrows),final_family_selected=False));checkpoint('FITS_COMPLETE')
if __name__=='__main__':go()
