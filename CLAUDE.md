# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment Setup

**Important — Windows Korean-path workaround**: `pip install -e .` creates a `.pth` file in
site-packages that contains the project path. Because this project lives under a Korean-character
directory, Python's `cp949` codec cannot read it back, crashing the site module. Do NOT run
`pip install -e .` for this project.

Instead, install dependencies only and use `PYTHONPATH`:

```powershell
# Install all dependencies (do NOT pass the project path to -e)
pip install anthropic pydantic pydantic-settings python-dotenv yfinance httpx finance-datareader pykrx requests pandas numpy ta jinja2 markdown typer rich fastapi "uvicorn[standard]"
pip install pytest pytest-asyncio pytest-cov respx responses mypy ruff

# Set PYTHONPATH before any python/pytest command
$env:PYTHONPATH = "C:\Users\elcax\OneDrive\바탕 화면\최용원\자격증 및 증명\개인 포트폴리오\26년\stock-analysis-agent\stock-analysis-agent"
Set-Location $env:PYTHONPATH
```

**NumPy version note**: The Anaconda base environment has NumPy 2.5 but older pandas/yfinance
compiled against NumPy 1.x. If pandas ImportError appears, run:
```powershell
pip install "numpy<2" --upgrade
```

## Running Tests

```powershell
# From the project root with PYTHONPATH set (see above):

# Unit tests only (no I/O, always fast)
python -m pytest tests/unit/ -v

# Cache integration test
python -m pytest tests/integration/test_cache.py -v

# All non-live tests (requires pandas/yfinance to be importable)
python -m pytest tests/ -m "not live" -v

# Single test file
python -m pytest tests/unit/test_valuation.py -v
```

## Running the CLI

```powershell
# Copy and fill .env.example → .env first
python -m apps.cli.main AAPL --market US
python -m apps.cli.main 005930 --market KR
```

## Architecture

```
Entry:  apps/cli/main.py (Typer)  |  apps/api/main.py (FastAPI)
            └── pipelines/analysis_pipeline.py
                    └── services/report_service/agent.py
                            (Anthropic SDK tool_use loop)
                        └── services/report_service/tools.py (ToolExecutor)
                            ├── services/data_gateway/registry.py  (DataGateway)
                            │     providers: yfinance, fmp, fdr, pykrx, dart
                            └── services/calculation_engine/engine.py (CalculationEngine)
                                  modules: valuation, profitability, liquidity,
                                           leverage, growth, efficiency, dupont, technical
```

**Critical invariant**: Claude receives only pre-computed values from `ToolExecutor.execute()`.
It never estimates or calculates financial figures itself.

Every data object carries `provenance: DataProvenance(source, as_of_date, fetched_at)`.

`free_cash_flow` is always computed as `OCF - abs(capex)` in `CashFlowStatement` — never
sourced directly, since provider definitions diverge.

## Key Files

| File | Purpose |
|---|---|
| `services/data_gateway/models.py` | All Pydantic data models with provenance |
| `services/data_gateway/registry.py` | Routes requests to providers; handles caching |
| `services/calculation_engine/engine.py` | Aggregates all ratio calculators |
| `services/report_service/agent.py` | Anthropic tool_use loop |
| `services/report_service/tools.py` | Tool definitions + ToolExecutor dispatch |
| `services/report_service/prompts.py` | System prompt (enforces no LLM calculations) |
| `config/settings.py` | pydantic-settings; reads `.env` |

## Environment Variables (`.env`)

| Variable | Required | Default | Notes |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | — | |
| `CLAUDE_MODEL` | No | `claude-sonnet-4-6` | |
| `DART_API_KEY` | For KR stocks | — | DART OpenAPI |
| `FMP_API_KEY` | No | — | yfinance used as fallback |
| `ALPHA_VANTAGE_API_KEY` | No | — | |
| `CACHE_TTL_SECONDS` | No | `3600` | |
| `REPORT_FORMAT` | No | `markdown` | `markdown` or `html` |

## Agent Behavior Principles

### Analysis Rules

- **Role**: 주식 투자 리서치 보조자다. 투자 판단을 대신하지 않는다.
- **No directional calls**: 특정 종목에 대해 "사라", "팔아라", "무조건 오른다"라고 단정하지 않는다.
- **Risk disclosure**: 모든 분석에 손실 가능성과 리스크를 포함한다.
- **No unverified sources**: 출처가 없는 루머는 분석에 사용하지 않는다.
- **Date attribution**: 최신 주가, 실적, 뉴스, 금리, 환율, 공시는 반드시 기준일을 표시한다.
- **Calculation source**: 재무 수치와 밸류에이션 계산은 `CalculationEngine.calculate_all()`
  (`services/calculation_engine/engine.py`) 결과만 사용한다. LLM이 직접 수치를 추정하거나 계산하는 것은 엄격히 금지한다.

### Required Report Sections

최종 리포트에는 아래 12개 섹션을 항상 포함한다:

| 섹션 | 내용 |
|---|---|
| A. 한 줄 요약 | 종목의 핵심을 한 문장으로 |
| B. 기업 개요와 핵심 사업 | 사업 모델, 주요 제품/서비스, 시장 위치 |
| C. 투자 포인트 | 이 종목을 주목하는 이유 |
| D. 실적 흐름 | 매출·이익 추세, 최근 분기 하이라이트 |
| E. 재무 안정성 | 유동성·레버리지·현금흐름 |
| F. 밸류에이션 | P/E, P/B, EV/EBITDA 등 멀티플 분석 |
| G. 산업 및 경쟁 구도 | 시장 구조, 주요 경쟁사, 시장점유율 |
| H. 성장 동력 | 향후 매출·이익 성장을 이끌 요인 |
| I. 주요 리스크 | 하락 시나리오를 유발할 수 있는 위험 요인 |
| J. 상승/중립/하락 시나리오 | 세 가지 경우의 수와 각 트리거 |
| K. 추가 확인 질문 | 판단 전 추가로 확인해야 할 사항 |
| L. 보수적 관점의 최종 의견 | 리스크를 강조한 균형 잡힌 종합 의견 |

## Extension Points

- **ML price prediction**: implement `services/model_service/base.BaseModelService`; the stub returns `is_available()=False` which suppresses the `predict_price` tool from Claude
- **Backtesting**: implement `services/backtest_engine/base.BaseBacktestEngine`; same gating pattern
- **New data provider**: implement `services/data_gateway/base.BaseDataProvider`, add one line to `DataGateway._register_providers()`
