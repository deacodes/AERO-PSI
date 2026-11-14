import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch
from aero_psi_gap_si import review,tools

class GapSI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.catalog=json.loads(Path('aero_psi_catalog.json').read_text())
    def plan(self):
        row=next(r for r in self.catalog['normalized_experiments'] if r['source_path'].startswith('FLEX/'))
        return {'interpretation':'Compare oxygen conditions with extinction outcomes.','clarification':'','clarification_blocker':'none','groups':['FLEX'],'search_queries':['FLEX oxygen extinction'], 'requirements':[{'name':'Oxygen at extinction','why':'Defines the comparison condition.'}], 'measurements':[{'path':row['source_path'],'fields':['pressure']}]}
    def answer(self):return {'summary':'Review the condition evidence before comparing outcomes.','findings':[{'title':'Establish the pressure range','what_is_supported':'A column summary is available.','limitation':'No causal comparison has been established.','next_action':'Match the conditions within runs.','why_it_matters':'Uncontrolled conditions limit interpretation.','source_ids':['S1']}],'limitations':['Sources need scientific review.']}
    def test_semantic_plan_executes_actual_columns_without_profile(self):
        calls=[]
        def provider(prompt,schema):calls.append(prompt);return self.plan() if len(calls)==1 else self.answer()
        with patch('aero_psi_gap_si.retrieve',return_value=[]):r=review(self.catalog,{'question':'When the air gets thinner, why might the fire go out?'},provider)
        self.assertEqual(r['status'],'generated');self.assertEqual(len(calls),2)
        self.assertEqual(r['groups'],['FLEX']);self.assertIn('computed_column_summary',calls[1])
        self.assertEqual(r['findings'][0]['source_ids'][0],r['sources'][0]['id'])
        self.assertEqual(r['requirements'][0]['name'],'Oxygen at extinction')
    def test_invented_column_stops_before_synthesis(self):
        p=self.plan();p['measurements'][0]['fields']=['invented_measurement']
        with patch('aero_psi_gap_si.tools') as tool:r=review(self.catalog,{'question':'Compare flames'},lambda *_:p)
        self.assertEqual(r['status'],'unavailable');tool.assert_not_called()
    def test_clarification_does_not_run_tools(self):
        p=self.plan();p['clarification_blocker']='missing_research_objective';p['clarification']='Do you mean flame dimensions or particle size?'
        with patch('aero_psi_gap_si.tools') as tool:r=review(self.catalog,{'question':'Does it get bigger?'},lambda *_:p)
        self.assertEqual(r['status'],'clarification');tool.assert_not_called()
    def test_out_of_scope_not_forced_to_acme(self):
        p=self.plan();p['groups']=[]
        r=review(self.catalog,{'question':'Study ocean salinity'},lambda *_:p)
        self.assertEqual(r['status'],'no_relevant_sources');self.assertNotIn('evidence_view',r)
    def test_unknown_citation_rejected(self):
        answers=iter([self.plan(),dict(self.answer(),findings=[dict(self.answer()['findings'][0],source_ids=['invented'])])])
        with patch('aero_psi_gap_si.retrieve',return_value=[]):r=review(self.catalog,{'question':'Compare flames'},lambda *_:next(answers))
        self.assertEqual(r['status'],'unavailable');self.assertNotIn('findings',r)
    def test_pinned_group_respected(self):
        r=review(self.catalog,{'question':'Compare smoke','group':'PSI101'},lambda *_:self.plan())
        self.assertEqual(r['status'],'unavailable')
    def test_provider_failure_is_not_rule_fallback(self):
        def fail(*_):raise TimeoutError('provider timeout')
        r=review(self.catalog,{'question':'Compare flames'},fail)
        self.assertEqual(r['status'],'unavailable');self.assertNotIn('assessment',r)
    def test_summaries_count_real_numeric_values(self):
        plan=self.plan()
        with patch('aero_psi_gap_si.retrieve',return_value=[]):sources,_=tools(self.catalog,plan)
        s=json.loads(sources[0]['text']);self.assertGreater(s['numeric_rows'],0);self.assertGreaterEqual(s['rows'],s['numeric_rows']);self.assertLessEqual(s['minimum'],s['maximum'])

    def test_exact_dataset_is_sent_to_both_ai_stages_and_measurements(self):
        path=next(t['source_path'] for t in self.catalog['raw_tables'] if t['source_path'].startswith('ACME FLAME DESIGN/') and 'Inverse' in t['source_path'])
        calls=[]
        def provider(prompt,schema):
            calls.append(prompt)
            if len(calls)==1:
                p=self.plan();p['groups']=['ACME FLAME DESIGN'];p['measurements']=[];p['search_queries']=[];return p
            return self.answer()
        r=review(self.catalog,{'question':'Review this flame dataset','source_path':path},provider)
        self.assertEqual(r['status'],'generated');self.assertEqual(r['selected_source'],path)
        self.assertEqual(r['evidence_view']['selected_table'],path)
        self.assertIn(path,calls[0]);self.assertIn('selected_dataset_preview',calls[1])
        self.assertEqual(r['sources'][0]['source_path'],path)
    def test_foreign_selected_dataset_rejected_before_provider(self):
        with self.assertRaises(ValueError):review(self.catalog,{'question':'Compare flames','source_path':'../../.env'},lambda *_:self.plan())
        path=self.plan()['measurements'][0]['path']
        with self.assertRaises(ValueError):review(self.catalog,{'question':'Compare flames','source_path':path,'group':'PSI101'},lambda *_:self.plan())
    def test_selected_dataset_cannot_be_replaced_by_other_table(self):
        path=next(t['source_path'] for t in self.catalog['raw_tables'] if t['source_path'].startswith('ACME FLAME DESIGN/') and 'Inverse' in t['source_path'])
        other=next(t['source_path'] for t in self.catalog['raw_tables'] if t['source_path'].startswith('ACME FLAME DESIGN/') and 'Normal' in t['source_path'])
        p=self.plan();p['groups']=['ACME FLAME DESIGN'];p['measurements']=[{'path':other,'fields':['pressure']}]
        r=review(self.catalog,{'question':'Review this table','source_path':path},lambda *_:p)
        self.assertEqual(r['status'],'unavailable')

    def test_pinned_investigation_constrains_inventory_and_schema(self):
        captured=[]
        def provider(prompt,schema):
            captured.append((prompt,schema))
            p=self.plan();p['clarification_blocker']='missing_research_objective';p['clarification']='Which outcome should be compared?';return p
        r=review(self.catalog,{'question':'Compare flames','group':'FLEX'},provider)
        self.assertEqual(r['status'],'clarification')
        prompt,schema=captured[0]
        self.assertEqual(schema['properties']['groups']['items']['enum'],['FLEX'])
        self.assertEqual(schema['properties']['groups']['maxItems'],1)
        context=json.loads(prompt.split('\n',1)[1])
        self.assertEqual([i['group'] for i in context['inventory']],['FLEX'])
    def test_duplicate_selected_group_is_harmless(self):
        p=self.plan();p['groups']=['FLEX','FLEX'];p['clarification_blocker']='missing_research_objective';p['clarification']='Which response?'
        r=review(self.catalog,{'question':'Compare flames','group':'FLEX'},lambda *_:p)
        self.assertEqual(r['status'],'clarification')

    def test_optional_scope_question_does_not_block_review(self):
        p=self.plan();p['clarification']='Measurements or metadata?';p['clarification_blocker']='none'
        replies=iter([p,self.answer()])
        with patch('aero_psi_gap_si.retrieve',return_value=[]):
            r=review(self.catalog,{'question':'What evidence is needed to validate a model?'},lambda *_:next(replies))
        self.assertEqual(r['status'],'generated')
        self.assertTrue(r['findings'])

    def test_automatic_measurement_view_uses_si_selected_table(self):
        path=next(t['source_path'] for t in self.catalog['raw_tables'] if t['source_path'].startswith('ACME FLAME DESIGN/') and 'Normal' in t['source_path'])
        p=self.plan();p['groups']=['ACME FLAME DESIGN'];p['measurements']=[{'path':path,'fields':['pressure']}];p['search_queries']=[]
        replies=iter([p,self.answer()])
        r=review(self.catalog,{'question':'How do pressure conditions vary?'},lambda *_:next(replies))
        self.assertEqual(r['status'],'generated')
        self.assertEqual(r['evidence_view']['selected_table'],path)
        self.assertEqual(r['selected_measurements'],p['measurements'])
