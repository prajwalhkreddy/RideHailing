"""Observation persistence under explicit, unverified publication-lag assumptions.

This is a research baseline, not archived forecasts or operational certification.
"""
import hashlib
import json
import numpy as np
import pandas as pd
from .causal_timing import ZONE, VERSION as ORACLE, civil, timing, build_oracle, validate_forecast

VERSION = 'CNN_OBSERVATION_PERSISTENCE_ASSUMED_AVAILABILITY_V1'
VARIABLES = ['WeatherCode', 'Temperature', 'WindSpeed']


def contract(lag_minutes):
    if not np.isfinite(lag_minutes) or lag_minutes < 60:
        raise ValueError('Explicit conservative hourly lag >=60 minutes required')
    return dict(version=VERSION, timezone=ZONE, source_timezone='UTC',
                assumed_availability_lag_minutes=float(lag_minutes),
                availability_status='ASSUMED_NOT_OBSERVED', operational_available=False,
                missing_weather='Latest complete earlier observation; no initial observation -> reject',
                units=dict(WeatherCode='Meteostat code', Temperature='Celsius', WindSpeed='km/h'))


def fingerprint(metadata):
    return hashlib.sha256(json.dumps(metadata, sort_keys=True).encode()).hexdigest()


def select_weather(weather, targets, metadata):
    if metadata != contract(metadata.get('assumed_availability_lag_minutes', float('nan'))):
        raise ValueError('Incompatible weather contract')
    d = weather.copy()
    times = pd.DatetimeIndex(d.Datetime)
    if times.tz is not None or times.hasnans or times.has_duplicates:
        raise ValueError('Expected unique naive Meteostat UTC labels')
    d['observation_time'] = times.tz_localize('UTC')
    values = d[VARIABLES].to_numpy(float)
    valid = np.isfinite(values).all(axis=1) & (values[:, 0] == np.floor(values[:, 0])) & (values[:, 2] >= 0)
    d = d.loc[valid].sort_values('observation_time')
    d['assumed_available_at'] = d.observation_time + pd.Timedelta(minutes=metadata['assumed_availability_lag_minutes'])
    rows = []
    for target in targets:
        info = timing(target)
        eligible = d.loc[d.assumed_available_at <= info['issued_at']]
        if eligible.empty:
            raise ValueError('No earlier complete weather observation; sample ineligible')
        row = eligible.iloc[-1]
        rows.append(dict(**info, **{k: float(row[k]) for k in VARIABLES},
                         observation_time=row.observation_time,
                         assumed_available_at=row.assumed_available_at,
                         observation_age_minutes=(info['issued_at']-row.observation_time).total_seconds()/60))
    return pd.DataFrame(rows)


def build_persistence(source, grid, weather, metadata):
    # Shared history builder retains seven channels, train-only scaling and DST policy.
    d = source.copy()
    labels = pd.DatetimeIndex(d.TimeSlot.unique()).sort_values()
    labels = labels[~labels.tz_localize(ZONE, nonexistent='NaT', ambiguous='raise').isna()]
    selected = select_weather(weather, labels, metadata)
    lookup = selected.set_index(selected.target_start.dt.tz_localize(None))
    for name in VARIABLES:
        d[name] = d.TimeSlot.map(lookup[name])
    x, y, samples, invalid = build_oracle(d, grid)
    samples['weather_mode'] = VERSION
    samples['weather_contract_sha256'] = fingerprint(metadata)
    samples = samples.merge(selected[['target_start', 'observation_time', 'assumed_available_at', 'observation_age_minutes']], on='target_start', validate='one_to_one')
    return x, y, samples, invalid


def validate_persistence_forecast(frame, metadata, checkpoint_metadata, decision_time, *, research=False):
    """Opt-in OD export adapter. Existing OD/historical loaders remain unchanged."""
    if metadata != contract(metadata.get('assumed_availability_lag_minutes', float('nan'))):
        raise ValueError('Invalid persistence metadata')
    if checkpoint_metadata.get('weather_contract_sha256') != fingerprint(metadata) or checkpoint_metadata.get('version') != VERSION:
        raise ValueError('Checkpoint weather contract mismatch; oracle checkpoints forbidden')
    if not research:
        raise ValueError('Availability assumed, not operationally verified')
    issue = timing(decision_time)['issued_at']
    obs = pd.to_datetime(frame.observation_time, utc=True)
    avail = pd.to_datetime(frame.assumed_available_at, utc=True)
    if not (avail == obs + pd.Timedelta(minutes=metadata['assumed_availability_lag_minutes'])).all() or not (avail <= issue).all():
        raise ValueError('Weather availability violation')
    # Reuse exact grid/prediction/time checks including legacy OD DST rejection.
    return validate_forecast(frame, dict(version=ORACLE, timezone=ZONE), decision_time, operational=False)
