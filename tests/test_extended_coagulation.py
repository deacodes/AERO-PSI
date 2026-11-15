import unittest
from aero_psi.sectional import simulate_sectional
from aero_psi.kernels import physics
from aero_psi.coagulation import _inputs

class ExtendedPhysicsTests(unittest.TestCase):
    def test_prescribed_source_number_and_volume(self):
        import math
        r=simulate_sectional({'initial_number_concentration_m3':0,'brownian_regime':'disabled','residence_time_s':10,'particle_sources':[{'diameter_m':1e-7,'number_rate_m3_s':1e6,'reference':'synthetic test'}]})
        self.assertAlmostEqual(r['series'][-1]['number_concentration_m3']/1e7,1)
        self.assertAlmostEqual(r['series'][-1]['total_volume_concentration_m3_per_m3']/(1e7*math.pi*1e-21/6),1)
        self.assertTrue(r['conservation_check']['passes_floating_point_tolerance'])

    def test_growth_and_evaporation_budgets(self):
        for rate in (1e-10,-1e-10):
            r=simulate_sectional({'brownian_regime':'disabled','diameter_growth_rate_m_s':rate,'residence_time_s':2,'section_count':16})
            self.assertTrue(r['conservation_check']['passes_floating_point_tolerance'])
            exchange=r['physics']['prescribed_processes']['vapor_exchange_volume_m3_m3']
            self.assertGreater(exchange*rate,0)

    def test_measured_distribution_preserves_number_and_volume(self):
        import math
        ds=[5e-8,1e-7,2e-7]; ns=[1e5,2e5,3e5]
        r=simulate_sectional({'residence_time_s':0,'initial_distribution':{'diameters_m':ds,'number_per_bin_m3':ns,'source':{'reference':'synthetic known bin totals'}}})
        self.assertAlmostEqual(r['initial']['number_concentration_m3']/sum(ns),1)
        self.assertAlmostEqual(r['initial']['total_volume_concentration_m3_per_m3']/sum(n*math.pi*d**3/6 for n,d in zip(ns,ds)),1)

    def test_comparison_and_sweep(self):
        from aero_psi.model_studies import compare_observations, sweep
        r=compare_observations({'scenario':{'brownian_regime':'disabled','residence_time_s':1},'observable':'number_concentration_m3','observations':[{'time_s':t,'value':1e10,'source':{'reference':'synthetic constant population'}} for t in (0,1)]})
        self.assertLess(r['rmse'],1e-4)
        self.assertEqual(len(sweep({'scenario':{'residence_time_s':0},'values':[0,9.81]})['results']),2)

    def test_fractional_bins_rejected(self):
        from aero_psi.coagulation import ScenarioInputError
        with self.assertRaises(ScenarioInputError): simulate_sectional({'section_count':16.5})

    def test_kernel_symmetry_and_zero_gravity(self):
        p=_inputs({})
        matrix,losses,meta=physics({'brownian_regime':'fuchs'},p,[1e-8,1e-7,1e-6])
        self.assertEqual(meta['settling_velocities_m_s'],[0,0,0])
        for i in range(3):
            for j in range(3):
                self.assertGreater(matrix[i][j],0)
                self.assertAlmostEqual(matrix[i][j],matrix[j][i],delta=1e-25)

    def test_settling_collisions_depend_on_gravity(self):
        p=_inputs({})
        zero,_,_=physics({'brownian_regime':'disabled'},p,[1e-7,1e-6])
        earth,_,_=physics({'brownian_regime':'disabled','gravity_m_s2':9.81},p,[1e-7,1e-6])
        self.assertEqual(zero[0][1],0)
        self.assertGreater(earth[0][1],0)
        self.assertEqual(earth[1][1],0)

    def test_loss_budget_and_distribution(self):
        import math
        r=simulate_sectional({'brownian_regime':'disabled','dilution_rate_s':.01,'residence_time_s':10,'section_count':16})
        self.assertTrue(r['conservation_check']['passes_floating_point_tolerance'])
        n=r['series'][-1]['number_concentration_m3']
        self.assertAlmostEqual(n/r['initial']['number_concentration_m3'],math.exp(-.1),delta=.002)
        self.assertAlmostEqual(sum(r['series'][-1]['distribution']['number_per_bin_m3']),n)
        self.assertGreater(r['removed_volume_m3_m3'],0)
