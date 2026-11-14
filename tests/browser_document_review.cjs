const {chromium}=require('playwright');
const fs=require('fs');
(async()=>{
  const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH});
  try{
    const page=await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
    const errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.goto('http://127.0.0.1:8765/#resources');
    await page.waitForFunction(()=>document.querySelector('#reviewScope')?.textContent.includes('49 files'));
    const review=(await (await page.request.get('http://127.0.0.1:8765/api/v1/evidence/review')).json()).data;
    if(review.source_files!==49||review.distinct_sources!==39)throw Error('Archive review count mismatch');
    await page.locator('#reviewFilter').fill('Lognormal equation discrepancy');
    const entry=page.locator('.scientific-review-entry').first();
    await entry.locator('summary').first().click();
    await entry.locator('[data-source-passages]').click();
    await entry.locator('.source-passages details').first().waitFor();
    if(!(await entry.textContent()).includes('missing')&&!(await entry.textContent()).includes('lacks'))throw Error('Source discrepancy missing');
    if(!(await entry.locator('.katex').count()))throw Error('Reviewed equation was not typeset');
    for(const width of [1440,390]){
      await page.setViewportSize({width,height:1000});
      await entry.locator('.katex-display').first().scrollIntoViewIfNeeded();
      if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+2))throw Error('Source review overflows viewport');
      await page.screenshot({path:`tmp/ui-checks/document-review-${width}.png`});
    }
    await page.locator('#reviewFilter').fill('NIST');
    await page.locator('.scientific-review-entry').filter({hasText:'Lognormal distribution'}).locator('summary').first().click();
    if(!(await page.locator('#reviewSources a[href^="https://itl.nist.gov/"]').count()))throw Error('Consulted website link missing');
    const note=review.notes.find(n=>n.title==='Lognormal equation discrepancy and moment reconstruction');
    const web=review.notes.find(n=>n.kind==='consulted_web_reference');
    await page.evaluate(sources=>{navigate('evidence');renderSourceTrail(sources);},[note,web].map(({text,...rest})=>rest));
    await page.locator('[data-source-index="0"]').click();
    await page.locator('.source-excerpt .katex').first().waitFor();
    await page.locator('[data-source-index="1"]').click();
    await page.locator('.source-excerpt a[href^="https://itl.nist.gov/"]').waitFor();
    const invalid=await page.request.post('http://127.0.0.1:8765/api/v1/evidence/excerpt',{data:{ids:[note.supporting_source_ids[0],'document:fake']}});
    if(invalid.status()!==400)throw Error('Unknown batch source not rejected');
    if(errors.length)throw Error(errors.join('\n'));
    fs.writeFileSync('derived/reports/document_review_browser.json',JSON.stringify({files:49,distinctSources:39,liveSourceAnchors:true,sourcePassages:true,renderedMath:true,consultedWebLinks:true,unknownSourceRejected:true,responsiveWidths:[1440,390],javascriptErrors:errors,paidAiCalls:0},null,2));
    console.log('PASS: review inventory, original source excerpts, equations, website links, stale-ID rejection and responsive layouts. No paid AI calls.');
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
