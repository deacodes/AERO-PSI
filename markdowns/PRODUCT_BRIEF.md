# AERO-PSI product brief

**Name:** AERO-PSI — Aerosol Evidence and Response Observatory.

**Value proposition:** An interactive NASA-data platform that lets users trace a spacecraft-fire smoke conclusion from its source record, compare observed detector signals, explore transparent model assumptions, and see where the archive still has coverage gaps.

**Challenge framing:** AERO-PSI makes difficult NASA microgravity fire and aerosol archives understandable, auditable, and useful for safer future spacecraft experiments.

## Audience and demo

Space Apps judges are the primary audience. Secondary users are combustion researchers, fire-safety engineers, and future mission designers.

1. Select a SAME-R smoke run.
2. Inspect observed detector, particle-count, and flow signals with their source path.
3. Adjust a transparent coagulation scenario without conflating it with observations.
4. Open the Experiment Atlas to identify missing conditions or measurements.
5. Ask the Evidence Copilot for a cited explanation or an explicit unknown.

## MVP navigation

| Page | Outcome |
|---|---|
| Home | Understand the mission, evidence policy, and entry point. |
| Run Explorer | Inspect a selected source-backed smoke run. |
| Smoke Lab | Test a deterministic coagulation scenario with assumptions visible. |
| Optical Response | Compare measured scatter, obscuration, ion, and particle signals. |
| Experiment Atlas | Browse ranked investigations and coverage gaps. |
| Evidence Copilot | Receive a cited explanation or an explicit unknown. |
| Methods & Limits | See data provenance, formulas, assumptions, and limitations. |

## MVP questions

1. What did this NASA run actually measure, and where did that value come from?
2. Under clearly stated assumptions, how would a coagulation scenario evolve relative to observed detector behavior?
3. Which material/condition/measurement combinations are absent or weakly covered in the supplied archive?

## Empty states and scope

- **No imported run:** “This source file is catalogued, but its time series has not been imported.”
- **Ambiguous join:** “This workbook may match more than one experiment-table record. Comparison is disabled until verified.”
- **Unsupported model input:** “This calculation needs a value not supplied by the selected source. Add an assumption to run a labelled scenario.”
- **No evidence:** “The supplied archive does not establish this value or relationship.”
- **Backend unavailable:** “AERO-PSI cannot load local evidence right now. Start the local server and refresh.”

Only features that strengthen the three MVP questions are in scope. Accounts, collaboration, opaque ML predictions, universal particle sizing, and unsupported detector-certification claims are excluded.

