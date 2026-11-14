let resourcesLoaded = false;
function loadResourcePage() {
  if (resourcesLoaded) return;
  resourcesLoaded = true;
// Resources remains separate and exposes every catalog entry without altering the archive.
const resourceSection=document.createElement('section');resourceSection.className='distribution-stage';resourceSection.innerHTML='<h2>Supplied source inventory</h2><label for="resourceFilter">Filter by investigation, material or filename</label><input id="resourceFilter" type="search" placeholder="For example: PSI102, Kapton, report"><p id="resourceTotal" class="micro">Loading catalog…</p><div id="resourceFiles" class="resource-files"></div>';$('#page-resources').append(resourceSection);
jsonFetch('/api/v1/files').then(files=>{const render=()=>{const query=$('#resourceFilter').value.toLowerCase();const chosen=files.filter(f=>f.source_path.toLowerCase().includes(query));$('#resourceTotal').textContent=`${chosen.length} of ${files.length} catalogued files · original archive is read-only`;$('#resourceFiles').innerHTML=chosen.map(f=>`<details><summary>${escapeHTML(f.source_path)}</summary><p>${escapeHTML(f.format)} · ${formatNumber(f.bytes)} bytes · ${escapeHTML(f.file_role)}</p><p class="micro">SHA-256: ${escapeHTML(f.source_sha256)}</p></details>`).join('');};$('#resourceFilter').oninput=render;render();}).catch(e=>$('#resourceTotal').textContent=e.message);
const opticsResource=document.createElement('a');opticsResource.className='resource-row';opticsResource.href='https://miepython.readthedocs.io/';opticsResource.target='_blank';opticsResource.rel='noreferrer';opticsResource.innerHTML='<span class="resource-kind">Optical calculations</span><div><strong>miepython 3.3.1</strong><p>Spherical Mie scattering. Numerical benchmarks are separate from NASA experimental validation.</p></div><span class="resource-state">Documentation</span>';$('.resource-directory').append(opticsResource);

const reviewSection=document.createElement('section');reviewSection.className='distribution-stage';
reviewSection.innerHTML='<h2>Scientific source review</h2><p id="reviewScope" class="micro" role="status">Loading document review…</p><label for="reviewFilter">Find methods, equations or source limitations</label><input id="reviewFilter" type="search" placeholder="For example: dilution, lognormal, calibration"><p id="reviewCount" class="micro" aria-live="polite"></p><div id="reviewSources" class="resource-files"></div>';
$('#page-resources').append(reviewSection);
jsonFetch('/api/v1/evidence/review').then(review=>{
  $('#reviewScope').textContent=`${review.source_files} files · ${review.distinct_sources} distinct sources · ${review.excerpts} searchable excerpts. ${review.scope}`;
  const render=()=>{
    const q=$('#reviewFilter').value.toLowerCase();
    const records=review.notes.filter(n=>[n.title,n.text,n.source_path].join(' ').toLowerCase().includes(q));
    $('#reviewCount').textContent=`${records.length} source-linked entries. Duplicate archive copies retain their own source paths.`;
    $('#reviewSources').innerHTML=records.map(n=>`<details class="scientific-review-entry"><summary>${escapeHTML(n.title)}</summary><p class="micro">${escapeHTML(n.classification.replaceAll('_',' '))} · ${escapeHTML(n.review_state)}</p>${reviewedSourceContent(n)}</details>`).join('')||'<p>No reviewed passages match this filter. Try a material or a scientific term.</p>';
  };
  $('#reviewFilter').oninput=render;render();
}).catch(e=>$('#reviewScope').textContent=`Document review could not load: ${e.message}`);


}
document.addEventListener('page-changed', e => { if (e.detail.page === 'resources') loadResourcePage(); });
