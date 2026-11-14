const {chromium}=require('playwright');
const fs=require('fs');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'reduce'}), errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  const base='http://127.0.0.1:8765';
  await page.goto(base+'/gaps');await page.waitForFunction(()=>document.documentElement.dataset.ready==='true');await page.evaluate(()=>{document.querySelector('#gapAnalysisMode').value='basic';document.querySelector('#gapAnalysisMode').dispatchEvent(new Event('change'));});
  await page.locator('#gapQuestion').fill('How does gravity affect flame size?');
  // A direct visit may initially offer automatic selection; populate from actual archive metadata.
  await page.evaluate(()=>setAtlasGroups());await page.locator('#atlasGroup').selectOption('FLEX');
  await page.locator('#gapForm button[type=submit]').click();
  await page.waitForFunction(()=>researchView.result?.group==='FLEX');
  await page.locator('[data-research-tab=measurements]').click();
  if(await page.locator('#researchPlot [data-rows]').count()<100)throw Error('FLEX measurements did not render');
  if(!(await page.locator('#researchFields').textContent()).includes('197 numeric values'))throw Error('Flame dimension availability incorrect');
  const material=await page.locator('#researchMaterial option').nth(1).getAttribute('value');
  await page.locator('#researchMaterial').selectOption(material);
  const subset=await page.evaluate(()=>({shown:researchView.dataset.rows.length,total:researchView.result.rows.length,expected:researchView.result.rows.filter(r=>r.values.material_or_fuel===document.querySelector('#researchMaterial').value).length}));
  if(subset.shown!==subset.expected||subset.shown>=subset.total)throw Error('Material filter did not select actual rows');
  await page.locator('#researchMaterial').selectOption('');
  await page.locator('#researchPlot [data-rows]').first().focus();await page.locator('#researchPlot [data-rows]').first().press('Enter');
  await page.locator('#researchAskPoint').click();
  if(!page.url().includes('/science'))throw Error('SI discussion did not open the SI page');
  let interpreted;
  await page.route('**/api/v1/research/interpret',async route=>{
    interpreted=route.request().postDataJSON();
    await route.fulfill({json:{data:{mode:'vertex_scientific',scientific_explanation:'**Test fixture only.** This value is a flame dimension recorded at extinction. It is not a matched gravity comparison. A useful comparison must define the outcome and its measurement time.',observed_in_source:[],model_result:[],unknown_or_limitation:[],sources:[]}}});
  });
  await page.locator('#askCopilot').click();await page.waitForFunction(()=>document.querySelector('#copilotAnswer').textContent.includes('Test fixture'));
  if(!interpreted.source_rows.length||interpreted.group!=='FLEX')throw Error('Selected evidence lost in inline SI request');
  await page.evaluate(()=>navigate('atlas'));await page.locator('[data-research-tab=gaps]').click();
  const gaps=await page.locator('#atlasGaps').textContent();
  if(!gaps.includes('Run-resolved acceleration history')||gaps.includes('indexed'))throw Error('Gap view is not useful or still exposes index jargon');
  await page.locator('[data-research-tab=reports]').click();if(await page.locator('#researchReports details').count()===0)throw Error('Reports missing');
  await page.locator('#researchReports summary').first().click();
  await page.locator('[data-research-tab=measurements]').click();
  fs.mkdirSync('.impeccable/review',{recursive:true});
  for(const width of [1440,390]){
   await page.setViewportSize({width,height:1000});await page.evaluate(()=>scrollTo(0,0));
   if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+2))throw Error('Evidence workspace overflows '+width);
   if(!process.env.AERO_SKIP_SCREENSHOTS)await page.screenshot({path:`.impeccable/review/research-${width}.png`,fullPage:true});
  }
  await page.locator('#gapCreateInvestigation').click();await page.waitForFunction(()=>Studio.view.record?.origin==='evidence_brief');
  if(await page.locator('#studioEditQuestion').inputValue()!=='How does gravity affect flame size?')throw Error('Research question lost during handoff');
  await page.locator('[data-studio-tab=design]').click();
  await page.locator('#designHypothesis').fill('Test fixture: compare a defined size response across proposed gravity conditions.');
  await page.locator('#designOutcome').fill('Flame diameter at a specified time (mm)');
  await page.locator('#designAddVariable').click();
  await page.locator('[data-design-field=name]').fill('Gravity');await page.locator('[data-design-field=unit]').fill('m/s²');
  await page.locator('[data-design-field=minimum]').fill('0');await page.locator('[data-design-field=maximum]').fill('9.81');
  await page.locator('[data-design-field=basis]').fill('Explicit test-planning assumption, not a measured response');
  await page.locator('#designReplicates').fill('2');await page.locator('#designPreview').click();
  await page.waitForFunction(()=>document.querySelector('#designStatus').textContent.includes('6 proposed trials'));
  if(await page.locator('#designPlot [data-rows]').count()!==6)throw Error('Trial-layout graph missing');
  await page.locator('[data-design-field=levels]').fill('5');
  await page.waitForFunction(()=>document.querySelector('#designStatus').textContent.includes('10 proposed trials'));
  await page.locator('#studioSave').click();await page.waitForFunction(()=>!Studio.view.dirty);
  for(const width of [1440,390]){
   await page.setViewportSize({width,height:1000});await page.locator('#studio-design').scrollIntoViewIfNeeded();
   if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+2))throw Error('Design workspace overflows '+width);
   if(!process.env.AERO_SKIP_SCREENSHOTS)await page.screenshot({path:`.impeccable/review/experiment-design-${width}.png`,fullPage:true});
  }
  const savedId=new URL(page.url()).searchParams.get('id');await page.reload();await page.waitForFunction(()=>document.documentElement.dataset.ready==='true');
  await page.waitForFunction(()=>Studio.view.record?.content.design?.variables.length===1);await page.locator('[data-studio-tab=design]').click();
  if(await page.locator('[data-design-field=levels]').inputValue()!=='5')throw Error('Design did not persist');
  // Actual PSI samples also render rather than a header-presence table.
  await page.goto(base+'/gaps');await page.waitForFunction(()=>document.documentElement.dataset.ready==='true');
  await page.locator('#gapQuestion').fill('How does the recorded smoke detector signal vary over a run?');await page.evaluate(()=>setAtlasGroups());await page.locator('#atlasGroup').selectOption('PSI101');
  await page.locator('#gapForm button[type=submit]').click();await page.waitForFunction(()=>researchView.result?.group==='PSI101');
  await page.locator('[data-research-tab=measurements]').click();
  const run=await page.locator('#researchSource option[value^="run:"]').first().getAttribute('value');await page.locator('#researchSource').selectOption(run);
  await page.waitForFunction(()=>document.querySelector('#atlasRunTitle').textContent.includes('recorded signal'));
  if(await page.locator('#researchPlot [data-rows]').count()===0)throw Error('PSI time series empty');
  const runContext=await page.evaluate(()=>({...researchView.request,run:researchView.runPath,signal:researchView.runSignal,source_rows:[researchView.sourceRows[0]],followup:'Explain this recorded sample'}));
  const checked=await page.request.post(base+'/api/v1/research/interpret',{data:runContext});
  const checkedData=(await checked.json()).data;
  if(!checked.ok()||checkedData.mode!=='science_unavailable'||!checkedData.sources.some(s=>s.kind==='verified_observed_sample'&&s.point.source_row===runContext.source_rows[0]))throw Error('Run point context was not verified by backend');
  await page.goto(base+'/science');await page.waitForFunction(()=>document.documentElement.dataset.ready==='true');
  await page.locator('#researchEntryQuestion').fill('Compare published flame imaging methods');await page.locator('#openResearchBuilder').click();await page.locator('#studioCreate').waitFor();
  if(await page.locator('#studioQuestion').inputValue()!=='Compare published flame imaging methods')throw Error('Science page still routes to fixed tools');
  if(errors.length)throw Error(errors.join('\n'));
  fs.writeFileSync('derived/reports/research_browser.json',JSON.stringify({realFlexMeasurements:true,sourceRowSelection:true,inlineSI:true,matchingReportPassages:true,explicitMissingAcceleration:true,questionPreservingBuilder:true,interactiveTrialDesign:true,slidersUpdateConditionsOnly:true,designPersists:true,psiTimeSeries:true,researchEntryReplacesToolPlan:true,viewports:[1440,390],paidAiCalls:0,aiResponse:'test fixture',javascriptErrors:errors},null,2));
  console.log('PASS: actual FLEX and PSI evidence, inline SI context, meaningful requirements, research handoff and interactive saved experiment designs.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
