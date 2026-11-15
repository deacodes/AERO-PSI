"""Read-only Cloud Storage runtime snapshot, verified into a separate local cache."""
from pathlib import Path
import os
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
import threading
from urllib.parse import quote

PROJECT=Path(__file__).resolve().parents[1]
def root():return Path(os.environ.get('AERO_PSI_RUNTIME_ROOT',PROJECT)).resolve()
def allowed(name):
    p=Path(name)
    return not p.is_absolute() and '..' not in p.parts and (name=='aero_psi_catalog.json' or name.startswith(('DATA/','derived/timeseries/','derived/evidence/')) or name=='derived/reports/ingestion_manifest.json')
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def initialize():
    env=PROJECT/'.env'
    if env.exists():
        for line in env.read_text().splitlines():
            if line.strip().startswith('#') or '=' not in line:continue
            key,value=line.split('=',1);os.environ.setdefault(key.strip(),value.strip().strip('"\''))
    bucket=os.environ.get('AERO_PSI_STORAGE_BUCKET','')
    if not bucket:return
    cache=Path(os.environ.get('AERO_PSI_CLOUD_CACHE',PROJECT/'cache/cloud-runtime'))/bucket
    cache=cache.resolve();cache.mkdir(parents=True,exist_ok=True)
    import google.auth
    from google.auth.transport.requests import AuthorizedSession,Request
    credentials,_=google.auth.default(scopes=['https://www.googleapis.com/auth/devstorage.read_only']);credentials.refresh(Request())
    session=AuthorizedSession(credentials);base='https://storage.googleapis.com/storage/v1/b/'+quote(bucket,safe='')
    items=[];token=None
    while True:
        r=session.get(base+'/o',params={'fields':'items(name,size,generation,metadata),nextPageToken',**({'pageToken':token} if token else {})},timeout=60);r.raise_for_status();data=r.json();items.extend(x for x in data.get('items',[]) if allowed(x['name']));token=data.get('nextPageToken')
        if not token:break
    names={x['name'] for x in items}
    for required in ('aero_psi_catalog.json','derived/reports/ingestion_manifest.json','derived/evidence/documents.json'):
        if required not in names:raise RuntimeError('Cloud runtime missing '+required)
    local=threading.local();lock=threading.Lock();counts={'downloaded':0,'cached':0}
    def fetch(item):
        name=item['name'];target=(cache/name).resolve()
        if not target.is_relative_to(cache):raise ValueError('Invalid cloud path')
        expected=item.get('metadata',{}).get('sha256','')
        if len(expected)!=64:raise RuntimeError('Cloud object lacks SHA-256 metadata: '+name)
        if target.is_file() and target.stat().st_size==int(item['size']) and digest(target)==expected:
            with lock:counts['cached']+=1
            return
        if not hasattr(local,'session'):local.session=AuthorizedSession(credentials)
        r=local.session.get(base+'/o/'+quote(name,safe=''),params={'alt':'media','generation':item['generation']},stream=True,timeout=300);r.raise_for_status()
        target.parent.mkdir(parents=True,exist_ok=True)
        import tempfile
        handle=tempfile.NamedTemporaryFile(dir=target.parent,delete=False);tmp=Path(handle.name)
        try:
            with handle:
                for block in r.iter_content(1024*1024):handle.write(block)
            if tmp.stat().st_size!=int(item['size']) or digest(tmp)!=expected:raise RuntimeError('Cloud checksum mismatch: '+name)
            tmp.replace(target)
        finally:tmp.unlink(missing_ok=True);r.close()
        with lock:counts['downloaded']+=1
    print(json.dumps({'event':'cloud_runtime_loading','bucket':bucket,'files':len(items)}),flush=True)
    with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(fetch,items))
    os.environ['AERO_PSI_RUNTIME_ROOT']=str(cache)
    print(json.dumps({'event':'cloud_runtime_ready','bucket':bucket,**counts}),flush=True)
