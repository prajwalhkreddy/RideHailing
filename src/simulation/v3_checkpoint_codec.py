"""Explicit, allow-listed V3 value schema. No pickle or arbitrary imports."""
import base64
from enum import Enum
from pathlib import Path
import numpy as np
import pandas as pd
from src.fleet.state import VehicleState, VehicleStatus
from src.fleet.fleet import Fleet
from src.charging.energy import EnergyParameters
from src.charging.stations import ChargingStation, QueueEntry
from src.charging.timed import TimedChargingInfrastructure
from src.simulation.operational_state import OperationalGridState, SmoothingParameters
from src.routing.operational_interface import OperationalRouting, UtilityConfig
from src.pricing.dqn_contract import Snapshot, DispatchLedger, PassengerCommitment, PricingStateBuilder
from src.pricing.slot_v3 import FittedSensitivity, DropoffProbability
from src.dispatch.generation import EmpiricalODDistribution, EmpiricalTripRecord
from src.pricing.empirical_sensitivity import EmpiricalCustomerSensitivityModel

from src.pricing.customer_sensitivity import SensitivityParameters

CLASSES = {c.__name__: c for c in [VehicleState,VehicleStatus,Fleet,EnergyParameters,
    ChargingStation,QueueEntry,TimedChargingInfrastructure,OperationalGridState,
    SmoothingParameters,OperationalRouting,UtilityConfig,Snapshot,DispatchLedger,
    PassengerCommitment,PricingStateBuilder,FittedSensitivity,DropoffProbability,
    EmpiricalODDistribution,EmpiricalTripRecord,EmpiricalCustomerSensitivityModel,SensitivityParameters]}


def encode(x):
    if isinstance(x, Enum):return {'type':'enum','class':type(x).__name__,'value':x.value}
    if x is None or isinstance(x,(str,bool,int)):return x
    if isinstance(x,(float,np.floating)):
        return {'type':'float','hex':float(x).hex()}
    if isinstance(x,np.integer):return int(x)
    if isinstance(x,np.bool_):return bool(x)
    if isinstance(x,pd.Timestamp):return {'type':'timestamp','value':x.isoformat()}
    if isinstance(x,Path):return {'type':'path','value':str(x)}
    if isinstance(x,np.ndarray):
        if x.dtype.hasobject:raise ValueError('Object arrays require an explicit schema')
        return {'type':'array','dtype':x.dtype.str,'shape':list(x.shape),'bytes':base64.b64encode(x.tobytes()).decode()}
    if isinstance(x,np.random.Generator):return {'type':'rng','value':encode(x.bit_generator.state)}
    if isinstance(x,pd.DataFrame):
        return {'type':'frame','columns':encode(list(x.columns)),'index':encode(list(x.index)),
                'index_name':encode(x.index.name),'columns_name':encode(x.columns.name),
                'dtypes':[str(d) for d in x.dtypes],
                'data':[encode(x[c].tolist()) for c in x.columns]}
    if isinstance(x,dict):return {'type':'dict','items':[[encode(k),encode(v)] for k,v in x.items()]}
    if isinstance(x,(list,tuple,set,frozenset)):
        values=sorted(x) if isinstance(x,(set,frozenset)) else x
        return {'type':type(x).__name__,'items':[encode(v) for v in values]}
    if type(x).__name__ in CLASSES and type(x) is CLASSES[type(x).__name__]:
        return {'type':'object','class':type(x).__name__,'fields':encode(vars(x))}
    raise ValueError('Unsupported checkpoint type: '+str(type(x)))


def decode(x):
    if not isinstance(x,dict):return x
    t=x['type']
    if t=='float':return float.fromhex(x['hex'])
    if t=='timestamp':return pd.Timestamp(x['value'])
    if t=='path':return Path(x['value'])
    if t=='array':return np.frombuffer(base64.b64decode(x['bytes']),dtype=x['dtype']).reshape(x['shape']).copy()
    if t=='dict':return {decode(k):decode(v) for k,v in x['items']}
    if t in ('list','tuple','set','frozenset'):
        return {'list':list,'tuple':tuple,'set':set,'frozenset':frozenset}[t](decode(v) for v in x['items'])
    if t=='rng':
        s=decode(x['value'])
        if s['bit_generator']!='PCG64':raise ValueError('Unsupported RNG schema')
        r=np.random.default_rng();r.bit_generator.state=s;return r
    if t=='frame':
        columns=decode(x['columns']);f=pd.DataFrame({c:pd.Series(decode(v),dtype=d) for c,v,d in zip(columns,x['data'],x['dtypes'])})
        f.index=pd.Index(decode(x['index']),name=decode(x['index_name']));f.columns.name=decode(x['columns_name']);return f
    if t=='enum':return CLASSES[x['class']](x['value'])
    if t=='object':
        cls=CLASSES[x['class']];o=object.__new__(cls)
        for k,v in decode(x['fields']).items():object.__setattr__(o,k,v)
        return o
    raise ValueError('Unknown checkpoint tag')
