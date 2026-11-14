#!/usr/bin/env python3
"""Read-only catalog API and local web shell for AERO-PSI."""
from __future__ import annotations

# Resolve the project interpreter before importing optional scientific dependencies.
if __name__ == "__main__":
    from aero_psi_runtime import use_project_environment
    use_project_environment()

import argparse, csv, hashlib, json, mimetypes, os, re
from collections import Counter, defaultdict
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse
from aero_psi_coagulation import ScenarioInputError, simulate as simulate_coagulation
from aero_psi_sectional import simulate_sectional, sensitivity as coagulation_sensitivity
from aero_psi_model_studies import sweep as coagulation_sweep, compare_observations
from aero_psi_model_studies import uncertainty, calibrate, convergence, domain_study
from aero_psi_scattering import simulate_scattering, coupled_scattering
from aero_psi_runtime import RuntimeDependencyError, capabilities
import aero_psi_archive as archive
from aero_psi_observed import analyze as analyze_observed, export_analysis, compare as compare_observed
from aero_psi_optical import runs as optical_runs, summary as optical_summary, time_series as optical_time_series, lag_analysis as optical_lag_analysis, coagulation_input_candidates
from aero_psi_atlas import coverage as atlas_coverage, gaps as atlas_gaps, conditions as atlas_conditions, condition_gaps as atlas_condition_gaps, suggested_measurement
from aero_psi_ranking import investigation_rankings
from aero_psi_discovery import rank_for_question, gap_plan
from aero_psi_copilot import ask as copilot_ask, interpret_point as copilot_interpret_point

from aero_psi_education import answer_question
from aero_psi_investigation import investigate, INVESTIGATION_STORAGE
import aero_psi_studio as studio
import aero_psi_research as research
from aero_psi_evidence import document_records

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_DATA_ROOT = Path(os.environ.get("AERO_PSI_DATA_ROOT", PROJECT_ROOT / "DATA"))
DEFAULT_CATALOG_PATH = PROJECT_ROOT / "aero_psi_catalog.json"
DEFAULT_FRONTEND_DIR = PROJECT_ROOT / "frontend"
DEFAULT_INGESTION_MANIFEST = PROJECT_ROOT / "derived" / "reports" / "ingestion_manifest.json"
SYSTEM_FILES = {
    '.DS_Store'
}; WORKBOOK_SUFFIXES = {
    '.xls',
    '.xlsx'
}; SCHEMA_VERSION = "1.1"; NORMALIZATION_VERSION = "1.0"
RELEVANCE = {
    'PSI101': (
        1,
        'Direct SAME-R smoke-aerosol and detector-response archive with experimental conditions and raw run workbooks.'
    ),
    'PSI102': (
        2,
        'Direct original SAME smoke-aerosol and detector-response archive; joins are less complete.'
    ),
    'SAFFIRE': (
        3,
        'Large-scale spacecraft-fire context with structured test conditions and image-transfer index.'
    ),
    'BASS-II': (
        4,
        'Structured microgravity solid-flammability conditions and material coverage, but no matched aerosol time series.'
    ),
    'BASS (ORIGINAL)': (
        5,
        'Earlier solid-flammability conditions and as-run matrices for historical context.'
    ),
    'FLEX': (
        6,
        'Structured microgravity droplet-extinction study, useful for combustion-condition coverage.'
    ),
    'ACME FLAME DESIGN': (
        7,
        'Structured gaseous diffusion-flame records, adjacent to rather than direct evidence for smoke aerosols.'
    ),
    'ACME II': (
        8,
        'Structured cool-flame gas records, adjacent combustion context rather than smoke measurements.'
    ),
    'SOFIE': (
        9,
        'Program and publication context only in the supplied archive.'
    )
}

def iso_now() -> str: return datetime.now(UTC).replace(microsecond=0).isoformat()
def relative_source_path(path: Path, root: Path) -> str: return path.relative_to(root).as_posix()
def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""): digest.update(block)
    return digest.hexdigest()

def material_from_path(path: str) -> str | None:
    choices = {
        'Dibutyl Phthalate': (
            'dibutyl phthalate',
            'dbp'
        ),
        'Kapton': ('kapton',),
        'Lampwick': ('lampwick',),
        'Pyrell': ('pyrell',),
        'Silicone': (
            'silicone',
            'silicon',
            'silcon'
        ),
        'Teflon': (
            'teflon',
            'tef'
        ),
        'SIBAL': ('sibal',),
        'PMMA': ('pmma',),
        'Nomex': ('nomex',)
    }
    lowered = path.lower()
    return next((name for name, terms in choices.items() if any(term in lowered for term in terms)), None)
def run_id_from_path(path: str) -> str | None:
    match = re.search(r"(?:run|test)[ _-]?(\d+[a-z]?)\b", path, re.I)
    return match.group(1) if match else None
def measurement_family(path: str) -> str:
    value = path.lower()
    if "psi101" in value or "psi102" in value: return "smoke aerosol and detector response"
    if "saffire" in value: return "large-scale spacecraft fire"
    if "bass" in value: return "solid-material flammability"
    if "flex" in value: return "droplet extinction"
    if "acme" in value: return "gaseous diffusion flames"
    return "program context"
def classify_file(path: str) -> str:
    name = Path(path).name.lower()
    if name == "i_investigation.txt": return "investigation metadata"
    if "experimental table" in name: return "experimental table"
    if name.endswith((".xls",".xlsx")) and any(v in name for v in ("run","gmt","hkp")): return "raw or derived run workbook"
    if name.endswith((".xls",".xlsx")): return "workbook"
    if name.endswith(".csv"): return "structured table"
    if name.endswith((".pdf",".doc",".docx",".pptx")): return "supporting document"
    return "other"
def data_level(role: str) -> str:
    if role == "raw or derived run workbook": return "direct raw or derived measurements"
    if role in {
        'experimental table',
        'structured table'
    }: return "structured conditions"
    if role == "supporting document": return "document context"
    return "metadata or other"

def read_investigation_metadata(path: Path) -> dict[str,str]:
    wanted = {
        'Study Identifier': 'investigation_id',
        'Study Title': 'title',
        'Comment[Investigation Acronym]': 'acronym',
        'Comment[Flight Platform]': 'platform',
        'Comment[Research Area]': 'research_area',
        'Comment[SubResearch Area]': 'subresearch_area',
        'Comment[DOI]': 'doi',
        'Comment[Objective]': 'objective',
        'Comment[Investigation Start Date]': 'start_date',
        'Comment[Investigation End Date]': 'end_date'
    }
    result = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        key, separator, value = line.partition("\t")
        if separator and key in wanted: result[wanted[key]] = value.strip().replace("\n"," ")
    return result
def material_column(headers: list[str]) -> str | None:
    return next((h for h in headers if "material" in h.lower() or "sample type" in h.lower() or h.lower().strip() == "fuel"), None)
def condition_key(header: str) -> str:
    value = header.lower().strip()
    if "material" in value or "sample type" in value or value == "fuel": return "material_or_fuel"
    if "air flow" in value or "inlet velocity" in value or "flow rate" in value: return "flow"
    if "oxygen" in value or "xo2" in value or value.startswith("o "): return "oxygen"
    if "pressure" in value or value.startswith(("pinit","pfinal","pmean")): return "pressure"
    if "duration" in value or "burn time" in value or "aging" in value: return "duration_or_aging"
    if "temperature" in value or "tad" in value: return "temperature"
    return re.sub(r"[^a-z0-9]+","_",value).strip("_")

def read_csv_table(path: Path, root: Path, checksum: str) -> tuple[dict[str,Any],dict[str,Any],list[dict[str,Any]]]:
    with path.open(encoding="utf-8-sig",errors="replace",newline="") as handle:
        reader = csv.DictReader(handle); rows = [dict(row) for row in reader]; headers = reader.fieldnames or []
    source_path = relative_source_path(path,root); column = material_column(headers)
    counts = Counter(row.get(column,"").strip() for row in rows if column and row.get(column,"").strip())
    table = {"source_path":source_path,"source_sha256":checksum,"row_count":len(rows),"columns":headers,"material_column":column,"material_counts":dict(sorted(counts.items())),"preview":rows[:3]}
    raw = {"namespace":"raw","source_path":source_path,"source_sha256":checksum,"columns":headers,"rows":rows}
    normalized=[]
    for row_number,row in enumerate(rows,start=2):
        fields={condition_key(header):{"value":row.get(header,""),"state":"missing" if not row.get(header,"").strip() else "observed","source_column":header,"source_path":source_path,"source_row":row_number} for header in headers}
        normalized.append({"normalization_version":NORMALIZATION_VERSION,"normalized_at":iso_now(),"source_path":source_path,"source_sha256":checksum,"source_row":row_number,"record_state":"observed","fields":fields})
    return table,raw,normalized

def build_catalog(root: Path) -> dict[str,Any]:
    if not root.is_dir(): raise FileNotFoundError(f"NASA data root was not found: {root}")
    files=[]; tables=[]; raw_tables=[]; experiments=[]; investigations=[]; workbooks=defaultdict(int)
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name in SYSTEM_FILES: continue
        source_path=relative_source_path(path,root); group=source_path.split("/",1)[0]; role=classify_file(source_path); checksum=sha256_file(path); rank,reason=RELEVANCE.get(group,(999,"No relevance rubric is configured for this source group."))
        files.append({"source_path":source_path,"source_sha256":checksum,"investigation_group":group,"format":path.suffix.lower().lstrip(".") or "unknown","bytes":path.stat().st_size,"file_role":role,"data_level":data_level(role),"material_candidate":material_from_path(source_path),"run_id_candidate":run_id_from_path(source_path),"measurement_family":measurement_family(source_path),"relevance_rank":rank,"relevance_reason":reason})
        if path.suffix.lower() in WORKBOOK_SUFFIXES: workbooks[group]+=1
        if path.suffix.lower()==".csv":
            table,raw,normal=read_csv_table(path,root,checksum); tables.append(table); raw_tables.append(raw); experiments.extend(normal)
        if path.name=="i_Investigation.txt":
            investigations.append({"source_path":source_path,"source_sha256":checksum,"group":group,"measurement_family":measurement_family(source_path),"relevance_rank":rank,"relevance_reason":reason,"relevance_rubric":"Direct aerosol evidence, structured conditions, spacecraft-fire scale/context, then machine readability.",**read_investigation_metadata(path)})
    formats=Counter(item["format"] for item in files); materials=Counter(item["material_candidate"] for item in files if item["material_candidate"])
    return {"schema_version":SCHEMA_VERSION,"normalization_version":NORMALIZATION_VERSION,"generated_at":iso_now(),"data_root":str(root),"read_only_source":True,"value_state_vocabulary":[
        'observed',
        'missing',
        'unknown',
        'not_applicable',
        'ambiguous'
    ],"summary":{"file_count":len(files),"format_counts":dict(sorted(formats.items())),"workbook_count_by_group":dict(sorted(workbooks.items())),"filename_material_counts":dict(sorted(materials.items())),"investigation_count":len(investigations),"experimental_record_count":len(experiments)},"investigations":sorted(investigations,key=lambda item:item["relevance_rank"]),"csv_tables":tables,"raw_tables":raw_tables,"normalized_experiments":experiments,"files":files}

def save_catalog(catalog: dict[str,Any], path: Path) -> None: path.write_text(json.dumps(catalog,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
def load_or_build_catalog(root: Path,path: Path) -> dict[str,Any]:
    if path.is_file(): return json.loads(path.read_text(encoding="utf-8"))
    catalog=build_catalog(root); save_catalog(catalog,path); return catalog
def envelope(data: Any,catalog: dict[str,Any],warnings: list[str]|None=None) -> dict[str,Any]:
    return {"data":data,"source":{"catalog_generated_at":catalog["generated_at"],"schema_version":catalog["schema_version"],"read_only_source":True},"warnings":warnings or [],"generated_at":iso_now()}

class CatalogHandler(BaseHTTPRequestHandler):
    catalog={}; frontend_dir=DEFAULT_FRONTEND_DIR; cors_origins:set[str]=set()
    def log_message(self,fmt: str,*args: Any) -> None: print(json.dumps({"time":iso_now(),"event":"http_request","client":self.address_string(),"message":fmt%args}))
    def send_json(self,payload: Any,status: HTTPStatus=HTTPStatus.OK) -> None:
        body=json.dumps(payload,ensure_ascii=False,indent=2).encode("utf-8"); self.send_response(status); self.send_header("Content-Type","application/json; charset=utf-8"); self.send_header("Content-Length",str(len(body)))
        origin=self.headers.get("Origin")
        if origin and origin in self.cors_origins: self.send_header("Access-Control-Allow-Origin",origin); self.send_header("Vary","Origin")
        self.end_headers(); self.wfile.write(body)
    def error_json(self,status: HTTPStatus,code: str,message: str) -> None: self.send_json({"error":{"code":code,"message":message},"generated_at":iso_now()},status)
    def send_static(self,requested: str) -> bool:
        relative="index.html" if requested.rstrip("/") in ("", "/studio", "/archive", "/models", "/gaps", "/science", "/resources") else requested.lstrip("/"); target=(self.frontend_dir/unquote(relative)).resolve(); root=self.frontend_dir.resolve()
        if root not in target.parents and target!=root or not target.is_file(): return False
        body=target.read_bytes(); self.send_response(HTTPStatus.OK); self.send_header("Content-Type",mimetypes.guess_type(target.name)[0] or "application/octet-stream"); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body); return True
    def do_OPTIONS(self) -> None:
        origin=self.headers.get("Origin"); self.send_response(HTTPStatus.NO_CONTENT)
        if origin and origin in self.cors_origins: self.send_header("Access-Control-Allow-Origin",origin); self.send_header("Access-Control-Allow-Methods","GET, POST, OPTIONS"); self.send_header("Access-Control-Allow-Headers","Content-Type"); self.send_header("Vary","Origin")
        self.end_headers()
    def do_GET(self) -> None:
        request=urlparse(self.path); query=parse_qs(request.query); path={
            '/api/health': '/api/v1/health',
            '/api/summary': '/api/v1/summary',
            '/api/investigations': '/api/v1/investigations',
            '/api/tables': '/api/v1/tables',
            '/api/files': '/api/v1/files'
        }.get(request.path,request.path)
        if path in ('/api/v1/studio/library', '/api/v1/studio/record', '/api/v1/studio/history'):
            try:
                if path.endswith('/library'): result = studio.library()
                elif path.endswith('/history'): result = studio.history(query.get('id', [''])[0])
                else: result = studio.get_record(query.get('id', [''])[0])
                self.send_json(envelope(result, self.catalog))
            except ValueError as exc: self.error_json(HTTPStatus.BAD_REQUEST, 'invalid_request', str(exc))
            except FileNotFoundError: self.error_json(HTTPStatus.NOT_FOUND, 'not_found', 'Investigation not found')
            return
        if path == '/api/v1/evidence/review':
            from aero_psi_knowledge import review_catalog
            self.send_json(envelope(review_catalog(),self.catalog)); return
        if path == '/api/v1/si/investigation':
            identifier=query.get('id',[''])[0]
            if not re.fullmatch(r'[a-f0-9]{32}',identifier):
                self.error_json(HTTPStatus.BAD_REQUEST,'invalid_id','Use the returned investigation ID.'); return
            saved=INVESTIGATION_STORAGE/f'{identifier}.json'
            if not saved.is_file():
                self.error_json(HTTPStatus.NOT_FOUND,'not_found','Investigation not found.'); return
            self.send_json(envelope(json.loads(saved.read_text()),self.catalog)); return
        routes={"/api/v1/archive/datasets":lambda:archive.datasets(self.catalog),"/api/v1/health":lambda:{
            'ok': True, 'capabilities': capabilities()
        },"/api/v1/summary":lambda:self.catalog["summary"],"/api/v1/investigations":lambda:self.catalog["investigations"],"/api/v1/rankings/investigations":lambda:investigation_rankings(self.catalog),"/api/v1/tables":lambda:self.catalog["csv_tables"],"/api/v1/raw-tables":lambda:self.catalog["raw_tables"],"/api/v1/experiments":lambda:self.catalog["normalized_experiments"],"/api/v1/atlas/coverage":lambda:atlas_coverage(self.catalog),"/api/v1/atlas/gaps":lambda:atlas_gaps(self.catalog,query.get("group",[
            None
        ])[0]),"/api/v1/atlas/conditions":lambda:atlas_conditions(self.catalog,query.get("group",[
            None
        ])[0]),"/api/v1/atlas/condition-gaps":lambda:atlas_condition_gaps(self.catalog,query.get("group",[
            None
        ])[0],[item for item in query.get("dimensions",[
            ''
        ])[0].split(",") if item] or None),"/api/v1/optical/runs":lambda:optical_runs(DEFAULT_INGESTION_MANIFEST,query.get("group",[
            None
        ])[0])}
        if path=="/api/v1/optical/summary":
            source_path=query.get("source_path",[
                None
            ])[0]
            if not source_path: self.error_json(HTTPStatus.BAD_REQUEST,"missing_source_path","source_path is required."); return
            try: self.send_json(envelope(optical_summary(DEFAULT_INGESTION_MANIFEST,source_path),self.catalog)); return
            except KeyError as exc: self.error_json(HTTPStatus.NOT_FOUND,"run_not_found",str(exc)); return
        if path=="/api/v1/optical/time-series":
            source_path=query.get("source_path",[
                None
            ])[0]
            signals=[item for item in query.get("signals",[
                ''
            ])[0].split(",") if item]
            try: maximum=int(query.get("max_points",[
                '1000'
            ])[0]); data=optical_time_series(DEFAULT_INGESTION_MANIFEST,PROJECT_ROOT,source_path,signals or None,maximum); self.send_json(envelope(data,self.catalog)); return
            except KeyError as exc: self.error_json(HTTPStatus.NOT_FOUND,"run_not_found",str(exc)); return
            except (ValueError,TypeError) as exc: self.error_json(HTTPStatus.BAD_REQUEST,"invalid_time_series_request",str(exc)); return
        if path=="/api/v1/optical/lag":
            source_path=query.get("source_path",[
                None
            ])[0]; left=query.get("left",[
                None
            ])[0]; right=query.get("right",[
                None
            ])[0]
            try: data=optical_lag_analysis(DEFAULT_INGESTION_MANIFEST,PROJECT_ROOT,source_path,left,right,int(query.get("max_lag_samples",[
                '30'
            ])[0])); self.send_json(envelope(data,self.catalog)); return
            except KeyError as exc: self.error_json(HTTPStatus.NOT_FOUND,"run_not_found",str(exc)); return
            except (ValueError,TypeError) as exc: self.error_json(HTTPStatus.BAD_REQUEST,"invalid_lag_request",str(exc)); return
        if path=="/api/v1/models/coagulation/source-candidates":
            source_path=query.get("source_path",[None])[0]
            try: self.send_json(envelope(coagulation_input_candidates(DEFAULT_INGESTION_MANIFEST,source_path),self.catalog)); return
            except KeyError as exc: self.error_json(HTTPStatus.NOT_FOUND,"run_not_found",str(exc)); return
        if path=="/api/v1/atlas/suggested-measurement":
            try:
                gaps=atlas_condition_gaps(self.catalog,query.get("group",[
                    None
                ])[0],[item for item in query.get("dimensions",[
                    ''
                ])[0].split(",") if item] or None)["gaps"]
                index=int(query.get("gap_index",[
                    '0'
                ])[0]); self.send_json(envelope(suggested_measurement(gaps[index]),self.catalog)); return
            except (ValueError,IndexError) as exc: self.error_json(HTTPStatus.BAD_REQUEST,"invalid_gap_request",str(exc)); return
        if path=="/api/v1/files":
            data=self.catalog["files"]; group=query.get("group",[
                None
            ])[0]; role=query.get("role",[
                None
            ])[0]
            if group: data=[item for item in data if item["investigation_group"]==group]
            if role: data=[item for item in data if item["file_role"]==role]
            self.send_json(envelope(data,self.catalog)); return
        if path in routes:
            try: self.send_json(envelope(routes[path](),self.catalog)); return
            except FileNotFoundError: self.error_json(HTTPStatus.SERVICE_UNAVAILABLE,"ingestion_not_available","Run the PSI importer before requesting optical summaries."); return
        if path.startswith("/api/"): self.error_json(HTTPStatus.NOT_FOUND,"route_not_found","Use a documented /api/v1 route."); return
        if not self.send_static(path): self.error_json(HTTPStatus.NOT_FOUND,"page_not_found","The requested page does not exist.")
    def do_POST(self) -> None:
        request=urlparse(self.path)
        if request.path not in {
            '/api/v1/models/coagulation',
            '/api/v1/models/coagulation/sectional',
            '/api/v1/models/coagulation/sensitivity',
            '/api/v1/models/coagulation/sweep',
            '/api/v1/models/coagulation/compare-observations',
            '/api/v1/models/coagulation/uncertainty',
            '/api/v1/models/coagulation/calibrate',
            '/api/v1/models/coagulation/convergence',
            '/api/v1/models/coagulation/domain-study',
            '/api/v1/models/scattering',
            '/api/v1/models/coupled-optics',
            '/api/v1/observed/analyze',
            '/api/v1/observed/export',
            '/api/v1/observed/compare',
            '/api/v1/copilot',
            '/api/v1/si/investigate',
            '/api/v1/research/gap-review', '/api/v1/research/explore', '/api/v1/research/interpret', '/api/v1/research/design', '/api/v1/archive/table', '/api/v1/archive/interpret',
            '/api/v1/studio/from-research', '/api/v1/studio/attach-model', '/api/v1/studio/create', '/api/v1/studio/save', '/api/v1/studio/generate',
            '/api/v1/studio/dataset', '/api/v1/studio/execute', '/api/v1/studio/interpret',
            '/api/v1/evidence/search',
            '/api/v1/evidence/excerpt',
            '/api/v1/evidence/record',
            '/api/v1/rankings/question',
            '/api/v1/atlas/plan',
            '/api/v1/si/interpret-point', '/api/v1/si/interpret-model'
        }:
            self.error_json(HTTPStatus.NOT_FOUND,"route_not_found","Use a documented /api/v1 route."); return
        try:
            length=int(self.headers.get("Content-Length","0"))
            if length < 0 or length > 100_000: raise ScenarioInputError("Request body must be between 0 and 100000 bytes.")
            raw=self.rfile.read(length) if length else b"{}"
            payload=json.loads(raw.decode("utf-8"))
            if not isinstance(payload,dict): raise ValueError("Request body must be a JSON object.")
            if request.path=='/api/v1/research/gap-review':
                from aero_psi_gap_si import review
                self.send_json(envelope(review(self.catalog,payload),self.catalog)); return
            if request.path=='/api/v1/si/interpret-model':
                from aero_psi_model_interpretation import interpret
                self.send_json(envelope(interpret(self.catalog,payload),self.catalog)); return
            if request.path=='/api/v1/archive/interpret':
                self.send_json(envelope(archive.interpret(self.catalog,payload),self.catalog)); return
            if request.path=='/api/v1/archive/table':
                self.send_json(envelope(archive.table_page(self.catalog,payload),self.catalog)); return
            if request.path=='/api/v1/research/design':
                from aero_psi_experiment_design import preview
                self.send_json(envelope(preview(payload.get('design')),self.catalog)); return
            if request.path in ('/api/v1/research/explore','/api/v1/research/interpret'):
                function=research.explore if request.path.endswith('/explore') else research.interpret
                self.send_json(envelope(function(self.catalog,payload),self.catalog)); return
            if request.path.startswith('/api/v1/studio/'):
                actions = {'from-research': lambda p: studio.from_research(p, self.catalog), 'attach-model': studio.attach_model, 'create': studio.create, 'save': studio.save, 'generate': lambda p: studio.generate(p, self.catalog),
                           'dataset': studio.add_dataset, 'execute': lambda p: studio.execute(p, self.catalog),
                           'interpret': lambda p: studio.interpret(p, self.catalog)}
                self.send_json(envelope(actions[request.path.rsplit('/', 1)[1]](payload), self.catalog)); return
            if request.path in ('/api/v1/rankings/question','/api/v1/atlas/plan'):
                function=rank_for_question if request.path.endswith('/question') else gap_plan
                self.send_json(envelope(function(self.catalog,payload),self.catalog)); return
            batch2={'/api/v1/models/scattering':simulate_scattering,'/api/v1/models/coupled-optics':coupled_scattering,'/api/v1/models/coagulation/domain-study':domain_study,'/api/v1/observed/analyze':analyze_observed,'/api/v1/observed/export':lambda p:export_analysis(analyze_observed(p)),'/api/v1/observed/compare':compare_observed}
            if request.path in batch2:
                self.send_json(envelope(batch2[request.path](payload),self.catalog)); return
            if request.path=='/api/v1/si/investigate':
                self.send_json(envelope(investigate(self.catalog,payload),self.catalog)); return
            if request.path=='/api/v1/evidence/record':
                from aero_psi_copilot import _chunks
                identifier=payload.get('id')
                if not isinstance(identifier,str) or len(identifier)>1000: raise ValueError('Provide a source record ID')
                record=next((r for r in _chunks(self.catalog) if r['id']==identifier),None)
                if record is None: raise ValueError('Unknown or stale source record')
                self.send_json(envelope(record,self.catalog)); return
            if request.path in ('/api/v1/evidence/search','/api/v1/evidence/excerpt'):
                records=document_records()
                if request.path.endswith('/excerpt'):
                    ids=payload.get('ids',[payload.get('id')])
                    if not isinstance(ids,list) or not 1<=len(ids)<=80 or not all(isinstance(i,str) and len(i)<=100 for i in ids):
                        raise ValueError('Provide 1–80 source excerpt IDs')
                    lookup={r['id']:r for r in records}
                    if any(identifier not in lookup for identifier in ids): raise ValueError('Unknown or stale document excerpt')
                    selected=[lookup[identifier] for identifier in dict.fromkeys(ids)]
                else:
                    question=payload.get('question')
                    if not isinstance(question,str) or not 1<=len(question.strip())<=2000: raise ValueError('question must be 1–2000 characters')
                    from aero_psi_copilot import retrieve
                    selected=retrieve(self.catalog,question,limit=10)
                self.send_json(envelope(selected,self.catalog)); return
            if request.path=='/api/v1/copilot':
                self.send_json(envelope(answer_question(self.catalog,payload.get("question"),payload.get("mode","auto"),history=payload.get("history")),self.catalog)); return
            if request.path=='/api/v1/si/interpret-point':
                self.send_json(envelope(copilot_interpret_point(self.catalog,payload),self.catalog)); return
            studies={'/api/v1/models/coagulation/uncertainty':uncertainty,'/api/v1/models/coagulation/calibrate':calibrate,'/api/v1/models/coagulation/convergence':convergence}
            if request.path in studies:
                self.send_json(envelope(studies[request.path](payload),self.catalog)); return
            model={"/api/v1/models/coagulation":simulate_coagulation,"/api/v1/models/coagulation/sectional":simulate_sectional,"/api/v1/models/coagulation/sensitivity":coagulation_sensitivity,"/api/v1/models/coagulation/sweep":coagulation_sweep,"/api/v1/models/coagulation/compare-observations":compare_observations}[request.path]
            self.send_json(envelope(model(payload),self.catalog))
        except (UnicodeDecodeError,json.JSONDecodeError):
            self.error_json(HTTPStatus.BAD_REQUEST,"invalid_json","Request body must be a JSON object.")
        except studio.RevisionConflict as exc:
            self.error_json(HTTPStatus.CONFLICT, 'revision_conflict', str(exc))
        except studio.StudioUnavailable as exc:
            self.error_json(HTTPStatus.SERVICE_UNAVAILABLE, 'si_unavailable', str(exc))
        except RuntimeDependencyError as exc:
            self.error_json(HTTPStatus.SERVICE_UNAVAILABLE,"scattering_unavailable",str(exc))
        except ScenarioInputError as exc:
            self.error_json(HTTPStatus.BAD_REQUEST,"invalid_scenario_input",str(exc))
        except (ValueError, KeyError) as exc:
            self.error_json(HTTPStatus.BAD_REQUEST,"invalid_request",str(exc))
        except FileNotFoundError:
            self.error_json(HTTPStatus.SERVICE_UNAVAILABLE,"source_unavailable","Source or derived data is unavailable; check ingestion.")

def command_index(args: argparse.Namespace) -> None:
    catalog=build_catalog(args.data_root); save_catalog(catalog,args.catalog); print(json.dumps({"event":"catalog_indexed","files":catalog["summary"]["file_count"],"catalog":str(args.catalog)}))
def command_serve(args: argparse.Namespace) -> None:
    CatalogHandler.catalog=load_or_build_catalog(args.data_root,args.catalog); CatalogHandler.frontend_dir=args.frontend_dir; CatalogHandler.cors_origins=set(args.cors_origin); server=ThreadingHTTPServer((args.host,args.port),CatalogHandler); print(json.dumps({"event":"server_started","url":f"http://{args.host}:{args.port}","api":"/api/v1/health"}))
    try: server.serve_forever()
    except KeyboardInterrupt: print(json.dumps({
        'event': 'server_stopped'
    }))
    finally: server.server_close()
def parser() -> argparse.ArgumentParser:
    result=argparse.ArgumentParser(description="Read-only AERO-PSI catalog API and frontend shell"); result.add_argument("--data-root",type=Path,default=DEFAULT_DATA_ROOT); result.add_argument("--catalog",type=Path,default=DEFAULT_CATALOG_PATH); subs=result.add_subparsers(dest="command",required=True); subs.add_parser("index",help="Create or refresh the local catalog")
    serve=subs.add_parser("serve",help="Run local API and frontend"); serve.add_argument("--host",default="127.0.0.1"); serve.add_argument("--port",type=int,default=8000); serve.add_argument("--frontend-dir",type=Path,default=DEFAULT_FRONTEND_DIR); serve.add_argument("--cors-origin",action="append",default=[
        'http://127.0.0.1:8000'
    ]); return result
def main() -> None:
    args=parser().parse_args()
    if args.command=="index": command_index(args)
    if args.command=="serve": command_serve(args)
if __name__=="__main__": main()
