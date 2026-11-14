"""Local checks of the document review; no model calls and no source mutations."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import math
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    from aero_psi_evidence import document_records
    from aero_psi_knowledge import review_records
    docs=document_records(); reviewed=review_records(docs)
    catalog=json.loads((ROOT/'aero_psi_catalog.json').read_text())
    changed=[]
    for entry in catalog['files']:
        path=ROOT/'DATA'/entry['source_path']
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=entry['source_sha256']:changed.append(entry['source_path'])
    assert not changed, changed
    source=ROOT/'DATA/FLEX/20CAL08.txt'; rows=[]
    for number,line in enumerate(source.read_text().splitlines(),1):
        if not re.match(r'^\d{4}-\d\d-\d\d ',line):continue
        cells=[x.strip() for x in line.split('\t') if x.strip()]
        assert len(cells)==9,(number,len(cells))
        times=[dt.datetime.fromisoformat(x) for x in cells[:2]]
        values=[float(x) for x in cells[2:]]
        assert all(math.isfinite(x) for x in values)
        rows.append((number,times,values))
    offsets=[(r[1][0]-r[1][1]).total_seconds() for r in rows]
    intervals=[(b[1][0]-a[1][0]).total_seconds() for a,b in zip(rows,rows[1:])]
    repeated=[{'rows':[a[0],b[0]], 'same_radiometer_values':a[2][:4]==b[2][:4],
               'same_image_counters':a[2][4:]==b[2][4:]} for a,b in zip(rows,rows[1:]) if b[1][0]==a[1][0]]
    log={'source_path':'FLEX/20CAL08.txt','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'numeric_rows':len(rows),'first_row':rows[0][0],'last_row':rows[-1][0],
        'clock_offset_s_range':[min(offsets),max(offsets)],'mdca_interval_s_range':[min(intervals),max(intervals)],
        'repeated_timestamps':repeated,'negative_intervals':sum(t<0 for t in intervals),
        'wide_mean_negative_rows':sum(r[2][2]<0 for r in rows),
        'columns':['MDCA MP Time','Radiometer Time','Narrow Mean','Narrow StdDev','Wide Mean','Wide StdDev','IPSU1 Archived','IPSU2 Archived','IPSU4 Archived'],
        'physical_radiometer_units':None,'calibration_applied':False}
    # These are independent algebra/unit checks, not flight-data fitting.
    total=1e12; diameter=100e-9; sigma=1.6; s=math.log(sigma)
    moments={j:total*diameter**j*math.exp(j*j*s*s/2) for j in [0,1,3]}
    recovered_d=moments[0]**(-4/3)*moments[1]**1.5*moments[3]**(-1/6)
    recovered_sigma=math.exp(math.sqrt(math.log(moments[0]**(2/3)*moments[3]**(1/3)/moments[1])))
    assert math.isclose(recovered_d,diameter,rel_tol=1e-12)
    assert math.isclose(recovered_sigma,sigma,rel_tol=1e-12)
    illustrative_count_cm3=2e-6/(1000*math.pi/6*(500e-9)**3*math.exp(4.5*math.log(1.3)**2))/1e6
    checks={'moment_inversion_roundtrip':True,'assumed_distribution':{'N_m3':total,'Dg_m':diameter,'sigma_g':sigma},
        'detector_slide_consistency':{'assumed_density_kg_m3':1000,'mass_kg_m3':2e-6,'Dg_m':500e-9,'sigma_g':1.3,
            'derived_number_cm3':illustrative_count_cm3,'printed_number_cm3':22e6,'status':'inconsistent under explicitly assumed density; not a corrected observation'},
        'eird_table_row4':{'printed_coagulation_fraction':0.981,'printed_wall_fraction':0.999,'product':0.981*0.999,'printed_combined_fraction':0.937,'status':'printed combined column inconsistent with the product'}}
    result={'original_files_checked':len(catalog['files']),'changed_originals':changed,'active_document_excerpts':len(docs),
        'active_source_notes_and_web_references':len(reviewed),'flex_log_audit':log,'mathematical_checks':checks,
        'limits':'No blanket verification of all figures/equations or validation of a NASA-calibrated platform model.'}
    output=ROOT/'derived/reports/document_review_verification.json';output.write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
