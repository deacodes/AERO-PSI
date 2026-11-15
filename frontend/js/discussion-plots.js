/* Inline source-data plots. No calculator navigation or generated coordinates. */
const DiscussionPlots=(()=>{
 function mount(host,analysis){
  if(!host||!analysis)return;
  host.className='discussion-plot';
  const heading=document.createElement('h3');heading.textContent='Patterns in this dataset';host.append(heading);
  const source=document.createElement('p');source.className='micro';source.textContent=analysis.source_path.split('/').at(-1)+' · '+analysis.scope;host.append(source);
  if(!analysis.charts?.length){const p=document.createElement('p');p.textContent='No plot available: this selection needs at least two usable numeric values in a displayed measurement.';host.append(p);return;}
  const label=document.createElement('label');label.textContent='Measurement ';const select=document.createElement('select');select.setAttribute('aria-label','Measurement to plot in this answer');
  analysis.charts.forEach((c,i)=>{const o=document.createElement('option');o.value=i;o.textContent=c.column;select.append(o);});label.append(select);host.append(label);
  const frame=document.createElement('div');frame.className='discussion-plot-frame';host.append(frame);
  const output=document.createElement('p');output.className='discussion-plot-readout';output.setAttribute('aria-live','polite');host.append(output);
  const stats=document.createElement('p');stats.className='micro';host.append(stats);
  const note=document.createElement('p');note.className='micro';host.append(note);
  const format=n=>Number(n).toLocaleString(undefined,{maximumSignificantDigits:5});
  function draw(){
   const chart=analysis.charts[Number(select.value)],points=chart.points,valid=points.filter(p=>Number.isFinite(p.value));
   const xmin=Math.min(...valid.map(p=>p.row)),xmax=Math.max(...valid.map(p=>p.row));
   let ymin=Math.min(...valid.map(p=>p.value)),ymax=Math.max(...valid.map(p=>p.value));const pad=(ymax-ymin)*.08||Math.abs(ymax)*.05||1;ymin-=pad;ymax+=pad;
   const x=p=>72+(p.row-xmin)/(xmax-xmin||1)*496,y=p=>24+(ymax-p.value)/(ymax-ymin)*166;
   let path='',previous=null;
   points.forEach(p=>{if(!Number.isFinite(p.value)){previous=null;return;}const contiguous=previous&&(chart.sampled||p.row===previous.row+1);path+=(contiguous?'L':'M')+x(p).toFixed(2)+','+y(p).toFixed(2)+' ';previous=p;});
   frame.innerHTML=`<svg viewBox="0 0 600 230" tabindex="0" role="img" aria-label="Source-row plot. Use left and right arrow keys to inspect values."><g class="discussion-grid"><path d="M72 24V190H568"/><path d="M72 107H568M72 24H568"/></g><g class="discussion-labels"><text x="64" y="28" text-anchor="end">${escapeHTML(format(ymax))}</text><text x="64" y="194" text-anchor="end">${escapeHTML(format(ymin))}</text><text x="72" y="210">${xmin}</text><text x="568" y="210" text-anchor="end">${xmax}</text><text x="320" y="228" text-anchor="middle">Source row (not elapsed time)</text></g><path class="discussion-data" d="${path}"/><circle class="discussion-cursor" r="4"/></svg>`;
   const svg=frame.querySelector('svg'),cursor=frame.querySelector('circle');let index=0;
   function inspect(i){index=Math.max(0,Math.min(valid.length-1,i));const p=valid[index];cursor.setAttribute('cx',x(p));cursor.setAttribute('cy',y(p));output.textContent=`Row ${p.row}: ${format(p.value)} · ${chart.column}`;}
   svg.onpointermove=e=>{const rect=svg.getBoundingClientRect(),row=xmin+((e.clientX-rect.left)/rect.width*600-72)/496*(xmax-xmin);inspect(valid.reduce((best,p,i)=>Math.abs(p.row-row)<Math.abs(valid[best].row-row)?i:best,0));};
   svg.onkeydown=e=>{if(['ArrowLeft','ArrowRight','Home','End'].includes(e.key)){e.preventDefault();inspect(e.key==='Home'?0:e.key==='End'?valid.length-1:index+(e.key==='ArrowLeft'?-1:1));}};
   const s=chart.statistics;stats.textContent=`${s.valid} usable values · min ${format(s.min.value)} (row ${s.min.row}) · max ${format(s.max.value)} (row ${s.max.row}) · ${s.missing_or_nonnumeric} blank/non-numeric · ${s.possible_sentinel} possible sentinels excluded.`;
   note.textContent=(chart.sampled?'Plot reduced with local extrema retained; statistics use all matching rows. ':'Plot shows every matching row. ')+'Units follow the source column. Gaps are not interpolated; patterns do not establish causation.';inspect(0);
  }
  select.onchange=draw;draw();
 }
 return {mount};
})();
