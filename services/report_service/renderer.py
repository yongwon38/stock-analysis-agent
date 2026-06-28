from pathlib import Path
from typing import Literal

from jinja2 import Environment, FileSystemLoader

from services.report_service.models import AnalysisReport

_TEMPLATE_DIR = Path(__file__).parent / "templates"


def render(report: AnalysisReport, fmt: Literal["markdown", "html"] = "markdown") -> str:
    env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)), autoescape=False)
    template_name = f"report.{'md' if fmt == 'markdown' else 'html'}.j2"
    template = env.get_template(template_name)
    return template.render(report=report)


def save(report: AnalysisReport, output_dir: Path, fmt: Literal["markdown", "html"] = "markdown") -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    ext = "md" if fmt == "markdown" else "html"
    filename = f"{report.ticker}_{report.generated_at.strftime('%Y%m%d_%H%M%S')}.{ext}"
    path = output_dir / filename
    content = render(report, fmt)
    path.write_text(content, encoding="utf-8")
    return path
