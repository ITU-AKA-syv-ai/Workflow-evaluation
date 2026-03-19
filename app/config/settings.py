from functools import lru_cache

from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMConfig(BaseModel):
    """
    The config for LLM judge evaluator.

    Attributes:
        provider (str): The provider of LLM judge evaluator. E.g. Azure.
        api_key (SecretStr): The api key for the given provider.
        api_endpoint (str): The endpoint of the given provider.
        model (str): The model of the given provider.
        api_version (str): The api_version of the given provider.
    """

    provider: str
    api_key: SecretStr
    api_endpoint: str
    model: str
    api_version: str


class Settings(BaseSettings):
    """
    Responsible for reading environment variables and packaging them, to be passed to evaluators.
    This removes the need for reading directly from env variables every time they're needed.

    Some config fields needed for LLM judge need to be read from env variables.
    These are marked with the prefix "LLM_..." in the .env files.

    This class maps the LLM env variables to the specified provider.

    Attributes:
        model_config (SettingsConfigDict): Configuration object for where and how pydantic reads the config file. Needed to enable prefix split functionality.
        llm (LLMConfig): Configuration for the specified provider used for LLM judge.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="_",
        env_nested_max_split=1,
    )

    llm: LLMConfig


@lru_cache
def get_settings() -> Settings:
    """
    Get method to retrieve settings where needed.

    Returns:
        Settings: Settings object containing environment variables.
    """
    # Please note, we have to ignore the ty warning, since this will be populated at run time
    # but `ty` won't stop complaining since it doesn't know this

    return Settings()  # ty:ignore[missing-argument]
