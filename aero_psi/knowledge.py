"""Source-linked review notes and explicitly consulted web references.

These are retrieval material, never canned answers. A reviewed passage is not a
validated experiment, and an identified equation is not an executable parameter.
"""
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
from .runtime_data import root as runtime_root
RUNTIME_ROOT=runtime_root()
NOTES = ROOT / 'mappings/scientific_review.json'
WEB = ROOT / 'mappings/scientific_web_references.json'


def review_records(documents, notes_path=NOTES, web_path=WEB):
    units = {}
    paths = {}
    for record in documents:
        paths.setdefault(record.get('source_sha256'), set()).add(record['source_path'])
        locator = record.get('locator', {})
        kind = next((k for k in locator if k != 'character_start'), None)
        key = (record['source_path'], kind, locator.get(kind))
        units.setdefault(key, []).append(record)
    output = []
    notes = json.loads(Path(notes_path).read_text()).get('notes', []) if Path(notes_path).is_file() else []
    for note in notes:
        # Exact duplicate source copies can share a note, but retain their own path.
        for path in sorted(paths.get(note['source_sha256'], [])):
            support = []
            for anchor in note['anchors']:
                fragments = sorted(units.get((path, anchor['kind'], anchor['number']), []), key=lambda r:r['locator']['character_start'])
                text = ''.join(r['text'] for r in fragments)
                if anchor['quote'] not in text: break
                support.extend(r['id'] for r in fragments)
            else:
                identity = hashlib.sha256((path+json.dumps(note,sort_keys=True)).encode()).hexdigest()[:24]
                output.append({'id':'review:'+identity, 'kind':'reviewed_source_note',
                    'group':path.split('/')[0], 'title':note['title'], 'source_path':path,
                    'source_sha256':note['source_sha256'], 'source_range':note['source_range'],
                    'review_state':note['review_state'], 'classification':note['classification'],
                    'text':note['text'], 'anchors':note['anchors'], 'supporting_source_ids':support,
                    'warnings':note.get('warnings', []), 'quantitative_use':'Not automatically approved as a model input',
                    'equations':note.get('equations', []), 'reviewed_on':note['reviewed_on']})
    references = json.loads(Path(web_path).read_text()).get('references', []) if Path(web_path).is_file() else []
    for reference in references:
        url = urlsplit(reference.get('source_url', ''))
        if url.scheme != 'https' or not url.hostname or url.username or url.password: continue
        if not reference.get('accessed_on') or reference.get('status') != 'consulted': continue
        identity = hashlib.sha256(json.dumps(reference,sort_keys=True).encode()).hexdigest()[:24]
        output.append({**reference, 'id':'web:'+identity, 'kind':'consulted_web_reference',
            'group':'REFERENCE', 'source_path':reference['source_url'],
            'review_state':'Consulted reference summary', 'source_range':reference['scope'],
            'text':reference['summary'], 'warnings':['A dated reference summary; not a live web search for this answer.']})
    return output


def review_catalog():
    from aero_psi.evidence import document_records
    documents = document_records()
    records = review_records(documents)
    active = {d['source_path'] for d in documents}
    report = RUNTIME_ROOT/'derived/evidence/review/coverage.json'
    coverage = json.loads(report.read_text()) if report.is_file() else {}
    return {'scope':coverage.get('review_claim', 'Document review has not been built.'),
        'source_files':len(active), 'distinct_sources':len({d['source_sha256'] for d in documents}),
        'excerpts':len(documents), 'notes':records,
        'files':[{k:v for k,v in f.items() if k not in ('text_json','text_path')} for f in coverage.get('files', []) if f['source_path'] in active],
        'web_policy':'Only listed, consulted references can be cited as web sources. General model knowledge is not live browsing.'}
