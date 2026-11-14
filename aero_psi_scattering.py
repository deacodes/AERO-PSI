"""Single-scattering homogeneous-sphere forward optics, never detector voltage.

miepython 3.3.1, https://miepython.readthedocs.io/en/latest/
Phase normalization: integral over 4*pi solid angle = 1.
"""
import math
from aero_psi_processes import finite, distribution
from aero_psi_coagulation import ScenarioInputError


def _optics(payload):
    wavelength=finite(payload.get('wavelength_vacuum_m'),'wavelength_vacuum_m',1e-9,1e-3)
    medium=finite(payload.get('medium_refractive_index',1),'medium_refractive_index',.1,5)
    index=payload.get('particle_refractive_index')
    if not isinstance(index,dict): raise ScenarioInputError('Supply particle_refractive_index with n, k and reference')
    n=finite(index.get('n'),'refractive index n',.01,10); k=finite(index.get('k'),'absorption index k',0,10)
    if not isinstance(index.get('reference'),str) or not index['reference'].strip(): raise ScenarioInputError('Optical properties require a source or explicit assumption reference')
    angles=payload.get('angles_deg')
    if not isinstance(angles,list) or not 2<=len(angles)<=361: raise ScenarioInputError('Supply 2–361 angles in degrees')
    angles=[finite(a,'angle',0,180) for a in angles]
    if any(b<=a for a,b in zip(angles,angles[1:])): raise ScenarioInputError('Angles must increase strictly')
    return wavelength,medium,n,k,angles


def simulate_scattering(payload):
    wavelength,medium,n,k,angles=_optics(payload)
    ds,ns,source=distribution(payload.get('distribution'),'distribution')
    if len(ds)>128: raise ScenarioInputError('Optical distribution limit is 128 bins')
    if any(v>1e30 for v in ns): raise ScenarioInputError('Bin concentration exceeds supported numerical range')
    method=payload.get('method','mie')
    if method not in ('mie','rayleigh'): raise ScenarioInputError('method must be mie or rayleigh')
    engine={'name':'analytic Rayleigh sphere','version':'1.0'}
    if method=='mie':
        try:
            import miepython
        except ImportError as exc:
            from aero_psi_runtime import RuntimeDependencyError
            raise RuntimeDependencyError('The running server cannot load its Mie scattering library. Restart AERO-PSI with the project environment; downloading a requirements file will not fix this running process.') from exc
        engine={'name':'miepython','version':miepython.__version__}
    relative=complex(n,-k)/medium
    mu=[math.cos(math.radians(angle)) for angle in angles]
    bins=[]; beta=[0.0]*len(angles); sca=ext=absorption=0.0
    for d,count in zip(ds,ns):
        x=math.pi*d*medium/wavelength
        if x>100*(1+1e-12) or abs(relative)*x>1000*(1+1e-12): raise ScenarioInputError('Optical size parameter exceeds the supported computational domain (x <= 100, |m|x <= 1000)')
        area=math.pi*d*d/4
        if method=='rayleigh':
            if x>.1*(1+1e-12) or abs(relative)*x>.1*(1+1e-12): raise ScenarioInputError('Rayleigh requires both x <= 0.1 and |m|x <= 0.1; use Mie')
            polar=(relative*relative-1)/(relative*relative+2)
            qsca=8*x**4*abs(polar)**2/3
            qabs=max(0.0,-4*x*polar.imag); qext=qsca+qabs
            phase=[3*(1+float(u)**2)/(16*math.pi) for u in mu]
        else:
            qext,qsca,_,_=miepython.efficiencies_mx(relative,x)
            qext=float(qext); qsca=float(qsca); qabs=qext-qsca
            if qabs < -1e-9*max(1,qext): raise ScenarioInputError('Mie solution violates passive absorption tolerance')
            qabs=max(0.0,qabs)
            import numpy as np
            phase=[float(v) for v in miepython.i_unpolarized(relative,x,np.asarray(mu),norm='one')] if qsca>0 else [0.0]*len(angles)
        csca=qsca*area; cext=qext*area; cabs=qabs*area
        for i,p in enumerate(phase): beta[i]+=count*csca*p
        sca+=count*csca; ext+=count*cext; absorption+=count*cabs
        bins.append({'diameter_m':d,'number_per_bin_m3':count,'size_parameter':x,'q_sca':qsca,'q_abs':qabs,'q_ext':qext,'c_sca_m2':csca,'c_abs_m2':cabs,'c_ext_m2':cext})
    phase=[b/sca for b in beta] if sca else None
    return {'classification':'theoretical single-scattering sphere model; not measured intensity or detector voltage','model_id':'sphere_optics_v1','engine':engine,'method':method,'inputs':payload,'distribution_source':source,
            'assumptions':['Homogeneous compact spheres; independent single scattering; nonabsorbing surrounding medium.','Unpolarized incident light; no detector solid angle, gain, saturation, or calibration.','Vacuum wavelength; particle index is absolute n with nonnegative absorption k. Internal relative index uses n-ik convention.','Nonspherical soot/aggregates and multiple scattering are excluded.'],
            'units':{'coefficients':'m^-1','angular_scattering_coefficient':'m^-1 sr^-1','phase_function':'sr^-1'},
            'coefficients':{'scattering_m_inv':sca,'absorption_m_inv':absorption,'extinction_m_inv':ext},'angles_deg':angles,'angular_scattering_coefficient_m_inv_sr_inv':beta,'phase_function_sr_inv':phase,'phase_normalization':'integral over 4*pi = 1 when scattering > 0; undefined for zero scattering','bins':bins,
            'warnings':['Optical-property references are user supplied and not independently verified.','No comparison to recorded detector voltage or inference of particle size is made.']}


def coupled_scattering(payload):
    from aero_psi_sectional import simulate_sectional
    scenario=payload.get('scenario'); optics=payload.get('optics')
    if not isinstance(scenario,dict) or not isinstance(optics,dict): raise ScenarioInputError('Supply scenario and optics objects')
    if 'distribution' in optics: raise ScenarioInputError('Coupled distributions come from the solver; omit optics.distribution')
    if scenario.get('section_count',64)>64 or scenario.get('output_points',61)>21: raise ScenarioInputError('Coupled study is limited to 64 bins and 21 output times; specify output_points')
    result=simulate_sectional(scenario); trajectory=[]
    if result['initial_number_fraction_outside_grid']>1e-5: raise ScenarioInputError('Initial distribution extends outside the grid; widen the domain before optical coupling')
    if result['conservation_check']['overflow_volume_fraction']>1e-5 or result['physics']['prescribed_processes']['underflow_volume_m3_m3']>0:
        raise ScenarioInputError('Widen the size grid: unresolved boundary material prevents interpreting coupled optics')
    if not result['conservation_check']['passes_floating_point_tolerance']: raise ScenarioInputError('Coagulation budget check failed')
    for point in result['series']:
        dist={**point['distribution'],'source':{'reference':'Computed '+result['model_id']+' at t='+str(point['time_s'])+' s; scenario, not measurement'}}
        optical=simulate_scattering({**optics,'distribution':dist})
        trajectory.append({'time_s':point['time_s'],'coefficients':optical['coefficients'],'angular_scattering_coefficient_m_inv_sr_inv':optical['angular_scattering_coefficient_m_inv_sr_inv'],'phase_function_sr_inv':optical['phase_function_sr_inv']})
    return {'classification':'coupled coagulation-to-optics scenario; no NASA experimental validation','coagulation':result,'optical_configuration':optics,'optical_engine':optical['engine'],'angles_deg':optical['angles_deg'],'units':optical['units'],'series':trajectory,'warnings':result['warnings']+optical['warnings'],'assumptions':optical['assumptions']}
