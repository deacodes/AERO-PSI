"""Bounded structured Vertex requests shared by research and contextual tools."""
import json
import os
import re


class AIResponseError(ValueError):
    pass


def parse_response(response):
    candidates=getattr(response,'candidates',None) or []
    reason=str(getattr(candidates[0],'finish_reason','')) if candidates else ''
    if 'MAX_TOKENS' in reason:
        raise AIResponseError('The AI response reached its length limit before completing. Request a narrower investigation or revise one part at a time.')
    if any(r in reason for r in ('SAFETY','BLOCKLIST','PROHIBITED_CONTENT')):
        raise AIResponseError('The AI service declined this response. Reframe the request around literature review, simulation or measurement planning.')
    raw=(getattr(response,'text',None) or '').strip()
    if raw.startswith('```'): raw=re.sub(r'^```(?:json)?\s*|\s*```$', '',raw,flags=re.I).strip()
    try:
        value=json.loads(raw)
    except (ValueError,TypeError) as exc:
        raise AIResponseError('The AI returned an incomplete or malformed response. Your saved work is unchanged. Retry the request; no default answer was substituted.') from exc
    if not isinstance(value,dict): raise AIResponseError('The AI returned the wrong response format. Retry the request.')
    return value


def generate_json(prompt, schema, *, max_tokens=8000):
    from google import genai
    from google.genai import types
    from aero_psi_copilot import load_local_env
    load_local_env()
    model=os.environ.get('AERO_PSI_VERTEX_MODEL','gemini-3.5-flash')
    config={'response_mime_type':'application/json','response_json_schema':schema,'max_output_tokens':max_tokens}
    if model.startswith('gemini-3'):config['thinking_config']=types.ThinkingConfig(thinking_level='LOW',include_thoughts=False)
    client=genai.Client(vertexai=True,project=os.environ.get('GOOGLE_CLOUD_PROJECT'),location=os.environ.get('GOOGLE_CLOUD_LOCATION','global'),
        http_options=types.HttpOptions(api_version='v1',timeout=120000,retry_options=types.HttpRetryOptions(attempts=1)))
    try:
        response=client.models.generate_content(model=model,contents=prompt,config=types.GenerateContentConfig(**config))
        return parse_response(response)
    finally:
        client.close()


def object_schema(properties):
    return {'type':'object','properties':properties,'required':list(properties),'additionalProperties':False}


def string_schema():return {'type':'string'}


def studio_schema(tools,source_ids):
    string=string_schema();strings={'type':'array','items':string}
    step=object_schema({k:string for k in ['title','method','rationale','inputs','expected_output','interpretation']}|{
        'tool':{'type':['string','null'],'enum':[None,*tools]},'source_ids':{'type':'array','items':({'type':'string','enum':source_ids} if source_ids else string),'maxItems':len(source_ids)}})
    variable=object_schema({'name':string,'unit':string,'minimum':{'type':'number'},'maximum':{'type':'number'},'levels':{'type':'integer','minimum':2,'maximum':9},'basis':string})
    design=object_schema({k:string for k in ['hypothesis','outcome','controls','measurement_method','analysis']}|{'variables':{'type':'array','items':variable,'maxItems':4},'replicates':{'type':'integer','minimum':1,'maximum':20}})
    chart=object_schema({'type':{'type':'string','enum':['line','scatter','bar','histogram','heatmap']},**{k:string for k in ['title','purpose','required_data']}})
    return object_schema({'title':string,'summary':string,'safety':string,'limitations':strings,'design':design,'suggested_charts':{'type':'array','items':chart,'maxItems':4},'steps':{'type':'array','items':step,'minItems':3,'maxItems':8}})
