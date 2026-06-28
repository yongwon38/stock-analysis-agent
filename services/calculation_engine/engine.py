from datetime import datetime, timezone

from services.calculation_engine import (
    dupont,
    efficiency,
    growth,
    leverage,
    liquidity,
    profitability,
    valuation,
)
from services.calculation_engine.models import FinancialRatios
from services.data_gateway.models import (
    BalanceSheet,
    CashFlowStatement,
    CompanyProfile,
    DataProvenance,
    IncomeStatement,
)


class CalculationEngine:
    """Aggregates all calculators and produces a FinancialRatios snapshot."""

    def calculate_all(
        self,
        income_stmts: list[IncomeStatement],
        balance_sheets: list[BalanceSheet],
        cashflow_stmts: list[CashFlowStatement],
        profile: CompanyProfile,
        close_price: float,
    ) -> FinancialRatios:
        inc = sorted(income_stmts, key=lambda x: x.period_end_date)
        bal = sorted(balance_sheets, key=lambda x: x.period_end_date)
        cf = sorted(cashflow_stmts, key=lambda x: x.period_end_date)

        latest_inc = inc[-1] if inc else None
        latest_bal = bal[-1] if bal else None
        latest_cf = cf[-1] if cf else None
        prior_bal = bal[-2] if len(bal) >= 2 else None
        prior_inc = inc[-2] if len(inc) >= 2 else None
        prior_cf = cf[-2] if len(cf) >= 2 else None

        # --- Valuation ---
        mc = profile.market_cap
        shares = profile.shares_outstanding
        eps_ttm = latest_inc.eps_diluted if latest_inc else None
        rev = latest_inc.revenue if latest_inc else None
        ebitda_ttm = latest_inc.ebitda if latest_inc else None
        total_debt = latest_bal.total_debt if latest_bal else 0.0
        cash = latest_bal.cash_and_equivalents if latest_bal else 0.0
        equity = latest_bal.total_equity if latest_bal else None

        bvps = (equity / shares) if (equity and shares) else None
        rev_ps = (rev / shares) if (rev and shares) else None
        ev = valuation.enterprise_value(mc, total_debt, cash) if mc else None

        pe = valuation.pe_ratio(close_price, eps_ttm)
        pb = valuation.pb_ratio(close_price, bvps)
        ps = valuation.ps_ratio(close_price, rev_ps)
        ev_eb = valuation.ev_ebitda(ev, ebitda_ttm) if ev else None
        ev_rv = valuation.ev_revenue(ev, rev) if ev else None

        # PEG: use 3y EPS CAGR
        eps_vals = [s.eps_diluted for s in inc if s.eps_diluted is not None]
        eps_cagr = growth.compute_cagr(eps_vals, years=3) if len(eps_vals) >= 4 else None
        peg = valuation.peg_ratio(pe, eps_cagr)

        # --- Profitability ---
        gm = profitability.gross_margin(latest_inc.gross_profit, latest_inc.revenue) if latest_inc else None
        om = profitability.operating_margin(latest_inc.operating_income, latest_inc.revenue) if latest_inc else None
        nm = profitability.net_margin(latest_inc.net_income, latest_inc.revenue) if latest_inc else None
        ebm = profitability.ebitda_margin(latest_inc.ebitda, latest_inc.revenue) if latest_inc else None

        avg_eq = profitability.avg(prior_bal.total_equity if prior_bal else None, latest_bal.total_equity if latest_bal else None)
        avg_as = profitability.avg(prior_bal.total_assets if prior_bal else None, latest_bal.total_assets if latest_bal else None)
        roe_v = profitability.roe(latest_inc.net_income, avg_eq) if latest_inc else None
        roa_v = profitability.roa(latest_inc.net_income, avg_as) if latest_inc else None

        roic_v: float | None = None
        if latest_inc and latest_bal and latest_inc.income_tax is not None and latest_inc.pretax_income:
            tax_rate = latest_inc.income_tax / latest_inc.pretax_income if latest_inc.pretax_income else 0.21
            roic_v = profitability.roic(
                ebit=latest_inc.operating_income,
                tax_rate=max(0.0, min(tax_rate, 1.0)),
                total_debt=latest_bal.total_debt,
                total_equity=latest_bal.total_equity,
                cash=latest_bal.cash_and_equivalents,
            )

        # --- Liquidity ---
        cr = liquidity.current_ratio(latest_bal.current_assets, latest_bal.current_liabilities) if latest_bal else None
        qr = liquidity.quick_ratio(latest_bal.current_assets, latest_bal.inventory, latest_bal.current_liabilities) if latest_bal else None
        cashr = liquidity.cash_ratio(latest_bal.cash_and_equivalents, latest_bal.current_liabilities) if latest_bal else None

        # --- Leverage ---
        dte = leverage.debt_to_equity(total_debt, equity) if equity else None
        dta = leverage.debt_to_assets(total_debt, latest_bal.total_assets) if latest_bal else None
        ic = leverage.interest_coverage(latest_inc.operating_income, latest_inc.interest_expense) if latest_inc else None
        nd = leverage.net_debt(total_debt, cash)
        nd_eb = leverage.net_debt_to_ebitda(total_debt, cash, ebitda_ttm)

        # --- Growth ---
        rev_list = [s.revenue for s in inc]
        op_list = [s.operating_income for s in inc]
        ni_list = [s.net_income for s in inc]
        fcf_list = [s.free_cash_flow for s in cf]

        rev_yoy = growth.compute_yoy(rev_list)
        op_yoy = growth.compute_yoy(op_list)
        ni_yoy = growth.compute_yoy(ni_list)
        eps_yoy = growth.compute_yoy(eps_vals)
        fcf_yoy = growth.compute_yoy(fcf_list)

        rev_cagr = growth.compute_cagr(rev_list, years=3) if len(rev_list) >= 4 else None

        # --- Efficiency ---
        avg_inv = profitability.avg(
            prior_bal.inventory if prior_bal else None,
            latest_bal.inventory if latest_bal else None,
        )
        avg_ar = profitability.avg(
            prior_bal.accounts_receivable if prior_bal else None,
            latest_bal.accounts_receivable if latest_bal else None,
        )
        at = efficiency.asset_turnover(latest_inc.revenue, avg_as) if latest_inc else None
        invt = efficiency.inventory_turnover(latest_inc.cost_of_revenue, avg_inv) if latest_inc else None
        rect = efficiency.receivables_turnover(latest_inc.revenue, avg_ar) if latest_inc else None
        dso = efficiency.days_sales_outstanding(rect)
        dio = efficiency.days_inventory_outstanding(invt)

        # --- DuPont ---
        dp_em = dupont.equity_multiplier(latest_bal.total_assets, latest_bal.total_equity) if latest_bal else None
        dp = dupont.dupont_3factor(nm, at, dp_em)

        return FinancialRatios(
            ticker=profile.ticker,
            as_of_date=latest_inc.period_end_date if latest_inc else latest_bal.period_end_date if latest_bal else profile.provenance.as_of_date,
            pe_ratio=pe, pb_ratio=pb, ps_ratio=ps,
            ev_ebitda=ev_eb, ev_revenue=ev_rv, peg_ratio=peg,
            gross_margin=gm, operating_margin=om, net_margin=nm, ebitda_margin=ebm,
            roe=roe_v, roa=roa_v, roic=roic_v,
            current_ratio=cr, quick_ratio=qr, cash_ratio=cashr,
            debt_to_equity=dte, debt_to_assets=dta, interest_coverage=ic,
            net_debt_to_ebitda=nd_eb, net_debt=nd,
            revenue_growth_yoy=rev_yoy, operating_income_growth_yoy=op_yoy,
            net_income_growth_yoy=ni_yoy, eps_growth_yoy=eps_yoy, fcf_growth_yoy=fcf_yoy,
            revenue_cagr_3y=rev_cagr, eps_cagr_3y=eps_cagr,
            asset_turnover=at, inventory_turnover=invt, receivables_turnover=rect,
            days_sales_outstanding=dso, days_inventory_outstanding=dio,
            dupont_3factor=dp,
            provenance=DataProvenance(
                source="calculation_engine",
                as_of_date=profile.provenance.as_of_date,
                fetched_at=datetime.now(tz=timezone.utc),
            ),
        )
