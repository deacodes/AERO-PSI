/* One shared label registry; identity and API requests always use original paths. */
const SourceLabels=(()=>{
 const records=new Map();
 const ready=jsonFetch('/api/v1/archive/datasets').then(r=>{r.items.forEach(i=>records.set(i.source_path,i));}).catch(()=>{});
 function get(path){return records.get(path);}
 function title(path,fallback){return get(path)?.display_name||fallback||String(path||'Source').split('/').at(-1);}
 function tags(path){return (get(path)?.tags||[]).map(t=>`<span class="source-tag">${escapeHTML(t)}</span>`).join('');}
 function caption(path){return `<span class="source-filename">${escapeHTML(get(path)?.filename||String(path).split('/').at(-1))}</span>`;}
 return {ready,get,title,tags,caption};
})();
