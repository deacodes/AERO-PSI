const {chromium}=require('playwright');const fs=require('fs');
(async()=>{const b=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH});try{
 const p=await b.newPage({viewport:{width:1440,height:1000},reducedMotion:'reduce'}),errors=[],calls=[];p.on('pageerror',e=>errors.push(e.message));
 for(const endpoint of ['archive/interpret','research/interpret','si/interpret-model','si/interpret-point'])await p.route('**/api/v1/'+endpoint,async route=>{calls.push({endpoint,payload:route.request().postDataJSON()});await route.fulfill({json:{data:endpoint==='si/interpret-point'?{mode:'vertex_verified_context',interpretation:'**Fixture** $N=1$',supported:[],limitations:[],sources:[]}:{mode:'vertex_scientific',scientific_explanation:'**Fixture** $N=1$',sources:[]}}});});
 await p.goto('http://127.0.0.1:8765/archive');await p.waitForFunction(()=>document.documentElement.dataset.ready==='true'&&ArchiveBrowser.view.items);await p.evaluate(()=>{document.querySelector('#gapAnalysisMode').value='basic';document.querySelector('#gapAnalysisMode').dispatchEvent(new Event('change'));});
 await p.evaluate(async()=>{await ArchiveBrowser.openGroup('FLEX');await ArchiveBrowser.open(ArchiveBrowser.view.items.find(i=>i.investigation_group==='FLEX'&&i.view!=='reference').source_path);});
 await p.locator('#datasetGrid [data-source-row-index]').first().click();await p.locator('#archiveSIRow').click();
 if(!p.url().includes('/science'))throw Error('Archive did not route to SI');
 if(await p.locator('.context-si').count())throw Error('Floating SI panel still exists');
 await p.locator('#askCopilot').click();await p.waitForSelector('#copilotAnswer .katex');
 await p.locator('#copilotQuestion').fill('What are the units?');await p.locator('#askCopilot').click();await p.waitForFunction(()=>!document.querySelector('#askCopilot').disabled);
 if(calls[1].payload.history.length!==2||calls[1].payload.source_row!==calls[0].payload.source_row)throw Error('Frozen row or follow-up history lost');
 await p.evaluate(()=>navigate('lab'));await p.locator('[data-lab=scattering]').click();await p.locator('#scatteringForm button[type=submit]').click();await p.waitForSelector('.angular-hit');await p.locator('#interpretScattering').click();
 if(!p.url().includes('/science'))throw Error('Model did not route to SI');await p.locator('#askCopilot').click();await p.waitForFunction(()=>!document.querySelector('#askCopilot').disabled);
 if(calls.at(-1).endpoint!=='si/interpret-model'||calls.at(-1).payload.history.length)throw Error('Model context mixed with archive');
 await p.evaluate(()=>{navigate('lab');setLabMode('coagulation');});await p.locator('#duration').fill('1');await p.locator('#coagForm button[type=submit]').click();await p.waitForFunction(()=>state.currentCoag);
 await p.evaluate(()=>askSIAboutPoint('coagulation',0));await p.locator('#askCopilot').click();await p.waitForFunction(()=>!document.querySelector('#askCopilot').disabled);
 if(calls.at(-1).endpoint!=='si/interpret-point')throw Error('Point context missing');
 await p.evaluate(()=>{navigate('atlas');setAtlasGroups();});await p.locator('#gapQuestion').fill('How does gravity affect flame size?');await p.locator('#atlasGroup').selectOption('FLEX');await p.locator('#gapForm button[type=submit]').click();await p.waitForFunction(()=>researchView.result?.assessment);
 await p.locator('[data-ask-finding=gravity]').click();if(!p.url().includes('/science'))throw Error('Gap finding did not route to SI');await p.locator('#askCopilot').click();await p.waitForFunction(()=>!document.querySelector('#askCopilot').disabled);
 if(calls.at(-1).endpoint!=='research/interpret')throw Error('Gap request not grounded');
 if(await p.locator('#investigationContext').isVisible()||await p.locator('#researchJourney').isVisible())throw Error('Persistent top bar remains');
 fs.mkdirSync('.impeccable/review',{recursive:true});for(const width of [1440,390]){await p.setViewportSize({width,height:950});if(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth+2))throw Error('SI overflow');await p.screenshot({path:'.impeccable/review/si-unified-'+width+'.png'});}
 await p.locator('#scienceContextClear').click();if(await p.locator('#answerMode').isDisabled()||await p.locator('#scienceContext').isVisible())throw Error('Context clear failed');
 if(errors.length)throw Error(errors.join('\n'));console.log('PASS: archive rows + follow-ups, models, graph points and gap findings share SI; context isolation, Markdown/math, no popup/top bars, desktop/mobile. No paid AI calls.');
}finally{await b.close();}})().catch(e=>{console.error(e);process.exitCode=1});
