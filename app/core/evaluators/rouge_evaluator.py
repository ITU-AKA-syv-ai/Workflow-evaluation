import sys
from typing import Any

from pydantic import BaseModel, ValidationError

from app.core.evaluators.base import BaseEvaluator
from app.core.models.evaluation_model import EvaluationResult

# PREFACE for some terminology used in this code
#
# 1: N-grams
#
# An N-gram is defined as a sequence of adjacent symbols of size N.
# A 1-gram is called unigram, a 2-gram is called bigram and a 3-gram is called a trigram.
#
# A symbol may be a single character, but it can also be an entire word.
# For this code, we're using entire words.
#
# Take the following sentence as an example "this is just an example"
# Here are all unigrams: [("this"), ("is"), ("just"), ("an"), ("example")]
# Here are all bigrams: [("this", "is"), ("is", "just"), ("just", "an"), ("an", "example")]
# Here are all trigrams: [("this", "is", "just"), ("is", "just", "an"), ("just", "an", "example")]
#
# 2: Longest Common Subsequence (LCS)
#
# A common subsequence between two lists A and B, is a sequence of values that appear in the same order in both.
#
# Take the following two lists of unigrams:
# A = [("this"), ("is"), ("the"), ("complicated"), ("example")]
# B = [("here"), ("is"), ("the"), ("simple"), ("example")]
#
# An example of a common subsequence would be [("the"), ("example")] because both unigrams appear in the same order in both lists.
#
# The longest common subsequence(or LCS for short) is the common subsequence which is the longest.
# In this example:
# LCS = [("is", "the", "example")]


class RougeEvaluatorConfig(BaseModel):
    """
    Configuration for the Rouge Evaluator.

    Attributes:
        reference (str): The human written text to compare the model text against
        n_grams (int | None): If int is given, then this will employ ROUGE-N. I.e. when n_grams = 1, ROUGE-1 will be used. If None is given, this configuration will employ ROUGE-L and so will n_grams = 0.
    """

    reference: str
    n_grams: int | None = None


class RougeEvaluator(BaseEvaluator):
    """
    Evaluator that employs the ROUGE metric to compare some LLM generated with a reference.

    Depending on whether if the `RougeEvaluatorConfig` given, this will either use ROUGE-N or ROUGE-L.

    The ROUGE-N metric finds the total number of matching N-grams between some LLM output and a human written reference that match.
    The ROUGE-L metric uses the longest common subsequence instead of N-grams.
    """

    @property
    def name(self) -> str:
        return "rouge_evaluator"

    @property
    def description(self) -> str:
        return "Computes the ROUGE metric"

    @property
    def config_schema(self) -> dict[str, Any]:
        return RougeEvaluatorConfig.model_json_schema()

    def validate_config(self, config: dict[str, Any]) -> RougeEvaluatorConfig | None:
        """
        Args:
            config (dict[str, Any]): The config to bind to a RougeEvaluatorConfig

        Returns:
            RougeEvaluatorConfig | None: Returns RougeEvaluatorConfig if config is correctly formatted, otherwise None is returned

        """
        try:
            bound_config = RougeEvaluatorConfig.model_validate(config)
            if bound_config.reference == "" or (
                bound_config.n_grams is not None and bound_config.n_grams < 0
            ):
                return None
            return bound_config
        except ValidationError:
            return None

    @property
    def default_threshold(self) -> float:
        return 0.5

    def _evaluate(self, output: str, config: RougeEvaluatorConfig) -> EvaluationResult:
        """
        Calculate the ROUGE metric on the output using the given configuration.

        If config.n_grams is some integer, then that is used as the N for ROUGE-N.

        If config.n_grams is None, then ROUGE-L is used.

        Args:
            output (str): The LLM output to calculate the ROUGE metric for.
            config (RougeEvaluatorConfig): The configuration containing the reference and potentially the size of the N-grams if ROUGE-N is desired.

        Returns:
            EvaluationResult: The evaluation result containing the ROUGE metric as the normalised score
        """
        if config.reference == "":
            return EvaluationResult(
                evaluator_id=self.name,
                reasoning="Expected a reference to compare the model output with.",
                error="No reference given.",
            )
        score = RougeScore(precision=0, recall=0, f1_score=0, reasoning="")

        # The LCS algorithm uses recursion, we set this as a limit to avoid a stack overflow.
        # The constant 2400 is here to match the character limit in the Cosine Similarity evaluator.
        if len(output) > 2400 or len(config.reference) > 2400:
            message = f"The given text is too long, limit is 2400, got: {len(output)} and {len(config.reference)}"
            return EvaluationResult(
                evaluator_id=self.name,
                reasoning=message,
                error=message,
                score=score.f1_score,
            )

        # If no N-gram size is given or is set to 0, then this is interpreted as a request for ROUGE-L
        if config.n_grams is not None and config.n_grams != 0:
            if config.n_grams > 0:
                score = rouge_n(output, config.reference, config.n_grams)
            else:
                return EvaluationResult(
                    evaluator_id=self.name,
                    reasoning="The given N value for N-gram is negative.",
                    error="N-Gram cannot be negative.",
                )
        else:
            score = rouge_l(output, config.reference)

        return EvaluationResult(
            evaluator_id=self.name,
            reasoning=score.reasoning,
            normalised_score=score.f1_score,
        )


# ROUGE
class RougeScore(BaseModel):
    """
    The three values computed by ROUGE.

    Attributes:
       precision: If ROUGE-N then this is the ratio between the intersection of N-Grams and the number of N-Grams in the LLM output. For ROUGE-L the intersection is replaced by the length of the LCS.
       recall: If ROUGE-N then this is the ratio between the intersection of N-Grams and the number of N-Grams in the reference. For ROUGE-L the intersection is replaced by the length of LCS.
       f1_score: The final ROUGE metric.
       reasoning: A textual explanation for the given score.
    """

    precision: float
    recall: float
    f1_score: float
    reasoning: str


class NGrams:
    """
    An add-only container type for holding N-grams and checking the size of intersection between two NGrams containers in O(N) time.

    NOTE, N-gram must be given as a tuple. This includes unigrams, i.e. ngrams.add(("example")), will not work as Python simply evaluates this as `("example")` as `"example"`. You must explicitly add a comma after the string like so: ngrams.add(("example",)).

    Attributes:
        ngrams (dict[tuple[str, ...], int]): A mapping between an N-gram and its number of occurrences
        n (int): Total number of N-grams in the container(counts duplicates).
    """

    ngrams: dict[tuple[str, ...], int]
    n: int

    def __init__(self) -> None:
        self.ngrams = {}
        self.n = 0

    def __len__(self) -> int:
        return self.n

    def contains(self, v: tuple[str, ...]) -> bool:
        """
        Checks if the given N-gram exists in the container.

        Args:
            v (tuple[str, ...]): The N-gram to check for

        Returns:
            bool: Whether if the N-gram was found in the container or not
        """
        return v in self.ngrams

    def multiples_of(self, v: tuple[str, ...]) -> int:
        """
        Counts the number of multiples of a specific N-gram within the container.

        Args:
            v (tuple[str, ...]): The N-gram to count the occurrences of.

        Returns:
            int: The number of occurrences of the N-gram found in the container. 0 if the N-gram does not occur.
        """
        return self.ngrams.get(v, 0)

    def add(self, ngram: tuple[str, ...]) -> None:
        """
        Add N-gram into the container.

        Args:
            ngram (tuple[str, ...]): The N-gram to add to the container.
        """
        self.n += 1
        if ngram in self.ngrams:
            self.ngrams[ngram] += 1
        else:
            self.ngrams[ngram] = 1

    def overlap_size(self, other: "NGrams") -> int:
        """
        Measures the number of N-grams that appear in self, which also appear in other.

        Args:
            other (NGrams): The other NGrams container to check measure the overlap with.

        Returns:
            int: The size of the overlap between the two NGrams containers.
        """
        sum = 0
        for k in self.ngrams:
            sum += min(self.multiples_of(k), other.multiples_of(k))
        return sum


def find_n_grams(text: str, n: int) -> NGrams:
    """
    Finds all N-grams within a given text.

    Args:
        text (str): The text to find the N-grams in.
        n (int): The size of the N-grams

    Returns:
        NGrams: All the N-grams found in the text
    """
    unigrams = text.split()
    number_of_ngrams = len(unigrams) - n + 1
    ngrams = NGrams()

    for i in range(number_of_ngrams):
        ngrams.add(tuple(unigrams[i : i + n]))

    return ngrams


def rouge_n(model_output: str, reference: str, n_gram: int) -> RougeScore:
    """
    ROUGE-N is a metric which measures the amount of overlap with the N-grams found in the model output that also exist in the reference.

    Args:
        model_output (str): The model output to measure the ROUGE-N metric for.
        reference (str): The reference to compare the model output with.
        n_gram (int): The size of the N-grams.

    Returns:
        RougeScore: The ROUGE-N score along with the two intermediary values used to compute it. (See docstrings for `RougeScore` for more information)
    """
    output_n_grams = find_n_grams(model_output, n_gram)
    reference_n_grams = find_n_grams(reference, n_gram)

    overlap_ref_out = output_n_grams.overlap_size(reference_n_grams)
    overlap_out_ref = reference_n_grams.overlap_size(output_n_grams)

    precision = 0 if len(output_n_grams) == 0 else overlap_ref_out / len(output_n_grams)
    recall = (
        0 if len(reference_n_grams) == 0 else overlap_out_ref / len(reference_n_grams)
    )

    score = (
        0
        if precision + recall == 0
        else 2 * (precision * recall) / (precision + recall)
    )

    reasoning = f"The overlap between the reference and output consists of {overlap_ref_out} {n_gram}-grams and {overlap_out_ref} between the output and reference. There are {len(output_n_grams)} {n_gram}-grams in the model output and {len(reference_n_grams)} in the reference."

    return RougeScore(
        precision=precision, recall=recall, f1_score=score, reasoning=reasoning
    )


def longest_common_subsequence(
    unigrams_model: list[str], unigrams_reference: list[str]
) -> int:
    """
    Determines the length of the longest common subsequence between two lists of unigrams.
    Specifically used for ROUGE-L, the parameter names are thus set to fit it.
    Read the pre-face at the start of this source file for more information.

    Args:
        unigrams_model (list[str]): The list of unigrams the LLM output consists of.
        unigrams_reference (list[str]): The list of unigrams the reference consists of.

    Returns:
        int: The length of the longest common subsequence.
    """
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

    previous_recursion_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(10**6)

    result = helper(rows, cols)
    sys.setrecursionlimit(previous_recursion_limit)
    return result


def rouge_l(model_output: str, reference: str) -> RougeScore:
    """
    ROUGE-L is a metric which measures the amount of overlap with the Longest Common Subsequence found in the model output that also exist in the reference.

    Args:
        model_output (str): The model output to measure the ROUGE-L metric for.
        reference (str): The reference to compare the model output with.

    Returns:
        RougeScore: The ROUGE-L score along with the two intermediary values used to compute it. (See docstrings for `RougeScore` for more information)
    """
    unigrams_model = model_output.split()
    unigrams_reference = reference.split()

    lcs = longest_common_subsequence(unigrams_model, unigrams_reference)

    precision = 0 if len(unigrams_model) == 0 else lcs / len(unigrams_model)
    recall = 0 if len(unigrams_reference) == 0 else lcs / len(unigrams_reference)

    score = (
        0
        if (precision + recall) == 0
        else 2 * (precision * recall) / (precision + recall)
    )

    reasoning = f"The Longest Common Sequence consists of {lcs} unigrams, there are {len(unigrams_model)} unigrams in the model output and {len(unigrams_reference)} in the reference"

    return RougeScore(
        precision=precision, recall=recall, f1_score=score, reasoning=reasoning
    )
