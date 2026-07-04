import argparse
import os
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from services.data_gateway.market_data_lake.daily_market_schemas import MarketDataIngestionRun


KST = ZoneInfo("Asia/Seoul")

DAILY_WIDE_TASKS: tuple[tuple[str, str], ...] = (
    ("kr_stocks", "yfinance"),
    ("us_stocks", "yfinance"),
    ("indexes", "yfinance"),
    ("fx", "yfinance"),
    ("commodities", "yfinance"),
    ("rates", "yfinance"),
    ("risk", "yfinance"),
    ("kr_stocks", "pykrx"),
)


@dataclass(frozen=True)
class DailyWideMarketDataResult:
    start_date: date
    end_date: date
    runs: list[MarketDataIngestionRun]
    failures: list[str]

    @property
    def status(self) -> str:
        if self.failures:
            return "partial_success" if any(run.point_count for run in self.runs) else "failed"
        return "success"

    @property
    def point_count(self) -> int:
        return sum(run.point_count for run in self.runs)

    @property
    def missing_count(self) -> int:
        return sum(run.missing_count for run in self.runs)


def calculate_daily_window(*, days: int = 7, run_date: date | None = None) -> tuple[date, date]:
    if days < 1:
        raise ValueError("--days must be >= 1")
    end_date = run_date or datetime.now(KST).date()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date


def run_daily_wide_market_data(
    *,
    days: int = 7,
    run_date: date | None = None,
    database_url: str | None = None,
    sqlite_path: str | Path = "data/local/market_data.sqlite",
    dry_run: bool = False,
    tasks: tuple[tuple[str, str], ...] = DAILY_WIDE_TASKS,
) -> DailyWideMarketDataResult:
    from pipelines.backfill_wide_market_data import backfill_wide_market_data, init_wide_market_db

    start_date, end_date = calculate_daily_window(days=days, run_date=run_date)
    runs: list[MarketDataIngestionRun] = []
    failures: list[str] = []

    if not dry_run:
        init_wide_market_db(database_url=database_url, sqlite_path=sqlite_path)

    for scope, provider in tasks:
        try:
            run = backfill_wide_market_data(
                start_date=start_date,
                end_date=end_date,
                scope=scope,
                provider_name=provider,
                database_url=database_url,
                sqlite_path=sqlite_path,
                dry_run=dry_run,
            )
            runs.append(run)
            if run.status == "failed":
                failures.append(f"{provider}:{scope}")
        except Exception as exc:
            failures.append(f"{provider}:{scope}: {exc}")

    return DailyWideMarketDataResult(
        start_date=start_date,
        end_date=end_date,
        runs=runs,
        failures=failures,
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run daily wide-format market data ingestion.")
    parser.add_argument("--days", default=7, type=int, help="Lookback days from the KST run date.")
    parser.add_argument(
        "--run-date",
        default=None,
        type=date.fromisoformat,
        help="KST run date, YYYY-MM-DD. Defaults to today in Asia/Seoul.",
    )
    parser.add_argument(
        "--database-url",
        default=os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL"),
        help="Postgres/Supabase URL. Defaults to SUPABASE_DB_URL.",
    )
    parser.add_argument(
        "--sqlite-path",
        default="data/local/market_data.sqlite",
        help="SQLite fallback path if no database URL is provided.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show planned runs without writing.")
    args = parser.parse_args(argv)

    result = run_daily_wide_market_data(
        days=args.days,
        run_date=args.run_date,
        database_url=args.database_url,
        sqlite_path=args.sqlite_path,
        dry_run=args.dry_run,
    )
    print(
        f"{result.status}: {result.start_date}..{result.end_date} "
        f"stored={result.point_count} missing={result.missing_count}"
    )
    for run in result.runs:
        print(
            f"{run.provider}\t{run.scope}\t{run.status}\t"
            f"points={run.point_count}\tmissing={run.missing_count}"
        )
    if result.failures:
        print("failures:")
        for failure in result.failures:
            print(f"- {failure}")
        sys.exit(1)


if __name__ == "__main__":
    main()
