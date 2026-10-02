import unittest
import numpy as np
import pandas as pd
from src.elasticity_v2.preclustering import calculate, aggregate

class PreclusteringTests(unittest.TestCase):
    def test_global_references_relative_changes_and_signs(self):
        # Global means both 10; includes both-negative deviations and negative elasticity.
        rows = pd.DataFrame({'fare':[5.,15.,10.,10.], 'trip_distance':[15.,5.,10.,10.], 'WeatherCode':[1,2,1,2], 'hour':[0,1,0,1]})
        bases, values, zero = calculate(rows)
        self.assertEqual(bases, {'P_base':10.,'L_base':10.,'N':4})
        self.assertEqual(zero,2)
        np.testing.assert_array_equal(values.delta_P,[-.5,.5])
        np.testing.assert_array_equal(values.delta_L,[.5,-.5])
        np.testing.assert_array_equal(values.epsilon,[-1.,-1.])
        rows.trip_distance=[5.,15.,10.,10.]
        _,values,_=calculate(rows)
        np.testing.assert_array_equal(values.epsilon,[1.,1.])

    def test_zero_epsilon_large_distance_and_near_zero_denominator_retained(self):
        rows=pd.DataFrame({'fare':[1.,1.+1e-12,2.], 'trip_distance':[101.,101.,101.], 'WeatherCode':[1]*3, 'hour':[0]*3})
        _,values,zero=calculate(rows)
        self.assertEqual(len(values),3)
        self.assertEqual(zero,0)
        self.assertTrue(values.epsilon.eq(0).all())
        rows.fare=[1.-1e-12,1.+1e-12,1.]
        _,values,zero=calculate(rows)
        self.assertEqual(len(values),2)
        self.assertEqual(zero,1)

    def test_population_variance_and_missing_cells(self):
        values=pd.DataFrame({'WeatherCode':[1,1,2], 'hour':[0,0,1], 'epsilon':[-1.,3.,7.]})
        table,matrix=aggregate(values,[1,2,3])
        self.assertEqual(len(table),2)
        self.assertEqual(table.iloc[0].mean_elasticity,1.)
        self.assertEqual(table.iloc[0].std_elasticity,2.)
        self.assertEqual(table.iloc[1].std_elasticity,0.)
        np.testing.assert_array_equal(table.variance_elasticity,table.std_elasticity**2)
        self.assertEqual(matrix.shape,(3,24))
        self.assertEqual(int(matrix.isna().sum().sum()),70)
        self.assertTrue(pd.isna(matrix.loc[1,1]))

if __name__=='__main__':unittest.main()
