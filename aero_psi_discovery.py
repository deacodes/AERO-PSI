"""Reproducible question routing and evidence prerequisites; no inferred measurements."""
from collections import Counter
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parent
VERSION = 'question-discovery-1.0'
# These are declared workflow requirements, not facts extracted from NASA reports.
REQUIREMENTS = {
    'detector': ('Detector response', ('scatter_voltage', 'obscuration_voltage', 'ion_a_voltage', 'sts_voltage'), ()),
    'number': ('Particle number concentration', ('ptrak_particles_per_cc',), ()),
    'size': ('Time-resolved particle-size distribution', (), ('particle_size_distribution',)),
    'temperature': ('Gas/plume temperature', ('plume_temperature_c',), ('temperature',)),
    'flow': ('Flow or transport setting', ('lfe_flow_sccm', 'mfc_flow_lpm'), ('flow',)),
    'gravity': ('Run-resolved acceleration history', (), ('acceleration_m_s2',)),
    'angular': ('Calibrated angular scattering', (), ('angular_scattering_m_inv_sr_inv',)),
    'optics': ('Wavelength, refractive index and detector geometry', (), ('verified_optical_configuration',)),
    'calibration': ('Traceable instrument calibration', (), ('verified_instrument_calibration',)),
    'oxygen': ('Oxygen condition', (), ('oxygen', 'calibrated_initial_o2_by_vol', 'percent_o2')),
    'extinction': ('Flame extinction outcome', (), ('visible_flame_extinction_diameter_mm',)),
    'spread': ('Solid-fuel flame-spread outcome', (), ('flame_spread_rate',)),
    'burning': ('Burning-rate outcome', (), ('burning_rate_mm',)),
    'flame_dimensions': ('Flame dimensions with a defined measurement time', (), ('visible_flame_extinction_diameter_mm','flame_length_mm','flame_diameter_mm','flame_height_mm')),
    'pressure': ('Pressure condition', (), ('pressure','approx_p_bar')),
    'material': ('Material or fuel identity', (), ('material_or_fuel',)),
}
PROFILES = {
    'detector': ('Smoke detector response', ('detector','number','flow','calibration')),
    'coagulation': ('Aerosol coagulation and gravity', ('number','size','temperature','flow','gravity')),
    'scattering': ('Multi-angle optical scattering', ('angular','size','optics','calibration')),
    'flammability': ('Solid-fuel fire behavior', ('material','oxygen','flow','spread')),
    'extinction': ('Droplet flame extinction', ('material','oxygen','extinction','burning')),
    'flame_geometry': ('Flame size and gravity', ('flame_dimensions','gravity','material','oxygen','pressure')),
    'general': ('Archive exploration', ()),
}
ALIASES = {
    'coagulation': ('coagulation','coagulate','brownian','aggregation'),
    'aerosol': ('aerosol','aerosols','particulate'),
    'scattering': ('scattering','scatter','multi-angle','mie'),
    'optical': ('optical','optics'),
    'detector': ('detector','detectors','detection'),
    'smoke': ('smoke',),
    'extinction': ('extinction','extinguish','extinguishment'),
    'droplet': ('droplet','droplets'),
    'flammability': ('flammability','flammable','flame spread'),
    'solid': ('solid','solids'),
    'gravity': ('gravity','microgravity','low gravity','freefall'),
}

STOP = set('a an the and or of in on at to for from with which what how why is are was be can could should would does do we i me my our your this that these those compare rank ranking investigate investigations investigation evidence available use using explain find best most relevant study question about across between nasa psi experiments experiment supplied archive measurement measurements response behavior'.split())


def tokens(text):
    return set(re.findall(r'[a-z0-9]+', str(text).lower()))


def query_spec(payload):
    question = payload.get('question')
    if not isinstance(question, str) or not 1 <= len(question.strip()) <= 2000:
        raise ValueError('question must be 1–2000 characters')
    q = question.lower()
    concepts = {}
    remaining = tokens(q) - STOP
    for concept, alternatives in ALIASES.items():
        if any(tokens(a) <= tokens(q) for a in alternatives):
            concepts[concept] = alternatives
            for a in alternatives: remaining -= tokens(a)
    for word in sorted(remaining): concepts[word] = (word,)
    goal = payload.get('goal', 'auto')
    if not isinstance(goal,str): raise ValueError('goal must be a profile name')
    if goal == 'auto':
        goal = next((g for g in ('scattering','coagulation','extinction','flammability','detector') if g in concepts), 'general')
        if goal=='general' and 'optical' in concepts: goal='scattering'
        if tokens(q) & {'flame','flames'} and tokens(q) & {'size','sizes','dimensions','dimension','height','length','diameter','shape'}: goal='flame_geometry'
    if goal not in PROFILES: raise ValueError('Unknown goal profile')
    return question.strip(), goal, concepts


def manifest_records():
    path = ROOT/'derived/reports/ingestion_manifest.json'
    return json.loads(path.read_text())['records'] if path.exists() else []


def ref(record, kind, column=None):
    path = record['source_path']
    identifier = ('investigation:'+record['group'] if kind == 'metadata' else
                  f'table:{path}:{record["source_row"]}' if kind == 'table' else 'run:'+path)
    return {'id':identifier, 'source_path':path, 'source_sha256':record.get('source_sha256'),
            'source_row':record.get('source_row'), 'worksheet':record.get('worksheet'),
            'source_column':column, 'kind':kind}


def assess_requirement(key, rows, runs):
    label, signals, fields = REQUIREMENTS[key]
    sources=[]
    for run in runs:
        analysis=run.get('analysis', {})
        for signal in signals:
            if signal in analysis.get('available_signals', {}):
                metric=analysis.get('metrics', {}).get(signal, {})
                # Header presence alone is not usable measurement coverage.
                if metric.get('status') == 'available' and signal not in analysis.get('fully_zero_core_signals', []):
                    sources.append(ref(run, 'run', analysis['available_signals'][signal]))
    for row in rows:
        for field in fields:
            value=row['fields'].get(field, {})
            if value.get('state') == 'observed' and str(value.get('value','')).strip():
                sources.append(ref(row, 'table', value.get('source_column')))
    return {'key':key,'label':label,'state':'located_in_index' if sources else 'not_located_in_index',
            'source_count':len(sources),'sources':sources[:3],
            'scope':'Imported nonzero channels with available metrics and observed normalized fields only; report text is not a verified measurement. Channels across runs are not assumed simultaneous or comparable.'}


def rank_for_question(catalog, payload, records=None, documents=None):
    question, goal, concepts=query_spec(payload)
    if documents is None:
        from aero_psi_evidence import document_records
        documents=document_records() if records is None else []
    records=manifest_records() if records is None else records
    result=[]
    for meta in catalog.get('investigations', []):
        group=meta['group']
        rows=[r for r in catalog.get('normalized_experiments',[]) if r['source_path'].split('/')[0]==group]
        runs=[r for r in records if r.get('group')==group and r.get('status')=='imported']
        # Metadata and observed table values provide topical matching, never quantity validation.
        entries=[(' '.join(str(meta.get(k,'')) for k in ('title','objective','measurement_family','group')),ref(meta,'metadata'))]
        entries.extend((' '.join(str(v.get('value','')) for v in row['fields'].values() if v.get('state')=='observed'), ref(row,'table')) for row in rows)
        entries.extend((doc['text'], {k:doc.get(k) for k in ('id','source_path','source_sha256','source_range','review_state')}) for doc in documents if doc['source_path'].split('/')[0]==group)
        entries=[(tokens(text),source) for text,source in entries]
        matches=[]
        for concept, alternatives in concepts.items():
            hit=next(((text,source,a) for text,source in entries for a in alternatives if tokens(a)<=text),None)
            if hit:
                text,source,alias=hit
                matches.append({'concept':concept,'matched_term':alias,'source':source,'support_weight':1.0 if source.get('kind')=='metadata' else .75 if source.get('kind')=='table' else .35})
        requirements=[assess_requirement(k,rows,runs) for k in PROFILES[goal][1]]
        relevance=sum(m['support_weight'] for m in matches)/len(concepts) if concepts else 0
        suitability=sum(r['state']=='located_in_index' for r in requirements)/len(requirements) if requirements else None
        rw,mw=(.75,.25) if requirements else (1.,0.)
        score=round(round(100*rw*relevance,2)+round(100*mw*(suitability or 0),2),2)
        quality={'state':'import_QA_available' if runs else 'unknown', 'imported_runs':len(runs),
                 'runs_with_warnings':sum(bool(r.get('warnings')) for r in runs),
                 'quality_states':dict(Counter(r.get('analysis',{}).get('quality_state','unknown') for r in runs)),
                 'interpretation':'Import QA describes parser/window usability, not scientific validity or calibration.'}
        result.append({'group':group,'title':meta.get('title',group),'score':score,
                       'components':{'question_relevance':{'value':relevance,'weight':rw,'points':round(100*rw*relevance,2)},
                                     'measurement_suitability':{'value':suitability,'weight':mw,'points':round(100*mw*(suitability or 0),2)}},
                       'matches':matches,'unmatched_concepts':sorted(set(concepts)-{m['concept'] for m in matches}),
                       'requirements':requirements,'data_quality':quality,
                       'comparability':{'state':'not_established','reason':'Matched run identity, units, calibration, windows and controlled conditions require pairwise review. Platform metadata is not acceleration history.'},
                       'metadata_source':ref(meta,'metadata')})
    result.sort(key=lambda r:(-r['score'],r['group']))
    for i,item in enumerate(result): item['position']=result[i-1]['position'] if i and item['score']==result[i-1]['score'] else i+1
    return {'version':VERSION,'classification':'question-specific archive navigation; not NASA importance or scientific validity',
            'question':question,'goal':goal,'goal_label':PROFILES[goal][0],'concepts':list(concepts),
            'formula':'75% weighted query-concept coverage + 25% indexed measurement-requirement coverage; general exploration uses 100% query coverage. Equal displayed scores share a rank.',
            'method':'Declared lexical aliases: metadata matches weight 1, observed table values 0.75, unreviewed hash-checked document excerpts 0.35. First match in that source order counts; each concept and requirement counts once regardless of file count. Quality and comparability are separate and never silently imputed. Goal profiles are AERO-PSI workflow choices, not NASA-derived weights.',
            'limitations':['A mention establishes topic relevance only. No semantic relevance or scientific importance is inferred.','Not located in the index does not mean absent from the source reports or NASA archive.','Positive suitability can describe partial channels across different runs, not a validated combined dataset.'],
            'catalog_generated_at':catalog.get('generated_at'),'items':result}


def proposal_for_requirement(requirement, group, question):
    key=requirement['key']
    designs={
      'size':('Validate time-dependent coagulation','residence/aging time','initial distribution, source material, gas pressure/temperature, flow and acceleration','size-resolved number distributions at initial and later times, instrument transfer function, bin uncertainties and replicate runs','Compare model and measured distributions in matched units; report residuals, uncertainty and held-out validation.'),
      'gravity':('Separate gravity effects from transport','measured acceleration condition','initial distribution, chamber geometry, gas properties, flow and sampling window','synchronized acceleration history, size distributions and number concentration','Use paired controlled conditions; quantify settling and loss separately before attributing changes to coagulation.'),
      'angular':('Test angular scattering predictions','scattering angle','wavelength, population, optical path, polarization and collection solid angle','calibrated angular intensity, dark/background readings and independent size distribution','Compare spherical-model angular response with calibrated observations; report shape-related limitations.'),
      'optics':('Establish the optical forward-model inputs','wavelength or optical configuration after an initial fixed-configuration baseline','particle material, concentration and size distribution','wavelength, complex refractive index with provenance, detector angles/solid angles and calibration','Propagate optical-input uncertainty before comparing detector and modeled response.'),
      'calibration':('Establish a usable measurement scale','traceable reference level','instrument configuration, gain, flow, environmental conditions and timing','blank, reference standards, repeatability, response curve, saturation and calibration uncertainty','Estimate calibration and uncertainty independently; raw voltage is not particle size or concentration.'),
    }
    target,varied,controls,outputs,analysis=designs.get(key,(f'Acquire {requirement["label"].lower()}','one declared experimental condition',
      'material, instrument configuration, environmental conditions and timing',requirement['label']+' with units, calibration, timestamps, uncertainty and replicates',
      'Predeclare the comparison and uncertainty analysis; retain source rows and matched run IDs.'))
    return {'classification':'conditional study proposal; not an observed result','question':question,'investigation_group':group,
            'objective':target,'varied_parameter':varied,'controls':controls,'required_outputs':outputs,'analysis_plan':analysis,
            'first_action':'Review the original reports and housekeeping for this prerequisite before commissioning new measurements. Record exact page/sheet/row and calibration scope if found.',
            'expected_benefit':f'Resolve the indexed prerequisite: {requirement["label"]}. No numerical information gain or predicted outcome is claimed.',
            'feasibility':{'state':'not_assessed','requires':['instrument availability and operating range','compatible chamber/sample design','access to controlled gravity conditions if needed','safety and operations review','replicate count based on pilot variance']}}


def gap_plan(catalog,payload,records=None):
    ranking=rank_for_question(catalog,payload,records)
    group=payload.get('group')
    if group is not None and not isinstance(group,str): raise ValueError('group must be an investigation name')
    if group and group not in {i['group'] for i in ranking['items']}: raise ValueError('Unknown investigation group')
    selected=[i for i in ranking['items'] if not group or i['group']==group]
    candidates=[]
    critical={'size','gravity','angular','optics','calibration'}
    for item in selected:
        for requirement in item['requirements']:
            if requirement['state']=='located_in_index': continue
            relevance=item['components']['question_relevance']['value']
            blocker=1. if requirement['key'] in critical else .5
            score=round(100*(.6*relevance+.4*blocker),2)
            identifier=hashlib.sha256(f'{VERSION}|{ranking["question"]}|{ranking["goal"]}|{item["group"]}|{requirement["key"]}'.encode()).hexdigest()[:16]
            candidates.append({'id':identifier,'group':item['group'],'title':requirement['label'],
              'category':'calibration_or_model_prerequisite' if requirement['key'] in critical else 'indexed_measurement_gap',
              'state':'not_located_in_index','interpretation':'A prerequisite was not located in the imported measurement index. This is not evidence of a missing NASA experiment or an unresolved scientific law.',
              'priority':score,'priority_components':{'question_relevance':round(60*relevance,2),'workflow_blocker':40*blocker},
              'evidence':[item['metadata_source']], 'audit':{'checked_requirement':requirement,'imported_run_count':item['data_quality']['imported_runs']},
              'proposal':proposal_for_requirement(requirement,item['group'],ranking['question'])})
    candidates.sort(key=lambda g:(-g['priority'],g['group'],g['title']))
    for i,gap in enumerate(candidates): gap['position']=candidates[i-1]['position'] if i and gap['priority']==candidates[i-1]['priority'] else i+1
    return {'version':VERSION,'question':ranking['question'],'goal':ranking['goal'],'group':group,
            'classification':'evidence-index audit and conditional experiment planning',
            'priority_formula':'100 × (0.60 weighted question-concept coverage + 0.40 declared workflow blocker). Critical calibration/model prerequisites = 1; other indexed requirements = 0.5. Cost and feasibility are unknown and unscored.',
            'scope':'Normalized structured fields and imported usable signals; unreviewed report mentions cannot close quantitative prerequisites.',
            'unresolved_scientific_questions':{'state':'not_established','reason':'Archive incompleteness alone cannot establish a scientific knowledge gap.'},
            'coverage':[{'group':i['group'],'requirements':i['requirements'],'comparability':i['comparability']} for i in selected],
            'gaps':candidates,'limits':ranking['limitations']}
