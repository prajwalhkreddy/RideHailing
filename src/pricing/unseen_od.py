"""Explicit provisional research policy; never expands learned OD support."""
VERSION = 'VALID_UNSEEN_OD_REFERENCE_PRICE_V1'


def validate(contract):
    if contract is not None and contract != {'version': VERSION, 'factor': 1.0}:
        raise ValueError('Incompatible unseen-OD reference policy')
    return None if contract is None else dict(contract)


from dataclasses import fields
import math
from src.pricing.slot_v3_request import V3Request
from src.dispatch.request import RequestState
from src.pricing.slot_v3 import load_contract,pmax

class ReferencePriceRequest(V3Request):
    """Neutral offer is not a member of the learned V3 action vocabulary."""
    def validate(self, valid_grid_ids, mini_slots_per_main_slot):
        if self.customer_model != VERSION:
            return super().validate(valid_grid_ids,mini_slots_per_main_slot)
        c=load_contract()
        if self.pricing_factor != 1.0 or self.base_fare != c['P_base'] or self.offered_fare != c['P_base']:
            raise ValueError('Unseen-OD reference offer mismatch')
        raw=pmax(self.trip_distance_km,self.epsilon_customer,c)
        if not math.isclose(raw,self.p_max,rel_tol=1e-12) or not isinstance(self.customer_accepted,bool) or self.customer_accepted != (self.offered_fare<=raw) or self.acceptance_probability is not None:
            raise ValueError('Unseen-OD acceptance mismatch')
        values={f.name:getattr(self,f.name) for f in fields(RequestState)}
        for key in ['pricing_factor','offered_fare','customer_accepted','customer_model','weather_code','period','historical_p_base','historical_d_base','epsilon_customer','p_max']:
            values[key]=None
        RequestState(**values).validate(valid_grid_ids,mini_slots_per_main_slot)
