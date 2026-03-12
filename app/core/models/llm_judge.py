from typing_extensions import Self
from pydantic import BaseModel, model_validator

from openai import OpenAI
import os

# todo: How to mock this object in testing?
PROVIDERS = {
    "openai": ["gpt-5-nano"]
}


class LLMAsAJudgeConfig(BaseModel):
    rubric: dict[str, str]  # Rubric = evaluation criteria

    provider: str
    model: str  # Contains both model and model version

    @model_validator(mode='after')
    def check_provider_and_model(self) -> Self:
        if not (self.provider in PROVIDERS and self.model in PROVIDERS[self.provider]):
            raise ValueError("Invalid model and provider, please select one of the following:" + PROVIDERS)

        return self
