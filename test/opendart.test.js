import test from 'node:test';
import assert from 'node:assert/strict';
import {createAdapter,COMPANIES,validateQuery,parseAmount} from '../server/opendart.js';
import {createApp} from '../server/index.js';
import {financialMarkup} from '../dist/financials.js';
import {companies,lessons,terms,quizzes,calculatePer,repository} from '../dist/data.js';
const params={id:'005930',year:'2025',reportCode:'11011',fsDiv:'CFS'};
const receipt='20260316000001';
const rowsFor=(p=params)=>[
  ['BS','ifrs-full_Assets','자산총계','1,000'],['BS','ifrs-full_Liabilities','부채총계','300'],
  ['BS','ifrs-full_Equity','자본총계','700'],['BS','ifrs-full_IssuedCapital','자본금','100'],
  ['IS','ifrs-full_Revenue','매출액','2,000'],['IS','dart_OperatingIncomeLoss','영업이익','-100'],
  ['IS','ifrs-full_ProfitLoss','당기순이익','0'],['CF','ifrs-full_CashFlowsFromUsedInOperatingActivities','영업활동현금흐름','120']
].map(([sj_div,account_id,account_nm,thstrm_amount])=>({sj_div,account_id,account_nm,thstrm_amount,thstrm_add_amount:'5,000',currency:'KRW',rcept_no:receipt,corp_code:COMPANIES[p.id].corpCode,bsns_year:p.year,reprt_code:p.reportCode}));
const response=body=>({ok:true,json:async()=>body});
const mock=(rows=rowsFor(),failure)=>async url=>url.pathname.endsWith('list.json')?response({status:'000',list:[{rcept_no:receipt,corp_code:rows[0]?.corp_code,rcept_dt:'20260316'}]}):response(failure||{status:'000',list:rows});
const adapter=(fetchImpl=mock(),extra={})=>createAdapter({apiKey:'synthetic-test-credential',fetchImpl,...extra});

test('all four company identifiers, provenance, negative/zero amounts and cache',async()=>{
 for(const id of Object.keys(COMPANIES)) {
  const p={...params,id};let calls=0;
  const a=adapter(async url=>{calls++;assert.equal(url.origin,'https://opendart.fss.or.kr');assert.equal(url.searchParams.get('corp_code'),COMPANIES[id].corpCode);assert.equal(url.searchParams.get('crtfc_key'),'synthetic-test-credential');return mock(rowsFor(p))(url);});
  const data=await a.financials(p);
  assert.equal(data.status,'ok');assert.equal(data.is_demo,false);assert.equal(data.basis,'연결');
  assert.equal(data.available_at,'2026-03-16');assert.equal(data.observed_at,'2025-12-31');
  assert.equal(data.metrics.find(x=>x.id==='operatingProfit').value,-100);assert.equal(data.metrics.find(x=>x.id==='netIncome').value,0);
  assert.equal(data.risk.label,'평가 불가');assert.ok(!JSON.stringify(data).includes('synthetic-test-credential'));
  await a.financials(p);assert.equal(calls,2);
 }
});
test('quarterly cumulative values and explicit separate basis',async()=>{
 const p={...params,reportCode:'11012',fsDiv:'OFS'};
 const d=await adapter(async url=>{if(url.pathname.includes('fnltt'))assert.equal(url.searchParams.get('fs_div'),'OFS');return mock(rowsFor(p))(url);}).financials(p);
 assert.equal(d.basis,'별도');assert.equal(d.observed_at,'2025-06-30');
 assert.equal(d.metrics.find(m=>m.id==='revenue').value,5000);assert.equal(d.metrics[0].value,1000);
});
test('missing, ambiguous, wrong-currency accounts never turn into zero',async()=>{
 let rows=rowsFor();rows[0].thstrm_amount='-';rows[1].currency='USD';rows.push({...rows[2]});
 const d=await adapter(mock(rows)).financials(params);assert.equal(d.status,'partial');
 for(const id of ['assets','liabilities','equity'])assert.equal(d.metrics.find(m=>m.id===id).value,null);
 assert.match(financialMarkup(d),/자료 없음/);
 const partial=rowsFor({...params,reportCode:'11014'});delete partial[4].thstrm_add_amount;
 const q=await adapter(mock(partial)).financials({...params,reportCode:'11014'});
 assert.equal(q.metrics.find(m=>m.id==='revenue').value,null);
});
test('missing disclosure date is explicit and does not discard valid financial data',async()=>{
 const a=adapter(async url=>url.pathname.endsWith('list.json')?response({status:'013'}):mock()(url));
 const d=await a.financials(params);assert.equal(d.status,'partial');assert.equal(d.available_at,null);assert.equal(d.metadata_missing_reason,'no_data');
});
test('mixed companies/receipts are rejected',async()=>{
 for(const change of [{corp_code:'bad'},{bsns_year:'2024'},{rcept_no:'20260317000001'}]) {
 const rows=rowsFor();Object.assign(rows[1],change);
 assert.equal((await adapter(mock(rows)).financials(params)).missing_reason,'invalid_response');
 }
});
test('no key means no upstream call; upstream errors never leak secrets or example values',async()=>{
 const d=await adapter(()=>{throw Error('must not call')},{apiKey:''}).financials(params);
 assert.equal(d.missing_reason,'server_key_missing');assert.deepEqual(d.metrics,[]);
 for(const status of ['010','011','012','013','020','800','900']) {
 const d=await adapter(mock([], {status,message:'sensitive upstream message'})).financials(params);
 assert.equal(d.status,'unavailable');assert.deepEqual(d.metrics,[]);assert.ok(!JSON.stringify(d).includes('sensitive'));assert.match(financialMarkup(d),/자료 없음/);
 }
 for(const fetchImpl of [async()=>{throw Error('URL with secret')},async()=>({ok:false}),async()=>({ok:true,json:()=>{throw Error('bad json')}}),async()=>response({status:'000'})]) {
 const d=await adapter(fetchImpl).financials(params);assert.equal(d.status,'unavailable');assert.ok(!JSON.stringify(d).includes('secret'));
 }
});
test('safe parsing and query validation',()=>{
 for(const x of ['',null,'-','1,2','NaN','Infinity','1.2','9007199254740992'])assert.equal(parseAmount(x),null);
 assert.equal(parseAmount(' -1,234 '),-1234);assert.equal(parseAmount('0'),0);
 for(const query of ['year=2014','year=2027','fsDiv=x','reportCode=x','reportCode=toString','year=2025&year=2024','crtfc_key=secret'])assert.equal(validateQuery(params.id,new URLSearchParams(query),new Date('2026-10-27')).httpStatus,400);
 assert.equal(validateQuery('000000',new URLSearchParams()).httpStatus,404);
});
test('UI escapes provider text and rejects unsafe source links',()=>{
 const html=financialMarkup({status:'partial',basis:'<script>',metrics:[{label:'<img src=x>',value:null}],source_url:'javascript:alert(1)'});
 assert.ok(!html.includes('<script>'));assert.ok(!html.includes('<img'));assert.ok(!html.includes('javascript:'));
});
test('B01 exports, demo prices and educational data remain available',async()=>{
 assert.equal(companies.length,4);assert.equal(lessons.length,4);assert.equal(terms.length,10);assert.equal(quizzes.length,4);
 assert.equal(companies[0].price,'72,400');assert.equal(repository.mode,'demo');assert.equal(calculatePer(10000,1000),10);assert.equal(calculatePer(10000,0),null);
});
test('real HTTP route, static asset isolation, method handling and missing-key startup',async t=>{
 const server=createApp({adapter:adapter(undefined,{apiKey:''})});await new Promise(r=>server.listen(0,'127.0.0.1',r));t.after(()=>server.close());
 const base=`http://127.0.0.1:${server.address().port}`;
 const res=await fetch(base+'/api/companies/005930/financials');assert.equal(res.status,200);assert.equal((await res.json()).missing_reason,'server_key_missing');
 assert.equal((await fetch(base+'/')).status,200);assert.equal((await fetch(base+'/financials.js')).status,200);
 for(const path of ['/.env','/.git/config','/server/opendart.js','/docs/API_CONTRACT.md','/api/companies/000000/financials','/api/unknown'])assert.equal((await fetch(base+path)).status,404);
 assert.equal((await fetch(base+'/api/companies/005930/financials?year=bad')).status,400);
 assert.equal((await fetch(base+'/api/companies/005930/financials',{method:'POST'})).status,405);
});
test('concurrent requests coalesce and cache expiry refreshes',async()=>{
 let calls=0,time=new Date('2026-10-27T00:00:00Z');
 const a=adapter(async url=>{calls++;return mock()(url);},{now:()=>time,ttlMs:100});
 await Promise.all([a.financials(params),a.financials(params)]);assert.equal(calls,2);
 time=new Date(time.getTime()+101);await a.financials(params);assert.equal(calls,4);
});
