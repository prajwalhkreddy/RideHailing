"""Charging admission only at the selected station after physical arrival."""
from src.charging.stations import ChargingInfrastructure,QueueEntry
from src.charging.energy import enter_charging,requires_charging
from src.fleet.state import VehicleStatus

class TimedChargingInfrastructure(ChargingInfrastructure):
    timed_navigation=True
    def present_vehicle(self,*args,**kwargs):
        raise ValueError('Zero-time charging presentation is prohibited; use admit_arrived.')
    def admit_arrived(self,vehicle,station_id,parameters,arrival_order):
        if station_id not in self.stations:raise ValueError('Unknown station.')
        station=self.stations[station_id]
        if vehicle.current_grid!=station.grid_id or vehicle.trip_status is not VehicleStatus.IDLE:
            raise ValueError('Charging admission requires completed arrival at selected station.')
        if vehicle.vehicle_id in self.vehicle_station:raise ValueError('Vehicle already queued/charging.')
        if not requires_charging(vehicle,parameters):raise ValueError('Charging threshold not reached.')
        enter_charging(vehicle,parameters);self.vehicle_station[vehicle.vehicle_id]=station_id
        if station.charging_available:
            station.active_vehicle_ids.add(vehicle.vehicle_id);vehicle.current_action='charging'
        else:
            station.queue.append(QueueEntry(vehicle.vehicle_id,arrival_order,float(self.rng.random())))
            station.queue.sort(key=lambda e:(e.arrival_order,e.random_priority,e.vehicle_id));vehicle.current_action='charging_queue'
        return station
