from typing import Any

from pydantic import BaseModel, ValidationError

from app.core.models.base import BaseEvaluator
from app.core.models.evaluation_model import EvaluationResult


class SubstringEvaluatorConfig(BaseModel):
    """
    Configuration for the SubstringEvaluator.

    Defines the substring to look for in the output.

    Attributes:
        substring (str): The substring to look for in the output.
    """

    substring: str


class SubstringEvaluator(BaseEvaluator):
    @property
    def name(self) -> str:
        return "substring_evaluator"

    @property
    def description(self) -> str:
        return "Evaluates whether a string contains a specific substring"

    @property
    def config_schema(self) -> dict[str, Any]:
        return SubstringEvaluatorConfig.model_json_schema()

    def bind(self, config: dict[str, Any]) -> SubstringEvaluatorConfig | None:
        try:
            return SubstringEvaluatorConfig.model_validate(config)
        except ValidationError:
            return None

    def evaluate(
        self, output: str, config: SubstringEvaluatorConfig
    ) -> EvaluationResult:
        """
        Evaluates whether the output contains the substring specified in the config.

        Args:
            output (str): The full string to evaluate if it contains the substring.
            config (SubstringEvaluatorConfig): The configuration specifying the substring to look for.

        Returns:
            EvaluationResult: Passed if the output contains the substring, failed otherwise. The normalised score is based on the difference between the expected length and the actual length.
        """

        normalised_score = 0
        passed = False
        reasoning = ""
        # The empty string is a substring of all strings
        if len(config.substring) == 0:
            normalised_score = 1
            passed = True
            reasoning = "The empty string is a substring of all strings."
        else:
            almost_substring = find_almost_substring(config.substring, output)
            passed = len(almost_substring) == len(config.substring)
            normalised_score = len(almost_substring) / len(config.substring)

            if passed:
                reasoning = f'Substring "{config.substring}" is present.'
            elif len(almost_substring) > 0:
                reasoning = f'Only found partial match "{almost_substring}".'
            else:
                reasoning = f'No occurences of "{config.substring}" found.'

        return EvaluationResult(
            evaluator_id=self.name,
            passed=passed,
            reasoning=reasoning,
            normalised_score=normalised_score,
        )


# This is a slighty modified version of the Knuth-Morris-Pratt algorithm
# https://en.wikipedia.org/wiki/Knuth%E2%80%93Morris%E2%80%93Pratt_algorithm
def kmp_table(haystack: str) -> list[int]:
    """
    Generates the backtracking table used for the Knuth-Morris-Pratt string search algorithm.

    Args:
        haystack (str): The string to generate a backtracking table for.
    Returns:
        list[int]: Backtracking table
    """
    cnd = 0
    table = [-1] * len(haystack)

    for pos in range(1, len(haystack)):
        if haystack[pos] == haystack[cnd]:
            table[pos] = table[cnd]
        else:
            table[pos] = cnd
            while (cnd >= 0) and (haystack[pos] != haystack[cnd]):
                cnd = table[cnd]
        cnd += 1

    table[-1] = cnd
    return table


def kmp_search(needle: str, haystack: str) -> tuple[int, int]:
    """
    A modified version of the Knuth-Morris-Pratt algorithm.
    The KMP algorithm can be used for efficently finding a substring(needle) within another string(haystack).

    This implementation has been modified to return the first occurence of the needle and to also find partial matches.
    I.e. given the needle "box" and the haystack "hi bob", this algortihm will consider "bo" to be a partial match in the haystack and thus return that.

    Args:
        needle (str): The substring to search for.
        haystack (str): The string to search in.
    Returns:
        (int, int): The start index of the match and the length.
    """
    j = 0
    k = 0
    table = kmp_table(haystack)

    candidate_start = 0
    candidate_len = 0

    while j < len(haystack):
        if needle[k] == haystack[j]:
            j += 1
            k += 1
            if k == len(needle):
                return (j - k, len(needle))
        else:
            if k > candidate_len:
                candidate_start = j - k
                candidate_len = k
            k = table[k]
            if k < 0:
                j += 1
                k += 1

    if k > candidate_len:
        return (j - k, k)

    return (candidate_start, candidate_len)


def find_almost_substring(needle: str, haystack: str) -> str:
    """
    Finds substring(needle) within another string(haystack) if it exists.
    Otherwise finds an "almost substring" if no actual substring exists.

    An almost substring is defined as a substring that shares a prefix with the needle.
    I.e. needle = "box", haystack = "hi bob", find_almost_substring(needle, haystack) -> "bo".

    Args:
        needle (str): The substring to search for.
        haystack (str): The string to find the needle(substring) in.
    Returns:
        str: The substring if it exists, otherwise a string whose prefix matches the needle
    """
    start, len = kmp_search(needle, haystack)
    if len == 0:
        return ""
    return haystack[start : (start + len)]
