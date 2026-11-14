    async function initialize() {
      try {
        const [health, summary, investigations, ranking, runs101, runs102] = await Promise.all([
          jsonFetch('/api/v1/health'), jsonFetch('/api/v1/summary'), jsonFetch('/api/v1/investigations'),
          jsonFetch('/api/v1/rankings/investigations'),
          jsonFetch('/api/v1/optical/runs?group=PSI101'), jsonFetch('/api/v1/optical/runs?group=PSI102')
        ]);
        state.summary = summary; state.investigations = investigations; state.ranking = ranking; state.runs.PSI101 = runs101; state.runs.PSI102 = runs102;
        $('#statusDot').classList.toggle('online', Boolean(health.ok)); $('#apiStatus').textContent = health.ok ? 'Archive connected' : 'Archive unavailable';
        $('#metricFiles').textContent = formatNumber(summary.file_count); $('#metricInvestigations').textContent = formatNumber(summary.investigation_count); $('#metricRuns').textContent = formatNumber(runs101.length + runs102.length);
        $('#rankFormula').textContent=ranking.formula; renderInvestigations(); renderRunCards(); populateOpticalRuns(); renderAtlasRuns(); loadAtlasGaps(); renderCoverage();
      } catch (error) {
        $('#apiStatus').textContent = 'Start Python backend';
        $('#investigationRanks').innerHTML = `<div class="error-box">${escapeHTML(error.message)}. Run <b>python3 aero_psi_backend.py serve</b> from the project folder.</div>`;
      }
    }

    function renderInvestigations() {}

    function renderRunCards() {
      const all=Object.values(state.runs).flat(); const ordered=all.filter(run=>state.runFilter==='all'||run.group===state.runFilter).sort((a,b)=>(b.analysis_readiness?.score||0)-(a.analysis_readiness?.score||0)||a.source_path.localeCompare(b.source_path)); const filtered=ordered.slice(0,10); state.runCardList=filtered;
      $('#topRunCards').innerHTML=filtered.length?filtered.map((run,index)=>{const label=friendlyRun(run);const readiness=run.analysis_readiness?.score||0;return `<button class="run-card" type="button" data-run-card="${index}"><span class="run-card-top"><span class="run-card-group">${escapeHTML(run.group)}</span><span class="run-card-score" aria-label="Analysis readiness ${readiness.toFixed(1)} out of 100">${readiness.toFixed(1)}</span></span><h3>${escapeHTML(label.title)}</h3><p>${escapeHTML(label.meta)} · ${run.warnings.length} importer warning${run.warnings.length===1?'':'s'}</p><span class="run-card-action">Inspect recorded signals →</span></button>`;}).join(''):'<p class="micro">No imported runs match this filter.</p>';
      $$('[data-run-card]',$('#topRunCards')).forEach(button=>button.addEventListener('click',()=>openRunInLab(state.runCardList[Number(button.dataset.runCard)])));
    }
    function openRunInLab(run) { if(!run)return; $('#opticalGroup').value=run.group; populateOpticalRuns(); selectOpticalRun(run.source_path); setLabMode('optical'); navigate('lab'); loadOptical(); }

