# 입력 데이터 계약

원본·개별기업 정리표는 `data/private/`에 저장합니다. 빈 템플릿의 검증 칸을 임의로 true로 바꾸지 마십시오.

## universe.csv

| 열 | 형식·의미 |
|---|---|
| corp_code | 8자리 OpenDART 법인 고유번호, 문자열 |
| stock_code | 6자리 종목코드, 문자열 |
| company_name | 공식 회사명 |
| listed_at / delisted_at | YYYY-MM-DD, 미폐지는 빈값. 중복 상장 spell은 수동 검토 필요 |
| history_source_url | 공식 KIND/KRX 출처 URL |
| history_verified | 역사적 상장 이력 확인 후 true |
| fiscal_year_end | 현재 구현에서는 12 |
| sector_class | 현재 구현에서는 nonfinancial |
| followup_end | 재무 사건을 실제로 추적 확인한 마지막 기간 말 |
| followup_verified | 추적기간 검증 후 true |
| universe_complete | 분석대상 모집단의 과거 생존·폐지기업 포함 여부 확인 후 true |

현재 상장목록 또는 폐지기록 635개를 내려받은 것만으로 `universe_complete`가 충족되지 않습니다. 누락된 해·이전상장·폐지 후 공시 중단을 검토해야 합니다. 상장 이력과 DART 고유번호의 연결도 검증이 필요합니다.

## financials.csv

필수 출처 열: `corp_code,stock_code,company_name,period_end,filed_at,rcept_no,fs_div,currency,unit,source,source_url,vintage_verified,fiscal_year_end,values_are_ytd`.

숫자 열: `assets,liabilities,equity,capital,current_assets,current_liabilities,retained_earnings,revenue,operating_income,net_income,ocf,ebit`.

- 금액 KRW 원단위. 백만원 원천은 검증된 환산 후 입력. `currency=KRW,unit=KRW`.
- `source=OpenDART`, 원문 URL은 `https://dart.fss.or.kr/`로 시작.
- `fs_div=OFS` 기본. 기준 혼합 금지.
- `period_end`는 실제 회계기간말. 현재 구현은 12월 결산 분기말만 지원.
- `filed_at`은 정확한 접수번호의 공식 공시일. 수집일 또는 사업연도 말로 대체 금지.
- `vintage_verified=true`는 해당 접수본의 값과 날짜를 검증했음을 뜻함. 정정본 수치를 원공시일로 변경하지 않음.
- `values_are_ytd=true`: 재무상태표는 시점 금액, 손익·현금흐름은 연초 이후 누적금액. 비교기 값으로 당기 결측을 채우지 않음.
- NaN은 결측. 0은 실제 값. 중복 공시 당일 충돌, 통화 불일치, 대차 불일치를 차단.
- 원문 회사별 비표준계정 매핑은 검증된 사전 없이는 추정하지 않음.

## 데이터 공개

KRX/KIND·OpenDART 이용조건과 파생물 공개범위를 재검토하기 전에는 기업별 원본·정리표를 Git에 넣지 않습니다. 공개 저장소에는 실행 코드·다운로드 URL·해시·집계·평가불가 사유만 둡니다. 키는 환경변수로만 읽고 요청 URL·인증값을 감사로그에 출력하지 않습니다.
