import unittest
from unittest.mock import patch
from types import SimpleNamespace
import numpy as np
from src.simulation.multi_episode_rng import advance_with_environment_rng
class ResetRNGTests(unittest.TestCase):
 def test_advanced_charging_and_request_streams_retained(self):
  def make():return SimpleNamespace(engine=SimpleNamespace(rng=np.random.default_rng(42),charging=SimpleNamespace(rng=np.random.default_rng(42)),customer=None),reset_evidence={})
  a=make();b=make();a.engine.rng.random(19);a.engine.charging.rng.random(7)
  expected=a.engine.charging.rng.bit_generator.state
  with patch('src.simulation.multi_episode_rng.advance_episode',return_value=b):out=advance_with_environment_rng(a,None)
  self.assertEqual(out.engine.charging.rng.bit_generator.state,expected)
  self.assertIsNot(out.engine.charging.rng,a.engine.charging.rng)
  np.testing.assert_array_equal(out.engine.rng.random(3),a.engine.rng.random(3))
if __name__=='__main__':unittest.main()
