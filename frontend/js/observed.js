    function friendlyRun(run) {
      const file=run.source_path.split('/').pop(); const runMatch=run.source_path.match(/run[_\s-]?(\d+)/i); const gmtMatch=run.source_path.match(/gmt[_\s-]?(\d+)/i); const material=run.material_candidate || 'Material not catalogued'; const ids=[runMatch?`Run ${runMatch[1]}`:'Imported run',gmtMatch?`GMT ${gmtMatch[1]}`:null].filter(Boolean).join(' · '); const signals=Object.keys(run.optical_signal_columns||{}).length;
      return { title:`${material} · ${ids}`, meta:`${run.group} · ${signals} optical channels · ${run.quality_state || 'quality unclassified'}`, file };
    }
    function findRun(source) { return Object.values(state.runs).flat().find(run=>run.source_path===source); }
    function populateOpticalRuns() {
      const runs=state.runs[$('#opticalGroup').value]||[]; const selected=runs.find(run=>run.source_path===$('#opticalRun').value) || runs[0]; $('#opticalRun').value=selected?.source_path||''; updateRunPickerButton(selected); renderRunPicker(''); populateOpticalSignals();
    }
    function updateRunPickerButton(run) {
      const label=run?friendlyRun(run):{title:'No imported run available',meta:'Change investigation group'}; $('#runPickerButton').innerHTML=`<strong>${escapeHTML(label.title)}</strong><span>${escapeHTML(label.meta)}</span>`;
    }
    function renderRunPicker(query='') {
      const normalized=query.trim().toLowerCase(); const runs=(state.runs[$('#opticalGroup').value]||[]).filter(run=>{const label=friendlyRun(run);return !normalized||`${label.title} ${label.meta} ${label.file}`.toLowerCase().includes(normalized);});
      $('#runPickerList').innerHTML=runs.map(run=>{const label=friendlyRun(run);return `<button class="run-choice" type="button" role="option" aria-selected="${run.source_path===$('#opticalRun').value}" data-run-source="${escapeHTML(run.source_path)}"><strong>${escapeHTML(label.title)}</strong><span>${escapeHTML(label.meta)}</span><small>${escapeHTML(label.file)}</small></button>`;}).join('')||'<p class="micro">No run matches this search.</p>';
      $$('.run-choice',$('#runPickerList')).forEach(button=>button.addEventListener('click',()=>selectOpticalRun(button.dataset.runSource)));
    }
    function selectOpticalRun(source) {
      const run=(state.runs[$('#opticalGroup').value]||[]).find(item=>item.source_path===source); if(!run)return; $('#opticalRun').value=source; updateRunPickerButton(run); populateOpticalSignals(); $('#runPickerPanel').hidden=true; $('#runPickerButton').setAttribute('aria-expanded','false'); $('#runPickerButton').focus();
    }
    $('#opticalGroup').addEventListener('change',()=>{ $('#opticalRun').value=''; populateOpticalRuns(); });
    $('#runPickerButton').addEventListener('click',()=>{const open=$('#runPickerPanel').hidden;$('#runPickerPanel').hidden=!open;$('#runPickerButton').setAttribute('aria-expanded',String(open));if(open){$('#runPickerSearch').value='';renderRunPicker('');$('#runPickerSearch').focus();}});
    $('#runPickerSearch').addEventListener('input',event=>renderRunPicker(event.target.value));
    $('#runPickerPanel').addEventListener('keydown',event=>{if(event.key==='Escape'){event.preventDefault();$('#runPickerPanel').hidden=true;$('#runPickerButton').setAttribute('aria-expanded','false');$('#runPickerButton').focus();}});
    document.addEventListener('pointerdown',event=>{if(!$('#runPickerPanel').hidden&&!event.target.closest('.run-picker-panel')&&!event.target.closest('#runPickerButton')){$('#runPickerPanel').hidden=true;$('#runPickerButton').setAttribute('aria-expanded','false');}});
    function populateOpticalSignals() {
      const group = $('#opticalGroup').value; const run = (state.runs[group] || []).find(item => item.source_path === $('#opticalRun').value); const signals = Object.keys(run?.optical_signal_columns || {});
      $('#opticalSignal').innerHTML = signals.map(signal => `<option>${escapeHTML(signal)}</option>`).join('') || '<option value="">No optical signal available</option>';
      $('#opticalSignalB').innerHTML = signals.map((signal, index) => `<option${index === 1 ? ' selected' : ''}>${escapeHTML(signal)}</option>`).join('') || '<option value="">No second signal available</option>';
    }
    $('#loadOptical').addEventListener('click', loadOptical);
    async function loadOptical() {
      const source = $('#opticalRun').value, signal = $('#opticalSignal').value; if (!source) return;
      const button = $('#loadOptical'); button.disabled = true; button.textContent = 'Loading…';
      try {
        const run=findRun(source); const available=Object.keys(run?.optical_signal_columns||{}); const signals=$('#multiAngle').checked ? available.filter(name=>name.startsWith('scatter_')) : [signal]; if(!signals.includes(signal))signals.unshift(signal);
        const data = await jsonFetch(`/api/v1/optical/time-series?source_path=${encodeURIComponent(source)}&signals=${encodeURIComponent(signals.join(','))}&max_points=700`);
        const seriesBySignal=Object.fromEntries(signals.map(name=>[name,data.points.map((point,index)=>({index,source_row:point.source_row,time:point.time,time_string:point.time_string,value:point.values[name]}))])); const series=seriesBySignal[signal]||[];
        state.currentOptical = { data, series, seriesBySignal, source, signal, signals }; document.dispatchEvent(new CustomEvent('run-loaded'));  state.pinnedPoints.optical.clear(); $('#opticalPointActions').classList.remove('open'); $('#opticalPointAnswer').innerHTML='';
        drawCurrentOptical();
        $('#opticalEmpty').classList.add('hidden'); $('#markOptical').disabled = false;
        const values = series.map(point => point.value).filter(value=>value!==null && Number.isFinite(value)); $('#opticalSamples').textContent = formatNumber(series.length); $('#opticalMin').textContent = formatNumber(Math.min(...values)); $('#opticalMax').textContent = formatNumber(Math.max(...values));
        const label=friendlyRun(run); $('#opticalCaption').textContent = `${signals.length} channel${signals.length===1?'':'s'} · ${label.title}`; $('#opticalObserved').textContent = `${data.downsample.returned_row_count} unchanged source samples are displayed from ${data.downsample.original_row_count} rows. Selection used every Nth row plus the final row.`;
      } catch (error) { $('#opticalObserved').textContent = error.message; }
      finally { button.disabled = false; button.textContent = 'Inspect response'; }
    }
    $('#markOptical').addEventListener('click', () => { if (!state.currentOptical) return; if(state.opticalMarks.some(m=>m.source!==state.currentOptical.source||m.signal!==state.currentOptical.signal)) { $('#opticalObserved').textContent='Cross-run or cross-signal overlays need verified comparability. Remove the previous mark first.'; return; } state.opticalMarks.push(structuredClone(state.currentOptical)); if (state.opticalMarks.length > 2) state.opticalMarks.shift(); renderOpticalMarks(); });
    function drawCurrentOptical() { if(!state.currentOptical)return; const extras=state.currentOptical.signals.filter(name=>name!==state.currentOptical.signal).map(name=>state.currentOptical.seriesBySignal[name]); drawSeries($('#opticalChart'),state.currentOptical.series,'index','value',state.opticalMarks,'series','optical',extras); $('#opticalLegend').innerHTML=state.currentOptical.signals.map((name,index)=>`<span class="legend-key"><i class="legend-line angle-${index%5}"></i>${escapeHTML(name.replace('scatter_','').replace('_deg_v','°').replace('_v',''))}</span>`).join('')+'<span>Hover for values · click or hold for SI actions</span>'; }
    $('#runLag').addEventListener('click', async () => {
      const source = $('#opticalRun').value, left = $('#opticalSignal').value, right = $('#opticalSignalB').value; if (!source || !left || !right) return;
      const button = $('#runLag'); button.disabled = true; button.textContent = 'Screening…';
      try {
        const data = await jsonFetch(`/api/v1/optical/lag?source_path=${encodeURIComponent(source)}&left=${encodeURIComponent(left)}&right=${encodeURIComponent(right)}&max_lag_samples=30`); const best = data.strongest_absolute_correlation;
        $('#opticalObserved').textContent = `${left} and ${right} show a strongest screened correlation of ${best.pearson_correlation.toFixed(3)} at ${best.lag_samples} samples${best.lag_seconds === null ? '' : ` (${best.lag_seconds.toFixed(2)} s)`}. This is an association screen, not evidence of causality.`;
      } catch (error) { $('#opticalObserved').textContent = error.message; }
      finally { button.disabled = false; button.textContent = 'Screen association'; }
    });
    function renderOpticalMarks() {
      if (state.currentOptical) drawCurrentOptical();
      $('#markedOptical').innerHTML = state.opticalMarks.length ? `<p class="kicker">Marked responses</p>${state.opticalMarks.map((mark, index) => {const run=findRun(mark.source);return `<div class="marked-state"><i></i><span>${index ? 'B' : 'A'} · ${escapeHTML(mark.signal)} · ${escapeHTML(run?friendlyRun(run).title:mark.source.split('/').pop())}</span><button type="button" data-remove-optical="${index}">Remove</button></div>`;}).join('')}` : '';
      $$('[data-remove-optical]').forEach(button => button.addEventListener('click', () => { state.opticalMarks.splice(Number(button.dataset.removeOptical), 1); renderOpticalMarks(); }));
    }

    // Evidence-group selection is managed by research.js.
