# 재무제표 기반 완전자본잠식 12·24개월 조기예측

연구 코드와 데이터 작업은 모두 `research/`에 한정합니다. 웹 UI·서버·기존 OpenDART 브랜치를 수정하지 않습니다.

**현재 상태: 연구 실행 기반 구현 / 실증 검증 미완료.** 실제 수집 결과는 `outputs/acquisition_summary.json`, 예측 실행 결과는 `outputs/status.json`, 상세 보고는 `outputs/REPORT.md`를 확인하십시오. 합성 테스트의 성공은 예측 정확도 검증이 아닙니다.

## 실행 환경

Python 3.12. 실제 실행 환경에서 확인한 직접 의존성 버전을 `requirements.txt`에 고정했습니다.
저장소 루트에서:

```sh
python -m venv research/.venv
. research/.venv/bin/activate
python -m pip install -r research/requirements.txt
export PYTHONPATH="$PWD/research/src"
python -m pytest -q research/tests
python -m capitalrisk.public_sources
python -m capitalrisk.pipeline probe
python -m capitalrisk.pipeline run
python research/scripts/execute_notebook.py
```

마지막 명령은 실행된 결과를 Notebook에 저장합니다. 연구 자료가 없으면 blocked 상태로 종료하며 성능 수치를 생성하지 않습니다. `research/` 안에서는 `make test`, `make probe`, `make run`, `make notebook`도 사용할 수 있습니다.

## 실제 수집 재개

1. 새로 발급한 미노출 키를 로컬 환경변수 `OPENDART_API_KEY`에 설정합니다. 키를 코드·Notebook·명령 인자·커밋에 넣지 않습니다. `.env` 자동 탐색·기존 키 재사용은 하지 않습니다.
2. `docs/DATA_CONTRACT.md` 형식에 맞춘 `data/private/universe.csv`를 준비합니다. 과거 상장폐지·시장 이전·합병·재상장·금융업 제외를 검토합니다. 현재 상장기업 목록만으로 완전한 모집단이라고 선언하지 않습니다.
3. 키를 설정한 같은 셸에서 `python -m capitalrisk.pipeline collect`를 실행합니다. 공식 계정 ID가 없거나 중복되면 결측으로 기록합니다.
4. 수집된 `financials.csv`의 공시 접수번호·공시일·계정·기준을 검증한 뒤 `python -m capitalrisk.pipeline run`을 실행합니다.
5. `config.json`의 시점 분리는 결과를 보기 전에 고정합니다. 2025년 재무정보만으로 2025년 예측의 24개월 후 정상 여부를 확인할 수 없습니다. 관찰 만료 사례는 미확정으로 남깁니다. 기본 테스트 2024~2025에서 충분한 추적관찰이 없으면 비교가 차단됩니다.

## 구현

- Altman 장부가치 Z″: 시장가치 원형 대체가 아닌 명시적 변형. 원공식 Z″와 train에서 학습한 확률 매핑, 고정 1.10 기준을 구분.
- Logistic: 2013년 초록에 제시된 1·2년 전 변수 접근의 근사 구현 + 재무 변화 변수를 추가한 개선 Logistic. 원 계수·원표본 복제는 아님.
- Cox: 기업당 마지막 학습 랜드마크로 적합, 학습 종료일 행정 검열. PH 검정·민감도 검증은 후속 과제.
- DTW: 최근 8개 분기 재무비율, 반경 2, 거리 가중 5-NN 분류.
- XGBoost + SHAP: 깊이 2, 150개 트리, 고정 seed. 성능 향상을 전제하지 않음.
- Accuracy·Precision·Recall·F1·ROC-AUC·PR-AUC(AP)·Brier·오경보율·혼동행렬, 검증셋 확률 보정, 기업 단위 부트스트랩 95% CI 및 Altman 대비 쌍체 차이.
- Cox C-index·IPCW 시간의존 AUC는 계산 조건을 충족할 때만 기록. 생존 지표 CI, IPCW Brier, PH 진단은 아직 구현하지 않음.
- 학습·검증·테스트 기업을 해시로 분리하고 시점도 분리. 테스트 재표본추출·SMOTE 없음. 기준모형 결측 때문에 테스트가 변하면 공통 비교를 차단.

## 산출물 경로

| 경로 | 내용 |
|---|---|
| `src/capitalrisk/` | 수집·전처리·모형·평가·시각화·CLI |
| `notebooks/research.ipynb` | 실제 실행 상태가 포함된 Notebook |
| `tests/` | 합성 fixture 전용 테스트, 연구 결과로 사용 금지 |
| `outputs/collection_audit.csv` | 접근 실패·API 오류·결측 로그 |
| `outputs/acquisition_summary.json` | 실제 다운로드 수·검증 한계 |
| `outputs/kind_delisting_counts.csv` | 내려받은 상장폐지 기록의 연도별 집계 |
| `outputs/figures/collection_coverage.svg` | 위 집계 그래프; 완전자본잠식 그래프 아님 |
| `outputs/run_*/` | 실행별 상태·실제 데이터가 있을 때만 성능·그래프 |
| `data/private/` | 원천 정리표·개별기업 예측 CSV, Git 제외 |
| `data/raw/` | 원천 응답·파일·해시 검증용 캐시, Git 제외 |

원천 데이터 재배포 허가를 확인하지 않았으므로 원본·전체 목록은 커밋하지 않습니다. 현재 공개 산출물은 코드·문서·집계치·접근 감사기록입니다. 기업별 데이터 공개는 공급원 조건 검토 후 별도 결정합니다.

세부 정의는 `docs/METHODOLOGY.md`, 입력 계약은 `docs/DATA_CONTRACT.md`, 출처는 `docs/SOURCES.md`에 있습니다.
