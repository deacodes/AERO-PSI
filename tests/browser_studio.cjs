const {chromium}=require('playwright');
const fs=require('fs');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  const base='http://127.0.0.1:8765';
  await page.goto(base+'/studio');
  await page.waitForFunction(()=>document.documentElement.dataset.ready==='true',{timeout:30000});
  if(errors.length)throw Error(errors.join('\n'));
  await page.locator('#studioNew').click();
  await page.locator('#studioQuestion').fill('Browser fixture: compare a sourced test table and numerical scenario');
  // Disabled SI is an explicit error, not a silently substituted generic plan.
  await page.locator('#studioGenerate').click();
  await page.waitForFunction(()=>document.querySelector('#studioStatus').textContent.includes('disabled'));
  await page.locator('#studioManual').click();
  await page.locator('#studioEditStep summary').click();
  await page.locator('[data-step-field=title]').fill('Inspect the data and its assumptions');
  await page.locator('[data-step-field=method]').fill('**Test fixture, not NASA data.**\n\n1. Inspect units and missing values.\n2. Compare the reported values.\n\n\\[ D=\\frac{k_B T}{3\\pi\\mu d} \\]\n\n<script>window.studioInjected=true</script>');
  await page.locator('[data-step-field=inputs]').fill('Explicit fixture values with column units.');
  await page.locator('[data-step-field=expected_output]').fill('A traceable graph and a record of limitations.');
  await page.locator('#studioApplyStep').click();
  await page.locator('#studioStepContent .katex').first().waitFor();
  if(await page.evaluate(()=>window.studioInjected))throw Error('Unsafe Markdown executed');
  await page.locator('[data-toggle-step]').first().check();
  await page.waitForFunction(()=>document.querySelector('#studioProgressLabel').textContent==='1 / 1 complete');
  await page.waitForFunction(()=>document.querySelector('#page-studio').getAttribute('aria-busy')!=='true');
  const id=new URL(page.url()).searchParams.get('id');
  await page.reload();await page.waitForFunction(()=>document.documentElement.dataset.ready==='true');
  await page.locator('[data-toggle-step]').first().waitFor();
  if(!await page.locator('[data-toggle-step]').first().isChecked())throw Error('Progress did not persist');
  await page.locator('[data-studio-tab=results]').click();
  await page.locator('#studioToggleData').click();
  await page.locator('#studioDataName').fill('Explicit browser fixture');
  await page.locator('#studioDataReference').fill('Synthetic values supplied only for interface verification; not observations.');
  await page.locator('#studioDataUnits').fill('s,V,K');
  await page.locator('#studioCsv').fill('Time,Signal,Temperature\n0,0.1,290\n1,,292\n2,0.3,294\n3,0.2,296');
  await page.locator('#studioAddData').click();await page.locator('#studioChart svg').waitFor();
  await page.waitForFunction(()=>document.querySelector('#page-studio').getAttribute('aria-busy')!=='true');
  if(await page.locator('#studioInterpret').isDisabled())throw Error('First imported dataset left actions disabled');
  for(const type of ['line','scatter','bar','histogram','heatmap']){
   await page.locator('#studioChartType').selectOption(type);await page.locator('#studioChart svg').waitFor();
   if(await page.locator('#studioChart [data-rows]').count()===0)throw Error('No interactive marks: '+type);
  }
  await page.locator('#studioChartType').selectOption('line');
  await page.locator('#studioChart [data-rows]').first().click();
  if(await page.locator('#studioPointStep').isDisabled())throw Error('Point action not enabled');
  await page.locator('#studioGraphQuestion').fill('Explain this selected fixture point');await page.locator('#studioInterpret').click();
  await page.waitForFunction(()=>document.querySelector('#studioGraphAnswer').textContent.length>10);
  await page.waitForFunction(()=>document.querySelector('#page-studio').getAttribute('aria-busy')!=='true');
  const saved=(await (await page.request.get(base+'/api/v1/studio/record?id='+id)).json()).data;
  if(saved.datasets[0].rows[1][1]!==null)throw Error('Missing cell became zero');
  if(saved.ai_reviews[0].row_indices[0]!==0)throw Error('Selected point provenance missing');
  const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#studioChartSvg').click()]);
  if(!download.suggestedFilename().endsWith('.svg'))throw Error('Chart export missing');
  await page.locator('#studioPointStep').click();await page.locator('#studioEditStep summary').click();
  await page.locator('#studioStepTool').selectOption('simulate_coagulation');await page.locator('#studioApplyStep').click();
  await page.locator('#studioRawInputs summary').click();
  await page.locator('#studioToolInputs').fill(JSON.stringify({scenario:{section_count:8,output_points:3,residence_time_s:1,initial_number_concentration_m3:1e9}}));
  await page.locator('#studioRunTool').click();
  await page.waitForFunction(()=>document.querySelector('#studioStatus').textContent.includes('Calculation and inputs saved'));
  const computed=(await (await page.request.get(base+'/api/v1/studio/record?id='+id)).json()).data;
  if(computed.runs.length!==1||computed.datasets.length!==4)throw Error('Real calculation or plot datasets missing');
  await page.locator('[data-studio-tab=method]').click();
  await page.locator('#studioEditStep summary').click();
  await page.locator('[data-step-field=inputs]').fill('Changed assumption: rerun before interpretation');await page.locator('#studioApplyStep').click();
  await page.waitForFunction(()=>document.querySelector('#studioStatus').textContent.includes('Step saved'));
  const changed=(await (await page.request.get(base+'/api/v1/studio/record?id='+id)).json()).data;
  if(!changed.runs[0].stale)throw Error('Changed method left calculation current');
  await page.locator('[data-open-step]').first().click();
  const screenshots=[];fs.mkdirSync('.impeccable/review',{recursive:true});
  for(const width of [1440,390]){
   await page.setViewportSize({width,height:1000});
   await page.evaluate(()=>scrollTo(0,0));
   if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+2))throw Error('Studio overflow '+width);
   const path=`.impeccable/review/studio-${width}.png`;await page.screenshot({path,fullPage:true});screenshots.push(path);
  }
  await page.setViewportSize({width:1440,height:1000});
  await page.locator('#sidebarThemeToggle').click();await page.screenshot({path:'.impeccable/review/studio-light.png',fullPage:true});
  await page.locator('#sidebarThemeToggle').click();
  await page.locator('#studioBack').click();await page.locator(`[data-record="${id}"]`).waitFor();
  await page.screenshot({path:'.impeccable/review/studio-library.png'});
  await page.goto(base+'/');await page.waitForFunction(()=>document.documentElement.dataset.ready==='true');
  const glow=await page.locator('.landing-hero').evaluate(el=>getComputedStyle(el,'::before').backgroundImage);
  if(glow!=='none')throw Error('Header gradient remains');
  await page.locator('.home-footer').scrollIntoViewIfNeeded();await page.screenshot({path:'.impeccable/review/home-footer.png'});
  await page.locator('.home-footer [data-jump=studio]').click();await page.waitForURL('**/studio');
  for(const path of ['/models','/archive','/gaps','/science','/resources']){
   await page.goto(base+path);await page.waitForFunction(()=>document.documentElement.dataset.ready==='true');
   if(!await page.locator('.page.active').count())throw Error('Missing routed page '+path);
  }
  // Back/forward uses real page paths.
  await page.locator('[data-page=studio]').click();await page.locator('[data-page=lab]').click();await page.goBack();
  if(!await page.locator('#page-studio').evaluate(e=>e.classList.contains('active')))throw Error('Back navigation failed');
  if(errors.length)throw Error(errors.join('\n'));
  fs.writeFileSync('derived/reports/studio_browser.json',JSON.stringify({manualPlan:true,providerFailureVisible:true,completionPersists:true,markdownMath:true,safeMarkdown:true,chartTypes:5,missingValuesPreserved:true,pointProvenance:true,realSolver:true,staleResultDetection:true,directRoutes:true,browserHistory:true,headerGradientRemoved:true,footerCTA:true,viewportWidths:[1440,390],javascriptErrors:errors,paidAiCalls:0},null,2));
  console.log('PASS: Studio creation, progress, graphs, actual solver, provenance, revisions, routes and homepage CTA. No paid AI calls.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
