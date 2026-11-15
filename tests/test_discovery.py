import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from aero_psi.discovery import rank_for_question, gap_plan, query_spec
from aero_psi.atlas import condition_gaps, conditions, gaps
from aero_psi.investigation import investigate


def row(group, material, flow, aging, index=2, table='runs.csv'):
    fields={k:{'value':v,'state':'observed','source_column':k} for k,v in zip(('material_or_fuel','flow','duration_or_aging'),(material,flow,aging))}
    return {'source_path':group+'/'+table,'source_sha256':'fixture','source_row':index,'fields':fields}


def metadata(group, objective):
    return {'group':group,'title':group,'objective':objective,'source_path':group+'/metadata.txt','source_sha256':'fixture'}


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.catalog={'investigations':[metadata('A','smoke detector aerosol coagulation gravity'),metadata('B','droplet extinction')],
                      'normalized_experiments':[]}

    def rank(self,q,**kwargs):
        return rank_for_question(self.catalog,{'question':q,**kwargs},records=[])

    def test_question_changes_order(self):
        self.assertEqual(self.rank('smoke detector')['items'][0]['group'],'A')
        self.assertEqual(self.rank('droplet extinction')['items'][0]['group'],'B')

    def test_ties_have_equal_rank_and_zero_not_fabricated_match(self):
        r=self.rank('quasar',goal='general')['items']
        self.assertEqual([i['position'] for i in r],[1,1])
        self.assertTrue(all(i['score']==0 for i in r))

    def test_ledger_sums_and_missing_quality_is_unknown(self):
        for i in self.rank('Which investigations support smoke detector response analysis?')['items']:
            self.assertAlmostEqual(i['score'],sum(v['points'] for v in i['components'].values()),places=2)
            self.assertEqual(i['data_quality']['state'],'unknown')
            self.assertEqual(i['comparability']['state'],'not_established')

    def test_repeated_records_do_not_raise_score(self):
        self.catalog['normalized_experiments']=[row('A','Kapton','5','1')]
        before=self.rank('Kapton',goal='flammability')
        self.catalog['normalized_experiments']*=10
        after=self.rank('Kapton',goal='flammability')
        self.assertEqual([i['score'] for i in before['items']],[i['score'] for i in after['items']])

    def test_document_mention_is_lower_weight_not_measurement(self):
        doc={'id':'document:fixture','source_path':'B/report.pdf','text':'coagulation','source_range':'page 1','review_state':'extracted_unreviewed'}
        r=rank_for_question(self.catalog,{'question':'coagulation'},records=[],documents=[doc])
        a,b=r['items'];self.assertGreater(a['score'],b['score'])
        self.assertEqual(b['matches'][0]['support_weight'],.35)
        self.assertTrue(all(q['state']=='not_located_in_index' for q in b['requirements']))

    def test_zero_or_header_only_signal_not_usable(self):
        run={'source_path':'A/run.xls','group':'A','status':'imported','analysis':{'available_signals':{'scatter_voltage':'Volts'},'fully_zero_core_signals':['scatter_voltage'],'metrics':{'scatter_voltage':{'status':'available'}}}}
        r=rank_for_question(self.catalog,{'question':'detector'},records=[run])
        self.assertEqual(r['items'][0]['requirements'][0]['state'],'not_located_in_index')
        run['analysis']['fully_zero_core_signals']=[]
        r=rank_for_question(self.catalog,{'question':'detector'},records=[run])
        self.assertEqual(r['items'][0]['requirements'][0]['state'],'located_in_index')
        self.assertEqual(r['items'][0]['requirements'][0]['sources'][0]['source_column'],'Volts')

    def test_proposal_has_controls_provenance_and_unknown_feasibility(self):
        p=gap_plan(self.catalog,{'question':'coagulation','group':'A'},records=[])
        self.assertEqual(p['unresolved_scientific_questions']['state'],'not_established')
        for g in p['gaps']:
            self.assertAlmostEqual(g['priority'],sum(g['priority_components'].values()))
            self.assertTrue(g['evidence'][0]['source_path'].startswith('A/'))
            self.assertEqual(g['proposal']['feasibility']['state'],'not_assessed')
            for k in ('controls','required_outputs','varied_parameter','analysis_plan','first_action'):self.assertTrue(g['proposal'][k])
        self.assertEqual(p,gap_plan(self.catalog,{'question':'coagulation','group':'A'},records=[]))

    def test_invalid_requests(self):
        for p in ({'question':''},{'question':'a','goal':[]},{'question':'a','goal':'unsupported'}):
            with self.assertRaises(ValueError):query_spec(p)
        for group in ('bad',[]):
            with self.assertRaises(ValueError):gap_plan(self.catalog,{'question':'a','group':group},records=[])

    def test_no_cross_material_group_or_table_cartesian_gaps(self):
        self.catalog['normalized_experiments']=[row('A','Kapton','5','1'),row('A','Teflon','10','2'),row('B','Kapton','20','3'),row('A','Kapton','30','4',table='other.csv')]
        self.assertEqual(condition_gaps(self.catalog)['gaps'],[])

    def test_incomplete_row_does_not_supply_candidate_values(self):
        complete=row('A','Kapton','5','1');incomplete=row('A','Kapton','99','9',3)
        incomplete['fields']['duration_or_aging']['state']='unknown'
        self.catalog['normalized_experiments']=[complete,incomplete]
        r=condition_gaps(self.catalog)
        self.assertEqual(r['excluded_record_count'],1)
        self.assertEqual(r['strata'][0]['observed_values']['flow'],['5'])
        self.assertEqual(r['gaps'],[])

    def test_contrast_has_single_factor_anchor_and_units(self):
        self.catalog['normalized_experiments']=[row('A','Kapton','5','1'),row('A','Kapton','10','1',3),row('A','Kapton','5','2',4)]
        r=condition_gaps(self.catalog);self.assertEqual(len(r['gaps']),1)
        g=r['gaps'][0];self.assertEqual(sum(g['selected_conditions'][k]!=v for k,v in g['anchor_conditions'].items()),1)
        self.assertTrue(g['source_columns']);self.assertTrue(g['anchor_source_row'])

    def test_bounded_candidates(self):
        self.catalog['normalized_experiments']=[row('A','Kapton',str(i),str(i),i+2) for i in range(60)]
        result=condition_gaps(self.catalog)
        self.assertTrue(result['truncated']);self.assertLessEqual(len(result['gaps']),100)
        self.assertLessEqual(result['examined_combination_count'],2000)

    def test_platform_is_not_measured_gravity(self):
        self.catalog['investigations'][0]['platform']='ISS';self.catalog['normalized_experiments']=[row('A','Kapton','5','1')]
        self.assertEqual(conditions(self.catalog)[0]['conditions']['platform_gravity']['state'],'unknown')

    def test_si_executes_and_saves_real_discovery_outputs(self):
        with tempfile.TemporaryDirectory() as directory,patch.dict(os.environ,{'AERO_PSI_COPILOT_ENABLED':'false'}):
            result=investigate(self.catalog,{'question':'coagulation','group':'A','action':'execute','plan':[{'tool':'rank_investigations','reason':'Compare evidence.'},{'tool':'plan_measurements','reason':'Audit prerequisites.'}]},storage=directory)
            self.assertEqual(result['status'],'completed')
            self.assertEqual(len(result['steps']),2)
            runtime=[s for s in result['evidence'] if s['id'].startswith('runtime:')]
            self.assertEqual(len(runtime),2)
            self.assertTrue(all('Tool output too large' not in s['text'] for s in runtime))
            saved=json.loads((Path(directory)/(result['id']+'.json')).read_text())
            self.assertTrue(saved['steps'][1]['output']['gaps'])
