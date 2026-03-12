from abc import ABC

from typing_extensions import Self, Any
from pydantic import BaseModel, ValidationError

from openai import AzureOpenAI

import os

class LLMResponse(BaseModel):
    scores: dict[str, float]
    reasoning: str

class BaseProvider(ABC):
    pass

class AzureOpenAIProviderClass(BaseProvider):
    def __init__(self, api_version: str, azure_endpoint: str, api_key: str) -> Self:
        self.client = AzureOpenAI(
            api_version=api_version,
            azure_endpoint=azure_endpoint,
            api_key=api_key
        )

    def get_response(self, prompt: str) -> LLMResponse:
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
    user_prompt: str
    rubric: list[str]  # Rubric = evaluation criteria

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

    JUDGE_PROMPT = """
        You will be given:
        - a user_question
        - a system_answer
        - a user_criteria
        
        Your task is to provide individual ratings for each of the user_criteria scoring how well the system_answer answers the user concerns expressed in the user_question.
        Give your ratings on a scale of 1 to 4, where 1 means that the system_answer does not live up to the criteria at all, and 4 means that the system_answer fulfills that user_criteria completely and perfectly.
        
        For each criterion, assign a score from 1 to 4, where:
        Here is the scale you should use to build your answer:
        1: The system_answer is terrible: completely irrelevant to the criterion specified, or very partial
        2: The system_answer is mostly not helpful: misses some key aspects of the criterion
        3: The system_answer is mostly helpful: fulfills the criterion, but still could be improved
        4: The system_answer is excellent: relevant, direct, detailed, and addresses all the concerns raised in the criterion
        
        You should:
        - carefully read the question and answer
        - evaluate the answer ONLY based on the provided criterion
        - give one overall reasoning paragraph covering the main strengths and weaknesses of the answer
        - then provide a score for each criterion individually
        
        Output format:
        
        Feedback:::
        Reasoning: (one concise but complete explanation covering the overall evaluation)
        Scores:
        - <criterion_1>: <score from 0 to 1>
        - <criterion_2>: <score from 0 to 1>
        - <criterion_3>: <score from 0 to 1>
        
        Important requirements:
        - You must provide exactly one Reasoning section
        - You must provide one score for every criterion in the list
        - Do not add extra criteria
        - Do not omit any criterion
        - Scores must be numeric values between 0 and 1
        
        Now here are the inputs.
        
        Question: {question}
        Answer: {answer}
        Criteria: {criteria}
        
        Provide your evaluation.
        
        Feedback:::
        Reasoning:"""