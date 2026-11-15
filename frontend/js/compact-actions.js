/* Secondary actions keep their existing handlers inside native disclosure menus. */
function actionMenu(host,label){if(!host)return;const menu=document.createElement('details');menu.className='compact-actions';const summary=document.createElement('summary');summary.setAttribute('aria-label',label);summary.textContent='•••';menu.append(summary);const content=document.createElement('div');while(host.firstChild)content.append(host.firstChild);menu.append(content);host.append(menu);menu.addEventListener('click',e=>{if(e.target.closest('button'))menu.open=false;});menu.addEventListener('keydown',e=>{if(e.key==='Escape'){menu.open=false;summary.focus();}});}
actionMenu(document.querySelector('.dataset-actions'),'Dataset actions');actionMenu(document.querySelector('#rankWithSI')?.parentElement,'Ranking actions');
actionMenu(document.querySelector('#gapsWithSI')?.parentElement,'Gap Finder actions');
const spark='<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><path d="M12 2 Q12 12 22 12 Q12 12 12 22 Q12 12 2 12 Q12 12 12 2Z" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>';
for(const el of document.querySelectorAll('.si-glyph'))el.innerHTML=spark;
for(const id of ['interpretScenario','interpretScattering']){const b=document.getElementById(id);b.title=b.textContent;b.setAttribute('aria-label',b.textContent);b.innerHTML=spark;b.classList.add('si-icon-action');}
// One shared treatment for contextual SI actions, including newly rendered findings.
const secondarySISelector='#archiveSISummary, #archiveSIRow, #rankWithSI, #gapsWithSI, #researchAskPoint, #studioInterpret, [data-point-ask], [data-ask-finding], [data-context-si], .distribution-stage > button.button-text';
function decorateSecondarySI(root=document){
 const buttons=[...(root.matches?.(secondarySISelector)?[root]:[]),...root.querySelectorAll?.(secondarySISelector)||[]];
 for(const b of buttons){
  if(b.querySelector('.si-action-star'))continue;
  const label=b.textContent.trim()||b.getAttribute('aria-label')||'Discuss with SI';
  b.title=label;b.setAttribute('aria-label',label);
  // Menu entries retain names to distinguish summarizing a table from discussing a row.
  const inMenu=!!b.closest('.compact-actions');
  b.innerHTML=`<span class="si-action-star" aria-hidden="true">${spark}</span>${inMenu?`<span>${escapeHTML(label)}</span>`:''}`;
  b.classList.toggle('si-icon-action',!inMenu);b.classList.add('si-secondary-action');
 }
}
decorateSecondarySI();
new MutationObserver(records=>{for(const r of records){if(r.target.closest?.(secondarySISelector))decorateSecondarySI(r.target.closest(secondarySISelector));for(const node of r.addedNodes)if(node.nodeType===1)decorateSecondarySI(node);}}).observe(document.querySelector('main'),{childList:true,subtree:true});
