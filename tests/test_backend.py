import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import aero_psi_backend as backend
import aero_psi_ingest as ingest
from aero_psi_ranking import investigation_rankings, run_readiness

class CatalogTests(unittest.TestCase):
    def make_source(self, root):
        meta=root/'PSI101'/'PSI-101_metadata';meta.mkdir(parents=True)
        (meta/'i_Investigation.txt').write_text('Study Identifier\tPSI-101\nStudy Title\tTest Study\nComment[Investigation Acronym]\tSAME-R\nComment[Flight Platform]\tISS\n')
        (root/'PSI101'/'PSI-101_Experimental table_SAME-R.csv').write_text('Sample Type,SAME Test #,Inlet velocity (cm/s)\nKapton,51,8.1\nPyrell,52,\n')
    def test_catalog_preserves_raw_csv_and_provenance(self):
        with tempfile.TemporaryDirectory() as temporary:
            catalog_root=Path(temporary);self.make_source(catalog_root);catalog=backend.build_catalog(catalog_root)
            self.assertEqual(catalog['summary']['file_count'],2);self.assertEqual(catalog['summary']['experimental_record_count'],2);self.assertEqual(catalog['investigations'][0]['investigation_id'],'PSI-101');self.assertEqual(catalog['raw_tables'][0]['rows'][0]['Sample Type'],'Kapton')
            record=catalog['normalized_experiments'][1];self.assertEqual(record['source_row'],3);self.assertEqual(record['fields']['flow']['state'],'missing');self.assertTrue(record['source_sha256'])
            self.assertIn('ambiguous', catalog['value_state_vocabulary'])
    def test_envelope_is_structured(self):
        result=backend.envelope({'ok':True},{'generated_at':'2026-01-01T00:00:00+00:00','schema_version':'1.1'})
        self.assertEqual(result['data'],{'ok':True});self.assertTrue(result['source']['read_only_source']);json.dumps(result)

    def test_ingest_reports_time_and_signal_quality_without_rewriting_values(self):
        headers=["Time","TimeString","TestRunning","ISSDetectorScatterMeasurement(Volts)","TestNumber"]
        rows=[
            {"Time":"1280000000","TimeString":"source-a","TestRunning":"0","ISSDetectorScatterMeasurement(Volts)":"0","TestNumber":"61"},
            {"Time":"1280000001","TimeString":"source-b","TestRunning":"1","ISSDetectorScatterMeasurement(Volts)":"0","TestNumber":"61"},
            {"Time":"1280000001","TimeString":"source-c","TestRunning":"1","ISSDetectorScatterMeasurement(Volts)":"0","TestNumber":"61"},
        ]
        analysis,warnings=ingest.analyze(rows,headers)
        self.assertEqual(analysis["duplicate_timestamps"],1)
        self.assertEqual(analysis["fully_zero_core_signals"],["scatter_voltage"])
        self.assertTrue(analysis["time_start_utc"].endswith("+00:00"))
        self.assertIn("obscuration_voltage",analysis["absent_core_signals"])
        self.assertIn("Fully-zero", " ".join(warnings))

    def test_investigation_ranking_is_derived_and_explained(self):
        catalog={
            "investigations":[
                {"group":"PSI101","title":"Direct smoke","measurement_family":"smoke aerosol and detector response","platform":"ISS","objective":"Smoke"},
                {"group":"FLEX","title":"Droplet context","measurement_family":"droplet extinction","platform":"ISS"},
            ],
            "files":[
                {"investigation_group":"PSI101","file_role":"raw or derived run workbook"},
                {"investigation_group":"PSI101","file_role":"experimental table"},
                {"investigation_group":"FLEX","file_role":"supporting document"},
            ],
            "normalized_experiments":[{"source_path":"PSI101/table.csv"}],
        }
        result=investigation_rankings(catalog)
        self.assertEqual(result["items"][0]["group"],"PSI101")
        self.assertIn("structured_condition_depth",result["items"][0]["components"])
        self.assertIn("not scientific quality",result["classification"])

    def test_run_readiness_rewards_event_window_and_signals(self):
        signals={str(i):str(i) for i in range(8)}
        ready=run_readiness({"optical_signal_columns":signals,"event_window":{"test_source_rows":[2,800]},"row_count":2000,"metrics":{name:{"missing_fraction":0.0} for name in signals},"verified_experiment_key":"PSI101:61","warnings":[]})
        review=run_readiness({"optical_signal_columns":{"scatter":"x"},"event_window":{},"row_count":20,"metrics":{"scatter":{"missing_fraction":0.5}},"warnings":["a","b","c","d"]})
        self.assertGreater(ready["score"],80.0)
        self.assertGreater(ready["score"],review["score"])
        self.assertIn("not scientific validity",ready["classification"])
if __name__=='__main__':unittest.main()
