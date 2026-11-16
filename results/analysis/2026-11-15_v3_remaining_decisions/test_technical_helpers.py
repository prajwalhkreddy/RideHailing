import unittest,json
from pathlib import Path
import numpy as np,pandas as pd
from scipy import stats
from technical_helpers import DropoffAdapter,FEATURES,state,dominated,factors,permitted
class Checks(unittest.TestCase):
 def test_normalization_and_immutability(self):
  a=np.arange(142,dtype=float);copy=a.copy();v,k=DropoffAdapter().build(a,'2026-03-01','2026-02-28 23:30');self.assertAlmostEqual(v.sum(),1);self.assertTrue((v>=0).all());np.testing.assert_array_equal(a,copy)
 def test_carry(self):
  a=DropoffAdapter();v,_=a.build(np.arange(142),'2026-03-01','2026-02-28 23:30');w,k=a.build(np.zeros(142),'2026-03-01 00:30','2026-03-01');np.testing.assert_array_equal(v,w);self.assertEqual(k,'CARRY_FORWARD')
 def test_initial_and_fail_closed(self):
  v=np.arange(142,dtype=float);v/=v.sum();a=DropoffAdapter(v,'2026-02-28');w,k=a.build(np.zeros(142),'2026-03-01','2026-02-28');np.testing.assert_array_equal(v,w)
  with self.assertRaises(ValueError):DropoffAdapter().build(np.zeros(142),'2026-03-01','2026-02-28')
 def test_future(self):
  with self.assertRaises(ValueError):DropoffAdapter().build(np.ones(142),'2026-03-01','2026-03-01')
  with self.assertRaises(ValueError):DropoffAdapter(np.ones(142)/142,'2026-03-02').build(np.zeros(142),'2026-03-01','2026-02-28')
 def test_state(self):
  v=state(dict(zip(FEATURES,range(15))));np.testing.assert_array_equal(v,np.arange(15));self.assertEqual(FEATURES[-2],'dropoff_probability')
 def test_pareto(self):np.testing.assert_array_equal(dominated([[1,1],[2,2],[0,3],[1,1]]),[False,True,False,False])
 def test_factors(self):
  a=factors(6.6,94.7,22.354198442390455);self.assertEqual(len(a),7);self.assertAlmostEqual(a[0]*22.354198442390455,6.6);self.assertAlmostEqual(a[-1]*22.354198442390455,94.7)
 def test_dates(self):
  for t in ['2026-03-16','2026-03-17','2026-03-31']:
   with self.assertRaises(ValueError):permitted(t)
 def test_fit_rows_and_support(self):
  p=Path(__file__).parent;f=pd.read_csv(p/'extended_conditional_distribution_fits.csv');meta=json.loads((p/'fit_split_hashes.json').read_text())
  for s in meta['conditions']:
   g=f[f.condition==s['condition']];self.assertTrue(g.fit_N.eq(s['fit_N']).all());self.assertTrue(g.validation_N.eq(s['validation_N']).all());self.assertEqual(len(s['fit_ids_hash']),64)
  mapping={'Gamma':stats.gamma,'Lognormal':stats.lognorm,'Weibull':stats.weibull_min,'Fisk':stats.fisk,'Generalized_gamma':stats.gengamma,'Truncated_normal':stats.truncnorm}
  for _,r in f[f.candidate!='Empirical_reference'].iterrows():
   d=mapping[r.candidate];args=json.loads(r.parameters);q=d.ppf([.0001,.5,.9999],*args);self.assertTrue(np.isfinite(q).all() and (q>0).all())
 def test_split_determinism(self):
  np.testing.assert_array_equal(np.random.default_rng(42).random(100)<.8,np.random.default_rng(42).random(100)<.8)
if __name__=='__main__':unittest.main()
