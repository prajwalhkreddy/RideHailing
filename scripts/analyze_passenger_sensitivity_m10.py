#!/usr/bin/env python3
"""Generate standalone M9/M10 professor review; never run a simulator."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np
import pandas as pd
from src.analysis.passenger_sensitivity_m10 import (
    START,CUTOFF,compute_m10,distribution,time_support,small_delta_p,outlier_comparison,
    candidate_distributions,acceptance_sanity,write_csv,
)

DEFAULT=ROOT/'results/analysis/2026-09-27_passenger_sensitivity_m10'
SOURCE_DOC=ROOT/'notebooks/plan/Final_Module_Wise_Algorithm_Input_Output_Document.pdf'


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def differences():
    rows=[
      ('epsilon formula','abs(relative price / relative distance)','relative distance / raw price deviation','NO','Isolated new M10; legacy preserved'),
      ('delta_L filter','Absolute distance deviation >= .01 mile','delta_L > 0','NO','Strict positive; no .01 rule'),
      ('delta_P filter','No positive-only deviation filter','delta_P > 0','NO','Strict positive; no extra floor'),
      ('absolute value','Applied','Not applied','NO','No abs in new formula'),
      ('base price','Arithmetic condition mean fare','Arithmetic condition mean fare','YES, definition','Recompute from documented M10 eligible inputs'),
      ('base distance','Arithmetic condition mean distance','Arithmetic condition mean distance','YES, definition','Recompute; do not reuse old capped-row bases'),
      ('Time grouping','30-minute Period 0..47','Time-of-Day width unspecified; M3 operational slots 30min','OPEN','Compare 30min/hourly; do not freeze'),
      ('Weather grouping','Hourly NYC WeatherCode, naive timestamps','Document join rule; no category regrouping specified','COMPATIBLE convention','Retain individual codes and disclose alignment assumption'),
      ('input validity','Finite positive fare, 0 < miles <=100','M1 documented invalid rules; no numeric cap in M9/M10','PARTIAL','Positive finite input rule; disclose omission of old 100-mile cap; no new rule'),
      ('outliers','No epsilon cap; .01-mile delta and 100-mile source rules','Document/apply chosen rule, no rule specified','OPEN','Diagnostic alternatives only; PROFESSOR DECISION REQUIRED'),
      ('mean/std','Mean, population and sample SD','Mean/std/count; ddof unspecified','COMPATIBLE with task','Population ddof=0 per explicit task'),
      ('sampling family','Positive-truncated Normal using historical mean/SD','Inspect empirical distribution before freezing','OPEN','Empirical/Normal/truncated Normal/lognormal diagnostics; no runtime sampler'),
      ('fallback','Exact -> Period -> Weather -> Global','No hierarchy specified','OPEN','No pooling or imputation in M10'),
      ('M12','P_base + relative distance * P_base / epsilon','P_base + relative distance / epsilon','NO','New equation analysis only; production untouched'),
      ('privacy','epsilon in request/customer audit; not eight-dimensional pricing or routing vector','Individual epsilon private; excluded from DQN','PARTIAL architecture','Private local diagnostics; explicit aggregate-only future schema, no DQN implementation'),
    ]
    return pd.DataFrame(rows,columns=['requirement','current_implementation','new_pdf_requirement','compatible','action'])


def charts(output, variants, outliers, sampling, sanity):
    folder=output/'charts';folder.mkdir(exist_ok=True)
    plt.rcParams.update({'font.size':10,'axes.titlesize':12,'axes.labelsize':10})
    manifest=[]
    names=list(variants)
    def save(fig,stem,note):
        fig.tight_layout(rect=(0,0.035,1,.95))
        fig.text(.5,.008,note,ha='center',fontsize=8,wrap=True)
        paths=[]
        for ext in ['png','pdf']:
            p=folder/f'{stem}.{ext}'
            kw={'metadata':{'CreationDate':None,'ModDate':None}} if ext=='pdf' else {}
            fig.savefig(p,dpi=170,bbox_inches='tight',**kw);paths.append(str(p.relative_to(output)))
        plt.close(fig)
        manifest.append(dict(chart=stem,files=paths,note=note))
    def panels(title):
        fig,axes=plt.subplots(1,len(names),figsize=(13,4.6),squeeze=False)
        fig.suptitle(title)
        return fig,axes[0]
    for mode,stem,title in [
        ('raw','01_epsilon_histogram','Raw M10 epsilon: entire range'),
        ('zoom','02_epsilon_histogram_zoomed','M10 epsilon: view through P99'),
        ('log','03_log_epsilon_distribution','log1p(epsilon): visualization only')]:
        fig,axes=panels(title)
        for ax,v in zip(axes,names):
            x=variants[v]['obs'].epsilon.to_numpy()
            if mode=='log':z=np.log1p(x)
            elif mode=='zoom':z=x[x<=np.quantile(x,.99)]
            else:z=x
            ax.hist(z,bins=90,color='#35618f');ax.set(title=v,xlabel='log1p(epsilon)' if mode=='log' else 'epsilon (1/USD)',ylabel='Observations')
            if mode in {'raw','log'}:ax.set_yscale('log')
            if mode=='zoom':ax.text(.98,.96,f'View omits {len(x)-len(z):,} rows\nFull max={x.max():.5g}',ha='right',va='top',transform=ax.transAxes,fontsize=9)
        save(fig,stem,'No analysis observations removed. Raw and log1p panels use log count axes; the P99 view is a display limit only.')
    fig,axes=panels('Empirical cumulative distribution (all valid observations)')
    for ax,v in zip(axes,names):
        x=np.sort(variants[v]['obs'].epsilon.to_numpy());ax.plot(x,np.arange(1,len(x)+1)/len(x),lw=1.5,rasterized=True)
        ax.set(xscale='log',xlabel='epsilon (1/USD), log axis',ylabel='Fraction at or below epsilon',title=v,ylim=(0,1));ax.grid(alpha=.2)
    save(fig,'04_epsilon_ecdf','The logarithmic x-axis displays the full positive tail; no iid significance test is implied.')
    fig,axes=panels('M10 epsilon by historical WeatherCode')
    for ax,v in zip(axes,names):
        obs=variants[v]['obs'];codes=variants[v]['codes'];summ=[];labels=[]
        for code in codes:
            x=obs.loc[obs.WeatherCode==code,'epsilon'].to_numpy()
            if len(x):
                q=np.quantile(x,[.05,.25,.5,.75,.95]);summ.append(dict(whislo=q[0],q1=q[1],med=q[2],q3=q[3],whishi=q[4],fliers=[]));labels.append(f'{code}\nN={len(x):,}')
            else:
                summ.append(dict(whislo=np.nan,q1=np.nan,med=np.nan,q3=np.nan,whishi=np.nan,fliers=[]));labels.append(f'{code}\nN=0')
        ax.bxp(summ,showfliers=False);ax.set_xticks(range(1,len(labels)+1),labels,rotation=60,ha='right',fontsize=7)
        ax.set(yscale='log',ylabel='epsilon (1/USD), log axis',xlabel='WeatherCode and retained N',title=v)
    save(fig,'05_epsilon_by_weather','Boxes: P25-P75; center: median; whiskers: P5-P95. Tails omitted visually only; codes remain separate.')
    def curves(v,metric,stem,title):
        d=variants[v];fig,ax=plt.subplots(figsize=(12,5.6));colors=plt.get_cmap('tab20')
        for i,code in enumerate(d['codes']):
            z=d['conditions'].loc[d['conditions'].WeatherCode==code].set_index('time_bucket').reindex(range(48 if v=='30min' else 24))
            ax.plot(z.index,z[metric],marker='.',ms=3,lw=1,color=colors(i),label=f'W{code}')
        ax.set(xlabel='Period 0-47' if v=='30min' else 'Hour 0-23',ylabel=f'{metric} (1/USD), log axis',yscale='log',title=title)
        ax.legend(ncol=7,loc='upper center',bbox_to_anchor=(.5,-.15),fontsize=9);ax.grid(alpha=.2)
        save(fig,stem,'Missing conditions remain gaps. Descriptive historical association; unequal support is shown in chart 09.')
    curves('30min','mean_epsilon','06_mean_epsilon_by_time_weather','Mean M10 epsilon by 30-minute Period and WeatherCode')
    curves('30min','median','07_median_epsilon_by_time_weather','Median M10 epsilon by 30-minute Period and WeatherCode')
    curves('hourly','mean_epsilon','08_mean_epsilon_by_hour_weather','Mean M10 epsilon by Hour and WeatherCode (comparison only)')
    fig,axes=plt.subplots(2,2,figsize=(14,9));fig.suptitle('Condition support: bases versus retained M10 observations')
    for row,v in enumerate(names):
        for col,pop in enumerate(['bases','conditions']):
            ax=axes[row,col];tab=variants[v][pop]
            mat=tab.pivot(index='WeatherCode',columns='time_bucket',values='sample_count').reindex(index=variants[v]['codes'],columns=range(48 if v=='30min' else 24))
            z=mat.to_numpy(dtype=float);cmap=plt.get_cmap('viridis').copy();cmap.set_bad('#dedede')
            im=ax.imshow(np.ma.masked_where(~np.isfinite(z)|(z<=0),z),aspect='auto',norm=LogNorm(vmin=1,vmax=max(1,np.nanmax(z))),cmap=cmap)
            ax.set(title=f'{v}: {"base N" if pop=="bases" else "epsilon N"}',xlabel='Time bucket',ylabel='WeatherCode');ax.set_yticks(range(len(mat)),[int(x) for x in mat.index]);fig.colorbar(im,ax=ax,label='Rows (log color scale)')
    save(fig,'09_condition_sample_counts','Grey = missing or zero. Possible conditions use only weather codes present in the pre-cutoff weather artifact.')
    for xcol,stem,title in [('delta_P','10_epsilon_vs_delta_p','Epsilon versus positive fare deviation'),('relative_delta_L','11_epsilon_vs_relative_distance','Epsilon versus positive relative distance deviation')]:
        fig,axes=panels(title)
        for ax,v in zip(axes,names):
            obs=variants[v]['obs'];im=ax.hexbin(obs[xcol],obs.epsilon,gridsize=60,xscale='log',yscale='log',bins='log',mincnt=1,cmap='viridis',rasterized=True)
            ax.set(xlabel='delta_P (USD), log axis' if xcol=='delta_P' else 'relative_delta_L, log axis',ylabel='epsilon (1/USD), log axis',title=v);fig.colorbar(im,ax=ax,label='Observations per hexagon (log)')
        save(fig,stem,'All retained rows contribute to density bins; the formula mechanically relates these variables, so this is not independent causal evidence.')
    fig,axes=panels('Small positive delta_P and the epsilon tail')
    for ax,v in zip(axes,names):
        tab=variants[v]['small'];x=np.arange(len(tab))
        for col,label in [('median','Median'),('p99','P99'),('max','Maximum')]:ax.plot(x,tab[col],marker='o',label=label)
        ax.set_xticks(x,[f'{label}\nN={n:,}' for label,n in zip(['(0,.01)','[.01,.05)','[.05,.10)','[.10,.25)','[.25,.50)','[.50,inf)'],tab['count'])],rotation=35,ha='right',fontsize=8)
        ax.set(yscale='log',ylabel='epsilon (1/USD), log axis',xlabel='delta_P bin (USD)',title=v);ax.legend()
    save(fig,'12_small_delta_p_tail','Bins are disjoint and exhaustive among valid M10 rows. No additional denominator floor is applied.')
    fig,axes=panels('Diagnostic outlier-rule effects: no rule selected')
    for ax,v in zip(axes,names):
        tab=outliers.loc[outliers.variant==v];x=np.arange(len(tab))
        for col in ['mean','std_population','median']:ax.plot(x,tab[col],marker='o',label=col)
        labels=['None','P99','P99.5','P99.9','IQR','log1p IQR']
        ax.set_xticks(x,[f'{l}\n{p:.2f}% kept' for l,p in zip(labels,tab.percent_retained)],rotation=30,ha='right',fontsize=8)
        ax.set(yscale='log',ylabel='epsilon (1/USD), log axis',title=v);ax.legend(fontsize=8)
    save(fig,'13_outlier_rule_comparison','PROFESSOR DECISION REQUIRED. Global pooled diagnostic thresholds; not per-condition production rules.')
    fig,axes=plt.subplots(2,2,figsize=(13,9));fig.suptitle('Empirical distribution and candidate sampling families (unfrozen)')
    for row,v in enumerate(names):
        x=np.sort(variants[v]['obs'].epsilon.to_numpy());_,candidates=candidate_distributions(x)
        ax=axes[row,0];lo,hi=np.quantile(x,[.001,.999]);grid=np.geomspace(max(x.min(),lo),hi,500)
        ax.plot(x,np.arange(1,len(x)+1)/len(x),label='Empirical',color='black',lw=2,rasterized=True)
        for name,dist in candidates.items():ax.plot(grid,dist.cdf(grid),label=name)
        ax.set(xscale='log',xlim=(grid[0],grid[-1]),ylim=(0,1),xlabel='epsilon (1/USD), log axis',ylabel='CDF',title=f'{v}: central 99.8% view');ax.legend(fontsize=7)
        ax=axes[row,1];qs=np.array([.1,.25,.5,.75,.9,.95,.99]);positions=np.arange(len(qs))
        ax.plot(positions,np.quantile(x,qs),label='Empirical',marker='o',color='black')
        for name,dist in candidates.items():ax.plot(positions,dist.ppf(qs),label=name,marker='.')
        ax.set_xticks(positions,[f'P{q*100:g}' for q in qs]);ax.set_yscale('symlog',linthresh=.01);ax.set(ylabel='epsilon (1/USD), symmetric-log axis',title=f'{v}: candidate quantiles (negative Normal allowed)')
        ax.axhline(0,color='grey',lw=.5)
    save(fig,'14_sampling_distribution_comparison','Descriptive pooled fits only; truncated Normal uses underlying empirical mean/SD, not matched truncated moments. No family is selected.')
    fig,axes=panels('Illustrative M12: fare tolerance above condition base')
    for ax,v in zip(axes,names):
        tab=sanity.loc[(sanity.variant==v)&(sanity.price_factor==1)]
        for rel in [.05,.1,.25,.5,1.]:
            z=tab.loc[tab.relative_distance==rel];ax.plot(z.epsilon_percentile,z.tolerance,marker='o',label=f'+{rel:.0%} distance')
        ax.set(yscale='log',xlabel='Pooled historical epsilon percentile',ylabel='P_max - P_base (USD), log axis',title=v);ax.legend(fontsize=8)
    save(fig,'15_m12_tolerance','ILLUSTRATIVE - NOT PRODUCTION INTEGRATION. Positive distance scenarios only; small epsilon can produce very high willingness to pay.')
    # Additional requested mean/std condition view, alongside the 15 numbered figures.
    fig,axes=plt.subplots(2,2,figsize=(14,9));fig.suptitle('Condition-level M10 mean and population standard deviation')
    for row,v in enumerate(names):
        for col,metric in enumerate(['mean_epsilon','std_epsilon']):
            ax=axes[row,col];mat=variants[v]['conditions'].pivot(index='WeatherCode',columns='time_bucket',values=metric).reindex(index=variants[v]['codes'],columns=range(48 if v=='30min' else 24))
            z=mat.to_numpy(float);masked=np.ma.masked_where(~np.isfinite(z)|(z<=0),z);cmap=plt.get_cmap('magma').copy();cmap.set_bad('#dedede')
            im=ax.imshow(masked,aspect='auto',norm=LogNorm(),cmap=cmap);fig.colorbar(im,ax=ax,label='epsilon units (1/USD), log color')
            ax.set(title=f'{v}: {metric}',xlabel='Time bucket',ylabel='WeatherCode');ax.set_yticks(range(len(mat)),[int(x) for x in mat.index])
    save(fig,'16_condition_summary','Grey = absent or zero statistic; singleton population SD is zero. Use condition N before interpreting extreme means/SDs.')
    return manifest


def markdown_table(frame,cols=None):
    f=frame if cols is None else frame[cols]
    def fmt(x):
        if isinstance(x,(float,np.floating)):return f'{x:.6g}'
        return str(x).replace('|','/')
    return '| '+' | '.join(map(str,f.columns))+' |\n| '+' | '.join(['---']*len(f.columns))+' |\n'+'\n'.join('| '+' | '.join(fmt(x) for x in row)+' |' for row in f.itertuples(index=False,name=None))


def review_readme(out,summary,variants,overall,support,small,outlier,sampling,sanity,weather_summary):
    parts=['''# M9/M10 passenger sensitivity: professor review

**Status: READY_FOR_PROFESSOR_REVIEW, not frozen and not production-integrated.**

## 1. Authoritative document and findings

Source: [Final_Module_Wise_Algorithm_Input_Output_Document.pdf](../../../notebooks/plan/Final_Module_Wise_Algorithm_Input_Output_Document.pdf). All 24 pages were text-inspected; M9/M10/M12 equations were also visually checked. Key sections: overall flow p.1; master table pp.2-4; M3 p.7; M9 p.13; M10 p.14; M11/privacy p.15; M12 p.16; exact slot algorithm and coding order p.23; integration checklist p.24. The document puts M9/M10 before pricing/integration. Future DQN and routing changes are outside this task.

M3 fixes **operational** slots at 30 minutes, but M9 says Time-of-Day groups without defining their width. Neither weather regrouping, a numeric outlier rule, a sampling family, nor sparse-condition fallback is specified. Thus 30-minute Period and Hour are compared, not selected. Population SD (`ddof=0`) follows the explicit task. “Document and apply the chosen outlier rule” remains pending; untrimmed results are the audit reference, not a frozen choice of no trimming.

## 2. Exact M9/M10 definitions and units

For condition c, **L_base,c = mean(L_i)** and **P_base,c = mean(P_i)** over positive finite historical distance/fare rows with a valid condition. Each trip has raw deviations `delta_L = L_i - L_base,c` and `delta_P = P_i - P_base,c`. Then:

```text
relative_delta_L = delta_L / L_base,c
epsilon_i = relative_delta_L / delta_P
retain iff delta_L > 0 and delta_P > 0 and epsilon finite and epsilon > 0
```

L_i is source TLC trip distance in miles, P_i is `fare_amount` in USD, and c identifies time bucket plus WeatherCode. The ratio of distances is dimensionless; **epsilon has units 1/USD**, unlike the old dimensionless ratio. Changing distance units consistently for L_i and its base cancels; changing fare currency rescales epsilon. No absolute value is used. Means are computed BEFORE the positive-deviation filters, not from only above-base trips.

Current production remains legacy: absolute relative-price/relative-distance ratio, previous input/deviation rules, positive-truncated Normal and exact→Period→Weather→Global fallback, with an extra P_base factor in its willingness-to-pay adjustment. [Full 15-row difference table](current_vs_new_m10.csv). Old code and artifacts were not overwritten.

## 3. Historical data, source validity and weather join

Use existing `data/processed/cleaned_trips.parquet`. Frozen pickup window: **2026-01-01 00:00 inclusive to 2026-01-25 18:30 exclusive**. Future trip rows and weather timestamps are removed before fitting or diagnostics. Invalid/unparseable pickup timestamps cannot enter that window. No hold-out values determine bases, percentiles, fit parameters, outlier diagnostics or acceptance scenarios.

Weather uses the existing processed NYC point-derived Meteostat hourly WeatherCode joined by pickup timestamp floored to the hour. Timestamps retain the project's documented naive-time assumption; no new timezone conversion, interpolation, or WeatherCode merging is introduced. The source weather file already contains legacy forward/backward fill; this analysis does not claim a new causal weather-feed validation. Condition IDs are unambiguous strings `30min:Txx:Wcode` or `hourly:Txx:Wcode`; “Time × Weather” is a Cartesian pairing, not numerical multiplication.

Input eligibility is finite strictly positive distance and fare. **The old sensitivity-specific 100-mile cap and .01-mile absolute distance-deviation threshold are not carried into new M10.** They are absent from the new M9/M10 formula and requested funnel. The old cap excludes 93 otherwise positive-finite historical rows; the summary separately records extreme source counts for review. No new “impossible trip” threshold is invented. This is a documented analysis input policy requiring source-quality interpretation before freezing, not an assertion that all positive historical outliers are plausible. A future approved input cleaning change would require recomputing both bases and epsilon.

`trip_id` is retained if present; otherwise stable zero-based source-row position is used, tied to the input hash. Full row-level diagnostic parquet files, including invalid rows and `valid_m10` flags, are local/ignored under `data/processed/passenger_sensitivity_m10_review/`. They contain PRIVATE epsilon and are never passed to a pricing or routing model.
''']
    parts.append('Historical input audit:\n\n'+markdown_table(pd.DataFrame([summary['input_population']])) )
    parts.append('## 4. Exact filter funnels\n\nPercent_previous is conditional on the previous stage; percent_raw always divides by historical rows. The final row repeats the positive-finite stage to identify the output population. No trims are applied. Missing condition/base exclusions are separate from invalid fare/distance.\n')
    for v,d in variants.items():parts.append(f'### {v}\n\n'+markdown_table(d['funnel']))
    parts.append('## 5. Time grouping support\n\nPossible conditions = 48 or 24 buckets × distinct codes present in **historical weather only**. It is not a claim of all possible meteorological codes. Observed conditions have N>0; missing means no support in that Cartesian product. N quantiles are over observed conditions; both observed-only and all-possible sparse counts are in the CSV. Base N and retained-epsilon N are separate populations. Sparse flags N<30, <100 and <500 are descriptive, overlapping thresholds, not pooling decisions.\n\n'+markdown_table(support,['variant','population','possible_conditions','observed_conditions','missing_conditions','observed_n_min','observed_n_p25','observed_n_median','observed_n_p75','observed_n_max','observed_groups_n_lt_30','observed_groups_n_lt_100','observed_groups_n_lt_500','observed_groups_n_ge_500']))
    parts.append('## 6. Raw epsilon distribution\n\n'+markdown_table(overall)+'\n\nPercentiles use NumPy linear interpolation; std is population ddof=0; skewness is SciPy bias-corrected sample skewness. `log1p(epsilon)` is visualization only: no values are transformed for M10/M12 or any frozen sampling configuration. Overall summaries are row-weighted, not averages of condition means.')
    parts.append('## 7. Small positive delta_P\n\n'+markdown_table(small,['variant','bin','count','mean','median','p90','p95','p99','max'])+'\n\nBins are disjoint and exhaustive. The formula mechanically amplifies relative-distance deviations when price deviations approach zero. Large epsilon at small delta_P is therefore a denominator effect, not independent evidence of a passenger behavioral law. Values below one cent are deviations from a group mean: source cent-denominated fares do not imply delta_P is cent-quantized. No minimum delta_P, epsilon cap or winsorization has been added.')
    parts.append('**Observed stability finding:** the very smallest positive delta_P bin is unstable, but it does not contain the overall maximum in either grouping. Both maxima lie in the [.10,.25) USD bin. Source-distance extremes also drive the tail: the historical input includes a maximum positive distance of '+f"{summary['input_population']['historical_max_positive_distance_miles']:,.2f}"+' miles. Treat such source values as data-quality issues for review, not plausible NYC trip lengths. A denominator floor alone would not address them.')
    for v in variants:
        audit=summary['variants'][v+'_source_distance_audit']
        parts.append(f"{v}: {audit['valid_epsilon_rows_above_100_miles']} retained rows above the legacy 100-mile reference contribute {100*audit['epsilon_sum_share_above_100_miles']:.2f}% of the sum of epsilon. This is an attribution diagnostic, not an applied exclusion; removing input rows would also change condition bases.")
    parts.append('## 8. Time × Weather findings\n\n'+markdown_table(weather_summary,['variant','WeatherCode','count','mean','median','p99','max'])+'\n\nThese are descriptive associations with historical fare-distance deviations, not causal weather or price-demand elasticity estimates. Hourly groups recompute both means and epsilon from their own members; they do not average half-hour epsilon statistics. Changing grouping can change retention, denominator closeness and tail magnitude, not merely reduce noise. The support heatmap retains missing cells; codes are never merged. Hourly WeatherCode 21 has zero retained M10 observations despite historical weather/base support; it is explicitly shown as N=0 rather than silently dropped.\n')
    for v,d in variants.items():
        top=d['conditions'].sort_values('mean_epsilon',ascending=False).head(5)
        parts.append(f'Largest condition means ({v}; inspect N before interpretation):\n\n'+markdown_table(top,['condition_id','base_sample_count','sample_count','mean_epsilon','std_epsilon','median','p99','maximum']))
    parts.append('## 9. Outlier-rule comparison - PROFESSOR DECISION REQUIRED\n\n'+markdown_table(outlier,['variant','rule','upper_inclusive','count','percent_retained','mean','std_population','median','p90','p95','p99','max'])+'\n\nEvery candidate starts from the same valid raw epsilon population. Upper trimming retains epsilon <= its pooled percentile. IQR = P75−P25; its upper fence is P75+1.5 IQR. The optional log-space diagnostic applies that fence to log1p(epsilon) and maps the bound back with expm1. Rules are global pooled **diagnostic comparisons**, not selected condition-specific production rules. Bases are held fixed during these epsilon-trimming comparisons; source-row cleaning would be a separate decision. No winner is selected and no runtime config is written.')
    parts.append('## 10. Candidate distributions - PROFESSOR DECISION REQUIRED\n\n'+markdown_table(sampling,['variant','candidate','mean','std_population','median','p90','p95','p99','probability_nonpositive','descriptive_cdf_max_gap'])+'\n\nEmpirical sampling describes the observed valid values with equal row probability. The Normal diagnostic uses empirical mean/population SD and can allocate invalid nonpositive probability. Positive-truncated Normal uses those same **underlying Normal parameters** and truncates at zero; its realized mean/SD differ and may be severely inflated by a heavy empirical tail. Lognormal uses the mean and population SD of log(epsilon), location fixed at zero, and ensures positive support. These pooled families are visual/descriptive candidates, not condition-level frozen sampling distributions.\n\nThe CDF gap is the maximum distance between candidate CDF and both sides of the exact empirical CDF steps. Parameters are estimated on the same descriptive sample; this is not a formal calibrated goodness-of-fit test or cross-validated ranking. No p-values, new dependencies or selected family are introduced. Inspect quantiles, central mass, tails and conditional variation together.')
    for v in variants:
        z=sampling.loc[sampling.variant==v].set_index('candidate')
        parts.append(f"{v}: untruncated Normal assigns {100*z.loc['Normal','probability_nonpositive']:.2f}% nonpositive mass. Truncation using those tail-inflated parameters moves the mean to {z.loc['positive_truncated_Normal','mean']:.4g}, versus empirical median {z.loc['empirical','median']:.5g}. Lognormal has a smaller descriptive CDF gap ({z.loc['lognormal','descriptive_cdf_max_gap']:.4g}) in this pooled comparison but does not reproduce the extreme tail or resolve conditional/source-quality problems. This observation does not select a family.")
    parts.append('## 11. M12 acceptance sanity - ILLUSTRATIVE, NOT PRODUCTION INTEGRATION\n\nPDF p.16 states `P_max = P_base + relative_distance / epsilon` and accepts when `factor * P_base <= P_max`. The extra P_base multiplier in current production is absent. `P_max−P_base` is in USD because epsilon is 1/USD. Historical inversion gives exactly delta_P for a retained trip with its own epsilon; this algebraic identity does not empirically validate willingness to pay.\n\nScenarios use pooled P10/P25/P50/P75/P90/P95 epsilon, distance deviations +5%, +10%, +25%, +50%, +100%, and all seven existing factors .85–1.15. A representative base is the median historical condition P_base across retained rows in each variant; the CSV states it explicitly. The tolerance itself is independent of that representative base; comparison with multiplier premiums is not.\n')
    for v in variants:
        z=sanity.loc[(sanity.variant==v)&(sanity.price_factor==1.)]
        parts.append(f'{v} tolerance above base, USD:\n\n'+markdown_table(z.pivot(index='epsilon_percentile',columns='relative_distance',values='tolerance').reindex(['P10','P25','P50','P75','P90','P95']).reset_index()))
    parts.append('For these positive-distance cases, factors <=1 always pass; larger epsilon lowers the permissible premium, while smaller epsilon can yield a very large premium. Zero relative distance gives P_max=P_base. Negative deviations (not part of the requested positive scenario grid) lower P_max and can make it nonpositive at small epsilon. The retained historical M10 sample contains only positive distance/price deviations; it cannot by itself validate acceptance for shorter trips. No Bernoulli draw, runtime distribution selection, dispatch, or simulation is performed.\n\n## 12. Privacy and API separation\n\n`src/analysis/passenger_sensitivity_m10.py` is never imported by production. Full private diagnostics remain in ignored local parquet; CSVs expose condition/population aggregates and illustrative quantiles, not identifiable per-trip epsilon. `illustrative_private_pmax` is the only new consumer using an individual sensitivity as an acceptance input. `public_aggregate_state` takes only explicit public fields J_hat, J_disp_prev, I, p, pi and rejects an epsilon keyword; it is an analysis schema, **not** a new DQN. Tests inspect existing pricing and routing state definitions for epsilon exposure. Existing request/customer audit epsilon is private research data, not a public state input. This is interface separation, not encryption, differential privacy, or a proof about a future unimplemented DQN.\n\n## 13. Production unchanged and reproduction\n\nNo production pricing, sampler, dispatch, routing, configuration or legacy sensitivity artifact was changed. No 2/8/48/298-slot production run was invoked. Unit tests include their existing small fixture-based orchestration checks; those are not production experiments.\n\nRun the standalone analysis with:\n\n```bash\npython scripts/analyze_passenger_sensitivity_m10.py\npython -m unittest discover -s tests -p test_passenger_sensitivity_m10.py -v\npython -m unittest discover -s tests -q\n```\n\nThe script reads only historical rows for computations; it hashes full source files solely for identity. Metadata contains input/source hashes, Python library versions, deterministic output hashes, population semantics and open decisions. Chart PDFs have volatile creation/modification timestamps removed. Small-fixture byte reproducibility is tested; full tables/figures are checked with a second standalone analysis pass. This does not rerun a simulator.\n')
    parts.append('## 14. Output guide\n\n- `current_vs_new_m10.csv`: 15 compatibility decisions.\n- `filter_funnel_*.csv`: exact sequential filters.\n- `base_conditions_*.csv`: M9 means/counts and sparse flags.\n- `sensitivity_conditions_*.csv`: retained epsilon statistics, including zero-output base conditions.\n- `overall_sensitivity_summary.csv`: raw and log1p summaries.\n- `time_grouping_comparison.csv`: base and epsilon support, possible/observed/missing cells.\n- `small_delta_p_diagnostic.csv`: disjoint denominator bins.\n- `outlier_rule_comparison.csv`: alternative trims, no selected rule.\n- `sampling_distribution_diagnostic.csv`: pooled descriptive candidates, no selected sampler.\n- `weather_sensitivity_summary.csv`: observed WeatherCode summaries.\n- `m12_acceptance_sanity.csv`: illustrative private-acceptance scenarios.\n- `summary.json`, `artifact_manifest.json`: assumptions, source identity, totals and output hashes.\n- `verification.json`: execution results and preservation checks from this task.\n- `charts/`: 15 requested chart topics plus additional condition mean/SD heatmaps; PNG and PDF per chart.\n\nPlots use log axes where needed, with units and tail-display omissions labeled. Scatter-density hexagons use all valid observations, not an undisclosed sample. Missing condition cells stay grey/gapped. Charts summarize historical association, not final runtime model behavior.\n')
    parts.append('''## QUESTIONS FOR PROFESSOR

1. M9 does not define Time-of-Day width: should 30-minute Period or Hour be frozen, given the support and distribution differences?
2. Which outlier rule, if any, should be selected, and should its scope be pooled or condition-specific? The M10 formula itself is explicit and has been implemented without reinterpretation.
3. Should a positive minimum delta_P be imposed after reviewing the denominator-tail diagnostics? If so, specify the currency threshold and its scientific rationale.
4. Which conditional runtime sampling family should be approved: empirical, positive-truncated Normal, lognormal, or another specified family? If truncation is selected, how should its parameters be estimated?
5. What fallback, if any, should apply to sparse or absent Time × Weather conditions, and what support threshold defines sparse for that purpose?
6. Does the numerical willingness-to-pay behavior from the fixed M12 equation match the intended passenger model, especially very small epsilon and negative distance deviations?
7. Should the legacy 100-mile source-validity cap be retained as a documented M1 cleaning rule for this new analysis, or should positive finite inputs remain the review population? No replacement threshold has been invented.

The formula, positive-deviation filters, condition means, individual-epsilon privacy, and M12 equation are already specified in the PDF and are not posed as unresolved choices. Time grouping, source cleaning, outliers, denominator floor, sampling and fallback remain **PROFESSOR DECISION REQUIRED**. No runtime sampling configuration is frozen by this package.
''')
    (out/'README.md').write_text('\n\n'.join(parts).rstrip()+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=DEFAULT)
    parser.add_argument('--skip-private-parquet',action='store_true',help='Keep private row diagnostics in memory only.')
    args=parser.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=True)
    if not SOURCE_DOC.is_file():raise FileNotFoundError(SOURCE_DOC)
    sources={'authoritative_pdf':SOURCE_DOC,'trips':ROOT/'data/processed/cleaned_trips.parquet',
             'weather':ROOT/'data/processed/weather/nyc_weather_processed_2026_01.parquet',
             'legacy_sensitivity':ROOT/'data/processed/customer_price_sensitivity_2026_01.parquet',
             'legacy_fallback':ROOT/'data/processed/customer_price_sensitivity_fallback_2026_01.parquet',
             'analysis_module':ROOT/'src/analysis/passenger_sensitivity_m10.py',
             'analysis_script':Path(__file__),
             'legacy_module':ROOT/'src/pricing/historical_sensitivity.py',
             'legacy_sampler':ROOT/'src/pricing/customer_sensitivity.py'}
    hashes={k:dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for k,p in sources.items()}
    import pyarrow.parquet as pq
    columns=['tpep_pickup_datetime','trip_distance','fare_amount']
    if 'trip_id' in pq.read_schema(sources['trips']).names: columns.append('trip_id')
    trips=pd.read_parquet(sources['trips'],columns=columns)
    weather=pd.read_parquet(sources['weather'])
    pickup=pd.to_datetime(trips.tpep_pickup_datetime,errors='coerce');historical=pickup.ge(START)&pickup.lt(CUTOFF)
    positive=np.isfinite(trips.trip_distance)&trips.trip_distance.gt(0)&np.isfinite(trips.fare_amount)&trips.fare_amount.gt(0)
    summary={'status':'READY_FOR_PROFESSOR_REVIEW','production_changed':False,'formula_frozen_in_pdf':True,'runtime_model_frozen':False,
             'training_start_inclusive':START.isoformat(),'training_cutoff_exclusive':CUTOFF.isoformat(),
             'input_population':dict(source_rows=len(trips),invalid_pickup_timestamps=int(pickup.isna().sum()),
                                     historical_rows=int(historical.sum()),outside_history=int((pickup.notna()&~historical).sum()),
                                     historical_positive_finite=int((historical&positive).sum()),
                                     historical_positive_finite_above_100_miles=int((historical&positive&trips.trip_distance.gt(100)).sum())),
             'source_hashes':hashes,'distance_unit':'miles','fare_unit':'USD','epsilon_unit':'1/USD',
             'input_rule':'finite positive fare and distance; no legacy 100-mile cap or .01-mile deviation threshold',
             'condition_universe':'all time buckets x codes observed in pre-cutoff hourly weather, not all theoretical weather codes',
             'sampling_configuration':None,'fallback':None,'outlier_rule_selected':None,
             'open_decisions':['time grouping','source cleaning cap','outlier treatment','minimum delta_P','sampling family/parameters','sparse fallback'],
             'variants':{}}
    summary['input_population']['historical_max_positive_distance_miles']=float(trips.loc[historical&positive,'trip_distance'].max())
    variants={};all_overall=[];all_support=[];all_small=[];all_out=[];all_sampling=[];all_sanity=[];all_weather=[]
    for v in ['30min','hourly']:
        print(f'Computing {v} M9/M10',flush=True)
        result=compute_m10(trips,weather,v)
        obs=result.observations
        if obs.empty:raise RuntimeError(f'No retained epsilon for {v}')
        if not args.skip_private_parquet:
            private=ROOT/'data/processed/passenger_sensitivity_m10_review';private.mkdir(exist_ok=True)
            result.rows.to_parquet(private/f'private_rows_{v}.parquet',index=False)
        write_csv(result.bases,out/f'base_conditions_{v}.csv');write_csv(result.conditions,out/f'sensitivity_conditions_{v}.csv');write_csv(result.funnel,out/f'filter_funnel_{v}.csv')
        small=small_delta_p(obs);small.insert(0,'variant',v);all_small.append(small)
        support=time_support(result);all_support.append(support)
        for transform,x in [('raw',obs.epsilon),('log1p',np.log1p(obs.epsilon))]:all_overall.append(dict(variant=v,transform=transform,**distribution(x)))
        trims=outlier_comparison(obs.epsilon);trims.insert(0,'variant',v);all_out.append(trims)
        fits,_=candidate_distributions(obs.epsilon);fits.insert(0,'variant',v);all_sampling.append(fits)
        sanity=acceptance_sanity(obs);sanity.insert(0,'variant',v);all_sanity.append(sanity)
        for code in result.weather_codes:
            all_weather.append(dict(variant=v,WeatherCode=int(code),**distribution(obs.loc[obs.WeatherCode==code,'epsilon'])))
        summary['variants'][v+'_source_distance_audit']=dict(valid_epsilon_rows_above_100_miles=int(obs.L_i.gt(100).sum()), epsilon_sum_share_above_100_miles=float(obs.loc[obs.L_i.gt(100),'epsilon'].sum()/obs.epsilon.sum()))
        variants[v]=dict(obs=obs,bases=result.bases,conditions=result.conditions,funnel=result.funnel,codes=result.weather_codes,small=small)
        summary['variants'][v]=dict(raw_epsilon=distribution(obs.epsilon),base_conditions=len(result.bases),epsilon_conditions=int((result.conditions.sample_count>0).sum()),weather_codes=result.weather_codes)
        print(f'{v}: {len(obs):,} observations, mean={obs.epsilon.mean():.8g}, max={obs.epsilon.max():.8g}',flush=True)
        del result
    overall=pd.DataFrame(all_overall);support=pd.concat(all_support,ignore_index=True);small=pd.concat(all_small,ignore_index=True)
    outlier=pd.concat(all_out,ignore_index=True);sampling=pd.concat(all_sampling,ignore_index=True);sanity=pd.concat(all_sanity,ignore_index=True);weather_summary=pd.DataFrame(all_weather)
    tables={'current_vs_new_m10.csv':differences(),'overall_sensitivity_summary.csv':overall,'time_grouping_comparison.csv':support,
            'small_delta_p_diagnostic.csv':small,'outlier_rule_comparison.csv':outlier,'sampling_distribution_diagnostic.csv':sampling,
            'm12_acceptance_sanity.csv':sanity,'weather_sensitivity_summary.csv':weather_summary}
    for name,table in tables.items():write_csv(table,out/name)
    summary['charts']=charts(out,variants,outlier,sampling,sanity)
    import scipy
    summary['software']={'python':sys.version.split()[0],'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__,'matplotlib':matplotlib.__version__}
    summary['private_rows_persisted']=not args.skip_private_parquet
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True,allow_nan=False)+'\n')
    review_readme(out,summary,variants,overall,support,small,outlier,sampling,sanity,weather_summary)
    # No timestamp-dependent metadata. Verification report is managed separately.
    manifest={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name not in ['artifact_manifest.json','verification.json']}
    (out/'artifact_manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    print(f'Completed standalone analysis: {out}',flush=True)


if __name__=='__main__':main()
