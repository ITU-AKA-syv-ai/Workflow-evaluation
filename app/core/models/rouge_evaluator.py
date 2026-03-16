from enum import Enum
from typing import Any

from pydantic import BaseModel, ValidationError

from app.core.models.base import BaseEvaluator
from app.core.models.evaluation_model import EvaluationResult


class TextClean(Enum):
    NONE = 1
    LOWERCASE = 2
    REMOVE_SYMBOLS = 3
    LOWERCASE_AND_REMOVE_SYMBOLS = 4


class RougeEvaluatorConfig(BaseModel):
    reference: str
    n_grams: int | None = 1


class RougeEvaluator(BaseEvaluator):
    @property
    def name(self) -> str:
        return "rouge_evaluator"

    @property
    def description(self) -> str:
        return "Computes the ROUGE metric"

    @property
    def config_schema(self) -> dict[str, Any]:
        return RougeEvaluatorConfig.model_json_schema()

    def bind(self, config: dict[str, Any]) -> RougeEvaluatorConfig | None:
        """
        Args:
            config (dict[str, Any]): The config to bind to a RougeEvaluatorConfig

        Returns:
            RougeEvaluatorConfig | None: Returns RougeEvaluatorConfig if config is correctly formattered, otherwise None is returned

        """
        try:
            bound_config = RougeEvaluatorConfig.model_validate(config)
            if bound_config.n_grams is not None and bound_config.n_grams <= 0:
                return None
            return bound_config
        except ValidationError:
            return None

    @property
    def default_threshold(self) -> float:
        return 0.5

    def _evaluate(self, output: str, config: RougeEvaluatorConfig) -> EvaluationResult:
        score = RougeScore(precision=0, recall=0, f1_score=0)
        if config.n_grams is not None:
            score = rouge_n(output, config.reference, config.n_grams)

        return EvaluationResult(
            evaluator_id=self.name,
            reasoning="0",
            normalised_score=score.f1_score,
        )


# ROUGE
class RougeScore(BaseModel):
    precision: float
    recall: float
    f1_score: float


class NGrams:
    # Maps NGram to number of occurences
    ngrams: dict[tuple[str, ...], int]
    n: int

    def __init__(self) -> None:
        self.ngrams = {}
        self.n = 0

    def __len__(self) -> int:
        return self.n

    def contains(self, v: tuple[str, ...]) -> bool:
        return v in self.ngrams

    def multiples_of(self, v: tuple[str, ...]) -> int:
        if v in self.ngrams:
            return self.ngrams[v]
        return 0

    def add(self, ngram: tuple[str, ...]) -> None:
        self.n += 1
        if ngram in self.ngrams:
            self.ngrams[ngram] += 1
        else:
            self.ngrams[ngram] = 1

    def size_of_intersection(self, other: "NGrams") -> int:
        sum = 0
        for k in self.ngrams:
            if k not in other.ngrams:
                continue
            sum += min(self.ngrams[k], other.ngrams[k])
        return sum


def find_n_grams(text: str, n: int) -> NGrams:
    unigrams = text.split()
    number_of_ngrams = len(unigrams) - n + 1
    ngrams = NGrams()

    for i in range(number_of_ngrams):
        ngrams.add(tuple(unigrams[i : i + n]))

    return ngrams


def rouge_n(model_output: str, reference: str, n_gram: int) -> RougeScore:
    output_n_grams = find_n_grams(model_output, n_gram)
    reference_n_grams = find_n_grams(reference, n_gram)

    intersection = output_n_grams.size_of_intersection(reference_n_grams)

    precision = intersection / len(output_n_grams)
    recall = intersection / len(reference_n_grams)
    score = 2 * (precision * recall) / (precision + recall)

    return RougeScore(precision=precision, recall=recall, f1_score=score)


def longest_common_subsequence(unigrams_model: list[str], unigrams_reference: list[str]) -> int:
    rows = len(unigrams_model)
    cols = len(unigrams_reference)
    memo = [[-1 for _ in range(cols + 1)] for _ in range(rows + 1)]

    def helper(i: int, j: int) -> int:
        if i == 0 or j == 0:
            return 0
        if memo[i][j] != -1:
            return memo[i][j]
        if unigrams_model[i - 1] == unigrams_reference[j - 1]:
            memo[i][j] = 1 + helper(i - 1, j - 1)
            return memo[i][j]
        memo[i][j] = max(helper(i, j - 1), (helper(i - 1, j)))
        return memo[i][j]

    return helper(rows, cols)


def rouge_l(model_output: str, reference: str) -> RougeScore:
    unigrams_model = model_output.split()
    unigrams_reference = reference.split()

    lcs = longest_common_subsequence(unigrams_model, unigrams_reference)

    precision = lcs / len(unigrams_model)
    recall = lcs / len(unigrams_reference)

    score = 2 * (precision * recall) / (precision + recall)
    return RougeScore(precision=precision, recall=recall, f1_score=score)
