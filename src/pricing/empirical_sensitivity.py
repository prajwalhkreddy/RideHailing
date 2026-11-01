"""Frozen absolute distance/price empirical passenger contract (2026-10-29)."""
from __future__ import annotations
import numpy as np
import pandas as pd
from .customer_sensitivity import (SensitivityParameters, ResolvedSensitivityParameters,
    HistoricalCustomerDecision, dispatch_price, maximum_price)


def absolute_epsilon(price, distance, p_base, d_base):
    """Return full ratio array and mutually exclusive sampling exclusions."""
    dp=(np.asarray(price,dtype=float)-p_base)/p_base
    dd=(np.asarray(distance,dtype=float)-d_base)/d_base
    zero=dp==0
    with np.errstate(divide='ignore',invalid='ignore',over='ignore'):
        values=np.abs(dd/dp)
    valid=(~zero)&np.isfinite(values)&(values>0)
    counts=dict(source_N=len(values),exact_zero_delta_P=int(zero.sum()),
        nonfinite=int(((~zero)&~np.isfinite(values)).sum()),
        nonpositive=int(((~zero)&np.isfinite(values)&(values<=0)).sum()),retained_N=int(valid.sum()))
    return values,valid,counts


class EmpiricalCustomerSensitivityModel:
    """Persistent caller RNG; uniform row sampling preserves duplicate frequency.

    Bases are recomputed within each broader fallback population, matching the
    existing hierarchy's reference semantics. No distance-resolution exclusion.
    """
    def __init__(self, observations, rng):
        if not isinstance(rng,np.random.Generator):raise ValueError('Explicit numpy Generator required.')
        self.rng=rng;self.pools={};self.parameters={};self.exclusions={}
        required=['WeatherCode','Period','fare_amount','trip_distance']
        x=observations[required+[c for c in ['P_base','D_base'] if c in observations.columns]]
        if x.empty or not np.isfinite(x.to_numpy(dtype=float)).all():raise ValueError('Finite source-valid observations required.')
        if (x.fare_amount<=0).any() or ((x.trip_distance<=0)|(x.trip_distance>100)).any():raise ValueError('Invalid historical fare/distance.')
        if not (x.Period.between(0,47)&(x.Period%1==0)).all():raise ValueError('Invalid Period.')
        for level,keys in [('exact',['WeatherCode','Period']),('period',['Period']),('weather',['WeatherCode']),('global',[])]:
            groups=x.groupby(keys,sort=True,observed=True) if keys else [((),x)]
            for key,g in groups:
                key=key if isinstance(key,tuple) else (key,)
                weather=float(key[0]) if level in ('exact','weather') else -1.
                period=int(key[-1]) if level in ('exact','period') else -1
                context=(level,weather,period)
                pb=float(g.fare_amount.mean());db=float(g.trip_distance.mean())
                if level=='exact' and {'P_base','D_base'}.issubset(g.columns):
                    if g.P_base.nunique()!=1 or g.D_base.nunique()!=1:raise ValueError('Conflicting exact references.')
                    if not np.isclose(pb,g.P_base.iloc[0],rtol=1e-13) or not np.isclose(db,g.D_base.iloc[0],rtol=1e-13):raise ValueError('Exact references disagree with source.')
                    pb=float(g.P_base.iloc[0]);db=float(g.D_base.iloc[0])
                vals,valid,counts=absolute_epsilon(g.fare_amount,g.trip_distance,pb,db)
                self.exclusions[context]=counts
                if not valid.any():continue
                pool=vals[valid].copy();pool.setflags(write=False);self.pools[context]=pool
                self.parameters[context]=SensitivityParameters(weather,period,pb,db,float(pool.mean()),float(pool.std(ddof=0)))
        if not self.pools:raise ValueError('No valid empirical epsilon observations.')

    @classmethod
    def from_parquet(cls,path,rng):return cls(pd.read_parquet(path),rng)

    def resolve_parameters(self,weather_code,period):
        weather=float(weather_code)
        if not np.isfinite(weather) or isinstance(period,bool) or not isinstance(period,(int,np.integer)) or not 0<=period<48:
            raise ValueError('Finite weather and integer Period0..47 required.')
        for key in [('exact',weather,int(period)),('period',-1.,int(period)),('weather',weather,-1),('global',-1.,-1)]:
            if key in self.pools:return ResolvedSensitivityParameters(self.parameters[key],key[0],weather,int(period))
        raise ValueError(f'No valid empirical fallback for {(weather,period)}')

    def pool_for(self,resolved):
        p=resolved.parameters
        return self.pools[(resolved.fallback_level_used,p.weather_code,p.period)]

    def sample_epsilon(self,weather_code,period):
        pool=self.pool_for(self.resolve_parameters(weather_code,period))
        return float(pool[self.rng.integers(len(pool))])

    def evaluate(self,weather_code,period,actual_distance,alpha):
        return self.evaluate_resolved(self.resolve_parameters(weather_code,period),actual_distance,alpha)

    def evaluate_resolved(self,resolved,actual_distance,alpha):
        pool=self.pool_for(resolved);epsilon=float(pool[self.rng.integers(len(pool))]);p=resolved.parameters
        offered=dispatch_price(p.p_base,alpha)
        try:limit=maximum_price(p.p_base,p.d_base,actual_distance,epsilon)
        except ValueError as exc:
            raise ValueError(f'Empirical P_max failure: requested={(resolved.requested_weather_code,resolved.requested_period)}, level={resolved.fallback_level_used}, P_base={p.p_base}, D_base={p.d_base}, distance={actual_distance}, epsilon={epsilon}: {exc}') from exc
        return HistoricalCustomerDecision(resolved.requested_weather_code,resolved.requested_period,p.p_base,p.d_base,float(actual_distance),float(alpha),epsilon,offered,limit,offered<=limit,resolved.fallback_level_used)
