import unittest
from types import SimpleNamespace
from unittest.mock import patch
from src.simulation.od_development_evaluation import due,evaluate_due,WINDOWS
class EvaluationScheduleTests(unittest.TestCase):
 def test_due(self):
  for e in range(1,36):
   self.assertEqual(due(SimpleNamespace(slots=16,episode_offset=(e-1)*16)),e in (7,14,21,28,35))
   self.assertFalse(due(SimpleNamespace(slots=15,episode_offset=(e-1)*16)))
 def test_pilot_never_evaluates(self):
  with patch('src.simulation.od_development_evaluation.isolated_evaluation',side_effect=AssertionError):
   for e in (1,2):self.assertEqual(evaluate_due(SimpleNamespace(slots=16,episode_offset=(e-1)*16),None),[])
 def test_no_protected_windows(self):
  self.assertEqual(tuple(x[:10] for x in WINDOWS),('2026-03-13','2026-03-14','2026-03-15'))
if __name__=='__main__':unittest.main()
