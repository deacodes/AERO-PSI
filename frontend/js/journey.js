/* A saved investigation anchors navigation. Stored IDs are not trusted as evidence. */
const Journey=(()=>{
 let record=null;
 const key='aeropsi.activeInvestigation';
 function remember(id){try{if(id)sessionStorage.setItem(key,id);else sessionStorage.removeItem(key);}catch{}}
 const panel=document.createElement('section');panel.id='researchJourney';panel.className='research-journey';panel.hidden=true;
 panel.innerHTML='<div><strong id="journeyTitle"></strong><p id="journeyScope"></p></div><nav aria-label="Active research journey"><button type="button" id="journeyEvidence" class="button-text">Review evidence</button><button type="button" id="journeyModels" class="button-text">Explore models</button><button type="button" id="journeyStudio" class="button-secondary">Return to investigation</button><button type="button" id="journeyClear" class="button-text">End active context</button></nav><p id="journeyStatus" role="status"></p>';
 document.querySelector('main').prepend(panel);
 const save=document.createElement('div');save.className='model-save-context';save.hidden=true;save.id='journeyModelSave';
 save.innerHTML='<label for="journeyModelReason">How does this scenario help your research question?</label><textarea id="journeyModelReason" rows="2" maxlength="2000" placeholder="State the assumption or comparison you are exploring."></textarea><button id="journeyAttach" type="button" class="button-secondary">Save computed scenario to investigation</button><p id="journeyAttachStatus" role="status">This saves explicit inputs and a backend-recomputed result; it does not fit the model to NASA measurements.</p>';
 $('#modelDiscussion').append(save);const back=document.createElement('button');back.type='button';back.className='button-text';back.textContent='Return to investigation';back.onclick=()=>move(async()=>{await Studio.persist();navigate('studio',{id:record.id});});save.append(back);
 const modelButtons=[];
 for(const [selector,kind] of [['#interpretScenario','coagulation'],['#interpretScattering','scattering']]){
  const button=document.createElement('button');button.type='button';button.className='button-secondary';button.textContent='Link scenario to investigation';button.dataset.linkModel=kind;button.hidden=true;
  $(selector).after(button);modelButtons.push(button);
  button.onclick=()=>ModelSI.link(kind);
 }
 function render(){
  document.body.classList.toggle('has-research-journey',Boolean(record));
  modelButtons.forEach(b=>{b.hidden=!record;b.disabled=b.dataset.linkModel==='scattering'?!workspace.optics:!state.currentCoag;});
  panel.hidden=true;save.hidden=!record;
  if(!record)return;
  $('#journeyTitle').textContent=record.content.question;
  const c=record.research_context;
  $('#journeyScope').textContent=(c?`${c.group} · saved evidence assessment`:'Saved investigation')+` · ${(record.model_links||[]).length} linked model scenarios`+(c&&c.question!==record.content.question?' · Question changed: reassess the saved evidence.':'');
  $('#journeyEvidence').disabled=!c;
  if(pageFromLocation()==='studio'&&Studio.view.record?.id===record.id){
   let linked=$('#studioLinkedModels');if(!linked){linked=document.createElement('section');linked.id='studioLinkedModels';$('#studio-sources').prepend(linked);}
   linked.innerHTML=(record.model_links||[]).length?'<h3>Models linked to this question</h3>'+record.model_links.map(m=>`<details><summary>${plain(m.model)} · ${plain(m.reason)}</summary><p>${plain(m.classification)}</p>${m.question!==record.content.question?'<p>Research question has changed since this scenario was attached. Review its relevance.</p>':''}<pre>${plain(JSON.stringify(m.inputs,null,2))}</pre><p>Recomputed output: ${plain(m.source_id)}</p></details>`).join(''):'';
  }
 }
 async function move(fn){try{await fn();}catch(e){$('#journeyStatus').textContent=e.message;}}
 function set(r){record=r;remember(r.id);render();}
 $('#journeyStudio').onclick=()=>move(async()=>{await Studio.persist();navigate('studio',{id:record.id});});
 $('#journeyModels').onclick=()=>move(async()=>{await Studio.persist();navigate('lab');$('#journeyStatus').textContent='Models use explicit assumptions. After computing, choose Link scenario to investigation. Models remain optional; they do not predict flame dimensions.';});
 $('#journeyEvidence').onclick=()=>move(async()=>{await Studio.persist();const c=record.research_context;setAtlasGroups();$('#gapQuestion').value=c.question;$('#gapGoal').value=c.goal;$('#atlasGroup').value=c.group;researchInvalidate();researchView.pendingSource=c.source_path||c.table;navigate('atlas');});
 $('#journeyClear').onclick=()=>{record=null;remember(null);render();};
 $('#journeyAttach').onclick=async()=>{
  if(!record||!ModelSI.view.inputs)return;const b=$('#journeyAttach');b.disabled=true;
  $('#journeyAttachStatus').textContent='Recomputing and saving this scenario…';
  try{await Studio.persist();if(Studio.view.record?.id===record.id)record=Studio.view.record;
    const updated=await post('/api/v1/studio/attach-model',{id:record.id,revision:record.revision,model_context:{model:ModelSI.view.kind,inputs:ModelSI.view.inputs},reason:$('#journeyModelReason').value});
    if(Studio.view.record?.id===updated.id)Studio.view.record=updated;set(updated);
    $('#journeyAttachStatus').textContent='Saved with inputs, recomputed output and your rationale. Return to the investigation to review its sources.';
  }catch(e){$('#journeyAttachStatus').textContent=e.message;}finally{b.disabled=false;}
 };
 document.addEventListener('studio-record-rendered',()=>set(Studio.view.record));
 document.addEventListener('page-changed',render);
 for(const event of ['model-updated','scenario-computed'])document.addEventListener(event,render);
 try{const id=sessionStorage.getItem(key);if(id&&/^[a-f0-9]{32}$/.test(id))jsonFetch('/api/v1/studio/record?id='+id).then(r=>{if(!record)set(r);}).catch(()=>remember(null));}catch{}
 return {set,get record(){return record;}};
})();
