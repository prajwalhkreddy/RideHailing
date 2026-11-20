"""Bounded documentation checks; no model, simulator or training imports."""
import unittest,re,json,csv
from scripts.validate_research_review import validate,R,O
class ReviewDocumentationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.report=validate()
 def test_local_links(self):self.assertEqual(self.report['broken_links'],[])
 def test_traceability_paths(self):self.assertEqual(self.report['missing_matrix_paths'],[])
 def test_source_preservation(self):
  for key in ['figure_source_hashes_changed','pilot_source_hashes_changed','evidence_hashes_changed']:self.assertEqual(self.report[key],[])
 def test_diagrams(self):
  self.assertEqual(self.report['diagrams'],9)
  for p in (O/'diagrams').glob('*.mmd'):self.assertRegex(p.read_text(),r'^(flowchart|sequenceDiagram)')
 def test_figures(self):self.assertEqual(self.report['figure_files'],2*self.report['figures'])
 def test_chronology(self):self.assertEqual(self.report['latest_completed_episodes'],2);self.assertFalse(self.report['remaining_training_started'])
 def test_review_sections(self):
  text=(R/'README.md').read_text();self.assertEqual(len(re.findall(r'^## [A-V]\. ',text,re.M)),22);self.assertEqual(text.count('```')%2,0);self.assertNotRegex(text.lower(),r'professor|\bprof\b')
 def test_status_totals(self):self.assertEqual(sum(self.report['requirement_statuses'].values()),self.report['master_requirements'])
if __name__=='__main__':unittest.main()
