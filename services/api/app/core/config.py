from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[4]
ROOT_ENV_FILE = ROOT_DIR / ".env"

class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "agentops-readiness-console"
    api_host: str = "localhost"
    api_port: int = 8000

    openai_api_key: str | None = None

    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None

    github_token: str | None = None
    github_owner: str | None = None
    github_repo: str | None = None

    enable_audit_logging: bool = True
    require_human_approval_for_writes: bool = True

    model_config = SettingsConfigDict(
        env_file=ROOT_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()