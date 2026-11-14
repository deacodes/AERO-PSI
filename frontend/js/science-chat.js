const explainSlice=document.createElement('button');explainSlice.type='button';explainSlice.className='button-text';explainSlice.textContent='Explain this time slice with SI';explainSlice.onclick=()=>{if(!state.currentCoag){$('#distributionReadout').textContent='Run a scenario first.';return;}askSIAboutPoint('coagulation',Number($('#distributionTime').value));$('#coagPointAnswer').scrollIntoView({block:'center',behavior:document.body.classList.contains('reduced-motion')?'auto':'smooth'});};$('.distribution-stage').append(explainSlice);

$$('.nav-button').forEach(button=>button.setAttribute('aria-label',$('.nav-copy',button).textContent));
$$('.settings-button').forEach(button=>{if(!button.hasAttribute('aria-label'))button.setAttribute('aria-label',button.textContent.trim());});
// Existing graph-point explanations share the same safe Markdown/math renderer.
formatEvidenceText = item => richText(item).replace(/^<p>/,'').replace(/<\/p>\s*$/,'');
// Direct science conversation is independent of the optional tool-planning workflow.
const scienceConversation={messages:[],turns:[],epoch:0};
function clearScienceConversation(){scienceConversation.epoch++;scienceConversation.messages=[];scienceConversation.turns=[];state.copilotSources=[];$('#sourceSearch').value='';$('#scienceConversationHistory').textContent='';$('#scienceConversationStatus').textContent='New conversation. Ask a science question directly.';$('#copilotAnswer').innerHTML='<p>Explain a mechanism, compare theories, explore a hypothesis, or interpret your evidence.</p>';$('#askCopilot').disabled=false;$('#askCopilot').textContent='Ask SI';renderSourceTrail([]);}
$('#clearScienceConversation').onclick=clearScienceConversation;
$('#answerMode').addEventListener('change',clearScienceConversation);
$('#copilotQuestion').addEventListener('keydown',e=>{if(e.key==='Enter'&&(e.ctrlKey||e.metaKey)){e.preventDefault();if(!$('#askCopilot').disabled)askScienceQuestion();}});
async function askScienceQuestion(){
  const question=$('#copilotQuestion').value.trim();if(!question)return;
  const epoch=++scienceConversation.epoch;const button=$('#askCopilot');button.disabled=true;button.textContent='Thinking…';
  $('#scienceConversationHistory').innerHTML=scienceConversation.turns.map(t=>`<details class="science-prior-turn"><summary>${escapeHTML(t.question)}</summary><div class="evidence-prose">${richText(t.answer)}</div></details>`).join('');
  $('#scienceConversationStatus').textContent='Preparing a scientific answer…';$('#copilotAnswer').innerHTML='<p class="execution-pending">Considering the question and relevant context. General science does not require an archive match.</p>';
  try{
    const answer=await post('/api/v1/copilot',{question,mode:$('#answerMode').value,history:scienceConversation.messages.slice(-8)});
    if(epoch!==scienceConversation.epoch)return;renderCopilot(answer);
    const unavailable=['science_unavailable','educational_unavailable','evidence_only_fallback'].includes(answer.mode);
    $('#scienceConversationStatus').textContent=unavailable?'The service did not generate an answer. The reason is shown below.':`Answered: “${question}” · You can ask a follow-up.`;
    if(!unavailable){const text=answer.scientific_explanation||answer.answer||[...(answer.observed_in_source||[]),...(answer.model_result||[])].map(normalizeText).join('\n\n');
      if(text){scienceConversation.messages.push({role:'user',content:question},{role:'assistant',content:text.slice(0,8000)});scienceConversation.messages=scienceConversation.messages.slice(-8);scienceConversation.turns.push({question,answer:text});scienceConversation.turns=scienceConversation.turns.slice(-4);}
    }
  }catch(error){if(epoch===scienceConversation.epoch){$('#copilotAnswer').innerHTML=`<div class="error-box"><strong>Could not reach SI</strong><p>${escapeHTML(error.message)}</p></div>`;$('#scienceConversationStatus').textContent='No generated answer was returned. Check the connection and retry.';}}
  finally{if(epoch===scienceConversation.epoch){button.disabled=false;button.textContent='Ask SI';}}
}
