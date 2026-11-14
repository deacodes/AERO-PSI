renderCopilot=function(answer){
  const sections=[];
  const scope=answer.information_scope;if(scope){const labels={auto:'Evidence + general science',evidence:'Project evidence only',explain:'General scientific knowledge'};sections.push(`<p class="answer-origin"><strong>${escapeHTML(labels[scope.requested]||'Scientific answer')}</strong> · ${scope.general_science_included&&scope.source_claims_included?'Includes scientific background and cited findings':scope.source_claims_included?'Includes cited findings':scope.general_science_included?'Includes general scientific reasoning':'No generated findings'}.</p>`);}const unavailable=['science_unavailable','educational_unavailable','evidence_only_fallback'].includes(answer.mode);
  if(unavailable)sections.push(`<div class="error-box" role="status"><strong>AI answer unavailable</strong><p>${escapeHTML(answer.service?.reason || answer.unknown_or_limitation?.[0] || 'No generated answer was returned.')}</p><p>Retrieved records below are source material, not an AI scientific answer.</p></div>`);

  if(answer.scientific_explanation)sections.push(`<section class="answer-section"><h3>General scientific reasoning</h3><div class="evidence-prose">${richText(answer.scientific_explanation)}</div></section>`);
  else if(answer.answer&&!unavailable)sections.push(`<section class="answer-section"><h3>General scientific reasoning</h3><div class="evidence-prose">${richText(answer.answer)}</div></section>`);
  for(const [key,title] of [['observed_in_source','Cited evidence'],['model_result','Model calculations'],['unknown_or_limitation','What remains uncertain']]){
    if(answer[key]?.length&&!(unavailable&&key==='unknown_or_limitation'))sections.push(`<section class="answer-section"><h3>${title}</h3>${answer[key].map(v=>`<div class="evidence-prose">${richText(v)}${v.source_ids?.length?`<p class="micro">Citations: ${v.source_ids.map(escapeHTML).join(', ')}</p>`:''}</div>`).join('')}</section>`);
  }
  $('#copilotAnswer').innerHTML=sections.join('')||'<p>No answer was returned. Try again or ask a more specific question.</p>';state.copilotSources=answer.sources||[];$('#sourceSearch').disabled=!state.copilotSources.length;renderSourceTrail(state.copilotSources);
};
function referenceLink(source){
  if(!source.source_url)return '';
  try{const url=new URL(source.source_url);if(url.protocol!=='https:'||url.username||url.password)return '';return `<p><a href="${escapeHTML(url.href)}" target="_blank" rel="noopener noreferrer">Open ${escapeHTML(url.hostname)} reference</a> <span class="micro">Consulted ${escapeHTML(source.accessed_on||'date unavailable')}</span></p>`;}catch{return '';}
}
function reviewedSourceContent(source){
  const equations=(source.equations||[]).map(e=>richText(`\\[${e}\\]`)).join('');
  const anchors=(source.anchors||[]).map(a=>`<p class="micro">${escapeHTML(a.kind)} ${escapeHTML(a.number)}</p><blockquote>${escapeHTML(a.quote)}</blockquote>`).join('');
  const passages=source.supporting_source_ids?.length?`<button type="button" class="button-text" data-source-passages="${escapeHTML(JSON.stringify(source.supporting_source_ids))}">Read cited source passages</button><div class="source-passages"></div>`:'';
  return `<p class="micro">${escapeHTML(source.source_path||'')} · ${escapeHTML(source.source_range||'')}</p><div class="evidence-prose">${richText(source.text||'')}</div>${equations}${referenceLink(source)}${anchors?`<details><summary>Inspect source anchors</summary>${anchors}</details>`:''}${passages}`;
}
document.addEventListener('click',async event=>{
  const button=event.target.closest('[data-source-passages]');if(!button||button.disabled)return;
  button.disabled=true;const box=button.nextElementSibling;box.textContent='Reading cited passages…';
  try{
    const ids=JSON.parse(button.dataset.sourcePassages);
    const records=await post('/api/v1/evidence/excerpt',{ids});
    box.innerHTML=records.map(r=>`<details><summary>${escapeHTML(r.source_range)}</summary><pre>${escapeHTML(r.text)}</pre></details>`).join('');
    button.textContent='Cited passages loaded';
  }catch(e){box.textContent=e.message;button.disabled=false;}
});
renderSourceTrail=function(sources,query=''){
  $('#sourceSearch').disabled=!sources.length;
  const list=sources.filter(s=>JSON.stringify(s).toLowerCase().includes(query.toLowerCase()));
  $('#sourceCount').textContent=`${list.length} source records`;
  $('#copilotSources').innerHTML=list.map((s,i)=>`<div class="citation"><button class="citation-button" data-source-index="${i}" type="button" aria-expanded="false"><strong>${escapeHTML(s.title||s.source_path||s.id)}</strong><span>${escapeHTML(s.source_range||'Source record')}</span><small>${escapeHTML(s.review_state||s.kind||'Source reference')} · Inspect source</small></button></div>`).join('')||'<p class="micro">No sources cited yet.</p>';
  $$('[data-source-index]').forEach(b=>b.onclick=async()=>{
    const s=list[Number(b.dataset.sourceIndex)];
    const existing=b.parentElement.querySelector('.source-excerpt');
    if(existing){existing.remove();b.setAttribute('aria-expanded','false');return;}
    b.disabled=true;
    try{
      let source=s;
      if(!s.text&&s.id?.startsWith('document:'))source=(await post('/api/v1/evidence/excerpt',{id:s.id}))[0];
      else if(!s.text&&s.id&&!s.id.startsWith('runtime:'))source=await post('/api/v1/evidence/record',{id:s.id});
      const box=document.createElement('div');box.className='source-excerpt';
      box.innerHTML=['reviewed_source_note','consulted_web_reference'].includes(source.kind)?reviewedSourceContent(source):`<p class="micro">${escapeHTML(source.source_path||'')} · ${escapeHTML(source.review_state||'Inspect evidence scope')}</p><pre>${escapeHTML(source.text||JSON.stringify(source,null,2))}</pre>`;
      if(s.review_notes?.length)box.insertAdjacentHTML('beforeend',`<details><summary>Review notes for this passage</summary>${s.review_notes.map(n=>`<h4>${escapeHTML(n.title)}</h4><div class="evidence-prose">${richText(n.text)}</div>`).join('')}</details>`);
      b.parentElement.append(box);b.setAttribute('aria-expanded','true');
    }catch(e){const p=document.createElement('p');p.className='source-excerpt';p.setAttribute('role','status');p.textContent=e.message;b.parentElement.append(p);}finally{b.disabled=false;}
  });
};
// Break lines at missing values instead of drawing fictitious continuity.
