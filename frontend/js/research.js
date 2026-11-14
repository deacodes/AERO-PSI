/* Actual measurements and contextual SI; never a fixed three-tool plan. */
const researchView={result:null,dataset:null,sourceRows:[],selected:[],epoch:0,history:[],request:null,tab:'gaps'};
function researchTab(name){researchView.tab=name;for(const tab of ['measurements','gaps','reports','discussion'])$('#research-'+tab).hidden=tab!==name;$$('[data-research-tab]').forEach(b=>b.setAttribute('aria-current',b.dataset.researchTab===name?'page':'false'));}
$$('[data-research-tab]').forEach(b=>b.onclick=()=>researchTab(b.dataset.researchTab));
function researchUnavailable(message){$('#gapStatus').textContent=message;}
function researchInvalidate(){researchView.epoch++;$('#gapForm button[type=submit]').disabled=false;researchView.result=null;researchView.selected=[];researchView.history=[];$('#researchSIAnswer').textContent='';['gapsWithSI','exportGapPlan','gapCreateInvestigation','researchAskPoint'].forEach(id=>$('#'+id).disabled=true);$('#gapStatus').textContent='Question or investigation changed. Explore evidence again to update the findings.';$('#researchAsk').disabled=true;}
loadAtlasGaps=async function(){
  const question=$('#gapQuestion').value.trim();if(!question)return;
  const epoch=++researchView.epoch;const request={question,goal:$('#gapGoal').value,group:$('#atlasGroup').value||undefined};
  const button=$('#gapForm button[type=submit]');button.disabled=true;$('#gapStatus').textContent='Reading experiment tables and finding relevant report passages…';
  researchView.result=null;researchView.selected=[];researchView.history=[];$('#researchSIAnswer').textContent='';
  ['gapsWithSI','gapCreateInvestigation','exportGapPlan','researchAsk','researchAskPoint'].forEach(id=>$('#'+id).disabled=true);
  try{
    const result=await post('/api/v1/research/explore',request);if(epoch!==researchView.epoch)return;
    researchView.result=result;researchView.request={...request,group:result.group,table:result.selected_table};discovery.plan=result;
    $('#atlasGroup').innerHTML='<option value="">Find relevant investigations</option>'+result.groups.map(g=>`<option value="${plain(g.group)}">${plain(g.group)}</option>`).join('');$('#atlasGroup').value=result.group;
    $('#gapStatus').textContent=`${result.group} · ${result.overview.group_records} experiment-table rows · ${result.runs.length} time-series files · ${result.passages.length} report passages`;
    $('#researchOverview').innerHTML=`<h2>${plain(result.question)}</h2><p>${plain(result.overview.explanation)}</p>${(result.overview.response_summary||[]).map(s=>`<p><strong>${s.numeric_rows} of ${s.total_rows} rows</strong> supply a numeric ${plain(s.measurement)}: ${formatNumber(s.minimum)} to ${formatNumber(s.maximum)}. Other rows may contain missing values or nonnumeric annotations.</p>`).join('')}`;
    $('#researchSource').innerHTML=result.tables.map(t=>`<option value="table:${plain(t.path)}">${plain(t.path.split('/').at(-1))} · ${t.row_count} rows</option>`).join('')+result.runs.map(r=>`<option value="run:${plain(r.source_path)}">${plain(r.material||'Material unspecified')} · ${plain(r.source_path.split('/').at(-1))}</option>`).join('');
    if(result.selected_table)$('#researchSource').value='table:'+result.selected_table;
    renderResearchFindings(result);renderResearchReports(result);
    if(result.selected_table)loadResearchTable();else if(result.runs.length)await loadResearchRun(result.runs[0].source_path);else clearResearchData('This investigation has report evidence but no supplied experiment table or imported time series. Open Report findings to inspect the available science.');
    ['gapsWithSI','gapCreateInvestigation','exportGapPlan','researchAsk'].forEach(id=>$('#'+id).disabled=false);
    document.dispatchEvent(new CustomEvent('research-loaded'));
  }catch(error){if(epoch===researchView.epoch){researchUnavailable(error.message);clearResearchData('Evidence could not be loaded. Retry the question.');}}
  finally{if(epoch===researchView.epoch)button.disabled=false;}
};
function renderResearchFindings(result){
  $('#atlasGaps').innerHTML=result.findings.map(f=>`<article class="research-finding"><h3>${plain(f.title)}</h3><p class="research-state">${{recorded:'Recorded values available',review_report:'Report evidence to examine',measurement_needed:'Measurement to establish'}[f.state]}</p><p>${plain(f.finding)}</p><p><strong>Next action:</strong> ${plain(f.next_action)}</p><button type="button" class="button-secondary" data-develop-finding="${plain(f.key)}">Develop this investigation</button>${f.sources.length?`<details><summary>Supporting source records</summary>${f.sources.map(sourceDetails).join('')}</details>`:''}${f.passages.length?`<button type="button" class="button-text" data-report-finding="${plain(f.key)}">Read relevant report passages</button>`:''}</article>`).join('')||'<p>No fixed measurement requirements fit this question. Use the observed fields and report findings to define your response variable and comparison; the experiment builder can develop a general research method.</p>';
  $$('[data-develop-finding]').forEach(b=>b.onclick=()=>{const f=result.findings.find(f=>f.key===b.dataset.developFinding);Studio.compose(`${result.question}\n\nFocus: ${f.title}. ${f.next_action}`,{group:result.group});});
  $$('[data-report-finding]').forEach(b=>b.onclick=()=>{researchTab('reports');const f=result.findings.find(f=>f.key===b.dataset.reportFinding);const entry=$$('[data-report-id]').find(e=>f.passages.includes(e.dataset.reportId));if(entry){entry.open=true;entry.scrollIntoView({block:'center'});}});
}
function renderResearchReports(result){$('#researchReports').innerHTML=result.passages.map(p=>`<details data-report-id="${plain(p.id)}"><summary>${plain(p.title||p.source_path.split('/').at(-1))} · ${plain(p.source_range)}</summary>${reviewedSourceContent(p)}</details>`).join('')||'<p>No matching passages were retrieved for this question and investigation. Try another scientific term or choose a different investigation.</p>';}
function clearResearchData(message){researchView.selected=[];$('#researchAskPoint').disabled=true;researchView.dataset=null;researchView.sourceRows=[];$('#researchPlot').innerHTML=`<p>${plain(message)}</p>`;$('#researchTable').textContent='';$('#researchFields').textContent='';$('#atlasRunTitle').textContent='Report-based evidence';$('#atlasRunClass').textContent=message;}
function loadResearchTable(){
  const result=researchView.result;$('#researchSignalLabel').hidden=true;$('#researchMaterialLabel').hidden=false;
  const prior=$('#researchMaterial').value;const materials=[...new Set(result.rows.map(r=>String(r.values.material_or_fuel||'')).filter(Boolean))];$('#researchMaterial').innerHTML='<option value="">All materials</option>'+materials.map(m=>`<option value="${plain(m)}">${plain(m)}</option>`).join('');if(materials.includes(prior))$('#researchMaterial').value=prior;
  const selectedRows=result.rows.filter(r=>!$('#researchMaterial').value||r.values.material_or_fuel===$('#researchMaterial').value);
  const numeric=result.columns.filter(c=>c.numeric_count>0);
  $('#atlasRunTitle').textContent=`${result.group} experiment measurements`;
  $('#atlasRunClass').textContent=`${selectedRows.length} of ${result.rows.length} populated rows from ${result.selected_table.split('/').at(-1)}. Axes retain the source column labels and units.`;
  $('#researchFields').innerHTML=numeric.map(c=>`<div><strong>${plain(c.label)}</strong><span>${c.numeric_count} numeric values in full table · ${formatNumber(c.minimum)} to ${formatNumber(c.maximum)}</span></div>`).join('')||'<p>This table has descriptions and identifiers but no numeric measurements.</p>';
  const columns=[{name:'Source row',unit:'row'},...numeric.map(c=>({name:c.label,unit:''}))];
  const rows=selectedRows.map(row=>[row.source_row,...numeric.map(c=>{const raw=row.values[c.key];if(raw==null||!String(raw).trim())return null;const n=Number(raw);return Number.isFinite(n)?n:null;})]);
  researchView.dataset={name:result.group+' — source table',columns,rows};researchView.sourceRows=selectedRows.map(r=>r.source_row);
  $('#researchProvenance').innerHTML=`<p>${plain(result.selected_table)}</p><p>${plain(result.scope)}</p><p>SHA-256: ${plain(result.rows[0]?.source_sha256||'')}</p>`;
  setupResearchAxes();
  const y=numeric.findIndex(c=>/flame.*(diameter|size|height|length)/i.test(c.label));if(y>=0)$('#researchY').value=String(y+1);
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
$('#gapForm').onsubmit=e=>{e.preventDefault();loadAtlasGaps();};
for(const id of ['gapQuestion','gapGoal','atlasGroup'])$('#'+id).addEventListener(id==='gapQuestion'?'input':'change',researchInvalidate);
$('#researchSource').onchange=async()=>{try{const value=$('#researchSource').value;const epoch=++researchView.epoch;researchView.selected=[];$('#researchAskPoint').disabled=true;$('#researchAsk').disabled=true;researchView.history=[];$('#researchSIAnswer').textContent='';if(value.startsWith('run:'))await loadResearchRun(value.slice(4));else{const result=await post('/api/v1/research/explore',{...researchView.request,table:value.slice(6)});if(epoch!==researchView.epoch)return;researchView.result=result;researchView.request.table=result.selected_table;loadResearchTable();}if(epoch===researchView.epoch)$('#researchAsk').disabled=false;}catch(e){researchUnavailable(e.message);}};
$('#researchMaterial').onchange=()=>{const x=$('#researchX').value,y=$('#researchY').value;loadResearchTable();$('#researchX').value=x;$('#researchY').value=y;drawResearch();};
$('#researchSignal').onchange=async()=>{const epoch=++researchView.epoch;researchView.selected=[];researchView.history=[];$('#researchAsk').disabled=true;$('#researchAskPoint').disabled=true;$('#researchSIAnswer').textContent='';try{await loadResearchRun($('#researchSignal').dataset.path);if(epoch===researchView.epoch)$('#researchAsk').disabled=false;}catch(e){researchUnavailable(e.message);}};
for(const id of ['researchX','researchY','researchChartType'])$('#'+id).onchange=drawResearch;
$('#researchRowLimit').oninput=drawResearch;
$('#gapsWithSI').onclick=()=>{researchTab('discussion');$('#researchFollowup').focus();};
$('#gapCreateInvestigation').onclick=()=>{if(researchView.result)Studio.compose(researchView.result.question,{group:researchView.result.group});};
$('#exportGapPlan').onclick=()=>{if(researchView.result)download('research-evidence.json',JSON.stringify(researchView.result,null,2));};
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
