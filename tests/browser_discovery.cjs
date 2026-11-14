const {chromium}=require('playwright');const fs=require('fs');
(async()=>{const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH});try{
const page=await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'reduce'}),errors=[];page.on('pageerror',e=>errors.push(e.message));
await page.goto('http://127.0.0.1:8765/archive');await page.waitForFunction(()=>document.documentElement.dataset.ready==='true'&&typeof discovery!=='undefined'&&discovery.rankCurrent);await page.evaluate(()=>{document.querySelector('#gapAnalysisMode').value='basic';document.querySelector('#gapAnalysisMode').dispatchEvent(new Event('change'));});await page.locator('[data-archive-tab=ranking]').click();
if(!(await page.locator('.question-rank').first().textContent()).includes('PSI10'))throw Error('Detector evidence not first');
await page.locator('[data-discovery-question]').last().click();await page.waitForFunction(()=>discovery.rankCurrent&&discovery.ranking.goal==='extinction');
if(!(await page.locator('.question-rank').first().textContent()).includes('FLEX'))throw Error('Question did not reorder evidence');
await page.locator('.question-rank > summary').first().click();await page.locator('[data-plan-group]').first().click();await page.waitForFunction(()=>researchView.result?.group==='FLEX');
if(!(await page.locator('#gapQuestion').inputValue()).toLowerCase().includes('droplet'))throw Error('Question handoff failed');
await page.locator('[data-research-tab=gaps]').click();await page.locator('#atlasGaps details').first().evaluate(e=>e.open=true);await page.locator('#atlasGaps .discovery-source').first().evaluate(e=>e.open=true);await page.locator('#atlasGaps [data-discovery-source]').first().click();await page.waitForSelector('#atlasGaps .discovery-excerpt pre');
if(!(await page.locator('#atlasGaps .discovery-excerpt pre').first().textContent()).trim())throw Error('Source record empty');
await page.locator('#gapsWithSI').click();if(!page.url().includes('/science'))throw Error('Discussion did not open SI');
await page.locator('#copilotQuestion').fill('What does this extinction diameter mean?');await page.locator('#askCopilot').click();await page.waitForFunction(()=>!document.querySelector('#askCopilot').disabled);
if(!(await page.locator('#copilotAnswer').textContent()).includes('disabled'))throw Error('Unavailable SI hidden');
await page.locator('[data-research-tab=gaps]').click();await page.locator('[data-develop-finding]').first().click();await page.locator('#studioCreate').waitFor();if(!(await page.locator('#studioQuestion').inputValue()).includes('Focus:'))throw Error('Missing finding context');
for(const width of [1440,390]){await page.setViewportSize({width,height:1000});for(const route of ['mission','atlas']){await page.evaluate(route=>navigate(route),route);if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+2))throw Error('Overflow '+route);}}
if(errors.length)throw Error(errors.join('\n'));fs.writeFileSync('derived/reports/discovery_browser.json',JSON.stringify({questionReorders:true,groupHandoff:true,exactSourceDrilldown:true,inlineSIUnavailableHonest:true,findingToResearch:true,responsiveWidths:[1440,390],javascriptErrors:errors},null,2));console.log('PASS: ranking, source drilldown, inline SI and finding-to-investigation handoff.');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1});
