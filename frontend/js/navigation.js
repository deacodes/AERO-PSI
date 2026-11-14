const PAGE_PATHS = {home:'/', mission:'/archive', lab:'/models', atlas:'/gaps', evidence:'/science', resources:'/resources', studio:'/studio'};
function pageFromLocation() {
  const hash = location.hash.slice(1);
  if (hash in PAGE_PATHS) return hash;
  return Object.keys(PAGE_PATHS).find(key => PAGE_PATHS[key] === (location.pathname.replace(/\/$/, '') || '/')) || 'home';
}
function navigate(page, options = {}) {
  if (!(page in PAGE_PATHS)) page = 'home';
  $$('.page').forEach(item => item.classList.toggle('active', item.id === `page-${page}`));
  $$('.nav-button').forEach(item => item.setAttribute('aria-current', item.dataset.page === page ? 'page' : 'false'));
  document.body.classList.toggle('landing-mode', page === 'home');
  const url = PAGE_PATHS[page] + (page === 'studio' && options.id ? `?id=${encodeURIComponent(options.id)}` : '');
  if (!options.pop) history[options.replace ? 'replaceState' : 'pushState']({page}, '', url);
  window.scrollTo({top:0, behavior:'instant'});
  document.dispatchEvent(new CustomEvent('page-changed', {detail:{page, id:options.id || (page === 'studio' ? new URLSearchParams(location.search).get('id') : null)}}));
}
addEventListener('popstate', () => navigate(pageFromLocation(), {pop:true}));
addEventListener('hashchange', () => { if (location.hash.slice(1) in PAGE_PATHS) navigate(location.hash.slice(1), {replace:true}); });
    $$('.nav-button').forEach(button => button.addEventListener('click', () => navigate(button.dataset.page)));
    $$('[data-jump]').forEach(button => button.addEventListener('click', () => { navigate(button.dataset.jump); if(button.dataset.openLab) setLabMode(button.dataset.openLab); }));
    $('.brand').addEventListener('keydown', event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); navigate('home'); } });
    const savedSidebar=localStorage.getItem('sidebarCollapsed')==='true'; document.body.classList.toggle('sidebar-collapsed',savedSidebar); $('#sidebarToggle').setAttribute('aria-pressed',String(savedSidebar)); $('#sidebarToggle').setAttribute('aria-label',savedSidebar?'Expand sidebar':'Collapse sidebar');
    $('#sidebarToggle').addEventListener('click',()=>{const collapsed=document.body.classList.toggle('sidebar-collapsed');localStorage.setItem('sidebarCollapsed',String(collapsed));$('#sidebarToggle').setAttribute('aria-pressed',String(collapsed));$('#sidebarToggle').setAttribute('aria-label',collapsed?'Expand sidebar':'Collapse sidebar');});
    function setTheme(light) { document.body.classList.toggle('light-mode',light); localStorage.setItem('lightMode',String(light)); $('#lightMode').checked=light; $$('.theme-label').forEach(label=>label.textContent=light?'Dark mode':'Light mode'); ['sidebarThemeToggle','homeThemeToggle'].forEach(id=>$('#'+id).setAttribute('aria-label',light?'Switch to dark mode':'Switch to light mode')); }
    setTheme(localStorage.getItem('lightMode')==='true');
    ['sidebarThemeToggle','homeThemeToggle'].forEach(id=>$('#'+id).addEventListener('click',()=>setTheme(!document.body.classList.contains('light-mode'))));
    $('#lightMode').addEventListener('change',event=>setTheme(event.target.checked));
    const homeModel=$('#homeModel');
    if ('IntersectionObserver' in window) { const modelObserver=new IntersectionObserver(entries=>entries.forEach(entry=>homeModel.classList.toggle('is-visible',entry.isIntersecting&&document.visibilityState==='visible')),{threshold:.25}); modelObserver.observe(homeModel); document.addEventListener('visibilitychange',()=>homeModel.classList.toggle('is-visible',document.visibilityState==='visible'&&homeModel.getBoundingClientRect().top<innerHeight&&homeModel.getBoundingClientRect().bottom>0)); } else homeModel.classList.add('is-visible');

