import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import aero_psi_copilot as copilot


class CopilotTests(unittest.TestCase):
    def setUp(self):
        self.catalog={
            "investigations":[{"group":"PSI101","source_path":"PSI101/meta/i_Investigation.txt","title":"SAME-R smoke","objective":"Measure smoke aerosol response","platform":"ISS","research_area":"Combustion","measurement_family":"smoke aerosol"}],
            "normalized_experiments":[{"source_path":"PSI101/table.csv","source_row":2,"fields":{"material_or_fuel":{"value":"Kapton"},"flow":{"value":"8.1"}}}],
        }

    def test_retrieval_keeps_exact_csv_path_and_row(self):
        records=copilot.retrieve(self.catalog,"Kapton flow")
        table_record=next(record for record in records if record["id"]=="table:PSI101/table.csv:2")
        self.assertEqual(table_record["source_row"],2)
        self.assertEqual(table_record["source_range"],"row 2")

    def test_investigation_hyphen_spelling_matches_archive_path(self):
        records=copilot.retrieve(self.catalog,"What PSI-101 smoke evidence exists?")
        self.assertTrue(any(record["id"]=="investigation:PSI101" for record in records))
        self.assertTrue(all(record["group"]=="PSI101" for record in records))

    def test_disabled_mode_returns_cited_evidence_fallback(self):
        before=os.environ.get("AERO_PSI_COPILOT_ENABLED")
        os.environ["AERO_PSI_COPILOT_ENABLED"]="false"
        try:
            answer=copilot.ask(self.catalog,"What Kapton flow exists?")
        finally:
            if before is None: os.environ.pop("AERO_PSI_COPILOT_ENABLED",None)
            else: os.environ["AERO_PSI_COPILOT_ENABLED"]=before
        self.assertEqual(answer["mode"],"evidence_only_fallback")
        self.assertTrue(answer["sources"])

    def test_invalid_question_is_rejected(self):
        with self.assertRaises(ValueError): copilot.ask(self.catalog,"")

    def test_invalid_model_citation_is_withheld(self):
        checked, warning=copilot._validate_response({"observed_in_source":[{"claim":"x","source_ids":["outside"]}],"model_result":[],"unknown_or_limitation":[],"sources":[]},{"inside"})
        self.assertIsNone(checked)
        self.assertIn("unverifiable",warning)

    def test_verified_coagulation_point_fallback_is_bounded(self):
        before=os.environ.get("AERO_PSI_COPILOT_ENABLED")
        os.environ["AERO_PSI_COPILOT_ENABLED"]="false"
        try:
            answer=copilot.interpret_point(self.catalog,{"kind":"coagulation_point","point_index":1,"scenario":{"initial_number_concentration_m3":1e9,"initial_median_diameter_m":100e-9,"initial_geometric_std_dev":1.2,"residence_time_s":10,"section_count":16,"output_points":3}})
        finally:
            if before is None: os.environ.pop("AERO_PSI_COPILOT_ENABLED",None)
            else: os.environ["AERO_PSI_COPILOT_ENABLED"]=before
        self.assertEqual(answer["mode"],"verified_context_fallback")
        self.assertEqual(answer["kind"],"coagulation_point")
        self.assertIn("Model scenario only",answer["limitations"][0])
        self.assertEqual(answer["sources"][0]["source_path"],"aero_psi_sectional.py")


if __name__ == "__main__": unittest.main()
