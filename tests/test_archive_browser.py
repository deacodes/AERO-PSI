import json
from pathlib import Path
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from aero_psi.archive import datasets,table_page,cell_state
from aero_psi.ai import parse_response,AIResponseError,studio_schema
from aero_psi.model_interpretation import interpret

class ArchiveBrowserTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.catalog=json.loads(Path('aero_psi_catalog.json').read_text())
 def test_lists_every_file_without_claiming_all_are_imported(self):
  result=datasets(self.catalog)['items'];self.assertEqual(len(result),len(self.catalog['files']))
  self.assertEqual(sum(i['view']=='table' for i in result),10);self.assertTrue(any(i['view']=='reference' for i in result))
 def test_pages_exact_raw_values_and_keeps_blank_rows(self):
  raw=next(r for r in self.catalog['raw_tables'] if r['source_path'].startswith('ACME II/'))
  r=table_page(self.catalog,{'source_path':raw['source_path'],'offset':51,'limit':3})
  self.assertEqual(r['total_rows'],len(raw['rows']));self.assertEqual(r['rows'][0]['source_row'],53)
  self.assertEqual(r['rows'][0]['values'],[raw['rows'][51].get(c) for c in raw['columns']])
 def test_run_view_preserves_all_columns_not_downsampling(self):
  item=next(i for i in datasets(self.catalog)['items'] if i['view']=='run')
  r=table_page(self.catalog,{'source_path':item['source_path'],'offset':50,'limit':2})
  self.assertGreater(len(r['columns']),20);self.assertEqual(r['rows'][1]['source_row']-r['rows'][0]['source_row'],1)
 def test_missing_and_zero_and_sentinel_differ(self):
  self.assertEqual(cell_state(''),'missing');self.assertEqual(cell_state('0'),'numeric');self.assertEqual(cell_state('-10',True),'sentinel');self.assertEqual(cell_state('-10'),'numeric')
 def test_rejects_traversal_and_bad_page_size(self):
  for p in [{'source_path':'../.env'},{'source_path':self.catalog['raw_tables'][0]['source_path'],'limit':999}]:
   with self.assertRaises(ValueError):table_page(self.catalog,p)
 def test_model_si_recomputes_instead_of_trusting_client_results(self):
  payload=json.loads(Path('examples/scattering.json').read_text())
  with patch('aero_psi.model_interpretation.ask',return_value={}) as ask:
   interpret(self.catalog,{'model':'scattering','inputs':payload,'result':{'coefficients':999},'question':'Explain the angular pattern'})
   data=json.loads(ask.call_args.kwargs['runtime_evidence'][0]['text'])
   self.assertGreater(data['coefficients']['scattering_m_inv'],0);self.assertLess(data['coefficients']['scattering_m_inv'],1)

 def test_studio_receives_recomputed_model_context(self):
  import tempfile,copy
  import aero_psi.studio as studio
  payload=json.loads(Path('examples/scattering.json').read_text())
  def provider(prompt,context):
   model=next(e for e in context['evidence'] if e['kind']=='executed_model')
   self.assertIn('coefficients',model['text'])
   return {'title':'Compare scattering','steps':[{'title':'Define an optical comparison','source_ids':[model['id']]}]}
  with tempfile.TemporaryDirectory() as storage:
   result=studio.generate({'question':'What optical comparison should follow this model?','model_context':{'model':'scattering','inputs':payload}},self.catalog,storage,provider)
   self.assertTrue(any(s['kind']=='executed_model' for s in result['sources']))

class AIResponseTests(unittest.TestCase):
 def test_truncated_response_is_not_reported_as_server_outage(self):
  with self.assertRaisesRegex(AIResponseError,'length limit'):parse_response(SimpleNamespace(candidates=[SimpleNamespace(finish_reason='MAX_TOKENS')],text='{}'))
 def test_fences_accepted_but_partial_json_never_repaired(self):
  self.assertEqual(parse_response(SimpleNamespace(text='```json\n{"title":"A"}\n```')),{'title':'A'})
  with self.assertRaises(AIResponseError):parse_response(SimpleNamespace(text='{"title":'))
 def test_schema_requires_titles_methods_and_known_tools(self):
  schema=studio_schema(['scattering'],['S1']);step=schema['properties']['steps']['items']
  self.assertIn('method',step['required']);self.assertEqual(step['properties']['tool']['enum'],[None,'scattering']);self.assertEqual(step['properties']['source_ids']['items']['enum'],['S1'])
