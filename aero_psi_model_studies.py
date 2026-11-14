"""Bounded scenario studies and explicit user-supplied observation comparisons."""
import math
import random
from aero_psi_sectional import simulate_sectional
from aero_psi_coagulation import ScenarioInputError
from aero_psi_processes import finite

FIELDS=('number_concentration_m3','equivalent_volume_mean_diameter_m','surface_area_m2_m3','mass_concentration_kg_m3')
PARAMETERS=('gravity_m_s2','gas_temperature_k','gas_viscosity_pa_s','gas_pressure_pa','initial_number_concentration_m3','initial_median_diameter_m','initial_geometric_std_dev','sticking_efficiency','dilution_rate_s','wall_loss_rate_s','diameter_growth_rate_m_s','shear_rate_s')


def _integer(value, name, low, high):
    result=finite(value,name,low,high)
    if result!=int(result): raise ScenarioInputError(f'{name} must be an integer')
    return int(result)


def _scenario(payload):
    scenario=payload.get('scenario',{})
    if not isinstance(scenario,dict): raise ScenarioInputError('scenario must be an object')
    return scenario


def _quantile(values,q):
    ordered=sorted(values); position=(len(ordered)-1)*q
    lower=int(position); upper=min(lower+1,len(ordered)-1)
    return ordered[lower]+(ordered[upper]-ordered[lower])*(position-lower)


def uncertainty(payload):
    """Independent bounded input sampling; quantiles are conditional on assumptions."""
    scenario=_scenario(payload)
    samples=_integer(payload.get('samples',16),'samples',2,64)
    seed=_integer(payload.get('seed',0),'seed',0,2**32-1)
    inputs=payload.get('uncertain_inputs')
    if not isinstance(inputs,dict) or not 1<=len(inputs)<=6: raise ScenarioInputError('Supply 1–6 uncertain_inputs')
    parsed={}
    for name,spec in inputs.items():
        if name not in PARAMETERS or not isinstance(spec,dict): raise ScenarioInputError('Unsupported uncertainty parameter')
        low=finite(spec.get('low'),f'{name}.low',-math.inf)
        high=finite(spec.get('high'),f'{name}.high',low)
        mode=spec.get('distribution','uniform')
        if mode not in ('uniform','log_uniform') or (mode=='log_uniform' and low<=0): raise ScenarioInputError('Use uniform or positive log_uniform bounds')
        if not isinstance(spec.get('reference'),str) or not spec['reference'].strip(): raise ScenarioInputError('Uncertainty bounds require a reference or explicit assumption')
        parsed[name]={**spec,'low':low,'high':high,'distribution':mode}
    if 'initial_distribution' in scenario and any(n in inputs for n in ('initial_number_concentration_m3','initial_median_diameter_m','initial_geometric_std_dev')):
        raise ScenarioInputError('Supplied distribution overrides lognormal parameters; cannot sample these parameters')
    rng=random.Random(seed); trajectories=[]; members=[]; warnings=set()
    for index in range(samples):
        chosen={}
        for name,spec in sorted(parsed.items()):
            lo,hi=spec['low'],spec['high']
            chosen[name]=math.exp(rng.uniform(math.log(lo),math.log(hi))) if spec['distribution']=='log_uniform' else rng.uniform(lo,hi)
        try: model=simulate_sectional({**scenario,**chosen})
        except ScenarioInputError as exc: raise ScenarioInputError(f'Uncertainty member {index} invalid: {exc}') from exc
        trajectories.append(model['series']); warnings.update(model['warnings'])
        members.append({'sample_index':index,'parameters':chosen,'final':{f:model['series'][-1][f] for f in FIELDS},'conservation_check':model['conservation_check']})
    series=[]
    for index,row in enumerate(trajectories[0]):
        series.append({'time_s':row['time_s'],'quantiles':{f:{'p05':_quantile([s[index][f] for s in trajectories],.05),'p50':_quantile([s[index][f] for s in trajectories],.5),'p95':_quantile([s[index][f] for s in trajectories],.95)} for f in FIELDS}})
    return {'classification':'Monte Carlo propagation of independently sampled input assumptions; not a confidence interval or model-discrepancy estimate','seed':seed,'samples':samples,'uncertain_inputs':parsed,'series':series,'members':members,'warnings':sorted(warnings)}


def calibrate(payload):
    """One-dimensional bounded grid fit; held-out data never selects the optimum."""
    scenario=_scenario(payload); name=payload.get('parameter')
    if name not in PARAMETERS: raise ScenarioInputError('Unsupported calibration parameter')
    if 'initial_distribution' in scenario and name.startswith('initial_'): raise ScenarioInputError('Supplied distribution overrides initial lognormal parameters')
    lo=finite(payload.get('lower'), 'lower',-math.inf); hi=finite(payload.get('upper'),'upper',lo)
    if hi<=lo: raise ScenarioInputError('upper must exceed lower')
    count=_integer(payload.get('candidate_count',11),'candidate_count',3,41)
    scores=[]; best=None
    for index in range(count):
        value=lo+(hi-lo)*index/(count-1)
        result=compare_observations({**payload,'scenario':{**scenario,name:value}})
        scores.append({'value':value,'rmse':result['rmse'],'mae':result['mae'],'bias':result['bias']})
        if best is None or result['rmse']<best[1]['rmse']: best=(value,result)
    selected,fit=best
    held_out=None
    if payload.get('validation_observations') is not None:
        train=payload.get('observations',[]); validation=payload['validation_observations']
        if not isinstance(validation,list): raise ScenarioInputError('validation_observations must be a list')
        train_times={row['time_s'] for row in train}
        if any(not isinstance(row,dict) or row.get('time_s') in train_times for row in validation):
            raise ScenarioInputError('Holdout times must not overlap training times')
        held_out=compare_observations({**payload,'scenario':{**scenario,name:selected},'observations':validation})
    spread=max(x['rmse'] for x in scores)-min(x['rmse'] for x in scores)
    return {'classification':'single-parameter grid calibration to supplied observations; no claim of unique physical identification','parameter':name,'best_value':selected,'search_resolution':(hi-lo)/(count-1),'boundary_optimum':selected in (lo,hi),'objective_spread':spread,'objective_flat':spread<=max(1e-30,max(x['rmse'] for x in scores)*1e-10),'candidates':scores,'training':fit,'held_out_validation':held_out,'provenance_status':'User references retained; independence and NASA provenance require external verification.'}


def convergence(payload):
    """Grid/time refinement at a common diameter domain; compare final moments."""
    scenario=_scenario(payload)
    counts=payload.get('section_counts',[16,32,64]); fractions=payload.get('stability_fractions',[.04,.02,.01])
    if not isinstance(counts,list) or not isinstance(fractions,list) or not 2<=len(counts)<=4 or not 2<=len(fractions)<=4:
        raise ScenarioInputError('Supply 2–4 grid sizes and time stability fractions')
    counts=sorted({_integer(x,'section_count',8,128) for x in counts})
    fractions=sorted({finite(x,'stability_fraction',1e-8,.1) for x in fractions},reverse=True)
    if len(counts)<2 or len(fractions)<2: raise ScenarioInputError('Refinements must have distinct values')
    results=[]
    for count in counts:
        for fraction in fractions:
            model=simulate_sectional({**scenario,'section_count':count,'stability_fraction':fraction})
            results.append({'section_count':count,'stability_fraction':fraction,'final':{f:model['series'][-1][f] for f in FIELDS},'conservation_check':model['conservation_check'],'warnings':model['warnings']})
    reference=results[-1]
    for result in results:
        result['relative_difference_to_reference']={f:(result['final'][f]-reference['final'][f])/abs(reference['final'][f]) if reference['final'][f] else None for f in FIELDS}
    return {'classification':'numerical refinement study; convergence is not experimental validation','reference':{'section_count':counts[-1],'stability_fraction':fractions[-1]},'results':results,'interpretation':'Inspect both refinements and grid-boundary loss. Small moment differences alone do not prove distribution convergence.'}


def sweep(payload):
    scenario=payload.get('scenario',{})
    name=payload.get('parameter','gravity_m_s2'); values=payload.get('values',[0,9.81])
    if not isinstance(scenario,dict) or name not in PARAMETERS: raise ScenarioInputError('Invalid scenario or sweep parameter')
    if not isinstance(values,list) or not 1<=len(values)<=12: raise ScenarioInputError('Supply 1–12 sweep values')
    results=[]
    for value in values:
        value=finite(value,name,-math.inf)
        model=simulate_sectional({**scenario,name:value})
        results.append({'value':value,'final':{field:model['series'][-1][field] for field in FIELDS},'conservation_check':model['conservation_check'],'warnings':model['warnings']})
    return {'classification':'deterministic parameter sweep; input ranges are assumptions','parameter':name,'results':results}


def compare_observations(payload):
    """Compare one explicitly matching observable; never accept detector voltage."""
    observable=payload.get('observable')
    if observable not in FIELDS: raise ScenarioInputError('Observable must match a model moment and its SI units')
    observations=payload.get('observations')
    if not isinstance(observations,list) or not 2<=len(observations)<=300: raise ScenarioInputError('Supply 2–300 observations')
    parsed=[]
    for row in observations:
        if not isinstance(row,dict) or not isinstance(row.get('source'),dict) or not row['source'].get('reference'):
            raise ScenarioInputError('Each observation requires source.reference')
        parsed.append((finite(row.get('time_s'),'time_s'),finite(row.get('value'),'value'),row['source']))
    if any(b[0]<=a[0] for a,b in zip(parsed,parsed[1:])): raise ScenarioInputError('Observation times must strictly increase')
    scenario=payload.get('scenario',{})
    if not isinstance(scenario,dict): raise ScenarioInputError('scenario must be an object')
    model=simulate_sectional(scenario); series=model['series']
    if parsed[-1][0]>series[-1]['time_s']: raise ScenarioInputError('Observations exceed simulated duration')
    residuals=[]
    for t,observed,source in parsed:
        index=next((i for i,row in enumerate(series) if row['time_s']>=t),len(series)-1)
        right=series[index]; left=series[max(0,index-1)]
        weight=(t-left['time_s'])/(right['time_s']-left['time_s']) if right['time_s']!=left['time_s'] else 0
        predicted=left[observable]+weight*(right[observable]-left[observable])
        residuals.append({'time_s':t,'observed':observed,'predicted':predicted,'residual':predicted-observed,'source':source})
    errors=[row['residual'] for row in residuals]
    return {'classification':'comparison against user-supplied observations; provenance has not been independently verified','observable':observable,'interpolation':'linear between model output times; increase output_points to check interpolation error','rmse':math.sqrt(sum(x*x for x in errors)/len(errors)),'mae':sum(abs(x) for x in errors)/len(errors),'bias':sum(errors)/len(errors),'residuals':residuals,'model_warnings':model['warnings'],'conservation_check':model['conservation_check']}


def domain_study(payload):
    """Vary grid bounds and resolution; report resolved distribution shape too."""
    scenario=_scenario(payload); domains=payload.get('domains')
    if not isinstance(domains,list) or not 2<=len(domains)<=4: raise ScenarioInputError('Supply 2–4 explicit diameter domains')
    models=[]; results=[]
    for domain in domains:
        if not isinstance(domain,dict) or set(domain)!={'diameter_min_m','diameter_max_m','section_count'}: raise ScenarioInputError('Each domain needs diameter_min_m, diameter_max_m and section_count')
        model=simulate_sectional({**scenario,**domain}); models.append(model)
        results.append({'domain':domain,'initial':model['initial'],'final':{f:model['series'][-1][f] for f in FIELDS},'conservation_check':model['conservation_check'],'warnings':model['warnings']})
    ref_index=_integer(payload.get('reference_index',len(models)-1),'reference_index',0,len(models)-1)
    reference=models[ref_index]['series'][-1]['distribution']
    def distance(left,right):
        ld=left['diameters_m']; rd=right['diameters_m']; ln=left['number_per_bin_m3']; rn=right['number_per_bin_m3']
        if not sum(ln) or not sum(rn): return None
        grid=sorted(set(ld+rd)); result=0.0; a=b=0; lc=rc=0.0
        for lo,hi in zip(grid,grid[1:]):
            while a<len(ld) and ld[a]<=lo: lc+=ln[a]/sum(ln); a+=1
            while b<len(rd) and rd[b]<=lo: rc+=rn[b]/sum(rn); b+=1
            result+=abs(lc-rc)*math.log(hi/lo)
        return result
    for item,model in zip(results,models):
        item['number_cdf_distance_log_diameter']=distance(model['series'][-1]['distribution'],reference)
        item['relative_final_moment_difference']={f:(item['final'][f]-results[ref_index]['final'][f])/abs(results[ref_index]['final'][f]) if results[ref_index]['final'][f] else None for f in FIELDS}
    return {'classification':'numerical domain sensitivity; not experimental validation','reference_index':ref_index,'shape_metric':'Integral |CDF_number - reference CDF_number| d(ln diameter) over discrete resolved pivots; zero if identical, null for empty distributions','results':results,'warnings':['Changing domains can change the discretized initial distribution; inspect initial moments.','This study does not by itself establish convergence or account for unresolved boundary-particle optics.']}
