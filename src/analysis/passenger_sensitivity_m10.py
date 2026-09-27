"""Unfrozen M9/M10 analysis from module document pp.13-16 (2026-09-27).

Private trip diagnostics remain local. No production imports, runtime sampler,
DQN, outlier selection, sparse pooling, or simulation integration is provided.
Distance is source miles; fare is USD; epsilon has units 1/USD.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd
from scipy import stats

START = pd.Timestamp('2026-01-01 00:00')
CUTOFF = pd.Timestamp('2026-01-25 18:30')
VARIANTS = {'30min': 48, 'hourly': 24}
QUANTILES = {'p01': .01, 'p05': .05, 'p10': .10, 'p25': .25,
             'median': .50, 'p75': .75, 'p90': .90, 'p95': .95,
             'p99': .99, 'p995': .995, 'p999': .999}
PUBLIC_STATE_FIELDS = ('J_hat', 'J_disp_prev', 'I', 'p', 'pi')


@dataclass
class M10Analysis:
    variant: str
    bases: pd.DataFrame
    rows: pd.DataFrame  # PRIVATE: all historical rows, including exclusion flags.
    conditions: pd.DataFrame
    funnel: pd.DataFrame
    weather_codes: tuple[int, ...]

    @property
    def observations(self) -> pd.DataFrame:
        return self.rows.loc[self.rows.valid_m10].copy()


def distribution(values: Sequence[float]) -> dict:
    """Describe the supplied finite sample without dropping or trimming values."""
    x = np.asarray(values, dtype=np.float64)
    if x.ndim != 1 or not np.isfinite(x).all():
        raise ValueError('Distribution input must be one-dimensional and finite.')
    result = {'count': int(x.size), 'mean': np.nan, 'std_population': np.nan,
              'min': np.nan, **{k: np.nan for k in QUANTILES}, 'max': np.nan,
              'skewness': np.nan}
    if x.size:
        result.update(mean=float(x.mean()), std_population=float(x.std(ddof=0)),
                      min=float(x.min()), max=float(x.max()))
        result.update(zip(QUANTILES, np.quantile(x, list(QUANTILES.values())).tolist()))
        if x.size > 2 and np.ptp(x) > 0:
            result['skewness'] = float(stats.skew(x, bias=False))
    return result


def compute_m10(trips: pd.DataFrame, weather: pd.DataFrame, variant: str) -> M10Analysis:
    """Fit bases and epsilon strictly on frozen historical rows.

    No upper distance limit or minimum positive delta-P is imposed. The prior
    method's 100-mile cap / .01-mile deviation rule are not M10 requirements.
    Weather is the existing timezone-naive NYC hourly WeatherCode lookup.
    """
    if variant not in VARIANTS:
        raise ValueError('variant must be 30min or hourly')
    required = {'tpep_pickup_datetime', 'trip_distance', 'fare_amount'}
    if not required.issubset(trips):
        raise ValueError(f'Missing trip fields: {required - set(trips)}')
    if not {'Datetime', 'WeatherCode'}.issubset(weather):
        raise ValueError('Weather requires Datetime and WeatherCode.')
    timestamp = pd.to_datetime(trips.tpep_pickup_datetime, errors='coerce')
    if timestamp.dt.tz is not None:
        raise ValueError('Frozen historical timestamps must be timezone-naive.')
    in_history = timestamp.ge(START) & timestamp.lt(CUTOFF)
    selected = trips.loc[in_history]
    ids = (selected.trip_id.to_numpy() if 'trip_id' in selected
           else np.flatnonzero(in_history.to_numpy()))
    if pd.isna(ids).any() or pd.Index(ids).has_duplicates:
        raise ValueError('Historical trip identifiers must be unique and nonmissing.')
    rows = pd.DataFrame({'trip_id': ids, 'pickup_timestamp': timestamp.loc[in_history].to_numpy(),
                         'L_i': pd.to_numeric(selected.trip_distance, errors='coerce').to_numpy(),
                         'P_i': pd.to_numeric(selected.fare_amount, errors='coerce').to_numpy()})
    if rows.empty:
        raise ValueError('No rows within frozen historical window.')
    w = weather[['Datetime', 'WeatherCode']].copy()
    w['Datetime'] = pd.to_datetime(w.Datetime, errors='coerce')
    if w.Datetime.dt.tz is not None:
        raise ValueError('Weather timestamps must be timezone-naive.')
    # Remove future weather before validating/grouping; it cannot affect diagnostics.
    w = w.loc[w.Datetime.ge(START.floor('h')) & w.Datetime.lt(CUTOFF)].copy()
    if w.Datetime.duplicated().any() or not w.Datetime.eq(w.Datetime.dt.floor('h')).all():
        raise ValueError('Historical weather must have unique hourly timestamps.')
    w['WeatherCode'] = pd.to_numeric(w.WeatherCode, errors='coerce')
    valid_w = np.isfinite(w.WeatherCode) & w.WeatherCode.gt(0) & w.WeatherCode.mod(1).eq(0)
    w.loc[~valid_w, 'WeatherCode'] = np.nan
    codes = tuple(sorted(w.WeatherCode.dropna().astype(int).unique().tolist()))
    rows['weather_hour'] = rows.pickup_timestamp.dt.floor('h')
    rows = rows.merge(w, left_on='weather_hour', right_on='Datetime', how='left', validate='many_to_one')
    rows = rows.drop(columns=['weather_hour', 'Datetime'])
    rows['time_bucket'] = rows.pickup_timestamp.dt.hour
    if variant == '30min':
        rows['time_bucket'] = 2 * rows.time_bucket + rows.pickup_timestamp.dt.minute // 30
    rows['condition_id'] = (variant + ':T' + rows.time_bucket.astype(str).str.zfill(2)
                            + ':W' + rows.WeatherCode.astype('Int64').astype(str))
    positive_inputs = np.isfinite(rows.L_i) & rows.L_i.gt(0) & np.isfinite(rows.P_i) & rows.P_i.gt(0)
    valid_context = rows.WeatherCode.notna()
    keys = ['condition_id', 'time_bucket', 'WeatherCode']
    bases = rows.loc[positive_inputs & valid_context].groupby(keys, sort=True, observed=True).agg(
        sample_count=('L_i', 'size'), L_base=('L_i', 'mean'), P_base=('P_i', 'mean')).reset_index()
    if bases.empty:
        raise ValueError('No usable historical condition bases.')
    rows = rows.merge(bases.drop(columns='sample_count'), on=keys, how='left', sort=False, validate='many_to_one')
    valid_base = positive_inputs.to_numpy() & np.isfinite(rows.L_base) & rows.L_base.gt(0) & np.isfinite(rows.P_base) & rows.P_base.gt(0)
    with np.errstate(divide='ignore', invalid='ignore', over='ignore', under='ignore'):
        rows['delta_L'] = rows.L_i - rows.L_base
        rows['delta_P'] = rows.P_i - rows.P_base
        rows['relative_delta_L'] = rows.delta_L / rows.L_base
        rows['epsilon'] = rows.relative_delta_L / rows.delta_P
    masks = [np.ones(len(rows), dtype=bool), positive_inputs.to_numpy(), np.asarray(valid_base)]
    masks += [masks[-1] & rows.delta_L.gt(0).to_numpy()]
    masks += [masks[-1] & rows.delta_P.gt(0).to_numpy()]
    masks += [masks[-1] & np.isfinite(rows.epsilon).to_numpy()]
    masks += [masks[-1] & rows.epsilon.gt(0).to_numpy()]
    masks += [masks[-1].copy()]
    names = ['raw_historical_rows', 'valid_positive_distance_fare', 'valid_condition_bases',
             'delta_L_positive', 'delta_P_positive', 'finite_epsilon', 'positive_epsilon', 'final_valid_m10']
    counts = [int(m.sum()) for m in masks]
    funnel = pd.DataFrame({'stage': names, 'count': counts})
    prev = np.asarray([counts[0], *counts[:-1]], dtype=float)
    funnel['percent_previous'] = np.divide(100*np.asarray(counts), prev, out=np.full(8,np.nan), where=prev!=0)
    funnel['percent_raw'] = 100 * funnel['count'] / counts[0]
    rows['valid_inputs'] = positive_inputs.to_numpy()
    rows['valid_condition_bases'] = np.asarray(valid_base)
    rows['valid_m10'] = masks[-1]
    grouped = rows.loc[rows.valid_m10].groupby(keys, sort=True, observed=True).epsilon
    metrics = grouped.agg(sample_count='size', mean_epsilon='mean', median='median', maximum='max')
    metrics['std_epsilon'] = grouped.std(ddof=0)
    for label,q in [('p25',.25),('p75',.75),('p90',.90),('p95',.95),('p99',.99)]:
        metrics[label] = grouped.quantile(q)
    # Include zero-output base conditions; missing combinations appear in support grids.
    conditions = bases[keys + ['sample_count']].rename(columns={'sample_count':'base_sample_count'}).merge(
        metrics.reset_index(), on=keys, how='left', validate='one_to_one')
    conditions['sample_count'] = conditions.sample_count.fillna(0).astype(int)
    for n in (30,100,500):
        conditions[f'n_lt_{n}'] = conditions.sample_count < n
        bases[f'n_lt_{n}'] = bases.sample_count < n
    return M10Analysis(variant, bases, rows, conditions, funnel, codes)


def time_support(result: M10Analysis) -> pd.DataFrame:
    """Possible = all time buckets x weather codes seen in historical weather only."""
    possible = VARIANTS[result.variant] * len(result.weather_codes)
    records = []
    for population, table in [('base', result.bases), ('epsilon', result.conditions)]:
        observed = table.loc[table.sample_count > 0, 'sample_count'].to_numpy()
        all_counts = np.r_[observed, np.zeros(possible-len(observed),dtype=int)]
        record = dict(variant=result.variant, population=population, possible_conditions=possible,
                      observed_conditions=len(observed), missing_conditions=possible-len(observed),
                      historical_weather_codes=len(result.weather_codes))
        for label,q in [('min',0),('p25',.25),('median',.5),('p75',.75),('max',1)]:
            record[f'observed_n_{label}'] = float(np.quantile(observed,q)) if len(observed) else np.nan
        for n in (30,100,500):
            record[f'observed_groups_n_lt_{n}'] = int((observed<n).sum())
            record[f'all_possible_groups_n_lt_{n}'] = int((all_counts<n).sum())
        record['observed_groups_n_ge_500'] = int((observed>=500).sum())
        records.append(record)
    return pd.DataFrame(records)


def small_delta_p(observations: pd.DataFrame) -> pd.DataFrame:
    edges=[0,.01,.05,.1,.25,.5,np.inf]
    out=[]
    for lo,hi in zip(edges[:-1],edges[1:]):
        m=observations.delta_P.ge(lo)&observations.delta_P.lt(hi)&observations.delta_P.gt(0)
        out.append({'delta_p_low_inclusive':lo,'delta_p_high_exclusive':hi,
                    'bin':f'{lo:g} <= delta_P < {hi:g} (positive)', **distribution(observations.loc[m,'epsilon'])})
    return pd.DataFrame(out)


def outlier_comparison(values: Sequence[float]) -> pd.DataFrame:
    x=np.asarray(values,dtype=float)
    if not len(x): return pd.DataFrame()
    q25,q75=np.quantile(x,[.25,.75])
    rules=[('none',np.inf),('upper_P99',np.quantile(x,.99)),('upper_P99.5',np.quantile(x,.995)),
           ('upper_P99.9',np.quantile(x,.999)),('IQR_Q3_plus_1.5IQR',q75+1.5*(q75-q25))]
    log=np.log1p(x); lq1,lq3=np.quantile(log,[.25,.75])
    rules.append(('log1p_IQR_diagnostic',np.expm1(lq3+1.5*(lq3-lq1))))
    return pd.DataFrame([dict(rule=name, upper_inclusive=limit,
                             percent_retained=100*int((x<=limit).sum())/len(x),
                             decision='PROFESSOR DECISION REQUIRED',
                             **distribution(x[x<=limit])) for name,limit in rules])


def candidate_distributions(values: Sequence[float]):
    """Descriptive candidates, not fitted production sampling configuration.

    Normal/truncated Normal use raw empirical mean/population SD as underlying
    parameters. Truncation changes realized moments. Lognormal fits mean/SD of
    log(epsilon) with location fixed to zero; no fitted outlier removal.
    """
    x=np.asarray(values,dtype=float)
    if not len(x) or not np.isfinite(x).all() or (x<=0).any():
        raise ValueError('Candidates require finite positive epsilon.')
    mu,sigma=x.mean(),x.std(ddof=0)
    if sigma<=0:
        return pd.DataFrame([dict(candidate='empirical_constant', **distribution(x))]), {}
    lm,ls=np.log(x).mean(),np.log(x).std(ddof=0)
    candidates={'Normal':stats.norm(loc=mu,scale=sigma),
                'positive_truncated_Normal':stats.truncnorm(-mu/sigma,np.inf,loc=mu,scale=sigma),
                'lognormal':stats.lognorm(s=ls,loc=0,scale=np.exp(lm))}
    empirical=distribution(x)
    rows=[dict(candidate='empirical',mean=mu,std_population=sigma,median=empirical['median'],
               p90=empirical['p90'],p95=empirical['p95'],p99=empirical['p99'],
               probability_nonpositive=0,descriptive_cdf_max_gap=0)]
    # Exact deterministic empirical CDF gap; descriptive only, no iid-test p-value.
    ordered=np.sort(x); lower=np.arange(len(x))/len(x); upper=(np.arange(len(x))+1)/len(x)
    for name,dist in candidates.items():
        cdf=dist.cdf(ordered)
        gap=float(max(np.max(np.abs(cdf-lower)),np.max(np.abs(cdf-upper))))
        rows.append(dict(candidate=name,mean=float(dist.mean()),std_population=float(dist.std()),
                         median=float(dist.ppf(.5)),p90=float(dist.ppf(.9)),p95=float(dist.ppf(.95)),
                         p99=float(dist.ppf(.99)),probability_nonpositive=float(dist.cdf(0)),
                         descriptive_cdf_max_gap=gap))
    table=pd.DataFrame(rows)
    table['underlying_normal_mean']=mu; table['underlying_normal_std']=sigma
    table['lognormal_log_mean']=lm; table['lognormal_log_std']=ls
    table['decision']='PROFESSOR DECISION REQUIRED'
    return table,candidates


def illustrative_private_pmax(p_base: float, relative_distance: float, private_epsilon: float) -> float:
    """PDF M12 p.16, analysis only. Private epsilon never becomes public state."""
    if not np.isfinite([p_base,relative_distance,private_epsilon]).all() or p_base<=0 or private_epsilon<=0:
        raise ValueError('Finite inputs and positive base/epsilon required.')
    value=p_base+relative_distance/private_epsilon
    if not np.isfinite(value): raise ValueError('Nonfinite Pmax')
    return float(value)


def public_aggregate_state(*, J_hat: float, J_disp_prev: float, I: float,
                           p: Sequence[float], pi: float) -> dict:
    """Analysis-only schema boundary for PDF M11, not a DQN implementation.

    Explicit keyword allowlist: no passenger records or private epsilon input.
    This documents/tests the intended interface, not a privacy/security proof.
    """
    routing=np.asarray(p,dtype=float)
    scalar=np.asarray([J_hat,J_disp_prev,I,pi],dtype=float)
    if (routing.ndim!=1 or not len(routing) or not np.isfinite(routing).all()
        or (routing<0).any() or not np.isclose(routing.sum(),1)
        or not np.isfinite(scalar).all() or (scalar<0).any() or pi>1):
        raise ValueError('Invalid public aggregate state')
    return dict(J_hat=float(J_hat),J_disp_prev=float(J_disp_prev),I=float(I),p=routing.tolist(),pi=float(pi))


def acceptance_sanity(observations: pd.DataFrame) -> pd.DataFrame:
    """Pooled percentile scenarios are illustrative, not condition sampling."""
    eps=np.quantile(observations.epsilon,[.1,.25,.5,.75,.9,.95])
    base=float(observations.P_base.median())
    rows=[]
    for label,e in zip(['P10','P25','P50','P75','P90','P95'],eps):
        for rel in [.05,.1,.25,.5,1.]:
            maximum=illustrative_private_pmax(base,rel,e)
            for factor in [.85,.90,.95,1.,1.05,1.10,1.15]:
                rows.append(dict(epsilon_percentile=label,epsilon=float(e),relative_distance=rel,
                                 P_base=base,price_factor=factor,P_dispatch=factor*base,
                                 tolerance=maximum-base,P_max=maximum,accepted=factor*base<=maximum,
                                 scope='ILLUSTRATIVE - NOT PRODUCTION INTEGRATION'))
    return pd.DataFrame(rows)


def write_csv(table: pd.DataFrame, path: Path) -> None:
    """Stable row order supplied by caller; full float roundtrip precision."""
    table.to_csv(path,index=False,float_format='%.17g',lineterminator='\n')
