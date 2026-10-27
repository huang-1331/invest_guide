# 확인한 출처

확인일: 2026-10-28 (KST). 코드의 감사 타임스탬프는 UTC입니다.

1. 주정아. (2013). *자본잠식기업과 비자본잠식기업의 비교연구* [석사학위논문, 중앙대학교]. DOI: 10.23169/cau.000000066933.11052.0000402.
   - 공식 학위논문 서지·초록: https://www.riss.kr/link?id=T13257758
   - 공개 초록의 1·2·3년 전 사건표본 수는 각각 112·93·76, 같은 수의 비교기업. 이전 대화의 206쌍은 이 논문에 확인된 숫자가 아님.
   - 원문 계수·정확한 변수정의·KIS-VALUE 원표본을 미확보. 초록 기반 방법론 근사만 수행.
2. Altman, E. I. (2002). *Corporate distress prediction models in a turbulent economic and Basel II environment*. NYU Stern.
   - https://w4.stern.nyu.edu/finance/docs/WP/2002/pdf/wpa02052.pdf
   - PDF pp.17–18: 장부가치 Z″, 1.10 cutoff, +3.25 EM 변환 구분.
3. 금융감독원. 단일회사 전체 재무제표 개발가이드.
   - https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS003&apiId=2019020
   - 2015년 이후 자료, CFS/OFS, 접수번호·누적금액·통화 정의.
4. 금융감독원. 재무정보 일괄다운로드.
   - https://opendart.fss.or.kr/disclosureinfo/fnltt/dwld/main.do
   - 색인: https://opendart.fss.or.kr/disclosureinfo/fnltt/dwld/list.do
   - 당시 일괄파일은 정정될 수 있어 과거 공시 시점 복원 증거로 단독 사용 불가. 실제 ZIP 요청은 오류 HTML 반환.
5. KRX KIND. 상장법인목록.
   - https://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13
6. KRX KIND. 상장폐지현황.
   - https://kind.krx.co.kr/investwarn/delcompany.do?method=searchDelCompanyMain
   - 검색 매개변수·실제 다운로드 URL은 `outputs/acquisition_summary.json`에 보존. 반환 기록의 완전성은 미검증.
7. KRX 정보데이터시스템.
   - https://data.krx.co.kr/comm/finder/finder_datastkisu.jsp
   - 초기 요청 403, 재시도에서는 HTML 접근 성공. 구조화된 과거 전체 상장 이력은 미확보. KIND 공식 자료는 별도로 다운로드 성공.

정확한 조회 원문·해시는 로컬 `data/raw/`, 공개 가능한 집계와 성공/실패 기록은 `outputs/`에 있습니다. 단순 웹페이지 접근 성공은 재무 데이터셋 수집 성공으로 집계하지 않습니다.
