/* Page templates are separate documents; scientific state survives page navigation. */
(async function bootWorkspace() {
  const pages = ['home', 'mission', 'lab', 'atlas', 'evidence', 'resources', 'studio'];
  const scripts = ['browser-storage', 'core', 'source-labels', 'navigation', 'charts', 'archive', 'coagulation', 'observed', 'atlas',
    'evidence-base', 'settings', 'workflow-shared', 'distribution', 'observed-analysis', 'scattering',
    'analysis-runner', 'discussion-plots', 'sources', 'accessibility', 'resources', 'science-chat', 'discovery', 'studio-charts', 'studio', 'experiment-design', 'research', 'gap-si', 'archive-browser', 'model-si', 'context-si', 'journey', 'si-workspace', 'si-evidence-picker', 'home-explore', 'home-previews', 'term-help', 'compact-actions'];
  async function template(path) {
    let response;
    try { response = await fetch(path); }
    catch { response = await fetch(path); } // One retry for a failed local static-file request only.
    if (!response.ok) throw Error(`Could not load ${path}. Reload to try again.`);
    return response.text();
  }
  try {
    const content = await Promise.all([template('/components/sidebar.html'), template('/components/settings.html')]);
    for (const page of pages) content.push(await template(`/pages/${page}.html`));
    document.querySelector('#navigationMount').outerHTML = content[0];
    document.querySelector('#settingsMount').outerHTML = content[1];
    document.querySelector('#pageMount').outerHTML = content.slice(2).join('\n');
    for (const name of scripts) {
      if(name==='navigation')await SourceLabels.ready;
      await new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = `/js/${name}.js`; script.onload = resolve;
        script.onerror = () => reject(Error(`Could not load ${name}. Reload to try again.`));
        document.body.append(script);
      });
    }
    navigate(pageFromLocation(), {replace: true, id:new URLSearchParams(location.search).get('id')});
    chartBase($('#coagChart')); chartBase($('#opticalChart'));
    await initialize();
    document.documentElement.dataset.ready = 'true';
  } catch (error) {
    const box = document.createElement('p');
    box.className = 'error-box'; box.setAttribute('role', 'alert'); box.textContent = error.message;
    document.querySelector('main').prepend(box);
  }
})();
