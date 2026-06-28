# Stock Analysis Agent

국내/미국 주식 구조적 분석 리포트 생성 도구.
투자 판단을 대신하지 않으며, 모든 수치는 Python calculation_engine으로 계산합니다.
자동매매·주문 API·매수매도 추천 기능은 없습니다.

---

## Quick Start — Mock 모드 (API 키 불필요)

```powershell
# 1. 의존성 설치
pip install anthropic pydantic pydantic-settings python-dotenv yfinance httpx finance-datareader pykrx requests pandas numpy ta jinja2 markdown typer rich fastapi "uvicorn[standard]"

# 2. PYTHONPATH 설정 (Korean path workaround — pip install -e . 사용 금지)
$env:PYTHONPATH = "C:\Users\elcax\OneDrive\바탕 화면\최용원\자격증 및 증명\개인 포트폴리오\26년\stock-analysis-agent\stock-analysis-agent"
Set-Location $env:PYTHONPATH

# 3. 실행 — 가상 데이터로 Markdown 리포트 출력
python -m apps.cli.main AAPL --market US --mock
python -m apps.cli.main 005930 --market KR --mock
```

출력 예시:
```
# AAPL 분석 리포트
## A. 한 줄 요약
Apple Inc. (AAPL, US) — 섹터: Technology, PER: 17.40x, 영업이익률: 30.00%
...
```

---

## 실제 API 모드 (Claude + 실시간 데이터)

```powershell
# .env.example → .env 복사 후 API 키 입력
cp .env.example .env

# 실행
python -m apps.cli.main AAPL --market US
python -m apps.cli.main 005930 --market KR
```

`.env` 필수 항목:
| 변수 | 설명 |
|------|------|
| `ANTHROPIC_API_KEY` | Claude API 키 |
| `DART_API_KEY` | 국내주식 DART OpenAPI (KR 필수) |
| `FMP_API_KEY` | Financial Modeling Prep (선택, yfinance 폴백) |

---

## 테스트 실행

```powershell
$env:PYTHONPATH = "<project_root>"

# 계산 함수 단위 테스트 (API 불필요, 항상 빠름)
python -m pytest tests/unit/ -v

# 통합 테스트
python -m pytest tests/integration/ -v

# 전체 (live 제외)
python -m pytest tests/ -m "not live" -v
```

---

## 아키텍처

```
apps/cli/main.py  (--mock → mock_pipeline, 기본 → analysis_pipeline)
       │
       ├── pipelines/mock_pipeline.py      ← MockProvider + CalculationEngine
       └── pipelines/analysis_pipeline.py ← DataGateway + Claude Agent
                   │
       services/
         data_gateway/
           providers/mock_provider.py     ← 가상 데이터 (API 불필요)
           providers/yfinance_provider.py ← 실시간 US 데이터
           providers/dart_provider.py     ← 실시간 KR 공시
         calculation_engine/
           valuation.py    ← PER, PBR, PSR, EV/EBITDA
           profitability.py← 영업이익률, 순이익률, ROE, ROA
           leverage.py     ← 부채비율, 이자보상배율
           liquidity.py    ← 유동비율, 당좌비율
           growth.py       ← YoY 성장률, CAGR
           engine.py       ← 위 모듈 통합
         report_service/
           renderer.py     ← Jinja2 → Markdown / HTML
```

**핵심 불변 원칙**:
- Claude는 사전 계산된 값만 받는다. 수치를 직접 추정하거나 계산하지 않는다.
- 모든 데이터 객체는 `provenance(source, as_of_date, fetched_at)`를 포함한다.
- `free_cash_flow = OCF - abs(capex)` 로 항상 직접 계산한다.

---

## 면책 고지

이 도구는 투자 정보 제공 목적이며, 투자 권유가 아닙니다.
모든 투자에는 원금 손실 위험이 있습니다.
