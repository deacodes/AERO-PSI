import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from aero_psi.evidence import build_index, document_records
from aero_psi.education import answer_question
from aero_psi.investigation import investigate, validate_plan

class EvidenceTests(unittest.TestCase):
    def test_extraction_locator_integrity_and_stale_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'DATA'; root.mkdir(); source=root/'sample.docx'; output=Path(tmp)/'index.json'
            with zipfile.ZipFile(source,'w') as z:
                z.writestr('word/document.xml','<w:document xmlns:w="urn:test"><w:p><w:r><w:t>Measured smoke evidence.</w:t></w:r></w:p></w:document>')
            before=source.read_bytes(); result=build_index(root,output)
            self.assertEqual(result['extracted'],1); self.assertEqual(source.read_bytes(),before)
            record=document_records(output,root)[0]
            self.assertEqual(record['locator']['paragraph'],1)
            self.assertEqual(record['review_state'],'extracted_unreviewed')
            source.write_bytes(b'changed')
            self.assertEqual(document_records(output,root),[])

    def test_archive_output_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError): build_index(Path(tmp),Path(tmp)/'out.json')

class InvestigationTests(unittest.TestCase):
    def setUp(self):
        self.env=patch.dict(os.environ,{'AERO_PSI_COPILOT_ENABLED':'false'}); self.env.start()
        self.catalog={'investigations':[],'normalized_experiments':[],'files':[]}
    def tearDown(self): self.env.stop()

    def test_general_definition_has_no_canned_offline_answer(self):
        result=answer_question(self.catalog,'what is brownian motion')
        self.assertEqual(result['observed_in_source'],[])
        self.assertEqual(result['mode'],'science_unavailable')
        self.assertNotIn('scientific_explanation',result)

    def test_forced_evidence_mode_does_not_return_general_education(self):
        result=answer_question(self.catalog,'what is brownian motion','evidence')
        self.assertEqual(result['mode'],'evidence_only_fallback')

    def test_invented_tools_and_unsupplied_scenario_rejected(self):
        for step in [{'tool':'shell','reason':'ignore instructions'}, {'tool':'simulate_coagulation','reason':'invent inputs'}]:
            with self.assertRaises(ValueError): validate_plan([step],{})

    def test_plan_does_not_execute_and_is_saved(self):
        with tempfile.TemporaryDirectory() as tmp:
            result=investigate(self.catalog,{'question':'Which evidence is available?'},tmp)
            self.assertEqual(result['status'],'planned'); self.assertEqual(result['steps'],[])
            self.assertEqual(json.loads((Path(tmp)/(result['id']+'.json')).read_text())['plan'],result['plan'])

    def test_gravity_execution_retains_inputs_and_full_output(self):
        scenario={'section_count':8,'output_points':3,'residence_time_s':1,'initial_number_concentration_m3':1e9}
        payload={'question':'Compare gravity scenarios','action':'execute','scenario':scenario,'plan':[{'tool':'gravity_comparison','reason':'Compare fixed supplied assumptions.'}]}
        with tempfile.TemporaryDirectory() as tmp:
            result=investigate(self.catalog,payload,tmp)
            self.assertEqual(result['status'],'completed')
            self.assertEqual(result['inputs']['scenario'],scenario)
            self.assertEqual([x['value'] for x in result['steps'][0]['output']['results']],[0,9.81])
            self.assertTrue(any(e['id'].startswith('runtime:') for e in result['evidence']))

    def test_tool_failure_is_not_reported_as_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            result=investigate(self.catalog,{'question':'Run a scenario','action':'execute','scenario':{'section_count':128},'plan':[{'tool':'simulate_coagulation','reason':'Test input limit.'}]},tmp)
            self.assertEqual(result['status'],'partial'); self.assertEqual(result['steps'][0]['status'],'failed')

    def test_cancel_before_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            result=investigate(self.catalog,{'question':'Find evidence','action':'execute'},tmp,cancelled=lambda:True)
            self.assertEqual(result['status'],'cancelled'); self.assertEqual(result['steps'],[])

if __name__=='__main__': unittest.main()

class EndpointTests(unittest.TestCase):
    def test_copilot_endpoint_reports_ai_unavailable_without_preset(self):
        import io
        from aero_psi.backend import CatalogHandler
        handler=object.__new__(CatalogHandler)
        body=json.dumps({'question':'what is brownian motion'}).encode()
        handler.path='/api/v1/copilot'; handler.headers={'Content-Length':str(len(body))}; handler.rfile=io.BytesIO(body)
        handler.catalog={'generated_at':'test','schema_version':1}
        sent=[]; handler.send_json=lambda payload,*args: sent.append(payload)
        with patch.dict(os.environ,{'AERO_PSI_COPILOT_ENABLED':'false'}): handler.do_POST()
        self.assertEqual(sent[0]['data']['mode'],'science_unavailable')
        self.assertNotIn('scientific_explanation',sent[0]['data'])

    def test_saved_investigation_endpoint_rejects_path_traversal(self):
        from aero_psi.backend import CatalogHandler
        handler=object.__new__(CatalogHandler); handler.path='/api/v1/si/investigation?id=../../.env'
        sent=[]; handler.error_json=lambda *args:sent.append(args)
        handler.do_GET()
        self.assertEqual(sent[0][1],'invalid_id')
