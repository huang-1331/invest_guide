// Optional browser regression suite: requires Playwright and Chromium locally.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
(async()=>{
 const {createApp}=await import('../server/index.js');
 const {createAdapter,COMPANIES}=await import('../server/opendart.js');
 let mode='ok';
 const server=createApp({adapter:createAdapter({apiKey:'synthetic-test-credential',ttlMs:0,fetchImpl:async url=>{
  const corp=url.searchParams.get('corp_code');
  const rcept_no='20260316000001';
  if(mode==='error')return {ok:true,json:async()=>({status:'020'})};
  if(url.pathname.endsWith('list.json'))return {ok:true,json:async()=>({status:'000',list:[{rcept_no,corp_code:corp,rcept_dt:'20260316'}]})};
  const year=url.searchParams.get('bsns_year'),report=url.searchParams.get('reprt_code');
  return {ok:true,json:async()=>({status:'000',list:[
   {sj_div:'BS',account_id:'ifrs-full_Assets',account_nm:'자산총계',thstrm_amount:'1,234,567'},
   {sj_div:'IS',account_id:'ifrs-full_Revenue',account_nm:'매출액',thstrm_amount:'100',thstrm_add_amount:'300'}
  ].map(r=>({...r,corp_code:corp,bsns_year:year,reprt_code:report,currency:'KRW',rcept_no}))})};
 }})});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const base=`http://127.0.0.1:${server.address().port}`;
 let browser;
 try {
  browser=await chromium.launch({headless:true});
  const page=await browser.newPage({viewport:{width:1280,height:900}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base);await page.waitForSelector('.company-card');
  assert.equal(await page.locator('.company-card').count(),4);
  await page.locator('#search').fill('삼성');assert.equal(await page.locator('.company-card').count(),1);
  await page.locator('[data-company="005930"]').click();
  await page.waitForSelector('.financial-table');
  assert.match(await page.locator('#financials').innerText(),/실제 공시 자료/);
  assert.match(await page.locator('#financials').innerText(),/1,234,567/);
  assert.match(await page.locator('#financials').innerText(),/자료 없음/);
  assert.match(await page.locator('#financials').innerText(),/2026-03-16/);
  assert.match(await page.locator('#dialog').innerText(),/가격·변동률·차트는 임의의 예시/);
  await page.selectOption('[name=fsDiv]','OFS');await page.selectOption('[name=reportCode]','11012');
  await page.locator('.financial-form button').click();
  await page.waitForFunction(()=>document.querySelector('.financial-result').textContent.includes('실제 공시 자료 · 별도'));
  assert.match(await page.locator('#financials').innerText(),/300/);
  await page.keyboard.press('Escape');
  await page.locator('#search').fill('없는기업');assert.equal(await page.locator('.company-card').count(),0);
  await page.locator('#search').fill('');await page.locator('[data-save="005930"]').click();await page.reload();
  await page.locator('[data-nav=saved]').click();assert.equal(await page.locator('.company-card').count(),1);
  await page.locator('[data-nav=learning]').click();assert.equal(await page.locator('.full-lessons article').count(),4);
  await page.locator('a[href="#lesson-01"]').last().click();await page.locator('[data-answer=true]').click();assert.match(await page.locator('.answer').innerText(),/맞아요/);await page.keyboard.press('Escape');
  await page.locator('[data-nav=glossary]').click();assert.equal(await page.locator('.glossary-item').count(),10);
  await page.locator('[data-term="0"]').click();assert.equal(await page.locator('#per').innerText(),'10.0');await page.keyboard.press('Escape');
  for(const id of Object.keys(COMPANIES)) {
   await page.goto(base+'/#company-'+id);await page.waitForSelector('.financial-table');
   assert.match(await page.locator('#dialog h2').innerText(),new RegExp(COMPANIES[id].name));
   await page.reload();await page.waitForSelector('.financial-table');await page.keyboard.press('Escape');
  }
  // A new period bypasses prior successful cache to exercise a provider failure.
  await page.goto(base+'/#company-005930');await page.waitForSelector('.financial-table');mode='error';
  await page.locator('[name=year]').fill('2024');await page.locator('.financial-form button').click();
  await page.waitForFunction(()=>document.querySelector('.financial-result').textContent.includes('요청 한도 초과'));
  assert.equal(await page.locator('.financial-table').count(),0);assert.match(await page.locator('#financials').innerText(),/평가 불가/);
  // Mobile viewport and keyboard closure retain working UI without horizontal document overflow.
  await page.setViewportSize({width:375,height:812});await page.keyboard.press('Escape');
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),true);
  await page.goto(base+'/#company-035420');await page.waitForSelector('.financial-result .notice');
  assert.equal(await page.evaluate(()=>document.querySelector('dialog').scrollWidth<=document.querySelector('dialog').clientWidth),true);
  await page.keyboard.press('Escape');assert.equal(await page.locator('dialog').evaluate(d=>d.open),false);
  assert.deepEqual(errors,[]);
  console.log('PASS: desktop/mobile, four companies, direct-link/reload, search, favorites, lessons/quiz/PER, provenance, basis/report selection, provider failure, no JS errors (synthetic upstream fixtures).');
 }finally{await browser?.close();await new Promise(r=>server.close(r));}
})().catch(e=>{console.error(e);process.exitCode=1;});
