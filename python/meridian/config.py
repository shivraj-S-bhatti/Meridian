from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    crawl_concurrency: int = int(os.getenv("CRAWL_CONCURRENCY", "4"))
    pipeline_version: str = os.getenv("MERIDIAN_PIPELINE_VERSION", "v0.1.0")


settings = Settings()
