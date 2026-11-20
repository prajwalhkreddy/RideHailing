"""Explicit OD-only adaptation of the preserved historical value codec."""
import copy
from src.simulation.utc_od_state import UTCLedger, UTCSnapshot, UTCStateBuilder
from src.pricing.dqn_contract import DispatchLedger, Snapshot, PricingStateBuilder

PAIRS={UTCLedger:DispatchLedger,UTCSnapshot:Snapshot,UTCStateBuilder:PricingStateBuilder}

def adapt(value, *, restore=False):
    mapping={v:k for k,v in PAIRS.items()} if restore else PAIRS
    if type(value) in mapping:
        result=object.__new__(mapping[type(value)])
        for k,v in vars(value).items():object.__setattr__(result,k,adapt(v,restore=restore))
        return result
    if isinstance(value,dict):return {k:adapt(v,restore=restore) for k,v in value.items()}
    if isinstance(value,list):return [adapt(v,restore=restore) for v in value]
    if isinstance(value,tuple):return tuple(adapt(v,restore=restore) for v in value)
    return value
