"""Evidence-preserving optical-response views over existing imported PSI run metrics."""
from __future__ import annotations

import json
import gzip
import math
from statistics import median
from pathlib import Path
from typing import Any

from aero_psi_ranking import run_readiness

OPTICAL_SIGNALS = {
    'obscuration_voltage',
    'scatter_voltage',
    'sts_voltage',
    'ion_a_voltage',
    'ion_b_voltage',
    'ptrak_particles_per_cc',
    'dusttrak_a_mg_m3',
    'dusttrak_b_mg_m3'
}


def _records(manifest_path: Path) -> list[dict[str, Any]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return [record for record in manifest.get("records", []) if record.get("status") == "imported"]


def runs(manifest_path: Path, group: str | None = None) -> list[dict[str, Any]]:
    result = []
    for record in _records(manifest_path):
        if group and record.get("group") != group:
            continue
        analysis = record.get("analysis", {})
        available = analysis.get("available_signals", {})
        optical = {name: header for name, header in available.items() if name in OPTICAL_SIGNALS}
        item={"source_path": record["source_path"], "source_sha256": record["source_sha256"], "group": record["group"], "material_candidate": record.get("material_candidate"), "worksheet": record.get("worksheet"), "quality_state": analysis.get("quality_state"), "event_window": analysis.get("selected_event_window"), "optical_signal_columns": optical, "warnings": record.get("warnings", [])}
        readiness_input={**item,"row_count":analysis.get("row_count"),"missing_time_rows":analysis.get("missing_time_rows"),"duplicate_timestamps":analysis.get("duplicate_timestamps"),"non_monotonic_transitions":analysis.get("non_monotonic_transitions"),"metrics":analysis.get("metrics"),"join_status":record.get("join_status"),"verified_experiment_key":record.get("verified_experiment_key")}
        item["analysis_readiness"] = run_readiness(readiness_input)
        result.append(item)
    return sorted(result, key=lambda item: item["source_path"])


def summary(manifest_path: Path, source_path: str) -> dict[str, Any]:
    record = next((item for item in _records(manifest_path) if item["source_path"] == source_path), None)
    if record is None:
        raise KeyError("No imported run matches source_path.")
    analysis = record.get("analysis", {})
    available = analysis.get("available_signals", {})
    metrics = analysis.get("metrics", {})
    selected = {name: metrics[name] for name in OPTICAL_SIGNALS if name in metrics}
    return {"classification": "source-derived signal summary; not a calibrated optical-property estimate", "source_path": record["source_path"], "source_sha256": record["source_sha256"], "worksheet": record.get("worksheet"), "quality_state": analysis.get("quality_state"), "event_window": analysis.get("selected_event_window"), "available_signal_columns": {name: header for name, header in available.items() if name in OPTICAL_SIGNALS}, "metrics": selected, "warnings": record.get("warnings", []) + ["Scatter and obscuration values remain detector voltages unless a run-specific calibration chain is supplied."]}


def _record(manifest_path: Path, source_path: str) -> dict[str, Any]:
    record=next((item for item in _records(manifest_path) if item["source_path"] == source_path),None)
    if record is None: raise KeyError("No imported run matches source_path.")
    return record


def _number(value: Any) -> float | None:
    try:
        number=float(value)
        return number if math.isfinite(number) and number != -10 else None
    except (TypeError,ValueError): return None


def _rows(record: dict[str, Any], root: Path) -> list[dict[str, Any]]:
    path=root/record["derived_path"]
    with gzip.open(path,"rt",encoding="utf-8") as handle: return [json.loads(line) for line in handle]


def time_series(manifest_path: Path, root: Path, source_path: str, signals: list[str] | None = None, max_points: int = 1000) -> dict[str, Any]:
    if max_points < 10 or max_points > 5000: raise ValueError("max_points must be between 10 and 5000.")
    record=_record(manifest_path,source_path); analysis=record.get("analysis",{}); available=analysis.get("available_signals",{})
    selected=signals or [name for name in available if name in OPTICAL_SIGNALS]
    unknown=[name for name in selected if name not in available]
    selected=[name for name in selected if name in available]
    if not selected: raise ValueError("No requested optical signal is available for this run.")
    source_rows=_rows(record,root); stride=max(1,math.ceil(len(source_rows)/max_points)); sample=source_rows[::stride]
    if sample[-1]["source_row"] != source_rows[-1]["source_row"]: sample.append(source_rows[-1])
    points=[]
    for row in sample:
        values=row["values"]; points.append({"source_row":row["source_row"],"time":_number(values.get("Time")),"time_string":values.get("TimeString"),"values":{name:_number(values.get(available[name])) for name in selected}})
    return {"classification":"observed source samples; values are not interpolated or recalibrated","source_path":source_path,"source_sha256":record["source_sha256"],"worksheet":record.get("worksheet"),"signal_columns":{name:available[name] for name in selected},"downsample":{"original_row_count":len(source_rows),"returned_row_count":len(points),"selection":"every Nth source row plus final source row; source values unchanged"},"event_window":analysis.get("selected_event_window"),"points":points,"warnings":record.get("warnings",[])+([f"Unavailable requested signals: {', '.join(unknown)}."] if unknown else [])}


def source_point(manifest_path: Path, root: Path, source_path: str, signal: str, source_row: int) -> dict[str, Any]:
    """Return one exact source row for SI inspection without downsampling or interpolation."""
    record=_record(manifest_path,source_path); analysis=record.get("analysis",{}); available=analysis.get("available_signals",{})
    if signal not in available: raise ValueError("Requested optical signal is not available for this run.")
    row=next((item for item in _rows(record,root) if item["source_row"] == source_row),None)
    if row is None: raise ValueError("source_row is not present in the imported source record.")
    values=row["values"]
    return {"classification":"exact observed source sample; value is not interpolated or recalibrated","source_path":source_path,"source_sha256":record["source_sha256"],"worksheet":record.get("worksheet"),"source_row":source_row,"time":_number(values.get("Time")),"time_string":values.get("TimeString"),"signal":signal,"source_column":available[signal],"value":_number(values.get(available[signal])),"warnings":record.get("warnings",[])+["Detector values remain in the source-named unit unless a run-specific calibration chain is supplied."]}


def lag_analysis(manifest_path: Path, root: Path, source_path: str, left: str, right: str, max_lag_samples: int = 30) -> dict[str, Any]:
    if max_lag_samples < 1 or max_lag_samples > 300: raise ValueError("max_lag_samples must be between 1 and 300.")
    record=_record(manifest_path,source_path); analysis=record.get("analysis",{}); available=analysis.get("available_signals",{})
    if left not in available or right not in available: raise ValueError("Both requested signals must be available in this run.")
    window=analysis.get("selected_event_window",{}); rows=_rows(record,root)
    boundaries=window.get("test_source_rows")
    if not boundaries: raise ValueError("Lag analysis requires a source-derived TestRunning event window.")
    start,end=boundaries[0],boundaries[1]; chosen=[row for row in rows if start <= row["source_row"] <= end]
    x=[_number(row["values"].get(available[left])) for row in chosen]; y=[_number(row["values"].get(available[right])) for row in chosen]
    times=[_number(row["values"].get("Time")) for row in chosen]
    valid_times=[b-a for a,b in zip(times,times[1:]) if a is not None and b is not None and b>a]
    interval=median(valid_times) if valid_times else None
    pairs=[]
    for lag in range(-max_lag_samples,max_lag_samples+1):
        paired=[(x[i],y[i+lag]) for i in range(len(x)) if 0 <= i+lag < len(y) and x[i] is not None and y[i+lag] is not None]
        if len(paired) < 4: continue
        a,b=zip(*paired); am=sum(a)/len(a); bm=sum(b)/len(b); da=sum((item-am)**2 for item in a); db=sum((item-bm)**2 for item in b)
        if da == 0 or db == 0: continue
        corr=sum((aa-am)*(bb-bm) for aa,bb in paired)/math.sqrt(da*db)
        pairs.append({"lag_samples":lag,"lag_seconds":lag*interval if interval is not None else None,"pearson_correlation":corr,"pair_count":len(paired)})
    if not pairs: raise ValueError("Insufficient non-sentinel paired values for lag analysis.")
    best=max(pairs,key=lambda item:abs(item["pearson_correlation"]))
    return {"classification":"within-run association screen; correlation/lag is not causality","source_path":source_path,"signals":{"left":{"name":left,"source_column":available[left]},"right":{"name":right,"source_column":available[right]}},"event_window":window,"sampling":{"median_interval_s":interval,"warning":"Lag seconds are only meaningful when source timestamps are sufficiently regular."},"strongest_absolute_correlation":best,"curve":pairs,"warnings":[
        'Signals are baseline-unadjusted here; use source-derived metric baselines separately.',
        'A lag/correlation result does not establish a physical causal relationship.'
    ]}


def coagulation_input_candidates(manifest_path: Path, source_path: str) -> dict[str, Any]:
    """Offer source-provenanced inputs for user review; never apply them automatically."""
    record=_record(manifest_path,source_path); analysis=record.get("analysis",{}); available=analysis.get("available_signals",{}); metrics=analysis.get("metrics",{})
    candidates=[]; ptrak=metrics.get("ptrak_particles_per_cc",{})
    if ptrak.get("status") == "available" and ptrak.get("baseline_median",0) > 0: candidates.append({"scenario_input":"initial_number_concentration_m3","value":ptrak["baseline_median"]*1_000_000,"state":"derived_from_observed_with_explicit_SI_conversion","source_field":available["ptrak_particles_per_cc"],"source_unit":"particles/cm^3 as named by source header","conversion":"1 m^3 = 1,000,000 cm^3","warning":"Candidate only; never automatically applied."})
    elif "ptrak_particles_per_cc" in available: candidates.append({"scenario_input":"initial_number_concentration_m3","value":None,"state":"rejected_invalid_source_value","source_field":available["ptrak_particles_per_cc"],"source_unit":"particles/cm^3 as named by source header","conversion":None,"warning":"Baseline is nonpositive or invalid; it is not eligible as a coagulation input candidate."})
    temp=metrics.get("plume_temperature_c",{})
    if temp.get("status") == "available": candidates.append({"scenario_input":"gas_temperature_k","value":temp["baseline_median"]+273.15,"state":"derived_from_observed_with_explicit_SI_conversion","source_field":available["plume_temperature_c"],"source_unit":"degrees C as named by source header","conversion":"K = degrees C + 273.15","warning":"Candidate only; model applicability remains an assumption."})
    candidates += [{"scenario_input":"initial_median_diameter_m","value":None,"state":"unknown","source_field":None,"source_unit":None,"conversion":None,"warning":"No particle-size distribution is inferred from detector signals."},{"scenario_input":"particle_density_kg_m3","value":None,"state":"unknown","source_field":None,"source_unit":None,"conversion":None,"warning":"Density requires an external documented rationale."}]
    return {"classification":"optional source-backed scenario candidates; user review required","source_path":source_path,"source_sha256":record["source_sha256"],"event_window":analysis.get("selected_event_window"),"candidates":candidates,"warnings":["Candidates are never inserted into a model automatically.","A source value does not establish continuum-model validity."]}
