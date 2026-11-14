const {chromium}=require('playwright');const fs=require('fs');
(async()=>{const b=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH});try{
const p=await b.newPage({viewport:{width:1440,height:1000},reducedMotion:'reduce'});const errors=[],calls=[];p.on('pageerror',e=>errors.push(e.message));
await p.route('**/api/v1/archive/interpret',async route=>{calls.push(route.request().postDataJSON());await route.fulfill({json:{data:{mode:'vertex_scientific',scientific_explanation:'Example explanation.',sources:[],information_scope:{requested:calls.at(-1).mode,general_science_included:true,source_claims_included:false,web_search_performed:false}}}});});
await p.goto('http://127.0.0.1:8765/');await p.waitForFunction(()=>document.documentElement.dataset.ready==='true');
fs.mkdirSync('.impeccable/review',{recursive:true});
for(const width of [1440,390]){await p.setViewportSize({width,height:950});if(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth+2))throw Error('Home overflow');await p.locator('.home-research-path').scrollIntoViewIfNeeded();await p.screenshot({path:`.impeccable/review/home-content-${width}.png`});}
await p.locator('[data-home-example=scattering]').click();if(!(await p.locator('#homeExampleQuestion').textContent()).includes('multi-angle'))throw Error('Question choice failed');await p.locator('#homeAskQuestion').click();if(!(await p.locator('#copilotQuestion').inputValue()).includes('multi-angle'))throw Error('Question not carried');
await p.locator('#siBrowseEvidence').click();await p.locator('#siEvidenceGroup').selectOption('FLEX');await p.locator('[data-si-file]').first().click();await p.waitForSelector('#siEvidencePreview:not([hidden])');
if(!(await p.locator('#siEvidenceScope').textContent()).includes('not the complete table'))throw Error('Scope missing');
await p.locator('#siEvidencePreview').scrollIntoViewIfNeeded();if(await p.locator('.copilot-panel').evaluate(e=>e.scrollWidth>e.clientWidth+2))throw Error('Conversation content clipped');await p.screenshot({path:'.impeccable/review/si-picker-390.png'});await p.locator('#siAttachEvidence').click();
if(calls.length)throw Error('Attaching caused AI call');if(!(await p.locator('#copilotQuestion').inputValue()).includes('multi-angle'))throw Error('Draft lost');
await p.locator('#answerMode').selectOption('explain');await p.locator('#askCopilot').click();await p.waitForFunction(()=>!document.querySelector('#askCopilot').disabled);
if(calls.at(-1).mode!=='explain'||!calls.at(-1).source_path)throw Error('Mode/context missing');
await p.locator('#answerMode').selectOption('evidence');await p.locator('#askCopilot').click();await p.waitForFunction(()=>!document.querySelector('#askCopilot').disabled);if(calls.at(-1).mode!=='evidence'||calls.at(-1).history.length)throw Error('Mode isolation failed');
await p.locator('#scienceContextClear').click();if(await p.locator('#scienceContext').isVisible())throw Error('Clear failed');if(errors.length)throw Error(errors.join('\n'));console.log('PASS: homepage questions, mobile layout, dataset browsing/preview, attachment, draft preservation, source modes; no paid AI.');
}finally{await b.close();}})().catch(e=>{console.error(e);process.exitCode=1});
