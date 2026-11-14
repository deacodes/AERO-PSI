/* Archive questions open in the shared SI workspace. */
const ContextSI=(()=>{
 const actions=document.createElement('div');actions.className='discovery-actions';
 actions.innerHTML='<button id="archiveSISummary" type="button" class="button-secondary">Summarize in SI</button><button id="archiveSIRow" type="button" class="button-text">Discuss selected row</button>';
 $('#datasetSIActions').append(actions);
 function open(row=false){const v=ArchiveBrowser.view;if(!v.page)return;
  if(row&&!v.selected){$('#datasetStatus').textContent='Select a row first.';return;}
  const context={source_path:v.page.source_path,offset:v.offset,query:$('#datasetQuery').value,...(row?{source_row:v.selected.source_row}:{})};
  ScienceContext.open(context.source_path.split('/').at(-1)+(row?' · row '+context.source_row:''),row?'Explain this row and which comparisons it supports.':'Summarize this table and its columns. Distinguish the sampled rows from the full dataset.',
   (question,history,mode)=>post('/api/v1/archive/interpret',{...context,question,history,mode}));
 }
 $('#archiveSISummary').onclick=()=>open();$('#archiveSIRow').onclick=()=>open(true);
 return {open};
})();
