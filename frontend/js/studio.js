/* Investigation authoring is independent of any one scientific model. */
const Studio = (() => {
  const view = {record:null, selected:null, items:[], dirty:false, busy:false, tab:'method', dataset:null, rows:[], pointLabel:''};
  const kinds = {literature:'Literature study', data_analysis:'Data analysis', simulation:'Simulation', experiment:'Experiment proposal', saved_analysis:'Saved tool analysis'};
  const status = (message, error=false) => { $('#studioStatus').textContent=message; $('#studioStatus').dataset.state=error?'error':'normal'; };
  const request = (action, data) => post(`/api/v1/studio/${action}`, data);
  const stamp = () => ({id:view.record.id, revision:view.record.revision});
  const step = () => view.record?.content.steps.find(s=>s.id===view.selected);
  const dataset = () => view.record?.datasets.find(d=>d.id===view.dataset);
  const date = value => new Date(value).toLocaleString(undefined,{dateStyle:'medium',timeStyle:'short'});
  function dirty() { view.dirty=true; $('#studioSaveState').textContent='Unsaved changes'; }
  async function action(fn) {
    if(view.busy)return;
    view.busy=true; $('#page-studio').setAttribute('aria-busy','true');
    const controls=$$('button,input,textarea,select',$('#page-studio')); const prior=controls.map(b=>b.disabled);
    controls.forEach(b=>b.disabled=true);
    try { await fn(); }
    catch(error) { status(error.message,true); }
    finally { view.busy=false; $('#page-studio').removeAttribute('aria-busy'); controls.forEach((b,i)=>{if(b.isConnected)b.disabled=prior[i];}); availability(); }
  }
  function availability() {
    const d=dataset();
    $('#studioInterpret').disabled=!d; $('#studioChartCsv').disabled=!d;
    $('#studioChartSvg').disabled=!$('#studioChart svg'); $('#studioPointStep').disabled=!view.rows.length;
  }
  function metadata() {
    const r=view.record,c=r.content;
    $('#studioMeta').textContent=`${kinds[c.kind]} · ${r.origin==='vertex_draft'?'SI-assisted draft':'User-authored'} · revision ${r.revision} · ${date(r.updated_at)}`;
  }
  function interpretationForDataset() {
    const review=view.record?.ai_reviews.filter(r=>r.dataset_id===view.dataset).at(-1);
    $('#studioGraphAnswer').innerHTML='';
    if(review) {
      showAnswer(review.answer);
      $('#studioGraphAnswer').insertAdjacentHTML('afterbegin', `<p class="micro">Question: ${escapeHTML(review.question)} · ${review.scope_row_count??review.row_indices.length} rows in scope · at most ${review.preview_rows??30} preview rows · plan revision ${review.plan_revision??'not recorded'}${dataset()?.stale?' · Dataset is now out of date':''}</p>`);
    }
  }
  async function persist() {
    if(!view.record||!view.dirty)return;
    const result=await request('save',{...stamp(),content:view.record.content});
    view.record=result;view.dirty=false;$('#studioSaveState').textContent=`Saved · revision ${result.revision}`;
    progress(); metadata();
  }
  function progress() {
    const steps=view.record.content.steps, complete=steps.filter(s=>s.completed).length;
    $('#studioProgress').max=steps.length||1;$('#studioProgress').value=complete;
    $('#studioProgressLabel').textContent=`${complete} / ${steps.length} complete`;
  }
  function showPanel(tab) {
    view.tab=tab;
    $$('[data-studio-tab]').forEach(b=>b.setAttribute('aria-current',b.dataset.studioTab===tab?'page':'false'));
    for(const name of ['method','design','results','safety','sources'])$('#studio-'+name).hidden=name!==tab;
    if(tab==='results')renderData();
  }
  async function library() {
    const result=await jsonFetch('/api/v1/studio/library');view.items=result.items;renderLibrary();
    if(result.warnings.length)status(result.warnings.join('; '),true);
  }
  function renderLibrary() {
    const query=$('#studioSearch').value.toLowerCase(), filter=$('#studioFilter').value;
    const items=view.items.filter(r=>(filter==='all'||(filter==='archived')===r.archived)&&`${r.title} ${r.question} ${r.kind}`.toLowerCase().includes(query));
    $('#studioLibraryItems').innerHTML=items.map(r=>`<button type="button" class="studio-record" data-record="${r.id}" data-origin="${r.origin}"><div class="studio-record-meta"><span>${escapeHTML(kinds[r.kind]||r.kind)}</span><span>${r.archived?'Archived':`${r.completed_steps} / ${r.total_steps} steps`}</span></div><h2>${escapeHTML(r.title)}</h2><p>${escapeHTML(r.question===r.title?'Open the saved method, evidence and results.':r.question.slice(0,200))}</p><progress max="${r.total_steps||1}" value="${r.completed_steps}" aria-label="${r.completed_steps} of ${r.total_steps} steps completed"></progress><p class="micro">${escapeHTML(date(r.updated_at))} · ${r.origin==='analysis'?'Earlier tool analysis':r.origin_label==='vertex_draft'?'SI-assisted draft':'User-authored plan'}</p></button>`).join('')||`<div class="studio-empty"><h2>${view.items.length?'No investigations match':'Your next question starts here'}</h2><p>${view.items.length?'Try another search or show all saved work.':'Create a literature study, analyze measurements, explore a model or develop an experiment proposal. Your methods and results will stay together here.'}</p>${view.items.length?'':'<button type="button" class="button-primary" data-start-investigation>Start an investigation</button>'}</div>`;
    $$('[data-record]').forEach(b=>b.onclick=()=>action(async()=>{
      await persist();
      if(b.dataset.origin==='analysis') {
        const r=await jsonFetch('/api/v1/si/investigation?id='+b.dataset.record);
        navigate('evidence');invalidatePlan();$('#investigationQuestion').value=r.question;displayInvestigation(r);
        $('#studioTitle').value='';return;
      }
      await open(b.dataset.record);
    }));
    $('[data-start-investigation]')?.addEventListener('click',()=>$('#studioNew').click());
  }
  async function open(id) {
    view.record=await jsonFetch('/api/v1/studio/record?id='+encodeURIComponent(id));
    view.dirty=false;view.selected=view.record.content.steps[0]?.id||null;view.dataset=view.record.datasets[0]?.id||null;view.rows=[];
    $('#studioLibrary').hidden=true;$('#studioCreate').hidden=true;$('#studioDetail').hidden=false;
    history.replaceState({page:'studio'},'',`/studio?id=${encodeURIComponent(id)}`);
    renderRecord();status('');
  }
  function renderRecord() {
    const r=view.record,c=r.content;
    $('#studioTitle').value=c.title;$('#studioEditQuestion').value=c.question;$('#studioSummary').value=c.summary;
    $('#studioSummaryView').innerHTML=richText(c.summary);
    $('#studioMeta').textContent=`${kinds[c.kind]} · ${r.origin==='vertex_draft'?'SI-assisted draft':'User-authored'} · revision ${r.revision} · ${date(r.updated_at)}`;
    $('#studioSaveState').textContent=`Saved · revision ${r.revision}`;$('#studioArchive').textContent=r.archived?'Restore to active':'Archive';
    $('#studioSafety').value=c.safety;$('#studioSafetyView').innerHTML=richText(c.safety||'No safety or integrity review has been recorded.');
    $('#studioSafetyScope').textContent=c.kind==='experiment'?'This is a proposed research plan, not approval to conduct a physical experiment. Record the applicable facility and qualified safety review before execution.':'Review source quality, model assumptions, data handling and limits of inference for this investigation.';
    $('#studioLimits').innerHTML=c.limitations.map(v=>`<li>${escapeHTML(v)}</li>`).join('')||'<li>No limitations recorded yet. This does not establish validity.</li>';
    $('#studioNotebook').value=c.notes;
    $('#studioSources').innerHTML=r.sources.map(s=>`<details><summary>${escapeHTML(s.title||s.source_path||s.id)}</summary><p class="micro">${escapeHTML(s.id)}</p>${reviewedSourceContent(s)}</details>`).join('')||'<p>No source records are attached. A general scientific plan can still be developed; source-specific claims require evidence.</p>';
    progress();renderSteps();renderStep();showPanel(view.tab);document.dispatchEvent(new CustomEvent('studio-record-rendered'));
  }
  function renderSteps() {
    $('#studioSteps').innerHTML=view.record.content.steps.map((s,i)=>`<li class="studio-step" data-active="${s.id===view.selected}"><input type="checkbox" class="studio-step-toggle" data-toggle-step="${s.id}" ${s.completed?'checked':''} aria-label="Mark step ${i+1}, ${escapeHTML(s.title)}, completed"><button type="button" class="studio-step-open" data-open-step="${s.id}">${escapeHTML(s.title)}<small>Step ${i+1}${s.tool?' · '+escapeHTML(toolLabels[s.tool]||s.tool):''}</small></button></li>`).join('')||'<p class="micro">Add your first step or develop the plan with SI.</p>';
    $$('[data-open-step]').forEach(b=>b.onclick=()=>{view.selected=b.dataset.openStep;renderSteps();renderStep();showPanel('method');});
    $$('[data-toggle-step]').forEach(b=>b.onchange=()=>action(async()=>{const s=view.record.content.steps.find(s=>s.id===b.dataset.toggleStep);s.completed=b.checked;dirty();await persist();renderSteps();status('Progress saved.');}));
  }
  function renderStep() {
    const s=step();
    if(!s){$('#studioStepContent').innerHTML='<h2>Build your method</h2><p>Add a step with its purpose, inputs and expected output, or ask SI to develop a plan for your research question.</p>';return;}
    const fields=[['title','Step title'],['method','Method · Markdown and LaTeX'],['rationale','Why this step matters'],['inputs','Required inputs and units'],['expected_output','Expected output'],['interpretation','Interpretation and success criteria']];
    $('#studioStepContent').innerHTML=`<h2>${escapeHTML(s.title)}</h2><div class="evidence-prose">${richText(s.method||'Write the method for this step, including what you need and how you will assess the result.')}</div>${s.rationale?`<h3>Why this matters</h3><div class="evidence-prose">${richText(s.rationale)}</div>`:''}<div class="studio-step-context"><div><h3>Required inputs</h3><div class="evidence-prose">${richText(s.inputs||'Not yet specified.')}</div></div><div><h3>Expected output</h3><div class="evidence-prose">${richText(s.expected_output||'Not yet specified.')}</div></div></div>${s.interpretation?`<h3>How to interpret the result</h3><div class="evidence-prose">${richText(s.interpretation)}</div>`:''}${s.source_ids.length?`<p class="micro">Evidence: ${s.source_ids.map(escapeHTML).join(', ')}</p><button type="button" class="button-text" id="studioStepSources">Inspect cited sources</button>`:''}<details id="studioEditStep"><summary>Edit this step</summary>${fields.map(([key,label])=>`<label>${label}${key==='title'?`<input data-step-field="${key}" maxlength="200" value="${escapeHTML(s[key])}">`:`<textarea data-step-field="${key}" rows="${key==='method'?6:3}">${escapeHTML(s[key])}</textarea>`}</label>`).join('')}<label>Optional mathematical / evidence tool<select id="studioStepTool"><option value="">No tool needed</option>${Object.entries(toolLabels).map(([id,name])=>`<option value="${id}" ${s.tool===id?'selected':''}>${escapeHTML(name)}</option>`).join('')}<option value="plan_measurements" ${s.tool==='plan_measurements'?'selected':''}>Plan missing measurements</option></select></label><div class="studio-step-actions"><button type="button" class="button-secondary" id="studioApplyStep">Apply edits</button><button type="button" class="button-text" id="studioMoveUp">Move earlier</button><button type="button" class="button-text" id="studioMoveDown">Move later</button><button type="button" class="button-text" id="studioRemoveStep">Remove step</button></div></details><label>Observations &amp; decisions<textarea id="studioStepNotes" rows="3" placeholder="Record what you observed or decided…">${escapeHTML(s.notes)}</textarea></label>${s.tool?`<div class="studio-tool"><h3>${escapeHTML(toolLabels[s.tool]||s.tool)}</h3><p>This runs the existing Python tool with the inputs you supply. It does not mark the research step complete.</p><div class="studio-actions"><button type="button" id="studioUseContext" class="button-secondary">Use current workbench inputs</button><button type="button" id="studioOpenModel" class="button-text">Open mathematical workbench</button></div><details id="studioRawInputs"><summary>Inspect or edit explicit tool inputs</summary><label for="studioToolInputs">Tool inputs · JSON</label><textarea id="studioToolInputs" rows="7" spellcheck="false">{}</textarea><p class="micro">Model tools require a scenario; optics requires optical_request; observed analysis requires observed_request. Source inspection requires source_path. Evidence retrieval and ranking can use {}. Imported workbench inputs remain editable.</p></details><button type="button" id="studioRunTool" class="button-primary">Run and save calculation</button></div>`:''}`;
    $$('[data-step-field]').forEach(el=>el.oninput=()=>{s[el.dataset.stepField]=el.value;dirty();});
    $('#studioStepNotes').oninput=e=>{s.notes=e.target.value;dirty();};
    $('#studioStepTool').onchange=e=>{s.tool=e.target.value||null;dirty();};
    $('#studioApplyStep').onclick=()=>action(async()=>{await persist();renderSteps();renderStep();status('Step saved. Changed methods invalidate their earlier calculations.');});
    $('#studioStepSources')?.addEventListener('click',()=>showPanel('sources'));
    for(const [id,offset] of [['studioMoveUp',-1],['studioMoveDown',1]])$('#'+id).onclick=()=>{const list=view.record.content.steps,index=list.indexOf(s),next=index+offset;if(next>=0&&next<list.length){[list[index],list[next]]=[list[next],list[index]];dirty();renderSteps();}};
    $('#studioRemoveStep').onclick=()=>action(async()=>{view.record.content.steps=view.record.content.steps.filter(v=>v.id!==s.id);view.selected=view.record.content.steps[0]?.id;dirty();await persist();renderSteps();renderStep();status('Step removed. Its prior version remains in revision history.');});
    if(s.tool){
      $('#studioUseContext').onclick=()=>{
        const inputs={};if(state.currentCoag)inputs.scenario=structuredClone(state.currentCoag.payload);
        if(state.currentOptical)inputs.source_path=state.currentOptical.source;
        if(workspace.optics)inputs.optical_request=structuredClone(workspace.optics.request);
        if(workspace.observed)inputs.observed_request=structuredClone(workspace.observed.request);
        $('#studioToolInputs').value=JSON.stringify(inputs,null,2);$('#studioRawInputs').open=true;status(Object.keys(inputs).length?'Workbench inputs copied. Review them before running.':'No computed workbench context yet. Enter inputs or open the relevant model.');
      };
      $('#studioOpenModel').onclick=()=>navigate('lab');
      $('#studioRunTool').onclick=()=>action(async()=>{
        const inputs=JSON.parse($('#studioToolInputs').value);await persist();status('Running the selected Python tool…');
        view.record=await request('execute',{...stamp(),step_id:s.id,inputs});view.dataset=view.record.datasets.at(-1)?.id||null;
        renderRecord();showPanel('results');status('Calculation and inputs saved. Research-step completion remains your decision.');
      });
    }
  }
  function addStep(title='New research step',notes='',data_links=[]) {
    const s={id:crypto.randomUUID().replaceAll('-',''),title,method:'',rationale:'',inputs:'',expected_output:'',interpretation:'',tool:null,source_ids:[],completed:false,notes,data_links};
    if(view.record.content.steps.length>=30)throw Error('This investigation already has 30 steps.');
    view.record.content.steps.push(s);view.selected=s.id;dirty();renderSteps();renderStep();showPanel('method');
  }
  function renderData() {
    const old=view.dataset;$('#studioDataset').innerHTML=view.record.datasets.map(d=>`<option value="${d.id}">${escapeHTML(d.name)}${d.stale?' · out of date':''}</option>`).join('');
    if(view.record.datasets.some(d=>d.id===old))$('#studioDataset').value=old;
    view.dataset=$('#studioDataset').value||null;
    $('#studioChartSuggestions').innerHTML=view.record.content.suggested_charts.length?`<details><summary>Graphs suggested for this question</summary>${view.record.content.suggested_charts.map(s=>`<h3>${escapeHTML(s.title)} · ${escapeHTML(s.type)}</h3><p>${escapeHTML(s.purpose)}</p><p class="micro">Data needed: ${escapeHTML(s.required_data)}</p>`).join('')}</details>`:'';
    $('#studioRuns').innerHTML=view.record.runs.map(r=>`<details><summary>${escapeHTML(toolLabels[r.tool]||r.tool)} · ${r.stale?'Out of date':'Saved calculation'} · ${escapeHTML(date(r.created_at))}</summary><pre>${escapeHTML(JSON.stringify(r,null,2))}</pre></details>`).join('')||'<p>No calculations have been executed in this investigation.</p>';
    axes();
    interpretationForDataset();
  }
  function axes() {
    view.dataset=$('#studioDataset').value||null;const d=dataset();view.rows=[];$('#studioPointStep').disabled=true;
    for(const [id,index] of [['studioX',0],['studioY',1],['studioZ',2]]){
      $('#'+id).innerHTML=(d?.columns||[]).map((c,i)=>`<option value="${i}">${escapeHTML(c.name)}${c.unit?' ('+escapeHTML(c.unit)+')':''}</option>`).join('');
      $('#'+id).value=String(Math.min(index,(d?.columns.length||1)-1));
    }
    draw(); interpretationForDataset();
  }
  function draw() {
    const d=dataset();view.rows=[];$('#studioPointStep').disabled=true;
    $('#studioZLabel').hidden=$('#studioChartType').value!=='heatmap';
    $('#studioDatasetScope').textContent=d?`${d.classification.replaceAll('_',' ')}${d.stale?' · OUT OF DATE: the plan has changed':''} · ${d.reference}${d.columns.some(c=>!c.unit)?' · Some column units have not been supplied.':''}`:'';
    StudioCharts.render($('#studioChart'),d,$('#studioChartType').value,Number($('#studioX').value),Number($('#studioY').value),Number($('#studioZ').value),(indices,label)=>{view.rows=indices;view.pointLabel=label;$('#studioPointStep').disabled=false;});
    $('#studioDataTable').innerHTML=d?`<table><thead><tr><th>Source row</th>${d.columns.map(c=>`<th>${escapeHTML(c.name)}${c.unit?' ('+escapeHTML(c.unit)+')':''}</th>`).join('')}</tr></thead><tbody>${d.rows.map((r,i)=>`<tr><td>${i+1}</td>${r.map(v=>`<td>${v===null?'Missing':escapeHTML(v)}</td>`).join('')}</tr>`).join('')}</tbody></table>`:'<p>No dataset selected.</p>';
    $('#studioInterpret').disabled=!d;$('#studioChartCsv').disabled=!d;$('#studioChartSvg').disabled=!$('#studioChart svg');
  }
  function showAnswer(answer) {
    const unavailable=['evidence_only_fallback','science_unavailable','educational_unavailable'].includes(answer.mode);
    $('#studioGraphAnswer').innerHTML=unavailable?`<p class="error-box">${escapeHTML(answer.service?.reason||'SI did not generate an interpretation. No preset answer has been substituted.')}</p>`:
      richText(answer.scientific_explanation||answer.answer||'')+['observed_in_source','model_result','unknown_or_limitation'].map(k=>(answer[k]||[]).map(v=>richText(v)).join('')).join('');
    if(answer.sources?.length)$('#studioGraphAnswer').insertAdjacentHTML('beforeend',`<details><summary>Interpretation sources</summary>${answer.sources.map(s=>`<p>${escapeHTML(s.id)} · ${escapeHTML(s.source_path||s.title||'')} · ${escapeHTML(s.source_range||'')}</p>`).join('')}</details>`);
  }
  function brief() {
    const r=view.record,c=r.content;
    return [`# ${c.title}`,c.question,`Revision ${r.revision} · ${r.origin} · saved ${r.updated_at}`,c.summary,'## Experiment design',c.design?.hypothesis||'',`Response: ${c.design?.outcome||'Not defined'}`,...(c.design?.variables||[]).map(v=>`- ${v.name}: ${v.minimum} to ${v.maximum} ${v.unit}; ${v.levels} proposed levels. Basis: ${v.basis}`),`Replicates per condition: ${c.design?.replicates||1}`,`Controls: ${c.design?.controls||'Not defined'}`,`Measurement method: ${c.design?.measurement_method||'Not defined'}`,`Analysis plan: ${c.design?.analysis||'Not defined'}`,'Design values are proposed conditions, not measured or predicted outcomes.','## Method',...c.steps.map((s,i)=>`### ${i+1}. ${s.title}\n\nCompletion recorded: ${s.completed?'yes':'no'}\n\n${s.method}\n\n**Rationale:** ${s.rationale}\n\n**Inputs:** ${s.inputs}\n\n**Expected output:** ${s.expected_output}\n\n**Interpretation:** ${s.interpretation}\n\n**Notes:** ${s.notes}\n\nSources: ${s.source_ids.join(', ')||'None cited'}`),'## Safety and limits',c.safety,...c.limitations.map(v=>'- '+v),'## Datasets',...r.datasets.map(d=>`- ${d.name}: ${d.classification}; ${d.rows.length} rows; ${d.reference}${d.stale?' (out of date)':''}`),'## Calculations',...r.runs.map(v=>`- ${v.id}: ${v.tool}; ${v.stale?'out of date':'saved'}; complete inputs and outputs are in the JSON export.`),'## Sources',...r.sources.map(s=>`- ${s.id}: ${s.source_path}; ${s.source_range}`),'## Notebook',c.notes,'Completion is user-recorded progress, not scientific verification.'].join('\n\n');
  }
  $('#studioSearch').oninput=renderLibrary;$('#studioFilter').onchange=renderLibrary;
  $('#studioNew').onclick=()=>action(async()=>{await persist();view.composeContext={};$('#studioLibrary').hidden=true;$('#studioDetail').hidden=true;$('#studioCreate').hidden=false;$('#studioQuestion').focus();status('');});
  $('#studioCancelCreate').onclick=()=>{ $('#studioCreate').hidden=true;$('#studioLibrary').hidden=false; };
  $('#studioBack').onclick=()=>action(async()=>{await persist();$('#studioDetail').hidden=true;$('#studioLibrary').hidden=false;history.replaceState({page:'studio'},'','/studio');await library();});
  $('#studioCreate').onsubmit=e=>{e.preventDefault();action(async()=>{
    status('SI is developing the method and its limitations. This may take up to 120 seconds…');
    const r=await request('generate',{question:$('#studioQuestion').value,kind:$('#studioKind').value,...(view.composeContext||{})});await open(r.id);status('SI draft saved. Review the steps, assumptions and sources before use.');
  });};
  $('#studioManual').onclick=()=>action(async()=>{
    const q=$('#studioQuestion').value.trim();if(!q)throw Error('Enter a research question first.');
    const r=await request('create',{content:{title:q.slice(0,180),question:q,kind:$('#studioKind').value,steps:[]}});await open(r.id);addStep('Define the research method');status('Manual draft created. Add your method or ask SI to develop it.');
  });
  $('#studioSave').onclick=()=>action(async()=>{await persist();renderRecord();status('Investigation saved.');});
  for(const [id,key] of [['studioTitle','title'],['studioEditQuestion','question'],['studioSummary','summary'],['studioSafety','safety'],['studioNotebook','notes']])$('#'+id).oninput=e=>{view.record.content[key]=e.target.value;dirty();};
  $('#studioAddStep').onclick=()=>{try{addStep();}catch(e){status(e.message,true);}};
  $$('[data-studio-tab]').forEach(b=>b.onclick=()=>showPanel(b.dataset.studioTab));
  $('#studioRevise').onclick=()=>action(async()=>{
    await persist();status('SI is revising the investigation. Your current saved revision is retained…');
    view.record=await request('generate',{...stamp(),question:view.record.content.question,kind:view.record.content.kind,instructions:$('#studioRevisionPrompt').value});
    view.selected=view.record.content.steps[0]?.id;view.dirty=false;renderRecord();status('Revised draft saved. Review its new steps and limitations.');
  });
  $('#studioArchive').onclick=()=>action(async()=>{await persist();view.record=await request('save',{...stamp(),content:view.record.content,archived:!view.record.archived});renderRecord();status(view.record.archived?'Archived; you can restore it at any time.':'Restored to active investigations.');});
  $('#studioHistory').onclick=()=>action(async()=>{const h=await jsonFetch('/api/v1/studio/history?id='+view.record.id);$('#studioHistoryItems').innerHTML=h.map(r=>`<details><summary>Revision ${r.revision} · ${escapeHTML(date(r.updated_at))}</summary><h3>${escapeHTML(r.content.title)}</h3><div class="evidence-prose">${richText(r.content.summary)}</div>${r.content.steps.map(s=>`<h4>${escapeHTML(s.title)}</h4><div class="evidence-prose">${richText(s.method)}</div>`).join('')}<button class="button-text" type="button" data-revision="${r.revision}">Export this plan revision</button></details>`).join('')||'<p>No earlier revisions yet.</p>';$$('[data-revision]').forEach(b=>b.onclick=()=>download(`investigation-revision-${b.dataset.revision}.json`,JSON.stringify(h.find(r=>r.revision===Number(b.dataset.revision)),null,2)));});
  $('#studioExport').onclick=()=>action(async()=>{await persist();download(`investigation-${view.record.id}.json`,JSON.stringify(view.record,null,2));});
  $('#studioBrief').onclick=()=>action(async()=>{await persist();download('research-brief.md',brief(),'text/markdown');});
  $('#studioToggleData').onclick=()=>{$('#studioDataForm').hidden=!$('#studioDataForm').hidden;};
  $('#studioCsvFile').onchange=async e=>{const f=e.target.files[0];if(!f)return;if(f.size>90000){status('Use a CSV smaller than 90 KB.',true);return;}$('#studioCsv').value=await f.text();if(!$('#studioDataName').value)$('#studioDataName').value=f.name.replace(/\.csv$/i,'');};
  $('#studioAddData').onclick=()=>action(async()=>{
    const parsed=StudioCharts.parseCSV($('#studioCsv').value), units=$('#studioDataUnits').value.split(',').map(s=>s.trim());await persist();
    view.record=await request('dataset',{...stamp(),dataset:{name:$('#studioDataName').value,reference:$('#studioDataReference').value,columns:parsed.headers.map((name,i)=>({name,unit:units[i]||''})),rows:parsed.rows}});
    view.dataset=view.record.datasets.at(-1).id;$('#studioDataForm').hidden=true;renderData();$('#studioSaveState').textContent=`Saved · revision ${view.record.revision}`;status('Dataset saved with your source description.');
  });
  $('#studioDataset').onchange=axes;for(const id of ['studioChartType','studioX','studioY','studioZ'])$('#'+id).onchange=draw;
  $('#studioChartCsv').onclick=()=>{const d=dataset();if(d)download('investigation-data.csv',StudioCharts.csv([d.columns.map(c=>c.name+(c.unit?' ['+c.unit+']':'')),...d.rows]),'text/csv');};
  $('#studioChartSvg').onclick=()=>{const svg=$('#studioChart svg');if(!svg)return;const copy=svg.cloneNode(true), css=getComputedStyle(document.body);copy.setAttribute('style',`background:${css.getPropertyValue('--surface')};--blue:${css.getPropertyValue('--blue')};--pink:${css.getPropertyValue('--pink')};--line:${css.getPropertyValue('--line')};--muted:${css.getPropertyValue('--muted')}`);download('investigation-chart.svg',new XMLSerializer().serializeToString(copy),'image/svg+xml');};
  $('#studioPointStep').onclick=()=>{if(view.rows.length)addStep('Investigate the selected data',`Dataset: ${dataset().name}\nSaved dataset ID: ${dataset().id}\n${view.rows.length} source rows selected; complete zero-based row indices are preserved in this step’s data_links.\n${view.pointLabel}`, [{dataset_id:dataset().id,row_indices:[...view.rows]}]);};
  $('#studioInterpret').insertAdjacentHTML('beforebegin','<p class="micro">SI receives summary statistics for all selected rows (or the whole dataset) plus up to 30 preview rows. Larger selections keep their full membership in the saved record. A preview cannot establish every trend in a long series.</p>');
  $('#studioInterpret').onclick=()=>action(async()=>{
    const q=$('#studioGraphQuestion').value.trim();if(!q)throw Error('Enter a question about these data.');await persist();status('SI is considering your saved values and the question…');
    view.record=await request('interpret',{...stamp(),question:q,dataset_id:view.dataset,row_indices:view.rows});interpretationForDataset();$('#studioSaveState').textContent=`Saved · revision ${view.record.revision}`;status('Interpretation request recorded. Provider availability is shown with the response.');
  });
  document.addEventListener('page-changed',e=>{if(e.detail.page!=='studio')return;action(async()=>{
    if(e.detail.id&&e.detail.id!==view.record?.id){await persist();await open(e.detail.id);}else if(!e.detail.id&&!view.record){await library();}
    else if(!e.detail.id&&$('#studioDetail').hidden)await library();
    else if(!e.detail.id&&view.record)history.replaceState({page:'studio'},'',`/studio?id=${view.record.id}`);
  });});
  addEventListener('beforeunload',e=>{if(view.dirty){e.preventDefault();e.returnValue='';}});
  // A return path from the mathematical module keeps the user's active investigation intact.
  async function compose(question,context={}) {
    await action(async()=>{
      await persist();navigate('studio');
      view.composeContext=context;
      $('#studioQuestion').value=question;$('#studioKind').value='experiment';
      $('#studioLibrary').hidden=true;$('#studioDetail').hidden=true;$('#studioCreate').hidden=false;
      $('#studioQuestion').focus();status('Develop a research method for this question; mathematical tools are optional.');
    });
  }
  return {view,open,library,compose,markDirty:dirty};
})();
