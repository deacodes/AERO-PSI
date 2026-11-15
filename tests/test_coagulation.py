import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import aero_psi.coagulation as coagulation
from aero_psi.sectional import simulate_sectional, sensitivity


class CoagulationTests(unittest.TestCase):
    def test_zero_concentration_stays_zero_and_conserves_mass(self):
        result = coagulation.simulate({"initial_number_concentration_m3": 0, "residence_time_s": 60})
        self.assertEqual(result["summary"]["final_number_concentration_m3"], 0)
        self.assertTrue(result["conservation_check"]["passes_floating_point_tolerance"])

    def test_number_solution_matches_constant_kernel_analytic_solution(self):
        result = coagulation.simulate({"initial_number_concentration_m3": 1e12, "gas_temperature_k": 300, "gas_viscosity_pa_s": 1.8e-5, "residence_time_s": 10, "output_points": 2})
        k = result["kernel"]["brownian_equal_size_m3_s"]
        expected = 1e12 / (1 + 0.5 * k * 1e12 * 10)
        self.assertTrue(math.isclose(result["summary"]["final_number_concentration_m3"], expected, rel_tol=1e-14))
        self.assertTrue(result["conservation_check"]["passes_floating_point_tolerance"])

    def test_invalid_input_is_rejected(self):
        with self.assertRaises(coagulation.ScenarioInputError):
            coagulation.simulate({"sticking_efficiency": 1.1})

    def test_regime_assessment_warns_when_continuum_is_not_supported(self):
        result = coagulation.simulate({"initial_median_diameter_m": 100e-9, "gas_mean_free_path_m": 65e-9})
        self.assertEqual(result["regime_assessment"]["state"], "outside_or_near_continuum_limit")

    def test_sectional_solver_conserves_volume(self):
        result=simulate_sectional({"initial_number_concentration_m3":1e12,"residence_time_s":60,"section_count":32})
        self.assertTrue(result["conservation_check"]["passes_floating_point_tolerance"])
        self.assertLess(result["series"][-1]["number_concentration_m3"],result["series"][0]["number_concentration_m3"])

    def test_sectional_equal_size_case_agrees_with_analytic_solution(self):
        payload={"initial_number_concentration_m3":1e12,"initial_median_diameter_m":100e-9,"residence_time_s":60,"section_count":128,"output_points":3,"stability_fraction":0.005}
        analytic=coagulation.simulate(payload)["summary"]["final_number_concentration_m3"]
        sectional=simulate_sectional(payload)["series"][-1]["number_concentration_m3"]
        self.assertLess(abs(sectional-analytic)/analytic,3e-5)

    def test_sectional_width_preserves_volume(self):
        result=simulate_sectional({"initial_number_concentration_m3":1e10,"initial_median_diameter_m":100e-9,"initial_geometric_std_dev":1.8,"residence_time_s":60,"section_count":64})
        self.assertTrue(result["conservation_check"]["passes_floating_point_tolerance"])
        self.assertGreater(result["solver"]["initial_diameter_grid_m"][1],100e-9)

    def test_sectional_sensitivity_reports_each_requested_grid(self):
        result=sensitivity({"residence_time_s":1,"section_counts":[16,32]})
        self.assertEqual([item["section_count"] for item in result["results"]],[16,32])


if __name__ == "__main__":
    unittest.main()
