const {chromium}=require('playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH});
 try{
  const page=await browser.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(process.env.AERO_TEST_URL||'http://127.0.0.1:8000/gaps');
  await page.waitForFunction(()=>document.documentElement.dataset.ready==='true');await page.evaluate(()=>{document.querySelector('#gapAnalysisMode').value='basic';document.querySelector('#gapAnalysisMode').dispatchEvent(new Event('change'));});
  for(const [question,group,goal] of [
   ['How does gravity affect flame size?','FLEX','flame_geometry'],
   ['What measurements would let us validate aerosol coagulation under different gravity conditions?','PSI101','coagulation'],
   ['Can the supplied measurements validate a multi-angle scattering model?','PSI102','scattering']]){
   await page.locator('#gapQuestion').fill(question);await page.evaluate(()=>setAtlasGroups());
   await page.locator('#atlasGroup').selectOption(group);await page.locator('#gapGoal').selectOption(goal);
   await page.locator('#gapForm button[type=submit]').click();
   await page.waitForFunction(group=>researchView.result?.group===group&&researchView.result?.assessment,group);
   await page.waitForFunction(()=>!document.querySelector('#gapForm button[type=submit]').disabled);
   if((await page.locator('#atlasRunTitle').textContent())==='Evidence unavailable')throw Error('Evidence failed: '+group);
  }
  await page.route('**/api/v1/research/explore',route=>route.fulfill({json:{data:{question:'legacy response'}}}));
  await page.locator('#gapForm button[type=submit]').click();
  await page.waitForFunction(()=>document.querySelector('#atlasRunClass').textContent.includes('backend is older'));
  if(await page.locator('#atlasRunTitle').textContent()!=='Evidence unavailable')throw Error('Failure mislabeled as report evidence');
  if(!(await page.locator('#gapCreateInvestigation').isDisabled()))throw Error('Stale study action remains enabled');
  if(await page.evaluate(()=>researchView.result!==null))throw Error('Stale result remains active');
  if(errors.length)throw Error(errors.join('\n'));
  console.log('PASS: FLEX, PSI101, PSI102 current responses render; old-server response explains restart and clears stale actions. No AI calls.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
