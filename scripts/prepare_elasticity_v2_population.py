"""Prepare Jan–Mar inputs using existing weather semantics; no model fitting."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from src.data.config import load_config
from src.data.weather import fetch_hourly_weather, prepare_weather, validate_weather, build_weather_metadata
from src.elasticity_v2.population import START, END, clean_trips, join_weather, weather_coverage


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def main():
    # Cache location is operational only; provider/query/preparation are unchanged.
    from meteostat import Hourly, Stations
    Hourly.cache_dir = '/tmp/elasticity_v2_meteostat'
    Stations.cache_dir = '/tmp/elasticity_v2_meteostat'
    cfg = load_config(ROOT / 'config/config.yaml')['weather']
    weather_dir = ROOT / 'data/processed/weather'
    manifest = {'window': {'start_inclusive': str(START), 'end_exclusive': str(END)},
                'join_rule': 'naive pickup timestamp floored to hour; no timezone conversion',
                'validity': 'finite positive fare/distance and valid timestamp; no maximum distance',
                'failure_count_semantics': 'Separate rule counts can overlap; nonpositive counts include finite values only.',
                'sources': {}, 'weather': {}}
    frames = []
    for month in ['2026-01', '2026-02', '2026-03']:
        suffix = month.replace('-', '_')
        path = weather_dir / f'nyc_weather_processed_{suffix}.parquet'
        meta = weather_dir / f'weather_metadata_{suffix}.json'
        if not path.exists():
            if month == '2026-01' or meta.exists():
                raise ValueError(f'Missing existing artifact or metadata collision: {path}')
            start = pd.Timestamp(month + '-01')
            config = {**cfg, 'start': str(start), 'end': str(start + pd.offsets.MonthBegin(1) - pd.Timedelta(seconds=1))}
            print(f'Fetching {month} with existing Meteostat utility', flush=True)
            raw = fetch_hourly_weather(config['latitude'], config['longitude'], config['altitude_m'], config['start'], config['end'])
            frame, fills = prepare_weather(raw)
            validate_weather(frame, month)
            weather_coverage(frame, month)
            metadata = build_weather_metadata(weather=frame, raw_row_count=len(raw), fill_counts=fills, config=config)
            frame.to_parquet(path, index=False)
            meta.write_text(json.dumps({**metadata, 'weather_artifact_path': str(path), 'output_sha256': sha(path)}, indent=2) + '\n')
        frame = pd.read_parquet(path)
        coverage = weather_coverage(frame, month)
        if not meta.exists() or json.loads(meta.read_text())['output_sha256'] != sha(path):
            raise ValueError(f'Weather provenance mismatch: {path}')
        manifest['weather'][month] = {**coverage, 'file': str(path.relative_to(ROOT)), 'sha256': sha(path), 'metadata': str(meta.relative_to(ROOT))}
        frames.append(frame)
    weather = pd.concat(frames, ignore_index=True)
    outdir = ROOT / 'data/processed/elasticity_v2'
    outdir.mkdir(exist_ok=True)
    output = outdir / 'elasticity_input_2026_01_03.parquet'
    if output.exists() or (outdir / 'population_manifest.json').exists():
        raise FileExistsError('Population already exists; refusing to overwrite')
    temporary = outdir / 'elasticity_input_2026_01_03.parquet.partial'
    counts, positions, calendar_counts = {}, {}, {}
    writer = None
    total_valid = total_matched = 0
    try:
        for month in ['2026-01', '2026-02', '2026-03']:
            source = ROOT / f'data/raw/yellow_taxi/yellow_tripdata_{month}.parquet'
            raw = pd.read_parquet(source, columns=['tpep_pickup_datetime', 'fare_amount', 'trip_distance'])
            clean, report = clean_trips(raw)
            joined = join_weather(clean, weather)
            matched = joined.WeatherCode.notna()
            report.update(file=str(source.relative_to(ROOT)), sha256=sha(source), matched_rows=int(matched.sum()), unmatched_rows=int((~matched).sum()))
            manifest['sources'][month] = report
            total_valid += len(joined)
            total_matched += int(matched.sum())
            if not matched.all():
                raise ValueError(f'Unmatched valid taxi rows: {month}: {report["unmatched_rows"]}')
            joined['WeatherCode'] = joined.WeatherCode.astype('int16')
            for code, group in joined.groupby('WeatherCode'):
                code = int(code)
                counts[code] = counts.get(code, 0) + len(group)
                positions.setdefault(code, set()).update(int(h) for h in group.hour.unique())
            for calendar, n in joined.pickup_timestamp.dt.strftime('%Y-%m').value_counts().items():
                calendar_counts[calendar] = calendar_counts.get(calendar, 0) + int(n)
            table = pa.Table.from_pandas(joined, preserve_index=False)
            if writer is None:
                writer = pq.ParquetWriter(temporary, table.schema, compression='snappy')
            writer.write_table(table)
            print(month, json.dumps(report), flush=True)
        writer.close()
        writer = None
        manifest['join'] = {'valid_rows_before_join': total_valid, 'matched_rows': total_matched,
                            'unmatched_rows': total_valid-total_matched, 'match_percentage': 100 * total_matched/total_valid}
        manifest['valid_rows_by_pickup_calendar_month'] = calendar_counts
        manifest['observed_WeatherCodes'] = sorted(counts)
        support = []
        for code, group in weather.groupby('WeatherCode'):
            code = int(code)
            hours = sorted(positions.get(code, set()))
            support.append({'WeatherCode': code, 'weather_hours': len(group), 'matched_taxi_trips': counts.get(code, 0),
                            'represented_hours': hours, 'distinct_hours': len(hours), 'missing_hours': sorted(set(range(24))-set(hours))})
        manifest['weather_code_hour_support'] = support
        manifest['missing_code_hour_positions'] = sum(len(r['missing_hours']) for r in support)
        if pq.ParquetFile(temporary).metadata.num_rows != total_matched:
            raise ValueError('Output row count mismatch')
        temporary.rename(output)
        manifest['output'] = {'file': str(output.relative_to(ROOT)), 'rows': total_matched, 'columns': joined.columns.tolist(), 'sha256': sha(output)}
        (outdir / 'population_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        print(json.dumps({'join': manifest['join'], 'support': support}, indent=2))
    finally:
        if writer is not None:
            writer.close()


if __name__ == '__main__':
    main()
