"""Global references and signed preliminary elasticity, without clustering."""
import numpy as np
import pandas as pd


def calculate(rows):
    p_base = float(rows.fare.mean())
    l_base = float(rows.trip_distance.mean())
    if not np.isfinite([p_base, l_base]).all() or min(p_base, l_base) <= 0:
        raise ValueError('Global references must be finite and positive')
    values = rows.copy()
    values['delta_P'] = (values.fare - p_base) / p_base
    values['delta_L'] = (values.trip_distance - l_base) / l_base
    zero = values.delta_P.eq(0)
    values = values.loc[~zero].copy()
    values['epsilon'] = values.delta_L / values.delta_P
    return {'P_base': p_base, 'L_base': l_base, 'N': len(rows)}, values, int(zero.sum())


def aggregate(values, codes):
    groups = values.groupby(['WeatherCode', 'hour'], observed=True).epsilon
    table = groups.agg(n_valid='size', mean_elasticity='mean', median_elasticity='median')
    table['std_elasticity'] = groups.std(ddof=0)
    table['variance_elasticity'] = table.std_elasticity ** 2
    table = table.reset_index()[['WeatherCode', 'hour', 'n_valid', 'mean_elasticity', 'std_elasticity', 'variance_elasticity', 'median_elasticity']]
    matrix = table.pivot(index='WeatherCode', columns='hour', values='mean_elasticity').reindex(index=codes, columns=range(24))
    return table, matrix
