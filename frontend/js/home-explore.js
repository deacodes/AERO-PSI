/* Homepage choices carry an editable research question into the appropriate tool. */
const HomeExplore=(()=>{
 const examples={
  flame:{question:'How does gravity affect flame size?',group:'FLEX',goal:'flame_geometry',explanation:'FLEX includes flame extinction diameters. A gravity comparison also needs matched conditions and acceleration measurements; one recorded diameter cannot describe the entire flame history.'},
  coagulation:{question:'What measurements would validate aerosol coagulation under different gravity conditions?',group:'PSI101',goal:'coagulation',explanation:'Particle-number records can help describe an aerosol population. Testing a size-evolution model also requires time-resolved size distributions and matched gas, flow and gravity conditions.'},
  scattering:{question:'Can the supplied measurements validate a multi-angle scattering model?',group:'PSI102',goal:'scattering',explanation:'Recorded detector signals and calculated angular scattering answer different questions. A quantitative comparison needs optical properties, angular geometry, calibration and a known particle population.'}
 };let selected='flame';
 function choose(key){selected=key;const e=examples[key];$('#homeExampleQuestion').textContent=e.question;$('#homeExampleExplanation').textContent=e.explanation;$$('[data-home-example]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.homeExample===key)));document.dispatchEvent(new CustomEvent('home-example-changed',{detail:{key}}));}
 function explore(key){const e=examples[key];setAtlasGroups();$('#gapQuestion').value=e.question;$('#atlasGroup').value=e.group;$('#gapGoal').value=e.goal;researchInvalidate();navigate('atlas');}
 $$('[data-home-example]').forEach(b=>b.onclick=()=>choose(b.dataset.homeExample));
 $$('[data-home-question]').forEach(b=>b.onclick=()=>explore(b.dataset.homeQuestion));
 $$('[data-home-tool]').forEach(b=>b.onclick=()=>{setLabMode(b.dataset.homeTool);navigate('lab');});
 $('#homeCheckEvidence').onclick=()=>explore(selected);
 $('#homeAskQuestion').onclick=()=>{clearScienceConversation();$('#copilotQuestion').value=examples[selected].question;navigate('evidence');$('#copilotQuestion').focus();};
 $$('[data-home-source]').forEach(b=>b.onclick=()=>{clearScienceConversation();$('#answerMode').value=b.dataset.homeSource;$('#answerMode').dispatchEvent(new Event('change'));navigate('evidence');$('#copilotQuestion').focus();});
 return {choose,explore};
})();

// Small, user-driven story interactions; no AI requests or fabricated chart data.
(()=>{
 const lenses={observed:['Start with what was measured','A detector signal is evidence. Its meaning needs context.','Inspect the recorded values, units and run conditions before comparing results. The original signal stays separate from any interpretation.'],calculated:['Explore a possible explanation','A model lets you change one assumption at a time.','Compare scenarios to understand what the equations predict. A calculated curve becomes an experimental claim only after an appropriate comparison with measurements.'],unknown:['Find the next useful question','A missing measurement can shape the next investigation.','Identify what would distinguish competing explanations. Missing evidence in this collection is a reason to investigate, not proof that nobody has studied it.']};
 $$('[data-lens]').forEach(b=>b.onclick=()=>{const [label,title,body]=lenses[b.dataset.lens];$('#homeLensLabel').textContent=label;$('#homeLensTitle').textContent=title;$('#homeLensText').textContent=body;$$('[data-lens]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));});
 if('IntersectionObserver' in window){const observer=new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting){e.target.classList.add('chapter-entered');observer.unobserve(e.target);}}),{threshold:.12});$$('#page-home .home-chapter').forEach(e=>observer.observe(e));}
})();
