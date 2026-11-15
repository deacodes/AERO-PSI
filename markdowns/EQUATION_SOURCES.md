# AERO-PSI equation-source register

This register prevents the application from silently replacing NASA workbook logic with generic physics. A formula is **not production-approved** merely because it appears in a workbook; it must be traced to its inputs, units, documentation, and a reproducible result.

## Source-derived formulas located

| Intended quantity | Formula as stored | Source location | Status |
|---|---|---|---|
| Hatch-Choate geometric standard deviation | `EXP((LN(BJ/BI))^0.5)` | `DATA/PSI101/Combined SAMER Results 06 02 14.xlsx`, `SAME R Results!BM3:BM…`; also `Drum 8-2012` and `Gnd Verif. 8-2012` | Formula independently recomputed against cached values for rows 3–5; input-column meaning/units still require validation before API use. |
| Hatch-Choate geometric diameter | `BJ / EXP(1.5*(LN(BM))^2)` | Same workbook, `SAME R Results!BN3:BN…` | Formula independently recomputed against cached values for rows 3–5; it depends on prior workbook-derived quantities. |
| Number-to-mass average diameter | `BE / BD * 1000` | Same workbook, `SAME R Results`, column headed `M1/M0 (micro-m)--AMD` | Source formula located; must preserve the source units and input definitions. |
| Diameter of average mass | `10*(BH/BD*6/PI()/BW)^(1/3)` | Same workbook, `SAME R Results`, column headed `Diameter of Average mass (micro-m)` | Source formula located; density/normalization inputs need source review. |
| CPC 100 nm calibration | Piecewise expression in `AY` divided by `AC`: below 100,000 use `AY*(0.000002*AY+1.3816)`; otherwise use `AY*(0.000006*AY+0.1946)+93239` | Same workbook, `SAME R Results`, column headed `CPC 100 nm cal, dilution corrected` | Source calibration located. It must not be applied to a different detector, campaign, or dilution convention without review. |
| Original SAME CPC calibrations | Three separate piecewise calibration formulas for 100 nm, 600 nm, and 1200 nm CPC channels | Same workbook, `SAME1 Flight Tests 8-27-09`, row 3 onward under `2nd order calibrations` | Source calibration located. Keep channel-specific; do not use as a universal conversion. |

## Equation-use rules

1. The current importer preserves source values and reports source-based metrics only. It does **not** apply the formulas above.
2. Any future implementation must cite this workbook, worksheet, formula column, source version checksum, and input units.
3. Recalculate representative rows independently and compare to stored workbook results before release.
4. Keep calibration equations separate by investigation, instrument, particle-size channel, and dilution convention.
5. The Brownian coagulation engine belongs to Step 7. Its governing equation and kernel must be selected from a documented source and validated independently; it must never be implied by the workbook calibration formulas above.

## Coagulation scenario source

| Model | Formula | Source | Scope / release status |
|---|---|---|---|
| `brownian_monodisperse_continuum_v1` | Equal-size continuum Brownian kernel: `K = sticking_efficiency × 8 k_B T / (3 μ)`; total number: `N(t) = N0 / (1 + K N0 t / 2)` | *The Simplified Aerosol Time Evolution Equations*, Appendix A, equations A.1, A.2, A.4 (public link embedded in `aero_psi/coagulation.py`) | Implemented as an assumption-explicit scenario only. It is not a NASA PSI measurement, does not infer particle size from detector voltage, and is not valid without checking its continuum-regime and closed-volume assumptions. |

