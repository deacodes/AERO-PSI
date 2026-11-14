"""Read-only, paginated source tables; values and original columns are preserved."""
import gzip
import json
from pathlib import Path
from aero_psi_discovery import manifest_records

ROOT=Path(__file__).resolve().parent


def datasets(catalog):
    tables={r['source_path']:r for r in catalog.get('raw_tables',[])}
    imported={r['source_path']:r for r in manifest_records() if r.get('status')=='imported'}
    items=[]
    for f in catalog['files']:
        path=f['source_path'];table=tables.get(path);run=imported.get(path)
        items.append({**{k:f.get(k) for k in ('source_path','source_sha256','investigation_group','format','file_role','material_candidate','bytes')},
            'view':'table' if table is not None else 'run' if run else 'reference',
            'row_count':len(table['rows']) if table is not None else run.get('analysis',{}).get('row_count') if run else None,
            'column_count':len(table['columns']) if table is not None else run.get('header_count') if run else None,
            'worksheet':run.get('worksheet') if run else None})
    return {'items':items,'groups':sorted({i['investigation_group'] for i in items})}


def cell_state(value,run=False):
    if value is None or not str(value).strip(): return 'missing'
    raw=str(value).strip()
    if run and raw in ('-10','-10.0'):return 'sentinel'
    from aero_psi_research import number
    return 'numeric' if number(value) is not None else 'text'


def table_page(catalog,payload):
    path=payload.get('source_path');offset=payload.get('offset',0);limit=payload.get('limit',50);query=payload.get('query','')
    if type(offset) is not int or offset<0 or type(limit) is not int or not 1<=limit<=100:raise ValueError('Use a nonnegative offset and 1–100 rows per page')
    if not isinstance(query,str) or len(query)>200:raise ValueError('Search must be at most 200 characters')
    if not isinstance(path,str) or not any(f['source_path']==path for f in catalog['files']):raise ValueError('Choose a source file from the archive')
    table=next((r for r in catalog.get('raw_tables',[]) if r['source_path']==path),None)
    run=None;worksheet=None
    if table is not None:
        columns=table['columns'];checksum=table['source_sha256'];iterator=({'source_row':n,'values':r} for n,r in enumerate(table['rows'],2))
    else:
        run=next((r for r in manifest_records() if r['source_path']==path and r.get('status')=='imported'),None)
        if not run:raise ValueError('This file is a reference or an unimported workbook; no tabular view is available')
        derived=(ROOT/run['derived_path']).resolve()
        if not derived.is_relative_to(ROOT/'derived'):raise ValueError('Invalid derived source path')
        checksum=run['source_sha256'];worksheet=run.get('worksheet');columns=[]
        def records():
            with gzip.open(derived,'rt',encoding='utf-8') as handle:
                for line in handle:yield json.loads(line)
        iterator=records()
    result=[];matched=0;total=0;query=query.casefold()
    for row in iterator:
        total+=1
        if not columns:columns=list(row['values'])
        if query and not any(query in str(v).casefold() for v in row['values'].values()) and query!=str(row['source_row']):continue
        if offset<=matched<offset+limit:
            values=[row['values'].get(k) for k in columns]
            result.append({'source_row':row['source_row'],'values':values,'states':[cell_state(v,run is not None) for v in values]})
        matched+=1
    return {'source_path':path,'source_sha256':checksum,'worksheet':worksheet,'columns':columns,'rows':result,'total_rows':total,'matching_rows':matched,'offset':offset,'limit':limit,
        'scope':'Original table values. Blank cells are retained; zero is a recorded value. Color describes value type, not scientific validity.' if not run else 'All columns of the imported worksheet, without graph downsampling. Original -10 values are retained and flagged as possible instrument sentinels; confirm the channel convention. Other workbook sheets are not included.'}


def interpret(catalog,payload):
    from aero_psi_copilot import ask
    page=table_page(catalog,{k:v for k,v in payload.items() if k in ('source_path','offset','query')}|{'limit':30})
    selected=payload.get('source_row')
    if selected is not None:
        if type(selected) is not int:raise ValueError('Source row must be an integer')
        # Find the actual row; never accept client-supplied cell values.
        offset=0;found=None
        while offset<page['total_rows']:
            chunk=table_page(catalog,{'source_path':page['source_path'],'offset':offset,'limit':100})
            found=next((r for r in chunk['rows'] if r['source_row']==selected),None)
            if found:break
            offset+=100
        if not found:raise ValueError('Selected source row was not found')
        page['rows']=[found]
    scope=f"Source row {selected}" if selected is not None else f"First {len(page['rows'])} rows of the requested page/filter; not the full dataset"
    evidence={'id':'runtime:archive-table','kind':'verified_source_table','title':'Verified archive table context','source_path':page['source_path'],'source_range':scope,'text':json.dumps(page,ensure_ascii=False)}
    # Keep table context intact rather than silently cutting off wide rows.
    evidence['text']=json.dumps({'columns':page['columns'],'rows':page['rows'][:3],'total_rows':page['total_rows'],'matching_rows':page['matching_rows'],'scope':scope+'; at most three source rows supplied as examples','source_sha256':page['source_sha256']},ensure_ascii=False)
    answer=ask(catalog,payload.get('question','Summarize what this dataset records, its useful comparisons and its limitations.'),runtime_evidence=[evidence],allow_background=True,history=payload.get('history'))
    answer['table_scope']=scope+'; at most three source rows supplied as examples'
    return answer
