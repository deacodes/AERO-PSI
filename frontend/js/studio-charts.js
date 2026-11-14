/* Deterministic SVG charts. Every point links back to saved dataset row indices. */
const StudioCharts = (() => {
  const finite = value => typeof value === 'number' && Number.isFinite(value);
  const esc = value => escapeHTML(String(value ?? ''));
  function csv(rows) {
    return rows.map(row => row.map(value => {
      const v = value == null ? '' : String(value);
      // Protect spreadsheet consumers from formulas in user-provided text cells.
      const safe = typeof value === 'string' && /^[=+@\-\t\r]/.test(v) ? "'" + v : v;
      return '"' + safe.replaceAll('"', '""') + '"';
    }).join(',')).join('\n');
  }
  function parseCSV(source) {
    if (source.length > 90000) throw Error('Use a CSV smaller than 90 KB.');
    const rows = []; let row = [], value = '', quoted = false;
    source = source.replace(/^\uFEFF/, '');
    for (let i = 0; i < source.length; i++) {
      const ch = source[i];
      if (ch === '"') {
        if (quoted && source[i + 1] === '"') { value += '"'; i++; }
        else quoted = !quoted;
      } else if (ch === ',' && !quoted) { row.push(value); value = ''; }
      else if ((ch === '\n' || ch === '\r') && !quoted) {
        if (ch === '\r' && source[i + 1] === '\n') i++;
        row.push(value); if (row.some(v => v.trim())) rows.push(row);
        row = []; value = '';
      } else value += ch;
    }
    if (quoted) throw Error('CSV has an unclosed quoted cell.');
    row.push(value); if (row.some(v => v.trim())) rows.push(row);
    if (rows.length < 2) throw Error('Include a header and at least one data row.');
    const headers = rows.shift().map(v => v.trim());
    if (new Set(headers).size !== headers.length || headers.some(v => !v)) throw Error('Use nonempty, unique column names.');
    if (rows.some(r => r.length !== headers.length)) throw Error('Every CSV row must have the same number of columns.');
    return {headers, rows: rows.map(r => r.map(v => {
      const t = v.trim(); if (!t) return null;
      return /^[+-]?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?$/i.test(t) && Number.isFinite(Number(t)) ? Number(t) : t;
    }))};
  }
  function render(container, dataset, type, xi, yi, zi, onSelect, options={}) {
    if (!dataset) { container.innerHTML = '<div class="studio-chart-empty"><h3>Your results belong here</h3><p>Run a relevant mathematical tool from a method step, or add a sourced dataset. A graph appears when there are actual values to plot.</p></div>'; return; }
    const label = i => `${dataset.columns[i]?.name || ''}${dataset.columns[i]?.unit ? ` (${dataset.columns[i].unit})` : ''}`;
    let items = [], xLabel = label(xi), yLabel = label(yi), notice = '', categorical = type === 'bar';
    if (type === 'histogram') {
      const valid = dataset.rows.map((r, i) => ({v:r[yi], i})).filter(p => finite(p.v));
      if (valid.length) {
        const lo = Math.min(...valid.map(p => p.v)), hi = Math.max(...valid.map(p => p.v));
        const count = hi === lo ? 1 : Math.min(20, Math.ceil(Math.sqrt(valid.length)));
        const width = hi === lo ? Math.max(Math.abs(lo) * .05, 1) : (hi - lo) / count;
        items = Array.from({length:count}, (_, i) => ({x:lo + (i + .5) * width, y:0, rows:[], label:`${formatNumber(lo + i * width)}–${formatNumber(lo + (i + 1) * width)}`}));
        valid.forEach(p => { const item = items[Math.min(count-1, Math.floor((p.v-lo)/width))]; item.y++; item.rows.push(p.i); });
        xLabel = label(yi); yLabel = 'Count of finite samples'; notice = 'Histogram counts finite samples; it is not a probability density.';
      }
    } else if (type === 'heatmap') {
      const cells = new Map();
      dataset.rows.forEach((r, i) => {
        if (r[xi] == null || r[yi] == null || !finite(r[zi])) return;
        const key = JSON.stringify([r[xi], r[yi]]);
        const cell = cells.get(key) || {x:r[xi], y:r[yi], total:0, rows:[]};
        cell.total += r[zi]; cell.rows.push(i); cells.set(key, cell);
      });
      items = [...cells.values()].map(c => ({...c, z:c.total/c.rows.length}));
      notice = `Cell color: ${label(zi)}. Repeated coordinates use their arithmetic mean; missing cells remain blank.`;
    } else {
      items = dataset.rows.map((r, i) => ({x:r[xi], y:r[yi], rows:[i], index:i})).filter(p => finite(p.y) && (categorical ? p.x != null : finite(p.x)));
      notice = `${items.length} of ${dataset.rows.length} rows plotted. Missing/non-numeric values are excluded${type === 'line' ? '; lines follow source row order and break at missing rows' : ''}.`;
    }
    if (!items.length) { container.innerHTML = '<p class="studio-chart-empty">No compatible values for these axes. Choose numeric columns, or use a bar chart for categories.</p>'; return; }
    const width = 800, height = 390, left = 90, right = 770, top = 35, bottom = 310;
    const marks = [], grid = [];
    const interactive = (item, labelText) => `class="studio-chart-point" tabindex="0" role="button" data-rows="${esc(JSON.stringify(item.rows))}" data-label="${esc(labelText)}" aria-label="${esc(labelText)}"`;
    if (type === 'heatmap') {
      const xs = [...new Set(items.map(i => i.x))], ys = [...new Set(items.map(i => i.y))];
      if (xs.length > 40 || ys.length > 40) { container.textContent = 'Heatmap supports up to 40 distinct values per axis. Choose another view for this table.'; return; }
      const lo = Math.min(...items.map(i => i.z)), hi = Math.max(...items.map(i => i.z));
      const cw = (right-left)/xs.length, ch = (bottom-top)/ys.length;
      items.forEach(item => {
        const opacity = .2 + .8*(item.z-lo)/(hi-lo || 1);
        marks.push(`<rect ${interactive(item, `${item.x}, ${item.y}: ${formatNumber(item.z)} ${dataset.columns[zi].unit}; ${item.rows.length} rows`)} x="${left+xs.indexOf(item.x)*cw}" y="${top+ys.indexOf(item.y)*ch}" width="${Math.max(1,cw-2)}" height="${Math.max(1,ch-2)}" fill="var(--blue)" fill-opacity="${opacity}"/>`);
      });
      xs.forEach((x,i) => {if(xs.length<=12 || i%Math.ceil(xs.length/10)===0) grid.push(`<text x="${left+(i+.5)*cw}" y="332" text-anchor="middle">${esc(String(x).slice(0,14))}</text>`);});
      ys.forEach((y,i) => {if(ys.length<=12 || i%Math.ceil(ys.length/10)===0) grid.push(`<text x="80" y="${top+(i+.5)*ch}" text-anchor="end">${esc(String(y).slice(0,12))}</text>`);});
      grid.push(`<text x="${right}" y="20" text-anchor="end">Color range ${esc(formatNumber(lo))} to ${esc(formatNumber(hi))}</text>`);
    } else {
      const xs = items.map(p => p.x), ys = items.map(p => p.y);
      let xmin = categorical ? 0 : Math.min(...xs), xmax = categorical ? items.length : Math.max(...xs);
      let ymin = Math.min(...ys), ymax = Math.max(...ys);
      if (type === 'bar' || type === 'histogram') { ymin=Math.min(0,ymin); ymax=Math.max(0,ymax); }
      if (ymin === ymax) { const pad=Math.abs(ymin)*.05 || 1; ymin-=pad; ymax+=pad; }
      if (xmin === xmax) { const pad=Math.abs(xmin)*.05 || 1; xmin-=pad; xmax+=pad; }
      const xp = (p,i) => categorical ? left+(i+.5)*(right-left)/items.length : left+(p.x-xmin)/(xmax-xmin)*(right-left);
      const yp = value => bottom-(value-ymin)/(ymax-ymin)*(bottom-top);
      for(let i=0;i<=4;i++) {
        const y=top+i*(bottom-top)/4;
        grid.push(`<line x1="${left}" x2="${right}" y1="${y}" y2="${y}" stroke="var(--line)"/><text x="80" y="${y+4}" text-anchor="end">${esc(formatNumber(ymax-i*(ymax-ymin)/4))}</text>`);
      }
      if (!categorical) for(let i=0;i<=4;i++) grid.push(`<text x="${left+i*(right-left)/4}" y="333" text-anchor="middle">${esc(formatNumber(xmin+i*(xmax-xmin)/4))}</text>`);
      if (type === 'line') {
        let last = -2;
        const path = items.map((p,i) => {const cmd=p.index===last+1?'L':'M';last=p.index;return `${cmd}${xp(p,i)},${yp(p.y)}`;}).join(' ');
        marks.push(`<path d="${path}" fill="none" stroke="var(--blue)" stroke-width="2"/>`);
      }
      items.forEach((p,i) => {
        const x=xp(p,i), y=yp(p.y), description=`${p.label || p.x}: ${formatNumber(p.y)} ${type==='histogram'?'samples':dataset.columns[yi].unit || ''}`;
        if (type === 'bar' || type === 'histogram') {
          const bw=Math.max(1,(right-left)/items.length*.7), zero=yp(0);
          marks.push(`<rect ${interactive(p,description)} x="${x-bw/2}" y="${Math.min(y,zero)}" width="${bw}" height="${Math.max(1,Math.abs(y-zero))}" rx="2" fill="var(--blue)"/>`);
          if(categorical && (items.length<=10 || i%Math.ceil(items.length/8)===0)) grid.push(`<text x="${x}" y="333" text-anchor="middle">${esc(String(p.x).slice(0,16))}</text>`);
        } else marks.push(`<circle ${interactive(p,description)} cx="${x}" cy="${y}" r="4" fill="var(--blue)"/>`);
      });
    }
    container.innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(dataset.name)}: ${type} chart" xmlns="http://www.w3.org/2000/svg"><title>${esc(dataset.name)}</title><g fill="var(--muted)" font-family="Avenir Next, sans-serif" font-size="12">${grid.join('')}<text x="430" y="376" text-anchor="middle">${esc(xLabel)}</text><text transform="translate(20 180) rotate(-90)" text-anchor="middle">${esc(yLabel)}</text></g>${marks.join('')}</svg><p class="micro">${esc(notice)}</p>`;
    container.querySelectorAll('[data-rows]').forEach(mark => {
      const show=()=>{ document.querySelector(options.readout || '#studioPointReadout').textContent=mark.dataset.label; };
      const select=()=>{show();container.querySelectorAll('.selected').forEach(m=>m.classList.remove('selected'));mark.classList.add('selected');onSelect(JSON.parse(mark.dataset.rows),mark.dataset.label);};
      mark.addEventListener('mouseenter',show);mark.addEventListener('focus',show);mark.addEventListener('click',select);
      mark.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();select();}});
    });
  }
  return {parseCSV, csv, render};
})();
