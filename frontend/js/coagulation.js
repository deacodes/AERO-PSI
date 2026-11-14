    function setLabMode(mode) {
      const button=$(`.subnav button[data-lab="${mode}"]`); if(!button)return;
      $$('.subnav button').forEach(item => { item.classList.toggle('active', item === button); item.setAttribute('aria-selected', item === button ? 'true' : 'false'); });
      $$('.lab-view').forEach(view => view.classList.toggle('active', view.id === `lab-${button.dataset.lab}`));
    }
    $$('.subnav button').forEach(button => button.addEventListener('click', () => setLabMode(button.dataset.lab)));
    $('#sticking').addEventListener('input', event => $('#stickingValue').textContent = Number(event.target.value).toFixed(2));

    $('#coagForm').addEventListener('submit', async event => {
      event.preventDefault();
      const button = event.submitter || $('#coagForm button[type=submit]'); const old = button.textContent; button.disabled = true; button.textContent = 'Running…';
      try {
        const payload = { ...readPhysicsInputs(), initial_number_concentration_m3: Number($('#n0').value), initial_median_diameter_m: Number($('#diameter').value) * 1e-9, initial_geometric_std_dev: Number($('#gsd').value), residence_time_s: Number($('#duration').value), sticking_efficiency: Number($('#sticking').value), section_count: Number($('#sections').value), output_points: 21 };
        const result = await jsonFetch('/api/v1/models/coagulation/sectional', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload) });
        state.currentCoag = { result, payload, series: result.series }; document.dispatchEvent(new CustomEvent('scenario-computed'));  state.pinnedPoints.coagulation.clear(); $('#coagPointActions').classList.remove('open'); $('#coagPointAnswer').innerHTML='';
        drawSeries($('#coagChart'), result.series, 'time_s', 'number_concentration_m3', state.coagMarks, 'series', 'coagulation');
        $('#coagEmpty').classList.add('hidden'); $('#markScenario').disabled = false;
        const final = result.series.at(-1); const start = result.series[0]; const reduction = start.number_concentration_m3 ? 100 * (1 - final.number_concentration_m3 / start.number_concentration_m3) : 0;
        $('#resultNumber').textContent = scientific(final.number_concentration_m3, ' m⁻³'); $('#resultDiameter').textContent = `${(final.equivalent_volume_mean_diameter_m * 1e9).toFixed(2)} nm`; $('#resultError').textContent = scientific(result.conservation_check.total_volume_relative_error);
        $('#coagInterpretation').className = 'finding observed'; $('#coagInterpretation').innerHTML = `<div class="state">Model result</div><p>Number concentration changed by ${(-reduction).toFixed(2)}%. Final equivalent volume-mean diameter is ${(final.equivalent_volume_mean_diameter_m*1e9).toFixed(2)} nm. This is a solver result under the selected assumptions, not a PSI observation.</p>`;
      } catch (error) { $('#coagInterpretation').className = 'error-box'; $('#coagInterpretation').textContent = error.message; }
      finally { button.disabled = false; button.textContent = old; }
    });
    $('#markScenario').addEventListener('click', () => {
      if (!state.currentCoag) return; state.coagMarks.push(structuredClone(state.currentCoag)); if (state.coagMarks.length > 2) state.coagMarks.shift(); renderCoagMarks();
    });
    $('#runSensitivity').addEventListener('click', async () => {
      const button = $('#runSensitivity'); button.disabled = true; button.textContent = 'Checking…';
      try {
        const payload = { ...readPhysicsInputs(), initial_number_concentration_m3: Number($('#n0').value), initial_median_diameter_m: Number($('#diameter').value) * 1e-9, initial_geometric_std_dev: Number($('#gsd').value), residence_time_s: Number($('#duration').value), sticking_efficiency: Number($('#sticking').value), section_counts: [32,64,96], output_points: 31 };
        const data = await jsonFetch('/api/v1/models/coagulation/sensitivity', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
        $('#sensitivityOutput').innerHTML = `<p class="kicker">Numerical sensitivity</p>${data.results.map(item => `<div class="marked-state"><i></i><span>${item.section_count} bins · final N ${scientific(item.final_number_concentration_m3)} · overflow ${scientific(item.overflow_volume_fraction)}</span><span>${(100 * item.number_relative_to_finest).toFixed(3)}%</span></div>`).join('')}<p class="micro">${escapeHTML(data.pass_rule)}</p>`;
      } catch (error) { $('#sensitivityOutput').innerHTML = `<div class="error-box">${escapeHTML(error.message)}</div>`; }
      finally { button.disabled = false; button.textContent = 'Check grid'; }
    });
    function renderCoagMarks() {
      if (state.currentCoag) drawSeries($('#coagChart'), state.currentCoag.series, 'time_s', 'number_concentration_m3', state.coagMarks, 'series', 'coagulation');
      $('#markedScenarios').innerHTML = state.coagMarks.length ? `<p class="kicker">Marked scenarios</p>${state.coagMarks.map((mark, index) => `<div class="marked-state"><i></i><span>${index ? 'B' : 'A'} · N₀ ${scientific(mark.payload.initial_number_concentration_m3)} · ${mark.payload.residence_time_s}s · α ${mark.payload.sticking_efficiency}</span><button type="button" data-remove-coag="${index}">Remove</button></div>`).join('')}` : '';
      $('#coagLegend').innerHTML = `<span class="legend-key"><i class="legend-line"></i>Current scenario</span>${state.coagMarks.map((_, index) => `<span class="legend-key"><i class="legend-line marked-${index ? 'b' : 'a'}"></i>Marked ${index ? 'B' : 'A'}</span>`).join('')}<span>Hover for values · click or hold for SI actions</span>`;
      $$('[data-remove-coag]').forEach(button => button.addEventListener('click', () => { state.coagMarks.splice(Number(button.dataset.removeCoag), 1); renderCoagMarks(); }));
    }

