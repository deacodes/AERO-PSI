"""Deterministic full-table summaries and small source-row plots for SI discussion.

No model-generated coordinates, calibration, interpolation or inferred time units.
"""
import gzip
import json
import math
import re
from .discovery import manifest_records
from .research import number
from .runtime_data import root


def _sample(points, target=240):
    """Preserve each bucket's extrema; break across missing/filtered source rows."""
    if len(points) <= target:
        return points
    width = math.ceil(len(points) / (target // 4))
    chosen = set()
    for start in range(0, len(points), width):
        indices = list(range(start, min(start + width, len(points))))
        valid = [i for i in indices if points[i]['value'] is not None]
        chosen.update((indices[0], indices[-1]))
        if valid:
            chosen.update((min(valid, key=lambda i: points[i]['value']), max(valid, key=lambda i: points[i]['value'])))
    output = []
    previous = None
    for i in sorted(chosen):
        if previous is not None and any(points[j]['value'] is None or points[j]['row'] != points[j-1]['row'] + 1 for j in range(previous+1, i+1)):
            output.append({'row': points[i]['row'], 'value': None})
        output.append(points[i]); previous = i
    return output


def analyze(catalog, payload, page):
    path = page['source_path']
    table = next((t for t in catalog.get('raw_tables', []) if t['source_path'] == path), None)
    if table is not None:
        rows = ({'source_row':i, 'values':v} for i,v in enumerate(table['rows'],2))
        is_run = False
    else:
        run = next(r for r in manifest_records() if r['source_path'] == path and r.get('status') == 'imported')
        filename = (root()/run['derived_path']).resolve()
        if not filename.is_relative_to(root()/'derived'): raise ValueError('Invalid derived path')
        def read():
            with gzip.open(filename, 'rt', encoding='utf-8') as stream:
                for line in stream: yield json.loads(line)
        rows = read(); is_run = True
    query = str(payload.get('query', '')).casefold()
    selected = payload.get('source_row')
    columns = page['columns']
    question = payload.get('question','').casefold()
    words = set(re.findall(r'[a-z]{3,}', question)) - {'what','this','that','show','data','table','does','with','from','about','columns'}
    def score(c):
        name = c.casefold()
        relevance = sum(8 for w in words if w in name)
        if 'concentration' in question and any(k in name for k in ('ptrak','dusttrak')): relevance += 12
        relevance += 5 if any(k in name for k in ('measurement','concentration','temperature','flowrate','pressure')) else 0
        relevance -= 10 if any(k in name for k in ('counter','number','time','sample','setpoint','enable','mode')) and 'concentration' not in name and 'measurement' not in name else 0
        return relevance
    stats = {c:{'valid':0,'missing_or_nonnumeric':0,'possible_sentinel':0,'min':None,'max':None,'first':None,'last':None} for c in columns}
    plot_columns = set(sorted(columns, key=score, reverse=True)[:12])
    series = {c:[] for c in plot_columns}
    count = 0; first_row = last_row = None
    for row in rows:
        r = row['source_row']; values = row['values']
        if selected is not None and r != selected: continue
        if query and selected is None and query != str(r) and not any(query in str(v).casefold() for v in values.values()): continue
        count += 1; first_row = r if first_row is None else first_row; last_row = r
        for c in columns:
            value = number(values.get(c)); item = stats[c]
            if value is not None and not math.isfinite(value): value = None
            if is_run and value in (-10, -999):
                item['possible_sentinel'] += 1; value = None
            elif value is None: item['missing_or_nonnumeric'] += 1
            point = {'row':r,'value':value}
            if c in series: series[c].append(point)
            if value is None: continue
            item['valid'] += 1
            if item['first'] is None: item['first'] = point
            item['last'] = point
            if item['min'] is None or value < item['min']['value']: item['min'] = point
            if item['max'] is None or value > item['max']['value']: item['max'] = point
    available = [c for c in columns if stats[c]['valid']]
    picked = sorted(available,key=score,reverse=True)[:8]
    summaries = [{'column':c,**stats[c]} for c in picked]
    charts=[]
    for c in picked:
        if stats[c]['valid'] < 2 or c not in series: continue
        points=_sample(series[c])
        charts.append({'column':c,'points':points,'statistics':stats[c], 'sampled':len(series[c])>240})
    scope = (f'Selected source row {selected}' if selected is not None else f'All {count} matching rows in the imported worksheet' if query else f'All {count} rows in the imported worksheet')
    return {'source_path':path,'source_sha256':page['source_sha256'],'worksheet':page['worksheet'],
            'scope':scope,'row_count':count,'source_row_range':[first_row,last_row],'filter':query,
            'x_label':'Source row (not elapsed time)','columns':columns,'summaries':summaries,'charts':charts,
            'limitations':['Only this imported worksheet is analyzed; other workbook sheets are not included. Numeric summaries cover the listed columns, not every column.',
                          'Values retain source column labels and units; calibration and instrument validity are not established.',
                          'Possible -10 and -999 instrument sentinel values are excluded from numeric summaries and plots for imported runs; confirm the channel convention.',
                          'Graphs use source-row order, not inferred time. Lines break at excluded or missing rows. Large plots retain sampled extrema; summaries use every matching row.',
                          'First-to-last differences and extrema are descriptive, not evidence of a mechanism or a monotonic trend.']}
