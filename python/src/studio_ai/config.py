import tempfile
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Settings below reads .env itself via pydantic-settings, but third-party
# SDKs (e.g. fal_client) read credentials straight from os.environ, which
# pydantic-settings never touches — load .env into the real process
# environment too. No-ops harmlessly if a file doesn't exist (e.g. Vercel,
# where real env vars are already injected by the platform).
load_dotenv(".env")
load_dotenv("../.env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    fal_key: str = Field(default="", alias="FAL_KEY")
    bot_token: str = Field(default="", alias="BOT_TOKEN")
    port: int = Field(default=3000, alias="PORT")
    bot_lock_path: str = Field(
        default=str(Path(tempfile.gettempdir()) / "studio-ai-telegram.lock"),
        alias="BOT_LOCK_PATH",
    )
    allowed_telegram_user_id: int | None = Field(
        default=None, alias="ALLOWED_TELEGRAM_USER_ID"
    )
    egress_budget_path: str = Field(
        default=str(
            Path(__file__).resolve().parents[3] / "data" / "egress_budget.json"
        ),
        alias="EGRESS_BUDGET_PATH",
    )

    @field_validator("allowed_telegram_user_id", mode="before")
    @classmethod
    def _blank_means_unset(cls, value: object) -> object:
        return None if value == "" else value


@lru_cache
def get_settings() -> Settings:
    return Settings()
