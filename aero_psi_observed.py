"""Explicit source-row windows and reproducible observed-signal metrics."""
import csv
import hashlib
import io
import math
from pathlib import Path
from statistics import mean, median
from aero_psi_optical import _record, _rows, _number

ROOT=Path(__file__).resolve().parent
MANIFEST=ROOT/'derived/reports/ingestion_manifest.json'
UNITS={'obscuration_voltage':'V','scatter_voltage':'V','sts_voltage':'V','ion_a_voltage':'V','ion_b_voltage':'V','ptrak_particles_per_cc':'particles/cm^3','dusttrak_a_mg_m3':'mg/m^3','dusttrak_b_mg_m3':'mg/m^3','plume_temperature_c':'degC','lfe_flow_sccm':'sccm','mfc_flow_lpm':'L/min'}


def _window(value,name):
    if not isinstance(value,list) or len(value)!=2 or any(type(x) is not int for x in value) or not 2<=value[0]<=value[1]:
        raise ValueError(name+' must be two ordered integer source-row numbers >= 2')
    return value


def analyze(payload,manifest=MANIFEST,root=ROOT):
    if payload.get('confirmed') is not True: raise ValueError('Window boundaries require explicit user confirmation')
    path=payload.get('source_path'); signal=payload.get('signal')
    record=_record(manifest,path); header=record.get('analysis',{}).get('available_signals',{}).get(signal)
    if not header or signal not in UNITS: raise ValueError('Select an available signal with a documented unit')
    source=(Path(root)/'DATA'/record['source_path']).resolve()
    if (Path(root)/'DATA').resolve() not in source.parents: raise ValueError('Invalid archive path')
    if hashlib.sha256(source.read_bytes()).hexdigest()!=record['source_sha256']: raise ValueError('Original source changed; re-import before analysis')
    baseline=_window(payload.get('baseline_rows'),'baseline_rows'); event=_window(payload.get('event_rows'),'event_rows')
    if baseline[1]>=event[0]: raise ValueError('Baseline must end before the event begins')
    recovery=payload.get('recovery_rows')
    if recovery is not None:
        recovery=_window(recovery,'recovery_rows')
        if recovery[0]<=event[1]: raise ValueError('Recovery must follow the event')
    method=payload.get('baseline_method','median')
    if method not in ('median','mean'): raise ValueError('baseline_method must be median or mean')
    if payload.get('time_unit')!='s': raise ValueError('Confirm source Time is in seconds using time_unit="s"')
    rows=_rows(record,Path(root)); indexed={r['source_row']:r for r in rows}
    for limits in (baseline,event,recovery):
        if limits and any(i not in indexed for i in range(limits[0],limits[1]+1)): raise ValueError('Window contains absent source rows')
    base_values=[_number(indexed[i]['values'].get(header)) for i in range(baseline[0],baseline[1]+1)]
    base_values=[x for x in base_values if x is not None]
    if len(base_values)<2: raise ValueError('Baseline needs at least two valid measurements')
    base=(median if method=='median' else mean)(base_values)
    selected=[indexed[i] for i in range(event[0],event[1]+1)]
    points=[{'source_row':r['source_row'],'time_s':_number(r['values'].get('Time')),'raw':_number(r['values'].get(header))} for r in selected]
    for point in points: point['corrected']=None if point['raw'] is None else point['raw']-base
    valid=[p for p in points if p['raw'] is not None]
    if not valid: raise ValueError('Event contains no valid measurements')
    peak=max(valid,key=lambda p:abs(p['corrected']))
    threshold=payload.get('threshold'); threshold_value=None
    if threshold is not None:
        if not isinstance(threshold,dict) or not isinstance(threshold.get('reference'),str) or not threshold['reference'].strip(): raise ValueError('Threshold needs an explicit source or user-assumption reference')
        value=threshold.get('value')
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<=0: raise ValueError('Threshold value must be finite and positive')
        if threshold.get('kind')=='absolute': threshold_value=value
        elif threshold.get('kind')=='relative_peak' and value<=1: threshold_value=value*abs(peak['corrected'])
        else: raise ValueError('Use absolute or relative_peak threshold (0 < fraction <= 1)')
    max_interval=payload.get('max_interval_s')
    if max_interval is not None and (isinstance(max_interval,bool) or not isinstance(max_interval,(int,float)) or not math.isfinite(max_interval) or max_interval<=0): raise ValueError('max_interval_s must be finite and positive')
    state_values=[_number(r['values'].get('TestRunning')) for r in selected]
    active=[v is not None and v>0 for v in state_values]
    episodes=sum(value and (i==0 or not active[i-1]) for i,value in enumerate(active))
    pairs=[]; excluded=0
    for a,b in zip(points,points[1:]):
        if any(p['time_s'] is None or p['corrected'] is None for p in (a,b)) or b['time_s']<=a['time_s'] or (max_interval is not None and b['time_s']-a['time_s']>max_interval):
            excluded+=1; continue
        pairs.append((a,b))
    valid_times=[p['time_s'] for p in points if p['time_s'] is not None]
    backwards=any(b<a for a,b in zip(valid_times,valid_times[1:]))
    # Do not bridge missing samples; threshold duration uses linear interpolation on each valid adjacent interval.
    duration=0.0
    if threshold_value is not None:
        for a,b in pairs:
            x,y=a['corrected'],b['corrected']; cuts=[0.0,1.0]
            if x!=y:
                cuts.extend(t for edge in (-threshold_value,threshold_value) if 0<(t:=(edge-x)/(y-x))<1)
            cuts.sort()
            duration+=(b['time_s']-a['time_s'])*sum(hi-lo for lo,hi in zip(cuts,cuts[1:]) if abs(x+(y-x)*(lo+hi)/2)>threshold_value)
    metrics={'baseline':base,'raw_peak':max(p['raw'] for p in valid),'raw_minimum':min(p['raw'] for p in valid),'signed_extreme_deviation':peak['corrected'],'extreme_source_row':peak['source_row'],
             'time_to_extreme_s':peak['time_s']-points[0]['time_s'] if not backwards and peak['time_s'] is not None and points[0]['time_s'] is not None else None,
             'signed_auc':sum((a['corrected']+b['corrected'])*(b['time_s']-a['time_s'])/2 for a,b in pairs) if pairs and not backwards else None,
             'duration_above_absolute_deviation_threshold_s':duration if threshold_value is not None and pairs and not backwards else None,'missing_fraction':1-len(valid)/len(points),
             'integrated_time_s':sum(b['time_s']-a['time_s'] for a,b in pairs) if not backwards else None,'excluded_adjacent_intervals':excluded}
    recovery_result=None
    if recovery:
        values=[_number(indexed[i]['values'].get(header)) for i in range(recovery[0],recovery[1]+1)]; usable=[v for v in values if v is not None]
        recovery_result={'median_deviation':median(usable)-base if usable else None,'missing_fraction':1-len(usable)/len(values)}
    return {'classification':'observed signal analysis; no detector calibration or causal inference','source_path':path,'source_sha256':record['source_sha256'],'worksheet':record.get('worksheet'),'group':record.get('group'),'signal':signal,'source_column':header,'units':{'signal':UNITS[signal],'auc':UNITS[signal]+' s','time':'s'},'window':{'confirmed':True,'baseline_rows':baseline,'event_rows':event,'recovery_rows':recovery,'baseline_method':method,'time_unit_origin':'user-confirmed source seconds','max_interval_s':max_interval,'test_running_episodes':episodes},'threshold':{'request':threshold,'absolute_deviation_value':threshold_value,'comparison':'abs(value-baseline) > threshold'},'metrics':metrics,'recovery':recovery_result,'points':points,'join_status':record.get('join_status'),'verified_experiment_key':record.get('verified_experiment_key'),'warnings':['Source polarity is preserved. Sentinel -10 and non-finite values are excluded.','AUC uses only valid adjacent intervals; missing intervals are not interpolated.','Recorded voltage is not an optical cross section or particle-size measurement.']+(['Time reversal detected: time-dependent metrics withheld.'] if backwards else [])+(['The window spans multiple TestRunning episodes; split it before treating it as a single test.'] if episodes>1 else [])+(['No maximum interval was supplied: inspect irregular sampling before interpreting integrated metrics.'] if max_interval is None else [])}


def export_analysis(result):
    stream=io.StringIO(); writer=csv.writer(stream)
    writer.writerow(['source_path','source_sha256','worksheet','source_row','time_s','signal','unit','raw','baseline','baseline_corrected'])
    for p in result['points']:
        writer.writerow([result['source_path'],result['source_sha256'],result['worksheet'],p['source_row'],p['time_s'],result['signal'],result['units']['signal'],p['raw'],result['metrics']['baseline'],p['corrected']])
    return {'csv':stream.getvalue(),'metadata':{k:v for k,v in result.items() if k!='points'},'resolution':'all selected event rows, no downsampling'}


def compare(payload,manifest=MANIFEST,root=ROOT):
    if not isinstance(payload.get('left'),dict) or not isinstance(payload.get('right'),dict): raise ValueError('Supply left and right confirmed analysis requests')
    left=analyze(payload['left'],manifest,root); right=analyze(payload['right'],manifest,root)
    reasons=[]
    if left['signal']!=right['signal']: reasons.append('Different signals')
    if left['source_path']!=right['source_path']:
        reasons.append('Cross-run condition and calibration equivalence has not been established by a reviewed comparison record')
        if left['group']!=right['group']: reasons.append('Different investigations cannot be pooled by default')
        if any(r['join_status']!='verified' for r in (left,right)): reasons.append('One or both run-condition joins are not verified')
    if left['window']['baseline_method']!=right['window']['baseline_method']: reasons.append('Different baseline methods')
    if reasons: return {'status':'blocked','reasons':reasons,'left':left,'right':right,'metric_differences':None}
    fields=('signed_extreme_deviation','raw_peak','raw_minimum')
    return {'status':'within_run_descriptive_comparison','left':left,'right':right,'metric_differences':{k:right['metrics'][k]-left['metrics'][k] for k in fields},'warnings':['Differences between selected windows are descriptive, not causal or independent replicates. AUC comparisons require matched time support and are not calculated here.']}
