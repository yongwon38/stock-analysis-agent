"""DART OpenAPI provider for Korean financial statements and filings.

API docs: https://opendart.fss.or.kr/guide/detail.do
"""
from datetime import date, datetime, timezone
from typing import Any, Literal, Optional

import requests

from services.data_gateway.base import BaseDataProvider
from services.data_gateway.models import (
    BalanceSheet,
    CashFlowStatement,
    CompanyProfile,
    DataProvenance,
    DARTFiling,
    IncomeStatement,
    StockPrice,
)

_DART_BASE = "https://opendart.fss.or.kr/api"


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _prov(as_of: date) -> DataProvenance:
    return DataProvenance(source="dart", as_of_date=as_of, fetched_at=_now())


def _safe_float(val: Any) -> Optional[float]:
    if val is None or val == "" or val == "-":
        return None
    try:
        return float(str(val).replace(",", ""))
    except (ValueError, TypeError):
        return None


class DARTProvider(BaseDataProvider):
    """Korean market: DART OpenAPI for financial statements and filings."""

    def __init__(self, api_key: str) -> None:
        self._key = api_key
        self._corp_cache: dict[str, str] = {}

    @property
    def source_name(self) -> str:
        return "dart"

    def _get(self, endpoint: str, params: dict) -> dict:
        params["crtfc_key"] = self._key
        resp = requests.get(f"{_DART_BASE}/{endpoint}", params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _resolve_corp_code(self, ticker: str) -> Optional[str]:
        if ticker in self._corp_cache:
            return self._corp_cache[ticker]
        data = self._get("company.json", {"stock_code": ticker})
        corp_code = data.get("corp_code")
        if corp_code:
            self._corp_cache[ticker] = corp_code
        return corp_code

    def get_company_profile(self, ticker: str, market: Literal["KR", "US"]) -> CompanyProfile:
        today = date.today()
        data = self._get("company.json", {"stock_code": ticker})
        corp_code = data.get("corp_code")
        if corp_code:
            self._corp_cache[ticker] = corp_code
        return CompanyProfile(
            ticker=ticker,
            market="KR",
            name=data.get("corp_name", ticker),
            name_en=data.get("corp_name_eng"),
            exchange="KRX",
            currency="KRW",
            dart_corp_code=corp_code,
            provenance=_prov(today),
        )

    def get_price_history(
        self,
        ticker: str,
        market: Literal["KR", "US"],
        start_date: date,
        end_date: date,
    ) -> list[StockPrice]:
        raise NotImplementedError("DARTProvider does not provide price history; use FDRProvider or pykrx")

    def _fetch_financial_statements(
        self, ticker: str, year: int, quarter: int, fs_div: str = "OFS"
    ) -> list[dict]:
        corp_code = self._resolve_corp_code(ticker)
        if not corp_code:
            return []
        rept_code = {1: "11013", 2: "11012", 3: "11014", 4: "11011"}.get(quarter, "11011")
        data = self._get(
            "fnlttSinglAcntAll.json",
            {
                "corp_code": corp_code,
                "bsns_year": str(year),
                "reprt_code": rept_code,
                "fs_div": fs_div,
            },
        )
        return data.get("list", [])

    def _get_account(self, rows: list[dict], *labels: str) -> Optional[float]:
        for row in rows:
            if row.get("account_nm") in labels:
                return _safe_float(row.get("thstrm_amount"))
        return None

    def get_income_statements(
        self,
        ticker: str,
        market: Literal["KR", "US"],
        period_type: Literal["annual", "quarterly"] = "annual",
        limit: int = 5,
    ) -> list[IncomeStatement]:
        results: list[IncomeStatement] = []
        current_year = date.today().year
        for yr in range(current_year - 1, current_year - limit - 1, -1):
            quarter = 4
            try:
                rows = self._fetch_financial_statements(ticker, yr, quarter)
                if not rows:
                    continue
                rev = self._get_account(rows, "매출액", "수익(매출액)")
                if rev is None:
                    continue
                cogs = self._get_account(rows, "매출원가") or 0.0
                gross = rev - cogs
                op_inc = self._get_account(rows, "영업이익") or 0.0
                net_inc = self._get_account(rows, "당기순이익") or 0.0
                int_exp = self._get_account(rows, "이자비용")
                ebitda = self._get_account(rows, "EBITDA")
                period_end = date(yr, 12, 31)
                results.append(
                    IncomeStatement(
                        ticker=ticker,
                        fiscal_year=yr,
                        period_type="annual",
                        period_end_date=period_end,
                        revenue=rev,
                        cost_of_revenue=cogs,
                        gross_profit=gross,
                        operating_income=op_inc,
                        ebitda=ebitda,
                        interest_expense=int_exp,
                        pretax_income=self._get_account(rows, "법인세비용차감전순이익") or net_inc,
                        income_tax=self._get_account(rows, "법인세비용"),
                        net_income=net_inc,
                        shares_basic=1.0,
                        provenance=_prov(period_end),
                    )
                )
            except Exception:
                continue
        return sorted(results, key=lambda x: x.period_end_date)

    def get_balance_sheets(
        self,
        ticker: str,
        market: Literal["KR", "US"],
        period_type: Literal["annual", "quarterly"] = "annual",
        limit: int = 5,
    ) -> list[BalanceSheet]:
        results: list[BalanceSheet] = []
        current_year = date.today().year
        for yr in range(current_year - 1, current_year - limit - 1, -1):
            try:
                rows = self._fetch_financial_statements(ticker, yr, 4)
                if not rows:
                    continue
                total_assets = self._get_account(rows, "자산총계")
                if total_assets is None:
                    continue
                period_end = date(yr, 12, 31)
                results.append(
                    BalanceSheet(
                        ticker=ticker,
                        period_end_date=period_end,
                        period_type="annual",
                        total_assets=total_assets,
                        current_assets=self._get_account(rows, "유동자산") or 0.0,
                        cash_and_equivalents=self._get_account(rows, "현금및현금성자산") or 0.0,
                        accounts_receivable=self._get_account(rows, "매출채권"),
                        inventory=self._get_account(rows, "재고자산"),
                        total_liabilities=self._get_account(rows, "부채총계") or 0.0,
                        current_liabilities=self._get_account(rows, "유동부채") or 0.0,
                        short_term_debt=self._get_account(rows, "단기차입금"),
                        accounts_payable=self._get_account(rows, "매입채무"),
                        long_term_debt=self._get_account(rows, "장기차입금"),
                        total_equity=self._get_account(rows, "자본총계") or 0.0,
                        retained_earnings=self._get_account(rows, "이익잉여금"),
                        provenance=_prov(period_end),
                    )
                )
            except Exception:
                continue
        return sorted(results, key=lambda x: x.period_end_date)

    def get_cash_flow_statements(
        self,
        ticker: str,
        market: Literal["KR", "US"],
        period_type: Literal["annual", "quarterly"] = "annual",
        limit: int = 5,
    ) -> list[CashFlowStatement]:
        results: list[CashFlowStatement] = []
        current_year = date.today().year
        for yr in range(current_year - 1, current_year - limit - 1, -1):
            try:
                rows = self._fetch_financial_statements(ticker, yr, 4)
                if not rows:
                    continue
                ocf = self._get_account(rows, "영업활동현금흐름")
                if ocf is None:
                    continue
                capex = self._get_account(rows, "유형자산의취득") or 0.0
                period_end = date(yr, 12, 31)
                results.append(
                    CashFlowStatement(
                        ticker=ticker,
                        fiscal_year=yr,
                        period_type="annual",
                        period_end_date=period_end,
                        operating_cash_flow=ocf,
                        capex=capex,
                        investing_cash_flow=self._get_account(rows, "투자활동현금흐름") or 0.0,
                        financing_cash_flow=self._get_account(rows, "재무활동현금흐름") or 0.0,
                        dividends_paid=self._get_account(rows, "배당금의지급"),
                        provenance=_prov(period_end),
                    )
                )
            except Exception:
                continue
        return sorted(results, key=lambda x: x.period_end_date)

    def get_dart_filings(self, ticker: str, limit: int = 10) -> list[DARTFiling]:
        corp_code = self._resolve_corp_code(ticker)
        if not corp_code:
            return []
        today = date.today()
        data = self._get(
            "list.json",
            {
                "corp_code": corp_code,
                "bgn_de": "20200101",
                "end_de": today.strftime("%Y%m%d"),
                "pblntf_ty": "A",
                "page_count": str(limit),
            },
        )
        results: list[DARTFiling] = []
        for item in data.get("list", []):
            filed_str = item.get("rcept_dt", "")
            try:
                filed_at = date(int(filed_str[:4]), int(filed_str[4:6]), int(filed_str[6:8]))
            except (ValueError, IndexError):
                filed_at = today
            receipt_no = item.get("rcept_no", "")
            results.append(
                DARTFiling(
                    corp_code=corp_code,
                    ticker=ticker,
                    report_name=item.get("report_nm", ""),
                    receipt_no=receipt_no,
                    filed_at=filed_at,
                    url=f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={receipt_no}",
                    provenance=_prov(filed_at),
                )
            )
        return results
