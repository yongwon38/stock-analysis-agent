import sys
from typing import Annotated

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

app = typer.Typer(help="Stock analysis agent — generates structured equity research reports.")
console = Console()


def _write(text: str) -> None:
    """Write UTF-8 text to stdout without Rich or Windows console API."""
    sys.stdout.buffer.write(text.encode("utf-8"))
    sys.stdout.buffer.flush()


@app.command()
def analyze(
    ticker: Annotated[str, typer.Argument(help="Stock ticker (e.g. 005930, AAPL)")],
    market: Annotated[str, typer.Option("--market", "-m", help="KR or US")] = "US",
    no_save: Annotated[bool, typer.Option("--no-save", help="Print report without saving")] = False,
    mock: Annotated[bool, typer.Option("--mock", help="Use mock data -- no API keys required")] = False,
) -> None:
    market = market.upper()
    if market not in ("KR", "US"):
        _write("[ERROR] --market must be KR or US\n")
        raise typer.Exit(1)

    if mock:
        from pipelines.mock_pipeline import run_mock_analysis
        _write(f"Analyzing {ticker} ({market}) with mock data...\n")
        report = run_mock_analysis(ticker, market)  # type: ignore[arg-type]
        from services.report_service.renderer import render
        _write(render(report, "markdown") + "\n")
        for w in report.warnings:
            _write(f"[Warning] {w}\n")
    else:
        from config.settings import Settings
        from pipelines.analysis_pipeline import run_analysis
        try:
            settings = Settings()  # type: ignore[call-arg]
        except Exception as exc:
            console.print(f"[red]Configuration error: {exc}[/red]")
            console.print("Copy .env.example to .env and fill in your API keys, or use --mock.")
            raise typer.Exit(1)
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            task = progress.add_task(f"Analyzing {ticker} ({market})...", total=None)
            report = run_analysis(ticker, market, settings, save_report=not no_save)  # type: ignore[arg-type]
            progress.update(task, description="Done!")
        if no_save:
            from services.report_service.renderer import render
            _write(render(report, settings.report_format) + "\n")
        else:
            console.print(f"[green]Report saved:[/green] {settings.report_output_dir}/{ticker}_*.{settings.report_format[:2]}")
        for w in report.warnings:
            console.print(f"[yellow]Warning:[/yellow] {w}")


if __name__ == "__main__":
    app()
