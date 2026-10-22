"""Canonical final-routing configuration and guarded historical priors."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
CONTRACT=ROOT/'results/analysis/2026-10-20_final_routing_configuration/routing_configuration.json'


def require_production_configuration(path=CONTRACT):
    data=json.loads(Path(path).read_text())
    missing=[k for k,v in data.items() if isinstance(v,dict) and v.get('required',False) and (v.get('value') is None or v.get('status')=='PROJECT_CONFIG_DECISION_REQUIRED')]
    if missing:raise ValueError('PROJECT_CONFIG_DECISION_REQUIRED: '+', '.join(missing))
    if data['policy_input_dim']['value']!=169 or data['policy_output_dim']['value']!=9:
        raise ValueError('Final architecture must be 169-input/9-output.')
    for name in ('alpha','beta','delta','kappa'):
        value=data[name]['value']
        if not isinstance(value,(int,float)) or not np.isfinite(value) or not 0<value<=1:
            raise ValueError(f'Invalid smoothing coefficient: {name}')
    for name in ('sigma_safeguard','H_hat_safeguard'):
        value=data[name]['value']
        if not isinstance(value,(int,float)) or not np.isfinite(value) or value<=0:
            raise ValueError(f'Invalid safeguard: {name}')
    return data


def configured_interfaces(grid_lookup, neighbours, stations, first_timestamp):
    """Wire the single final contract; missing production choices block startup."""
    from src.simulation.operational_state import OperationalGridState, SmoothingParameters
    from src.routing.operational_interface import OperationalRouting, UtilityConfig
    data=require_production_configuration()
    value=lambda key:data[key]['value']
    priors,cutoff=historical_priors(first_timestamp,
        F_hat_0=value('F_hat_initialization'),H_hat_0=value('H_hat_initialization'))
    producer=OperationalGridState(grid_lookup,priors,first_timestamp=first_timestamp,
        prior_as_of=cutoff,parameters=SmoothingParameters(
            value('alpha'),value('beta'),value('delta'),value('kappa'),value('sigma_safeguard')))
    routing=OperationalRouting(neighbours,stations,UtilityConfig(
        value('sigma_safeguard'),value('H_hat_safeguard'),value('reposition_cost_coefficient')/(3*np.sqrt(2))))
    return producer,routing


def historical_priors(first_timestamp, *, F_hat_0, H_hat_0):
    """Use verified training fare priors only after their exclusive cutoff.

    F/H priors must be explicitly supplied; never estimated from held-out data.
    """
    import hashlib
    cutoff=pd.Timestamp('2026-01-25 18:30:00')
    if pd.Timestamp(first_timestamp)<=cutoff:
        raise ValueError('Historical fare prior cutoff must precede first decision.')
    base=ROOT/'data/processed/spatial_3km_jan_mar_2026'
    source=base/'fare_bootstrap_legacy_cutoff.parquet'
    meta=json.loads((base/'fare_bootstrap_legacy_cutoff.metadata.json').read_text())
    if hashlib.sha256(source.read_bytes()).hexdigest()!=meta['sha256']:
        raise ValueError('Historical prior fingerprint changed; review provenance.')
    for name,value in [('F_hat_0',F_hat_0),('H_hat_0',H_hat_0)]:
        if value is None or not np.isfinite(value) or value<0:
            raise ValueError('PROJECT_CONFIG_DECISION_REQUIRED: '+name)
    p=pd.read_parquet(source).rename(columns={'grid_id':'Grid_ID','mean_fare':'mu','std_fare':'sigma'})
    if len(p)!=142 or set(p.Grid_ID)!=set(range(142)) or p.Grid_ID.duplicated().any():raise ValueError('Invalid prior grid domain.')
    p=p[['Grid_ID','mu','sigma']].copy();p['F_hat']=float(F_hat_0);p['H_hat']=float(H_hat_0)
    if not np.isfinite(p.to_numpy()).all() or (p[['mu','sigma']]<0).any().any():raise ValueError('Invalid priors.')
    return p,cutoff
