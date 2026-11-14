import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import aero_psi_studio as studio

class StudioTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.storage=Path(self.temp.name)
        self.catalog={'generated_at':'test','schema_version':1,'files':[],'investigations':[],'normalized_experiments':[]}
        self.content={'title':'A literature question','question':'How do measurement methods differ?', 'kind':'literature', 'steps':[{'title':'Compare the methods','method':'Read the actual sources.'}]}
    def tearDown(self): self.temp.cleanup()
    def create(self): return studio.create({'content':self.content},self.storage)
    def stamp(self,r): return {'id':r['id'],'revision':r['revision']}
    def test_progress_persists_and_conflicting_save_preserves_record(self):
        r=self.create(); c=copy.deepcopy(r['content']);c['steps'][0]['completed']=True
        saved=studio.save(self.stamp(r)|{'content':c},self.storage)
        self.assertTrue(studio.get_record(r['id'],self.storage)['content']['steps'][0]['completed'])
        with self.assertRaises(studio.RevisionConflict):studio.save(self.stamp(r)|{'content':c},self.storage)
        self.assertEqual(len(studio.history(r['id'],self.storage)),1)
        self.assertEqual(saved['revision'],2)
    def test_si_disabled_never_creates_fake_plan(self):
        with patch.dict(os.environ,{'AERO_PSI_COPILOT_ENABLED':'false'}):
            with self.assertRaises(studio.StudioUnavailable):studio.generate({'question':'A general science question'},self.catalog,self.storage)
        self.assertEqual(list(self.storage.glob('*.json')),[])
    def test_ai_general_plan_no_forced_models_and_citations_validated(self):
        def provider(prompt,context):
            self.assertIn('Never force aerosol',prompt)
            return copy.deepcopy(self.content)
        with patch.object(studio,'retrieve',return_value=[]):
            r=studio.generate({'question':'Compare two literature methods','kind':'literature'},self.catalog,self.storage,provider)
            self.assertIsNone(r['content']['steps'][0]['tool']);self.assertEqual(r['runs'],[])
            bad=copy.deepcopy(self.content);bad['steps'][0]['source_ids']=['invented:source']
            with self.assertRaises(ValueError):studio.generate({'question':'Compare methods'},self.catalog,self.storage,lambda *_:bad)
    def test_untrusted_ids_and_unknown_tool(self):
        for i in ['../../.env',None,'abc']:
            with self.assertRaises(ValueError):studio.get_record(i,self.storage)
        c=copy.deepcopy(self.content);c['steps'][0]['tool']='shell'
        with self.assertRaises(ValueError):studio.create({'content':c},self.storage)
    def test_dataset_missing_values_preserved_nonfinite_rejected(self):
        r=self.create();data={'name':'Measured table','reference':'User notebook, no external verification','columns':[{'name':'Time','unit':'s'},{'name':'Signal','unit':'V'}],'rows':[[0,0.4],[1,None],[2,0.7]]}
        result=studio.add_dataset(self.stamp(r)|{'dataset':data},self.storage)
        self.assertIsNone(result['datasets'][0]['rows'][1][1])
        self.assertEqual(result['datasets'][0]['classification'],'user_supplied_unverified')
        data['rows'][0][1]=float('nan')
        with self.assertRaises(ValueError):studio.add_dataset(self.stamp(result)|{'dataset':data},self.storage)
    def test_real_solver_results_and_edit_invalidates_results(self):
        self.content['kind']='simulation';self.content['steps'][0]['tool']='simulate_coagulation';r=self.create()
        scenario={'section_count':8,'output_points':3,'residence_time_s':1,'initial_number_concentration_m3':1e9}
        r=studio.execute(self.stamp(r)|{'step_id':r['content']['steps'][0]['id'],'inputs':{'scenario':scenario}},self.catalog,self.storage)
        self.assertEqual(len(r['datasets']),3);self.assertEqual(r['runs'][0]['inputs']['scenario'],scenario)
        self.assertFalse(r['content']['steps'][0]['completed'])
        self.assertEqual(r['datasets'][0]['rows'][0][1],r['runs'][0]['output']['series'][0]['number_concentration_m3'])
        c=copy.deepcopy(r['content']);c['steps'][0]['method']='A revised initial condition'
        saved=studio.save(self.stamp(r)|{'content':c},self.storage)
        self.assertTrue(saved['runs'][0]['stale']);self.assertTrue(all(d['stale'] for d in saved['datasets']))
    def test_missing_explicit_inputs_cannot_execute(self):
        self.content['steps'][0]['tool']='scattering';r=self.create()
        with self.assertRaises(ValueError):studio.execute(self.stamp(r)|{'step_id':r['content']['steps'][0]['id'],'inputs':{}},self.catalog,self.storage)
        self.assertEqual(studio.get_record(r['id'],self.storage)['runs'],[])
    def test_interpretation_reads_saved_rows_not_client_claims(self):
        r=self.create();r=studio.add_dataset(self.stamp(r)|{'dataset':{'name':'Test','reference':'User supplied','columns':[{'name':'x'},{'name':'y'}],'rows':[[1,2],[3,4]]}},self.storage)
        def ask(catalog,question,runtime_evidence,allow_background,history=None,information_mode=None):
            data=json.loads(runtime_evidence[0]['text']);self.assertEqual(data['rows'],[[3,4]]);self.assertEqual(history,[{'role':'user','content':'What is this dataset?'}])
            return {'mode':'science_unavailable'}
        with patch.object(studio,'ask',side_effect=ask):
            result=studio.interpret(self.stamp(r)|{'question':'Explain this point','history':[{'role':'user','content':'What is this dataset?'}],'dataset_id':r['datasets'][0]['id'],'row_indices':[1]},self.catalog,self.storage)
        self.assertEqual(result['ai_reviews'][0]['row_indices'],[1])
    def test_library_includes_legacy_and_archive_can_restore(self):
        r=self.create();legacy=self.storage/'legacy';legacy.mkdir();i='a'*32
        (legacy/(i+'.json')).write_text(json.dumps({'id':i,'question':'Old analysis','created_at':studio.now(),'steps':[]}))
        self.assertEqual(len(studio.library(self.storage,legacy)['items']),2)
        r=studio.save(self.stamp(r)|{'content':r['content'],'archived':True},self.storage)
        self.assertTrue(r['archived'])
        r=studio.save(self.stamp(r)|{'content':r['content'],'archived':False},self.storage)
        self.assertFalse(r['archived'])
    def test_full_aggregate_membership_and_full_summary_are_preserved(self):
        r=self.create()
        r=studio.add_dataset(self.stamp(r)|{'dataset':{'name':'More than 30 rows','reference':'Unit test fixture','columns':[{'name':'x'},{'name':'y'}],'rows':[[i,i*2] for i in range(45)]}},self.storage)
        indices=list(range(45));c=copy.deepcopy(r['content'])
        c['steps'][0]['data_links']=[{'dataset_id':r['datasets'][0]['id'],'row_indices':indices}]
        r=studio.save(self.stamp(r)|{'content':c},self.storage)
        self.assertEqual(len(r['content']['steps'][0]['data_links'][0]['row_indices']),45)
        def ask(catalog,question,runtime_evidence,allow_background,history=None,information_mode=None):
            data=json.loads(runtime_evidence[0]['text'])
            self.assertEqual(len(data['rows']),30)
            self.assertEqual(data['scope_row_count'],45)
            self.assertEqual(data['summary_over_all_scope_rows'][1]['mean'],44)
            self.assertFalse(data['preview_is_complete'])
            return {'mode':'science_unavailable'}
        with patch.object(studio,'ask',side_effect=ask):
            result=studio.interpret(self.stamp(r)|{'question':'Explain the aggregate','dataset_id':r['datasets'][0]['id'],'row_indices':indices},self.catalog,self.storage)
        self.assertEqual(result['ai_reviews'][0]['row_indices'],indices)

    def test_edit_during_ai_generation_is_not_overwritten(self):
        r=self.create()
        def provider(*_):
            c=copy.deepcopy(r['content']);c['notes']='Saved concurrently'
            studio.save(self.stamp(r)|{'content':c},self.storage)
            return copy.deepcopy(self.content)
        with patch.object(studio,'retrieve',return_value=[]):
            with self.assertRaises(studio.RevisionConflict):studio.generate(self.stamp(r)|{'question':r['content']['question']},self.catalog,self.storage,provider)
        self.assertEqual(studio.get_record(r['id'],self.storage)['content']['notes'],'Saved concurrently')

if __name__=='__main__':unittest.main()
