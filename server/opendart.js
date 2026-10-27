// Server only: no upstream URLs or errors containing credentials leave this module.
export const COMPANIES = Object.freeze({
  '005930': {name:'삼성전자', corpCode:'00126380'},
  '000660': {name:'SK하이닉스', corpCode:'00164779'},
  '035420': {name:'NAVER', corpCode:'00266961'},
  '005380': {name:'현대자동차', corpCode:'00164742'}
});
export const REPORTS = Object.freeze({
  '11011': {name:'사업보고서', end:'12-31'},
  '11013': {name:'1분기보고서', end:'03-31'},
  '11012': {name:'반기보고서', end:'06-30'},
  '11014': {name:'3분기보고서', end:'09-30'}
});
const definitions = [
  ['assets','자산총계','BS',['ifrs-full_Assets'],['자산총계']],
  ['liabilities','부채총계','BS',['ifrs-full_Liabilities'],['부채총계']],
  ['equity','자본총계','BS',['ifrs-full_Equity'],['자본총계']],
  ['capital','자본금','BS',['ifrs-full_IssuedCapital'],['자본금']],
  ['revenue','매출액','IS',['ifrs-full_Revenue'],['매출액','수익(매출액)','영업수익']],
  ['operatingProfit','영업이익','IS',['dart_OperatingIncomeLoss'],['영업이익','영업이익(손실)']],
  ['netIncome','당기순이익','IS',['ifrs-full_ProfitLoss'],['당기순이익','당기순이익(손실)']],
  ['operatingCashFlow','영업활동현금흐름','CF',['ifrs-full_CashFlowsFromUsedInOperatingActivities'],['영업활동현금흐름','영업활동으로인한현금흐름','영업활동으로부터의현금흐름']]
];
export function parseAmount(value) {
  if (typeof value !== 'string' || !/^-?(?:\d{1,3}(?:,\d{3})+|\d+)$/.test(value.trim())) return null;
  const n=Number(value.replaceAll(',','').trim());
  return Number.isSafeInteger(n) ? n : null;
}
const normalize=s=>String(s||'').replaceAll(/\s/g,'');
function selectMetric(rows, definition, reportCode) {
  const [id,label,statement,ids,names]=definition;
  // Prefer IS to CIS; never pull components from SCE or cash-flow rows.
  const groups=statement==='IS'?['IS','CIS']:[statement];
  let matches=[];
  for (const group of groups) {
    const candidates=rows.filter(r=>r.sj_div===group);
    matches=candidates.filter(r=>ids.includes(r.account_id));
    if(!matches.length)matches=candidates.filter(r=>names.includes(normalize(r.account_nm)));
    if(matches.length)break;
  }
  const field=statement==='IS'&&reportCode!=='11011'?'thstrm_add_amount':'thstrm_amount';
  const row=matches.length===1?matches[0]:null;
  const value=row?.currency==='KRW'?parseAmount(row[field]):null;
  return {id,label,value,unit:'원',currency:'KRW',account_id:row?.account_id||null,
    amount_field:field,missing_reason:value===null?(matches.length>1?'ambiguous_account':row?.currency!=='KRW'&&row?'unsupported_currency':'missing_account_or_amount'):null};
}
export function validateQuery(id, query, now=new Date()) {
  if (!COMPANIES[id]) return {error:'unknown_company',httpStatus:404};
  const year=query.get('year')??String(now.getUTCFullYear()-1);
  const reportCode=query.get('reportCode')??'11011';
  const fsDiv=query.get('fsDiv')??'CFS';
  if (!/^\d{4}$/.test(year)||Number(year)<2015||Number(year)>now.getUTCFullYear()||!Object.hasOwn(REPORTS,reportCode)||!['CFS','OFS'].includes(fsDiv)) return {error:'invalid_query',httpStatus:400};
  if([...query.keys()].some(k=>!['year','reportCode','fsDiv'].includes(k))||[...query.keys()].some(k=>query.getAll(k).length!==1)) return {error:'invalid_query',httpStatus:400};
  return {id,year,reportCode,fsDiv};
}
export function unavailable(reason, extra={}) {
  return {status:'unavailable',is_demo:false,source:'금융감독원 OpenDART',
    metrics:[],missing_reason:reason,verification_status:'unavailable',risk:{status:'not_evaluated',label:'평가 불가'},...extra};
}
export function createAdapter({apiKey=process.env.OPENDART_API_KEY,fetchImpl=fetch,now=()=>new Date(),timeoutMs=10000,ttlMs=300000}={}) {
  const cache=new Map(); const pending=new Map();
  async function request(endpoint, params) {
    const url=new URL(`https://opendart.fss.or.kr/api/${endpoint}.json`);
    url.search=new URLSearchParams({...params,crtfc_key:apiKey});
    try {
      const res=await fetchImpl(url,{signal:AbortSignal.timeout(timeoutMs),redirect:'error'});
      if(!res.ok) return {error:'upstream_http_error'};
      const data=await res.json();
      if(data.status!=='000') return {error:({'013':'no_data','010':'invalid_key','011':'invalid_key','012':'ip_restricted','020':'rate_limited','800':'maintenance'})[data.status]||'upstream_error'};
      if(!Array.isArray(data.list)) return {error:'invalid_response'};
      return {rows:data.list};
    } catch {return {error:'upstream_unavailable'};}
  }
  async function load({id,year,reportCode,fsDiv}) {
    const company=COMPANIES[id], report=REPORTS[reportCode];
    const meta={company_id:id,company_name:company.name,corp_code:company.corpCode,
      business_year:year,report_code:reportCode,report_name:report.name,fs_div:fsDiv,
      basis:fsDiv==='CFS'?'연결':'별도',currency:'KRW',unit:'원',
      observed_at:`${year}-${report.end}`,period_start:`${year}-01-01`,
      available_at:null,updated_at:now().toISOString(),source_url:null,
      period_note:'손익·현금흐름: 연초부터 누적 / 재무상태: 기말. 기본은 전년도 사업보고서이며 최신 공시 자동선택이 아닙니다.'};
    if(!apiKey) return unavailable('server_key_missing',meta);
    const data=await request('fnlttSinglAcntAll',{corp_code:company.corpCode,bsns_year:year,reprt_code:reportCode,fs_div:fsDiv});
    if(data.error)return unavailable(data.error,meta);
    // Reject mixed company/period/receipt payloads instead of combining unrelated filings.
    const rows=data.rows;
    const receipts=[...new Set(rows.map(r=>r.rcept_no))];
    if(!rows.length)return unavailable('no_data',meta);
    if(rows.some(r=>r.corp_code!==company.corpCode||r.bsns_year!==year||r.reprt_code!==reportCode)||receipts.length!==1||!/^\d{14}$/.test(receipts[0]))return unavailable('invalid_response',meta);
    const receipt=receipts[0];
    meta.source_url=`https://dart.fss.or.kr/dsaf001/main.do?rcpNo=${receipt}`;
    meta.receipt_no=receipt;
    // Obtain the real filing date from disclosure metadata; do not equate fiscal end to disclosure date.
    const date=receipt.slice(0,8);
    const filings=await request('list',{corp_code:company.corpCode,bgn_de:date,end_de:date,page_count:'100'});
    const filing=filings.rows?.find(r=>r.rcept_no===receipt&&r.corp_code===company.corpCode);
    if(filing&&/^\d{8}$/.test(filing.rcept_dt))meta.available_at=filing.rcept_dt.replace(/^(\d{4})(\d{2})(\d{2})$/,'$1-$2-$3');
    meta.metadata_missing_reason=meta.available_at?null:(filings.error||'filing_metadata_missing');
    const metrics=definitions.map(d=>selectMetric(rows,d,reportCode));
    const complete=metrics.every(m=>m.value!==null)&&!!meta.available_at;
    return {...unavailable(null,meta),status:metrics.some(m=>m.value!==null)?(complete?'ok':'partial'):'unavailable',
      metrics,missing_reason:complete?null:'incomplete_data',verification_status:'provider_response'};
  }
  return {async financials(params) {
    const key=JSON.stringify(params),cached=cache.get(key);
    if(cached&&cached.expires>now().getTime()) return cached.value;
    if(pending.has(key))return pending.get(key);
    const task=load(params).then(value=>{
      if(cache.size>=128)cache.delete(cache.keys().next().value);
      cache.set(key,{value,expires:now().getTime()+(value.status==='unavailable'?10000:ttlMs)});
      return value;
    }).finally(()=>pending.delete(key));
    pending.set(key,task);return task;
  }};
}
