from functools import lru_cache

from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMConfig(BaseModel):
    provider: str = "azure"
    api_key: SecretStr
    api_endpoint: str
    model: str
    api_version: str = "2025-03-01-preview"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../../.env",
        env_file_encoding="utf-8",
        env_nested_delimiter="_",
        env_nested_max_split=1,
    )

    llm: LLMConfig


@lru_cache
def get_settings() -> Settings:
    # Please note, we have to ignore the ty warning, since this will be populated at run time
    # but `ty` won't stop complaining since it doesn't know this

    return Settings()  # ty:ignore[missing-argument]