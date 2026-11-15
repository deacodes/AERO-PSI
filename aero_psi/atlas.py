"""Transparent supplied-archive coverage and gap calculation; no opaque scoring."""
from __future__ import annotations

from collections import defaultdict
from typing import Any

DIMENSIONS=("material_or_fuel","flow","oxygen","pressure","duration_or_aging","temperature","platform_gravity","geometry_flame_type","outcome")


def conditions(catalog: dict[str, Any], group: str | None = None) -> list[dict[str, Any]]:
    result=[]
    investigation_meta={item.get("group"):{"platform":item.get("platform"),"title":item.get("title")} for item in catalog.get("investigations",[])}
    for record in catalog.get("normalized_experiments",[]):
        source=record["source_path"]; investigation=source.split("/",1)[0]
        if group and investigation != group: continue
        fields=record.get("fields",{})
        values={dimension:fields.get(dimension,{
            'value': '',
            'state': 'missing',
            'source_column': None
        }) for dimension in DIMENSIONS}
        platform=investigation_meta.get(investigation,{}).get("platform")
        # Platform context must never masquerade as a measured acceleration.
        values["platform_gravity"]=fields.get("acceleration_m_s2", {"value":"","state":"unknown","source_column":None})
        values["geometry_flame_type"]=fields.get("geometry_flame_type", fields.get("flame_type", {"value":"","state":"unknown","source_column":None}))
        values["outcome"]=fields.get("outcome", {"value":"","state":"unknown","source_column":None})
        result.append({"investigation_group":investigation,"investigation_title":investigation_meta.get(investigation,{}).get("title"),"source_path":source,"source_sha256":record["source_sha256"],"source_row":record["source_row"],"conditions":values,"platform_context":platform,"data_level":"structured conditions","provenance":{"source_path":source,"source_row":record["source_row"]}})
    return result


def coverage(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    cells: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for file in catalog.get("files", []):
        group = file["investigation_group"]
        material = file.get("material_candidate") or "unspecified"
        family = file["measurement_family"]
        cells[(group, material, family)].append(file)
    result=[]
    for (group, material, family), files in sorted(cells.items()):
        levels={item["data_level"] for item in files}
        state = "direct_raw_or_derived_measurements" if "direct raw or derived measurements" in levels else "structured_or_document_context_only"
        result.append({"investigation_group":group,"material_or_fuel":material,"measurement_family":family,"coverage_state":state,"file_count":len(files),"source_paths":[item["source_path"] for item in files]})
    return result


def gaps(catalog: dict[str, Any], group: str | None = None) -> list[dict[str, Any]]:
    rows = coverage(catalog)
    if group: rows=[row for row in rows if row["investigation_group"] == group]
    groups=sorted({row["investigation_group"] for row in rows})
    materials=sorted({row["material_or_fuel"] for row in rows if row["material_or_fuel"] != "unspecified"})
    families=sorted({row["measurement_family"] for row in rows})
    existing={(row["investigation_group"],row["material_or_fuel"],row["measurement_family"]) for row in rows}
    missing=[]
    for investigation in groups:
        local=[r for r in rows if r["investigation_group"]==investigation]
        materials=sorted({r["material_or_fuel"] for r in local if r["material_or_fuel"]!="unspecified"})
        families=sorted({r["measurement_family"] for r in local})
        for material in materials:
            for family in families:
                if (investigation,material,family) not in existing:
                    missing.append({"investigation_group":investigation,"material_or_fuel":material,"measurement_family":family,"gap_state":"no_cataloged_supplied_file_for_selected_combination","interpretation":"catalog gap only; not evidence that no real-world measurement exists"})
    return missing


def condition_gaps(catalog: dict[str, Any], group: str | None = None, dimensions: list[str] | None = None) -> dict[str, Any]:
    from itertools import product
    selected=dimensions or ["material_or_fuel","flow","duration_or_aging"]
    if not isinstance(selected,list) or not 1 <= len(selected) <= 4 or len(set(selected)) != len(selected) or any(d not in DIMENSIONS for d in selected):
        raise ValueError("Choose 1–4 distinct supported atlas dimensions.")
    rows=conditions(catalog,group); strata=defaultdict(list); excluded=0
    for row in rows:
        fields=[row["conditions"][d] for d in selected]
        if any(f.get("state")!="observed" or not str(f.get("value","")).strip() for f in fields):
            excluded+=1; continue
        # Never transfer factor levels between source tables, materials or flame geometries.
        material=row["conditions"]["material_or_fuel"].get("value","")
        geometry=row["conditions"]["geometry_flame_type"].get("value","")
        key=(row["source_path"],str(material),str(geometry),tuple(f.get("source_column") for f in fields))
        strata[key].append((row,tuple(str(f["value"]).strip() for f in fields)))
    gaps_out=[]; summaries=[]; examined=0; truncated=False
    for (source,material,geometry,columns), items in sorted(strata.items(),key=lambda pair:str(pair[0])):
        values=[sorted({combo[i] for _,combo in items}) for i in range(len(selected))]
        observed={combo for _,combo in items}
        summaries.append({"source_path":source,"material":material,"geometry":geometry,"source_columns":dict(zip(selected,columns)),
                          "record_count":len(items),"observed_combination_count":len(observed),
                          "observed_values":dict(zip(selected,values)),"source_rows":[r["source_row"] for r,_ in items]})
        if truncated: continue
        for combo in product(*values):
            if examined>=2000 or len(gaps_out)>=100: truncated=True; break
            examined+=1
            if combo in observed: continue
            # Require a nearest same-material record differing in exactly one selected factor.
            neighbor=next(((r,c) for r,c in items if sum(a!=b for a,b in zip(combo,c))==1),None)
            if neighbor is None: continue
            row,base=neighbor
            changed=next(d for d,a,b in zip(selected,combo,base) if a!=b)
            gaps_out.append({"investigation_group":row["investigation_group"],"selected_conditions":dict(zip(selected,combo)),
                "source_path":source,"source_sha256":row["source_sha256"],"source_columns":dict(zip(selected,columns)),
                "anchor_source_row":row["source_row"],"anchor_conditions":dict(zip(selected,base)),"varied_dimension":changed,
                "gap_state":"no_structured_supplied_record_for_selected_combination",
                "feasibility":"unknown; same-table factor recombination still requires physical and operating-range review",
                "interpretation":"Unrecorded same-table, same-material candidate contrast; not evidence of a missing real-world experiment or scientific knowledge gap."})
    return {"classification":"bounded condition candidates within source table, material, geometry and column units", "dimensions":selected,
        "included_record_count":len(rows)-excluded,"excluded_record_count":excluded,"strata":summaries,
        "examined_combination_count":examined,"truncated":truncated,"limits":{"examined":2000,"returned":100},"gaps":gaps_out}


def suggested_measurement(gap: dict[str, Any]) -> dict[str, Any]:
    if gap.get("gap_state") != "no_structured_supplied_record_for_selected_combination": raise ValueError("Input must be a condition-gap record.")
    return {"classification":"proposal, not a scientific recommendation or finding",
        "proposal":"Review the source table and operating constraints, then test a single-factor contrast if physically feasible.",
        "selected_conditions":gap["selected_conditions"],"controls":{k:v for k,v in gap["selected_conditions"].items() if k!=gap.get("varied_dimension")},
        "varied_parameter":gap.get("varied_dimension"),"reference_conditions":gap.get("anchor_conditions"),
        "evidence":{"source_path":gap.get("source_path"),"source_row":gap.get("anchor_source_row"),"source_sha256":gap.get("source_sha256"),"source_columns":gap.get("source_columns")},
        "feasibility":gap.get("feasibility","not assessed"),
        "required_outputs":["run identifier, exact conditions and source rows","synchronized measurements, units and instrument calibration","blank/reference observations, replicates and uncertainty","question-specific validation target declared before acquisition"],
        "reason":gap["interpretation"]}
