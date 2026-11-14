"""Evidence readiness and durable research handoffs, with no paid AI calls."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from aero_psi_gap_assessment import assess
from aero_psi_research import explore
import aero_psi_studio as studio

class GapJourneyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.catalog=json.loads(Path('aero_psi_catalog.json').read_text())
    def request(self): return {'question':'How does gravity affect flame size?','group':'FLEX'}
    def test_real_flex_readiness_has_numeric_dimensions_but_no_acceleration(self):
        r=explore(self.catalog,self.request());a=r['assessment'];m={m['key']:m for m in a['matrix']}
        self.assertEqual(m['flame_dimensions']['table_row_count'],197)
        self.assertEqual(m['gravity']['state'],'not_found')
        self.assertEqual(a['joint_structured_rows'],0)
        self.assertIn('not yet supported',a['verdict'])
        gravity=next(x for x in a['actions'] if x['key']=='gravity')
        self.assertIn('flame',gravity['proposal']['required_outputs'])
        self.assertNotIn('particle',gravity['proposal']['required_outputs'])
        self.assertEqual(a['id'],explore(self.catalog,self.request())['assessment']['id'])
    def test_annotation_is_not_numeric_and_zero_is_preserved(self):
        rows=[{'source_path':'A/a.csv','source_row':2,'fields':{'flame_height_mm':{'state':'observed','value':'not measured'}}}]
        f=[{'key':'flame_dimensions','passages':[],'finding':'fixture'}]
        a=assess('flame height','flame_geometry','A',rows,[],f)
        self.assertEqual(a['matrix'][0]['state'],'not_found')
        rows[0]['fields']['flame_height_mm']['value']=0
        self.assertEqual(assess('flame height','flame_geometry','A',rows,[],f)['matrix'][0]['table_row_count'],1)
    def test_report_mention_does_not_close_requirement(self):
        a=assess('scattering','scattering','A',[],[],[{'key':'angular','passages':['document:test'],'finding':'Report lead'}])
        self.assertEqual(a['matrix'][0]['state'],'report_review')
        self.assertEqual(a['actions'][0]['category'],'report_verification')
    def test_general_question_does_not_invent_prerequisites(self):
        a=assess('unrelated question','general','A',[],[],[])
        self.assertEqual(a['matrix'],[]);self.assertEqual(a['actions'],[])
        self.assertIn('Define',a['verdict'])
    def test_save_brief_exact_rows_and_recomputed_model_survive_reload(self):
        context=explore(self.catalog,self.request());row=context['rows'][0]
        with tempfile.TemporaryDirectory() as tmp:
            r=studio.from_research(self.request()|{'finding_key':'gravity','selected_source':'table:'+context['selected_table'],'source_rows':[row['source_row']]},self.catalog,tmp)
            self.assertEqual(r['origin'],'evidence_brief')
            self.assertEqual(r['research_context']['source_rows'],[row['source_row']])
            selected=next(s for s in r['sources'] if s['id']==f"table:{row['source_path']}:{row['source_row']}")
            self.assertEqual(json.loads(selected['text'])['values'],row['values'])
            stamp={'id':r['id'],'revision':r['revision']}
            request={'model':'coagulation','inputs':{'section_count':8,'output_points':3,'residence_time_s':1}}
            r=studio.attach_model(stamp|{'model_context':request,'reason':'Explore an assumed aerosol process, separate from flame dimensions.'},tmp)
            saved=studio.get_record(r['id'],tmp)
            self.assertEqual(saved['content']['question'],self.request()['question'])
            self.assertEqual(saved['model_links'][0]['inputs'],request['inputs'])
            model=next(s for s in saved['sources'] if s['kind']=='executed_model')
            self.assertIn('final',json.loads(model['text']))
            with self.assertRaises(studio.RevisionConflict):studio.attach_model(stamp|{'model_context':request,'reason':'stale'},tmp)
    def test_reject_foreign_source_rows_actions_and_unknown_models(self):
        with tempfile.TemporaryDirectory() as tmp:
            for extra in ({'finding_key':'invented'},{'source_path':'../.env'},{'source_rows':[999999]},{'source_rows':[True]}):
                with self.assertRaises(ValueError):studio.from_research(self.request()|extra,self.catalog,tmp)
            r=studio.from_research(self.request(),self.catalog,tmp)
            for ctx in ({'model':'invented','inputs':{}},{'model':'coagulation','inputs':None}):
                with self.assertRaises(ValueError):studio.attach_model({'id':r['id'],'revision':r['revision'],'model_context':ctx,'reason':'test'},tmp)
            self.assertEqual(studio.get_record(r['id'],tmp)['revision'],1)
    def test_si_revision_retains_assessment_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=studio.from_research(self.request(),self.catalog,tmp)
            def provider(prompt,context):
                self.assertTrue(any(s['kind']=='research_assessment' for s in context['evidence']))
                return {'title':'Revised plan','question':r['content']['question'],'kind':'experiment','steps':[{'title':'Review measured acceleration','source_ids':[r['sources'][0]['id']]}]}
            with patch('aero_psi_studio.retrieve',return_value=[]):
                revised=studio.generate({'id':r['id'],'revision':r['revision'],'question':r['content']['question'],'kind':'experiment'},self.catalog,tmp,provider)
            self.assertEqual(revised['research_context'],r['research_context'])
            self.assertTrue(any(s['kind']=='research_assessment' for s in revised['sources']))

if __name__=='__main__':unittest.main()
