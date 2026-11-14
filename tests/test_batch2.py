import csv
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import tempfile
import unittest
from decimal import Decimal, localcontext
from unittest.mock import patch
from aero_psi_observed import analyze, export_analysis, compare
from aero_psi_kernels import _fuchs_delta, physics
from aero_psi_coagulation import _inputs, BOLTZMANN_J_PER_K
from aero_psi_model_studies import domain_study
from aero_psi_sectional import simulate_sectional
from aero_psi_scattering import simulate_scattering, coupled_scattering

class ObservedTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
        (self.root/'DATA').mkdir(); (self.root/'DATA/source.xls').write_bytes(b'fixture')
        rows=[{'source_row':i+2,'values':{'Time':i,'voltage':v}} for i,v in enumerate([1,1,1,3,1])]
        with gzip.open(self.root/'rows.gz','wt') as f:
            for r in rows: f.write(json.dumps(r)+'\n')
        self.manifest=self.root/'manifest.json'
        self.manifest.write_text(json.dumps({'records':[{'status':'imported','source_path':'source.xls','source_sha256':hashlib.sha256(b'fixture').hexdigest(),'derived_path':'rows.gz','worksheet':'sheet','group':'PSI101','join_status':'unmatched','analysis':{'available_signals':{'scatter_voltage':'voltage'}}}]}))
        self.payload={'source_path':'source.xls','signal':'scatter_voltage','confirmed':True,'time_unit':'s','baseline_rows':[2,3],'event_rows':[4,6],'threshold':{'kind':'absolute','value':1,'reference':'synthetic threshold'}}
    def tearDown(self): self.temp.cleanup()
    def test_hand_computed_triangle_auc_and_threshold(self):
        r=analyze(self.payload,self.manifest,self.root)
        self.assertEqual(r['metrics']['baseline'],1); self.assertEqual(r['metrics']['signed_auc'],2)
        self.assertEqual(r['metrics']['duration_above_absolute_deviation_threshold_s'],1)
        self.assertEqual(r['metrics']['time_to_extreme_s'],1)
        self.assertEqual(len(list(csv.reader(io.StringIO(export_analysis(r)['csv'])))),4)
    def test_negative_polarity_preserved(self):
        with gzip.open(self.root/'rows.gz','rt') as f: rows=[json.loads(l) for l in f]
        rows[3]['values']['voltage']=-1
        with gzip.open(self.root/'rows.gz','wt') as f:
            for r in rows:f.write(json.dumps(r)+'\n')
        r=analyze(self.payload,self.manifest,self.root)
        self.assertEqual(r['metrics']['signed_auc'],-2); self.assertEqual(r['metrics']['signed_extreme_deviation'],-2)
    def test_maximum_time_interval_excludes_integration(self):
        r=analyze({**self.payload,'max_interval_s':.5},self.manifest,self.root)
        self.assertIsNone(r['metrics']['signed_auc'])
        self.assertEqual(r['metrics']['excluded_adjacent_intervals'],2)
    def test_cross_run_comparison_stays_blocked(self):
        (self.root/'DATA/other.xls').write_bytes(b'fixture')
        manifest=json.loads(self.manifest.read_text());manifest['records'].append({**manifest['records'][0],'source_path':'other.xls'})
        self.manifest.write_text(json.dumps(manifest))
        result=compare({'left':self.payload,'right':{**self.payload,'source_path':'other.xls'}},self.manifest,self.root)
        self.assertEqual(result['status'],'blocked');self.assertIsNone(result['metric_differences'])
    def test_confirmation_missing_and_stale_source(self):
        with self.assertRaises(ValueError): analyze({**self.payload,'confirmed':False},self.manifest,self.root)
        (self.root/'DATA/source.xls').write_bytes(b'changed')
        with self.assertRaises(ValueError): analyze(self.payload,self.manifest,self.root)
    def test_missing_data_not_bridged(self):
        with gzip.open(self.root/'rows.gz','rt') as f: rows=[json.loads(l) for l in f]
        rows[3]['values']['voltage']=-10
        with gzip.open(self.root/'rows.gz','wt') as f:
            for r in rows:f.write(json.dumps(r)+'\n')
        r=analyze(self.payload,self.manifest,self.root)
        self.assertIsNone(r['metrics']['signed_auc']); self.assertAlmostEqual(r['metrics']['missing_fraction'],1/3)

class KernelBenchmarks(unittest.TestCase):
    def test_stable_delta_against_60_digit_direct_expression(self):
        with localcontext() as ctx:
            ctx.prec=60
            for ratio in ('1e-10','0.001','1','1000000'):
                d=Decimal('1e-7'); l=d*Decimal(ratio)
                reference=((d+l)**3-(d*d+l*l)*(d*d+l*l).sqrt())/(3*d*l)-d
                self.assertAlmostEqual(_fuchs_delta(float(d),float(l))/float(reference),1,delta=1e-12)
    def test_fuchs_independent_high_precision_reference_values(self):
        # Direct published Fuchs expression evaluated separately with 60-digit Decimal arithmetic.
        p=_inputs({})
        for ds,expected in [([1e-8,1e-7],2.3832010289696279e-14),([1e-7,1e-6],4.7673375607419316e-15)]:
            matrix,_,_=physics({'brownian_regime':'fuchs','gas_mean_free_path_m':65e-9},p,ds)
            self.assertAlmostEqual(matrix[0][1]/expected,1,delta=1e-12)

    def test_continuum_equal_size_and_shear_reference(self):
        p=_inputs({}); d=1e-7
        kernel,_,_=physics({},p,[d]); self.assertAlmostEqual(kernel[0][0]/(8*BOLTZMANN_J_PER_K*p['gas_temperature_k']/(3*p['gas_viscosity_pa_s'])),1)
        k,_,_=physics({'brownian_regime':'disabled','shear_rate_s':4},p,[d]); self.assertAlmostEqual(k[0][0]/(4*(2*d)**3/6),1)
    def test_fuchs_free_molecular_limit(self):
        p=_inputs({}); ds=[1e-8,2e-8]
        k,_,_=physics({'brownian_regime':'fuchs','gas_mean_free_path_m':1e-2},p,ds)
        speeds=[math.sqrt(8*BOLTZMANN_J_PER_K*p['gas_temperature_k']/(math.pi*p['particle_density_kg_m3']*math.pi*d**3/6)) for d in ds]
        reference=math.pi*(sum(ds))**2*math.hypot(*speeds)/4
        self.assertAlmostEqual(k[0][1]/reference,1,delta=1e-4)
    def test_population_number_against_constant_kernel_analytic(self):
        coefficient=1e-15; n0=1e10; duration=100
        def constant(raw,p,ds):
            _,losses,meta=physics(raw,p,ds)
            return [[coefficient]*len(ds) for _ in ds],losses,meta
        with patch('aero_psi_sectional.physics',side_effect=constant):
            r=simulate_sectional({'initial_number_concentration_m3':n0,'residence_time_s':duration,'section_count':32,'output_points':5,'stability_fraction':.001})
        exact=n0/(1+.5*coefficient*n0*duration)
        self.assertAlmostEqual(r['series'][-1]['number_concentration_m3']/exact,1,delta=.001)
    def test_domain_shape_distance(self):
        r=domain_study({'scenario':{'residence_time_s':0},'domains':[{'diameter_min_m':1e-8,'diameter_max_m':1e-6,'section_count':8},{'diameter_min_m':1e-8,'diameter_max_m':1e-6,'section_count':16}]})
        self.assertEqual(r['results'][1]['number_cdf_distance_log_diameter'],0)

class ScatteringTests(unittest.TestCase):
    def payload(self,d=2*550e-9/math.pi,n=1e8):
        return {'wavelength_vacuum_m':550e-9,'particle_refractive_index':{'n':1.5,'k':.01,'reference':'synthetic benchmark'},'angles_deg':[0,90,180],'distribution':{'diameters_m':[d],'number_per_bin_m3':[n],'source':{'reference':'synthetic monodisperse population'}}}
    def test_published_absorbing_sphere_benchmark(self):
        # miepython efficiencies_mx docs: m=1.5-0.01j, x=2.
        r=simulate_scattering(self.payload()); b=r['bins'][0]
        self.assertAlmostEqual(b['q_ext'],1.812597,delta=5e-7); self.assertAlmostEqual(b['q_sca'],1.724396,delta=5e-7)
        self.assertAlmostEqual(b['q_abs']+b['q_sca'],b['q_ext'],delta=1e-12)
    def test_phase_solid_angle_normalization(self):
        import numpy as np
        nodes,weights=np.polynomial.legendre.leggauss(100)
        p=self.payload(); p['angles_deg']=sorted(float(math.degrees(math.acos(x))) for x in nodes)
        r=simulate_scattering(p)
        self.assertAlmostEqual(2*math.pi*sum(w*v for w,v in zip(weights[::-1],r['phase_function_sr_inv'])),1,delta=1e-9)
    def test_rayleigh_limit_and_applicability(self):
        p=self.payload(d=2e-9);p['particle_refractive_index']['k']=0
        a=simulate_scattering(p);b=simulate_scattering({**p,'method':'rayleigh'})
        self.assertAlmostEqual(a['bins'][0]['q_sca']/b['bins'][0]['q_sca'],1,delta=.001)
        with self.assertRaises(ValueError):simulate_scattering({**self.payload(),'method':'rayleigh'})
    def test_concentration_scaling_and_zero(self):
        a=simulate_scattering(self.payload(n=1e8));b=simulate_scattering(self.payload(n=2e8));z=simulate_scattering(self.payload(n=0))
        self.assertAlmostEqual(b['coefficients']['scattering_m_inv']/a['coefficients']['scattering_m_inv'],2)
        self.assertEqual(a['phase_function_sr_inv'],b['phase_function_sr_inv']);self.assertIsNone(z['phase_function_sr_inv'])
    def test_coupled_static_population_unchanged(self):
        optics=self.payload();del optics['distribution']
        r=coupled_scattering({'scenario':{'brownian_regime':'disabled','section_count':8,'output_points':3,'residence_time_s':1},'optics':optics})
        self.assertEqual(r['series'][0]['coefficients'],r['series'][-1]['coefficients'])

class AdditionalPhysicsTests(unittest.TestCase):
    def test_growth_grid_refinement_reduces_known_diameter_error(self):
        errors=[]
        for count in (16,64):
            r=simulate_sectional({'brownian_regime':'disabled','initial_median_diameter_m':1e-7,'diameter_growth_rate_m_s':1e-9,'residence_time_s':10,'section_count':count,'output_points':3,'diameter_min_m':5e-8,'diameter_max_m':3e-7})
            errors.append(abs(r['series'][-1]['equivalent_volume_mean_diameter_m']/1.1e-7-1))
        self.assertLess(errors[1],errors[0]); self.assertLess(errors[1],1e-3)
    def test_truncated_lognormal_is_visible(self):
        r=simulate_sectional({'initial_geometric_std_dev':2,'residence_time_s':0,'diameter_min_m':8e-8,'diameter_max_m':1.2e-7})
        self.assertGreater(r['initial_number_fraction_outside_grid'],.5)
        self.assertTrue(any('truncates' in w for w in r['warnings']))
    def test_index_matching_yields_no_scattering(self):
        p=ScatteringTests().payload();p['particle_refractive_index']={'n':1,'k':0,'reference':'index matching test'}
        result=simulate_scattering(p)
        self.assertAlmostEqual(result['coefficients']['scattering_m_inv'],0,delta=1e-20)
    def test_size_parameter_domain_and_roundoff_boundary(self):
        p=ScatteringTests().payload()
        for x in (.001,.1,1,10,100):
            p['distribution']['diameters_m']=[x*p['wavelength_vacuum_m']/math.pi]
            r=simulate_scattering(p)
            self.assertTrue(all(math.isfinite(v) and v>=0 for v in r['coefficients'].values()))
        p['distribution']['diameters_m']=[101*p['wavelength_vacuum_m']/math.pi]
        with self.assertRaises(ValueError):simulate_scattering(p)
    def test_invalid_optical_inputs_are_rejected(self):
        p=ScatteringTests().payload()
        for change in ({'wavelength_vacuum_m':float('nan')},{'angles_deg':[90,0]},{'particle_refractive_index':{'n':1.5,'k':-1,'reference':'test'}}):
            with self.assertRaises(ValueError):simulate_scattering({**p,**change})

class Batch2EndpointTests(unittest.TestCase):
    def test_scattering_http_handler_without_starting_server(self):
        from aero_psi_backend import CatalogHandler
        handler=object.__new__(CatalogHandler);body=json.dumps(ScatteringTests().payload()).encode()
        handler.path='/api/v1/models/scattering';handler.headers={'Content-Length':str(len(body))};handler.rfile=io.BytesIO(body)
        handler.catalog={'generated_at':'test','schema_version':1};sent=[];handler.send_json=lambda payload,*args:sent.append(payload)
        handler.do_POST()
        self.assertEqual(sent[0]['data']['model_id'],'sphere_optics_v1')
    def test_si_rejects_unsupplied_optical_parameters(self):
        from aero_psi_investigation import validate_plan
        with self.assertRaises(ValueError):validate_plan([{'tool':'scattering','reason':'Invent properties'}],{})
