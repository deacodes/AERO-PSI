"""Read-only document extraction. Extracted text is not scientific verification."""
from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import subprocess
import zipfile
import xml.etree.ElementTree as ET
import posixpath

ROOT = Path(__file__).resolve().parents[1]
from .runtime_data import root as runtime_root
RUNTIME_ROOT=runtime_root()
INDEX = RUNTIME_ROOT / 'derived/evidence/documents.json'
CONVERSIONS = ROOT / 'mappings/document_conversions.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract(path, pdf_tool=None):
    suffix = path.suffix.lower()
    if suffix == '.pdf':
        tool = pdf_tool or shutil.which('pdftotext')
        if not tool:
            raise ValueError('pdftotext unavailable; pass --pdftotext PATH')
        result = subprocess.run([str(tool), '-layout', str(path), '-'], capture_output=True, timeout=90, check=True)
        pages = result.stdout.decode('utf-8', errors='replace').split('\f')
        if pages and not pages[-1].strip(): pages.pop()
        return [('page', i+1, text) for i, text in enumerate(pages)]
    if suffix == '.txt':
        # Preserve line numbers even for ISA metadata and tab-separated logs.
        return [('line', i+1, line) for i, line in enumerate(path.read_text(encoding='utf-8-sig', errors='replace').splitlines())]
    if suffix in ('.pptx', '.docx'):
        with zipfile.ZipFile(path) as archive:
            if suffix == '.pptx':
                ns = {'p':'http://schemas.openxmlformats.org/presentationml/2006/main'}
                rels = {r.attrib['Id']:r.attrib['Target'] for r in ET.fromstring(archive.read('ppt/_rels/presentation.xml.rels')) if r.attrib.get('TargetMode') != 'External'}
                ids = ET.fromstring(archive.read('ppt/presentation.xml')).findall('.//p:sldId', ns)
                names = [posixpath.normpath('ppt/'+rels[e.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]) for e in ids]
            else:
                names = ['word/document.xml']
            output = []
            for i, name in enumerate(names):
                tree = ET.fromstring(archive.read(name))
                paragraphs = [' '.join(n.text or '' for n in p.iter() if n.tag.endswith('}t')) for p in tree.iter() if p.tag.endswith('}p')]
                if suffix == '.docx': output.extend(('paragraph', j+1, text) for j, text in enumerate(paragraphs))
                else:
                    output.append(('slide', i+1, '\n'.join(paragraphs)))
                    relname = posixpath.dirname(name)+'/_rels/'+posixpath.basename(name)+'.rels'
                    if relname in archive.namelist():
                        for rel in ET.fromstring(archive.read(relname)):
                            if rel.attrib.get('Type','').endswith('/notesSlide') and rel.attrib.get('TargetMode') != 'External':
                                target = posixpath.normpath(posixpath.dirname(name)+'/'+rel.attrib['Target'])
                                notes = ET.fromstring(archive.read(target))
                                # Exclude slide-number and date/footer placeholders, not actual speaker notes.
                                bodies = []
                                for shape in notes.iter():
                                    if not shape.tag.endswith('}sp'): continue
                                    placeholders = [p.attrib.get('type') for p in shape.iter() if p.tag.endswith('}ph')]
                                    if any(p in ('sldNum', 'dt', 'ftr', 'hdr') for p in placeholders): continue
                                    bodies.extend(n.text or '' for n in shape.iter() if n.tag.endswith('}t'))
                                if any(t.strip() for t in bodies): output.append(('slide_notes', i+1, '\n'.join(bodies)))
            return output
    raise ValueError('Legacy binary document requires a separately reviewed conversion')


def build_index(data_root, output=INDEX, pdf_tool=None, conversions=None):
    data_root = Path(data_root).resolve(); output = Path(output).resolve()
    if output == data_root or data_root in output.parents:
        raise ValueError('Derived evidence must be outside the original archive')
    if conversions is None:
        conversions = json.loads(CONVERSIONS.read_text()) if data_root == (RUNTIME_ROOT/'DATA').resolve() and CONVERSIONS.is_file() else []
    records, reports, seen = [], [], {}
    for path in sorted(data_root.rglob('*')):
        if path.suffix.lower() not in {'.pdf', '.pptx', '.ppt', '.docx', '.doc', '.txt'}: continue
        if not path.is_file() or data_root not in path.resolve().parents: continue
        relative = path.relative_to(data_root).as_posix(); sha = digest(path)
        try:
            conversion = next((c for c in conversions if c['source_path'] == relative and c['source_sha256'] == sha), None)
            conversion_metadata = {}
            if path.suffix.lower() in ('.doc', '.ppt') and conversion:
                converted = (RUNTIME_ROOT/conversion['converted_path']).resolve()
                if (RUNTIME_ROOT/'derived').resolve() not in converted.parents or not converted.is_file() or digest(converted) != conversion['converted_sha256']:
                    raise ValueError('Derived conversion is missing, changed or outside derived/')
                units = [('converted_page', n, t) for _, n, t in extract(converted, pdf_tool)]
                conversion_metadata = {'conversion': conversion, 'conversion_note':'Page numbers refer to the derived PDF, not the original Word pagination. Embedded equations require visual checking.'}
            else:
                units = extract(path, pdf_tool)
            duplicate = seen.get(sha)
            seen.setdefault(sha, relative)
            for unit, number, text in units:
                if not text.strip(): continue
                # Bounded chunks retain exact offsets into the extracted page/slide/paragraph.
                for start in range(0, len(text), 3000):
                    fragment = text[start:start+3000]
                    identity = hashlib.sha256(f'{relative}:{sha}:{unit}:{number}:{start}'.encode()).hexdigest()[:24]
                    records.append({'id': 'document:'+identity, 'kind':'document_excerpt', 'group':relative.split('/')[0], 'title':path.name,
                        'source_path':relative, 'source_sha256':sha, 'source_range':f'{ {"page":"PDF page", "converted_page":"converted PDF page", "slide_notes":"speaker notes for slide"}.get(unit,unit)} {number}, extracted characters {start}-{start+len(fragment)}',
                        'locator':{unit:number, 'character_start':start}, 'text':fragment,
                        'review_state':'extracted_unreviewed', 'duplicate_of':duplicate, **conversion_metadata,
                        'warnings':['Text extraction may omit figures or damage equations; not approved as a numerical parameter or equation source.']})
            reports.append({'source_path':relative,'source_sha256':sha,'status':'extracted','unit_count':len(units),'empty_units':sum(not t.strip() for _,_,t in units),'duplicate_of':duplicate, **conversion_metadata})
        except (ValueError, KeyError, OSError, subprocess.SubprocessError, zipfile.BadZipFile, ET.ParseError) as exc:
            reports.append({'source_path':relative,'source_sha256':sha,'status':'unavailable','reason':str(exc)[:300]})
        if digest(path) != sha: raise RuntimeError('Source changed during extraction')
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_suffix('.tmp')
    temp.write_text(json.dumps({'version':2,'records':records,'reports':reports},ensure_ascii=False),encoding='utf-8')
    os.replace(temp, output)
    return {'documents':len(reports),'extracted':sum(r['status']=='extracted' for r in reports),'chunks':len(records),'unavailable':[r for r in reports if r['status']=='unavailable']}


def document_records(index=INDEX, data_root=RUNTIME_ROOT/'DATA'):
    if not Path(index).is_file(): return []
    data = json.loads(Path(index).read_text())
    # Never expose stale excerpts as current evidence after a source changes.
    checks = {}
    result = []
    for record in data['records']:
        key = record['source_path']; path = (Path(data_root)/key).resolve()
        if Path(data_root).resolve() not in path.parents: continue
        if key not in checks: checks[key] = digest(path) if path.is_file() else None
        conversion = record.get('conversion')
        if conversion:
            converted = (RUNTIME_ROOT/conversion['converted_path']).resolve()
            cache_key = str(converted)
            if cache_key not in checks:
                checks[cache_key] = digest(converted) if (RUNTIME_ROOT/'derived').resolve() in converted.parents and converted.is_file() else None
            if checks[cache_key] != conversion['converted_sha256']: continue
        if checks[key] == record['source_sha256']: result.append(record)
    return result


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser(); parser.add_argument('--data-root',type=Path,default=RUNTIME_ROOT/'DATA'); parser.add_argument('--output',type=Path,default=INDEX); parser.add_argument('--pdftotext')
    args=parser.parse_args(); print(json.dumps(build_index(args.data_root,args.output,args.pdftotext),indent=2))
