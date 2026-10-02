"""Input preparation only; no elasticity estimation or spatial dependencies."""
import numpy as np
import pandas as pd

START = pd.Timestamp('2026-01-01')
END = pd.Timestamp('2026-04-01')
COLUMNS = ['pickup_timestamp', 'hour', 'fare', 'trip_distance', 'WeatherCode']


def clean_trips(raw):
    timestamp = pd.to_datetime(raw['tpep_pickup_datetime'], errors='coerce')
    if timestamp.dt.tz is not None:
        raise ValueError('Expected legacy timezone-naive taxi timestamps')
    fare = pd.to_numeric(raw['fare_amount'], errors='coerce')
    distance = pd.to_numeric(raw['trip_distance'], errors='coerce')
    failures = {'invalid_timestamp': timestamp.isna(),
                'nonfinite_fare': ~np.isfinite(fare),
                'nonfinite_distance': ~np.isfinite(distance),
                'nonpositive_fare': np.isfinite(fare) & fare.le(0),
                'nonpositive_distance': np.isfinite(distance) & distance.le(0)}
    inside = timestamp.ge(START) & timestamp.lt(END)
    valid = inside.copy()
    for mask in failures.values():
        valid &= ~mask
    result = pd.DataFrame({'pickup_timestamp': timestamp[valid],
                           'hour': timestamp[valid].dt.hour.astype('int8'),
                           'fare': fare[valid].astype('float64'),
                           'trip_distance': distance[valid].astype('float64')})
    report = {'raw_rows': len(raw), 'in_window_rows': int(inside.sum()),
              'outside_window_valid_timestamp': int((timestamp.notna() & ~inside).sum()),
              'valid_rows': len(result),
              'failures_all_source_rows': {k: int(v.sum()) for k, v in failures.items()},
              'failures_in_window': {k: int((v & inside).sum()) for k, v in failures.items()}}
    return result, report


def weather_coverage(weather, month):
    start = pd.Timestamp(month + '-01')
    expected = pd.date_range(start, start + pd.offsets.MonthBegin(1), freq='h', inclusive='left')
    times = pd.DatetimeIndex(weather['Datetime'])
    report = {'expected_hours': len(expected), 'actual_hours': len(times),
              'missing_timestamps': [str(x) for x in expected.difference(times)],
              'unexpected_timestamps': [str(x) for x in times.difference(expected)],
              'duplicate_timestamps': int(times.duplicated().sum()),
              'missing_WeatherCode': int(weather.WeatherCode.isna().sum()),
              'observed_WeatherCodes': sorted(int(x) for x in weather.WeatherCode.dropna().unique())}
    if times.tz is not None or not times.equals(expected) or report['missing_WeatherCode']:
        raise ValueError(f'Invalid weather calendar: {month}: {report}')
    codes = weather.WeatherCode.to_numpy(dtype=float)
    if not (np.isfinite(codes) & (codes > 0) & (codes == np.floor(codes))).all():
        raise ValueError('Invalid WeatherCode')
    return report


def join_weather(trips, weather):
    times = pd.DatetimeIndex(weather.Datetime)
    if times.tz is not None or times.has_duplicates or not times.equals(times.floor('h')):
        raise ValueError('Weather requires unique naive hourly timestamps')
    result = trips.assign(weather_hour=trips.pickup_timestamp.dt.floor('h')).merge(
        weather[['Datetime', 'WeatherCode']], left_on='weather_hour', right_on='Datetime',
        how='left', validate='many_to_one', sort=False)
    return result[COLUMNS]
