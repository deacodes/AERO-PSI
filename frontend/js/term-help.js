/* Plain-language help preserves source headers and distinguishes notation from verified definitions. */
const TermHelp=(()=>{
 const terms={
 'source row':'Row number in the source table, so you can trace a value back to its original record.',
 'flame type':'The flame configuration recorded for this test. Category codes belong to the source investigation.',
 'day':'The day identifier recorded by the investigation. Do not assume this is a calendar date without checking the source.',
 'fuel':'The fuel or fuel mixture recorded for the test.',
 'test':'The investigation’s test identifier. It is a label, not a measurement.',
 'xfuel':'Conventionally the mole fraction of fuel in a mixture. Confirm the mixture and whether values are fractions or percentages in the source documentation.',
 'mfuel (mg/s)':'Fuel mass-flow rate: milligrams of fuel supplied per second.',
 'mn2 (mg/s)':'Nitrogen mass-flow rate: milligrams of nitrogen supplied per second.',
 'mtot (mg/s)':'Total mass-flow rate in milligrams per second. Check the source for which streams are included.',
 'xo2 (init)':'Initial oxygen composition. X conventionally denotes mole fraction; confirm whether this table uses a fraction or percentage.',
 'xo2 (final)':'Final oxygen composition. Confirm the reporting basis and the time defining “final” in the source.',
 'pinit (atm)':'Initial pressure, expressed in atmospheres (atm).',
 'pfinal (atm)':'Final pressure, expressed in atmospheres (atm).',
 'pmean (atm)':'Mean pressure in atmospheres. The source defines the averaging interval.',
 'mean zst':'Conventionally the mean stoichiometric mixture fraction: the mixture proportion at which fuel and oxidizer are in the ratio needed for complete reaction. Confirm this table’s definition and averaging method.',
 'tad (k)':'Conventionally the adiabatic flame temperature in kelvin: an ideal temperature calculated without heat loss. It is not necessarily a measured flame temperature.',
 'tad':'Conventionally adiabatic flame temperature: an ideal calculation without heat loss. Confirm units and calculation assumptions in the source.',
 'geometric sd':'Geometric standard deviation describes the spread of a lognormal size distribution. A value near 1 means particles are close in size.',
 'median diameter':'The middle diameter of the assumed particle-size distribution. It is an input assumption unless supported by a measurement.',
 'initial number':'Initial particle number concentration: how many particles are present per unit gas volume.',
 'residence time':'How long the scenario is simulated. In an experiment, residence time describes how long material remains in a region.',
 'sticking efficiency':'Fraction of modeled collisions assumed to result in particles joining. This is not automatically known from the material name.',
 'section count':'Number of numerical size bins. More bins can improve resolution but take longer; compare solutions to check convergence.',
 'brownian regime':'Choice of collision physics for random thermal particle motion. Applicability depends on particle size and the gas mean free path.',
 'dynamic viscosity':'The gas’s resistance to flow. This affects particle drag and Brownian diffusion.',
 'particle density':'Mass per unit particle volume. The spherical-particle model uses this to convert volume to mass.',
 'wall loss':'Removal of suspended particles at surrounding surfaces, represented by the selected model assumption.',
 'dilution':'Reduction in particle concentration caused by mixing with cleaner gas or exchanging gas.',
 'shear rate':'How quickly fluid velocity changes across distance. Shear can bring particles into collision.',
 'settling height':'Vertical distance used to estimate removal by gravitational settling.',
 'refractive index n':'Real part of the refractive index, describing how light propagates through the particle relative to the reference medium. It depends on wavelength.',
 'absorption k':'Imaginary part of the refractive index, representing light absorption under the model’s sign convention. It depends on wavelength.',
 'vacuum wavelength (nm)':'Light wavelength in vacuum, in nanometres. Scattering depends on particle size relative to this wavelength.',
 'possible sentinel':'A value that may be a placeholder code rather than a measurement. Check the source before treating it as numerical data.',
 'selected row & provenance':'The selected values together with their source identity, so the evidence can be traced and checked.'
 };
 const tip=document.createElement('div');tip.id='scientificTermTip';tip.className='term-tooltip';tip.role='tooltip';tip.hidden=true;document.body.append(tip);let active=null;
 const key=s=>s.trim().toLowerCase().replace(/\s+/g,' ');
 function textFor(label,table=false){const k=key(label);return terms[k]||Object.entries(terms).find(([t])=>k.startsWith(t+' '))?.[1]||null;}
 function hide(){if(active)active.removeAttribute('aria-describedby');active=null;tip.hidden=true;}
 function show(b){active=b;tip.textContent=b.dataset.termHelp;tip.hidden=false;b.setAttribute('aria-describedby',tip.id);const r=b.getBoundingClientRect(),w=tip.offsetWidth,h=tip.offsetHeight;tip.style.left=Math.max(12,Math.min(innerWidth-w-12,r.left))+'px';tip.style.top=Math.max(12,r.bottom+h+16<innerHeight?r.bottom+8:r.top-h-8)+'px';}
 function enhance(root=document){root.querySelectorAll('th[scope="col"],label,.dataset-legend .cell-sentinel').forEach(el=>{if(el.dataset.helpChecked||el.classList.contains('sr-only'))return;el.dataset.helpChecked='true';const label=[...el.childNodes].filter(n=>n.nodeType===3).map(n=>n.textContent).join('').trim()||el.textContent.trim();const text=textFor(label,el.matches('th[scope="col"]'));if(!text)return;const b=document.createElement('button');b.type='button';b.className='term-help';b.textContent='?';b.setAttribute('aria-label','Explain '+label);b.dataset.termHelp=text;el.append(b);b.onmouseenter=()=>show(b);b.onmouseleave=()=>{if(document.activeElement!==b)hide();};b.onfocus=()=>show(b);b.onblur=hide;b.onclick=e=>{e.preventDefault();e.stopPropagation();show(b);};});}
 document.addEventListener('keydown',e=>{if(e.key==='Escape')hide();});document.addEventListener('pointerdown',e=>{if(!e.target.closest('.term-help'))hide();});window.addEventListener('scroll',hide,true);window.addEventListener('resize',hide);
 enhance();let pending=false;new MutationObserver(records=>{if(!records.some(r=>r.target!==tip&&[...r.addedNodes].some(n=>n.nodeType===1&&!n.classList.contains('term-help'))))return;if(!pending){pending=true;requestAnimationFrame(()=>{pending=false;enhance();});}}).observe(document.querySelector('main'),{childList:true,subtree:true});
 return {enhance};
})();
