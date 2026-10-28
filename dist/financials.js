const esc=value=>String(value??'자료 없음').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const reasons={server_key_missing:'서버 인증키 미설정',api_unavailable:'API 서버 조회 실패',no_data:'공시 재무자료 없음',invalid_key:'서버 인증 오류',ip_restricted:'서버 IP 접근 제한',rate_limited:'요청 한도 초과',maintenance:'OpenDART 점검 중',upstream_unavailable:'OpenDART 연결 실패',upstream_http_error:'OpenDART 응답 오류',invalid_response:'OpenDART 응답 검증 실패',upstream_error:'OpenDART 조회 실패'};
export function financialMarkup(data) {
  if(data.status==='unavailable')return `<div class="notice">자료 없음 · ${esc(reasons[data.missing_reason]||'재무정보를 확인할 수 없습니다.')}<br>위험 평가: 평가 불가 · 예시 수치로 대체하지 않습니다.</div>`;
  const source=/^https:\/\/dart\.fss\.or\.kr\/dsaf001\/main\.do\?rcpNo=\d{14}$/.test(data.source_url||'')?`<a href="${esc(data.source_url)}" target="_blank" rel="noopener noreferrer">공시 원문 ↗</a>`:'자료 없음';
  return `<p><strong>실제 공시 자료 · ${esc(data.basis)} · ${esc(data.report_name)}</strong>${data.status==='partial'?' · 일부 자료 없음':''}</p>
    <dl class="financial-meta"><dt>출처</dt><dd>금융감독원 OpenDART · ${source}</dd>
    <dt>재무 기준일</dt><dd>${esc(data.observed_at)}</dd><dt>공시일</dt><dd>${esc(data.available_at)}</dd>
    <dt>조회 시각</dt><dd>${esc(data.updated_at)}</dd><dt>단위 / 기준</dt><dd>원 (KRW) / ${esc(data.basis)}</dd></dl>
    <p>${esc(data.period_start)} ~ ${esc(data.observed_at)} · 손익·현금흐름은 누적, 재무상태는 기말</p>
    <div class="financial-table"><table><caption>공시 재무정보 (단위: 원)</caption><thead><tr><th scope="col">항목</th><th scope="col">금액</th></tr></thead><tbody>${data.metrics.map(m=>`<tr><th scope="row">${esc(m.label)}</th><td>${Number.isSafeInteger(m.value)?m.value.toLocaleString('ko-KR'):'자료 없음'}</td></tr>`).join('')}</tbody></table></div>
    <p>재무정보 조회 결과이며 위험 등급·투자 적합성을 뜻하지 않습니다. 위험 평가: 평가 불가.</p>`;
}
export function mountFinancials(host,id,repository) {
  const defaultYear=new Date().getFullYear()-1;
  host.innerHTML=`<h3>공시 재무정보 · OpenDART</h3><form class="financial-form">
    <label>사업연도 <input name="year" type="number" min="2015" max="${defaultYear+1}" value="${defaultYear}" required></label>
    <label>보고서 <select name="reportCode"><option value="11011">사업보고서</option><option value="11013">1분기</option><option value="11012">반기</option><option value="11014">3분기</option></select></label>
    <label>재무 기준 <select name="fsDiv"><option value="CFS">연결</option><option value="OFS">별도</option></select></label>
    <button type="submit" class="chip">조회</button></form><p>기본: 전년도 사업보고서 · 최신 공시 자동선택 아님 · 가격·차트는 예시</p><div class="financial-result" role="status" aria-live="polite"></div>`;
  const form=host.querySelector('form'),result=host.querySelector('.financial-result');let serial=0;
  const load=async()=>{
    const ticket=++serial;
    result.setAttribute('aria-busy','true');result.textContent='OpenDART 재무정보 조회 중…';
    const data=await repository.getFinancials(id,Object.fromEntries(new FormData(form)));
    if(!host.isConnected||ticket!==serial)return;
    result.setAttribute('aria-busy','false');result.innerHTML=financialMarkup(data);
  };
  form.addEventListener('submit',event=>{event.preventDefault();load();});load();
}
