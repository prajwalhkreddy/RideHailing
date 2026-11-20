"""Master mathematical/elapsed-time boundary; historical engines remain unchanged."""
import numpy as np
import pandas as pd

EWMA = 'MASTER_PREVIOUS_MEAN_ABSOLUTE_DEVIATION_V1'
TEMPORAL = 'UTC_ELAPSED_NY_CALENDAR_V1'


def utc(value):
    t = pd.Timestamp(value)
    if pd.isna(t):
        raise ValueError('Missing time')
    if t.tz is None:
        t = t.tz_localize('America/New_York', ambiguous='raise', nonexistent='raise')
    return t.tz_convert('UTC')


def slot(value):
    t = utc(value)
    if t != t.floor('30min'):
        raise ValueError('Half-hour boundary required')
    return t


def arrival_slot(start, duration_minutes):
    if not np.isfinite(duration_minutes) or duration_minutes < 0:
        raise ValueError('Invalid elapsed duration')
    arrival = utc(start) + pd.Timedelta(minutes=float(duration_minutes))
    return arrival, arrival.floor('30min')


def request_order(frame, start):
    """Fail on invalid civil times; do not discard or synthesize requests."""
    t = slot(start)
    f = frame.copy()
    f['pickup_utc'] = [utc(v) for v in f.tpep_pickup_datetime]
    f['dropoff_utc'] = [utc(v) for v in f.tpep_dropoff_datetime]
    if not ((f.pickup_utc >= t) & (f.pickup_utc < t+pd.Timedelta(minutes=30))).all():
        raise ValueError('Request outside elapsed slot')
    f['duration_minutes'] = (f.dropoff_utc-f.pickup_utc).dt.total_seconds()/60
    if not (f.duration_minutes > 0).all():
        raise ValueError('Nonpositive elapsed trip duration')
    f['mini_slot'] = ((f.pickup_utc-t).dt.total_seconds()//120).astype(int)
    return f.sort_values(['pickup_utc','source_file_month','source_prepared_row'],kind='stable')


def ewma(previous, fares, wait_minutes, parameters):
    """§6 (5)–(8). Store frequency/minute and wait/minute for existing consumers.

    Dividing wait and tolerance by 30 yields the manuscript slot units without
    changing ratios. No dispatch retains mu/sigma; no wait observation retains H.
    """
    old = np.asarray(previous, dtype=float)
    p = np.asarray(fares, dtype=float)
    if old.shape != (4,) or not np.isfinite(old).all() or (old < 0).any() or p.ndim != 1 or not np.isfinite(p).all() or (p < 0).any():
        raise ValueError('Invalid EWMA input')
    if wait_minutes is not None and (not np.isfinite(wait_minutes) or wait_minutes < 0):
        raise ValueError('Invalid charging wait')
    mu, sigma, freq, wait = old
    if len(p):
        mu = parameters.alpha*p.mean() + (1-parameters.alpha)*old[0]
        sigma = parameters.beta*np.abs(p-old[0]).mean() + (1-parameters.beta)*old[1]
    freq = parameters.delta*len(p)/30 + (1-parameters.delta)*freq
    if wait_minutes is not None:
        wait = parameters.kappa*wait_minutes+(1-parameters.kappa)*wait
    return np.array([mu,sigma,freq,wait])
