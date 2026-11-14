"""Sphere collision kernels in SI units; prescribed homogeneous gas conditions.

Fuchs limiting-sphere interpolation: Seinfeld & Pandis, ch. 13;
https://aerosol.earthsci.dev/stable/dynamics/ . Settling uses Stokes drag
with Cunningham correction. Shear uses the rectilinear collision approximation.
"""
import math
from aero_psi_coagulation import BOLTZMANN_J_PER_K as KB, ScenarioInputError


def _fuchs_delta(diameter, flight):
    """Algebraic evaluation avoiding subtraction of nearly equal cubes."""
    r=flight/diameter
    if r<=1:
        value=(3*r*r+r**3-math.expm1(1.5*math.log1p(r*r)))/(3*r)
    else:
        value=r+1/(3*r)-r*r*math.expm1(1.5*math.log1p(1/(r*r)))/3
    return diameter*value


def physics(raw, p, diameters):
    def number(key, default, low=0, high=math.inf):
        value=raw.get(key, default)
        if isinstance(value,bool): raise ScenarioInputError(f'{key} must be numeric')
        try: value=float(value)
        except (ValueError,TypeError): raise ScenarioInputError(f'{key} must be numeric')
        if not math.isfinite(value) or not low <= value <= high: raise ScenarioInputError(f'{key} outside [{low}, {high}]')
        return value
    mode=raw.get('brownian_regime','continuum')
    if mode not in ('continuum','slip','fuchs','disabled'): raise ScenarioInputError('Unknown brownian_regime')
    t=p['gas_temperature_k']; mu=p['gas_viscosity_pa_s']; rho=p['particle_density_kg_m3']
    pressure=number('gas_pressure_pa',101325,1)
    molar=number('gas_molar_mass_kg_mol',.028965,1e-6)
    gas_density=pressure*molar/(8.314462618*t)
    mean=number('gas_mean_free_path_m',mu/pressure*math.sqrt(math.pi*8.314462618*t/(2*molar)),1e-15) if raw.get('gas_mean_free_path_m') is not None else mu/pressure*math.sqrt(math.pi*8.314462618*t/(2*molar))
    gravity=number('gravity_m_s2',0,0,9.81)
    shear=number('shear_rate_s',0)
    efficiency=number('settling_collection_efficiency',1,0,1)
    height=number('settling_height_m',1,1e-9)
    dilution=number('dilution_rate_s',0); wall=number('wall_loss_rate_s',0)
    kn=[2*mean/d for d in diameters]
    cc=[1+k*(1.257+.4*math.exp(-1.1/k)) for k in kn]
    diffusion=[KB*t*c/(3*math.pi*mu*d) for c,d in zip(cc,diameters)]
    speed=[math.sqrt(8*KB*t/(math.pi*rho*math.pi*d**3/6)) for d in diameters]
    flight=[8*D/(math.pi*c) for D,c in zip(diffusion,speed)]
    delta=[_fuchs_delta(d,l) for d,l in zip(diameters,flight)]
    settling=[max(0,rho-gas_density)*gravity*d*d*c/(18*mu) for d,c in zip(diameters,cc)]
    if max(gas_density*v*d/mu for v,d in zip(settling,diameters))>.1:
        raise ScenarioInputError('Stokes settling requires particle Reynolds number <= 0.1; reduce size or gravity')
    matrix=[]
    for i,di in enumerate(diameters):
        row=[]
        for j,dj in enumerate(diameters):
            D=diffusion[i]+diffusion[j]; ds=di+dj
            brown=2*math.pi*D*ds
            if mode=='continuum': brown=2*KB*t/(3*mu)*ds*(1/di+1/dj)
            elif mode=='fuchs': brown/=ds/(ds+2*math.hypot(delta[i],delta[j]))+8*D/(ds*math.hypot(speed[i],speed[j]))
            elif mode=='disabled': brown=0
            grav=math.pi*ds**2/4*abs(settling[i]-settling[j])*efficiency
            row.append(p['sticking_efficiency']*(brown+grav+shear*ds**3/6))
        matrix.append(row)
    deposition=raw.get('settling_deposition',False)
    if not isinstance(deposition,bool): raise ScenarioInputError('settling_deposition must be boolean')
    losses=[dilution+wall+(v/height if deposition else 0) for v in settling]
    return matrix,losses,{'brownian_regime':mode,'gravity_m_s2':gravity,'gas_pressure_pa':pressure,'gas_molar_mass_kg_mol':molar,'gas_mean_free_path_m':mean,'knudsen_numbers':kn,'cunningham_factors':cc,'settling_velocities_m_s':settling,'shear_rate_s':shear,'settling_collection_efficiency':efficiency,'settling_deposition':deposition,'settling_height_m':height,'dilution_rate_s':dilution,'wall_loss_rate_s':wall,'assumptions':['Compact spheres; uniform gas; additive collision kernels; prescribed collection efficiency.','Mean free path estimated from viscosity, pressure and molar mass unless supplied.','Settling loss assumes a well-mixed chamber with a perfectly collecting floor.','Turbulent inertia, charge, nonspherical morphology, vapor thermodynamics and spatial transport are not modeled.']}
