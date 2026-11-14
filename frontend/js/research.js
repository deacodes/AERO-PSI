/* Actual measurements and contextual SI; never a fixed three-tool plan. */
const researchView={result:null,dataset:null,sourceRows:[],selected:[],epoch:0,history:[],request:null,tab:'gaps'};
function researchTab(name){researchView.tab=name;for(const tab of ['measurements','gaps','reports','discussion'])$('#research-'+tab).hidden=tab!==name;$$('[data-research-tab]').forEach(b=>b.setAttribute('aria-current',b.dataset.researchTab===name?'page':'false'));}
$$('[data-research-tab]').forEach(b=>b.onclick=()=>researchTab(b.dataset.researchTab));
function researchUnavailable(message){$('#gapStatus').textContent=message;}
function researchInvalidate(){researchView.siResult=null;researchView.pendingSource=null;$('#researchCandidates').replaceChildren();$('#researchOverview').replaceChildren();$('#researchReports').replaceChildren();clearResearchData('Check measurement gaps to load evidence for the current question.','Evidence needs updating');$('#atlasGaps').replaceChildren();researchView.epoch++;$('#gapForm button[type=submit]').disabled=false;researchView.result=null;researchView.selected=[];researchView.history=[];$('#researchSIAnswer').textContent='';['gapsWithSI','exportGapPlan','gapCreateInvestigation','researchAskPoint'].forEach(id=>$('#'+id).disabled=true);$('#gapStatus').textContent='Question or investigation changed. Explore evidence again to update the findings.';$('#researchAsk').disabled=true;}
loadAtlasGaps=async function(interactive=false){
  const useSI=$('#gapAnalysisMode').value==='si';
  if(useSI&&!interactive){$('#gapStatus').textContent='Ready to review your question with SI. Click Review with SI to begin.';return;}
  const question=$('#gapQuestion').value.trim();if(!question)return;
  const epoch=++researchView.epoch;const request={question,goal:$('#gapGoal').value,group:$('#atlasGroup').value||undefined,...(researchView.pendingSource?{source_path:researchView.pendingSource}:{})};
  const button=$('#gapForm button[type=submit]');button.disabled=true;$('#gapStatus').textContent=useSI?'SI is interpreting your question, inspecting evidence and developing findings. This can take a few minutes.':'Running a basic rule-based evidence check…';
  $('#atlasGaps').replaceChildren();researchView.siResult=null;researchView.result=null;researchView.selected=[];researchView.history=[];$('#researchSIAnswer').textContent='';
  ['gapsWithSI','gapCreateInvestigation','exportGapPlan','researchAsk','researchAskPoint'].forEach(id=>$('#'+id).disabled=true);
  try{
    const response=await post(useSI?'/api/v1/research/gap-review':'/api/v1/research/explore',request);if(epoch!==researchView.epoch)return;
    if(useSI&&response.status!=='generated'){renderSIGapState(response);return;}
    const result=useSI?response.evidence_view:response;
    researchView.siResult=useSI?response:null;
    if(!result?.assessment)throw Error('The running Python backend is older than this page. Stop it with Ctrl+C, run python3 aero_psi_backend.py serve again, then reload this page.');
    researchView.result=result;researchView.request={...request,group:result.group,table:result.selected_table};discovery.plan=result;
    $('#atlasGroup').innerHTML='<option value="">Find relevant investigations</option>'+result.groups.map(g=>`<option value="${plain(g.group)}">${plain(g.group)}</option>`).join('');$('#atlasGroup').value=request.group||'';
    if(useSI)$('#researchCandidates').replaceChildren();else renderResearchCandidates(result);
    $('#gapStatus').textContent=`${useSI?'SI review complete ·':'Basic rule-based check ·'} ${result.group} · ${result.overview.group_records} experiment-table rows · ${result.runs.length} time-series files · ${result.passages.length} report passages`;
    $('#researchOverview').innerHTML=`<h2>${plain(result.question)}</h2><p>${plain(result.overview.explanation)}</p>${(result.overview.response_summary||[]).map(s=>`<p><strong>${s.numeric_rows} of ${s.total_rows} rows</strong> supply a numeric ${plain(s.measurement)}: ${formatNumber(s.minimum)} to ${formatNumber(s.maximum)}. Other rows may contain missing values or nonnumeric annotations.</p>`).join('')}`;
    $('#researchSource').innerHTML=result.tables.map(t=>`<option value="table:${plain(t.path)}">${plain(t.path.split('/').at(-1))} · ${t.row_count} rows</option>`).join('')+result.runs.map(r=>`<option value="run:${plain(r.source_path)}">${plain(r.material||'Material unspecified')} · ${plain(r.source_path.split('/').at(-1))}</option>`).join('');
    if(result.selected_table)$('#researchSource').value='table:'+result.selected_table;
    renderResearchFindings(result);renderResearchReports(result);document.dispatchEvent(new CustomEvent('research-assessed'));
    if(result.selected_source&&result.runs.some(r=>r.source_path===result.selected_source)){$('#researchSource').value='run:'+result.selected_source;await loadResearchRun(result.selected_source);}else if(result.selected_table)loadResearchTable();else if(result.runs.length)await loadResearchRun(result.runs[0].source_path);else clearResearchData('This investigation has report evidence but no supplied experiment table or imported time series. Open Report findings to inspect the available science.');
    ['gapsWithSI','gapCreateInvestigation','exportGapPlan','researchAsk'].forEach(id=>$('#'+id).disabled=false);
    document.dispatchEvent(new CustomEvent('research-loaded'));
  }catch(error){if(epoch===researchView.epoch){researchView.result=null;$('#atlasGaps').replaceChildren();researchUnavailable(error.message);clearResearchData(error.message||'Evidence could not be loaded. Check that the Python server is running.','Evidence unavailable');}}
  finally{if(epoch===researchView.epoch)button.disabled=false;}
};
function renderResearchCandidates(result){
  const selection=result.selection;if(!selection){$('#researchCandidates').replaceChildren();return;}
  const tied=selection.tied_top_groups.length>1;
  const intro=selection.automatic?`Searched all investigations. Showing ${result.group}. ${tied?'Several investigations share the highest score; the first is displayed alphabetically, not because it is scientifically superior.':'This investigation has the highest score under the matching rule.'}`:`Showing your selected investigation: ${result.group}. Choose another below to inspect its gaps.`;
  $('#researchCandidates').innerHTML=`<h2>Investigations for this question</h2><p>${plain(intro)}</p><p class="micro">${plain(selection.formula)} These scores describe indexed evidence matches, not scientific validity.</p><div class="research-candidates">${selection.candidates.map(c=>`<button type="button" class="button-secondary" data-research-group="${plain(c.group)}" aria-pressed="${c.group===result.group}"><strong>${plain(c.group)}</strong><span>${c.score} / 100</span><small>${c.matched_concepts.length?'Matches: '+plain(c.matched_concepts.join(', ')):'No question concepts matched; any score comes from measurement coverage.'}</small></button>`).join('')}</div>`;
  $$('[data-research-group]').forEach(b=>b.onclick=()=>{$('#atlasGroup').value=b.dataset.researchGroup;researchInvalidate();loadAtlasGaps();});
}
function renderResearchFindings(result){
  if(researchView.siResult){renderSIGapReview(researchView.siResult);return;}
  const a=result.assessment;
  $('#atlasGaps').innerHTML=`<div class="gap-verdict"><h3>${plain(a.verdict)}</h3><p>${plain(a.explanation)}</p>${a.supported_now.length?`<details><summary>What the evidence supports now</summary><ul>${a.supported_now.map(x=>`<li>${plain(x)}</li>`).join('')}</ul></details>`:''}<p class="micro">${plain(a.scope)}</p></div>
    ${a.matrix.length?`<div class="research-table gap-matrix" tabindex="0" role="region" aria-label="Measurement readiness matrix"><table><caption>Evidence needed for this question</caption><thead><tr><th scope="col">Prerequisite</th><th scope="col">Evidence state</th><th scope="col">Recorded coverage</th><th scope="col">Inspect</th></tr></thead><tbody>${a.matrix.map(m=>`<tr><th scope="row">${plain(m.label)}</th><td><span class="gap-state" data-state="${m.state}">${{values_available:'Values available',report_review:'Review report',not_found:'Not found in supplied measurements'}[m.state]}</span></td><td>${m.table_row_count} rows · ${m.usable_channel_count} channels<p class="micro">${plain(m.limit)}</p></td><td>${m.sources.length?`<details><summary>Inspect ${m.sources.length} sample source references</summary>${m.sources.map(sourceDetails).join('')}</details>`:'No measurement source located'}${m.report_ids.length?`<button type="button" class="button-text" data-report-finding="${m.key}">Review report leads</button>`:''}</td></tr>`).join('')}</tbody></table></div>`:''}
    <h3>Next steps</h3><p class="micro">${plain(a.priority_rule)}</p>
    ${a.actions.map(f=>`<article class="research-finding"><p class="research-state">Priority ${f.priority} · ${plain(f.category.replaceAll('_',' '))}</p><h3>${plain(f.title)}</h3><p>${plain(f.reason)}</p><p><strong>Why this matters:</strong> ${plain(f.priority_reason)}</p><p><strong>First action:</strong> ${plain(f.proposal.first_action)}</p><details><summary>Measurement and comparison plan</summary><dl class="gap-plan">${[['Vary','varied_parameter'],['Keep controlled','controls'],['Record','required_outputs'],['Analyze','analysis_plan'],['Expected benefit','expected_benefit']].map(([label,key])=>`<dt>${label}</dt><dd>${plain(f.proposal[key])}</dd>`).join('')}</dl><p>Operating ranges, equipment, cost and physical feasibility require review. No outcome is predicted.</p></details><div class="discovery-actions"><button type="button" class="button-primary" data-save-finding="${f.key}">Save this investigation brief</button><button type="button" class="button-text" data-ask-finding="${f.key}">Discuss in SI</button></div></article>`).join('')||'<p>Choose a focus to assess declared measurement requirements, or save a source-review brief to define your research method.</p>'}`;
  $$('[data-save-finding]').forEach(b=>b.onclick=()=>saveResearchBrief(b.dataset.saveFinding,b));
  $$('[data-ask-finding]').forEach(b=>b.onclick=()=>{const f=a.actions.find(x=>x.key===b.dataset.askFinding);researchTab('discussion');$('#researchFollowup').value=`For my question “${result.question}”, explain why ${f.title.toLowerCase()} matters and how to resolve it using the available evidence. Distinguish recorded values from proposed measurements.`;$('#researchFollowup').focus();});
  $$('[data-report-finding]').forEach(b=>b.onclick=()=>{researchTab('reports');const m=a.matrix.find(x=>x.key===b.dataset.reportFinding);const entry=$$('[data-report-id]').find(e=>m.report_ids.includes(e.dataset.reportId));if(entry){entry.open=true;entry.scrollIntoView({block:'center'});}});
}
async function saveResearchBrief(key,button){
  if(researchView.siResult){draftSIGap();return;}
  if(!researchView.result)return;const epoch=researchView.epoch;button.disabled=true;
  $('#gapStatus').textContent='Rechecking the source evidence and saving your investigation brief…';
  try{await Studio.persist();const r=await post('/api/v1/studio/from-research',{...researchView.request,selected_source:$('#researchSource').value,selected_signal:researchView.runSignal,source_rows:researchView.selected,...(key?{finding_key:key}:{})});
    if(epoch!==researchView.epoch){$('#gapStatus').textContent='The previous question was saved to Studio. Recheck the current question before continuing.';return;}
    Journey.set(r);navigate('studio',{id:r.id});
  }catch(e){$('#gapStatus').textContent=e.message;}finally{if(epoch===researchView.epoch)button.disabled=false;}
}
function renderResearchReports(result){$('#researchReports').innerHTML=result.passages.map(p=>`<details data-report-id="${plain(p.id)}"><summary>${plain(p.title||p.source_path.split('/').at(-1))} · ${plain(p.source_range)}</summary>${reviewedSourceContent(p)}</details>`).join('')||'<p>No matching passages were retrieved for this question and investigation. Try another scientific term or choose a different investigation.</p>';}
function clearResearchData(message,title='Report-based evidence'){researchView.selected=[];$('#researchAskPoint').disabled=true;researchView.dataset=null;researchView.sourceRows=[];$('#researchPlot').innerHTML=`<p>${plain(message)}</p>`;$('#researchTable').textContent='';$('#researchFields').textContent='';$('#atlasRunTitle').textContent=title;$('#atlasRunClass').textContent=message;}
function loadResearchTable(){
  const result=researchView.result;$('#researchSignalLabel').hidden=true;$('#researchMaterialLabel').hidden=false;
  const prior=$('#researchMaterial').value;const materials=[...new Set(result.rows.map(r=>String(r.values.material_or_fuel||'')).filter(Boolean))];$('#researchMaterial').innerHTML='<option value="">All materials</option>'+materials.map(m=>`<option value="${plain(m)}">${plain(m)}</option>`).join('');if(materials.includes(prior))$('#researchMaterial').value=prior;
  const selectedRows=result.rows.filter(r=>!$('#researchMaterial').value||r.values.material_or_fuel===$('#researchMaterial').value);
  const numeric=result.columns.filter(c=>c.numeric_count>0);
  $('#atlasRunTitle').textContent=`${result.group} experiment measurements`;
  $('#atlasRunClass').textContent=`${selectedRows.length} of ${result.rows.length} populated rows from ${result.selected_table.split('/').at(-1)}. Axes retain the source column labels and units.`;
  $('#researchFields').innerHTML=numeric.map(c=>`<div><strong>${plain(c.label)}</strong><span>${c.numeric_count} numeric values in full table · ${formatNumber(c.minimum)} to ${formatNumber(c.maximum)}</span></div>`).join('')||'<p>This table has descriptions and identifiers but no numeric measurements.</p>';
  const columns=[{name:'Source row',unit:'row'},...numeric.map(c=>({name:c.label,unit:'',key:c.key}))];
  const rows=selectedRows.map(row=>[row.source_row,...numeric.map(c=>{const raw=row.values[c.key];if(raw==null||!String(raw).trim())return null;const n=Number(raw);return Number.isFinite(n)?n:null;})]);
  researchView.dataset={name:result.group+' — source table',columns,rows};researchView.sourceRows=selectedRows.map(r=>r.source_row);
  $('#researchProvenance').innerHTML=`<p>${plain(result.selected_table)}</p><p>${plain(result.scope)}</p><p>SHA-256: ${plain(result.rows[0]?.source_sha256||'')}</p>`;
  setupResearchAxes();
  const y=numeric.findIndex(c=>/flame.*(diameter|size|height|length)/i.test(c.label));if(y>=0)$('#researchY').value=String(y+1);
  const requested=researchView.siResult?.selected_measurements?.find(m=>m.path===result.selected_table);
  if(requested){const indices=requested.fields.map(key=>columns.findIndex(c=>c.key===key)).filter(i=>i>0);if(indices.length){$('#researchX').value=String(indices.length>1?indices[0]:0);$('#researchY').value=String(indices.length>1?indices[1]:indices[0]);$('#atlasRunClass').textContent+=' SI-selected fields: '+requested.fields.map(k=>result.columns.find(c=>c.key===k)?.label||k).join(', ')+'. Axes are editable; selection does not establish a causal relationship.';}}
  drawResearch();
}
async function loadResearchRun(path){
  const epoch=researchView.epoch;$('#researchPlot').textContent='Reading recorded samples…';
  const run=researchView.result.runs.find(r=>r.source_path===path);if(!run)return;
  const signal=$('#researchSignal').dataset.path===path?$('#researchSignal').value:run.signals[0];
  const [result,stats]=await Promise.all([jsonFetch('/api/v1/optical/time-series?source_path='+encodeURIComponent(path)+'&signals='+encodeURIComponent(signal)+'&max_points=1000'),jsonFetch('/api/v1/optical/summary?source_path='+encodeURIComponent(path))]);
  if(epoch!==researchView.epoch)return;
  $('#researchMaterialLabel').hidden=true;$('#researchSignalLabel').hidden=false;$('#researchSignal').innerHTML=run.signals.map(s=>`<option value="${plain(s)}">${plain(s.replaceAll('_',' '))}</option>`).join('');$('#researchSignal').value=signal;$('#researchSignal').dataset.path=path;
  $('#atlasRunTitle').textContent=(run.material||researchView.result.group)+' — recorded signal';$('#atlasRunClass').textContent=`${result.downsample.returned_row_count} displayed samples from ${result.downsample.original_row_count} rows. ${result.signal_columns[signal]}`;
  const metric=stats.metrics?.[signal];$('#researchFields').innerHTML=metric?`<details><summary>Signal summary and usable window</summary><pre>${plain(JSON.stringify(metric,null,2))}</pre></details>`:'';
  researchView.dataset={name:result.signal_columns[signal],columns:[{name:'Original source row',unit:'row'},{name:result.signal_columns[signal],unit:''}],rows:result.points.map(p=>[p.source_row,p.values[signal]])};researchView.sourceRows=result.points.map(p=>p.source_row);researchView.runPath=path;researchView.runSignal=signal;
  $('#researchProvenance').innerHTML=`<p>${plain(path)} · ${plain(result.worksheet)}</p><p>SHA-256: ${plain(result.source_sha256)}</p>${stats.warnings.map(w=>`<p>${plain(w)}</p>`).join('')}`;
  setupResearchAxes();$('#researchChartType').value='line';drawResearch();
}
function setupResearchAxes(){const d=researchView.dataset;researchView.selected=[];$('#researchAskPoint').disabled=true;for(const [id,index] of [['researchX',0],['researchY',1]]){$('#'+id).innerHTML=d.columns.map((c,i)=>`<option value="${i}">${plain(c.name)}</option>`).join('');$('#'+id).value=String(Math.min(index,d.columns.length-1));}$('#researchRowLimit').max=d.rows.length;$('#researchRowLimit').value=d.rows.length;$('#researchRowLimit').disabled=!d.rows.length;}
function drawResearch(){const d=researchView.dataset;if(!d)return;researchView.selected=[];$('#researchAskPoint').disabled=true;const count=Number($('#researchRowLimit').value);$('#researchRowCount').textContent=`${count} / ${d.rows.length}`;const slice={...d,rows:d.rows.slice(0,count)};
  StudioCharts.render($('#researchPlot'),slice,$('#researchChartType').value,Number($('#researchX').value),Number($('#researchY').value),0,indices=>{if(!researchView.result)return;researchView.selected=indices.map(i=>researchView.sourceRows[i]);$('#researchAskPoint').disabled=false;},{readout:'#researchPointReadout'});
  $('#researchTable').innerHTML=`<table><thead><tr>${d.columns.map(c=>`<th>${plain(c.name)}</th>`).join('')}</tr></thead><tbody>${slice.rows.map(r=>`<tr>${r.map(v=>`<td>${v===null?'—':plain(v)}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
}
$('#gapForm').onsubmit=e=>{e.preventDefault();loadAtlasGaps(true);};
$('#gapAnalysisMode').onchange=()=>{researchInvalidate();$('#gapForm button[type=submit]').textContent=$('#gapAnalysisMode').value==='si'?'Review with SI':'Check evidence';};
for(const id of ['gapQuestion','gapGoal','atlasGroup'])$('#'+id).addEventListener(id==='gapQuestion'?'input':'change',researchInvalidate);
$('#researchSource').onchange=async()=>{try{const value=$('#researchSource').value;const epoch=++researchView.epoch;researchView.selected=[];$('#researchAskPoint').disabled=true;$('#researchAsk').disabled=true;researchView.history=[];$('#researchSIAnswer').textContent='';if(value.startsWith('run:'))await loadResearchRun(value.slice(4));else{const result=await post('/api/v1/research/explore',{...researchView.request,table:value.slice(6)});if(epoch!==researchView.epoch)return;researchView.result=result;researchView.request.table=result.selected_table;renderResearchFindings(result);renderResearchReports(result);loadResearchTable();}if(epoch===researchView.epoch)$('#researchAsk').disabled=false;}catch(e){researchUnavailable(e.message);}};
$('#researchMaterial').onchange=()=>{const x=$('#researchX').value,y=$('#researchY').value;loadResearchTable();$('#researchX').value=x;$('#researchY').value=y;drawResearch();};
$('#researchSignal').onchange=async()=>{const epoch=++researchView.epoch;researchView.selected=[];researchView.history=[];$('#researchAsk').disabled=true;$('#researchAskPoint').disabled=true;$('#researchSIAnswer').textContent='';try{await loadResearchRun($('#researchSignal').dataset.path);if(epoch===researchView.epoch)$('#researchAsk').disabled=false;}catch(e){researchUnavailable(e.message);}};
for(const id of ['researchX','researchY','researchChartType'])$('#'+id).onchange=drawResearch;
$('#researchRowLimit').oninput=drawResearch;
$('#gapsWithSI').onclick=()=>{researchTab('discussion');$('#researchFollowup').focus();};
$('#gapCreateInvestigation').onclick=()=>saveResearchBrief(null,$('#gapCreateInvestigation'));
$('#exportGapPlan').onclick=()=>{if(researchView.result)download('research-evidence.json',JSON.stringify(researchView.siResult||researchView.result,null,2));};
$('#researchAskPoint').onclick=()=>{if(!researchView.result)return;researchTab('discussion');$('#researchFollowup').value=(researchView.selected.length>30?'Using the first 30 selected source rows, ':'')+'Help interpret the selected source row(s) for this question: '+researchView.result.question;$('#researchFollowup').focus();};
$('#researchAsk').onclick=async()=>{
  if(!researchView.result)return;const question=$('#researchFollowup').value.trim();if(!question){$('#researchSIAnswer').textContent='Enter a question about these findings.';return;}
  const epoch=researchView.epoch;const button=$('#researchAsk');button.disabled=true;$('#researchSIAnswer').textContent='Considering the selected evidence and your research question…';
  try{
    let answer;
    answer=await post('/api/v1/research/interpret',{...researchView.request,followup:question,source_rows:researchView.selected.slice(0,30),...($('#researchSource').value.startsWith('run:')?{run:researchView.runPath,signal:researchView.runSignal}:{}),history:researchView.history});
    if(epoch!==researchView.epoch)return;
    const unavailable=['science_unavailable','evidence_only_fallback','educational_unavailable'].includes(answer.mode);
    $('#researchSIAnswer').innerHTML=unavailable?`<p class="error-box">${plain(answer.service?.reason||'SI could not generate an answer. Your evidence remains available above.')}</p>`:richText(answer.scientific_explanation||answer.answer||'')+['observed_in_source','model_result','unknown_or_limitation'].map(k=>(answer[k]||[]).map(r=>richText(r)).join('')).join('');
    if(answer.sources?.length)$('#researchSIAnswer').insertAdjacentHTML('beforeend',`<details><summary>Sources used in this answer</summary>${answer.sources.map(sourceDetails).join('')}</details>`);
    if(!unavailable){researchView.history.push({role:'user',content:question},{role:'assistant',content:(answer.scientific_explanation||answer.answer||'').slice(0,6000)});researchView.history=researchView.history.slice(-6);}
  }catch(e){if(epoch===researchView.epoch)$('#researchSIAnswer').textContent=e.message;}finally{if(epoch===researchView.epoch)button.disabled=false;}
};
document.addEventListener('page-changed',e=>{if(e.detail.page==='atlas'){setAtlasGroups();if($('#gapQuestion').value&&!researchView.result)loadAtlasGaps();}});

$('#gapBrowseDatasets').onclick=()=>{navigate('mission');ArchiveBrowser.openGroup($('#atlasGroup').value);};
