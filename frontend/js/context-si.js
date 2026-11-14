/* Persistent discussion with explicit, frozen evidence scope. */
const ContextSI=(()=>{
 const state={context:null,history:[],epoch:0};
 const dock=document.createElement('aside');dock.className='context-si';dock.hidden=true;dock.setAttribute('aria-label','Contextual scientific intelligence');
 dock.innerHTML='<header><strong>SI · Evidence discussion</strong><button type="button" id="contextSIClose" aria-label="Close SI panel">×</button></header><p id="contextSIScope"></p><div id="contextSIAnswer" class="evidence-prose" aria-live="polite"></div><label for="contextSIQuestion">Your question</label><textarea id="contextSIQuestion" rows="3" maxlength="2000"></textarea><button id="contextSIAsk" type="button" class="button-primary">Ask SI</button>';
 document.body.append(dock);
 const actions=document.createElement('div');actions.className='discovery-actions';actions.innerHTML='<button id="archiveSISummary" type="button" class="button-secondary">SI overview of this table</button><button id="archiveSIRow" type="button" class="button-text">Ask SI about selected row</button>';
 $('#datasetViewer').append(actions);
 function open(row=false){const v=ArchiveBrowser.view;if(!v.page)return;if(row&&!v.selected){$('#datasetStatus').textContent='Select a source-row number first, then ask SI.';return;}
 const context={source_path:v.page.source_path,offset:v.offset,query:$('#datasetQuery').value,...(row?{source_row:v.selected.source_row}:{})};
 if(JSON.stringify(context)!==JSON.stringify(state.context)){state.epoch++;state.context=context;state.history=[];$('#contextSIAnswer').textContent='';}
 $('#contextSIScope').textContent=context.source_path+(row?' · source row '+context.source_row:' · dataset metadata and bounded row examples; not a full statistical analysis');
 $('#contextSIQuestion').value=row?'Explain this row and which comparisons it could support.':'Give a high-level overview of what this table records, the meaning of its columns and useful research questions. Distinguish the sampled rows from the full dataset.';dock.hidden=false;$('#contextSIAsk').disabled=false;$('#contextSIQuestion').focus();
 }
 $('#archiveSISummary').onclick=()=>open(false);$('#archiveSIRow').onclick=()=>open(true);$('#contextSIClose').onclick=()=>dock.hidden=true;
 $('#contextSIAsk').onclick=async()=>{if(!state.context)return;const epoch=++state.epoch,q=$('#contextSIQuestion').value.trim();$('#contextSIAsk').disabled=true;$('#contextSIAnswer').textContent='Reading the selected source context…';try{const r=await post('/api/v1/archive/interpret',{...state.context,question:q,history:state.history});if(epoch!==state.epoch)return;const unavailable=['science_unavailable','evidence_only_fallback'].includes(r.mode);$('#contextSIAnswer').innerHTML=unavailable?`<p>${plain(r.service?.reason||'SI is unavailable. Retry shortly.')}</p>`:richText(r.scientific_explanation||r.answer||'')+['observed_in_source','model_result','unknown_or_limitation'].map(k=>(r[k]||[]).map(richText).join('')).join('');$('#contextSIAnswer').insertAdjacentHTML('beforeend',`<p class="micro">${plain(r.table_scope)}</p>${r.sources?.length?`<details><summary>Sources</summary>${r.sources.map(sourceDetails).join('')}</details>`:''}`);if(!unavailable){state.history.push({role:'user',content:q},{role:'assistant',content:(r.scientific_explanation||'').slice(0,6000)});state.history=state.history.slice(-6);}}catch(e){if(epoch===state.epoch)$('#contextSIAnswer').textContent=e.message;}finally{if(epoch===state.epoch)$('#contextSIAsk').disabled=false;}};
 return {open,state};
})();
