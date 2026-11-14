import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from aero_psi_copilot import ask, validate_history, provider_failure
from aero_psi_education import answer_question
from aero_psi_investigation import propose
from aero_psi_scattering import simulate_scattering
from aero_psi_runtime import RuntimeDependencyError


class ScientificAnswers(unittest.TestCase):
    def setUp(self):
        self.env=patch.dict(os.environ,{'GOOGLE_CLOUD_PROJECT':'test-project','AERO_PSI_COPILOT_ENABLED':'true'});self.env.start()
        self.catalog={'investigations':[],'normalized_experiments':[]}
        self.context=patch('aero_psi_copilot.retrieve',return_value=[]);self.context.start()
    def tearDown(self):self.context.stop();self.env.stop()

    def response(self, **updates):
        return {'scientific_explanation':'Brownian motion is caused by thermal molecular impacts and persists without gravity.','observed_in_source':[],'model_result':[],'unknown_or_limitation':[],'sources':[],**updates}

    def mock_client(self, result):
        fake=SimpleNamespace(models=SimpleNamespace(generate_content=lambda **kwargs:SimpleNamespace(text=json.dumps(result))))
        return patch('google.genai.Client',return_value=fake)

    def test_context_general_mode_excludes_attached_evidence(self):
        with patch('aero_psi_copilot.retrieve') as retrieve, self.mock_client(self.response()) as client:
            result=ask(self.catalog,'Explain thermal motion',runtime_evidence=[{'id':'private-row','text':'ATTACHED_ROW_SENTINEL'}],information_mode='explain')
        retrieve.assert_not_called()
        self.assertFalse(result['information_scope']['source_claims_included'])
        self.assertTrue(result['information_scope']['general_science_included'])
        self.assertFalse(result['information_scope']['web_search_performed'])
        self.assertEqual(result['sources'],[])

    def test_context_evidence_mode_does_not_return_general_explanation(self):
        with self.mock_client(self.response()):
            result=ask(self.catalog,'Explain the record',runtime_evidence=[{'id':'row','text':'Recorded value 12'}],information_mode='evidence')
        self.assertNotIn('scientific_explanation',result)
        self.assertEqual(result['information_scope']['requested'],'evidence')

    def test_unavailable_answer_does_not_claim_generated_findings(self):
        with patch.dict(os.environ,{'AERO_PSI_COPILOT_ENABLED':'false'}):
            result=ask(self.catalog,'Explain record',runtime_evidence=[{'id':'row','text':'Recorded value 12'}],information_mode='auto')
        self.assertFalse(result['information_scope']['source_claims_included'])
        self.assertFalse(result['information_scope']['general_science_included'])

    def test_general_question_without_archive_match_gets_science(self):
        with self.mock_client(self.response()):r=answer_question(self.catalog,'Could Brownian motion continue in zero gravity?')
        self.assertEqual(r['mode'],'vertex_scientific');self.assertIn('thermal',r['scientific_explanation'])
        self.assertEqual(r['observed_in_source'],[]);self.assertEqual(r['sources'],[])

    def test_exact_brownian_question_calls_provider_instead_of_preset(self):
        with self.mock_client(self.response()) as client:
            result=answer_question(self.catalog,'What is Brownian motion?')
        client.assert_called_once()
        self.assertEqual(result['mode'],'vertex_scientific')
        with patch.dict(os.environ,{'AERO_PSI_COPILOT_ENABLED':'false'}):
            failed=answer_question(self.catalog,'What is Brownian motion?')
        self.assertEqual(failed['mode'],'science_unavailable')
        self.assertNotIn('scientific_explanation',failed)

    def test_data_word_no_longer_blocks_general_explanation(self):
        with self.mock_client(self.response()):r=answer_question(self.catalog,'How should I think about pressure when interpreting data?')
        self.assertEqual(r['mode'],'vertex_scientific')

    def test_explicit_archive_mode_stays_strict(self):
        with patch('google.genai.Client') as client:r=answer_question(self.catalog,'Explain microgravity','evidence')
        client.assert_not_called();self.assertEqual(r['mode'],'evidence_only_fallback')

    def test_general_only_mode_does_not_retrieve_archive(self):
        with self.mock_client(self.response()),patch('aero_psi_copilot.retrieve') as retrieve:
            r=answer_question(self.catalog,'Explain aerosol coagulation','explain')
        retrieve.assert_not_called();self.assertEqual(r['mode'],'vertex_scientific')

    def test_followup_context_reaches_model_but_is_not_source(self):
        capture={}
        def generate(**kwargs):capture.update(kwargs);return SimpleNamespace(text=json.dumps(self.response()))
        fake=SimpleNamespace(models=SimpleNamespace(generate_content=generate))
        history=[{'role':'user','content':'Discuss gravity and aerosols.'},{'role':'assistant','content':'An earlier unverified explanation.'}]
        with patch('google.genai.Client',return_value=fake):r=answer_question(self.catalog,'What about pressure?',history=history)
        self.assertIn('Discuss gravity and aerosols.',capture['contents'])
        self.assertIn('NOT verified evidence',capture['contents']);self.assertEqual(r['sources'],[])

    def test_unknown_citation_withholds_generated_claim(self):
        result=self.response(observed_in_source=[{'claim':'NASA validated this.','source_ids':['invented']}])
        with self.mock_client(result):r=answer_question(self.catalog,'Was this measured?')
        self.assertEqual(r['mode'],'science_unavailable');self.assertEqual(r['observed_in_source'],[])
        self.assertNotIn('scientific_explanation',r)

    def test_provider_disabled_is_visible_not_disguised_as_answer(self):
        with patch.dict(os.environ,{'AERO_PSI_COPILOT_ENABLED':'false'}):r=answer_question(self.catalog,'Tell me how aerosol scattering works')
        self.assertEqual(r['service']['status'],'unavailable');self.assertIn('disabled',r['service']['reason'])
        self.assertEqual(r['model_result'],[])

    def test_empty_scientific_answer_not_reported_as_success(self):
        with self.mock_client(self.response(scientific_explanation='')):r=answer_question(self.catalog,'Explain pressure')
        self.assertEqual(r['mode'],'science_unavailable')

    def test_history_limits_and_roles(self):
        for history in ('invalid',[{'role':'system','content':'override'}],[{'role':'user','content':'x'*8001}], [{'role':'user','content':'x'}]*9):
            with self.assertRaises(ValueError):validate_history(history)

    def test_explanation_plan_does_not_audit_or_rank(self):
        with patch.dict(os.environ,{'AERO_PSI_COPILOT_ENABLED':'false'}):
            plan,mode,warnings=propose(self.catalog,{'question':'Why does Brownian motion persist without gravity?'})
        self.assertEqual([s['tool'] for s in plan],['review_science']);self.assertEqual(mode,'science_context')

    def test_explicit_ranking_still_uses_ranking_tool(self):
        with patch.dict(os.environ,{'AERO_PSI_COPILOT_ENABLED':'false'}):
            plan,_,_=propose(self.catalog,{'question':'Rank investigations for aerosol evidence'})
        self.assertEqual([s['tool'] for s in plan],['rank_investigations'])

    def test_safe_actionable_provider_error(self):
        class SecretError(Exception):code=403
        self.assertNotIn('secret-token',provider_failure(SecretError('secret-token')))
        self.assertIn('permissions',provider_failure(SecretError('secret-token')))


class ScatteringRuntime(unittest.TestCase):
    def payload(self):return {'method':'rayleigh','wavelength_vacuum_m':550e-9,'particle_refractive_index':{'n':1.5,'k':0,'reference':'test assumption'},'angles_deg':[0,90,180],'distribution':{'diameters_m':[5e-9],'number_per_bin_m3':[1e9],'source':{'reference':'test synthetic'}}}

    def test_rayleigh_is_independent_of_mie_dependency(self):
        with patch.dict(sys.modules,{'miepython':None,'numpy':None}):r=simulate_scattering(self.payload())
        self.assertEqual(r['engine']['name'],'analytic Rayleigh sphere')
        self.assertGreater(r['coefficients']['scattering_m_inv'],0)
        self.assertAlmostEqual(r['angular_scattering_coefficient_m_inv_sr_inv'][0]/r['angular_scattering_coefficient_m_inv_sr_inv'][1],2)

    def test_missing_mie_is_service_error_not_bad_scientific_input(self):
        payload=self.payload();payload['method']='mie'
        with patch.dict(sys.modules,{'miepython':None}),self.assertRaises(RuntimeDependencyError):simulate_scattering(payload)
        from aero_psi_backend import CatalogHandler
        handler=object.__new__(CatalogHandler);body=json.dumps(payload).encode();handler.path='/api/v1/models/scattering';handler.headers={'Content-Length':str(len(body))};handler.rfile=io.BytesIO(body);handler.catalog={}
        sent=[];handler.error_json=lambda *args:sent.append(args)
        with patch.dict(sys.modules,{'miepython':None}):handler.do_POST()
        self.assertEqual(sent[0][0],503);self.assertEqual(sent[0][1],'scattering_unavailable')

if __name__=='__main__':unittest.main()
