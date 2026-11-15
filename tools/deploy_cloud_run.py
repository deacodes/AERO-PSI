#!/usr/bin/env python3
"""Build and deploy the allowlisted application using ADC (no local Docker required).

Provision a private build bucket, Artifact Registry repository, and dedicated
builder/runtime service accounts first. Defaults to a PRIVATE Cloud Run service.
Use --public explicitly to enable browser access without a Google login.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import tarfile
import time
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]


def source_files():
    files = [ROOT / n for n in ('Dockerfile', 'requirements.txt', 'requirements-deploy.txt', 'deploy/start.sh')]
    for folder in ('aero_psi', 'frontend', 'mappings'):
        files.extend(p for p in (ROOT / folder).rglob('*') if p.is_file()
                     and not p.is_symlink() and '__pycache__' not in p.parts
                     and p.suffix != '.pyc' and p.name != '.DS_Store')
    return sorted(files)


def package():
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode='w:gz') as archive:
        for path in source_files():
            if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
                raise ValueError('Refusing source symlink: ' + str(path))
            archive.add(path, arcname=path.relative_to(ROOT), recursive=False)
    return out.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True)
    parser.add_argument('--region', default='asia-south1')
    parser.add_argument('--model', required=True)
    parser.add_argument('--vertex-location', default='global')
    parser.add_argument('--bucket', default='aeropsi-data')
    parser.add_argument('--public', action='store_true')
    parser.add_argument('--apply', action='store_true', help='Actually upload, build and deploy; otherwise list the package only')
    args = parser.parse_args()
    bundle = package()
    print(json.dumps({'source_files':len(source_files()), 'archive_bytes':len(bundle), 'public':args.public}), flush=True)
    if not args.apply:
        for path in source_files(): print(path.relative_to(ROOT))
        return
    import google.auth
    from google.auth.transport.requests import AuthorizedSession
    session = AuthorizedSession(google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])[0])
    def request(method, url, **kwargs):
        response = session.request(method, url, timeout=90, **kwargs)
        if not response.ok:
            raise RuntimeError(f'{response.status_code}: {response.text[:2000]}')
        return response.json() if response.content else {}
    tag = hashlib.sha256(bundle).hexdigest()[:16]
    build_bucket = args.project + '-aeropsi-builds'
    object_name = 'source/' + tag + '.tar.gz'
    uploaded = request('POST', 'https://storage.googleapis.com/upload/storage/v1/b/' + build_bucket + '/o',
                       params={'uploadType':'media', 'name':object_name, 'ifGenerationMatch':'0'},
                       data=bundle, headers={'Content-Type':'application/gzip'})
    image = f'{args.region}-docker.pkg.dev/{args.project}/aeropsi/app:{tag}'
    build_base = f'https://cloudbuild.googleapis.com/v1/projects/{args.project}/locations/{args.region}/builds'
    build = request('POST', build_base, json={
        'source':{'storageSource':{'bucket':build_bucket,'object':object_name,'generation':uploaded['generation']}},
        'steps':[{'name':'gcr.io/cloud-builders/docker','args':['build','-t',image,'.']}],
        'images':[image], 'timeout':'1200s',
        'serviceAccount':f'projects/{args.project}/serviceAccounts/aeropsi-builder@{args.project}.iam.gserviceaccount.com',
        'options':{'logging':'CLOUD_LOGGING_ONLY'}})
    build_id = build['metadata']['build']['id']
    report = ROOT / 'output/deployment'; report.mkdir(parents=True, exist_ok=True)
    state = {'project':args.project,'region':args.region,'build_id':build_id,'image':image}
    (report/'latest.json').write_text(json.dumps(state,indent=2))
    previous = None
    while True:
        status = request('GET',build_base+'/'+build_id)
        if status['status'] != previous:
            print('Build: '+status['status'], flush=True); previous = status['status']
        if status['status'] == 'SUCCESS': break
        if status['status'] not in ('QUEUED','WORKING','STATUS_UNKNOWN','PENDING'):
            raise RuntimeError('Build failed: '+json.dumps(status.get('failureInfo',{}))+' '+status.get('logUrl',''))
        time.sleep(10)
    service_base = f'https://run.googleapis.com/v2/projects/{args.project}/locations/{args.region}/services'
    service_url = service_base+'/aeropsi'
    env = {'GOOGLE_CLOUD_PROJECT':args.project,'GOOGLE_CLOUD_LOCATION':args.vertex_location,
           'AERO_PSI_VERTEX_MODEL':args.model,'AERO_PSI_COPILOT_ENABLED':'true',
           'AERO_PSI_STORAGE_BUCKET':args.bucket,'AERO_PSI_CLOUD_CACHE':'/tmp/aeropsi-runtime'}
    config = {'ingress':'INGRESS_TRAFFIC_ALL', 'template':{
        'serviceAccount':f'aeropsi-runtime@{args.project}.iam.gserviceaccount.com',
        'scaling':{'minInstanceCount':0,'maxInstanceCount':1},
        'maxInstanceRequestConcurrency':2,'timeout':'300s',
        'containers':[{'image':image,'ports':[{'containerPort':8080}],
            'env':[{'name':k,'value':v} for k,v in env.items()],
            'resources':{'limits':{'cpu':'1','memory':'2Gi'},'cpuIdle':True,'startupCpuBoost':True},
            'startupProbe':{'tcpSocket':{'port':8080},'periodSeconds':10,'timeoutSeconds':1,'failureThreshold':24}}]}}
    existing = session.get(service_url,timeout=60)
    if existing.status_code == 404:
        operation = request('POST',service_base,params={'serviceId':'aeropsi'},json=config)
    elif existing.ok:
        config['name']=existing.json()['name']
        operation=request('PATCH',service_url,params={'updateMask':'template,ingress'},json=config)
    else: raise RuntimeError(existing.text[:1000])
    print('Deploying Cloud Run service…',flush=True)
    for _ in range(120):
        result=request('GET','https://run.googleapis.com/v2/'+operation['name'])
        if result.get('done'):
            if result.get('error'): raise RuntimeError(json.dumps(result['error']))
            break
        time.sleep(5)
    else: raise TimeoutError('Deployment still running; inspect Cloud Run console.')
    if args.public:
        policy=request('GET',service_url+':getIamPolicy')
        bindings=policy.setdefault('bindings',[])
        binding=next((b for b in bindings if b['role']=='roles/run.invoker' and 'condition' not in b),None)
        if binding is None: binding={'role':'roles/run.invoker','members':[]};bindings.append(binding)
        if 'allUsers' not in binding['members']:binding['members'].append('allUsers')
        request('POST',service_url+':setIamPolicy',json={'policy':policy})
    service=request('GET',service_url)
    state.update(url=service['uri'],public=args.public)
    (report/'latest.json').write_text(json.dumps(state,indent=2))
    print(json.dumps(state,indent=2),flush=True)

if __name__=='__main__':main()
