"""Upload the explicit runtime allowlist to a private bucket, without overwrites.

Dry-run by default. Uses existing ADC; never uploads credentials or saved work.
"""
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import sys
import threading
import time
from urllib.parse import quote

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.package_runtime_data import files


def fingerprints(path):
    sha=hashlib.sha256();md5=hashlib.md5()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):
            sha.update(block);md5.update(block)
    return {'path':path.relative_to(ROOT).as_posix(),'bytes':path.stat().st_size,
            'sha256':sha.hexdigest(),'md5_base64':base64.b64encode(md5.digest()).decode()}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bucket',required=True)
    parser.add_argument('--upload',action='store_true')
    args=parser.parse_args()
    records=[fingerprints(p) for p in files()]
    output=ROOT/'output/cloud-upload';output.mkdir(parents=True,exist_ok=True)
    (output/'runtime-manifest.json').write_text(json.dumps({'files':records},indent=2)+'\n')
    print(json.dumps({'bucket':args.bucket,'files':len(records),'bytes':sum(r['bytes'] for r in records),'upload':args.upload}),flush=True)
    if not args.upload:return
    import google.auth
    from google.auth.transport.requests import AuthorizedSession,Request
    from aero_psi.copilot import load_local_env
    load_local_env()
    credentials,_=google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
    credentials.refresh(Request())
    session=AuthorizedSession(credentials)
    bucket='https://storage.googleapis.com/storage/v1/b/'+quote(args.bucket,safe='')
    response=session.get(bucket,timeout=60);response.raise_for_status();config=response.json()
    iam=config.get('iamConfiguration',{})
    if iam.get('publicAccessPrevention')!='enforced' or not iam.get('uniformBucketLevelAccess',{}).get('enabled'):
        raise RuntimeError('Bucket must enforce public access prevention and uniform access before upload')
    local=threading.local()
    def client():
        if not hasattr(local,'session'):local.session=AuthorizedSession(credentials)
        return local.session
    def inspect(record):
        r=client().get(bucket+'/o/'+quote(record['path'],safe=''),timeout=60)
        if r.status_code==404:return None
        r.raise_for_status();return r.json()
    def same(record,obj):return int(obj.get('size',-1))==record['bytes'] and obj.get('md5Hash')==record['md5_base64']
    def transfer(record):
        existing=inspect(record)
        if existing:
            if not same(record,existing):raise RuntimeError('Existing object differs; refusing overwrite: '+record['path'])
            return {'path':record['path'],'status':'already_verified','generation':existing['generation']}
        path=ROOT/record['path']
        if fingerprints(path)!=record:raise RuntimeError('Local file changed after manifest: '+record['path'])
        for attempt in range(3):
            r=client().post('https://storage.googleapis.com/upload/storage/v1/b/'+quote(args.bucket,safe='')+'/o',params={'uploadType':'resumable','ifGenerationMatch':'0'},json={'name':record['path'],'md5Hash':record['md5_base64'],'metadata':{'sha256':record['sha256']}},headers={'X-Upload-Content-Type':'application/octet-stream','X-Upload-Content-Length':str(record['bytes'])},timeout=60)
            if r.status_code==412:
                obj=inspect(record)
                if obj and same(record,obj):return {'path':record['path'],'status':'already_verified','generation':obj['generation']}
            r.raise_for_status()
            try:
                with path.open('rb') as stream:
                    result=client().put(r.headers['Location'],data=stream,headers={'Content-Type':'application/octet-stream','Content-Length':str(record['bytes'])},timeout=300)
                result.raise_for_status()
                obj=inspect(record)
                if not obj or not same(record,obj):raise RuntimeError('Remote checksum mismatch: '+record['path'])
                return {'path':record['path'],'status':'uploaded_verified','generation':obj['generation']}
            except Exception:
                obj=inspect(record)
                if obj and same(record,obj):return {'path':record['path'],'status':'uploaded_verified','generation':obj['generation']}
                if attempt==2:raise
                time.sleep(2**attempt)
    results=[];failures=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures={pool.submit(transfer,r):r for r in records}
        for future in as_completed(futures):
            record=futures[future]
            try:results.append(future.result())
            except Exception as exc:failures.append({'path':record['path'],'error_type':type(exc).__name__});print('Failed: '+record['path'],flush=True)
            if (len(results)+len(failures))%25==0:print(f'{len(results)} verified; {len(failures)} failed; {len(records)} total',flush=True)
    report={'bucket':args.bucket,'verified':len(results),'total':len(records),'failures':failures,'objects':results,'verification':'Server object MD5 and size matched local file; local SHA-256 retained in manifest and object metadata.','local_files_deleted':False}
    (output/'upload-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='objects'}),flush=True)
    if failures:raise SystemExit(1)

if __name__=='__main__':main()
