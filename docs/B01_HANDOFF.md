# B01 인계 사항 (A 담당 수정 요청)

- 기존 `dist/data.js`를 검토 후 `B01_data.js` 내용으로 대체 (기존 `companies`, `lessons`, `terms`, `repository` export 유지).
- 기존 기업 4개·종목코드·섹터·화면 사용 속성 유지. **가격·등락률·차트는 모두 예시임을 계속 표시**.
- `app.js`의 `lessonText`, `questions` 하드코딩을 삭제하고 `lessons[].content`, `quizzes[]`를 연결해야 새 본문·객관식 퀴즈가 표시됨 (A 수정).
- 현재 `app.js`에는 두 선택지와 `data-answer`에 맞춘 로직만 있음. `correctIndex` 기반 4지선다·해설·로컬 학습 기록은 A 구현 필요.
- PER 슬라이더는 현재 `app.js`에 정상적인 교육 예시가 하드코딩되어 있음. 필요 시 `perPractice`, `calculatePer`로 전환.
- `data.js`를 로드한 뒤 `app.js`를 수정하지 않아도 기존 UI는 동작하는 형태로 데이터 속성 유지.
- 기존 `app.js`에서 `if(b.dataset.term)`는 값 `"0"`도 truthy이므로 첫 항목도 동작함.
- 기존 `app.js`의 `data-period`별 차트 변환은 실제 기간별 데이터가 아닌 임의 변형이며, 모든 기간 예시 표시 유지.
- 이 파일은 실서비스 금융 데이터, ML 예측 결과, 공시 API를 포함하지 않음.

## 완료 현황
- 기업 4개(기존 유지), 용어 10개, 수업 본문 4개, 객관식 퀴즈 4개, PER 실습 1개 데이터 준비.
- 아직 미완료: A의 UI 연결, 학습 기록 저장, 화면 통합 테스트.