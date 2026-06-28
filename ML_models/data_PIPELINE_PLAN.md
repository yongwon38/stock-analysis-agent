# 주식 분석 멀티 에이전트를 위한 무료 운영형 ML 마켓 데이터 파이프라인 구축 계획

## 1. 목적과 범위

이 문서는 `stock-analysis-agent` 프로젝트에 **매일 자동 데이터 수집 배치와 ML/DL 기반 종목별 예측 결과 반환 기능**을 추가하기 위한 데이터·운영 파이프라인 설계서다.

핵심 요구 조건은 다음과 같다.

1. 로컬 컴퓨터가 꺼져 있어도 매일 배치가 실행되어야 한다.
2. 외부 서비스는 반드시 무료 플랜만 사용한다.
3. 초기 운영은 자동매매가 아니라 리서치 보조용 데이터 수집과 예측 결과 생성에 한정한다.
4. 매일 수행하는 작업은 데이터 수집, 피처 생성, 기존 모델 기반 예측 추론이다.
5. 모델 재학습은 매일 수행하지 않고, 주 1회 또는 수동 실행으로 분리한다.
6. 모델 예측 결과는 매수/매도 신호가 아니라 리서치 보조 지표로만 사용한다.

본 프로젝트는 투자 판단을 대신하지 않는다. 모델이 반환하는 결과는 다음과 같은 보조 지표로 제한한다.

- 기대수익률 추정치
- 하방 확률
- 예측 신뢰도
- 주요 기여 피처
- 모델 버전
- 예측 기준일
- 데이터 품질 상태

자동매매, 주문 API, 매수/매도 추천 기능은 본 파이프라인의 범위에서 제외한다.

---

## 2. 최종 권장 운영 플랫폼

### 2.1 결론

무료 조건과 로컬 PC 전원 문제를 동시에 고려하면, 운영 구조는 다음 조합을 기본값으로 한다.

```text
개발/테스트: 로컬 PC + Claude Code
스케줄 실행: GitHub Actions Free
운영 DB: Supabase Free Postgres
코드 저장소: GitHub Repository
모델 파일: GitHub repository 또는 Supabase Storage에 소형 artifact로 저장
실험/무거운 학습: 선택적으로 Kaggle Notebook 또는 로컬에서 수동 실행
```

### 2.2 왜 로컬 단독 운영을 쓰지 않는가

로컬 PC는 개발과 디버깅에는 적합하지만, 사용자의 컴퓨터가 꺼져 있으면 배치가 실행되지 않는다. 따라서 매일 데이터 수집과 ML 예측 결과 생성의 운영 플랫폼으로는 부적합하다.

로컬 PC의 역할은 다음으로 제한한다.

- Claude Code를 이용한 코드 개발
- mock provider 기반 테스트
- 소규모 실험
- 수동 backfill 실행
- 모델 실험 또는 디버깅

### 2.3 플랫폼 비교

| 후보 | 무료 운영 적합도 | 장점 | 단점 | 본 프로젝트에서의 역할 |
|---|---:|---|---|---|
| 로컬 PC | 낮음 | 완전 무료, 개발 편함 | PC가 꺼지면 배치 중단 | 개발/테스트 전용 |
| GitHub Actions | 높음 | 무료 cron, 로그, secrets, CI 가능 | 실행 지연 가능, 긴 학습 부적합 | 매일 배치 실행 |
| Supabase Free | 높음 | 무료 Postgres, 외부에서 접근 가능 | 무료 용량 제한 | 운영 DB |
| Neon Free | 중간~높음 | 무료 serverless Postgres | 용량 제한, 대시보드 취향 차이 | Supabase 대체 후보 |
| Kaggle Notebook | 중간 | 무료 연산 자원, 실험 편함 | 운영 배치로는 덜 깔끔 | 선택적 모델 실험 |
| Colab Free | 낮음 | 실험용으로 쉬움 | 자동 운영 안정성 낮음 | 비추천 |
| Airflow/Prefect 서버 | 낮음 | 전문 오케스트레이션 | 무료로 상시 운영 부담 | 추후 유료/서버 확보 시 검토 |

---

## 3. 운영 아키텍처

```text
GitHub Actions
  ├─ Morning Batch
  │   ├─ 미국 주식 데이터 수집
  │   ├─ 글로벌 지수/환율/금리/원자재 수집
  │   ├─ 공포탐욕지수 수집 시도
  │   └─ Supabase Postgres raw_market_data 저장
  │
  ├─ Afternoon Batch
  │   ├─ 한국 종목 가격/거래량 수집
  │   ├─ 외국인/기관/연기금 수급 수집
  │   └─ Supabase Postgres raw_market_data 저장
  │
  ├─ Prediction Batch
  │   ├─ feature engineering
  │   ├─ label update, 가능한 과거 날짜만
  │   ├─ ML inference
  │   ├─ model_predictions 저장
  │   └─ daily report 또는 summary 저장
  │
  └─ Weekly Training
      ├─ training dataset build
      ├─ baseline/model 후보 학습
      ├─ walk-forward validation
      ├─ 성능 기준 충족 시 model_registry 갱신
      └─ 기준 미달 시 기존 모델 유지

Supabase Free Postgres
  ├─ asset_master
  ├─ raw_market_data
  ├─ engineered_features
  ├─ model_labels
  ├─ model_predictions
  ├─ model_registry
  ├─ model_metrics
  ├─ pipeline_runs
  ├─ data_quality_checks
  └─ daily_research_outputs
```

---

## 4. 핵심 설계 원칙

### 4.1 Claude는 오케스트레이터, 계산과 데이터는 코드가 담당한다

Claude 또는 LLM 에이전트는 데이터를 직접 추정하거나 임의로 계산하지 않는다. 데이터 수집, 정제, 피처 계산, 라벨 생성, 모델 추론, 예측값 저장은 모두 Python 코드로 수행한다.

### 4.2 운영 DB는 Supabase Postgres, 로컬 DB는 SQLite

기존 SQLite 중심 MVP는 로컬 개발에는 적합하지만, GitHub Actions의 실행 환경은 매번 새로 만들어지므로 파일 기반 SQLite를 운영 저장소로 쓰면 데이터가 지속되지 않는다.

따라서 DB 역할을 다음처럼 분리한다.

| 환경 | DB | 용도 |
|---|---|---|
| 로컬 개발 | SQLite | 빠른 테스트, mock provider, 단위 테스트 |
| CI 테스트 | SQLite in-memory 또는 임시 파일 | 외부 네트워크 없는 테스트 |
| 운영 배치 | Supabase Free Postgres | 매일 데이터와 예측 결과 저장 |
| 대체 운영 DB | Neon Free Postgres | Supabase 대체 후보 |

`DatabaseManager` 인터페이스를 분리해 `SQLiteDatabaseManager`와 `PostgresDatabaseManager`를 교체 가능하게 만든다.

### 4.3 모든 데이터는 기준 시점을 명확히 가진다

ML 파이프라인에서 가장 중요한 것은 데이터가 “언제 관측되었고, 언제 투자자가 알 수 있었는지”를 구분하는 것이다.

모든 원천 데이터에는 아래 필드를 포함한다.

| 필드 | 의미 |
|---|---|
| `source` | 데이터 출처. 예: `pykrx`, `yfinance`, `manual`, `fear_greed` |
| `data_date` | 데이터가 귀속되는 시장 날짜 |
| `observed_date` | 원천 데이터의 기준일 |
| `available_at` | 해당 데이터가 투자자에게 사용 가능하다고 간주되는 시각 |
| `fetched_at` | 우리 시스템이 실제로 수집한 시각 |
| `batch_name` | `morning`, `afternoon`, `prediction`, `weekly_training`, `manual_backfill` 등 |

### 4.4 Look-ahead bias를 방지한다

모델 학습과 피처 생성은 반드시 `as_of_date` 기준으로 수행한다.

`as_of_date` 시점에 아직 알 수 없었던 데이터는 피처에 포함하지 않는다. 특히 미국장 데이터, 한국장 데이터, 금리, 환율, 공시성 데이터는 시장별 시차와 공개 가능 시점을 반영해야 한다.

### 4.5 원천 데이터와 피처 데이터를 분리한다

원천 데이터는 최대한 수정하지 않고 append 또는 idempotent upsert 방식으로 저장한다. 정제와 피처 생성은 별도 테이블에서 수행한다.

### 4.6 테스트에서는 외부 API를 호출하지 않는다

기본 `pytest`는 네트워크에 의존하지 않아야 한다. 외부 API 호출은 mock provider 또는 fixture 데이터로 대체한다.

### 4.7 무료 한도 초과를 방지한다

무료 서비스만 사용한다는 조건이 있으므로 저장량, 실행 시간, artifact 크기, API 호출량을 관리한다.

- raw data는 필요한 필드만 저장한다.
- 로그와 artifact는 장기 보관하지 않는다.
- 모델 파일은 작게 유지한다.
- 대형 DL 모델 학습은 MVP 범위에서 제외한다.
- GitHub Actions에서 무거운 학습을 매일 실행하지 않는다.

---

## 5. 기술 스택

### 5.1 MVP 기술 스택

| 영역 | 도구 |
|---|---|
| Language | Python 3.10+ 또는 Python 3.12 |
| Data processing | `pandas`, `numpy` |
| Market data | `pykrx`, `yfinance` |
| Technical indicators | `ta` 또는 내부 계산 함수 |
| HTTP | `requests`, 필요 시 `httpx` |
| Local DB | SQLite |
| Production DB | Supabase Free Postgres |
| DB access | `sqlalchemy`, `psycopg`, 또는 `asyncpg` 중 택1 |
| Test | `pytest` |
| CLI | `argparse` 또는 `typer` |
| Scheduler | GitHub Actions |
| Secrets | GitHub Actions Secrets |

### 5.2 향후 확장 후보

| 영역 | 향후 후보 | 비고 |
|---|---|---|
| Analytical DB | DuckDB | 로컬 분석/백테스트용 |
| Production DB | PostgreSQL | Supabase/Neon에서 시작 |
| Workflow | Prefect, Airflow | 무료 외부 서버 확보 전까지 보류 |
| Model tracking | MLflow | 무료로 직접 운영 필요하므로 후순위 |
| Feature store | Feast 또는 자체 feature table | MVP에서는 자체 table 유지 |
| Dashboard | Streamlit, FastAPI + Web UI | 운영 안정화 후 검토 |

---

## 6. 프로젝트 내 위치

권장 디렉터리 구조는 다음과 같다.

```text
stock-analysis-agent/
  .github/
    workflows/
      daily-market-pipeline.yml
      weekly-model-training.yml
      manual-backfill.yml

  services/
    data_gateway/
      market_data_lake/
        __init__.py
        database.py
        postgres_database.py
        sqlite_database.py
        schemas.py
        asset_registry.py
        extractors.py
        feature_engineer.py
        label_generator.py
        dataset_builder.py
        data_quality.py
        retention.py
        providers/
          __init__.py
          base.py
          pykrx_provider.py
          yfinance_provider.py
          macro_provider.py
          fear_greed_provider.py
          mock_provider.py

    model_service/
      __init__.py
      schemas.py
      baseline_model.py
      train.py
      predict.py
      prediction_store.py
      model_registry.py
      metrics.py

  pipelines/
    run_market_data_batch.py
    build_features.py
    build_training_dataset.py
    run_model_prediction.py
    train_model.py
    run_scheduled_pipeline.py
    backfill_market_data.py

  tests/
    unit/
      test_feature_engineer.py
      test_label_generator.py
      test_no_lookahead.py
      test_missing_value_policy.py
      test_model_prediction_schema.py
      test_database_interface.py
    integration/
      test_market_data_pipeline.py
      test_database_upsert.py
      test_provider_failure_handling.py
      test_scheduled_pipeline_mock.py
    external_api/
      test_pykrx_provider_external.py
      test_yfinance_provider_external.py
```

---

## 7. 데이터 수집 대상

### 7.1 한국 타겟 종목

오후 배치에서 한국장 마감 후 수집한다.

| 기업 | 티커 | 시장 | 비고 |
|---|---:|---|---|
| 삼성전자 | 005930 | KR | 반도체 대형주 |
| SK하이닉스 | 000660 | KR | 메모리 반도체 |
| NAVER | 035420 | KR | 인터넷/AI/커머스 |
| 현대차 | 005380 | KR | 자동차 |
| SK텔레콤 | 017670 | KR | 통신/배당주 |
| 기아 | 000270 | KR | 자동차 |
| 현대모비스 | 012330 | KR | 자동차 부품 |
| 카카오 | 035720 | KR | 플랫폼 |
| KT | 030200 | KR | 통신 |
| LG유플러스 | 032640 | KR | 통신 |

필수 수집 필드:

- 종가 `close`
- 시가 `open`
- 고가 `high`
- 저가 `low`
- 거래량 `volume`
- 거래대금 `trading_value`, 가능할 경우
- 외국인 순매수 `foreign_net_buy`
- 기관합계 순매수 `institution_net_buy`
- 연기금등 순매수 `pension_net_buy`

### 7.2 미국 및 글로벌 주식

오전 배치에서 미국장 마감 후 수집한다.

| 종목 | 티커 | 비고 |
|---|---|---|
| NVIDIA | NVDA | AI 반도체 |
| TSMC | TSM | 파운드리 |
| ASML | ASML | 반도체 장비 |
| Apple | AAPL | 빅테크 |
| Alphabet | GOOGL | 빅테크 |
| Meta | META | 빅테크/AI |
| Amazon | AMZN | 빅테크/클라우드 |
| Toyota | TM | 글로벌 자동차 |
| Tesla | TSLA | 전기차 |
| General Motors | GM | 자동차 |
| Verizon | VZ | 통신 |
| AT&T | T | 통신 |

필수 수집 필드:

- 종가 `close`
- 시가 `open`
- 고가 `high`
- 저가 `low`
- 거래량 `volume`
- 수정종가 `adjusted_close`, 가능할 경우

### 7.3 매크로 및 지수

오전 배치에서 수집한다. 단, 각 데이터의 실제 사용 가능 시각은 `available_at`에 기록한다.

| 구분 | 항목 | 예시 티커/출처 |
|---|---|---|
| 한국 지수 | 코스피200 | pykrx 또는 대체 데이터 |
| 미국 지수 | 나스닥100 | `^NDX` |
| 미국 지수 | S&P500 | `^GSPC` |
| 반도체 | 필라델피아반도체 | `^SOX` |
| 변동성 | VIX | `^VIX` |
| 환율 | 원/달러 | `KRW=X` |
| 환율 | 원/엔 | 데이터 공급원 확인 필요 |
| 원자재 | WTI 유가 | `CL=F` |
| 원자재 | 금 | `GC=F` |
| 금리 | 미국채 2년물 | 데이터 공급원 확인 필요 |
| 금리 | 미국채 10년물 | 데이터 공급원 확인 필요 |
| 금리 | 한국 국고채 3년물 | 데이터 공급원 확인 필요 |
| 금리 | 한국 국고채 5년물 | 데이터 공급원 확인 필요 |
| 심리 | CNN Fear & Greed Index | optional provider |
| 선물 | KOSPI 200 야간선물 | 데이터 공급원 확인 필요 |

CNN 공포탐욕지수는 안정적인 공식 API가 보장되지 않을 수 있으므로 optional provider로 구현한다. 수집 실패 시 전체 파이프라인을 실패시키지 않고 warning과 품질 체크 결과만 남긴다.

---

## 8. 데이터베이스 스키마

### 8.1 `asset_master`

수집 대상 자산의 메타데이터를 관리한다.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `asset_id` | TEXT PRIMARY KEY | 내부 자산 ID. 예: `KR_005930`, `US_NVDA`, `MACRO_VIX` |
| `ticker` | TEXT | 외부 데이터 공급원 티커 |
| `name` | TEXT | 자산명 |
| `market` | TEXT | `KR`, `US`, `GLOBAL`, `MACRO` |
| `asset_type` | TEXT | `stock`, `index`, `fx`, `rate`, `commodity`, `sentiment` |
| `currency` | TEXT | `KRW`, `USD`, `JPY` 등 |
| `sector` | TEXT | 섹터. 없으면 null 허용 |
| `is_active` | INTEGER | 수집 활성 여부 |
| `created_at` | TIMESTAMP | 생성 시각 |
| `updated_at` | TIMESTAMP | 수정 시각 |

### 8.2 `raw_market_data`

원천 수집 데이터를 저장한다. 기존 `raw_market_prices`보다 넓은 개념의 long-format 테이블이다.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | row id |
| `asset_id` | TEXT | `asset_master.asset_id` |
| `data_date` | DATE | 데이터 귀속 날짜 |
| `field_name` | TEXT | `close`, `volume`, `foreign_net_buy`, `vix`, `yield_10y` 등 |
| `field_value` | REAL | 수치 값 |
| `source` | TEXT | 데이터 출처 |
| `observed_date` | DATE | 원천 데이터 기준일 |
| `available_at` | TIMESTAMP | 사용 가능 시각 |
| `fetched_at` | TIMESTAMP | 수집 시각 |
| `batch_name` | TEXT | `morning`, `afternoon`, `manual_backfill` |
| `provider_metadata_json` | TEXT | 원천 응답 일부 또는 메타데이터 |

권장 유니크 키:

```text
(asset_id, data_date, field_name, source)
```

주의:

- 같은 데이터가 같은 날짜에 여러 번 수집되어도 중복 row를 만들지 않는다.
- `batch_name`은 중복 방지 키에 넣지 않는 것을 기본값으로 한다. 같은 값이 morning/manual_backfill에서 들어와도 동일 데이터로 취급하기 위함이다.
- provider별로 같은 필드의 값이 다를 수 있으면 `source`를 포함해 공급원별로 구분한다.

### 8.3 `engineered_features`

모델 학습과 예측에 사용할 피처를 저장한다.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | row id |
| `asset_id` | TEXT | 자산 ID |
| `as_of_date` | DATE | 피처 기준일 |
| `feature_name` | TEXT | 피처명 |
| `feature_value` | REAL | 피처 값 |
| `source_version` | TEXT | 피처 생성 코드 버전 또는 해시 |
| `created_at` | TIMESTAMP | 생성 시각 |

권장 유니크 키:

```text
(asset_id, as_of_date, feature_name, source_version)
```

### 8.4 `model_labels`

지도학습용 정답값을 저장한다.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | row id |
| `asset_id` | TEXT | 자산 ID |
| `as_of_date` | DATE | 예측 기준일 |
| `horizon_days` | INTEGER | 1, 5, 20 등 |
| `future_return` | REAL | horizon 이후 수익률 |
| `excess_return` | REAL | 벤치마크 대비 초과수익률 |
| `target_class` | INTEGER | 상승이면 1, 아니면 0 |
| `benchmark_asset_id` | TEXT | 초과수익률 기준 자산 |
| `created_at` | TIMESTAMP | 생성 시각 |

권장 유니크 키:

```text
(asset_id, as_of_date, horizon_days, benchmark_asset_id)
```

### 8.5 `model_predictions`

모델 추론 결과를 저장한다.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | row id |
| `asset_id` | TEXT | 자산 ID |
| `as_of_date` | DATE | 예측 기준일 |
| `model_version` | TEXT | 모델 버전 |
| `prediction_horizon` | TEXT | 예: `20 trading days` |
| `expected_return` | REAL | 기대수익률 추정치 |
| `downside_probability` | REAL | 하방 확률 |
| `confidence` | TEXT | `low`, `medium`, `high` |
| `top_features_json` | TEXT | 주요 피처 목록 JSON |
| `data_quality_status` | TEXT | `pass`, `warning`, `fail` |
| `created_at` | TIMESTAMP | 생성 시각 |

권장 유니크 키:

```text
(asset_id, as_of_date, model_version, prediction_horizon)
```

### 8.6 `model_registry`

운영에 사용하는 모델 버전을 관리한다.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `model_version` | TEXT PRIMARY KEY | 모델 버전. 예: `baseline-v1` |
| `model_type` | TEXT | `baseline`, `xgboost`, `lightgbm`, `lstm` 등 |
| `artifact_uri` | TEXT | 모델 파일 위치. repo path 또는 storage path |
| `feature_version` | TEXT | 사용한 feature source version |
| `training_start_date` | DATE | 학습 시작일 |
| `training_end_date` | DATE | 학습 종료일 |
| `target_horizon_days` | INTEGER | 예측 horizon |
| `status` | TEXT | `candidate`, `production`, `archived` |
| `created_at` | TIMESTAMP | 생성 시각 |

### 8.7 `model_metrics`

모델 검증 성능을 저장한다.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | row id |
| `model_version` | TEXT | 모델 버전 |
| `metric_name` | TEXT | `mae`, `rmse`, `directional_accuracy`, `ic`, `hit_rate` 등 |
| `metric_value` | REAL | 성능 값 |
| `evaluation_start_date` | DATE | 평가 시작일 |
| `evaluation_end_date` | DATE | 평가 종료일 |
| `created_at` | TIMESTAMP | 생성 시각 |

### 8.8 `pipeline_runs`

배치 실행 이력을 저장한다.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `run_id` | TEXT PRIMARY KEY | 실행 ID |
| `pipeline_name` | TEXT | 배치명 |
| `batch_name` | TEXT | `morning`, `afternoon`, `features`, `prediction`, `weekly_training` |
| `run_date` | DATE | 실행 대상 날짜 |
| `started_at` | TIMESTAMP | 시작 시각 |
| `finished_at` | TIMESTAMP | 종료 시각 |
| `status` | TEXT | `success`, `failed`, `partial_success`, `skipped` |
| `row_count` | INTEGER | 처리 row 수 |
| `message` | TEXT | 요약 메시지 |
| `github_run_id` | TEXT | GitHub Actions run id, 가능할 경우 |

### 8.9 `data_quality_checks`

품질 검사 결과를 저장한다.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | row id |
| `run_id` | TEXT | pipeline run id |
| `check_name` | TEXT | 검사명 |
| `asset_id` | TEXT | 해당 자산. 전체 검사면 null |
| `as_of_date` | DATE | 기준일 |
| `status` | TEXT | `pass`, `warning`, `fail` |
| `severity` | TEXT | `info`, `warning`, `critical` |
| `message` | TEXT | 상세 메시지 |
| `created_at` | TIMESTAMP | 생성 시각 |

### 8.10 `daily_research_outputs`

리포트 에이전트가 조회할 수 있는 일별 산출물을 저장한다.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | row id |
| `as_of_date` | DATE | 기준일 |
| `output_type` | TEXT | `prediction_summary`, `data_quality_summary`, `watchlist_report` |
| `content_markdown` | TEXT | Markdown 결과물 |
| `source_json` | TEXT | 사용한 prediction 또는 feature 요약 |
| `created_at` | TIMESTAMP | 생성 시각 |

---

## 9. 배치 스케줄링

### 9.1 기본 배치 시간

| 배치 | KST 기준 실행 시간 | 목적 | 실행 빈도 |
|---|---:|---|---|
| Morning Batch | 07:40 | 미국장/글로벌/매크로 수집 | 화~토 |
| Afternoon Batch | 16:40 | 한국장 가격/수급 수집 | 월~금 |
| Prediction Batch | 17:10 | 피처 생성 + 모델 예측 | 월~금 |
| Weekly Training | 토요일 10:00 | 모델 재학습/검증 | 주 1회 |
| Manual Backfill | 수동 | 누락 데이터 복구 | 필요 시 |

### 9.2 GitHub Actions cron 설계

GitHub Actions 스케줄은 UTC 또는 timezone 설정을 기준으로 해석될 수 있으므로, 구현 시 공식 문서를 기준으로 확인한다. 안전하게 운영하려면 UTC fallback 값을 함께 주석으로 남긴다.

KST는 UTC+9이다.

| 배치 | KST | UTC fallback cron |
|---|---:|---|
| Morning Batch | 화~토 07:40 | 월~금 22:40 UTC → `40 22 * * 1-5` |
| Afternoon Batch | 월~금 16:40 | 월~금 07:40 UTC → `40 7 * * 1-5` |
| Prediction Batch | 월~금 17:10 | 월~금 08:10 UTC → `10 8 * * 1-5` |
| Weekly Training | 토 10:00 | 토 01:00 UTC → `0 1 * * 6` |

### 9.3 Workflow 분리 전략

MVP에서는 하나의 workflow에서 분기 처리해도 된다. 다만 운영 가독성을 위해 다음처럼 분리하는 것을 권장한다.

```text
.github/workflows/daily-market-pipeline.yml
  - morning
  - afternoon
  - prediction
  - workflow_dispatch 수동 실행

.github/workflows/weekly-model-training.yml
  - weekly training
  - workflow_dispatch 수동 실행

.github/workflows/manual-backfill.yml
  - 날짜 범위 지정 backfill
  - workflow_dispatch only
```

### 9.4 Daily workflow 예시

```yaml
name: Daily Market Pipeline

on:
  schedule:
    # 07:40 KST Tue-Sat = 22:40 UTC Mon-Fri
    - cron: "40 22 * * 1-5"
    # 16:40 KST Mon-Fri = 07:40 UTC Mon-Fri
    - cron: "40 7 * * 1-5"
    # 17:10 KST Mon-Fri = 08:10 UTC Mon-Fri
    - cron: "10 8 * * 1-5"
  workflow_dispatch:
    inputs:
      batch:
        description: "morning, afternoon, prediction, all"
        required: true
        default: "all"
      run_date:
        description: "YYYY-MM-DD, KST 기준. 비우면 오늘"
        required: false

jobs:
  run-pipeline:
    runs-on: ubuntu-latest
    timeout-minutes: 20

    env:
      DATABASE_URL: ${{ secrets.SUPABASE_DB_URL }}
      DART_API_KEY: ${{ secrets.DART_API_KEY }}
      PYTHONUNBUFFERED: "1"

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .

      - name: Run tests without external API
        run: |
          pytest -m "not external_api"

      - name: Run scheduled pipeline
        run: |
          python -m pipelines.run_scheduled_pipeline
```

주의:

- 실제 구현에서는 `github.event.schedule` 값 또는 `workflow_dispatch.inputs.batch`를 읽어 어떤 batch를 실행할지 분기한다.
- GitHub Actions의 실행 시각은 지연될 수 있으므로 장마감 직후가 아니라 10~30분 여유를 둔다.
- 배치는 반드시 idempotent해야 한다.

---

## 10. Pipeline CLI 설계

### 10.1 Market data batch

```bash
python -m pipelines.run_market_data_batch --batch morning --date YYYY-MM-DD
python -m pipelines.run_market_data_batch --batch afternoon --date YYYY-MM-DD
```

### 10.2 Feature build

```bash
python -m pipelines.build_features --date YYYY-MM-DD
```

### 10.3 Training dataset build

```bash
python -m pipelines.build_training_dataset --horizon 20 --start YYYY-MM-DD --end YYYY-MM-DD
```

### 10.4 Prediction

```bash
python -m pipelines.run_model_prediction --date YYYY-MM-DD --model-version baseline-v1
```

### 10.5 Weekly training

```bash
python -m pipelines.train_model --mode weekly --horizon 20
```

### 10.6 Scheduled pipeline dispatcher

```bash
python -m pipelines.run_scheduled_pipeline --batch morning --date YYYY-MM-DD
python -m pipelines.run_scheduled_pipeline --batch afternoon --date YYYY-MM-DD
python -m pipelines.run_scheduled_pipeline --batch prediction --date YYYY-MM-DD
python -m pipelines.run_scheduled_pipeline --batch all --date YYYY-MM-DD
```

### 10.7 Backfill

```bash
python -m pipelines.backfill_market_data --start YYYY-MM-DD --end YYYY-MM-DD --batch all
```

---

## 11. 배치별 상세 로직

### 11.1 Morning Batch

실행 시각: 한국시간 07:40 권장

역할:

1. 미국 및 글로벌 주식 데이터 수집
2. 미국 지수, VIX, 원자재, 환율, 금리 데이터 수집
3. CNN 공포탐욕지수 수집 시도
4. KOSPI 200 야간선물 데이터 수집 시도
5. 수집 결과를 `raw_market_data`에 저장
6. 실패한 optional provider는 warning으로 기록
7. `pipeline_runs`와 `data_quality_checks`에 결과 저장

주의:

- `--date`는 한국 기준 실행일을 의미한다.
- 미국장 데이터의 `data_date`는 미국 시장일 기준으로 다를 수 있다.
- ML 피처에는 `available_at` 기준으로 사용 가능 여부를 판단한다.

### 11.2 Afternoon Batch

실행 시각: 한국시간 16:40 권장

역할:

1. 한국 타겟 종목 가격 데이터 수집
2. 한국 타겟 종목 수급 데이터 수집
3. 코스피200 등 한국 시장 데이터 수집
4. `raw_market_data`에 저장
5. `pipeline_runs`와 `data_quality_checks`에 결과 저장

### 11.3 Prediction Batch

실행 시각: 한국시간 17:10 권장

역할:

1. 당일 afternoon batch 성공 여부 확인
2. `raw_market_data`를 `as_of_date` 기준으로 조회
3. 사용 가능한 데이터만 사용해 feature 계산
4. `engineered_features`에 upsert
5. 과거 날짜 중 label 생성 가능한 건만 `model_labels` 업데이트
6. production 모델 버전 조회
7. ML inference 실행
8. `model_predictions`에 결과 저장
9. `daily_research_outputs`에 요약 markdown 저장
10. `pipeline_runs`와 `data_quality_checks`에 결과 저장

### 11.4 Weekly Training

실행 시각: 토요일 10:00 KST 권장

역할:

1. 학습 기간의 feature/label 데이터셋 생성
2. 시간 순서 기준 train/validation/test split
3. baseline 또는 후보 모델 학습
4. walk-forward validation
5. 성능이 기준 이상이면 `model_registry`에 candidate 또는 production 등록
6. 기준 미달이면 기존 production 모델 유지
7. 모델 성능을 `model_metrics`에 저장

주의:

- 무료 GitHub Actions 한도를 고려해 학습 시간을 짧게 유지한다.
- 초기에는 Logistic Regression, RandomForest, XGBoost/LightGBM 등 CPU 기반 경량 모델을 우선한다.
- DL 모델은 데이터와 운영 안정성이 확보된 이후 검토한다.

---

## 12. Feature Engineering 설계

### 12.1 기본 가격 기반 피처

| 피처 | 설명 |
|---|---|
| `log_return_1d` | 1일 로그 수익률 |
| `return_5d` | 5거래일 단순 수익률 |
| `return_20d` | 20거래일 단순 수익률 |
| `volatility_20d` | 20거래일 수익률 표준편차 |
| `volume_change_5d` | 5거래일 평균 거래량 변화율 |

### 12.2 기술적 지표

| 피처 | 설명 |
|---|---|
| `rsi_14` | 14일 RSI |
| `macd` | MACD |
| `macd_signal` | MACD signal |
| `bollinger_width` | Bollinger Band Width |
| `obv` | On-Balance Volume |

### 12.3 수급 피처

수급 데이터는 forward fill하지 않는다.

| 피처 | 설명 |
|---|---|
| `foreign_net_buy_1d` | 외국인 순매수 |
| `foreign_net_buy_5d_sum` | 외국인 순매수 5일 합 |
| `foreign_net_buy_20d_sum` | 외국인 순매수 20일 합 |
| `institution_net_buy_5d_sum` | 기관 순매수 5일 합 |
| `institution_net_buy_20d_sum` | 기관 순매수 20일 합 |
| `pension_net_buy_20d_sum` | 연기금 순매수 20일 합 |
| `flow_missing_flag` | 수급 데이터 결측 여부 |

### 12.4 도메인 파생 피처

| 피처 | 설명 |
|---|---|
| `hyundai_kia_price_ratio` | 현대차 종가 / 기아 종가 |
| `hyundai_kia_ratio_change_20d` | 현대차/기아 비율의 20일 변화율 |
| `skt_yield_gap` | SKT 배당수익률 - 한국 국고채 3년물 금리 |

SKT 배당수익률은 MVP에서는 하드코딩 상수를 허용한다. 단, 반드시 설정 파일 또는 상수 모듈에서 관리하고, 향후 배당 데이터 provider로 교체할 수 있게 한다.

### 12.5 매크로 피처

| 피처 | 설명 |
|---|---|
| `vix_level` | VIX 수준 |
| `usd_krw_return_5d` | 원/달러 5일 변화율 |
| `us_10y_yield` | 미국채 10년물 금리 |
| `us_2y_10y_spread` | 미국채 10년-2년 스프레드 |
| `kr_3y_yield` | 한국 국고채 3년물 금리 |
| `sox_return_1d` | 필라델피아반도체 1일 수익률 |
| `ndx_return_1d` | 나스닥100 1일 수익률 |
| `spx_return_1d` | S&P500 1일 수익률 |
| `wti_return_5d` | WTI 5일 변화율 |
| `gold_return_5d` | 금 5일 변화율 |
| `fear_greed_index` | 공포탐욕지수. optional |

### 12.6 결측치 처리 원칙

| 데이터 유형 | 처리 원칙 |
|---|---|
| 가격 | 거래일 정렬 목적의 제한적 forward fill 허용 |
| 지수 | 제한적 forward fill 허용 |
| 환율 | 제한적 forward fill 허용 |
| 금리 | 제한적 forward fill 허용 |
| 거래량 | forward fill 금지. 결측 flag 생성 |
| 외국인/기관/연기금 순매수 | forward fill 금지. 0 또는 NaN + missing flag 처리 |
| 공포탐욕지수 | optional. 실패 시 NaN 또는 직전값 사용 옵션 |
| 재무제표 | 발표일과 사용 가능일 기준으로 유지 |

---

## 13. Label 생성 설계

`LabelGenerator`는 지도학습용 정답값을 생성한다.

### 13.1 기본 라벨

| 라벨 | 설명 |
|---|---|
| `future_return_1d` | 1거래일 후 수익률 |
| `future_return_5d` | 5거래일 후 수익률 |
| `future_return_20d` | 20거래일 후 수익률 |
| `target_up_20d` | 20거래일 후 수익률이 0보다 크면 1, 아니면 0 |
| `target_excess_20d` | 종목 20일 수익률 - 벤치마크 20일 수익률 |

### 13.2 라벨 생성 주의사항

- 라벨은 학습 데이터 생성 단계에서만 사용한다.
- 예측 시점의 feature 계산에는 미래 가격이 절대 들어가면 안 된다.
- `model_labels`는 `engineered_features`와 별도 테이블로 관리한다.
- 학습/검증/테스트 데이터 분리는 시간 순서 기준으로 수행한다.
- 당일 예측 batch에서 미래 가격이 필요한 label은 생성하지 않는다. label은 horizon이 지난 과거 `as_of_date`에 대해서만 생성한다.

---

## 14. Model Service 연결 설계

모델은 `model_service`에서 별도 모듈로 관리한다.

### 14.1 모델 입력

`TrainingDatasetBuilder`가 다음 형태의 데이터를 만든다.

```text
as_of_date | asset_id | feature_1 | feature_2 | ... | label
```

모델 추론 시에는 label 없이 같은 피처 컬럼만 사용한다.

### 14.2 모델 출력 schema

모델 예측 결과는 아래 JSON 구조를 따른다.

```json
{
  "ticker": "005930",
  "market": "KR",
  "as_of_date": "YYYY-MM-DD",
  "prediction_horizon": "20 trading days",
  "expected_return": 0.032,
  "downside_probability": 0.38,
  "confidence": "low",
  "top_features": ["relative_momentum", "foreign_flow_20d", "vix"],
  "model_version": "baseline-v1",
  "data_quality_status": "warning"
}
```

### 14.3 리포트 에이전트 사용 원칙

허용:

```text
모델 기준 20거래일 기대수익률은 +3.2%로 추정되지만, 하방 확률이 38%이고 confidence가 low이므로 단독 투자 근거로 쓰기 어렵다.
```

금지:

```text
모델이 상승을 예측했으므로 매수해야 한다.
```

---

## 15. 주요 클래스 설계

### 15.1 `DatabaseManager`

역할:

- 공통 DB 인터페이스 정의
- table migration 실행
- raw data insert/upsert
- feature upsert
- label upsert
- prediction upsert
- model registry 저장
- pipeline run 기록
- data quality 결과 기록

구현체:

| 클래스 | 용도 |
|---|---|
| `SQLiteDatabaseManager` | 로컬/테스트용 |
| `PostgresDatabaseManager` | Supabase/Neon 운영용 |

### 15.2 `AssetRegistry`

역할:

- `asset_master` 초기화
- 수집 대상 종목과 매크로 자산 관리
- ticker와 asset_id 매핑

### 15.3 `MarketDataExtractor`

역할:

- 배치 이름에 따라 provider 호출
- provider 결과를 표준 schema로 변환
- 실패한 provider를 logging하고 optional/required 여부에 따라 처리

### 15.4 Provider 계층

공통 인터페이스:

```python
class BaseMarketDataProvider:
    def fetch(self, assets, start_date, end_date, context):
        ...
```

Provider 목록:

| 클래스 | 역할 |
|---|---|
| `PykrxProvider` | 한국 주식 가격, 거래량, 수급 데이터 |
| `YFinanceProvider` | 미국 주식, 글로벌 지수, 환율, 원자재 일부 |
| `MacroDataProvider` | 금리, 지수, 매크로 데이터 |
| `FearGreedProvider` | CNN 공포탐욕지수. optional |
| `MockProvider` | 테스트용 provider |

### 15.5 `FeatureEngineer`

역할:

- raw data를 pivot 또는 time-series 형태로 변환
- 가격 기반 피처 계산
- 기술적 지표 계산
- 수급 rolling 피처 계산
- 도메인 피처 계산
- 매크로 피처 병합
- 결측치 정책 적용

### 15.6 `LabelGenerator`

역할:

- horizon별 future return 계산
- 상승/하락 classification label 생성
- benchmark 대비 excess return 계산

### 15.7 `TrainingDatasetBuilder`

역할:

- `engineered_features`와 `model_labels`를 wide-format으로 결합
- 기간 필터링
- 시간 순서 기반 split 지원
- 모델 학습용 DataFrame 반환

### 15.8 `DataQualityChecker`

역할:

- 중복 데이터 검사
- 결측치 비율 검사
- optional provider 실패 기록
- 비정상 값 검사
- `available_at > fetched_at` 같은 시간 오류 검사
- no look-ahead rule 검사
- stale data 검사

### 15.9 `ModelPredictionStore`

역할:

- 모델 예측 결과 schema 검증
- `model_predictions` 저장
- 리포트 에이전트가 조회할 수 있는 형태로 반환

### 15.10 `ScheduledPipelineRunner`

역할:

- GitHub Actions에서 호출되는 entrypoint
- schedule 또는 workflow_dispatch input을 batch로 변환
- batch별 실행 순서 관리
- 실패 시 `pipeline_runs`에 기록
- optional provider 실패와 required provider 실패를 구분

---

## 16. GitHub Secrets 설계

운영 배치에는 API key와 DB URL을 코드에 직접 넣지 않는다. GitHub Actions Secrets를 사용한다.

필수 secrets:

| Secret | 설명 |
|---|---|
| `SUPABASE_DB_URL` 또는 `DATABASE_URL` | Supabase Postgres connection string |
| `DART_API_KEY` | OpenDART 사용 시 |

선택 secrets:

| Secret | 설명 |
|---|---|
| `FRED_API_KEY` | FRED 또는 금리 데이터 provider 사용 시 |
| `SLACK_WEBHOOK_URL` | 배치 실패 알림을 붙일 경우. MVP에서는 선택 |
| `NOTION_API_KEY` | 리포트 저장을 Notion으로 확장할 경우. MVP에서는 제외 |

금지:

- API key를 코드, 테스트 fixture, README 예시에 실값으로 넣지 않는다.
- `.env` 파일을 git에 올리지 않는다.
- Supabase service role key를 클라이언트 코드에 노출하지 않는다.

---

## 17. 무료 한도 관리 정책

### 17.1 DB 저장량 관리

무료 DB 용량을 넘기지 않기 위해 다음 원칙을 적용한다.

1. raw data는 필요한 필드만 long-format으로 저장한다.
2. provider 원본 응답 전체를 저장하지 않고 핵심 metadata만 저장한다.
3. `provider_metadata_json`은 길이를 제한한다.
4. 지나치게 오래된 intraday data는 저장하지 않는다. MVP는 daily data만 사용한다.
5. `pipeline_runs`, `data_quality_checks`는 일정 기간 이후 요약 또는 삭제할 수 있게 한다.

### 17.2 Actions 실행 시간 관리

1. 기본 테스트는 mock 기반으로 빠르게 실행한다.
2. 외부 API 테스트는 기본 workflow에서 제외한다.
3. daily prediction은 inference만 수행한다.
4. weekly training은 timeout을 둔다.
5. 대형 DL 학습은 GitHub Actions에서 수행하지 않는다.

### 17.3 모델 artifact 관리

1. 초기 모델은 작은 `joblib` 또는 `pickle` 파일로 관리한다.
2. 100MB 이상 대형 모델 파일은 repo에 넣지 않는다.
3. production 모델만 보관하고 오래된 candidate는 정리한다.
4. 모델 registry에는 artifact 경로와 성능 지표만 저장한다.

---

## 18. 테스트 계획

### 18.1 단위 테스트

| 테스트 파일 | 목적 |
|---|---|
| `test_feature_engineer.py` | RSI, MACD, 수익률, rolling flow 계산 검증 |
| `test_label_generator.py` | future return, target_up, excess_return 검증 |
| `test_no_lookahead.py` | `as_of_date` 이후 데이터가 피처에 들어가지 않는지 검증 |
| `test_missing_value_policy.py` | 가격/수급/매크로별 결측치 처리 정책 검증 |
| `test_model_prediction_schema.py` | 예측 결과 schema 검증 |
| `test_database_interface.py` | SQLite/Postgres 공통 인터페이스 계약 검증 |

### 18.2 통합 테스트

| 테스트 파일 | 목적 |
|---|---|
| `test_market_data_pipeline.py` | mock provider 기반 morning/afternoon 배치 실행 검증 |
| `test_database_upsert.py` | raw/feature/label/prediction upsert 검증 |
| `test_provider_failure_handling.py` | optional provider 실패 시 pipeline 지속 여부 검증 |
| `test_scheduled_pipeline_mock.py` | GitHub Actions entrypoint의 batch 분기 검증 |

### 18.3 외부 API 테스트

| 테스트 파일 | 목적 |
|---|---|
| `test_pykrx_provider_external.py` | 실제 pykrx provider 수집 검증 |
| `test_yfinance_provider_external.py` | 실제 yfinance provider 수집 검증 |

원칙:

- 기본 `pytest`에서는 실제 외부 API를 호출하지 않는다.
- 실제 provider 테스트는 `external_api` marker를 둔다.
- CI에서는 기본적으로 `pytest -m "not external_api"`만 실행한다.

---

## 19. 실패 처리와 복구 전략

### 19.1 Provider 실패 처리

| Provider 유형 | 실패 시 처리 |
|---|---|
| required provider | batch status를 `failed` 또는 `partial_success`로 기록 |
| optional provider | warning 기록 후 pipeline 계속 진행 |
| 공포탐욕지수 | warning + NaN 또는 직전값 사용 옵션 |
| 특정 종목 일부 실패 | 해당 asset만 warning, 나머지 계속 처리 |

### 19.2 재실행 원칙

배치는 idempotent해야 한다.

- 같은 날짜에 두 번 실행되어도 중복 저장하지 않는다.
- raw data upsert 기준은 `(asset_id, data_date, field_name, source)`로 한다.
- feature upsert 기준은 `(asset_id, as_of_date, feature_name, source_version)`로 한다.
- prediction upsert 기준은 `(asset_id, as_of_date, model_version, prediction_horizon)`로 한다.

### 19.3 Backfill

누락 데이터가 생기면 `manual-backfill.yml` workflow 또는 로컬 CLI로 복구한다.

```bash
python -m pipelines.backfill_market_data --start 2026-01-01 --end 2026-01-31 --batch all
```

---

## 20. 구현 단계

### 20.1 1단계: DB 인터페이스와 Mock 기반 파이프라인

목표:

- `DatabaseManager` 인터페이스 정의
- SQLite 구현체 작성
- Postgres 구현체 skeleton 작성
- schema 생성
- `asset_master` 초기화
- mock provider로 morning/afternoon batch 실행
- raw data 저장 테스트 통과

### 20.2 2단계: Supabase 운영 연결

목표:

- `PostgresDatabaseManager` 구현
- `SUPABASE_DB_URL` 환경변수 연결
- GitHub Secrets 사용
- DB migration 실행 CLI 추가
- GitHub Actions에서 mock 테스트 후 DB 연결 smoke check

### 20.3 3단계: Feature Engineering

목표:

- 가격 기반 피처 계산
- 기술적 지표 계산
- 수급 rolling 피처 계산
- 도메인 피처 계산
- 결측치 정책 테스트 통과

### 20.4 4단계: Label 생성

목표:

- 1일, 5일, 20일 future return 생성
- 상승/하락 label 생성
- benchmark 대비 excess return 생성
- no look-ahead 테스트 통과

### 20.5 5단계: 실제 Provider 연결

목표:

- `pykrx` provider 연결
- `yfinance` provider 연결
- optional macro/fear-greed provider 연결
- 외부 API 테스트는 별도 marker로 분리

### 20.6 6단계: Daily Prediction Batch

목표:

- baseline 모델 추론 구현
- `model_predictions` 저장
- `daily_research_outputs` 저장
- GitHub Actions daily workflow와 연결

### 20.7 7단계: Weekly Training Batch

목표:

- training dataset 생성
- baseline 모델 재학습
- 검증 성능 저장
- 성능 기준 충족 시 production 모델 갱신

---

## 21. Claude Code 구현 지시 원칙

Claude Code에게 이 문서를 구현시키기 전, 먼저 다음을 요구한다.

1. 변경할 파일 목록
2. 새로 만들 파일 목록
3. DB schema 초안
4. GitHub Actions workflow 설계
5. Supabase secrets 목록
6. CLI 명령어 설계
7. 테스트 계획
8. 외부 API 호출 없이 mock 기반으로 먼저 구현하는 계획

Claude Code는 승인 없이 대규모 파일 수정을 하지 않는다.

---

## 22. Claude Code에 줄 구현 요청 예시

```text
이 문서 `data_PIPELINE_PLAN.md`에 맞춰 무료 운영형 ML 마켓 데이터 파이프라인 MVP를 구현해줘.

중요 조건:
- 로컬 PC가 꺼져 있어도 매일 배치가 돌아가야 하므로 운영 스케줄러는 GitHub Actions를 사용한다.
- 운영 DB는 Supabase Free Postgres를 기본으로 한다.
- 로컬 개발과 테스트는 SQLite를 사용한다.
- 모든 외부 서비스는 무료 플랜 기준으로만 사용한다.
- 자동매매, 주문 API, 매수/매도 추천 기능은 만들지 않는다.
- 매일 실행할 것은 데이터 수집, feature 생성, ML inference이다.
- 모델 재학습은 매일 하지 말고 주 1회 또는 수동 실행으로 분리한다.

바로 구현하지 말고 먼저 아래 내용을 보여줘.
1. 바꿀 파일 목록
2. 새로 만들 파일 목록
3. DB 스키마 초안
4. GitHub Actions workflow 설계
5. Supabase/GitHub Secrets 목록
6. CLI 명령어 설계
7. 테스트 계획
8. mock provider 기반 MVP 구현 순서

구현 원칙:
- 테스트에서 실제 외부 API를 호출하지 마라.
- GitHub Actions 기본 테스트는 `pytest -m "not external_api"`로 실행해라.
- 모든 데이터에는 source, data_date, observed_date, available_at, fetched_at, batch_name을 포함해라.
- look-ahead bias를 막기 위한 test_no_lookahead.py를 반드시 추가해라.
- DatabaseManager 인터페이스를 분리해 SQLite와 Supabase Postgres를 교체 가능하게 해라.
- CNN 공포탐욕지수 provider는 optional로 구현하고, 실패해도 전체 파이프라인이 죽지 않게 해라.
- 배치는 idempotent하게 구현해 같은 날짜에 두 번 실행되어도 중복 저장되지 않게 해라.
- pipeline_runs와 data_quality_checks에 모든 실행 결과를 남겨라.
```

---

## 23. 투자 리서치 관점의 사용 제한

이 파이프라인과 모델은 투자 결정을 자동화하기 위한 것이 아니다.

모델 예측 결과는 다음 항목과 함께 해석해야 한다.

1. 기업 실적 변화
2. 밸류에이션 부담
3. 수급 변화
4. 금리와 환율 환경
5. 업종 사이클
6. 실적 발표 전후 변동성
7. 포트폴리오 비중과 손실 감내폭
8. 데이터 품질 상태
9. 모델 검증 성능

모델의 기대수익률이 높더라도 하방 확률, 신뢰도, 데이터 품질, 시장 환경을 함께 확인해야 한다.

---

## 24. 최종 산출물

MVP 완료 시점의 산출물은 다음과 같다.

1. Supabase Free Postgres 기반 운영 DB
2. 로컬 SQLite 기반 개발/테스트 DB
3. `asset_master`, `raw_market_data`, `engineered_features`, `model_labels`, `model_predictions`, `model_registry`, `model_metrics`, `pipeline_runs`, `data_quality_checks`, `daily_research_outputs` 테이블
4. morning/afternoon batch CLI
5. feature build CLI
6. training dataset build CLI
7. daily model prediction CLI
8. weekly model training CLI
9. GitHub Actions daily workflow
10. GitHub Actions weekly training workflow
11. manual backfill workflow
12. mock provider 기반 테스트 세트
13. no look-ahead 테스트
14. 결측치 정책 테스트
15. model prediction schema 테스트
16. provider 실패 처리 테스트
17. Claude 리포트 에이전트가 예측 결과를 조회할 수 있는 schema

