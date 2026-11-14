"""Prescribed population sources and size growth; no inferred vapor chemistry."""
import math
from aero_psi_coagulation import ScenarioInputError


def finite(value, name, low=0, high=math.inf):
    if isinstance(value, bool): raise ScenarioInputError(f'{name} must be numeric')
    try: result=float(value)
    except (TypeError, ValueError): raise ScenarioInputError(f'{name} must be numeric')
    if not math.isfinite(result) or not low <= result <= high:
        raise ScenarioInputError(f'{name} must be finite in [{low}, {high}]')
    return result


def distribution(value, name):
    if not isinstance(value,dict): raise ScenarioInputError(f'{name} must be an object')
    ds=value.get('diameters_m'); ns=value.get('number_per_bin_m3')
    if not isinstance(ds,list) or not isinstance(ns,list) or not ds or len(ds)!=len(ns) or len(ds)>1024:
        raise ScenarioInputError(f'{name} requires equal nonempty diameter and bin-number arrays (max 1024)')
    ds=[finite(d,'diameter',1e-12,1e-2) for d in ds]
    ns=[finite(n,'bin number') for n in ns]
    if any(b<=a for a,b in zip(ds,ds[1:])): raise ScenarioInputError('Diameters must increase strictly')
    source=value.get('source')
    if not isinstance(source,dict) or not source.get('reference'):
        raise ScenarioInputError('Supplied distribution requires source.reference (file/table or explicit synthetic assumption)')
    return ds,ns,source


def process_inputs(raw, diameters):
    rate=finite(raw.get('diameter_growth_rate_m_s',0),'diameter_growth_rate_m_s',-1e-5,1e-5)
    sources=raw.get('particle_sources',[])
    if not isinstance(sources,list) or len(sources)>16: raise ScenarioInputError('particle_sources must be a list of at most 16 prescribed sources')
    parsed=[]
    for source in sources:
        if not isinstance(source,dict): raise ScenarioInputError('Each particle source must be an object')
        d=finite(source.get('diameter_m'),'source diameter',diameters[0],diameters[-1])
        n=finite(source.get('number_rate_m3_s'),'source number rate')
        reference=source.get('reference')
        if not isinstance(reference,str) or not reference.strip(): raise ScenarioInputError('Source requires a reference or explicit assumption')
        parsed.append({'diameter_m':d,'number_rate_m3_s':n,'reference':reference})
    return rate,parsed
