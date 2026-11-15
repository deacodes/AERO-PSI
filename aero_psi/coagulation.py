#!/usr/bin/env python3
"""Deterministic, assumption-explicit Brownian coagulation scenario model.

This is a model scenario, not a NASA measurement or a detector calibration.  It
uses the monodisperse, continuum-regime Brownian kernel K = 8 k_B T / (3 mu)
and the analytic constant-kernel number solution N(t) = N0/(1 + K N0 t / 2).
"""
from __future__ import annotations

import math
from typing import Any

BOLTZMANN_J_PER_K = 1.380649e-23  # Exact SI defining constant.
MODEL_ID = "brownian_monodisperse_continuum_v1"
SOURCE = {
    'title': 'The Simplified Aerosol Time Evolution Equations, Appendix A',
    'url': 'https://etd.ohiolink.edu/acprod/odb_etd/ws/send_file/send?accession=osu1122929507&disposition=inline',
    'equations': [
        'A.1',
        'A.2',
        'A.4'
    ],
    'use': 'Continuum Brownian kernel and constant-kernel coagulation formulation.'
}
NASA_ARCHIVE_CONTEXT = [
    {
        'source_path': 'PSI102/SAME EIRD Rev 2.00 02-25-05 HIgh Q (1).pdf',
        'locations': [
            'Section 7.1',
            'Appendix A, equations A-1 through A-7'
        ],
        'use': 'Supplied NASA design report: moment-method context and a DBP growth formulation with Knudsen/slip terms. Those additional terms are not inputs to this v1 scenario.'
    },
    {
        'source_path': 'PSI101/SAMER_Final 0602 2014.pdf',
        'locations': [
            'Table 1',
            'SMPS aging discussion and distributions'
        ],
        'use': 'Supplied NASA report: measured material- and aging-dependent size results. It is validation context, not a size-distribution target automatically joined to this scenario.'
    }
]

DEFAULTS = {
    'initial_number_concentration_m3': 1.0e10,
    'initial_median_diameter_m': 100e-9,
    'initial_geometric_std_dev': 1.0,
    'particle_density_kg_m3': 1000.0,
    'gas_temperature_k': 298.15,
    'gas_viscosity_pa_s': 1.85e-5,
    'residence_time_s': 60.0,
    'sticking_efficiency': 1.0,
    'gas_mean_free_path_m': None,
    'output_points': 61
}


class ScenarioInputError(ValueError):
    """Raised when a scenario input cannot represent this model."""


def _number(payload: dict[str, Any], name: str) -> float:
    value = payload.get(name, DEFAULTS[name])
    if isinstance(value, bool):
        raise ScenarioInputError(f"{name} must be numeric.")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ScenarioInputError(f"{name} must be numeric.") from exc


def _positive(payload: dict[str, Any], name: str, *, allow_zero: bool = False) -> float:
    value = _number(payload, name)
    if value < 0 or (value == 0 and not allow_zero) or not math.isfinite(value):
        comparison = "non-negative" if allow_zero else "positive"
        raise ScenarioInputError(f"{name} must be a finite {comparison} number.")
    return value


def _inputs(payload: dict[str, Any] | None) -> dict[str, float | int]:
    raw = payload or {}
    if not isinstance(raw, dict):
        raise ScenarioInputError("Scenario input must be a JSON object.")
    values: dict[str, float | int] = {
        "initial_number_concentration_m3": _positive(raw, "initial_number_concentration_m3", allow_zero=True),
        "initial_median_diameter_m": _positive(raw, "initial_median_diameter_m"),
        "initial_geometric_std_dev": _positive(raw, "initial_geometric_std_dev"),
        "particle_density_kg_m3": _positive(raw, "particle_density_kg_m3"),
        "gas_temperature_k": _positive(raw, "gas_temperature_k"),
        "gas_viscosity_pa_s": _positive(raw, "gas_viscosity_pa_s"),
        "residence_time_s": _positive(raw, "residence_time_s", allow_zero=True),
        "sticking_efficiency": _positive(raw, "sticking_efficiency", allow_zero=True),
    }
    if values["initial_geometric_std_dev"] < 1:
        raise ScenarioInputError("initial_geometric_std_dev must be greater than or equal to 1.")
    if values["sticking_efficiency"] > 1:
        raise ScenarioInputError("sticking_efficiency must be between 0 and 1.")
    points = raw.get("output_points", DEFAULTS["output_points"])
    if isinstance(points, bool):
        raise ScenarioInputError("output_points must be an integer between 2 and 1001.")
    try:
        points = int(points)
    except (TypeError, ValueError) as exc:
        raise ScenarioInputError("output_points must be an integer between 2 and 1001.") from exc
    if points < 2 or points > 1001:
        raise ScenarioInputError("output_points must be an integer between 2 and 1001.")
    values["output_points"] = points
    mean_free_path = raw.get("gas_mean_free_path_m")
    if mean_free_path not in (None, ""):
        values["gas_mean_free_path_m"] = _positive(raw, "gas_mean_free_path_m")
    return values


def simulate(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run the exact constant-kernel moment scenario and return SI-valued results."""
    p = _inputs(payload)
    n0 = float(p["initial_number_concentration_m3"])
    d0 = float(p["initial_median_diameter_m"])
    density = float(p["particle_density_kg_m3"])
    duration = float(p["residence_time_s"])
    kernel = (float(p["sticking_efficiency"]) * 8 * BOLTZMANN_J_PER_K * float(p["gas_temperature_k"]) / (3 * float(p["gas_viscosity_pa_s"])))
    initial_volume_concentration = n0 * math.pi * d0**3 / 6
    initial_mass_concentration = initial_volume_concentration * density
    rows = []
    for point in range(int(p["output_points"])):
        time_s = duration * point / (int(p["output_points"]) - 1)
        denominator = 1 + 0.5 * kernel * n0 * time_s
        number = n0 / denominator
        diameter = d0 * (n0 / number) ** (1 / 3) if n0 else d0
        volume = number * math.pi * diameter**3 / 6
        mass = volume * density
        rows.append({
            "time_s": time_s,
            "number_concentration_m3": number,
            "equivalent_volume_median_diameter_m": diameter,
            "volume_concentration_m3_per_m3": volume,
            "mass_concentration_kg_m3": mass,
        })
    final = rows[-1]
    volume_relative_error = 0.0 if initial_volume_concentration == 0 else abs(final["volume_concentration_m3_per_m3"] - initial_volume_concentration) / initial_volume_concentration
    mass_relative_error = 0.0 if initial_mass_concentration == 0 else abs(final["mass_concentration_kg_m3"] - initial_mass_concentration) / initial_mass_concentration
    half_time = math.inf if kernel == 0 or n0 == 0 else 2 / (kernel * n0)
    mean_free_path = p.get("gas_mean_free_path_m")
    knudsen_number = (2 * float(mean_free_path) / d0) if mean_free_path is not None else None
    if knudsen_number is None:
        regime = {
            'state': 'not_assessed',
            'knudsen_number': None,
            'message': 'Gas mean free path was not supplied; continuum-regime applicability cannot be assessed.'
        }
    elif knudsen_number <= 0.1:
        regime = {"state": "consistent_with_continuum_assumption", "knudsen_number": knudsen_number, "message": "Kn <= 0.1 is consistent with this v1 continuum-kernel assumption."}
    else:
        regime = {"state": "outside_or_near_continuum_limit", "knudsen_number": knudsen_number, "message": "Kn > 0.1: do not interpret this continuum-only v1 result as transition/free-molecular physics."}
    warnings = [
        'Model scenario only: no NASA PSI run is used as a measured size-distribution target.',
        'Continuum-regime assumption is not verified here; pressure, gas composition, mean free path, particle slip, charge, shape, wall loss, dilution, condensation, fragmentation, and flow mixing are omitted.',
        'initial_geometric_std_dev is displayed for provenance but this v1 monodisperse formulation does not evolve a width parameter.',
        'Do not compare the modeled equivalent diameter directly to detector voltage without a run- and instrument-specific calibration chain.'
    ]
    return {
        "model_id": MODEL_ID,
        "classification": "deterministic model scenario; not NASA measurement",
        "source": SOURCE,
        "nasa_archive_context": NASA_ARCHIVE_CONTEXT,
        "units": {
            'kernel_m3_s': 'm^3/s',
            'number_concentration_m3': 'particles/m^3',
            'diameter_m': 'm',
            'volume_concentration_m3_per_m3': 'm^3 particle/m^3 gas',
            'mass_concentration_kg_m3': 'kg/m^3'
        },
        "inputs": p,
        "assumptions": [
            'Initially monodisperse spherical particles.',
            'Brownian collisions only, continuum regime, and constant gas temperature/viscosity.',
            'Binary coalescence with a user-selected sticking efficiency.',
            'Closed, well-mixed volume with no sources, sinks, wall loss, dilution, or transport.'
        ],
        "kernel": {"brownian_equal_size_m3_s": kernel, "formula": "sticking_efficiency × 8 k_B T / (3 μ)"},
        "regime_assessment": regime,
        "summary": {"initial_number_concentration_m3": n0, "final_number_concentration_m3": final["number_concentration_m3"], "number_fraction_remaining": final["number_concentration_m3"] / n0 if n0 else 1.0, "coagulation_half_time_s": half_time, "initial_mass_concentration_kg_m3": initial_mass_concentration, "final_mass_concentration_kg_m3": final["mass_concentration_kg_m3"]},
        "conservation_check": {"volume_relative_error": volume_relative_error, "mass_relative_error": mass_relative_error, "passes_floating_point_tolerance": volume_relative_error < 1e-12 and mass_relative_error < 1e-12},
        "series": rows,
        "warnings": warnings,
    }
