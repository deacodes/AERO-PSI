    function chartDomain(seriesList, xKey, yKey) {
      const valid = seriesList.flat().filter(point => point[xKey] !== null && point[yKey] !== null && Number.isFinite(Number(point[xKey])) && Number.isFinite(Number(point[yKey])));
      const xs = valid.map(point => Number(point[xKey])), ys = valid.map(point => Number(point[yKey]));
      return { xmin: Math.min(...xs), xmax: Math.max(...xs), ymin: Math.min(...ys), ymax: Math.max(...ys) };
    }
    function chartCoordinates(point, xKey, yKey, domain) {
      return { x: 60 + ((Number(point[xKey]) - domain.xmin) / (domain.xmax - domain.xmin || 1)) * 680, y: 315 - ((Number(point[yKey]) - domain.ymin) / (domain.ymax - domain.ymin || 1)) * 285 };
    }
    function chartBase(svg, domain) {
      const labels = domain ? `<text class="axis-text" x="60" y="340">${escapeHTML(formatNumber(domain.xmin))}</text><text class="axis-text" x="740" y="340" text-anchor="end">${escapeHTML(formatNumber(domain.xmax))}</text><text class="axis-text" x="52" y="38" text-anchor="end">${escapeHTML(domain.ymax.toExponential(5))}</text><text class="axis-text" x="52" y="318" text-anchor="end">${escapeHTML(domain.ymin.toExponential(5))}</text>` : '';
      svg.innerHTML = `<g aria-hidden="true"><line class="grid-line" x1="60" y1="30" x2="60" y2="315"/><line class="grid-line" x1="60" y1="315" x2="740" y2="315"/>${[0,1,2,3,4].map(i => `<line class="grid-line" x1="60" y1="${30+i*71.25}" x2="740" y2="${30+i*71.25}"/>`).join('')}${labels}</g>`;
    }
    function pathFor(points, xKey, yKey, domain) {
      const valid = points.filter(point => point[xKey] !== null && point[yKey] !== null && Number.isFinite(Number(point[xKey])) && Number.isFinite(Number(point[yKey])));
      return valid.map((point, index) => { const {x,y} = chartCoordinates(point,xKey,yKey,domain); return `${index ? 'L' : 'M'}${x.toFixed(2)},${y.toFixed(2)}`; }).join(' ');
    }
    function drawSeries(svg, series, xKey, yKey, marks = [], markSeries = 'series', kind = 'coagulation', extraSeries = []) {
      const markSeriesList = marks.map(mark => mark[markSeries]); const domain = chartDomain([series, ...extraSeries, ...markSeriesList], xKey, yKey); chartBase(svg, domain);
      marks.forEach((mark, index) => { const path = pathFor(mark[markSeries], xKey, yKey, domain); if (path) svg.insertAdjacentHTML('beforeend', `<path class="data-path marked-${index ? 'b' : 'a'}" d="${path}"/>`); });
      extraSeries.forEach((items,index)=>{const extraPath=pathFor(items,xKey,yKey,domain);if(extraPath)svg.insertAdjacentHTML('beforeend',`<path class="data-path angle-${(index+1)%5}" d="${extraPath}"/>`);});
      const path = pathFor(series, xKey, yKey, domain); if (path) svg.insertAdjacentHTML('beforeend', `<path class="data-path angle-0" d="${path}"/>`);
      const stride = Math.max(1, Math.ceil(series.length / 48));
      series.forEach((point, index) => { if (point[xKey]===null || point[yKey]===null || !Number.isFinite(Number(point[xKey])) || !Number.isFinite(Number(point[yKey]))) return; if (index % stride && index !== series.length - 1) return; const {x,y}=chartCoordinates(point,xKey,yKey,domain); const pinned=state.pinnedPoints[kind].has(index) ? ' pinned' : ''; svg.insertAdjacentHTML('beforeend', `<g class="chart-point-target${pinned}" data-kind="${kind}" data-index="${index}" tabindex="0" role="button" aria-label="Inspect graph point ${index + 1}"><circle class="chart-point-hit" cx="${x}" cy="${y}" r="16"/><circle class="chart-point-dot" cx="${x}" cy="${y}" r="4"/></g>`); });
      bindGraphPoints(svg, kind);
    }
    function pointSummary(kind, point) {
      if (kind === 'coagulation') return { title: `${formatNumber(point.time_s)} s`, detail: `${scientific(point.number_concentration_m3)} particles/m³ · ${(point.equivalent_volume_mean_diameter_m * 1e9).toFixed(2)} nm` };
      return { title: point.time_string || `Source row ${point.source_row}`, detail: `${escapeHTML(state.currentOptical?.signal || 'signal')} = ${formatNumber(point.value)}` };
    }
    function bindGraphPoints(svg, kind) {
      const tooltip = document.createElement('div'); tooltip.className = 'chart-tooltip'; tooltip.hidden = true; svg.parentElement.querySelector('.chart-tooltip')?.remove(); svg.parentElement.append(tooltip);
      $$('.chart-point-target', svg).forEach(target => {
        const index=Number(target.dataset.index); const show=()=>{ const series=kind==='coagulation' ? state.currentCoag?.series : state.currentOptical?.series; const point=series?.[index]; if(!point) return; const summary=pointSummary(kind,point); const dot=$('.chart-point-dot',target); tooltip.innerHTML=`<strong>${summary.title}</strong><span>${summary.detail}</span>`; tooltip.style.left=`${100*Number(dot.getAttribute('cx'))/760}%`; tooltip.style.top=`${100*Number(dot.getAttribute('cy'))/360}%`; tooltip.hidden=false; }; const hide=()=>tooltip.hidden=true;
        target.addEventListener('mouseenter',show); target.addEventListener('mouseleave',hide); target.addEventListener('focus',show); target.addEventListener('blur',hide); target.addEventListener('click',()=>openPointActions(kind,index)); target.addEventListener('keydown',event=>{ if(event.key==='Enter'||event.key===' '){event.preventDefault();openPointActions(kind,index);} });
        let hold; target.addEventListener('pointerdown',()=>hold=setTimeout(()=>openPointActions(kind,index),550)); ['pointerup','pointercancel','pointerleave'].forEach(name=>target.addEventListener(name,()=>clearTimeout(hold)));
      });
    }
    function openPointActions(kind,index) {
      const series=kind==='coagulation' ? state.currentCoag?.series : state.currentOptical?.series; const point=series?.[index]; if(!point) return; const summary=pointSummary(kind,point); const target=kind==='coagulation' ? $('#coagPointActions') : $('#opticalPointActions'); target.classList.add('open'); target.innerHTML=`<div><strong>${summary.title}</strong><span>${summary.detail}</span></div><button class="button-primary" type="button" data-point-ask>Ask SI</button><button class="button-secondary" type="button" data-point-pin>${state.pinnedPoints[kind].has(index)?'Unpin':'Pin point'}</button>`;
      $('[data-point-ask]',target).addEventListener('click',()=>askSIAboutPoint(kind,index)); $('[data-point-pin]',target).addEventListener('click',()=>{ const pins=state.pinnedPoints[kind]; pins.has(index)?pins.delete(index):pins.add(index); if(kind==='coagulation') drawSeries($('#coagChart'),state.currentCoag.series,'time_s','number_concentration_m3',state.coagMarks,'series','coagulation'); else drawCurrentOptical(); openPointActions(kind,index); });
    }
    async function askSIAboutPoint(kind,index) {
      const output=kind==='coagulation' ? $('#coagPointAnswer') : $('#opticalPointAnswer'); output.innerHTML='<div class="si-point-answer"><h4>SI is verifying this point…</h4><p>The backend is reconstructing the source or model context before interpretation.</p></div>';
      const payload=kind==='coagulation' ? {kind:'coagulation_point',scenario:state.currentCoag.payload,point_index:index,question:'Explain this selected coagulation point, what changed by this time, and what cannot be concluded.'} : {kind:'optical_point',source_path:state.currentOptical.source,signal:state.currentOptical.signal,source_row:state.currentOptical.series[index].source_row,question:'Explain this selected detector sample, its relation to the run, and what cannot be concluded.'};
      try { const result=await jsonFetch('/api/v1/si/interpret-point',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}); output.innerHTML=`<div class="si-point-answer"><h4>${escapeHTML(result.headline)}</h4><p>${formatEvidenceText(result.interpretation)}</p>${result.supported?.length?`<ul>${result.supported.map(item=>`<li>${formatEvidenceText(item)}</li>`).join('')}</ul>`:''}${result.limitations?.length?`<p><strong>Limits:</strong> ${result.limitations.map(item=>formatEvidenceText(item)).join(' ')}</p>`:''}<p class="micro">${result.mode==='vertex_verified_context'?'Vertex SI · backend-verified context':'Recorded/computed context only — AI answer unavailable'}</p>${result.service?.reason?`<p class="micro">${escapeHTML(result.service.reason)}</p>`:''}</div>`; }
      catch(error){ output.innerHTML=`<div class="error-box">${escapeHTML(error.message)}</div>`; }
    }

