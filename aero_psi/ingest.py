#!/usr/bin/env python3
"""Read-only PSI-101/PSI-102 workbook importer for AERO-PSI.

Writes derived, gzip-compressed JSONL plus reports outside DATA/. It never
modifies source workbooks. Legacy XLS files are converted into derived cache
files with LibreOffice before being parsed.
"""
from __future__ import annotations

import argparse, gzip, hashlib, json, re, shutil, subprocess, tempfile, zipfile
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from statistics import median
from typing import Any
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "DATA"
DERIVED = ROOT / "derived"
NS = {
    'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
    'rel': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'pkg': 'http://schemas.openxmlformats.org/package/2006/relationships'
}
CORE = {
    'obscuration_voltage': 'ISSDetectorObscurationMeasurement(Volts)',
    'scatter_voltage': 'ISSDetectorScatterMeasurement(Volts)',
    'sts_voltage': 'STSDetectorMeasurement(Volts)',
    'ion_a_voltage': 'IonDetectorAMeasurement(Volts)',
    'ion_b_voltage': 'IonDetectorBMeasurement(Volts)',
    'ptrak_particles_per_cc': 'PTrakMeasurement(PtPerCC)',
    'dusttrak_a_mg_m3': 'DustTrakAMeasurement(MgPerM3)',
    'dusttrak_b_mg_m3': 'DustTrakBMeasurement(MgPerM3)',
    'plume_temperature_c': 'GasPlumeTemperature(DegC)',
    'lfe_flow_sccm': 'LFEFlowRate[AT08](SCCM)',
    'mfc_flow_lpm': 'MFCMassFlowRate(LPM)'
}

def now() -> str: return datetime.now(UTC).replace(microsecond=0).isoformat()
def digest(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
    return h.hexdigest()
def col_number(ref: str) -> int:
    letters=re.match(r"[A-Z]+",ref).group(0); value=0
    for char in letters: value=value*26+ord(char)-64
    return value-1
def numeric(value: Any) -> float | None:
    try: return float(value)
    except (ValueError,TypeError): return None
def canonical_utc(value: Any) -> str | None:
    """Convert only clearly Unix-second source times; retain all source values unchanged."""
    number=numeric(value)
    if number is None or not 946684800 <= number <= 4102444800: return None
    return datetime.fromtimestamp(number,UTC).replace(microsecond=0).isoformat()

def office_binary() -> str:
    candidates=[shutil.which("soffice"), "/Users/deabhargava/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/soffice"]
    found=next((item for item in candidates if item and Path(item).exists()),None)
    if not found: raise RuntimeError("LibreOffice/soffice is required to import .xls files.")
    return found
def converted_xlsx(source: Path, checksum: str) -> Path:
    target=DERIVED/"converted"/f"{checksum}.xlsx"
    if target.exists(): return target
    target.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="aero-psi-office-") as profile, tempfile.TemporaryDirectory(prefix="aero-psi-xls-") as output:
        command=[office_binary(),f"-env:UserInstallation=file://{profile}","--headless","--convert-to","xlsx","--outdir",output,str(source)]
        result=subprocess.run(command,capture_output=True,text=True,timeout=90)
        candidates=list(Path(output).glob("*.xlsx"))
        if result.returncode != 0 or not candidates: raise RuntimeError(f"Conversion failed: {source.name}: {result.stderr[-300:]}")
        shutil.move(str(candidates[0]),target)
    return target

def xlsx_sheet_index(path: Path) -> list[tuple[str,str]]:
    with zipfile.ZipFile(path) as archive:
        workbook=ET.fromstring(archive.read("xl/workbook.xml")); rels=ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    targets={item.attrib["Id"]: item.attrib["Target"] for item in rels}
    result=[]
    for sheet in workbook.findall("main:sheets/main:sheet",NS):
        target=targets[sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]]
        result.append((sheet.attrib["name"], "xl/"+target.lstrip("/")))
    return result
def shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist(): return []
    root=ET.fromstring(archive.read("xl/sharedStrings.xml")); return ["".join(item.itertext()) for item in root.findall("main:si",NS)]
def cell_value(cell: ET.Element, shared: list[str]) -> str:
    kind=cell.attrib.get("t"); value=cell.find("main:v",NS)
    if kind=="inlineStr": return "".join(cell.find("main:is",NS).itertext()) if cell.find("main:is",NS) is not None else ""
    if value is None: return ""
    text=value.text or ""
    return shared[int(text)] if kind=="s" and text.isdigit() and int(text)<len(shared) else text
def sheet_rows(path: Path, internal_path: str) -> tuple[list[str], list[dict[str,str]]]:
    with zipfile.ZipFile(path) as archive:
        shared=shared_strings(archive); root=ET.fromstring(archive.read(internal_path))
    rows=[]
    for xml_row in root.findall("main:sheetData/main:row",NS):
        cells={col_number(cell.attrib["r"]):cell_value(cell,shared) for cell in xml_row.findall("main:c",NS)}
        width=max(cells.keys(),default=-1)+1; rows.append([cells.get(i,"") for i in range(width)])
    if not rows: return [],[]
    headers=rows[0]
    return headers,[{headers[i] if i<len(headers) and headers[i] else f"unnamed_{i+1}":row[i] if i<len(row) else "" for i in range(max(len(headers),len(row)))} for row in rows[1:]]
def select_raw_sheet(path: Path) -> tuple[str,list[str],list[dict[str,str]]] | None:
    candidates=[]
    for name,internal in xlsx_sheet_index(path):
        try: headers,_=sheet_rows(path,internal)
        except Exception: continue
        if "Time" in headers and "TimeString" in headers: candidates.append((len(headers),name,internal))
    if not candidates: return None
    _,name,internal=max(candidates,key=lambda item:item[0]); headers,rows=sheet_rows(path,internal); return name,headers,rows

def state_active(value: str) -> bool:
    number=numeric(value); return number is not None and number>0
def run_metadata(rows: list[dict[str,str]], headers: list[str]) -> dict[str,Any]:
    result={}
    for field in ("TestNumber","SampleNumber","CarouselNumber","RunMode","ElapsedTestTime(Secs)"):
        if field not in headers: result[field]={"state":"absent","values":[]}; continue
        values=[]
        for row in rows:
            value=row.get(field,"").strip()
            if value and value not in values: values.append(value)
            if len(values)>=20: break
        result[field]={"state":"observed" if values else "missing","values":values}
    return result
def signal_metrics(rows: list[dict[str,str]], header: str, start: int, end: int, baseline_start: int, warnings: list[str]) -> dict[str,Any]:
    values=[numeric(row.get(header,"")) for row in rows]; baseline=[v for v in values[baseline_start:start] if v is not None and v!=-10]
    window=[v for v in values[start:end+1] if v is not None and v!=-10]
    if not baseline or not window: return {"status":"unavailable","missing_fraction":1-len(window)/max(1,end-start+1)}
    base=median(baseline); peak=max(window); low=min(window); deviations=[v-base for v in window]; extreme=max(deviations,key=abs); peak_index=next(i for i,v in enumerate(values[start:end+1]) if v is not None and v!=-10 and v-base==extreme)+start
    times=[numeric(row.get("Time","")) for row in rows]; auc=0.0; valid_pairs=0
    for i in range(start+1,end+1):
        if values[i-1] is None or values[i] is None or values[i-1]==-10 or values[i]==-10 or times[i-1] is None or times[i] is None or times[i]<=times[i-1]: continue
        auc+=((values[i-1]-base)+(values[i]-base))*(times[i]-times[i-1])/2; valid_pairs+=1
    if not valid_pairs: warnings.append(f"{header}: AUC unavailable because usable increasing timestamps were absent.")
    threshold=abs(extreme)*0.10; count=sum(1 for v in deviations if abs(v)>=threshold); duration=0.0
    for i in range(start+1,end+1):
        if values[i-1] is None or values[i] is None or times[i-1] is None or times[i] is None or times[i] <= times[i-1]: continue
        if abs(values[i-1]-base) >= threshold and abs(values[i]-base) >= threshold: duration += times[i]-times[i-1]
    return {"status":"available","unit_from_header":header,"baseline_median":base,"raw_peak":peak,"raw_minimum":low,"peak_deviation_from_baseline":extreme,"peak_row":peak_index+2,"peak_time_source":times[peak_index],"event_start_time_source":times[start],"time_to_peak_source_time_units":times[peak_index]-times[start] if times[peak_index] is not None and times[start] is not None else None,"auc_baseline_corrected":auc if valid_pairs else None,"auc_unit":"source signal × source Time","relative_threshold":"10% of absolute peak deviation; display heuristic, not a physical alarm threshold","samples_at_or_above_relative_threshold":count,"duration_above_relative_threshold_source_time_units":duration,"missing_fraction":1-len(window)/max(1,end-start+1)}
def analyze(rows: list[dict[str,str]], headers: list[str]) -> tuple[dict[str,Any],list[str]]:
    warnings=[]; times=[numeric(row.get("Time","")) for row in rows]; valid=[v for v in times if v is not None]
    if len(valid)<2: warnings.append("No usable numeric Time series.")
    duplicates=len(valid)-len(set(valid)); nonmonotonic=sum(1 for a,b in zip(valid,valid[1:]) if b<a)
    if duplicates: warnings.append(f"{duplicates} duplicate numeric timestamps retained.")
    if nonmonotonic: warnings.append(f"{nonmonotonic} non-monotonic timestamp transitions retained.")
    missing_time=len(rows)-len(valid)
    if missing_time: warnings.append(f"{missing_time} rows have missing/non-numeric Time values.")
    active=[index for index,row in enumerate(rows) if state_active(row.get("TestRunning",""))]
    if active: start,end=active[0],active[-1]; method="TestRunning > 0"; baseline_start=max(0,start-min(60,start))
    else: start=end=baseline_start=0; method="unavailable"; warnings.append("No TestRunning > 0 event window; metrics are unavailable until a user confirms a window.")
    available={alias:header for alias,header in CORE.items() if header in headers}; absent=[alias for alias in CORE if alias not in available]; sentinels={alias:sum(1 for row in rows if numeric(row.get(header,""))==-10) for alias,header in available.items()}
    fully_zero={alias:all(value == 0 for value in (numeric(row.get(header,"")) for row in rows) if value is not None and value != -10) for alias,header in available.items()}
    if any(sentinels.values()): warnings.append("Sentinel value -10 retained and excluded from derived metrics.")
    if absent: warnings.append(f"Absent core signals: {', '.join(absent)}.")
    zeroed=[alias for alias,value in fully_zero.items() if value]
    if zeroed: warnings.append(f"Fully-zero core signals retained: {', '.join(zeroed)}.")
    metrics={alias:signal_metrics(rows,header,start,end,baseline_start,warnings) for alias,header in available.items()} if active else {}
    quality="usable_for_within_run" if active and len(available)>=2 and len(valid)>=2 else "needs_review"
    return {"row_count":len(rows),"time_start":valid[0] if valid else None,"time_end":valid[-1] if valid else None,"time_start_utc":canonical_utc(valid[0]) if valid else None,"time_end_utc":canonical_utc(valid[-1]) if valid else None,"time_parse_rule":"Unix seconds converted to UTC only when within 2000-2100; original Time and TimeString are always preserved.","missing_time_rows":missing_time,"duplicate_timestamps":duplicates,"non_monotonic_transitions":nonmonotonic,"selected_event_window":{"method":method,"baseline_source_rows":[baseline_start+2,start+1] if active else None,"test_source_rows":[start+2,end+2] if active else None},"available_signals":available,"absent_core_signals":absent,"fully_zero_core_signals":zeroed,"sentinel_minus_10_counts":sentinels,"quality_state":quality,"metrics":metrics},warnings

def mappings() -> dict[str,str]:
    path=ROOT/"mappings"/"verified_run_links.csv"
    if not path.exists(): return {}
    lines=path.read_text(encoding="utf-8").splitlines()[1:]; return {line.split(",")[0]:line.split(",")[1] for line in lines if "," in line}
def import_one(source: Path, group: str, verified: dict[str,str]) -> dict[str,Any]:
    rel=source.relative_to(DATA).as_posix(); checksum=digest(source); warning=[]
    try: workbook=converted_xlsx(source,checksum) if source.suffix.lower()==".xls" else source; selected=select_raw_sheet(workbook)
    except Exception as exc: return {"source_path":rel,"source_sha256":checksum,"group":group,"status":"failed","warnings":[str(exc)]}
    if not selected: return {"source_path":rel,"source_sha256":checksum,"group":group,"status":"not_time_series","warnings":[
        'No worksheet contained both Time and TimeString headers.'
    ]}
    sheet,headers,rows=selected; analysis,warnings=analyze(rows,headers); output=DERIVED/"timeseries"/f"{checksum}.jsonl.gz"; output.parent.mkdir(parents=True,exist_ok=True)
    with gzip.open(output,"wt",encoding="utf-8") as handle:
        for row_number,row in enumerate(rows,start=2): handle.write(json.dumps({"source_path":rel,"source_sha256":checksum,"worksheet":sheet,"source_row":row_number,"timestamp_utc":canonical_utc(row.get("Time")),"values":row},ensure_ascii=False)+"\n")
    status="verified" if rel in verified else "unmatched"
    material=next((item for item in [
        'Kapton',
        'Pyrell',
        'Silicone',
        'Teflon',
        'Lampwick',
        'Dibutyl Phthalate'
    ] if item.lower() in rel.lower()),None)
    return {"source_path":rel,"source_sha256":checksum,"group":group,"status":"imported","derived_path":output.relative_to(ROOT).as_posix(),"worksheet":sheet,"header_count":len(headers),"material_candidate":material,"run_metadata":run_metadata(rows,headers),"join_status":status,"verified_experiment_key":verified.get(rel),"parser_version":"1.1","imported_at":now(),"warnings":warnings,"analysis":analysis}
def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("--groups",nargs="+",default=[
        'PSI101',
        'PSI102'
    ]); args=parser.parse_args(); DERIVED.joinpath("reports").mkdir(parents=True,exist_ok=True)
    verified=mappings(); manifest_path=DERIVED/"reports"/"ingestion_manifest.json"; retained=[]
    if manifest_path.exists():
        try: retained=[record for record in json.loads(manifest_path.read_text(encoding="utf-8")).get("records",[]) if record.get("group") not in args.groups]
        except (json.JSONDecodeError,OSError): retained=[]
    records=[]
    for group in args.groups:
        for source in sorted((DATA/group).rglob("*")):
            if source.is_file() and source.suffix.lower() in {
                '.xls',
                '.xlsx'
            }: records.append(import_one(source,group,verified))
    records=retained+records
    manifest={"generated_at":now(),"parser_version":"1.2","derived_storage_format":"gzip-compressed JSON Lines; selected for a portable MVP while preserving one source row per record","source_archive_read_only":True,"records":records,"summary":dict(Counter(f"{r['group']}:{r['status']}" for r in records))}
    manifest_path.write_text(json.dumps(manifest,indent=2)+"\n")
    candidates=sorted([r for r in records if r["status"]=="imported"],key=lambda r:(r["analysis"]["quality_state"]!="usable_for_within_run",len(r["warnings"]),-len(r["analysis"]["available_signals"])))
    (DERIVED/"reports"/"demo_candidates.json").write_text(json.dumps({"generated_at":now(),"selection_rule":"Prefer usable within-run time series, fewer warnings, then more available core signals. Selection is data quality only, not a scientific ranking.","candidates":candidates[:20]},indent=2)+"\n")
    print(json.dumps(manifest["summary"],indent=2))
if __name__=="__main__": main()
