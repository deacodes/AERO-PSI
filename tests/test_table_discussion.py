import unittest
from unittest.mock import patch
from aero_psi.archive import table_page, interpret
from aero_psi.table_discussion import analyze, _sample

class TableDiscussionTests(unittest.TestCase):
 def setUp(self):
  self.path='PSI101/example.csv'
  rows=[{'Time':str(i),'Concentration':str(i*2),'Temperature':None} for i in range(400)]
  rows[250]['Concentration']='5000';rows[252]['Concentration']='';rows[300]['Concentration']='-10'
  self.catalog={'files':[{'source_path':self.path}], 'raw_tables':[{'source_path':self.path,'source_sha256':'abc','columns':['Time','Concentration','Temperature'],'rows':rows}]}
 def test_all_rows_not_preview_and_extrema_preserved(self):
  payload={'source_path':self.path,'question':'What concentration patterns are present?'}
  a=analyze(self.catalog,payload,table_page(self.catalog,payload));c=a['charts'][0]
  self.assertEqual(a['row_count'],400);self.assertEqual(c['column'],'Concentration')
  self.assertEqual(c['statistics']['max'],{'row':252,'value':5000})
  self.assertIn({'row':252,'value':5000},c['points'])
  self.assertEqual(c['statistics']['missing_or_nonnumeric'],1)
  self.assertEqual(c['statistics']['min']['value'],-10) # raw-table -10 is not assumed sentinel
 def test_filter_and_selected_row_scope(self):
  for extra,count in [({'query':'5000'},1),({'source_row':12},1)]:
   p={'source_path':self.path,**extra};a=analyze(self.catalog,p,table_page(self.catalog,p))
   self.assertEqual(a['row_count'],count);self.assertEqual(a['charts'],[])
 def test_sampling_breaks_across_omitted_missing_row(self):
  points=[{'row':i,'value':i} for i in range(1000)];points[501]['value']=None
  sampled=_sample(points);self.assertTrue(any(p['value'] is None for p in sampled))
 def test_followup_uses_computed_selected_dataset_not_broad_retrieval(self):
  p={'source_path':self.path,'question':'What patterns does it show?','history':[{'role':'user','content':'Summarize this table'}]}
  with patch('aero_psi.copilot.ask',return_value={'sources':[]}) as ask:
   result=interpret(self.catalog,p)
   self.assertFalse(ask.call_args.kwargs['retrieve_sources'])
   self.assertEqual(ask.call_args.kwargs['history'],p['history'])
   self.assertEqual(result['table_analysis']['row_count'],400)
   self.assertNotIn('First 30',result['table_scope'])
 def test_imported_sentinel_codes_excluded_without_changing_source(self):
  import tempfile,gzip,json
  from pathlib import Path
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder).resolve();(root/'derived').mkdir();file=root/'derived/run.gz'
   with gzip.open(file,'wt') as f:
    for i,value in enumerate([-999,-10,0,20],2):f.write(json.dumps({'source_row':i,'values':{'PTrakMeasurement(PtPerCC)':value}})+'\n')
   before=file.read_bytes()
   page={'source_path':'run.xls','source_sha256':'abc','worksheet':'Sheet1','columns':['PTrakMeasurement(PtPerCC)']}
   with patch('aero_psi.table_discussion.root',return_value=root),patch('aero_psi.table_discussion.manifest_records',return_value=[{'source_path':'run.xls','status':'imported','derived_path':'derived/run.gz'}]):
    a=analyze({'raw_tables':[]},{},page)
   self.assertEqual(a['summaries'][0]['possible_sentinel'],2)
   self.assertEqual(a['summaries'][0]['min']['value'],0)
   self.assertEqual(before,file.read_bytes())
 def test_state_changes_time_resets_and_adjacent_trends(self):
  rows=[{'Concentration':v,'ElapsedTestTime(Secs)':t,'HeatingInProgress':h} for v,t,h in [(1,0,0),(3,1,1),(None,2,1),(2,0,0),(4,1,0)]]
  table=self.catalog['raw_tables'][0];table['rows']=rows;table['columns']=list(rows[0])
  payload={'source_path':self.path,'question':'concentration'}
  a=analyze(self.catalog,payload,table_page(self.catalog,payload))
  v=next(s for s in a['summaries'] if s['column']=='Concentration')
  self.assertEqual(v['adjacent_increases'],2);self.assertEqual(v['adjacent_decreases'],0)
  self.assertEqual(v['first_to_last_change'],3)
  self.assertEqual(a['elapsed_time_diagnostics'][0]['adjacent_decreases'],1)
  self.assertEqual(a['operating_state_changes'][0]['transition_count'],2)
  self.assertEqual(a['operating_state_changes'][0]['examples'][0]['row'],3)
 def test_general_science_mode_does_not_display_unused_data(self):
  with patch('aero_psi.copilot.ask',return_value={'sources':[]}):
   result=interpret(self.catalog,{'source_path':self.path,'mode':'explain'})
   self.assertNotIn('table_analysis',result)
