const {chromium}=require('playwright');
const fs=require('fs');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'reduce'}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  const base='http://127.0.0.1:8765';
  await page.goto(base+'/archive');await page.waitForFunction(()=>document.documentElement.dataset.ready==='true');await page.evaluate(()=>{document.querySelector('#gapAnalysisMode').value='basic';document.querySelector('#gapAnalysisMode').dispatchEvent(new Event('change'));});
  await page.evaluate(async()=>{await ArchiveBrowser.openGroup('FLEX');const item=ArchiveBrowser.view.items.find(i=>i.investigation_group==='FLEX'&&i.view!=='reference'&&i.source_path.endsWith('.csv'));await ArchiveBrowser.open(item.source_path);});
  await page.locator('#datasetGaps').click();await page.waitForFunction(()=>researchView.result?.assessment);
  await page.locator('#gapQuestion').fill('How does gravity affect flame size?');await page.locator('#gapForm button[type=submit]').click();
  await page.waitForFunction(()=>researchView.result?.question==='How does gravity affect flame size?');
  if(!(await page.locator('.gap-matrix').textContent()).includes('197 rows'))throw Error('Numeric evidence coverage missing');
  if(!(await page.locator('.gap-verdict').textContent()).includes('not yet supported'))throw Error('Unsupported conclusion not blocked');
  await page.locator('[data-ask-finding=gravity]').click();
  if(!(await page.locator('#copilotQuestion').inputValue()).includes('gravity'))throw Error('SI lost requirement context');
  await page.evaluate(()=>navigate('atlas'));await page.locator('[data-research-tab=gaps]').click();
  fs.mkdirSync('.impeccable/review',{recursive:true});
  for(const width of [1440,390]){
   await page.setViewportSize({width,height:1000});
   if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+2))throw Error('Overflow '+width);
   await page.locator('.gap-verdict').scrollIntoViewIfNeeded();await page.screenshot({path:'.impeccable/review/gap-readiness-'+width+'.png',fullPage:false});
  }
  await page.locator('[data-save-finding=gravity]').click();
  await page.waitForFunction(()=>Studio.view.record?.origin==='evidence_brief');
  const id=await page.evaluate(()=>Studio.view.record.id);
  if(!(await page.locator('#studioEditQuestion').inputValue()).includes('flame size'))throw Error('Question lost');
  await page.evaluate(()=>navigate('lab'));
  await page.evaluate(()=>setLabMode('scattering'));
  await page.locator('#scatteringForm button[type=submit]').click();
  await page.waitForFunction(()=>workspace.optics?.result);
  await page.locator('[data-link-model=scattering]').click();
  await page.locator('#journeyModelReason').fill('Illustrate an assumed aerosol optical response separately from the flame-size question.');
  await page.locator('#journeyAttach').click();
  await page.waitForFunction(()=>Journey.record?.model_links?.length===1);
  await page.reload();await page.waitForFunction(()=>document.documentElement.dataset.ready==='true'&&Journey.record?.model_links?.length===1);
  await page.evaluate(()=>navigate('studio',{id:Journey.record.id}));await page.waitForFunction(()=>Studio.view.record?.model_links?.length===1);
  await page.locator('[data-studio-tab=sources]').click();
  if(!(await page.locator('#studioLinkedModels').textContent()).includes('Illustrate'))throw Error('Model rationale missing');
  if(await page.evaluate(()=>Studio.view.record.id)!==id)throw Error('Model created a different study');
  await page.evaluate(()=>{$('#gapAnalysisMode').value='basic';const c=Journey.record.research_context;setAtlasGroups();$('#gapQuestion').value=c.question;$('#gapGoal').value=c.goal;$('#atlasGroup').value=c.group;researchInvalidate();navigate('atlas');});await page.waitForFunction(()=>researchView.result?.assessment);
  await page.locator('#gapQuestion').fill('A new unanswered question');
  if(await page.locator('[data-save-finding]').count())throw Error('Stale finding remains actionable');
  await page.locator('#gapGoal').selectOption('general');await page.locator('#gapForm button[type=submit]').click();
  await page.waitForFunction(()=>researchView.result?.goal==='general');
  if(!(await page.locator('.gap-verdict').textContent()).includes('Define the response'))throw Error('General question has fabricated coverage');
  if(errors.length)throw Error(errors.join('\n'));
  fs.writeFileSync('derived/reports/gap_journey_browser.json',JSON.stringify({archiveToAssessment:true,numericCoverage:true,scopedSIQuestion:true,savedEvidenceBrief:true,modelRecomputedAndLinked:true,reloadRecovery:true,studioSourcesVisible:true,returnToEvidence:true,staleActionsCleared:true,unknownQuestionHonest:true,viewports:[1440,390],paidAiCalls:0,javascriptErrors:errors},null,2));
  console.log('PASS: Archive → assessment → saved brief → scattering → attach → reload → Studio → evidence.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
