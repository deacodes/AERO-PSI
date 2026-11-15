import json
from pathlib import Path
import unittest
from aero_psi.archive import datasets
from aero_psi.source_labels import labels,presentation

class SourceLabelTests(unittest.TestCase):
 def test_all_catalog_files_have_labels_without_changing_identity(self):
  catalog=json.loads(Path('aero_psi_catalog.json').read_text());before=json.dumps(catalog)
  items=datasets(catalog)['items'];self.assertEqual(len(items),len(catalog['files']))
  for item in items:
   self.assertIn(item['source_path'],labels());self.assertTrue(item['display_name']);self.assertTrue(item['data_kind'])
   self.assertEqual(item['filename'],Path(item['source_path']).name)
  self.assertEqual(json.dumps(catalog),before)
 def test_readable_run_title_and_verified_link(self):
  for p,title in [('PSI101/Kapton Runs/2010_238_17_kapton_run73.xls','Kapton — Run 73 — measurements'),('PSI102/Kapton/kaptonGMT257 zgy average.xls','Kapton — Run 8 — measurements (averaged)')]:
   self.assertEqual(presentation({'source_path':p})['display_name'],title)
 def test_unknown_file_has_safe_fallback(self):
  result=presentation({'source_path':'FLEX/new_source.pdf'})
  self.assertEqual(result['display_name'],'new source');self.assertEqual(result['data_kind'],'Reference file')
