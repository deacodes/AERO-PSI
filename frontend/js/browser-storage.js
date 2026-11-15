/* Investigations live in IndexedDB for this origin, never a shared server library. */
const BrowserWork=(()=>{
 const ready=new Promise((resolve,reject)=>{const r=indexedDB.open('aeropsi-private-work',1);r.onupgradeneeded=()=>{for(const name of ['records','history','analyses'])r.result.createObjectStore(name,{keyPath:'id'});};r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(Error('Browser storage unavailable. Enable site storage to save investigations.'));});
 async function read(store,id){const db=await ready;return new Promise((resolve,reject)=>{const r=db.transaction(store).objectStore(store)[id?'get':'getAll'](...(id?[id]:[]));r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);});}
 async function save(record,previous,store='records'){const db=await ready;return new Promise((resolve,reject)=>{const tx=db.transaction([store,'history'],'readwrite'),objects=tx.objectStore(store);const check=objects.get(record.id);check.onsuccess=()=>{const current=check.result;if(previous&&(!current||current.revision!==previous.revision)){tx.abort();return;}if(previous)tx.objectStore('history').put({id:record.id+':'+previous.revision,record:previous});objects.put(record);};tx.oncomplete=()=>resolve(record);tx.onabort=()=>reject(Error('Work changed in another tab, or browser storage is full. Export unsaved work before reloading.'));tx.onerror=()=>reject(tx.error);});}
 async function request(url,options,network){const u=new URL(url,location.origin),path=u.pathname,id=u.searchParams.get('id');
  if(!options?.method||options.method==='GET'){
   if(path==='/api/v1/studio/library'){const records=await read('records');return {items:records.map(r=>({id:r.id,origin:'studio',origin_label:r.origin,title:r.content.title,question:r.content.question,kind:r.content.kind,created_at:r.created_at,updated_at:r.updated_at,revision:r.revision,archived:r.archived,completed_steps:r.content.steps.filter(s=>s.completed).length,total_steps:r.content.steps.length})),warnings:[]};}
   if(path==='/api/v1/studio/history')return (await read('history')).filter(v=>v.id.startsWith(id+':')).map(v=>v.record).sort((a,b)=>b.revision-a.revision);
   if(path==='/api/v1/studio/record'||path==='/api/v1/si/investigation'){const r=await read(path.includes('/studio/')?'records':'analyses',id);if(!r)throw Error('This investigation is not saved in this browser.');return r;}
  }
  if(path.startsWith('/api/v1/studio/')){const payload=JSON.parse(options.body),previous=payload.id?await read('records',payload.id):null;if(payload.id&&!previous)throw Error('Investigation not found in this browser.');if(previous&&payload.revision!==previous.revision)throw Error('A newer revision exists. Reopen this investigation.');const result=await network(url,{...options,body:JSON.stringify({...payload,...(previous?{browser_record:previous}:{})})});return save(result,previous);}
  const result=await network(url,options);if(path==='/api/v1/si/investigate'&&result.id)await save(result,null,'analyses');return result;
 }
 return {request};
})();
