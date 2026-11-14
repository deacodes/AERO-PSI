"""Recompute the supplied model inputs before requesting scientific interpretation."""
import hashlib
import json
from aero_psi_copilot import ask
from aero_psi_scattering import simulate_scattering
from aero_psi_sectional import simulate_sectional


def context_evidence(payload):
    kind=payload.get('model');inputs=payload.get('inputs');question=payload.get('question','Explain this result and the assumptions that matter most.')
    if not isinstance(inputs,dict):raise ValueError('Compute a model scenario first')
    if kind=='scattering':
        result=simulate_scattering(inputs)
        compact={k:result[k] for k in ('classification','engine','inputs','coefficients','angles_deg','angular_scattering_coefficient_m_inv_sr_inv','assumptions','warnings')}
    elif kind=='coagulation':
        result=simulate_sectional(inputs)
        compact={k:result[k] for k in ('model_id','conservation_check','warnings') if k in result}
        compact['final']={k:v for k,v in result['series'][-1].items() if k!='distribution'}
        compact['inputs']=inputs
        compact['trajectory']=[{k:v for k,v in row.items() if k!='distribution'} for row in result['series'][::max(1,len(result['series'])//8)]]
        compact['final']={k:v for k,v in result['series'][-1].items() if k!='distribution'}
    else:raise ValueError('Choose coagulation or scattering')
    digest=hashlib.sha256(json.dumps(inputs,sort_keys=True).encode()).hexdigest()[:16]
    evidence={'id':f'runtime:model:{kind}:{digest}','kind':'executed_model','title':f'Executed {kind} scenario','source_path':f'runtime/{kind}','source_range':'Backend recomputation of supplied inputs','text':json.dumps(compact,ensure_ascii=False)}
    return evidence


def interpret(catalog,payload):
    evidence=context_evidence(payload)
    return ask(catalog,payload.get('question','Explain this result and the assumptions that matter most.'),runtime_evidence=[evidence],allow_background=True,history=payload.get('history'))
