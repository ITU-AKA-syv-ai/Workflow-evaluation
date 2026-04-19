from typing import Any

from pydantic import BaseModel, Field, ValidationError

from app.core.evaluators.base import BaseEvaluator
from app.core.models.evaluation_model import EvaluationResult
from app.core.providers.base import BaseProvider, LLMResponse


class LLMJudgeConfig(BaseModel):
    """
    The configuration object for the LLMJudge.

    Attributes:
        prompt (str): The user's original question, the answer to which needs to be evaluated.
        rubric (list[str]): The rubric with a list fo criteria that needs to be evaluated.

    """

    prompt: str
    rubric: list[str] = Field(min_length=1)


class LLMJudgeEvaluator(BaseEvaluator):
    """
    LLM as a judge takes a model_output and a config.
    The config contains the user's original question as well as a list of criteria,
    defined in a 'rubric', that the LLM judge bases its evaluation upon.

    It returns a normalised and aggregated score for each criterion in the rubric,
    as well as reasonings for each individual criterion in the rubric.
    """

    def __init__(self, provider: BaseProvider, threshold: float) -> None:
        super().__init__(threshold)
        self.provider = provider

    @property
    def name(self) -> str:
        return "llm_judge"

    @property
    def description(self) -> str:
        return "Uses an LLM to judge the output of another LLM based on user defined criteria."

    @property
    def config_schema(self) -> dict[str, Any]:
        return LLMJudgeConfig.model_json_schema()

    def validate_config(self, config: dict[str, Any]) -> LLMJudgeConfig | None:
        """
        Converts a configuration consisting of the user prompt and a list of rubrics to an instance of LLMJudgeConfig.

        Args:
            config (dict[str, Any]): The config to bind to a LLMJudgeConfig.

        Returns:
            LLMJudgeConfig | None: Returns LLMJudgeConfig if config is correctly formatted, otherwise None is returned.
        """

        try:
            bound = LLMJudgeConfig.model_validate(config)
        except ValidationError:
            return None

        return bound

    async def _evaluate(self, output: str, config: LLMJudgeConfig) -> EvaluationResult:
        """
        Uses an LLM to judge the output of another LLM based on user defined criteria in a rubric, by constructing a prompt based on the aforementioned rubric.

        Args:
                output (str): The AI output to be evaluated.
            config (LengthEvaluatorConfig): The config which specifies the criteria the judge should use, collectively called the rubric, as well as the original user prompt.

        Returns:
                EvaluationResult: Result which contains the evaluator_id, normalised score, and a reasoning. The reasoning field contains the scores and reasoning of each individual criterion in the rubric.
        """

        try:
            response = await self.provider.generate_response(
                model_output=output, prompt=config.prompt, rubric=config.rubric
            )
            return EvaluationResult(
                evaluator_id="llm_judge",
                reasoning=response,
                normalised_score=_normalise_and_aggregate(response),
            )
        except Exception as e:
            return EvaluationResult(
                evaluator_id="llm_judge",
                reasoning=str(e),
                error=str(e),
            )


def _normalise_and_aggregate(response: LLMResponse) -> float:
    """
    Normalises and aggregates the score of each criterion in the rubric. The scale is converted from 1-4 to 0-1.

    Args:
        response: (LLMResponse): The response from the LLM judge, containing the rubric scores.

    Returns:
        float: The normalised and aggregated score for each criterion in the rubric.
    """
    normalised_scores = []
    for res in response.results:
        normalised = (res.score - 1) / 3
        normalised_scores.append(normalised)

    if len(normalised_scores) == 0:
        return 0

    return sum(normalised_scores) / len(normalised_scores)
