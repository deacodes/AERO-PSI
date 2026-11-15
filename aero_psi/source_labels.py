"""Presentation labels only; source paths, hashes and scientific joins never change."""
import json
from functools import lru_cache
from pathlib import Path

@lru_cache(maxsize=1)
def labels():
    return json.loads((Path(__file__).resolve().parents[1]/'mappings/source_labels.json').read_text())

def presentation(record, view=None):
    path=record['source_path'];entry=labels().get(path,{})
    kind=entry.get('kind','Reference file')
    if view=='run' and kind=='Run workbook':kind='Run'
    return {'display_name':entry.get('title',Path(path).stem.replace('_',' ')),
            'filename':Path(path).name,'data_kind':kind,
            'tags':[kind,record.get('investigation_group',path.split('/')[0]),record.get('format',Path(path).suffix.lstrip('.')).upper()]}
