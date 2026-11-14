"""Question-led exploration of actual archive tables and source passages."""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re

from aero_psi_discovery import rank_for_question, query_spec, manifest_records, assess_requirement, PROFILES, REQUIREMENTS
from aero_psi_copilot import retrieve, ask
from aero_psi_optical import summary, time_series, source_point

ROOT=Path(__file__).resolve().parent


def number(value):
    if isinstance(value,bool): return None
    if not re.fullmatch(r'[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?',str(value).strip()): return None
    result=float(value)
    return result if math.isfinite(result) else None


def clean_title(meta):
    title=meta.get('title','')
    return meta['group'] if not title or 'cut and paste' in title.lower() or title.lower().startswith('original') else title


def explore(catalog,payload):
    question,goal,concepts=query_spec(payload)
    ranking=rank_for_question(catalog,payload)
    if not ranking['items']: raise ValueError('No investigations are available in this archive')
    group=payload.get('group') or ranking['items'][0]['group']
    meta=next((r for r in catalog.get('investigations',[]) if r['group']==group),None)
    if meta is None: raise ValueError('Choose an investigation from this archive')
    rows=[r for r in catalog.get('normalized_experiments',[]) if r['source_path'].split('/')[0]==group and any(v.get('state')=='observed' and str(v.get('value','')).strip() for v in r['fields'].values())]
    paths=sorted({r['source_path'] for r in rows})
    source_path=payload.get('source_path')
    if source_path is not None and not any(f['source_path']==source_path and source_path.split('/')[0]==group for f in catalog.get('files',[])):
        raise ValueError('Choose a source file from the selected investigation')
    table=payload.get('table') or (source_path if source_path in paths else None) or (paths[0] if paths else None)
    if table is not None and table not in paths: raise ValueError('Choose a table from the selected investigation')
    selected=[r for r in rows if r['source_path']==table]
    fields={}
    for row in selected:
        for key,cell in row['fields'].items():
            if cell.get('state')=='observed' and str(cell.get('value','')).strip():
                fields.setdefault(key,{'key':key,'label':cell.get('source_column') or key,'values':[]})['values'].append(cell['value'])
    columns=[]
    for f in fields.values():
        nums=[n for v in f['values'] if (n:=number(v)) is not None]
        columns.append({k:f[k] for k in ('key','label')}|{'recorded_count':len(f['values']),'numeric_count':len(nums),'minimum':min(nums) if nums else None,'maximum':max(nums) if nums else None,'distinct_count':len(set(map(str,f['values']))),'examples':list(dict.fromkeys(map(str,f['values'])))[:8]})
    docs=retrieve(catalog,question+' '+group,limit=12)
    docs=[r for r in docs if r.get('source_path','').split('/')[0]==group and r.get('kind') in ('document_excerpt','reviewed_source_note','document') or r.get('kind')=='consulted_web_reference']
    # Retrieval kinds vary; preserve any document/review ID, then require selected group.
    if not any(r.get('id','').startswith(('document:','review:')) for r in docs):
        docs=[r for r in retrieve(catalog,question+' '+group,limit=12) if r.get('id','').startswith(('document:','review:')) and r.get('source_path','').split('/')[0]==group]
    runs=[r for r in manifest_records() if r.get('group')==group and r.get('status')=='imported']
    requirements=[assess_requirement(k,rows,runs) for k in PROFILES[goal][1]]
    findings=[]
    for r in requirements:
        exists=r['source_count']>0
        passages=[d for d in docs if any(t in d.get('text','').lower() for t in re.findall(r'[a-z]{4,}',r['label'].lower()))][:2]
        details=[]
        for field in REQUIREMENTS[r['key']][2]:
            cells=[row['fields'][field] for row in rows if row['fields'].get(field,{}).get('state')=='observed' and str(row['fields'][field].get('value','')).strip()]
            if cells:
                numeric=sum(number(c['value']) is not None for c in cells)
                label=cells[0].get('source_column') or field
                details.append(f"{len(cells)} rows contain {label}"+(f"; {numeric} contain numeric values" if numeric else '')+'.')
        finding=' '.join(details) if details else f"{r['source_count']} run channels have usable source-derived metrics."
        findings.append({'key':r['key'],'title':r['label'],'state':'recorded' if exists else 'review_report' if passages else 'measurement_needed',
            'finding':finding if exists else ('Relevant report passages are available; extract the applicable measurement and its conditions before numerical use.' if passages else 'No matching values were found in the supplied structured records for this investigation.'),
            'next_action':('Check that the values belong to the same run and retain the original units.' if exists else f"Specify how to measure {r['label'].lower()}, including units, timing and uncertainty; check the source reports before proposing a new test."),
            'sources':r['sources'],'passages':[d['id'] for d in passages]})
    response_keys={'flame_geometry':['visible_flame_extinction_diameter_mm','flame_length_mm','flame_diameter_mm','flame_height_mm'],'extinction':['visible_flame_extinction_diameter_mm','burning_rate_mm'],'flammability':['flame_spread_rate']}.get(goal,[])
    response_summary=[{'measurement':c['label'],'numeric_rows':c['numeric_count'],'total_rows':len(selected),'minimum':c['minimum'],'maximum':c['maximum']} for c in columns if c['key'] in response_keys]
    observed_fields=[c['label'] for c in columns if c['numeric_count']]
    missing=[f['title'] for f in findings if f['state']!='recorded']
    overview={'question':question,'group':group,'title':clean_title(meta),'table_records':len(selected),'group_records':len(rows),
              'available':observed_fields,'next_questions':missing,'response_summary':response_summary,
              'explanation':f"{group} has {len(rows)} populated experiment-table rows and {len(runs)} imported time-series files. The table view below retains source values; report evidence is shown separately."}
    grid=[]
    for row in selected:
        grid.append({'source_row':row['source_row'],'source_path':row['source_path'],'source_sha256':row['source_sha256'],
                     'values':{k:v['value'] if v.get('state')=='observed' else None for k,v in row['fields'].items()}})
    from aero_psi_gap_assessment import assess
    assessment=assess(question,goal,group,rows,runs,findings)
    return {'selection':{'automatic':not bool(payload.get('group')),'tied_top_groups':[i['group'] for i in ranking['items'] if i['score']==ranking['items'][0]['score']], 'formula':ranking['formula'], 'candidates':[{'group':i['group'],'score':i['score'],'matched_concepts':[m['concept'] for m in i['matches']], 'unmatched_concepts':i['unmatched_concepts']} for i in ranking['items']]},'selected_source':source_path,'assessment':assessment,'question':question,'goal':goal,'group':group,'overview':overview,
            'groups':[{'group':i['group'],'title':clean_title(i),'score':next((v['score'] for v in ranking['items'] if v['group']==i['group']),0)} for i in catalog['investigations']],
            'tables':[{'path':p,'row_count':sum(r['source_path']==p for r in rows)} for p in paths],
            'selected_table':table,'columns':columns,'rows':grid,'findings':findings,'passages':docs,
            'runs':[{'source_path':r['source_path'],'worksheet':r.get('worksheet'),'material':r.get('material_candidate'),'signals':list(r.get('analysis',{}).get('available_signals',{}))} for r in runs],
            'scope':'An absent value in this supplied collection is a data requirement, not proof that no published experiment exists. Separate tables and runs are not automatically comparable.'}


def interpret(catalog,payload):
    context=explore(catalog,payload)
    question=payload.get('followup') or payload.get('question')
    if not isinstance(question,str) or not 1<=len(question.strip())<=2000: raise ValueError('Enter a question of 1–2000 characters')
    supplied=payload.get('source_rows',[])
    if not isinstance(supplied,list) or len(supplied)>30 or any(type(i) is not int for i in supplied): raise ValueError('Select up to 30 source rows')
    evidence=list(context['passages'])
    if payload.get('run'):
        run=next((r for r in context['runs'] if r['source_path']==payload['run']),None)
        if not run or payload.get('signal') not in run['signals']: raise ValueError('Choose a signal from the selected investigation')
        indices=supplied
        if not indices:
            samples=time_series(ROOT/'derived/reports/ingestion_manifest.json',ROOT,run['source_path'],[payload['signal']],10)
            indices=[p['source_row'] for p in samples['points'][:8]]
        for row in indices:
            point=source_point(ROOT/'derived/reports/ingestion_manifest.json',ROOT,run['source_path'],payload['signal'],row)
            evidence.append({'id':f"runtime:research-point:{hashlib.sha256(run['source_path'].encode()).hexdigest()[:12]}:{row}",'kind':'verified_observed_sample','title':payload['signal'],
                'source_path':run['source_path'],'source_range':f"worksheet {point['worksheet']}, row {row}",'point':point,'text':json.dumps(point,ensure_ascii=False)})
    else:
        available={r['source_row']:r for r in context['rows']}
        if any(i not in available for i in supplied): raise ValueError('Selected rows must belong to the displayed source table')
        selected=[available[i] for i in supplied] if supplied else context['rows'][:8]
        for row in selected:
            evidence.append({'id':f"table:{row['source_path']}:{row['source_row']}",'kind':'source_table_row','title':f"{context['group']} — row {row['source_row']}",'source_path':row['source_path'],'source_range':f"row {row['source_row']}",
                'text':json.dumps({'source_sha256':row['source_sha256'],'values':row['values'],'columns':[{k:c[k] for k in ('key','label')} for c in context['columns']]},ensure_ascii=False)})
    evidence.append({'id':'runtime:research:'+hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()[:20], 'kind':'archive_comparison','title':'Current question and measurement requirements','source_path':context['selected_table'] or context['group'],'source_range':'Question-specific source review','text':json.dumps({'overview':context['overview'],'requirements':context['assessment'],'scope':context['scope']},ensure_ascii=False)})
    return ask(catalog,question,runtime_evidence=evidence,allow_background=True,history=payload.get('history'),information_mode=payload.get('mode','auto'))
