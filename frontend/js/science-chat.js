const explainSlice=document.createElement('button');explainSlice.type='button';explainSlice.className='button-text';explainSlice.textContent='Explain this time slice with SI';explainSlice.onclick=()=>{if(!state.currentCoag){$('#distributionReadout').textContent='Run a scenario first.';return;}askSIAboutPoint('coagulation',Number($('#distributionTime').value));};$('.distribution-stage').append(explainSlice);

$$('.nav-button').forEach(button=>button.setAttribute('aria-label',$('.nav-copy',button).textContent));
$$('.settings-button').forEach(button=>{if(!button.hasAttribute('aria-label'))button.setAttribute('aria-label',button.textContent.trim());});
// Existing graph-point explanations share the same safe Markdown/math renderer.
formatEvidenceText = item => richText(item).replace(/^<p>/,'').replace(/<\/p>\s*$/,'');
// Direct science conversation is independent of the optional tool-planning workflow.
const scienceConversation={messages:[],turns:[],epoch:0,context:null};
function clearScienceConversation(){scienceConversation.epoch++;scienceConversation.context=null;if($('#scienceContext'))$('#scienceContext').hidden=true;$('#answerMode').disabled=false;scienceConversation.messages=[];scienceConversation.turns=[];state.copilotSources=[];$('#sourceSearch').value='';$('#scienceConversationHistory').textContent='';$('#scienceConversationStatus').textContent='New conversation.';$('#copilotAnswer').innerHTML='<p>Ask a question to begin.</p>';$('#scienceCurrentQuestion').textContent='';$('#copilotQuestion').value='';$('#askCopilot').disabled=false;$('#askCopilot').textContent='Ask SI';renderSourceTrail([]);document.dispatchEvent(new CustomEvent('si-scope-changed'));}
$('#clearScienceConversation').onclick=clearScienceConversation;
$('#answerMode').addEventListener('change',()=>{const context=scienceConversation.context;clearScienceConversation();if(context){scienceConversation.context=context;$('#scienceContext').hidden=false;}document.dispatchEvent(new CustomEvent('si-scope-changed'));});
$('#copilotQuestion').addEventListener('keydown',e=>{if(e.key==='Enter'&&(e.ctrlKey||e.metaKey)){e.preventDefault();if(!$('#askCopilot').disabled)askScienceQuestion();}});
async function askScienceQuestion(){
  const question=$('#copilotQuestion').value.trim();if(!question)return;
  const epoch=++scienceConversation.epoch;const button=$('#askCopilot');button.disabled=true;button.textContent='Thinking…';
  $('#scienceConversationHistory').innerHTML=scienceConversation.turns.map(t=>`<article class="science-prior-turn"><div class="science-user-message"><strong>You</strong><p>${escapeHTML(t.question)}</p></div><div class="evidence-prose"><strong>SI</strong>${richText(t.answer)}</div>${t.sources?.length?`<details><summary>Sources for this answer</summary>${t.sources.map(source=>`<p>${escapeHTML(source.title||source.source_path||source.id)}</p>`).join('')}</details>`:''}</article>`).join('');
  $('#scienceCurrentQuestion').textContent=question;$('#scienceConversationStatus').textContent='Thinking…';$('#copilotAnswer').innerHTML='<p class="execution-pending">Thinking…</p>';
  try{
    const context=scienceConversation.context;
    const answer=context?await context.request(question,scienceConversation.messages.slice(-8),$('#answerMode').value):await post('/api/v1/copilot',{question,mode:$('#answerMode').value,history:scienceConversation.messages.slice(-8)});
    if(epoch!==scienceConversation.epoch)return;renderCopilot(answer);
    const unavailable=['science_unavailable','educational_unavailable','evidence_only_fallback'].includes(answer.mode);
    $('#scienceConversationStatus').textContent=unavailable?'SI is unavailable.':'Ask a follow-up.';
    if(!unavailable){const text=[answer.scientific_explanation||answer.answer,...(answer.observed_in_source||[]),...(answer.model_result||[]),...(answer.unknown_or_limitation||[])].filter(Boolean).map(normalizeText).join('\n\n');
      if(text){scienceConversation.messages.push({role:'user',content:question},{role:'assistant',content:text.slice(0,8000)});scienceConversation.messages=scienceConversation.messages.slice(-8);scienceConversation.turns.push({question,answer:text,sources:answer.sources||[]});$('#copilotQuestion').value='';$('#copilotQuestion').placeholder='Ask a follow-up about this answer…';scienceConversation.turns=scienceConversation.turns.slice(-4);}
    }
  }catch(error){if(epoch===scienceConversation.epoch){$('#copilotAnswer').innerHTML=`<div class="error-box"><strong>Could not reach SI</strong><p>${escapeHTML(error.message)}</p></div>`;$('#scienceConversationStatus').textContent='No generated answer was returned. Check the connection and retry.';}}
  finally{if(epoch===scienceConversation.epoch){button.disabled=false;button.textContent='Ask SI';}}
}
