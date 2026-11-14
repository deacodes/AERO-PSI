import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from aero_psi_research import explore,interpret
from aero_psi_discovery import query_spec
from aero_psi_experiment_design import preview,validate_design
from aero_psi_investigation import validate_plan,propose
import aero_psi_studio as studio

class ResearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.catalog=json.loads(Path('aero_psi_catalog.json').read_text())
    def test_auto_selection_exposes_ranked_alternatives_and_ties(self):
        r=explore(self.catalog,{'question':'How does gravity affect flame size?'})
        self.assertTrue(r['selection']['automatic'])
        candidates=r['selection']['candidates']
        self.assertEqual(len(candidates),len(self.catalog['investigations']))
        self.assertEqual(r['group'],candidates[0]['group'])
        self.assertEqual(r['selection']['tied_top_groups'],[c['group'] for c in candidates if c['score']==candidates[0]['score']])
        chosen=explore(self.catalog,{'question':'How does gravity affect flame size?','group':'PSI102'})
        self.assertEqual(chosen['group'],'PSI102')
        self.assertFalse(chosen['selection']['automatic'])

    def test_flame_size_routes_to_flame_measurements_not_aerosol(self):
        _,goal,_=query_spec({'question':'How does gravity affect flame size?'})
        self.assertEqual(goal,'flame_geometry')
    def test_flex_exposes_real_rows_and_exact_values(self):
        r=explore(self.catalog,{'question':'How does gravity affect flame size?','group':'FLEX'})
        self.assertEqual(len(r['rows']),274)
        col=next(c for c in r['columns'] if c['key']=='visible_flame_extinction_diameter_mm')
        self.assertGreater(col['numeric_count'],0)
        source=next(x for x in self.catalog['normalized_experiments'] if x['source_path']==r['selected_table'] and x['source_row']==r['rows'][0]['source_row'])
        self.assertEqual(r['rows'][0]['values']['pressure'],source['fields']['pressure']['value'])
        gravity=next(f for f in r['findings'] if f['key']=='gravity')
        self.assertNotEqual(gravity['state'],'recorded')
        self.assertTrue(r['passages'])
    def test_foreign_tables_rejected(self):
        with self.assertRaises(ValueError):explore(self.catalog,{'question':'flame size','group':'FLEX','table':'../../.env'})
    def test_si_receives_exact_selected_rows(self):
        r=explore(self.catalog,{'question':'flame size','group':'FLEX'});row=r['rows'][1]['source_row']
        with patch('aero_psi_research.ask',return_value={'mode':'science_unavailable'}) as ask:
            interpret(self.catalog,{'question':'flame size','group':'FLEX','table':r['selected_table'],'source_rows':[row],'followup':'What does this measurement mean?'})
            records=ask.call_args.kwargs['runtime_evidence']
            table=[x for x in records if x['kind']=='source_table_row']
            self.assertEqual(len(table),1);self.assertEqual(table[0]['source_range'],f'row {row}')
    def test_si_rereads_selected_run_point_and_rejects_foreign_signal(self):
        r=explore(self.catalog,{'question':'smoke detector response','group':'PSI101'})
        run=next(x for x in r['runs'] if x['signals']);signal=run['signals'][0]
        from aero_psi_optical import time_series
        samples=time_series(Path('derived/reports/ingestion_manifest.json'),Path.cwd(),run['source_path'],[signal],10)
        row=samples['points'][0]['source_row']
        payload={'question':'smoke detector response','group':'PSI101','run':run['source_path'],'signal':signal,'source_rows':[row],'followup':'Explain this sample'}
        with patch('aero_psi_research.ask',return_value={}) as ask:
            interpret(self.catalog,payload)
            points=[x for x in ask.call_args.kwargs['runtime_evidence'] if x['kind']=='verified_observed_sample']
            self.assertEqual(len(points),1)
            self.assertEqual(points[0]['point']['source_row'],row)
            self.assertEqual(points[0]['point']['value'],samples['points'][0]['values'][signal])
        with self.assertRaises(ValueError):interpret(self.catalog,payload|{'signal':'fabricated'})
    def test_titles_are_question_specific_optional_plan_fields(self):
        p=[{'tool':'review_science','title':'Define flame diameter at extinction','reason':'Distinguish the recorded outcome from an arbitrary flame size.'}]
        self.assertEqual(validate_plan(p,{})[0]['title'],p[0]['title'])
    def test_cached_aerosol_scenario_does_not_hijack_flame_question(self):
        with patch.dict(os.environ,{'AERO_PSI_COPILOT_ENABLED':'false'}):
            plan,_,_=propose(self.catalog,{'question':'How does gravity affect flame size?','scenario':{'section_count':8}})
        self.assertNotIn('gravity_comparison',[s['tool'] for s in plan])

class DesignTests(unittest.TestCase):
    def design(self):return {'variables':[{'name':'Gravity','unit':'m/s²','minimum':0,'maximum':9.81,'levels':3,'basis':'Explicit test-planning assumption'}],'replicates':2,'outcome':'Defined flame diameter (mm)'}
    def test_trials_are_conditions_not_outcomes(self):
        r=preview(self.design());self.assertEqual(r['trial_count'],6)
        self.assertEqual([r['trials'][i]['conditions']['Gravity'] for i in [0,2,4]],[0,4.905,9.81])
        self.assertFalse(any('prediction' in t or 'outcome' in t for t in r['trials']))
    def test_bounds_and_workload_are_validated(self):
        for v in [float('nan'),float('inf'),-1]:
            d=self.design();d['variables'][0]['maximum']=v
            with self.assertRaises(ValueError):preview(d)
        d=self.design();d['variables']=[dict(d['variables'][0],name=f'Factor{i}',levels=9) for i in range(4)]
        with self.assertRaises(ValueError):preview(d)
    def test_design_persists_and_changes_invalidate_calculations(self):
        with tempfile.TemporaryDirectory() as temp:
            r=studio.create({'content':{'title':'Test','question':'Aerosol comparison','kind':'experiment','design':self.design(),'steps':[{'title':'Evaluate an explicit scenario','tool':'simulate_coagulation'}]}},temp)
            stamp=lambda:{'id':r['id'],'revision':r['revision']}
            r=studio.execute(stamp()|{'step_id':r['content']['steps'][0]['id'],'inputs':{'scenario':{'section_count':8,'output_points':3,'residence_time_s':1}}},{'generated_at':'test'},temp)
            c=copy.deepcopy(r['content']);c['design']['replicates']=3
            r=studio.save(stamp()|{'content':c},temp)
            self.assertTrue(r['runs'][0]['stale']);self.assertEqual(r['content']['design']['replicates'],3)

if __name__=='__main__':unittest.main()
