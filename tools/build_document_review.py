"""Rebuild the source-linked review ledger from the local extracted corpus.

Review annotations below were written after reading the cited passages. They are
not generated answers. The complete corpus remains separately available, with
unreviewed equations/figures explicitly distinguished from inspected passages.
"""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / 'derived/evidence/review/corpus.json'
DATE = '2026-11-14'


def main():
    corpus = json.loads(CORPUS.read_text())
    docs = {r['source_sha256'][:12]:json.loads((ROOT/r['text_json']).read_text()) for r in corpus}
    notes = []

    def add(key, numbers, title, text, classification='reported_method', visual=False, equations=None, warnings=None):
        doc = docs[key]
        selected = [u for u in doc['units'] if u['number'] in numbers]
        if len(selected) != len(numbers): raise ValueError((key, numbers))
        anchors = [{'kind':u['kind'], 'number':u['number'], 'quote':u['text'].strip()[:180]} for u in selected if u['text'].strip()]
        notes.append({'title':title, 'source_path':doc['source_path'], 'source_sha256':doc['source_sha256'],
            'source_range':', '.join(f"{ {'page':'PDF page','converted_page':'converted PDF page'}.get(a['kind'],a['kind'])} {a['number']}" for a in anchors), 'anchors':anchors,
            'text':text, 'classification':classification,
            'review_state':'Selected passage visually and mathematically checked' if visual else 'Selected source passages reviewed',
            'reviewed_on':DATE, 'equations':equations or [], 'warnings':warnings or []})

    add('941dca3ccf71',[32,33], 'SAME coagulation convention and diffusive wall loss',
        'The engineering report uses dN/dt = -K0 N² and N(t)=N0/(1+N0 K0 t) for a uniform-particle aging estimate. '
        'K0 is a number-decay coefficient. For an identical-particle pair collision kernel beta, total-number balance gives K0=beta/2; do not insert beta in the report formula without checking conventions. '
        'The separate spherical-wall solution assumes constant diffusivity, initially uniform concentration, quiescent gas and a perfectly absorbing wall. '
        'Its dimensionless time is tau=D t/rw². Table 3-2 uses a 100 mm radius and mixes concentration in particles/cc with K0 in mm³/s; convert cc to 1000 mm³. '
        'The printed combined value 0.937 for the 1 µm, 10^6 particles/cc, 60 s row is inconsistent with 0.981×0.999≈0.980. Preserve this source discrepancy; the table is an estimate, not measured flight validation.',
        'design_calculation_and_review', True,
        [r'\frac{dN}{dt}=-K_0N^2,\quad N(t)=\frac{N_0}{1+N_0K_0t}',
         r'\frac{\bar C(t)}{C_0}=\frac{6}{\pi^2}\sum_{n=1}^{\infty}\frac{e^{-n^2\pi^2Dt/r_w^2}}{n^2}'])
    add('941dca3ccf71',[48,49], 'Lognormal equation discrepancy and moment reconstruction',
        'Visual inspection of printed equation (8) on page 48 confirms the numerator in the exponential lacks the square required for a lognormal density. '
        'Equation (12) also places the half power ambiguously outside the exponential. Use the clearly printed square-root form in the later SAME final report page 18, not a literal transcription of this early report. '
        'Corrected mathematical background is n(D)=N/[sqrt(2π) D ln(sigma_g)] exp[-(ln(D/Dg))²/(2 ln²(sigma_g))], D>0, sigma_g>1. '
        'M_j=integral D^j n(D)dD. Mean diameter is M1/M0; diameter of average mass is (M3/M0)^(1/3). M3 is proportional to mass, not equal to mass: spherical constant-density mass concentration is rho*pi*M3/6. '
        'The report proposes iterative calibration for the scattering moment and TEM checks. This is not permission to treat uncalibrated detector voltage as a measured size distribution.',
        'source_discrepancy_and_derived_math', True,
        [r'n(D)=\frac{N}{\sqrt{2\pi}D\ln\sigma_g}\exp\!\left[-\frac{\ln^2(D/D_g)}{2\ln^2\sigma_g}\right]',
         r'M_j=\int_0^\infty D^j n(D)\,dD,\quad c_m=\rho\pi M_3/6'],
        ['Corrected density is an explicitly identified mathematical correction, not the formula as printed in this source.'])
    add('941dca3ccf71',[52,58,59,60,63], 'DBP nucleation and condensation models: applicability and missing inputs',
        'Appendix A describes a modified FDS-v2 nucleation/condensation calculation that explicitly excludes coagulation. '
        'The global DBP growth model couples vapor depletion, aerosol mass and droplet diameter, with Kelvin curvature, temperature-dependent vapor pressure/surface tension, and f(Kn)=(1+Kn)/(1+1.71Kn+1.333Kn²). '
        'Here Kn=2 lambda/Dp and lambda refers to condensing-vapor molecular transport, not automatically the air mean free path used in a Brownian kernel. '
        'Equations require DBP vapor mole fraction, total pressure, temperature history, liquid density, molecular volume and diffusion coefficient. '
        'The report models condensation becoming negligible within 30 cm; Appendix B interprets ground results as mainly coagulation by roughly 20 cm. These are configuration-specific estimates, not universal cutoff lengths. '
        'Property-correlation validity ranges and required transport histories still need verification before implementation. See the separately recovered diameter-growth equation note.',
        'reported_model', equations=[r'f(Kn)=\frac{1+Kn}{1+1.71Kn+1.333Kn^2},\quad Kn=2\lambda/D_p'])
    add('941dca3ccf71',[57,58,59,60], 'DBP diameter-growth equation recovered from the original PDF',
        'Visual review recovers dDp/dt=[4 Vm DAB/(k Dp)]*[Pinf/Tg-Pd/Td]*f(Kn), with Pd=Psat*exp[4 sigma Vm/(k Td Dp)]. '
        'Dp is diameter [m], Vm molecular liquid volume [m³/molecule], DAB vapor diffusivity [m²/s], k Boltzmann constant [J/K], partial pressures [Pa], temperatures [K], and sigma surface tension [N/m]. '
        'The dimensions reduce to m/s. The vapor molecular mean free path is lambda=3DAB/cbar, cbar=sqrt(8 k Tg/(pi m)). '
        'The model assumes droplet/gas thermal equilibrium and a prescribed number concentration. Differentiating aerosol mass as on page 57 also treats N, V and density as fixed in that derivative; changes in those quantities require additional terms. '
        'This is a report model with DBP-specific properties and transport histories, not a new validated coagulation or arbitrary-material condensation solver.',
        'reported_equation_and_review', True,
        [r'\frac{dD_p}{dt}=\frac{4V_mD_{AB}}{kD_p}\left(\frac{P_\infty}{T_g}-\frac{P_d}{T_d}\right)f(Kn)',
         r'P_d=P_{sat}\exp\left(\frac{4\sigma V_m}{kT_dD_p}\right)'])
    add('af91c96d22d9',[17,18,19], 'SAME moment inversion and uncertainty equations',
        'The final report defines DA=M1/M0 and DM=(M3/M0)^(1/3), Dg=sqrt(DA³/DM), and sigma_g=exp(sqrt(ln(DM/DA))). '
        'Equivalent Dg=M0^(-4/3) M1^(3/2) M3^(-1/6). Positive moments and DM>=DA are necessary; inconsistent measured moments must be rejected or investigated, not forced into a distribution. '
        'These reconstruct an assumed lognormal distribution from calibrated moments; they are not direct bin-resolved size measurements. '
        'For independent moment errors, relative variance of Dg is (16/9)u_r(M0)²+(9/4)u_r(M1)²+(1/36)u_r(M3)². '
        'For sigma_g it is [u_r(M0)²+2.25u_r(M1)²+0.25u_r(M3)²]/[9 ln²(sigma_g)]. '
        'Shared dilution/calibration errors require covariance terms; the sigma_g approximation becomes singular near a monodisperse distribution. '
        'DustTrak red-light scattering at 90 degrees is described as approximately third-moment sensitive over 0.2–2 µm, with calibration corrections; do not confuse it with the ISS detector geometry.',
        'reported_equation_and_review', True,
        [r'D_g=M_0^{-4/3}M_1^{3/2}M_3^{-1/6}',r'\sigma_g=\exp\sqrt{\ln\left(M_0^{2/3}M_3^{1/3}/M_1\right)}',
         r'u_r^2(D_g)=\frac{16}{9}u_r^2(M_0)+\frac94u_r^2(M_1)+\frac1{36}u_r^2(M_3)'])
    add('af91c96d22d9',[23,24,28], 'SAME calibration, material coverage and contaminated TEM grids',
        'The final report describes per-smoke-source DustTrak calibration against a tapered-element oscillating microbalance and use of estimated material densities. '
        'The calibration is conditional on size distribution not changing significantly. Optical refractive index, agglomeration and lognormal departures remain uncertainties. '
        'SAME tested silicone, cellulose/lampwick, Teflon, Kapton and DBP in September/October 2007. '
        'Lampwick and silicone have a substantial large-particle mass tail despite smaller count means; Kapton and Teflon are narrower in these reported tests. '
        'Recovered TEM grids were contaminated. Do not call the flight TEM collection clean independent validation, or apply one calibration to every material and aging condition.', 'reported_measurement_and_limitation')
    add('65381e2715eb',[2,3], 'SAME-R differs from SAME: materials, instruments and run counts',
        'SAME-R added Pyrell in place of DBP, higher-temperature and no-flow conditions, and M-pass in place of one Commercial Diagnostic Enclosure. '
        'The report describes 2010 flight tests and post-flight dilution-flow, TEM and ground SMPS studies. '
        'Its abstract gives 66 successful test points; page 3 describes 67 runs including two reused-sample runs and 109 appendix entries when secondary aging is counted separately. '
        'These counts describe different entities. Preserve run identifiers, aging suffixes and sample reuse rather than treating them as 109 independent experiments. '
        'PSI101 is the re-flight in this archive; PSI102 is the original SAME. The presence of ground SMPS plots in a report does not establish an available machine-readable flight PSD.', 'reported_experiment_context')
    add('65381e2715eb',[11,19,20,22], 'Lognormal and SMPS validation is material- and range-dependent',
        'The report compares ground SMPS distributions, lognormal fits and TEM. It excludes non-spherical Pyrell and Teflon from its spherical-aerosol SMPS moment-method comparison. '
        'SMPS upper range changes from about 660 nm at 10:1 sheath/sample flow to 1000 nm at 5:1; a conservative 700 nm cutoff is also assessed. '
        'One high-temperature silicone example captures only about 40% of fitted volume to 1000 nm and 20% to 700 nm, while the displayed Kapton case captures 98–100% of its distributions. '
        'Higher-moment silicone diameters disagree more strongly with lognormal conversions; some upper bins have fewer than ten particles. '
        'A good number-distribution fit does not guarantee accurate mass moments or universal validation for all materials.', 'reported_measurement_and_limitation')
    add('65381e2715eb',[26], 'SAME-R dilution correction coefficients are instrument-specific',
        'Reported flight dynamic-diluter sample flow: actual flow [ccm]=0.9474*command [ccm]-1.2395. '
        'Engineering diluter calibration was unavailable; applying the flight correlation to it is an assumption stated in the report. '
        'Reported P-Trak total flows average 703.96 ccm engineering and 705.64 ccm flight. '
        'The reported nitrogen-orifice relation is N2 flow [SLPM]=0.308*(regulated N2 pressure)^0.5283, but the pressure convention/units are not identified in this excerpt. '
        'The dilution orifice did not maintain critical flow, whereas the total-flow orifice did. Do not silently use this power law as an SI-unit calibration. '
        'Flight DustTrak B total flow is reported as 1.69076 LPM. Match hardware, pressures and engineering logs before using these coefficients.', 'reported_calibration',
        warnings=['Pressure units for the empirical power law require confirmation from its calibration context.'])
    add('65381e2715eb',[27,28,29,30], 'Heater temperature and truncated aerosol moments',
        'The heater analysis separates wire touching the sample from exposed lead wire. Total resistance is not a direct sample temperature. '
        'It uses measured resistance, temperature-dependent resistivity, current, wire dimensions and a bounded effective heat-transfer parameter 0.5<mu<1, with steady-state and lumped-transfer assumptions. '
        'A separate derivation calculates the fraction of a lognormal moment captured between instrument size limits using error functions. '
        'A useful independently derived form is F_j=Phi((ln(Du/Dg)-j*s²)/s)-Phi((ln(Dl/Dg)-j*s²)/s), s=ln(sigma_g). '
        'This is a conditional lognormal correction, not measured missing particles. Extracted equations on pages 28–30 have missing glyphs and must not be copied as executable code.', 'reported_method_and_derived_math',
        equations=[r'F_j=\Phi\!\left(\frac{\ln(D_u/D_g)-j s^2}{s}\right)-\Phi\!\left(\frac{\ln(D_l/D_g)-j s^2}{s}\right),\quad s=\ln\sigma_g'])
    add('65381e2715eb',[29,30], 'Instrument-window moment fraction: equation images checked',
        'The PDF equations give eta(D)=[ln(D/dg)-p ln²(sigma_g)]/[sqrt(2) ln(sigma_g)], and measured fraction M_p,rel=0.5[erf(eta(Du))-erf(eta(Dl))]. '
        'This is equivalent to the standard-normal CDF expression in the review derivation. The appendix normalizes its total moment without N: Mp=dg^p exp[0.5(p ln(sigma_g))²]. '
        'Multiply by total number concentration to recover dimensional concentration moments. Number fractions (p=0), area-weighted fractions (p=2) and volume-weighted fractions (p=3) generally differ. '
        'Requires positive ordered size limits and sigma_g>1, with a separate degenerate treatment at sigma_g=1. A fitted-tail estimate remains assumption-dependent.',
        'reported_equation_and_review', True,
        [r'\eta(D)=\frac{\ln(D/d_g)-p\ln^2\sigma_g}{\sqrt2\ln\sigma_g}',
         r'M_{p,rel}=\tfrac12[\operatorname{erf}(\eta(D_u))-\operatorname{erf}(\eta(D_l))]'])
    add('0e8480e701f4',[4,7,8,27,28,29], 'SAME presentation: detector moments, morphology and size-sensitive detection',
        'The presentation contrasts an ionization STS detector with a two-pass infrared ISS detector using 30-degree forward scattering; these are distinct from the DustTrak measurement instrument. '
        'It reports roughly 100–600 nm particle sizes in its study context, growth with aging and decreasing airflow, and distinct material morphologies. '
        'About 40% of lampwick/silicone aerosol mass is reported above 1 µm aerodynamic diameter, whereas Kapton/Teflon mass is mostly below that threshold. '
        'The conclusions motivate size-aware or multiple-moment detection and nuisance discrimination. They do not validate an arbitrary multi-angle instrument or the platform solver. '
        'Count mean, count median, aerodynamic size and volume-equivalent diameter must remain distinct.', 'reported_findings')
    add('0e8480e701f4',[25,26], 'Detector-design slides contain a number-concentration ambiguity',
        'Slide 25 visibly labels an illustrative alarm level of 2 mg/m³, 500 nm count-median diameter, sigma_g=1.3 and 22×10^6 particles/cc. '
        'These are illustrative normalized detector comparisons, not a measured run. The particle-number label is dimensionally suspect for ordinary-density spherical particles. '
        'For example, assuming rho=1000 kg/m³ explicitly, the stated mass and lognormal size imply approximately 2.24×10^4 particles/cm³, not 22×10^6. '
        'Density is not specified on the slide, so this is a consistency check under a stated assumption, not a replacement measured value. Do not import the printed count as a default.',
        'source_discrepancy_and_assumption_check', True)
    add('67ede025a6cf',[7,8], 'Legacy Word paper recovered: CSD results and proposed SAME moment method',
        'The converted Word paper distinguishes CSD smoke tests from the then-proposed SAME experiment. '
        'Liquid aerosols evaporated from TEM grids before examination; solid primary-particle and aggregate dimensions are reported separately. '
        'The detection comparison used a 20% operating-range criterion and an ISS detector more sensitive than the ISS standard, not a flight qualification threshold. '
        'Moment equations are embedded images and were absent from extracted text. Visual inspection of converted page 8 found the same missing-square lognormal formula as EIRD page 48 and ambiguous sigma_g exponent placement. '
        'Use the later final report for the explicit corrected square-root expression; do not treat all text extraction as complete mathematical extraction.',
        'reported_method_and_source_discrepancy', True)
    add('69f32647792f',[13,14,15,18,19,20,21,23,25], 'BASS-II FAQ: timing, airflow, oxygen and radiometer caveats',
        'Use the spreadsheet date: the video date display is one day later because leap year was not handled. GMT is day of year. '
        'Lettered test variants may reuse the same sample. Flow restrictor setting 0 is highest flow; 2 is lowest. Fan-voltage display is voltage×10. '
        'The airflow display responds slowly, about one minute, so it represents steady flow better than transients. '
        'Radiometer gain is uncalibrated and gives relative intensity, not absolute heat flux. FAQ reports displayed data at 5 Hz, while engineering requirements specify 4 Hz; preserve this discrepancy. '
        'The oxygen sensor was out of calibration; daily ISS MCA readings supplied a constant offset. CO OR indicates overrange above 1000 ppm, not a numerical sample.', 'reported_data_handling')
    add('08ab1b85ba60',[1,2,3], 'BASS-II engineering presentation: requirements, not measured coverage',
        'The presentation specifies GN2 supply up to 500 SCCM, reused SPICE/BASS hardware, 4 Hz acquisition and ±10% measurement accuracy previously met by SPICE. '
        'It calls for nearby SAMS acceleration measurements and avoidance of planned thruster/docking events. '
        'These are engineering requirements and heritage specifications; they do not prove this archive contains synchronized acceleration, calibrated radiometry, or successful measurements for every sample.', 'design_requirement')
    add('d00a763d6071',[1,2,3], 'BASS-II science requirements and success criteria',
        'The requirements describe five PI sample sets, additional Nomex, GN2 atmosphere vitiation, video-overlay signals and 4 Hz heritage acquisition. '
        'Minimum/complete success criteria specify desired numbers of tests and images. These targets must not be counted as actual completed runs. '
        'Use the summary report and run records for achieved coverage; the FAQ supplies post-test data caveats.', 'design_requirement')
    add('5ffa911fd9b6',[9,35,36,71,97,109], 'BASS-II results: flow-dependent extinction, geometry and model limitations',
        'The summary report combines distinct PI studies, not one universal flame-spread model. Thin-PMMA scaling relates radiative extinction velocity to surface radiative loss divided by gas sensible-heat transport. '
        'Table 2.1 at 1 atm reports extinction velocities at 21% O2: experiment 10±5 mm/s, computation 15, theory 7.5; at 16% O2: experiment 30±5, computation 35, theory 10. '
        'Do not merge theoretical, simulated and observed values into one training target. The thick-fuel study explicitly says its model overpredicts spread rates and needs kinetics/material-property improvements. '
        'The fabric study reports 1–5 cm/s quenching velocities for its configurations. Rod-flame quenching involves oxygen transport, three-dimensional effects and oscillations. '
        'These studies support conditional flow/oxygen/geometry explanations, not a universal extinction threshold or aerosol collision kernel.', 'reported_results_and_model_limits')
    add('5ffa911fd9b6',[14,15], 'BASS-II mixed-volume and oxygen-depletion assumptions',
        'The atmosphere-dilution model assumes constant pressure, temperature and volume, with well-mixed outflow and nitrogen inflow balanced by leakage. '
        'Its mixing time must be much shorter than V/Q; this is not guaranteed merely by calling a vessel well mixed. '
        'The PMMA repeat-unit complete-combustion balance is C5H8O2+6 O2 ->5 CO2+4 H2O. Thus the ideal O2 consumption to CO2 production molar ratio is 6:5. '
        'CO was also observed and an overrange case had no quantitative CO value. Oxygen-depletion fuel estimates need incomplete-combustion, leakage and gas-inventory assumptions; do not automatically convert oxygen percentage differences into mass loss.',
        'reported_equation_and_review', True, [r'\mathrm{C_5H_8O_2}+6\mathrm{O_2}\rightarrow5\mathrm{CO_2}+4\mathrm{H_2O}'])
    add('5ffa911fd9b6',[35,36,90,92], 'BASS-II heat-transfer equations and thermal-property naming discrepancy',
        'For thermally thin opposed-flow PMMA, the scaling is Vf,thermal~lambda_g*(Tf-Tv)/[rho_s*c_s*tau*(Tv-Tinf)], where tau is half-thickness. '
        'The derived critical flow is Vg,cr=epsilon*sigma*(Tv^4-Tinf^4)/[c_g*rho_g*(Tf-Tv)]. It is a scaling relation under the stated thermal/radiative assumptions, not a universal measured threshold. '
        'A different rod-tip analysis uses Nu=1.32 Re^0.5 Pr^0.4 and convective heat flux Nu*lambda*(Tcrit-Ts)/s. '
        'Page 90 calls lambda thermal diffusivity, but dimensional consistency of the printed heat-flux equation requires thermal conductivity [W/(m K)], not diffusivity [m²/s]. The same terminology concern affects lambda_s in the page 92 conductive-loss term. '
        'Retain this discrepancy and verify property definitions before numerical reuse. Solid regression rates and hemispherical mass flux differ by an area factor; these are not aerosol source rates without a measured smoke yield.',
        'reported_equation_and_source_discrepancy', True,
        [r'V_{g,cr}=\frac{\epsilon\sigma(T_v^4-T_\infty^4)}{c_g\rho_g(T_f-T_v)}',r'Nu=1.32Re^{1/2}Pr^{0.4}'])
    add('768a7c289af3',[3], 'BASS research hypothesis and suppression context',
        'BASS investigates flame spread and suppression under reduced buoyancy and low-speed circulation. '
        'The claim that adequately ventilated microgravity materials may burn as well or better than at 1g is a research hypothesis here. '
        'The document explains why extinguisher application and entrainment can differ in microgravity; it is not an operational firefighting prescription or a measured aerosol PSD.', 'design_rationale')
    add('e38622cce587',[1], 'BASS archive layout is a directory guide',
        'The layout document separates BASS_2012 and BASS_2013; images and videos are organized by dates. '
        'It describes 21 image galleries for 2012, and 12 audiovisual collections plus 15 image galleries for 2013 on PSI. '
        'These are website inventory descriptions, not proof all corresponding media were downloaded locally, and contain no new coagulation equations.', 'archive_navigation')
    add('434e9b2cade6',[17,152,165,169], 'BASS fabric study: measured spread versus extrapolated extinction',
        'The paper studies cotton–fiberglass fabric in concurrent and opposed flow in the ISS glovebox. '
        'Concurrent spread at low flow was approximately linear with flow for the tested widths; opposed-flow spread peaked around 10–15 cm/s. '
        'Concurrent-flow extinction below about 1 cm/s was observed. In the described opposed-flow attempt the flame reached the end of the fuel before quenching; its finite low-flow extinction boundary was inferred, not directly measured. '
        'Steady spread is obtained from flame-position slopes; short samples, direction, width and response time constrain comparability.', 'reported_measurement_and_inference')
    add('0af43477a04b',[2,3,4,5], 'FLEX planned extinction matrix, timing and LOI relation',
        'The test plan describes a conceptual droplet flammability map, not a measured boundary. LOI=0.209*(1-MEC) assumes suppressant dilution of standard air; it is not universal for arbitrary initial oxygen mixtures. '
        'Ambient temperature/pressure measurement and GMT synchronization specifications are requirements (10 Hz minimum, ±0.5 °C, ±0.01 atm, ±0.03 s). '
        'The plan explicitly states its matrices are an engineering envelope rather than the final executed matrix. '
        'Heptane and methanol fuels, suppressant fractions, droplet size, pressure and imposed/drift flows are relevant experimental variables; these are combustion droplets, not automatically smoke aerosol bins.', 'design_requirement_and_equation',
        equations=[r'LOI=0.209(1-MEC)'])
    add('1120819bb8f5',[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16], 'FLEX data organization and calibration-record distinction',
        'The organization document describes text data and images/videos organized by fuel, GMT and atmosphere. '
        'Listed calibration records must remain distinct from heptane and methanol fuel experiments. '
        'A reference to PSI media or data does not establish that every file is in the local archive. Read timing logs together with their instrument calibration and atmosphere metadata.', 'archive_navigation')
    add('393f3ebc6662',[3,55,61,63], 'ACME actual instrumentation and geometry',
        'The engineering report describes six gas-fueled laminar diffusion-flame investigations in the CIR, distinct from FLEX liquid-droplet experiments. '
        'The low-light ultraviolet camera was used only for s-Flame. Radiometer fields of view depend on array/burner configuration; the CFI-G array is not covered by the shown FOV diagrams. '
        'Thermocouple rakes have near/far variants; actual thermocouple types differ from original intent and bead size was not measured. '
        'Use hardware-specific geometry, response and calibration rather than interpreting every camera/radiometer channel as interchangeable optical scattering data.', 'reported_instrumentation')
    add('1d64b7f42f07',[18,25,26,27], 'Flame Design: reported extinction results and unavailable acceleration archive',
        'The final report describes normal and inverse ethylene spherical flames at atmospheric pressure and reports a critical extinction temperature of 1130 K for that study. '
        'Reported extinction fluxes are fuel-based 0.2 g/(m² s) for normal flames and oxygen-based 0.68 g/(m² s) for inverse flames. These are different reactants and are not generic smoke-generation rates. '
        'Some flames showed steady-state behaviour for up to 870 s; numerical infinite-domain times approaching 100000 s are model results, not flight durations. '
        'SAMS acceleration is explicitly archived separately through PIMS, not with ACME PSI files. Diagnostic/calibration limitations and non-spherical burner flow are discussed. '
        'CH4/CO2 and desired coflow conditions in earlier requirements were not all flown.', 'reported_results_and_scope')
    add('f6cce7cc08ca',[15,16,23,24], 'CFI-G cool flames: restricted conditions and lost data',
        'The final report reports spherical gas-fueled cool flames only for normal n-butane at 2 bar and ambient oxygen mole fraction 0.39 in its investigated conditions. '
        'A separate pool-heptane/stagnation-flow study is ground research; its temperatures must not be relabelled as ISS observations. '
        'Difficult-to-see cool flames, interrupted tests, lost primary camera data on a failed-drive test day, low-range mass-flow-controller errors and asymmetric high-flow flames affect interpretation. '
        'A missing cool-flame image is not proof no reaction occurred. Gaseous combustion kinetics are separate from aerosol coagulation.', 'reported_results_and_limitations')
    add('f7f9e4947660',[1,2,34,35], 'ACME integrated science requirements and optical calibration',
        'This 2013 requirements document covers five planned investigations. It specifies imaging filters and characterization requirements, including CH*/background bands, UV imaging and temperature diagnostics. '
        'Required field of view, transmission tolerance, sampling and calibration do not establish achieved performance in a supplied run. '
        'Requirement applicability changes by investigation. Compare the later engineering and final reports before interpreting optical signals or counting instruments.', 'design_requirement')
    add('32afd4c0d3c9',[1,3], 'ACME operations requirements are command plans',
        'The 2011 operations document derives from the integrated requirements and covers four planned experiments, command functions, flow/electric-field ramps and example sequences. '
        'It explicitly distinguishes italic commentary from requirements. Extracted plain text loses that typography; retain the original for requirement interpretation. '
        'Example control sequences are not observed time series or proof a particular flow/voltage sequence was executed.', 'design_requirement')
    add('e783fc0da3d3',[8,17,27,38], 'Flame Design equations describe flame structure and transport',
        'The requirements report defines Zst=[1+YF*WO*nuO/(YO*WF*nuF)]^(-1), using stream mass fractions, molecular weights and stoichiometric coefficients. '
        'It describes inert exchange at fixed adiabatic temperature, reacting-flow conservation, participating-gas radiation and gravity-disturbance constraints. '
        'Appendix mass flux is m_dot/(4*pi*rf²); this is a spherical flame-front flux, not particle mass concentration. '
        'Its example detailed chemistry/radiation solver and desired end products are not implemented by the platform coagulation solver. '
        'Gas reaction rates, soot formation, Brownian particle collisions and detector scattering require separate models and evidence.', 'reported_model_and_design',
        equations=[r'Z_{st}=\left(1+\frac{Y_F W_O\nu_O}{Y_O W_F\nu_F}\right)^{-1}',r'F=\dot m/(4\pi r_f^2)'])
    add('efb9ac32a82a',[1,2,3], 'Flame Design publication list is bibliographic evidence',
        'This file lists papers, presentations and theses with dates and DOI links. It is useful for finding primary research, but a title or link is not the contents of that publication. '
        'Do not report an equation or numerical result from a listed paper unless its actual text has been consulted.', 'bibliography')
    add('81cea0977ef2',[1,2], 'Flame Design taskbook reports mix annual progress and objectives',
        'The taskbook compilation contains administrative history, proposed objectives, yearly progress and publication lists. '
        'The 2024 entry reports processing normal/inverse flame tests and simulations, including chemistry and radiation-boundary work. '
        'Repeated annual text is not independent replication. Funding dates, proposed conditions and numerical studies must remain distinct from measured flight run conditions.', 'progress_report')
    add('01f812143679',[1], 'Saffire operations occurred on uncrewed Cygnus after undocking',
        'Saffire I–III were carried in Cygnus cargo vehicles and run after departure from ISS. '
        'The operations description distinguishes large I/III samples from the smaller Saffire-II specimens and explains autonomous operations/downlink before destructive reentry. '
        'The generic ISS platform metadata must not be used to imply that these large fires burned inside the crewed station.', 'reported_experiment_context')
    add('c775153b5c68',[1], 'Saffire raw-image offset must follow the exact directory stage',
        'The image-nomenclature PDF says Raw_CamOriginal has an 8-byte offset and Raw_DistroMaster has already been corrected. '
        'This conflicts with the DoD table description calling Raw_DistroMaster offset-bearing. Do not apply an unconditional second 8-byte removal. '
        'Mapped images have geometric distortion correction; JPEG2PNG avoids another lossy save but does not recover original image information. '
        'Preserve acquisition, demosaic, mapping, exposure and gain provenance before extracting flame geometry.', 'reported_data_handling_and_conflict')
    add('49c939337fa0',[3,5], 'Saffire material, image mapping and embedded diagnostics table',
        'The DoD describes SIBAL as 75% cotton and 25% fiberglass by mass, with stated I/III airflow values of 20/30 cm/s. '
        'F1/F2 denote pre/post-flow records; C1/C2 distinguish cameras. These labels are not fuel species or aerosol size bins. '
        'Visual review of Table 2 on converted PDF page 2 recovers an image-only diagnostics table: thermocouples, radiometers, O2/CO2 sensors, pressure sensors, anemometers, cameras and smoke-wire flow visualization. '
        'Sensor descriptions do not prove availability or calibration of every channel locally. The Raw_DistroMaster offset description conflicts with the separate image-nomenclature PDF.', 'archive_navigation_and_instrumentation')
    add('40b8b7f20b35',[1,2,4,5], 'SoFIE-GEL PMMA sphere growth and oxygen-depletion assumptions',
        'The 2026 paper studies 4 cm PMMA spheres using projected flame-tip length, angle and radius, assuming approximate axisymmetry. '
        'Fuel burn rate is inferred from oxygen depletion assuming complete combustion; pressure transients also enter when pressure changes. '
        'A representative fixed-flow test at 4.7 cm/s reaches a limiting flame length and then retreats as oxygen declines; this is not a general constant-flow law. '
        'Figure 5 explicitly marks interpolated missing-image segments and oscillation-trough data. Treat these differently from directly tracked continuous observations. '
        'This is flame geometry/combustion evidence, not a particle-size distribution.', 'reported_measurement_and_assumptions')
    add('748922dd194b',[2], 'SoFIE taskbook: experimental period and conditional findings',
        'The 2026 taskbook reports GEL operations from January 2023 to March 2024, using PMMA spheres to study flow, oxygen, pressure and internal heating. '
        'It describes flammability maps, quenching, preheating and limiting flame length. It attributes lower inferred sphere burning rates than equivalent ground tests to flow/flame separation. '
        'This is a project summary, not raw measurements or universal behaviour for all spacecraft materials.', 'progress_report')
    add('978dc0948910',[7,8,9,14,16], 'NASA flammability update: scale, partial gravity and dated scope',
        'The 2021 presentation separates executed Saffire IV/V conditions from future plans. '
        'It cautions that bubbling polymers may not extinguish quickly in quiescent conditions and that sample/duct geometry changes spread and pyrolysis length. '
        'Partial-gravity minimum oxygen concentration depends on material; stopping ventilation does not remove natural convection on the Moon or Mars. '
        'Lunar smoke-transport/detector placement is posed as a modeling need, not an established result. Dates and planned schedules are historical, not current commitments.', 'reported_context_and_limitations')
    add('dc42805d92fb',[2,4,5,6,7,8,9,14,21], 'SoFIE project presentation: separate investigations and a size discrepancy',
        'The presentation outlines MIST, SMuRF, NCA, RTDFS and GEL, each with different geometry, objectives and boundary conditions. '
        'It is mostly facility/design context and anticipated operations, not a uniform measured dataset. '
        'Page 14 text labels the GEL sphere as 40 cm diameter, whereas the later GEL paper reports 4 cm; preserve this discrepancy and use run-specific/later experimental documentation before assigning sample dimensions. '
        'Descriptions of cameras, fans, heaters and gas sampling do not imply aerosol scattering measurements.', 'design_context_and_source_discrepancy')

    # Text-file reviews: metadata remains contextual; placeholder rows are not data.
    for record in corpus:
        if record['duplicate_of'] or record['format'] != '.txt': continue
        doc=docs[record['source_sha256'][:12]]
        source=ROOT/'DATA'/record['source_path']
        if source.name == 'i_Investigation.txt':
            lines=source.read_text().splitlines()
            line=next((i+1 for i,t in enumerate(lines) if t.startswith('Study Title\t')),1)
            title=lines[line-1].partition('\t')[2]
            note={'title':f'{title}: ISA metadata scope','source_path':record['source_path'],'source_sha256':record['source_sha256'],
                'source_range':f'line {line}', 'anchors':[{'kind':'line','number':line,'quote':lines[line-1]}],
                'text':f'This ISA metadata identifies {title}. Objective, hypothesis and approach fields describe investigation context; they are not measured rows. Publication and hardware URLs are bibliographic pointers, not websites consulted by SI. Directory PSI identifiers differ in some export names; retain the actual path and Study Title. Source-specific instrument, location and calibration claims should be checked against the associated reports.',
                'classification':'investigation_metadata','review_state':'Metadata structure reviewed','reviewed_on':DATE,'equations':[],'warnings':[]}
            if record['source_path'].startswith('SAFFIRE/'):
                note['text']+=' The ISS platform label needs the Operations document qualification: burning occurred aboard uncrewed Cygnus after undocking.'
            notes.append(note)
        elif source.name.startswith('s_'):
            notes.append({'title':'ISA sample files contain placeholder text, not scientific samples',
                'source_path':record['source_path'],'source_sha256':record['source_sha256'],'source_range':'line 1',
                'anchors':[{'kind':'line','number':1,'quote':source.read_text().splitlines()[0]}],
                'text':'All eight identical s_PSI sample text exports contain literal escaped separators and a Do not use this placeholder. They contain no measured sample table. Preserve them as archive artifacts and exclude them from scientific sample counts.',
                'classification':'non_scientific_placeholder','review_state':'Content inspected','reviewed_on':DATE,'equations':[],'warnings':[]})
        else:
            notes.append({'title':'FLEX 20CAL08 timing/radiometer log needs calibration and clock alignment',
                'source_path':record['source_path'],'source_sha256':record['source_sha256'],'source_range':'lines 1–206',
                'anchors':[{'kind':'line','number':1,'quote':source.read_text().splitlines()[0]}],
                'text':'20CAL08 is a calibration-labelled log with setup/burn events, two timestamps, narrow/wide radiometer means and standard deviations, and archived image counters. Rows 94–95 repeat both timestamps and radiometer values while image counters advance; do not treat these as two independent radiation samples or drop the distinct image metadata. Programmed igniter and burn-to-completion durations are not measured extinction times. Numerical radiometer rows do not state physical units. Wide-channel negative values must be retained; do not silently turn them into absolute irradiance or particle concentrations. Check clock offsets and counters before aligning with video. This is potentially useful time-series data, not a measured aerosol PSD.',
                'classification':'raw_log_data_review','review_state':'Log structure and numeric rows audited','reviewed_on':DATE,'equations':[],'warnings':[]})

    (ROOT/'mappings/scientific_review.json').write_text(json.dumps({'reviewed_on':DATE,'scope':'Source-linked selected scientific passages; not exhaustive figure verification or peer review.','notes':notes},ensure_ascii=False,indent=2))

    # Every extracted unit is mapped. Flags are candidates, never equation approval.
    review=[]
    for record in corpus:
        doc=docs[record['source_sha256'][:12]]
        covered=sorted({a['number'] for n in notes if n['source_sha256']==record['source_sha256'] for a in n['anchors']})
        topics={}
        for topic,pattern in {'coagulation':'coagulat|Brownian|Smoluchowski','scattering':'scatter|Mie|Rayleigh|refractive',
            'combustion':'flame|pyrolys|extinct|burning','calibration':'calibrat|uncertaint|accuracy',
            'transport':'diffusi|settling|ventilat|gravity|Knudsen','equation_candidate':r'equation|\beq\.|=|∫|∂|σ|λ'}.items():
            topics[topic]=[u['number'] for u in doc['units'] if re.search(pattern,u['text'],re.I)]
        urls=sorted(set(re.findall(r'https?://[^\s<>"\)]+','\n'.join(u['text'] for u in doc['units']))))
        review.append({**record,'reviewed_passage_units':covered,'topic_unit_map':topics,
            'bibliographic_urls_not_necessarily_consulted':urls,
            'review_state':'Text extracted; selected scientific passages reviewed',
            'limitations':['Figures and image-only equations are not all digitized or visually verified.','Requirements, reported results, and local measurements are different evidence classes.']})
    (ROOT/'derived/evidence/review/coverage.json').write_text(json.dumps({'date':DATE,'files':review,'notes':len(notes),
        'source_files':len(corpus),'distinct_sources':len({r['source_sha256'] for r in corpus}),
        'review_claim':'All eligible files inventoried and text extracted. Selected scientific passages reviewed; no blanket claim of complete equation/figure verification.'},ensure_ascii=False,indent=2))
    print(json.dumps({'files':len(review),'review_notes':len(notes),'distinct_sources_with_notes':len({n['source_sha256'] for n in notes})}))


if __name__ == '__main__': main()
