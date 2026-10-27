# OpenDART 서버 연동

기준: 2026-10-27, 브랜치 `feat/opendart-server-adapter`. 기존 B01~B04 산출물을 보존한 후속 확장. main 병합·배포는 수행하지 않음.

## API 계약

`GET /api/companies/{id}/financials?year=2025&reportCode=11011&fsDiv=CFS`

- 회사: `005930 → 00126380`, `000660 → 00164779`, `035420 → 00266961`, `005380 → 00164742` (종목코드 → DART 고유번호).
- 기본: 전년도, 사업보고서, 연결. 최신 보고서 자동선택/별도 자동대체 없음.
- year: 2015~현재 연도. reportCode: 11011(사업), 11013(1분기), 11012(반기), 11014(3분기). fsDiv: CFS(연결), OFS(별도).
- 미지원 회사 404, 잘못된 쿼리 400, 미지원 메서드 405. 공급원 실패는 HTTP 200의 `status:unavailable`로 표시.
- 정상/부분/불가: `status=ok|partial|unavailable`, 실제 조회 경로 `is_demo:false` (조회 성공을 의미하지 않음).
- `metrics[]`: id, label, value(number|null), currency=KRW, unit=원, account_id, amount_field, missing_reason.
- source, source_url, receipt_no, observed_at(재무 기준일), available_at(공시일), updated_at(공급원 조회 시각), business_year, report_code, fs_div, basis, period_start 포함.
- `verification_status=provider_response`: OpenDART 응답 기반이라는 뜻이며 독립 회계 검증을 의미하지 않음. `risk.label`은 항상 평가 불가.
- 공시일은 `list.json`의 **동일 접수번호** 메타데이터로 조회. 실패하면 null/자료 없음, `metadata_missing_reason` 제공. 재무 기준일은 12월 결산 4개 회사의 선택된 보고서 기말일. 접수번호 앞 8자리는 메타데이터 검색일 범위로만 사용.
- 원 단위 안전 정수만 수용. 쉼표·음수·실제 0은 허용, 공백·하이픈·잘못된 숫자·안전 정수 범위 초과는 null. 큰 금액의 반올림 오차를 허용하지 않음.
- 표준 XBRL ID 우선, 제한된 계정명 정확 일치 대체. IS 우선/CIS 대체. 중복·모호한 계정은 평가하지 않음. 자본변동표의 구성 항목을 총액으로 선택하지 않음.
- 분·반기 손익은 `thstrm_add_amount`를 사용하며 없으면 null. 3개월 금액으로 대체하지 않음. BS/CF/사업보고서는 `thstrm_amount`.
- 같은 회사/연도/보고서/접수번호의 응답만 허용. 서로 다른 공시를 합산하지 않음.

## 오류·보안·운영

`OPENDART_API_KEY`는 서버 프로세스에서만 읽음. 기존 노출 키를 소스·Git 이력에서 추출하거나 재사용하지 않았음. 폐기/재발급은 키 소유자가 OpenDART 관리 화면에서 수행해야 함.

브라우저 요청은 동일 출처 `/api`만 호출. 공급원 URL/오류 메시지/키를 클라이언트·로그에 출력하지 않으며 리다이렉트를 거부함. 정적 파일은 dist의 HTML/JS/CSS만 제공하여 .env·Git·서버 소스가 노출되지 않음. 화면의 외부 텍스트 escape 및 원문 링크 패턴 검증 적용.

키 미설정, 인증/IP 오류, 조회 없음, 한도, 점검, HTTP 오류, 네트워크/타임아웃, JSON 오류를 구분하여 자료 없음 처리. 실패 시 기존 실자료나 예시 수치로 대체하지 않음. 실제 자료 일부만 존재하면 partial과 각 결측 항목을 표시. 위험등급·RandomForest·안전 판단·자본잠식 임계값 구현 없음.

5분 메모리 캐시(최대 128개), 실패 10초 캐시, 동일 요청 합치기. 캐시 응답의 updated_at은 공급원 조회 시각이며 매 화면 조회 시각으로 바꾸지 않음. 각 공급원 요청 10초 제한, 브라우저 요청 25초 제한. 재시도·영구보관·스케줄 수집 없음. 공개 운영 규모에서는 외부 호출 한도/인증/요청 제한·관측 시스템을 별도 검토해야 함.

## 공식 명세

- [단일회사 전체 재무제표](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS003&apiId=2019020): fs_div, 누적손익, 통화, 상태코드.
- [공시검색](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS001&apiId=2019001): 접수번호와 rcept_dt.
- [OpenDART 이용약관](https://opendart.fss.or.kr/intro/terms.do): 운영 전 확인.

## 실행 검증 결과

- `npm test`: 11개 테스트 통과. 네 기업 식별자·원본 출처, 음수/0, 연결/별도, 반기 누적, 결측/중복/타통화, 공시일 누락, 혼합 응답 거부, 키 미설정, 공급원 상태코드·HTTP/JSON/네트워크 실패, 입력 검증, HTML/링크 방어, 기존 B01 export, 실제 로컬 HTTP 경로·정적 파일 격리, 캐시·동시 요청·만료 검증.
- `npm run test:live`: **미실행(종료 코드 2)**. 서버에 새 미노출 키가 없어 실제 OpenDART 인증/수치 대조는 완료하지 못함. 성공으로 간주하지 않음.
- 브라우저 통합 테스트: 결과는 아래 최종 검증 기록 참조. 모의 공급원이며 실제 재무 수치를 검증한 것이 아님.

## 배포 전 조건

1. 노출 키 폐기 후 새 키를 배포 대상 서버의 비밀 설정에 등록 (브라우저/소스/GitHub 커밋 금지).
2. 서버 환경에서 `npm run test:live` 통과 및 네 기업의 원문 대비 주요 수치·연결/별도·공시일 확인.
3. Node 서버를 제공하거나 정적 호스팅에 동일 출처 `/api` 프록시 연결. 기존 `.openai/hosting.json`은 변경하지 않았으며 정적 Sites 배포만으로 서버가 생성되지 않음.
4. PR 테스트 결과를 검토한 뒤 병합/배포 판단. B04의 기존 학습기록/4지선다 미구현 등은 별도 과제로 유지.

### 최종 검증 기록

- Node.js 24.22.1에서 `npm test` **11/11 통과**, `node --check` 및 `git diff --check` 통과.
- `npm run test:browser`는 **브라우저 미설치로 실행 실패**. Playwright는 존재하지만 Chromium 실행 파일이 없었고 다운로드도 ZIP 오류로 실패했습니다. 따라서 모바일·키보드·상세 화면 시각 검증을 통과로 기록하지 않습니다. 재실행 스크립트를 PR에 포함했습니다.
- `npm run test:live`는 **새 키 미설정으로 미실행**. 실제 네 기업 API 인증/수치 확인은 배포 전 필수입니다.
- 기존 B01~B04 문서와 교육 데이터·기업 가격·차트는 유지했습니다. 이번 검증이 기존 B04의 미완료 항목을 해결했다는 뜻은 아닙니다.
- 배포 판정: **보류**. 새 키 실제 조회 및 브라우저 검증 후 판단해야 합니다.
