import math
import unittest
from aero_psi.coagulation import ScenarioInputError
from aero_psi.model_studies import uncertainty, calibrate, convergence


class ModelStudiesTests(unittest.TestCase):
    def test_seed_reproduces_quantiles_and_parameters(self):
        p={'scenario':{'brownian_regime':'disabled','residence_time_s':1,'section_count':8,'output_points':3},'samples':4,'seed':17,'uncertain_inputs':{'initial_number_concentration_m3':{'low':1e8,'high':1e10,'distribution':'log_uniform','reference':'synthetic bounds'}}}
        a=uncertainty(p); b=uncertainty(p)
        self.assertEqual(a,b)
        q=a['series'][-1]['quantiles']['number_concentration_m3']
        self.assertTrue(1e8<=q['p05']<=q['p50']<=q['p95']<=1e10)
        for member in a['members']:
            self.assertAlmostEqual(member['final']['number_concentration_m3']/member['parameters']['initial_number_concentration_m3'],1)

    def test_zero_width_uncertainty_is_constant(self):
        r=uncertainty({'scenario':{'residence_time_s':0,'section_count':8},'samples':2,'uncertain_inputs':{'initial_number_concentration_m3':{'low':1e8,'high':1e8,'reference':'fixed value'}}})
        q=r['series'][0]['quantiles']['number_concentration_m3']
        self.assertEqual(q['p05'],q['p95'])

    def test_fit_recovers_known_dilution_rate_on_grid_and_holdout(self):
        def observation(t): return {'time_s':t,'value':1e10*math.exp(-.02*t),'source':{'reference':'analytic exponential dilution benchmark'}}
        result=calibrate({'scenario':{'brownian_regime':'disabled','section_count':8,'residence_time_s':10,'output_points':11,'stability_fraction':.001},'parameter':'dilution_rate_s','lower':0,'upper':.04,'candidate_count':5,'observable':'number_concentration_m3','observations':[observation(t) for t in (0,2,4,6)],'validation_observations':[observation(t) for t in (7,9)]})
        self.assertAlmostEqual(result['best_value'],.02)
        self.assertFalse(result['boundary_optimum'])
        self.assertLess(result['held_out_validation']['rmse']/1e10,.001)

    def test_holdout_overlap_is_rejected(self):
        rows=[{'time_s':t,'value':1e10,'source':{'reference':'synthetic'}} for t in (0,1)]
        with self.assertRaises(ScenarioInputError):
            calibrate({'scenario':{'residence_time_s':1,'section_count':8},'parameter':'dilution_rate_s','lower':0,'upper':.01,'candidate_count':3,'observable':'number_concentration_m3','observations':rows,'validation_observations':rows})

    def test_refinement_uses_finest_grid_and_smallest_step(self):
        r=convergence({'scenario':{'residence_time_s':1,'output_points':2},'section_counts':[16,8],'stability_fractions':[.01,.04]})
        self.assertEqual(r['reference'],{'section_count':16,'stability_fraction':.01})
        self.assertEqual(len(r['results']),4)
        self.assertEqual(r['results'][-1]['relative_difference_to_reference']['number_concentration_m3'],0)

    def test_unsupported_and_fractional_requests_fail(self):
        for override in ({'samples':2.5},{'seed':True},{'uncertain_inputs':{'charge':{'low':0,'high':1,'reference':'test'}}}):
            p={'samples':2,'uncertain_inputs':{'gravity_m_s2':{'low':0,'high':1,'reference':'test'}},**override}
            with self.assertRaises(ScenarioInputError): uncertainty(p)
