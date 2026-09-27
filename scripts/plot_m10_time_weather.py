"""Reporting-only extension: read frozen M10 tables; never run M10 or simulations."""
from pathlib import Path
import argparse
import hashlib
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DEFAULT = Path('results/analysis/2026-09-27_passenger_sensitivity_m10')
SECTION = '## PROFESSOR-REQUESTED ELASTICITY VS TIME/WEATHER PLOTS'
STATS = ['mean_epsilon', 'median', 'p25', 'p75']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare_series(table, codes, periods, minimum_n):
    """Return the complete display grid; unsupported statistics stay NaN."""
    grid = pd.MultiIndex.from_product([range(periods), codes], names=['time_bucket', 'WeatherCode'])
    result = table.set_index(['time_bucket', 'WeatherCode']).reindex(grid).copy()
    result.loc[~result.sample_count.ge(minimum_n), STATS] = np.nan
    return result


def clock_label(period, minutes):
    return f'{period * minutes // 60:02d}:{period * minutes % 60:02d}'


def generate(root):
    before = {str(p.relative_to(root)): digest(p) for p in root.rglob('*') if p.is_file()}
    tables = {v: pd.read_csv(root / f'sensitivity_conditions_{v}.csv', float_precision='round_trip')
              for v in ['hourly', '30min']}
    overall = pd.read_csv(root / 'overall_sensitivity_summary.csv', float_precision='round_trip')
    codes = sorted(set().union(*(set(t.WeatherCode) for t in tables.values())))
    colors = dict(zip(codes, ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                             '#8c564b', '#e377c2', '#606060', '#9a9100', '#17becf',
                             '#173f5f', '#6d8300', '#a34490']))
    manifest = {'purpose': 'Reporting only; frozen CSV statistics, no recomputation or filtering.',
                'weather_labels': {str(c): f'Weather {c}' for c in codes},
                'distribution_minimum_n': 2,
                'minimum_n_explanation': 'Only empty and singleton groups are absent from distribution plots; this is a display rule, not a research support threshold.',
                'source_hashes': {f'sensitivity_conditions_{v}.csv': digest(root / f'sensitivity_conditions_{v}.csv') for v in tables},
                'charts': [], 'support': {}}
    manifest['source_hashes']['overall_sensitivity_summary.csv'] = digest(root / 'overall_sensitivity_summary.csv')
    for variant, table in tables.items():
        periods, minutes = (24, 60) if variant == 'hourly' else (48, 30)
        n = table.sample_count
        support = {'observations': int(n.sum()), 'possible_combinations': periods * len(codes),
                   'observed_combinations': int(n.gt(0).sum()),
                   'missing_combinations': periods * len(codes) - int(n.gt(0).sum()),
                   'observations_by_weather': {str(c): int(table.loc[table.WeatherCode.eq(c), 'sample_count'].sum()) for c in codes},
                   'singleton_distribution_omissions': table.loc[n.eq(1), ['time_bucket', 'WeatherCode', 'sample_count']].to_dict('records'),
                   'condition_sample_counts': prepare_series(table, codes, periods, 1).reset_index()[['time_bucket', 'WeatherCode', 'sample_count']].assign(
                       sample_count=lambda d: d.sample_count.fillna(0).astype(int)).to_dict('records')}
        manifest['support'][variant] = support
        for distribution in [False, True]:
            frame = prepare_series(table, codes, periods, 2 if distribution else 1)
            # Exact equality, including gaps: verify the actual plotting arrays before drawing.
            for code in codes:
                actual = frame.xs(code, level='WeatherCode')
                expected = table.loc[table.WeatherCode.eq(code)].set_index('time_bucket').reindex(range(periods))
                for column in (['median', 'p25', 'p75'] if distribution else ['mean_epsilon']):
                    expected_values = expected[column].where(expected.sample_count.ge(2 if distribution else 1))
                    np.testing.assert_array_equal(actual[column].to_numpy(), expected_values.to_numpy())
            fig, ax = plt.subplots(figsize=(15, 7.8))
            fig.subplots_adjust(left=.08, right=.83, bottom=.30, top=.88)
            x = np.arange(periods)
            limit = float(overall.loc[overall.variant.eq(variant) & overall['transform'].eq('raw'), 'p99'].iloc[0]) if distribution else None
            clipped = []
            for code in codes:
                series = frame.xs(code, level='WeatherCode')
                y = series['median' if distribution else 'mean_epsilon'].to_numpy()
                ax.plot(x, y, color=colors[code], marker='o', markersize=3.5, linewidth=1.35, label=f'Weather {code}')
                if distribution:
                    low, high = series.p25.to_numpy(), series.p75.to_numpy()
                    ax.fill_between(x, low, high, color=colors[code], alpha=.12)
                    # Show the IQR also at isolated supported points without bridging missing times.
                    ax.vlines(x, low, high, color=colors[code], alpha=.38, linewidth=1.3)
                    for period in x[np.isfinite(high) & (high > limit)]:
                        clipped.append({'time_bucket': int(period), 'WeatherCode': int(code),
                                        'sample_count': int(series.loc[period, 'sample_count']),
                                        'p25': float(low[period]), 'median': float(y[period]), 'p75': float(high[period])})
            ax.set_title(('Passenger Elasticity Distribution' if distribution else 'Mean Passenger Elasticity') + '\nvs Time of Day by Weather Condition', fontsize=16, pad=15)
            ax.set_xlabel('Time of Day', fontsize=12)
            ax.set_ylabel('Passenger Elasticity (ε)' if distribution else 'Mean Elasticity (ε)', fontsize=12)
            ticks = list(range(0, periods, 1 if variant == 'hourly' else 2))
            if periods == 48:
                ticks.append(47)
            ax.set_xticks(ticks, [clock_label(t, minutes) for t in ticks], rotation=45, ha='right')
            ax.set_xlim(-.35, periods - .65)
            ax.grid(alpha=.2)
            ax.legend(title='Weather Condition', loc='upper left', bbox_to_anchor=(1.01, 1), frameon=False)
            scope = 'Hourly • primary presentation' if variant == 'hourly' else '30-minute • supplementary; final time grouping awaits professor confirmation'
            if distribution:
                ax.set_ylim(0, limit)
                note = ('Central line = median ε; shaded channel = interquartile range (P25–P75).\n'
                        f'View only: y-axis 0–pooled P99 ({limit:.6f}); statistics use the full untrimmed valid M10 population.\n'
                        'Groups with N < 2 are absent; vertical IQR marks retain isolated supported points.')
            else:
                ax.set_yscale('log')
                note = 'Logarithmic y-axis; every observed mean is shown, with no trimming or view-only clipping.'
            empty = [str(c) for c in codes if support['observations_by_weather'][str(c)] == 0]
            note += '\nMissing combinations remain gaps.' + (f' Weather {", ".join(empty)} has no valid observations.' if empty else '')
            fig.text(.08, .155, scope, fontsize=10, weight='bold')
            fig.text(.08, .055, note, fontsize=9, linespacing=1.5)
            stem = ('18_elasticity_distribution_channel_vs_time_weather' if distribution else '17_mean_elasticity_vs_time_weather') if variant == 'hourly' else ('18b_elasticity_distribution_channel_vs_halfhour_weather' if distribution else '17b_mean_elasticity_vs_halfhour_weather')
            files = []
            for ext in ['png', 'pdf']:
                rel = f'charts/{stem}.{ext}'
                kwargs = {'metadata': {'CreationDate': None, 'ModDate': None}} if ext == 'pdf' else {}
                fig.savefig(root / rel, dpi=170, **kwargs)
                files.append(rel)
            plt.close(fig)
            manifest['charts'].append({'variant': variant, 'files': files,
                'statistics': ['median', 'p25', 'p75'] if distribution else ['mean_epsilon'],
                'scale': 'linear' if distribution else 'log', 'view_only_upper_limit': limit,
                'conditions_with_iqr_above_view_limit': clipped, 'exact_source_value_check': 'passed'})
    section = f'''{SECTION}

Graph 1 plots the existing `mean_epsilon` for each time-of-day × WeatherCode condition as a separate weather line. Its logarithmic y-axis shows every observed mean without clipping, trimming, or changing values.

Graph 2 plots the existing median ε with the empirical P25–P75 shaded band. Thin vertical IQR marks also show isolated supported points. The term distribution channel in Graph 2 refers only to the empirical interquartile band (P25–P75). It is not a newly defined channelization metric.

Hourly versions (`17_mean_elasticity_vs_time_weather` and `18_elasticity_distribution_channel_vs_time_weather`) are the primary presentation versions. The 30-minute versions (`17b_mean_elasticity_vs_halfhour_weather` and `18b_elasticity_distribution_channel_vs_halfhour_weather`) are supplementary because final Time-of-Day grouping remains subject to professor confirmation. Each is available as PNG and PDF in `charts/`.

The project has no authoritative descriptive weather-name mapping for these tables, so labels are Weather 1, 2, 3, 5, 7, 8, 9, 12, 13, 14, 15, 16, and 21. No categories are merged. Hourly charts represent 487,710 valid observations across 117 of 312 combinations and 12 observed weather codes; Weather 21 remains in the legend with no data. The 195 missing hourly combinations remain gaps. The supplementary charts represent 526,892 observations across 238 of 624 combinations and all 13 weather codes; 386 missing combinations remain gaps.

No values are interpolated, zero-filled, or forward-filled. Means require N ≥ 1. Distribution plots omit empty and singleton groups (N < 2), the minimum display rule needed to avoid a single-observation distribution; this does not define a new methodological sample-size threshold. Hourly data have no singleton groups. The 30-minute distribution omits Period 7 / 03:30 / Weather 1 (N=1) and Period 28 / 14:00 / Weather 2 (N=1); their means remain on Graph 1. All condition sample sizes, including zero support, are recorded in `elasticity_time_weather_chart_manifest.json`.

Graph 2 uses a **view-only** y-axis range from zero to pooled raw ε P99: 0.493789 for hourly and 0.576244 for 30-minute data (exact limits in the chart manifest). This keeps the central distribution readable; portions of IQRs/medians above this display limit are clipped only in the rendering. Statistics use the full untrimmed valid M10 population. The manifest lists each affected condition and its unchanged quantiles. No maxima, filtering changes, or new outlier rule are introduced.

Reproduce this reporting-only addition with `MPLCONFIGDIR=/tmp/m10_mpl_cache python scripts/plot_m10_time_weather.py`. It reads only the existing condition tables and pooled summary. Exact source-to-plot equality and preservation of all original package files except this README and chart manifests are checked during generation. The original `summary.json` and `verification.json` describe the original analysis run; the supplementary chart manifest records these additions, and `artifact_manifest.json` includes their hashes.

'''
    readme_path = root / 'README.md'
    readme = readme_path.read_text()
    if SECTION in readme:
        start = readme.index(SECTION)
        end = readme.index('## QUESTIONS FOR PROFESSOR', start)
        readme = readme[:start] + readme[end:]
    readme = readme.replace('## QUESTIONS FOR PROFESSOR', section + '## QUESTIONS FOR PROFESSOR')
    readme_path.write_text(readme)
    new_charts = {f for chart in manifest['charts'] for f in chart['files']}
    allowed = new_charts | {'README.md', 'artifact_manifest.json', 'elasticity_time_weather_chart_manifest.json'}
    unchanged = [name for name in before if name not in allowed]
    for name in unchanged:
        assert digest(root / name) == before[name], f'Unexpected change: {name}'
    manifest['verification'] = {'exact_plot_statistics': 'passed', 'original_artifacts_unchanged': unchanged,
                                'missing_statistics_are_nan': True, 'production_code_modified': False}
    (root / 'elasticity_time_weather_chart_manifest.json').write_text(json.dumps(manifest, indent=2, allow_nan=False) + '\n')
    hashes = {str(p.relative_to(root)): digest(p) for p in sorted(root.rglob('*'))
              if p.is_file() and p.name not in {'artifact_manifest.json', 'verification.json'}}
    (root / 'artifact_manifest.json').write_text(json.dumps(hashes, indent=2) + '\n')
    print(json.dumps({'charts_created': sorted(new_charts), 'original_files_preserved': len(unchanged),
                      'exact_value_checks': 'passed'}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', type=Path, default=DEFAULT)
    generate(parser.parse_args().results)
