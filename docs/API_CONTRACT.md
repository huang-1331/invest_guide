# B03 — 데이터·API 계약 (MVP)

검토 기준: 2026-10-27, `main`의 `dist/data.js`·`dist/app.js`.

## 1. 현재 실행 계약 (구현되어 있음)

- 런타임: 브라우저 ES module; `app.js`에서 `import {repository, lessons, terms} from './data.js'`.
- 서버/DB/HTTP API **없음**. 이 문서의 HTTP 경로는 모두 향후 연동 **제안**일 뿐 구현된 엔드포인트가 아님.
- `repository.mode === 'demo'`.
- 비동기 메서드: `listCompanies(): Promise<Company[]>`, `getCompany(id): Promise<Company|null>`, `listLessons(): Promise<Lesson[]>`, `getLesson(n): Promise<Lesson|null>`, `listTerms(): Promise<Term[]>`, `listQuizzes(): Promise<Quiz[]>`, `getQuizForLesson(n): Promise<Quiz|null>`.
- `companies`, `lessons`, `terms`, `quizzes`, `perPractice`, `calculatePer`, `dataMeta`도 named export로 제공.
- 화면 코드 변경 권한: A만 `app.js`; B는 `data.js` 및 `docs`. 필드 변경 시 먼저 합의.

## 2. 현재 데이터 필드 (확인된 구조)

| 객체 | 식별자 | 필드와 타입 |
|---|---|---|
| Company | `id: string` (앞자리 0 유지) | `name,initial,sector,market,price,change,tone: string`; `points: number[]` |
| Lesson | `n: string` (예: `"01"`) | `category,title,text,time,tag,icon,content: string`; `keyPoints: string[]`; `quizId: string` |
| Term | `term: string` | `ko,text: string`; `formula?, example?: string` |
| Quiz | `id: string` (예: `"Q01"`) | `lessonId,question,explanation: string`; `options: string[4]`; `correctIndex: integer` (0 기반) |
| PER practice | `id: string` | `price,eps,expectedPer: number`; `currency: "KRW"`; `isSample: true`; `note: string` |
| dataMeta | — | `mode: "demo"`, `priceType:"illustrative"`, `source:string`, `asOf:null`, `disclaimer:string` |

**단위·주의**
- `Company.price`는 쉼표 포함 **표시 문자열**, 원 단위. 수치 계산에 직접 사용 금지.
- `Company.change`는 부호와 % 포함 **표시 문자열**이며 실제 등락률이 아님.
- `Company.points`는 **차트 도형용 무단위 점수**. 날짜, KRW 종가, 수익률, 실제 1개월/3개월/1년 시계열 아님.
- `getCompany`·`getLesson`·`getQuizForLesson`는 항목 부재 시 `null`; 목록은 빈 배열 반환.
- 외부 입력은 화면 출력 시 HTML escape 및 타입 검증 필요.

## 3. 화면 연결 지침 (A 소유 영역)

1. 기존 `app.js`는 기업 카드/차트와 용어 목록, 수업 메타데이터에 일부 B01 데이터 사용.
2. `lesson()`은 여전히 하드코딩한 `lessonText` 및 **2지선다 퀴즈** 사용 중. `lessons[].content`, `quizzes[].options`, `correctIndex`, `explanation`으로 변경 필요.
3. 용어 상세는 `terms[].example` 미표시. PER 실습은 `perPractice`·`calculatePer` 대신 하드코딩. 연결은 A가 변경.
4. `localStorage('jusik:saved')`는 현재 관심기업 ID 배열 저장에만 사용. 학습 완료 기록과 초기화 기능은 아직 미구현. 추후 별도 키(예: `jusik:learning:v1`)를 A와 합의하고 JSON 스키마·버전 명시.
5. 기존 해시 라우팅: `#home`, `#companies`, `#learning`, `#glossary`, `#saved`, `#company-{id}`, `#lesson-{n}`. 이 계약 유지.

## 4. 출처·결측·상태 표시 규칙

| 상황 | 상태/표시 | 금지 |
|---|---|---|
| 현 예시 데이터 | `mode=demo`, `source=교육용 임의 생성 데이터`; 가격·변동·차트에 **예시** 명시 | 실시간 시세처럼 표시 |
| 실데이터 미연결 | `자료 미연결`, 위험: `평가 불가` | 안전/위험 등급 또는 확률 산출 |
| 값 없음/조회 실패 | 값은 `null` 또는 명시적 오류 상태; 화면에 `자료 없음`/`조회 실패` | 0이나 임의 수치 대체 |
| PER | `price/eps` (EPS>0, 유한 수치 조건) | EPS ≤0인데 의미 있는 양수 PER 표시 |
| 실데이터 연결(선택) | 공급원, 이용조건, 종목코드, 통화/단위, 관측일/발행일, 갱신일, 연결/별도 재무 기준, 예시 여부 기록 | 무출처 수치 노출 |
| 데이터 혼합 | 각 필드의 `isSample`/출처/기준일 독립 표시 | 실자료와 예시를 한 시리즈로 오인 유발 |

- API 키·토큰을 브라우저 코드, 정적 `data.js`, Git 커밋, 공유 파일에 두지 않음.
- 현재 기업 이름·코드는 실제 식별정보지만 모든 가격·변동률·차트는 허구임.

## 5. 향후 HTTP 어댑터 제안 (미구현)

아래는 **계약 초안**이고 운영 API가 아님. 서버 측 인증 경로와 데이터 이용조건 확보 후 구현.

| 제안 경로 | 응답 | 상태 |
|---|---|---|
| `GET /api/companies?q=...` | `{items: CompanyV2[], mode, source, asOf}` | 미구현 |
| `GET /api/companies/{id}` | `{item: CompanyV2|null, mode, source, asOf}` | 미구현 |
| `GET /api/companies/{id}/prices?range=1m` | `{items: PricePoint[], source, currency, asOf}` | 미구현 |
| `GET /api/companies/{id}/filings` | `{items: Filing[], source, asOf}` | 미구현 |

추천 V2 데이터 형태:
```json
{
  "id": "005930",
  "name": "삼성전자",
  "currency": "KRW",
  "price": null,
  "isSample": false,
  "status": "unavailable",
  "source": null,
  "asOf": null
}
```
- 위 JSON은 **형식 예시**이고 실시간 시세 값 아님.
- `PricePoint`: `{date:"YYYY-MM-DD", close:number|null}` (해당 일자·단위·수정주가 적용 여부 명시).
- `Filing`: `{title:string, filedAt:string, sourceUrl:string}`; 출처·원문 이용 가능 여부 확인.
- 조회 실패 시 응답 구조와 `status`를 명확히 구분하고, 브라우저에서 민감한 인증정보 사용 금지.

## 6. B03 완료 / 통합 인수 조건

- [x] 현재 데이터 구조·메서드·식별자 확인
- [x] 실데이터·예시 데이터 및 결측 처리 규칙 정의
- [x] 향후 API 경로 및 샘플 응답 문서화
- [x] A가 수정해야 할 UI 연결 지점 지정
- [ ] A가 4지선다/수업 본문/PER 실습을 `data.js`에 연결
- [ ] 학습기록 저장·복원·초기화 구현
- [ ] B04 브라우저 실제 시연/접근성/배포 확인

## 7. OpenDART 확장 (2026-10-27)

위 1~6절은 B03 작성 시점의 정적 MVP 기준입니다. 이번 확장으로 서버 경로 **`GET /api/companies/{id}/financials`만 구현**되었습니다. 기존 `repository.mode='demo'`는 가격·교육 데이터의 계약을 유지하며, 새 `getFinancials(id, {year, reportCode, fsDiv})` 응답은 독립적인 `is_demo:false`를 가집니다. 다른 제안 HTTP 경로는 여전히 미구현입니다.

상세 계약과 검증 결과는 [OPENDART_INTEGRATION.md](OPENDART_INTEGRATION.md)를 참조합니다. 기존 export·기업 가격·차트·교육 본문·퀴즈 데이터는 유지합니다.
