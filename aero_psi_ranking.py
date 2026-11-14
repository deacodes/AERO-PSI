"""Transparent evidence-priority and run-readiness scores for AERO-PSI.

These scores order the supplied archive for this application's workflow. They do
not measure scientific quality, experimental validity, or the importance of a
NASA investigation outside AERO-PSI.
"""
from __future__ import annotations

import math
from collections import Counter, defaultdict
from typing import Any


INVESTIGATION_WEIGHTS = {
    "aerosol_goal_fit": 0.35,
    "direct_measurement_depth": 0.25,
    "structured_condition_depth": 0.20,
    "machine_readability": 0.10,
    "metadata_completeness": 0.10,
}

GOAL_FIT = {
    "smoke aerosol and detector response": 1.00,
    "large-scale spacecraft fire": 0.75,
    "solid-material flammability": 0.55,
    "droplet extinction": 0.35,
    "gaseous diffusion flames": 0.25,
    "program context": 0.10,
}

RUN_WEIGHTS = {
    "optical_signal_coverage": 0.25,
    "event_window_available": 0.20,
    "value_completeness": 0.15,
    "time_integrity": 0.15,
    "sample_depth": 0.10,
    "verified_linkage": 0.05,
    "warning_cleanliness": 0.10,
}

MACHINE_READABLE_ROLES = {
    "raw or derived run workbook",
    "workbook",
    "experimental table",
    "structured table",
}
METADATA_FIELDS = (
    "title",
    "platform",
    "research_area",
    "objective",
    "start_date",
    "end_date",
    "doi",
)


def _group_from_source(record: dict[str, Any]) -> str:
    return str(record.get("source_path", "")).split("/", 1)[0]


def investigation_rankings(catalog: dict[str, Any]) -> dict[str, Any]:
    """Rank investigations by explicit, source-derived AERO-PSI usefulness."""
    files_by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in catalog.get("files", []):
        files_by_group[str(item.get("investigation_group", "unknown"))].append(item)

    records_by_group = Counter(
        _group_from_source(record) for record in catalog.get("normalized_experiments", [])
    )
    maximum_records = max(records_by_group.values(), default=0)
    ranked = []

    for investigation in catalog.get("investigations", []):
        group = str(investigation.get("group", "unknown"))
        files = files_by_group.get(group, [])
        role_counts = Counter(str(item.get("file_role", "unknown")) for item in files)
        direct_count = role_counts["raw or derived run workbook"]
        structured_count = records_by_group[group]
        machine_count = sum(role_counts[role] for role in MACHINE_READABLE_ROLES)
        known_metadata = sum(bool(str(investigation.get(field, "")).strip()) for field in METADATA_FIELDS)

        components = {
            "aerosol_goal_fit": GOAL_FIT.get(str(investigation.get("measurement_family", "program context")), 0.10),
            "direct_measurement_depth": min(1.0, direct_count / 10.0),
            "structured_condition_depth": (
                math.log1p(structured_count) / math.log1p(maximum_records)
                if maximum_records else 0.0
            ),
            "machine_readability": machine_count / len(files) if files else 0.0,
            "metadata_completeness": known_metadata / len(METADATA_FIELDS),
        }
        score = 100.0 * sum(
            INVESTIGATION_WEIGHTS[name] * value for name, value in components.items()
        )
        component_rows = {
            name: {
                "normalized_value": round(value, 4),
                "weight": weight,
                "points": round(100.0 * value * weight, 1),
            }
            for name, value in components.items()
            for weight in (INVESTIGATION_WEIGHTS[name],)
        }
        ranked.append({
            "group": group,
            "title": investigation.get("title") or group,
            "measurement_family": investigation.get("measurement_family"),
            "platform": investigation.get("platform"),
            "score": round(score, 1),
            "components": component_rows,
            "evidence_counts": {
                "catalogued_files": len(files),
                "direct_measurement_files": direct_count,
                "structured_experiment_records": structured_count,
                "machine_readable_files": machine_count,
                "known_metadata_fields": known_metadata,
                "metadata_fields_considered": len(METADATA_FIELDS),
            },
            "classification": "AERO-PSI evidence-priority score",
        })

    ranked.sort(key=lambda item: (-item["score"], str(item["title"])))
    for position, item in enumerate(ranked, start=1):
        item["position"] = position
    return {
        "classification": "derived archive-navigation ranking; not scientific quality or experimental validity",
        "formula": "100 × (0.35 goal fit + 0.25 direct measurement depth + 0.20 structured-condition depth + 0.10 machine readability + 0.10 metadata completeness)",
        "normalization": {
            "direct_measurement_depth": "min(1, direct run-workbook count / 10)",
            "structured_condition_depth": "log(1 + group records) / log(1 + largest group record count)",
            "machine_readability": "machine-readable files / catalogued group files",
            "metadata_completeness": "present fields / 7 considered metadata fields",
        },
        "weights": INVESTIGATION_WEIGHTS,
        "items": ranked,
    }


def run_readiness(run: dict[str, Any]) -> dict[str, Any]:
    """Score whether an imported run is convenient for immediate UI analysis."""
    signal_count = len(run.get("optical_signal_columns", {}))
    event_window = run.get("event_window") or {}
    row_count = max(0, int(run.get("row_count") or 0))
    anomalies = sum(max(0, int(run.get(name) or 0)) for name in (
        "missing_time_rows", "duplicate_timestamps", "non_monotonic_transitions"
    ))
    metrics = run.get("metrics") or {}
    missing_fractions = [
        details.get("missing_fraction")
        for name, details in metrics.items()
        if name in run.get("optical_signal_columns", {})
        and isinstance(details, dict)
        and isinstance(details.get("missing_fraction"), (int, float))
    ]
    value_completeness = (
        max(0.0, 1.0 - sum(missing_fractions) / len(missing_fractions))
        if missing_fractions else 0.0
    )
    verified_linkage = (
        1.0 if run.get("verified_experiment_key")
        else 0.5 if run.get("join_status") == "matched"
        else 0.0
    )
    components = {
        "optical_signal_coverage": min(1.0, signal_count / 8.0),
        "event_window_available": 1.0 if event_window.get("test_source_rows") else 0.0,
        "value_completeness": value_completeness,
        "time_integrity": max(0.0, 1.0 - min(1.0, anomalies / max(1, row_count))),
        "sample_depth": 1.0 - math.exp(-row_count / 2000.0),
        "verified_linkage": verified_linkage,
        "warning_cleanliness": max(0.0, 1.0 - len(run.get("warnings", [])) / 5.0),
    }
    score = 100.0 * sum(RUN_WEIGHTS[name] * value for name, value in components.items())
    return {
        "score": round(score, 1),
        "classification": "analysis-readiness score; not scientific validity",
        "formula": "100 × (0.25 signal coverage + 0.20 event window + 0.15 value completeness + 0.15 time integrity + 0.10 sample depth + 0.05 verified linkage + 0.10 warning cleanliness)",
        "components": {
            name: {
                "normalized_value": round(value, 4),
                "weight": RUN_WEIGHTS[name],
                "points": round(100.0 * value * RUN_WEIGHTS[name], 1),
            }
            for name, value in components.items()
        },
    }
