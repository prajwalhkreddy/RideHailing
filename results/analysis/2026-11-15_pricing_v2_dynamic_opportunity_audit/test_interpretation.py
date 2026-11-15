import unittest
from interpretation import value_classification,reconvergence_classification
class ReportingTests(unittest.TestCase):
 def test_recovery_is_net_of_initial_sacrifice(self):
  self.assertEqual(value_classification(True,-8,-10),'PARTIAL_REVENUE_RECOVERY')
  self.assertEqual(value_classification(True,0,-10),'FULL_REVENUE_RECOVERY')
  self.assertEqual(value_classification(True,2,-10),'NET_POSITIVE_DYNAMIC_VALUE')
  self.assertEqual(value_classification(True,-12,-10),'STATE_DIFFERENCE_NO_RECOVERY')
 def test_equal_action_control(self):
  self.assertEqual(value_classification(False,0,0),'NO_STATE_EFFECT')
  self.assertEqual(reconvergence_classification([('H0',False),('NEXT_SLOT_BOUNDARY',False),('ONE_FULL_SLOT_AFTER_BOUNDARY',False)]),('NO_STATE_DIVERGENCE',None))
 def test_reconvergence_follows_capture_order(self):
  self.assertEqual(reconvergence_classification([('H0',True),('NEXT_SLOT_BOUNDARY',False),('H100',False),('ONE_FULL_SLOT_AFTER_BOUNDARY',False)]),('SHORT_LIVED_DIVERGENCE','NEXT_SLOT_BOUNDARY'))
 def test_delayed_divergence_and_persistence(self):
  self.assertEqual(reconvergence_classification([('H0',False),('NEXT_SLOT_BOUNDARY',True),('ONE_FULL_SLOT_AFTER_BOUNDARY',True)]),('PERSISTS_MULTIPLE_SLOTS',None))
if __name__=='__main__':unittest.main()
