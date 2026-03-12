from abc import ABC

from typing_extensions import Self, Any
from pydantic import BaseModel, ValidationError

from openai import AzureOpenAI

import os

class BaseProvider(ABC):
    pass

class AzureOpenAIProviderClass(BaseProvider):
    def __init__(self, api_version: str, azure_endpoint: str, api_key: str) -> Self:
        self.client = AzureOpenAI(
            api_version=api_version,
            azure_endpoint=azure_endpoint,
            api_key=api_key
        )

    def get_response(self, prompt: str) -> str:
        completion = self.client.chat.completions.create(
            model="gpt-5-nano-ITU-students",  # e.g. gpt-35-instant
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )
        return completion.to_json()["choices"]["message"]["content"]


AzureOpenAIclient = AzureOpenAIProviderClass(
    api_version=os.environ.get("AZURE_API_VERSION"),
    azure_endpoint=os.environ.get("AZURE_ENDPOINT"),
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
)

from app.core.models.base import BaseEvaluator


class LLMAsAJudgeConfig(BaseModel):
    rubric: dict[str, str]  # Rubric = evaluation criteria

    provider: str
    model: str  # Contains both model and model version

class LLMAsAJudge(BaseEvaluator):
    @property
    def name(self) -> str:
        return "llm_as_judge_evaluator"

    @property
    def description(self) -> str:
        return "Cool LLM judge"

    @property
    def config_schema(self) -> dict[str, Any]:
        return LLMAsAJudgeConfig.model_json_schema()

    def bind(self, config: dict[str, Any]) -> LLMAsAJudgeConfig | None:
        try:
            return LLMAsAJudgeConfig.model_validate(config)
        except ValidationError:
            return None

    def evaluate(self, output: str, config: LLMAsAJudgeConfig) -> bool:
        print(AzureOpenAIclient.get_response())
        return True
