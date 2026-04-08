from functools import lru_cache

from pydantic import BaseModel, PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DBConfig(BaseModel):
    """
    The config for database connection.
    Attributes:
        driver (str): The driver of the database connection. E.g. postgresql+psycopg2
        database (str): The database name.
        host (str): The host of the database.
        port (int): The port of the database. Defaults to 5432.
        username (str): The username of the database.
        password (str): The password to the database.
    """

    driver: str
    host: str
    port: int = 5432  # Default port
    database: str
    username: str
    password: SecretStr

    def sqlalchemy_database_uri(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme=self.driver,
            username=self.username,
            password=self.password.get_secret_value(),
            host=self.host,
            port=self.port,
            path=self.database,
        )


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
    db: DBConfig


@lru_cache
def get_settings() -> Settings:
    """
    Get method to retrieve settings where needed.

    Returns:
        Settings: Settings object containing environment variables.
    """

    return Settings()  # ty:ignore[missing-argument]
