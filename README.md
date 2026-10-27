# 주식의 이해
한국어 투자·교육 웹앱의 UI 프로토타입. 원래 상장폐지 예측 연구와 분리된 서비스 프레임입니다.

## 실행
정적 서버로 dist/를 제공합니다. 빌드 및 패키지 설치 불필요.

## 구조
- dist/index.html: 앱 프레임, 내비게이션, 접근 가능한 모달
- dist/styles.css: 반응형 디자인
- dist/app.js: 화면 이동과 브라우저 내 시연 상호작용
- dist/data.js: 예시 데이터 및 비동기 repository 인터페이스

## 동작 범위
기업 검색·업종 필터·관심기업(브라우저 저장), 학습 미리보기·퀴즈·용어 해설·가상 PER 실습. 가격과 차트는 임의 예시입니다. 서버 기능과 실제 투자 위험 분석은 구현하지 않았습니다.

## 백엔드 확장
repository의 listCompanies/getCompany/listLessons를 HTTP 어댑터로 교체할 수 있습니다. 회사 종목코드와 교육 개념 식별자를 유지합니다. 현재 secret·외부 API 호출·DB 바인딩은 없습니다.

예정 API: GET /api/companies?q=&sector=, GET /api/companies/:id, GET /api/companies/:id/prices?period=, GET /api/companies/:id/events, GET /api/companies/:id/risk-signals, GET /api/concepts, GET /api/lessons. 로그인 이후 사용자별 관심기업·학습 기록 별도 추가.

실제 응답에는 source, observed_at, available_at, updated_at, is_demo, missing_reason, verification_status를 포함하고 자료 부족은 평가 불가로 표시해야 합니다. 재무·시장·공시 위험을 구분하고 검증 전 연구 모델을 전 업종 위험 점수로 사용하지 않습니다. API 키는 서버 환경변수로만 관리합니다. 공급원별 표시·재배포 조건과 교육 콘텐츠 검수를 연결 전에 확인합니다.

기술 스택·공급원·위험 임계값·인증 방식은 미확정이며 현재 정적 구조는 후속 API 및 서버 앱으로 이전 가능합니다.

## 협업
- 3일 MVP 역할·일정: [docs/ROADMAP.md](docs/ROADMAP.md)
- 로컬 실행: `python3 -m http.server 4173 --directory dist` 후 http://localhost:4173 열기. ES 모듈을 사용하므로 file://로 직접 열지 않습니다.
- 실행·미리보기는 로그인이나 API 키 없이 가능합니다.
- `.openai/hosting.json`은 기존 Sites 배포의 식별자를 보존합니다. 별도 사이트로 복제할 때 그대로 배포하지 않습니다.

## 브랜치·진행 기록
- A(화면·사용 경험): `tw`. B(데이터·교육): `main`. 파일 소유권은 [로드맵](docs/ROADMAP.md)을 따릅니다.
- A는 `git fetch origin` 후 `tw`에서 `git merge origin/main`으로 B 변경을 가져와 검증하고 `tw`에만 업로드합니다.
- 공용 문서 정본은 이 저장소의 `docs/`입니다. [실행 규칙](docs/A_EXECUTION_PROTOCOL.md), [진행 기록](docs/WORK_PROGRESS.json), [A 작업 카드](docs/A_TASK_PROMPTS.txt)를 사용합니다. 기존 바깥 `docs/` 사본은 사용하지 않습니다.
- 진행 JSON은 한 명씩 수정하고, 병합할 때 revision과 양쪽 기록을 보존합니다.
- B 교육 데이터·검수 기록은 병합되었으나 화면 연결·공동 실행·API 계약 확인은 별도 작업입니다.
