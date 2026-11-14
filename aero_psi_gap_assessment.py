"""Deterministic evidence readiness, not scientific novelty or causal inference."""
import hashlib
import json
from aero_psi_discovery import REQUIREMENTS, proposal_for_requirement, ref

VERSION = 'evidence-readiness-1'
# Transparent workflow ordering; these are not NASA-derived scientific scores.
CORE = {'size', 'gravity', 'angular', 'optics', 'calibration', 'flame_dimensions', 'spread', 'extinction', 'detector'}


def assess(question, goal, group, rows, runs, findings):
    from aero_psi_research import number
    matrix, actions = [], []
    for finding in findings:
        key = finding['key']
        label, signals, fields = REQUIREMENTS[key]
        numeric_required = key not in {'material', 'optics', 'calibration'}
        sources, values, row_keys = [], [], set()
        for row in rows:
            for field in fields:
                cell = row['fields'].get(field, {})
                if cell.get('state') != 'observed': continue
                value = cell.get('value')
                if value is None or not str(value).strip(): continue
                if numeric_required and number(value) is None: continue
                sources.append(ref(row, 'table', cell.get('source_column')))
                values.append(value)
                row_keys.add((row['source_path'], row['source_row']))
        run_count = 0
        for run in runs:
            analysis = run.get('analysis', {})
            for signal in signals:
                if (signal in analysis.get('available_signals', {}) and
                    analysis.get('metrics', {}).get(signal, {}).get('status') == 'available' and
                    signal not in analysis.get('fully_zero_core_signals', [])):
                    sources.append(ref(run, 'run', analysis['available_signals'][signal])); run_count += 1
        state = 'values_available' if sources else 'report_review' if finding['passages'] else 'not_found'
        impact = 'Blocks the requested comparison' if key in CORE else 'Needed to control or interpret the comparison'
        entry = {'key':key, 'label':label, 'state':state, 'numeric_required':numeric_required,
                 'table_row_count':len(row_keys), 'usable_channel_count':run_count,
                 'distinct_recorded_values':len(set(map(str,values))), 'sources':sources[:5],
                 'source_count':len(sources), 'report_ids':finding['passages'], 'impact':impact,
                 'limit':('Extinction diameter describes the extinction endpoint, not the entire flame history. ' if key=='flame_dimensions' and any('visible_flame_extinction_diameter_mm' in r['fields'] for r in rows) else '')+'Values are source records, not proof of calibration, synchronization or comparability.'}
        matrix.append(entry)
        if state != 'values_available':
            proposal = proposal_for_requirement({'key':key,'label':label},group,question)
            proposal['expected_benefit']=proposal['expected_benefit'].replace('indexed prerequisite','measurement requirement')
            # Flame dimensions must not inherit aerosol-specific acceleration controls.
            if goal == 'flame_geometry' and key == 'gravity':
                proposal.update(objective='Pair flame dimensions with measured acceleration',
                    varied_parameter='measured acceleration condition',
                    controls='fuel, geometry, oxygen, pressure, flow and the defined flame-measurement time',
                    required_outputs='synchronized acceleration and flame-image dimensions with spatial calibration, uncertainty and matched run IDs',
                    analysis_plan='Compare matched conditions and report uncertainty; extinction diameter alone does not describe flame size throughout burning.')
            tier = 1 if key in CORE else 2
            actions.append({'key':key,'title':('Review evidence for ' if state=='report_review' else 'Establish ')+label.lower(),
                'category':'report_verification' if state=='report_review' else 'measurement_requirement',
                'priority':tier,'priority_reason':impact+'. Review existing reports first; hardware cost and feasibility are not scored.',
                'reason':finding['finding'],'proposal':proposal,'sources':sources[:5],'report_ids':finding['passages']})
    available = [m for m in matrix if m['state']=='values_available']
    # Co-occurrence is a necessary check, never a sufficient validity claim.
    row_sets = []
    for entry in matrix:
        fields = REQUIREMENTS[entry['key']][2]
        if not fields: row_sets.append(set()); continue
        row_sets.append({(r['source_path'],r['source_row']) for r in rows if any(
            r['fields'].get(f,{}).get('state')=='observed' and
            (number(r['fields'][f].get('value')) is not None if entry['numeric_required'] else bool(str(r['fields'][f].get('value','')).strip()))
            for f in fields)})
    joint = set.intersection(*row_sets) if row_sets else set()
    if matrix:
        actions.append({'key':'comparability','title':'Establish a matched comparison',
            'category':'comparability','priority':2,
            'priority_reason':'Co-occurrence and calibration must be reviewed before interpreting a difference as a gravity or material effect.',
            'reason':f'{len(joint)} structured rows contain all required fields. Cross-file synchronization and calibration have not been established.',
            'sources':[], 'report_ids':[],
            'proposal':{'objective':'Establish which records can be compared','first_action':'Select source runs and record their identity, timing, units, calibration and controlled conditions.',
                'varied_parameter':'the factor specified in the research question','controls':'all other conditions relevant to the selected response',
                'required_outputs':'a reviewed run-pair table with source references, uncertainty and exclusion reasons',
                'analysis_plan':'Compare only matched records; label unmatched records descriptive, not causal.',
                'expected_benefit':'Prevent apparent differences from being attributed to an uncontrolled factor.',
                'feasibility':{'state':'requires_review'}}})
    actions.sort(key=lambda a:(a['priority'],a['key']))
    if not matrix:
        verdict='Define the response and comparison'
        explanation='No declared measurement profile matches this question. Choose a focus or develop a source-review investigation; this is not an automatic finding of missing research.'
    elif len(available)<len(matrix):
        verdict='Partial evidence — comparison not yet supported'
        explanation=f'{len(available)} of {len(matrix)} prerequisites have recorded values. Resolve the listed evidence requirements and review matched conditions before making the requested comparison.'
    else:
        verdict='Candidate evidence — matching and calibration still required'
        explanation='Recorded values cover the declared prerequisites, but this does not establish a validated or causal comparison.'
    payload={'version':VERSION,'question':question,'goal':goal,'group':group,'verdict':verdict,'explanation':explanation,
        'matrix':matrix,'actions':actions,'joint_structured_rows':len(joint),
        'supported_now':[f"Inspect {m['label'].lower()} in {m['table_row_count']} structured rows and {m['usable_channel_count']} usable imported channels." for m in available],
        'not_supported':['Treating archive absence as an unresolved scientific knowledge gap.','Attributing differences to gravity without matched conditions and calibration.'],
        'priority_rule':'Priority 1: missing response, gravity, size or calibration/model prerequisites. Priority 2: controls and comparability. Equal priorities are ties; ordering within a tie is alphabetical, not scientific importance.',
        'scope':'Selected investigation, normalized structured rows and imported channel metrics. Report matches are leads only. No cross-run join or exhaustive literature search is implied.'}
    payload['id']=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()[:20]
    return payload
