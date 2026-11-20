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

class RenderingRepairTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  from scripts.validate_readme_rendering import audit
  cls.report=audit()
 def test_links_and_anchors(self):self.assertEqual(self.report['link_errors'],[])
 def test_math_parser(self):
  self.assertTrue(all(r['parsed'] for r in self.report['mathtext_diagnostics']))
  self.assertGreater(self.report['display_formulas'],0)
 def test_diagram_subset(self):self.assertEqual(self.report['restricted_grammar_errors'],[])
 def test_images_decode(self):self.assertTrue(all(r['readable'] for r in self.report['images']))
 def test_status_and_next_steps(self):
  text=(R/'README.md').read_text();self.assertIn('## Current Research Status and Next Steps',text);self.assertIn('### Next steps',text)
 def test_complete_html(self):
  text=(O/'readme_structural_preview.html').read_text();self.assertIn('Supporting evidence and review validation',text);self.assertGreaterEqual(self.report['rendered_tables'],6)

if __name__=='__main__':unittest.main()
