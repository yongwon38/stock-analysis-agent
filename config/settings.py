from pathlib import Path
from typing import Literal, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Anthropic
    anthropic_api_key: str
    claude_model: str = "claude-sonnet-4-6"
    max_tokens_per_response: int = 8096

    # US market data (yfinance used as fallback when absent)
    fmp_api_key: Optional[str] = None
    alpha_vantage_api_key: Optional[str] = None

    # Korean market data
    dart_api_key: Optional[str] = None

    # Caching
    cache_dir: Path = Path("data/raw")
    cache_ttl_seconds: int = 3600

    # Report output
    report_output_dir: Path = Path("data/reports")
    report_format: Literal["markdown", "html"] = "markdown"

    # Logging
    log_level: str = "INFO"
