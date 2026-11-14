/* Model interpretation shares the SI page; scenario linking stays in the lab. */
const ModelSI=(()=>{
 const view={kind:null,inputs:null};
 const panel=document.createElement('section');panel.id='modelDiscussion';panel.className='research-panel';panel.hidden=true;$('#page-lab').append(panel);
 function prepare(kind){const input=kind==='scattering'?workspace.optics?.request:state.currentCoag?.payload;if(!input)return false;
  view.kind=kind;view.inputs=structuredClone(input);return true;
 }
 function link(kind){if(!prepare(kind))return;$('#lab-'+(kind==='scattering'?'scattering':'coagulation')).append(panel);panel.hidden=false;$('#journeyModelReason').focus();}
 function open(kind){if(!prepare(kind))return;const context={model:kind,inputs:structuredClone(view.inputs)};
  ScienceContext.open(kind==='scattering'?'Scattering scenario':'Coagulation scenario','Explain this result and the assumptions that matter most.',(question,history,mode)=>post('/api/v1/si/interpret-model',{...context,question,history,mode}),{model_context:context});
 }
 for(const event of ['model-updated','scenario-computed'])document.addEventListener(event,()=>panel.hidden=true);
 return {open,link,view};
})();
