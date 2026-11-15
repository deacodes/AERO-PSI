"""Fixed-pivot sphere population solver with explicit source/sink budgets.

Growth and injection are prescribed scenarios, not material chemistry fits.
"""
from __future__ import annotations

import bisect
import math
from typing import Any

from aero_psi.coagulation import BOLTZMANN_J_PER_K, DEFAULTS, ScenarioInputError, _inputs
from aero_psi.kernels import physics
from aero_psi.processes import finite, distribution, process_inputs

MODEL_ID = "sectional_sphere_coagulation_v2"


def _integer(payload: dict[str, Any], name: str, default: int, low: int, high: int) -> int:
    value = payload.get(name, default)
    if isinstance(value, bool): raise ScenarioInputError(f"{name} must be an integer.")
    try: result = int(value)
    except (TypeError, ValueError) as exc: raise ScenarioInputError(f"{name} must be an integer.") from exc
    if result != value or result < low or result > high: raise ScenarioInputError(f"{name} must be an integer between {low} and {high}.")
    return result


def _volume_grid(median_diameter_m: float, gsd: float, bins: int) -> tuple[list[float], list[float], float]:
    """Build a log-spaced grid with adequate initial lognormal tail support."""
    log_width=math.log(gsd)
    span=max(6 * log_width, math.log(20.0))
    log_median=math.log(median_diameter_m)
    diameters=[math.exp(log_median - span + 2 * span * index / (bins - 1)) for index in range(bins)]
    return diameters,[math.pi * diameter ** 3 / 6 for diameter in diameters],span


def _deposit(concentrations: list[float], volumes: list[float], particle_volume: float, amount: float) -> float:
    """Deposit a collision product conservatively; return volume sent above grid."""
    if amount <= 0: return 0.0
    if particle_volume > volumes[-1]: return amount * particle_volume
    if particle_volume <= volumes[0]:
        # Initial tails below the first pivot are assigned a fractional count so volume is retained.
        concentrations[0] += amount * particle_volume / volumes[0]
        return 0.0
    upper=bisect.bisect_left(volumes,particle_volume)
    lower=upper-1
    high_weight=(particle_volume-volumes[lower])/(volumes[upper]-volumes[lower])
    concentrations[lower] += amount * (1-high_weight)
    concentrations[upper] += amount * high_weight
    return 0.0


def _initial_bins(n0: float, diameters: list[float], volumes: list[float], median_diameter_m: float, gsd: float) -> list[float]:
    """Discretize a lognormal number distribution on the sectional grid."""
    values=[0.0] * len(diameters)
    if n0 == 0: return values
    if gsd == 1:
        _deposit(values,volumes,math.pi * median_diameter_m ** 3 / 6,n0)
        return values
    sigma=math.log(gsd)
    log_d=[math.log(value) for value in diameters]
    edges=[float("-inf")]+[(log_d[index]+log_d[index+1])/2 for index in range(len(log_d)-1)]+[float("inf")]
    cdf=lambda value: 0.5 * (1 + math.erf((value-math.log(median_diameter_m))/(sigma * math.sqrt(2))))
    for index,diameter in enumerate(diameters):
        probability=cdf(edges[index+1])-cdf(edges[index])
        values[index]=n0 * probability
    return values


def _kernel(temperature_k: float, viscosity_pa_s: float, sticking: float, diameters: list[float]) -> list[list[float]]:
    factor=2 * BOLTZMANN_J_PER_K * temperature_k * sticking / (3 * viscosity_pa_s)
    return [[factor * (first + second) * (1 / first + 1 / second) for second in diameters] for first in diameters]


def _moments(concentrations: list[float], volumes: list[float], density: float, overflow_mass: float) -> dict[str, float]:
    number=sum(concentrations)
    volume=sum(value * particle_volume for value,particle_volume in zip(concentrations,volumes))
    second=sum(value * particle_volume ** (2 / 3) for value,particle_volume in zip(concentrations,volumes))
    equivalent_diameter=(6 * (volume / number) / math.pi) ** (1 / 3) if number and volume else 0.0
    return {"number_concentration_m3":number,"resolved_volume_concentration_m3_per_m3":volume,"overflow_volume_concentration_m3_per_m3":overflow_mass,"total_volume_concentration_m3_per_m3":volume+overflow_mass,"mass_concentration_kg_m3":(volume+overflow_mass)*density,"equivalent_volume_mean_diameter_m":equivalent_diameter,"second_moment_volume_2_3_m2_m3":second}


def simulate_sectional(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    raw=payload or {}
    p=_inputs(raw)
    bins=_integer(raw,"section_count",64,8,128)
    output_points=_integer(raw,"output_points",DEFAULTS["output_points"],2,301)
    safety=finite(raw.get("stability_fraction",0.02),'stability_fraction',1e-8,.1)
    if not math.isfinite(safety) or safety <= 0 or safety > 0.1: raise ScenarioInputError("stability_fraction must be > 0 and <= 0.1.")
    n0=float(p["initial_number_concentration_m3"]); diameter=float(p["initial_median_diameter_m"]); density=float(p["particle_density_kg_m3"])
    duration=float(p["residence_time_s"]); diameters,volumes,span=_volume_grid(diameter,float(p["initial_geometric_std_dev"]),bins)
    if 'diameter_min_m' in raw or 'diameter_max_m' in raw:
        lo=finite(raw.get('diameter_min_m',diameters[0]),'diameter_min_m',1e-12,1e-2)
        hi=finite(raw.get('diameter_max_m',diameters[-1]),'diameter_max_m',lo,1e-2)
        if hi<=lo: raise ScenarioInputError('Maximum diameter must exceed minimum')
        diameters=[math.exp(math.log(lo)+i*math.log(hi/lo)/(bins-1)) for i in range(bins)]
        volumes=[math.pi*d**3/6 for d in diameters]
    concentrations=_initial_bins(n0,diameters,volumes,diameter,float(p["initial_geometric_std_dev"]))
    if 'initial_distribution' not in raw and not diameters[0]<=diameter<=diameters[-1]:
        raise ScenarioInputError('Initial median diameter must lie inside grid')
    initial_tail_fraction=0.0
    if 'initial_distribution' not in raw and p['initial_geometric_std_dev']>1:
        sigma=math.log(p['initial_geometric_std_dev'])
        cdf=lambda d: .5*(1+math.erf(math.log(d/diameter)/(sigma*math.sqrt(2))))
        initial_tail_fraction=cdf(diameters[0])+1-cdf(diameters[-1])
    initial_source={'reference':'assumed lognormal distribution'}
    if 'initial_distribution' in raw:
        ds,ns,initial_source=distribution(raw['initial_distribution'],'initial_distribution')
        if ds[0]<diameters[0]*(1-1e-12) or ds[-1]>diameters[-1]*(1+1e-12): raise ScenarioInputError('Supplied distribution exceeds grid; set diameter_min_m and diameter_max_m')
        concentrations=[0.0]*bins
        for d,n in zip(ds,ns): _deposit(concentrations,volumes,math.pi*d**3/6,n)
    growth,sources=process_inputs(raw,diameters)
    initial=_moments(concentrations,volumes,density,0.0)
    kernel,losses,physical=physics(raw,p,diameters)
    time_s=0.0; overflow=0.0; removed=0.0; steps=0; points=[]; target_index=0
    injected=0.0; vapor_exchange=0.0; underflow=0.0
    targets=[duration * i / (output_points - 1) for i in range(output_points)]
    while target_index < len(targets):
        if time_s + 1e-14 >= targets[target_index]:
            moment=_moments(concentrations,volumes,density,overflow); moment["time_s"]=targets[target_index]
            moment['distribution']={'diameters_m':diameters,'number_per_bin_m3':list(concentrations),'dN_dlnD_m3':[v/(math.log(diameters[1]/diameters[0])) for v in concentrations]}
            moment['surface_area_m2_m3']=sum(n*math.pi*d*d for n,d in zip(concentrations,diameters))
            moment['removed_volume_m3_m3']=removed
            moment['process_budget']={'injected_volume_m3_m3':injected,'vapor_exchange_volume_m3_m3':vapor_exchange,'underflow_volume_m3_m3':underflow}
            points.append(moment); target_index += 1; continue
        loss_rates=[losses[i]+sum(kernel[i][j] * concentrations[j] for j in range(bins)) for i in range(bins)]
        maximum=max(loss_rates,default=0.0)
        next_target=targets[target_index]
        step=min(next_target-time_s, safety / maximum if maximum > 0 else next_target-time_s)
        if growth: step=min(step,safety*min(diameters)/abs(growth))
        if not math.isfinite(step) or step<=0 or time_s+step==time_s: raise ScenarioInputError('Time step cannot advance; reduce rates or duration')
        delta=[0.0] * bins; overflow_delta=0.0
        for i in range(bins):
            lost=losses[i]*concentrations[i]*step
            delta[i]-=lost; removed+=lost*volumes[i]
        for i in range(bins):
            ni=concentrations[i]
            if ni <= 0: continue
            for j in range(i,bins):
                nj=concentrations[j]
                if nj <= 0: continue
                event=(0.5 * kernel[i][j] * ni * ni if i == j else kernel[i][j] * ni * nj) * step
                if event <= 0: continue
                if i == j: delta[i] -= 2 * event
                else: delta[i] -= event; delta[j] -= event
                product_volume=volumes[i]+volumes[j]
                overflow_delta += _deposit(delta,volumes,product_volume,event)
        concentrations=[max(0.0, value + adjustment) for value,adjustment in zip(concentrations,delta)]
        if growth:
            grown=[0.0]*bins
            for d,v,n in zip(diameters,volumes,concentrations):
                new_d=max(0.0,d+growth*step); new_v=math.pi*new_d**3/6
                vapor_exchange+=n*(new_v-v)
                if new_v<volumes[0]: underflow+=n*new_v
                else: overflow_delta+=_deposit(grown,volumes,new_v,n)
            concentrations=grown
        for source in sources:
            v=math.pi*source['diameter_m']**3/6; amount=source['number_rate_m3_s']*step
            overflow_delta+=_deposit(concentrations,volumes,v,amount); injected+=v*amount
        overflow += overflow_delta; time_s += step; steps += 1
        if steps > 200_000: raise ScenarioInputError("Scenario exceeded safe step limit; reduce duration/concentration or use fewer bins.")
    final=points[-1]; expected=initial['total_volume_concentration_m3_per_m3']+injected+vapor_exchange
    total_error=abs(final["total_volume_concentration_m3_per_m3"]+removed+underflow-expected)/max(initial["total_volume_concentration_m3_per_m3"]+injected+abs(vapor_exchange),1e-300)
    overflow_fraction=final["overflow_volume_concentration_m3_per_m3"]/max(final["total_volume_concentration_m3_per_m3"],1e-300)
    warnings=[
        'Model scenario only: no NASA PSI run is used as a measured size-distribution target.',
        'Fixed-pivot compact-sphere scenario with prescribed homogeneous gas conditions.',
        'Growth and particle injection, if enabled, are prescribed rates. Vapor depletion, thermodynamics, nucleation kinetics, charge, morphology, fragmentation and spatial transport remain unsupported.',
        'Overflow is an inert accounting reservoir; its particles no longer collide or deposit. Reject substantial overflow.'
    ]
    if initial_tail_fraction > 1e-5: warnings.append('The selected grid truncates the assumed initial lognormal tails; tail counts are assigned to boundary pivots. Widen the domain before interpretation.')
    if overflow_fraction > 1e-5: warnings.append("Top sectional bin overflowed; the diameter domain must be widened before interpreting the resolved distribution. Increasing bin count alone does not widen it.")
    if physical['brownian_regime']=='continuum' and max(physical['knudsen_numbers'])>.1:
        warnings.append('Continuum kernel selected despite bins with Kn > 0.1; consider fuchs regime.')
    if underflow: warnings.append('Particles evaporating below the grid are removed to an inert underflow reservoir; widen the grid for continued evolution.')
    physical['prescribed_processes']={'diameter_growth_rate_m_s':growth,'particle_sources':sources,'initial_distribution_source':initial_source,'underflow_volume_m3_m3':underflow,'injected_volume_m3_m3':injected,'vapor_exchange_volume_m3_m3':vapor_exchange}
    effective={**p,**{key:value for key,value in physical.items() if isinstance(value,(str,int,float,bool))},'section_count':bins,'stability_fraction':safety,'output_points':output_points,'diameter_growth_rate_m_s':growth,'particle_sources':sources,'diameter_min_m':diameters[0],'diameter_max_m':diameters[-1]}
    if 'initial_distribution' in raw: effective['initial_distribution']=raw['initial_distribution']
    provenance={key:{'value':value,'origin':'user input (unverified)' if key in raw else 'default or derived assumption'} for key,value in effective.items()}
    return {"initial_number_fraction_outside_grid":initial_tail_fraction,"physics":physical,"parameter_provenance":provenance,"removed_volume_m3_m3":removed,"model_id":MODEL_ID,"classification":"deterministic model scenario; not NASA measurement","inputs":effective,"units":{
        'diameter_m': 'm',
        'number_concentration_m3': 'particles/m^3',
        'volume_concentration_m3_per_m3': 'm^3 particle/m^3 gas'
    },"solver":{"formulation":"log-volume, fixed-pivot discrete Smoluchowski sectional solver","kernel":f"{physical['brownian_regime']} Brownian + differential settling + prescribed laminar shear","stability_rule":"adaptive explicit loss-rate and diameter-growth limits","steps":steps,"section_count":bins,"initial_diameter_grid_m":[diameters[0],diameters[-1]],"initial_log_half_span":span},"initial":initial,"series":points,"conservation_check":{"balance":"final resolved + overflow + removed + underflow = initial + injected + vapor exchange","total_volume_relative_error":total_error,"overflow_volume_fraction":overflow_fraction,"passes_floating_point_tolerance":total_error < 5e-10},"warnings":warnings}


def sensitivity(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    raw=dict(payload or {}); counts=raw.pop("section_counts",[
        32,
        64,
        96
    ])
    if not isinstance(counts,list) or not counts: raise ScenarioInputError("section_counts must be a non-empty list.")
    results=[]
    for count in counts:
        candidate={**raw,"section_count":count}
        result=simulate_sectional(candidate); final=result["series"][-1]
        results.append({"section_count":result["solver"]["section_count"],"final_number_concentration_m3":final["number_concentration_m3"],"final_equivalent_volume_mean_diameter_m":final["equivalent_volume_mean_diameter_m"],"volume_relative_error":result["conservation_check"]["total_volume_relative_error"],"overflow_volume_fraction":result["conservation_check"]["overflow_volume_fraction"],"steps":result["solver"]["steps"]})
    reference=max(results,key=lambda item:item['section_count'])
    for result in results: result["number_relative_to_finest"]=(result["final_number_concentration_m3"]-reference["final_number_concentration_m3"])/max(reference["final_number_concentration_m3"],1e-300)
    return {"classification":"numerical sensitivity check; model scenario, not NASA measurement","results":results,"pass_rule":"Inspect convergence of final number and diameter and require negligible top-bin overflow before use."}
