"""Provisional master §3 estimator; does not authorize a runtime sampler."""
import numpy as np
import pandas as pd

VERSION = 'MASTER_BINNED_SENSITIVITY_ESTIMATOR_V1'


def binned_elasticity(frame, *, p_base, l_base, group_columns=()):
    """500m left-closed bins; km lower limit and bin mean USD fare.

    One output row per observed bin. Counts are retained, not implicitly used as
    distribution weights. Exact zero price deviation is explicitly undefined;
    no near-zero threshold, magnitude transform or clipping is applied here.
    """
    if not np.isfinite([p_base,l_base]).all() or p_base<=0 or l_base<=0:
        raise ValueError('Positive finite common references required')
    x=frame[list(group_columns)+['distance_km','fare']].copy()
    values=x[['distance_km','fare']].to_numpy(float)
    if not np.isfinite(values).all() or (values<0).any():raise ValueError('Invalid empirical observations')
    if group_columns and x[list(group_columns)].isna().any().any():raise ValueError('Missing conditioning values')
    x['bin_lower_km']=np.floor(x.distance_km/.5)*.5
    keys=list(group_columns)+['bin_lower_km']
    out=x.groupby(keys,sort=True,observed=True).agg(n_requests=('fare','size'),mean_fare=('fare','mean')).reset_index()
    out['bin_upper_km']=out.bin_lower_km+.5
    out['P_base']=float(p_base);out['L_base_km']=float(l_base)
    out['relative_distance_deviation']=(out.bin_lower_km-l_base)/l_base
    out['relative_price_deviation']=(out.mean_fare-p_base)/p_base
    out['epsilon']=np.divide(out.relative_distance_deviation,out.relative_price_deviation,
        out=np.full(len(out),np.nan),where=out.relative_price_deviation.to_numpy()!=0)
    out['status']=np.select([out.relative_price_deviation==0,~np.isfinite(out.epsilon),out.epsilon==0,out.epsilon<0],
        ['UNDEFINED_EXACT_ZERO_PRICE_DENOMINATOR','NONFINITE_RATIO','ZERO_ELASTICITY','NEGATIVE_ELASTICITY'],default='POSITIVE_ELASTICITY')
    return out


def require_runtime_approved(contract):
    """Fail closed until conditioning, support and fitted calibration are approved."""
    if contract.get('version')!=VERSION or contract.get('runtime_approved') is not True:
        raise ValueError('Binned sensitivity is provisional; runtime selection prohibited')
    # No approved serializer/sampler exists for this provisional schema.
    raise ValueError('No validated runtime sampler for this estimator-only schema')


def historical_pool(frame, condition, mapping):
    """Reuse existing pool definitions, not only requests routed to a fallback."""
    if condition=='GLOBAL':return frame
    if condition.startswith('RAW_'):
        return frame.loc[frame.weather_code==int(condition[4:])]
    if condition in {'T1_POOLED','T2_POOLED','T3_POOLED','T4_POOLED'}:
        return frame.loc[frame.T_group==condition[:2]]
    keys=[(code,T) for (code,T),sid in mapping.items() if sid==condition]
    if not keys:raise ValueError('Unknown historical condition')
    mask=np.zeros(len(frame),dtype=bool)
    for code,T in keys:mask|=(frame.weather_code.to_numpy()==code)&(frame.T_group.to_numpy()==T)
    return frame.loc[mask]
