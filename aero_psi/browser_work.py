"""Request-scoped Studio computation. No visitor records are written to disk."""
from contextvars import ContextVar
import copy
from . import studio

CURRENT=ContextVar('browser_studio_record',default=None)


def execute(action,payload,catalog):
    record=payload.pop('browser_record',None)
    if payload.get('id'):
        if not isinstance(record,dict) or record.get('id')!=payload['id']:
            raise ValueError('Supply the investigation saved in this browser')
        studio.identifier(record['id'])
        if type(record.get('revision')) is not int or record['revision']<1:raise ValueError('Invalid revision')
        record=copy.deepcopy(record)
        record['content']=studio.validate_content(record.get('content'))
        for key in ('datasets','runs','sources','ai_reviews','model_links'):
            if not isinstance(record.get(key,[]),list):raise ValueError('Invalid '+key)
        for ds in record.get('datasets',[]):
            studio.identifier(ds.get('id'));studio.validate_dataset(ds)
            ds['classification']='browser_supplied_unverified'
        # Historical sources/results are user-supplied context, not new verified executions.
        for source in record.get('sources',[]):
            if not isinstance(source,dict) or not isinstance(source.get('id'),str):raise ValueError('Invalid source')
        for step in record['content']['steps']:
            for link in step['data_links']:
                ds=next((d for d in record.get('datasets',[]) if d['id']==link['dataset_id']),None)
                if not ds or any(i>=len(ds['rows']) for i in link['row_indices']):raise ValueError('Invalid dataset selection')
    token=CURRENT.set({'record':record})
    try:
        actions={'create':studio.create,'save':studio.save,'dataset':studio.add_dataset,'attach-model':studio.attach_model,
                 'generate':lambda p:studio.generate(p,catalog),'execute':lambda p:studio.execute(p,catalog),
                 'interpret':lambda p:studio.interpret(p,catalog),'from-research':lambda p:studio.from_research(p,catalog)}
        return actions[action](payload)
    finally:CURRENT.reset(token)
