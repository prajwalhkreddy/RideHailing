"""Standalone M10 contracts; these tests never invoke production experiments."""
import ast
import inspect
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
from src.analysis.passenger_sensitivity_m10 import (
    START,CUTOFF,compute_m10,distribution,time_support,small_delta_p,outlier_comparison,
    candidate_distributions,illustrative_private_pmax,public_aggregate_state,write_csv,
)


class M10Tests(unittest.TestCase):
    def setUp(self):
        self.trips=pd.DataFrame({'tpep_pickup_datetime':pd.to_datetime(['2026-01-01 00:01']*4),
                                 'trip_distance':[1.,2.,5.,8.],'fare_amount':[10.,20.,30.,60.]})
        self.weather=pd.DataFrame({'Datetime':pd.to_datetime(['2026-01-01 00:00']),'WeatherCode':[1]})

    def test_exact_m9_means_and_m10_not_legacy_ratio(self):
        r=compute_m10(self.trips,self.weather,'30min')
        self.assertEqual(r.bases.iloc[0].L_base,4)
        self.assertEqual(r.bases.iloc[0].P_base,30)
        self.assertEqual(len(r.observations),1)
        x=r.observations.iloc[0]
        self.assertEqual(x.delta_L,4);self.assertEqual(x.delta_P,30)
        self.assertAlmostEqual(x.epsilon,1/30)
        self.assertNotAlmostEqual(x.epsilon,1) # old dimensionless ratio

    def test_negative_and_zero_distance_deviations_excluded(self):
        t=self.trips.iloc[:3].copy();t['trip_distance']=[1.,2.,3.];t['fare_amount']=[30.,40.,50.]
        r=compute_m10(t,self.weather,'30min')
        self.assertEqual(r.observations.trip_id.tolist(),[2])
        self.assertEqual(r.funnel.set_index('stage').loc['delta_L_positive','count'],1)

    def test_positive_distance_zero_or_negative_price_excluded(self):
        t=self.trips.copy();t['fare_amount']=[60.,30.,20.,10.]
        r=compute_m10(t,self.weather,'30min');self.assertTrue(r.observations.empty)
        self.assertEqual(r.funnel.set_index('stage').loc['delta_L_positive','count'],2)
        self.assertEqual(r.funnel.set_index('stage').loc['delta_P_positive','count'],0)

    def test_nonfinite_and_nonpositive_source_rows_excluded(self):
        extra=self.trips.iloc[[0]*4].copy();extra['trip_distance']=[0,-1,np.inf,2];extra['fare_amount']=[10,20,30,np.nan]
        r=compute_m10(pd.concat([self.trips,extra],ignore_index=True),self.weather,'30min')
        self.assertEqual(r.bases.sample_count.sum(),4)
        self.assertTrue(np.isfinite(r.observations.epsilon).all());self.assertTrue((r.observations.epsilon>0).all())

    def test_overflow_epsilon_is_counted_then_excluded(self):
        t=self.trips.iloc[:3].copy();t['trip_distance']=[1.,1.,4.];t['fare_amount']=[1e-320,1e-320,4e-320]
        r=compute_m10(t,self.weather,'30min');f=r.funnel.set_index('stage')['count']
        self.assertEqual(f['delta_P_positive'],1);self.assertEqual(f['finite_epsilon'],0)
        self.assertTrue(r.observations.empty)

    def test_no_legacy_distance_cap_or_deviation_floor(self):
        t=self.trips.iloc[:3].copy();t['trip_distance']=[101.,102.,103.];t['fare_amount']=[10.,20.,30.]
        r=compute_m10(t,self.weather,'30min');self.assertEqual(r.bases.sample_count.sum(),3)
        self.assertEqual(len(r.observations),1)
        t['trip_distance']=[1.,1.,1.001]
        r=compute_m10(t,self.weather,'30min');self.assertEqual(len(r.observations),1)

    def test_population_standard_deviation(self):
        t=self.trips.copy();t['trip_distance']=[1.,1.,5.,9.];t['fare_amount']=[10.,10.,40.,60.]
        r=compute_m10(t,self.weather,'30min')
        expected=np.array([.25/10,1.25/30])
        self.assertAlmostEqual(r.conditions.iloc[0].std_epsilon,expected.std(ddof=0))
        self.assertAlmostEqual(distribution(expected)['std_population'],expected.std(ddof=0))

    def test_hourly_recomputes_bases_and_preserves_weather_codes(self):
        t=pd.concat([self.trips,self.trips],ignore_index=True);t.loc[4:,'tpep_pickup_datetime']=pd.Timestamp('2026-01-01 00:31');t.loc[4:,'fare_amount']*=2
        a=compute_m10(t,self.weather,'30min');b=compute_m10(t,self.weather,'hourly')
        self.assertEqual(len(a.bases),2);self.assertEqual(len(b.bases),1)
        self.assertEqual(b.bases.iloc[0].P_base,45)
        self.assertEqual(set(a.bases.time_bucket),{0,1})

    def test_cutoff_is_exclusive_and_future_data_cannot_affect_outputs(self):
        future=self.trips.copy();future['tpep_pickup_datetime']=CUTOFF;future['fare_amount']=1e9
        before=self.trips.copy();before['tpep_pickup_datetime']=START-pd.Timedelta(minutes=1)
        w=pd.concat([self.weather,pd.DataFrame({'Datetime':[CUTOFF.ceil('h')],'WeatherCode':[99]})],ignore_index=True)
        base=compute_m10(self.trips,self.weather,'30min')
        r=compute_m10(pd.concat([self.trips,future,before],ignore_index=True),w,'30min')
        assert_frame_equal(base.bases,r.bases);assert_frame_equal(base.conditions,r.conditions);assert_frame_equal(base.funnel,r.funnel)
        self.assertEqual(r.weather_codes,(1,))

    def test_missing_weather_is_accounted_without_fallback(self):
        t=self.trips.copy();t.loc[0,'tpep_pickup_datetime']=pd.Timestamp('2026-01-01 01:01')
        r=compute_m10(t,self.weather,'30min');f=r.funnel.set_index('stage')['count']
        self.assertEqual(f['valid_positive_distance_fare'],4);self.assertEqual(f['valid_condition_bases'],3)
        self.assertEqual(time_support(r).iloc[0].possible_conditions,48)
        self.assertEqual(time_support(r).iloc[0].missing_conditions,47)

    def test_duplicate_weather_and_timezone_are_rejected(self):
        with self.assertRaises(ValueError):compute_m10(self.trips,pd.concat([self.weather,self.weather]),'30min')
        t=self.trips.copy();t['tpep_pickup_datetime']=t.tpep_pickup_datetime.dt.tz_localize('UTC')
        with self.assertRaises(ValueError):compute_m10(t,self.weather,'30min')

    def test_denominator_bins_are_disjoint_with_correct_edges(self):
        obs=pd.DataFrame({'delta_P':[.001,.01,.05,.1,.25,.5], 'epsilon':[1.,2.,3.,4.,5.,6.]})
        z=small_delta_p(obs);self.assertEqual(z['count'].tolist(),[1]*6)
        self.assertEqual(z['mean'].tolist(),[1.,2.,3.,4.,5.,6.])

    def test_trimming_is_diagnostic_and_input_unchanged(self):
        x=np.array([.01,.02,.03,.04,100.]);original=x.copy();z=outlier_comparison(x)
        np.testing.assert_array_equal(x,original);self.assertEqual(z.iloc[0]['count'],5)
        self.assertTrue(z.decision.eq('PROFESSOR DECISION REQUIRED').all())

    def test_candidate_normal_invalid_mass_and_truncated_moments(self):
        tab,_=candidate_distributions([.01,.02,.03,100.]);z=tab.set_index('candidate')
        self.assertGreater(z.loc['Normal','probability_nonpositive'],0)
        self.assertEqual(z.loc['positive_truncated_Normal','probability_nonpositive'],0)
        self.assertGreater(z.loc['positive_truncated_Normal','mean'],z.loc['Normal','mean'])

    def test_new_m12_private_equation_and_historical_inverse(self):
        self.assertEqual(illustrative_private_pmax(20,.5,.1),25)
        self.assertEqual(illustrative_private_pmax(20,0,.1),20)
        self.assertEqual(illustrative_private_pmax(20,-.5,.1),15)
        x=compute_m10(self.trips,self.weather,'30min').observations.iloc[0]
        self.assertAlmostEqual(illustrative_private_pmax(x.P_base,x.relative_delta_L,x.epsilon),x.P_i)
        with self.assertRaises(ValueError):illustrative_private_pmax(20,.5,0)

    def test_private_epsilon_cannot_enter_new_public_schema(self):
        args=dict(J_hat=10,J_disp_prev=2,I=3,p=[.2]*5,pi=.3)
        first=public_aggregate_state(**args)
        for epsilon in [.001,1.,100.]:
            illustrative_private_pmax(20,.2,epsilon)
            self.assertEqual(public_aggregate_state(**args),first)
            with self.assertRaises(TypeError):public_aggregate_state(**args,epsilon_j=epsilon)
        self.assertEqual(set(first),{'J_hat','J_disp_prev','I','p','pi'})
        self.assertFalse(any('epsilon' in k for k in inspect.signature(public_aggregate_state).parameters))

    def test_existing_pricing_and_routing_state_have_no_passenger_epsilon(self):
        root=Path(__file__).resolve().parents[1]
        tree=ast.parse((root/'src/pricing/request_context.py').read_text())
        order=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='REQUEST_PRICING_CONTEXT_FEATURE_ORDER' for t in n.targets))
        self.assertFalse(any('epsilon' in x.lower() for x in ast.literal_eval(order.value)))
        tree=ast.parse((root/'src/routing/baseline.py').read_text())
        classes={n.name:n for n in tree.body if isinstance(n,ast.ClassDef)}
        for name in ['RoutingState','GridRoutingFeatures']:
            fields=[n.target.id for n in classes[name].body if isinstance(n,ast.AnnAssign)]
            self.assertFalse(any('epsilon' in x.lower() for x in fields))

    def test_deterministic_artifact_bytes_and_ids(self):
        a=compute_m10(self.trips,self.weather,'30min');b=compute_m10(self.trips,self.weather,'30min')
        assert_frame_equal(a.rows,b.rows)
        with tempfile.TemporaryDirectory() as d:
            for name in ['bases','conditions','funnel']:
                p,q=Path(d)/(name+'1.csv'),Path(d)/(name+'2.csv')
                write_csv(getattr(a,name),p);write_csv(getattr(b,name),q)
                self.assertEqual(p.read_bytes(),q.read_bytes())
        self.assertEqual(a.rows.trip_id.tolist(),[0,1,2,3])


if __name__=='__main__':unittest.main()
