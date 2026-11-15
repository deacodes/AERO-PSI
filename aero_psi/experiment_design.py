"""Explicit factorial planning. No predicted physical outcomes are generated."""
from itertools import product
import math


def validate_design(raw):
    if raw is None: raw={}
    if not isinstance(raw,dict): raise ValueError('Experiment design must be an object')
    def label(v,name,limit=2000):
        if not isinstance(v,str) or len(v)>limit: raise ValueError(f'{name} must be text (up to {limit} characters)')
        return v.strip()
    variables=raw.get('variables',[])
    if not isinstance(variables,list) or len(variables)>4: raise ValueError('Use up to four independent variables')
    result=[]; names=set()
    for v in variables:
        if not isinstance(v,dict): raise ValueError('Each variable must be an object')
        name=label(v.get('name',''),'Variable name',100)
        if not name or name.casefold() in names: raise ValueError('Variables need unique names')
        names.add(name.casefold())
        lo,hi,levels=v.get('minimum'),v.get('maximum'),v.get('levels',3)
        if any(type(x) not in (int,float) or not math.isfinite(x) for x in (lo,hi)) or hi<lo: raise ValueError('Each variable needs finite bounds with maximum ≥ minimum')
        if type(levels) is not int or not 2<=levels<=9: raise ValueError('Use 2–9 levels per variable')
        if hi==lo: raise ValueError('Varying factors need distinct bounds; put fixed values in controls')
        result.append({'name':name,'unit':label(v.get('unit',''),'Unit',60),'minimum':lo,'maximum':hi,'levels':levels,'basis':label(v.get('basis','User-proposed range; feasibility requires review'),'Range basis')})
    reps=raw.get('replicates',1)
    if type(reps) is not int or not 1<=reps<=20: raise ValueError('Use 1–20 planned replicates')
    count=math.prod(v['levels'] for v in result)*reps if result else 0
    if count>1000: raise ValueError('This design exceeds 1,000 planned trials. Reduce levels, variables or replicates.')
    return {'variables':result,'replicates':reps,'outcome':label(raw.get('outcome',''),'Response to measure'),
            'controls':label(raw.get('controls',''),'Controls'), 'hypothesis':label(raw.get('hypothesis',''),'Hypothesis'),
            'measurement_method':label(raw.get('measurement_method',''),'Measurement method'),
            'analysis':label(raw.get('analysis',''),'Analysis plan'),'range_reviewed':raw.get('range_reviewed') is True}


def preview(raw):
    design=validate_design(raw);variables=design['variables']
    levels=[[v['minimum']+(v['maximum']-v['minimum'])*i/(v['levels']-1) for i in range(v['levels'])] for v in variables]
    trials=[]
    if variables:
        for condition in product(*levels):
            for replicate in range(1,design['replicates']+1):
                trials.append({'trial':len(trials)+1,'replicate':replicate,'conditions':dict(zip([v['name'] for v in variables],condition))})
    return {'design':design,'trial_count':len(trials),'condition_count':len(trials)//design['replicates'],'trials':trials,
            'classification':'proposed experimental conditions; no measured or predicted outcomes',
            'scope':'Full factorial planning with evenly spaced levels. Replication is a user choice, not a statistical power calculation. Trial numbering is for bookkeeping; randomization and blocking require a protocol appropriate to the apparatus.'}
