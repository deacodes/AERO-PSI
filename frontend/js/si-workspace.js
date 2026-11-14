/* One conversation surface, with frozen context supplied by its originating page. */
const ScienceContext=(()=>{
 const scope=document.createElement('div');scope.id='scienceContext';scope.hidden=true;scope.className='science-conversation-controls';
 scope.innerHTML='<span id="scienceContextLabel"></span><button type="button" id="scienceContextPlan" class="button-text" hidden>Create investigation</button><button type="button" id="scienceContextClear" class="button-text">Clear context</button>';
 $('#copilotQuestion').closest('.prompt-row').before(scope);
 $('#scienceContextClear').onclick=clearScienceConversation;
 function open(label,question,request,planContext=null){clearScienceConversation();scienceConversation.context={label,request};$('#scienceContextPlan').hidden=!planContext;$('#scienceContextPlan').onclick=()=>Studio.compose($('#copilotQuestion').value,planContext||{});scope.hidden=false;$('#scienceContextLabel').textContent=label;$('#answerMode').disabled=false;$('#copilotQuestion').value=question;navigate('evidence');$('#copilotQuestion').focus();document.dispatchEvent(new CustomEvent('si-scope-changed'));}
 function show(label,answer){open(label,'',null);renderCopilot(answer);scienceConversation.context=null;$('#answerMode').disabled=false;$('#scienceConversationStatus').textContent='Saved interpretation.';}
 function research(question){if(!researchView.result)return;
  const payload=structuredClone({...researchView.request,source_rows:researchView.selected.slice(0,30),...($('#researchSource').value.startsWith('run:')?{run:researchView.runPath,signal:researchView.runSignal}:{})});
  open(researchView.result.group+' · '+researchView.result.question,question||'What can this evidence establish, and what should I investigate next?',(followup,history,mode)=>post('/api/v1/research/interpret',{...payload,followup,history,mode}));
 }
 // Replace the local discussion surface with a route to the shared conversation.
 $('[data-research-tab="discussion"]').onclick=()=>research();
 $('#gapsWithSI').onclick=()=>research();$('#researchAskPoint').onclick=()=>research('Explain the selected source rows and their limitations.');
 $('#researchAsk').onclick=()=>research($('#researchFollowup').value);
 document.addEventListener('click',e=>{const b=e.target.closest('[data-ask-finding]');if(!b)return;e.preventDefault();e.stopImmediatePropagation();const f=researchView.result?.assessment.actions.find(a=>a.key===b.dataset.askFinding);if(f)research(`For “${researchView.result.question}”, explain why ${f.title.toLowerCase()} matters and how to resolve it.`);},true);
 // Ranking also opens SI with the exact question; the backend rechecks its evidence.
 $('#rankWithSI').onclick=()=>{const r=discovery.ranking;if(!r||!discovery.rankCurrent)return;const payload={question:r.question,goal:r.goal,group:r.items[0]?.group};open('Archive ranking',`Which evidence best supports: ${r.question}?`,(followup,history,mode)=>post('/api/v1/research/interpret',{...payload,followup,history,mode}));};
 return {open,show,research};
})();
