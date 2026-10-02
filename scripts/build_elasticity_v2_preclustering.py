"""Build preliminary diagnostics from the validated input only."""
from pathlib import Path
import sys
import hashlib
import json
import shutil
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from src.elasticity_v2.preclustering import calculate, aggregate


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()


def main():
    canonical = ROOT / 'data/processed/elasticity_v2'
    source = canonical / 'elasticity_input_2026_01_03.parquet'
    checksum = digest(source)
    rows = pd.read_parquet(source)
    assert len(rows) == 10620887
    assert rows.columns.tolist() == ['pickup_timestamp', 'hour', 'fare', 'trip_distance', 'WeatherCode']
    assert rows.pickup_timestamp.ge('2026-01-01').all() and rows.pickup_timestamp.lt('2026-04-01').all()
    assert rows.hour.eq(rows.pickup_timestamp.dt.hour).all()
    assert np.isfinite(rows[['fare','trip_distance']]).all().all() and rows[['fare','trip_distance']].gt(0).all().all()
    codes = sorted(int(c) for c in rows.WeatherCode.unique())
    assert codes == [1,2,3,5,7,8,9,12,13,14,15,16,17,21]
    bases, values, zero = calculate(rows)
    epsilon = values.epsilon.to_numpy()
    nonfinite = int((~np.isfinite(epsilon)).sum())
    counts = {'negative': int((epsilon < 0).sum()), 'zero': int((epsilon == 0).sum()), 'positive': int((epsilon > 0).sum())}
    print(json.dumps({'total_rows': len(rows), 'delta_P_zero': zero, 'nonfinite_epsilon': nonfinite, 'sign_counts': counts}), flush=True)
    if nonfinite:
        raise ValueError('Nonfinite epsilon requires investigation; no observations silently removed')
    table, matrix = aggregate(values, codes)
    bases.update(date_window={'start_inclusive':'2026-01-01 00:00:00', 'end_exclusive':'2026-04-01 00:00:00'}, input_artifact=str(source.relative_to(ROOT)), input_sha256=checksum)
    quantiles = np.quantile(epsilon, [.01,.05,.25,.5,.75,.95,.99])
    std = float(np.std(epsilon, ddof=0))
    stats = {'mean': float(epsilon.mean()), 'std_population': std, 'variance': std**2, 'min': float(epsilon.min()), 'max':float(epsilon.max()), **dict(zip(['p1','p5','p25','median','p75','p95','p99'], map(float, quantiles)))}
    summary = {'global_bases': bases, 'total_rows': len(rows), 'exact_zero_delta_P_excluded': zero, 'epsilon_valid_count':len(values), 'nonfinite_epsilon_count':nonfinite, 'epsilon_units':'dimensionless', 'ddof':0,
               'sign_counts':counts, 'sign_percentages':{k:100*v/len(values) for k,v in counts.items()}, 'overall_epsilon':stats,
               'extreme_absolute_epsilon':{str(t):{'count':int((np.abs(epsilon)>t).sum()), 'percentage':float(100*(np.abs(epsilon)>t).mean())} for t in [1,10,100,1000]},
               'matrix':{'total_cells':int(matrix.size), 'populated_cells':int(matrix.notna().sum().sum()), 'missing_cells':int(matrix.isna().sum().sum()), 'missing_hours_by_code':{str(c):matrix.columns[matrix.loc[c].isna()].tolist() for c in codes}},
               'status':'READY_FOR_CLUSTERING_DECISION', 'clustering_blocker':'Missing-hour rule requires a decision; no imputation or clustering performed.'}
    result = ROOT / 'results/analysis/2026-10-02_elasticity_v2_preclustering'
    result.mkdir(parents=True, exist_ok=True)
    (result/'charts').mkdir(exist_ok=True)
    (canonical/'global_bases.json').write_text(json.dumps(bases,indent=2)+'\n')
    table.to_csv(canonical/'preliminary_weather_code_hour_elasticity.csv',index=False,float_format='%.17g')
    matrix.to_csv(canonical/'weather_code_hour_mean_matrix.csv',na_rep='NaN',float_format='%.17g')
    for name in ['global_bases.json','preliminary_weather_code_hour_elasticity.csv','weather_code_hour_mean_matrix.csv']:
        shutil.copyfile(canonical/name,result/name)
    top = values.loc[values.epsilon.abs().nlargest(20).index, ['pickup_timestamp','WeatherCode','hour','fare','trip_distance','delta_P','delta_L','epsilon']]
    top.to_csv(result/'extreme_epsilon_top20.csv',index=False,float_format='%.17g')
    for metric, label, stem in [('mean_elasticity','Mean elasticity','mean'), ('std_elasticity','Population standard deviation','std')]:
        fig, ax = plt.subplots(figsize=(14,7))
        for i,code in enumerate(codes):
            series = table.loc[table.WeatherCode.eq(code)].set_index('hour')[metric].reindex(range(24))
            ax.plot(range(24), series, marker='o', markersize=3, color=plt.get_cmap('tab20')(i), label=f'Weather {code}')
        ax.set(title='PRELIMINARY — BEFORE 3-CLASS CLUSTERING\nRaw-weather '+label.lower()+' vs hour',xlabel='Hour of day',ylabel=label)
        ax.set_xticks(range(24));ax.grid(alpha=.2)
        ax.legend(title='Original WeatherCode',bbox_to_anchor=(1.01,1),loc='upper left',frameon=False)
        fig.text(.08,.025,'Jan–Mar 2026 • Global references • All signed values retained • Missing combinations remain gaps',fontsize=10)
        fig.tight_layout(rect=(0,.06,1,1))
        fig.savefig(result/f'charts/raw_weather_{stem}_elasticity_vs_hour.png',dpi=170)
        plt.close(fig)
    assert digest(source) == checksum
    assert int(table.n_valid.sum()) == len(values)
    summary['output_sha256'] = {str(p.relative_to(result)):digest(p) for p in sorted(result.rglob('*')) if p.is_file() and p.name not in ['summary.json','README.md']}
    (result/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    (result/'README.md').write_text('''# Preliminary elasticity V2 — before 3-class clustering

Input: validated Jan–Mar 2026 parquet, unchanged; its hash and exact window are in `global_bases.json`.
One global fare mean and distance mean are calculated from all 10,620,887 rows. Relative distance change is divided by relative price change. Only exact zero price-change denominators are excluded. Signed dimensionless epsilon is retained without caps, clipping, trimming, or near-zero thresholds.

`summary.json` records denominator, sign, nonfinite, tail and overall diagnostics. Shares use valid epsilon N. SD is population SD (ddof=0); variance is its square. `extreme_epsilon_top20.csv` preserves the 20 largest absolute epsilon observations for inspection; none are removed.

The preliminary table contains observed code/hour groups only. The 14×24 matrix explicitly retains NaN in missing positions. Median is diagnostic only. Charts use full linear axes and show original codes, not final classes. Missing-hour handling must be decided before clustering; no imputation or K-means is performed.

Canonical bases and both tables are in `data/processed/elasticity_v2/`; copies here are identical. Reproduce with `MPLCONFIGDIR=/tmp/m10_mpl_cache python scripts/build_elasticity_v2_preclustering.py`. No runtime or simulation changes.
''')
    print(json.dumps(summary,indent=2))

if __name__ == '__main__':
    main()
