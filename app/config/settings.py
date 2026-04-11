from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field, PostgresDsn, SecretStr
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

    @property
    def sqlalchemy_database_uri(self) -> str:
        """
        Construct the sqlalchemy database URI to be used by SQLAlchemy to establish a connection to the database.

        Returns:
        str: The sqlalchemy database URI.
        """
        return str(
            PostgresDsn.build(
                scheme=self.driver,
                username=self.username,
                password=self.password.get_secret_value(),
                host=self.host,
                port=self.port,
                path=self.database,
            )
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


class EmbeddingConfig(BaseModel):
    api_key: SecretStr
    api_endpoint: str
    model: str
    api_version: str


class SimilarityConfig(BaseModel):
    max_length: int


class ThresholdConfig(BaseModel):
    rouge: float = Field(0.5, ge=0.0, le=1.0)
    cosine: float = Field(0.7, ge=0.0, le=1.0)
    llm_judge: float = Field(1.0, ge=0.0, le=1.0)
    rule_based: float = Field(1.0, ge=0.0, le=1.0)


class LogLevelConfig(BaseModel):
    level: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="./../../.env",
        env_file_encoding="utf-8",
        env_nested_delimiter="_",
        env_nested_max_split=1,
    )

    environment: Literal["dev", "staging", "production"] = "dev"
    llm: LLMConfig
    db: DBConfig
    embedding: EmbeddingConfig
    similarity: SimilarityConfig
    threshold: ThresholdConfig = ThresholdConfig()
    log: LogLevelConfig


@lru_cache
def get_settings() -> Settings:
    """
    Get method to retrieve settings where needed. The function call is cached.

    Returns:
        Settings: Settings object containing environment variables.
    """

    return Settings()  # ty:ignore[missing-argument]
