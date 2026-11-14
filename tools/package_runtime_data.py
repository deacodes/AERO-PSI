"""Package required scientific data separately from Git; never include user work or credentials."""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile
ROOT=Path(__file__).resolve().parents[1]
PATHS=['DATA','aero_psi_catalog.json','derived/timeseries','derived/evidence','derived/reports/ingestion_manifest.json']
def files():
    result=[]
    for name in PATHS:
        path=ROOT/name
        if not path.exists():raise SystemExit('Missing required runtime data: '+name)
        for f in sorted(path.rglob('*')) if path.is_dir() else [path]:
            if f.is_file() and not f.is_symlink() and f.name!='.DS_Store':result.append(f)
    return result
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args();items=files()
    print(json.dumps({'files':len(items),'uncompressed_bytes':sum(f.stat().st_size for f in items),'included':PATHS,'excluded':['credentials','.env','derived/studio','derived/investigations']},indent=2))
    if args.output:
        target=args.output.resolve();target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():raise SystemExit('Output already exists; choose a new filename')
        with tarfile.open(target,'w:gz') as archive:
            for f in items:archive.add(f,arcname=f.relative_to(ROOT),recursive=False)
        digest=hashlib.sha256()
        with target.open('rb') as handle:
            for chunk in iter(lambda:handle.read(1024*1024),b''):digest.update(chunk)
        print(json.dumps({'archive':str(target),'sha256':digest.hexdigest(),'bytes':target.stat().st_size}))
