import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aero_psi_atlas import coverage, gaps, condition_gaps, suggested_measurement, conditions
from aero_psi_optical import summary


class OpticalAtlasTests(unittest.TestCase):
    def test_coverage_and_catalog_gap_are_explicit(self):
        catalog={"files":[{"investigation_group":"PSI101","material_candidate":"Kapton","measurement_family":"smoke aerosol and detector response","data_level":"direct raw or derived measurements","source_path":"PSI101/Kapton/run.xls"}]}
        cell=coverage(catalog)[0]
        self.assertEqual(cell["coverage_state"],"direct_raw_or_derived_measurements")
        self.assertEqual(gaps(catalog), [])

    def test_optical_summary_rejects_unknown_run(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"manifest.json";path.write_text('{"records": []}')
            with self.assertRaises(KeyError): summary(path,"PSI101/not-here.xls")

    def test_condition_gaps_and_proposal_are_transparent(self):
        fields=lambda material,flow:{"material_or_fuel":{"value":material,"state":"observed"},"flow":{"value":flow,"state":"observed"},"duration_or_aging":{"value":"1","state":"observed"}}
        catalog={"normalized_experiments":[{"source_path":"PSI101/table.csv","source_sha256":"x","source_row":2,"fields":fields("Kapton","5")},{"source_path":"PSI101/table.csv","source_sha256":"x","source_row":3,"fields":fields("Kapton","10")} ]}
        row=dict(catalog['normalized_experiments'][0]); row['source_row']=4
        row['fields']=fields('Kapton','5'); row['fields']['duration_or_aging']['value']='2'
        catalog['normalized_experiments'].append(row)
        result=condition_gaps(catalog,"PSI101")
        self.assertEqual(len(result["gaps"]),1)
        proposal=suggested_measurement(result["gaps"][0])
        self.assertEqual(proposal["classification"],"proposal, not a scientific recommendation or finding")

    def test_conditions_preserve_unknown_states_for_absent_investigation_fields(self):
        catalog={"investigations":[{"group":"PSI101","platform":"ISS","title":"Test"}],"normalized_experiments":[{"source_path":"PSI101/table.csv","source_sha256":"x","source_row":2,"fields":{}}]}
        row=conditions(catalog)[0]
        self.assertEqual(row["platform_context"],"ISS")
        self.assertEqual(row["conditions"]["platform_gravity"]["state"],"unknown")
        self.assertEqual(row["conditions"]["geometry_flame_type"]["state"],"unknown")
