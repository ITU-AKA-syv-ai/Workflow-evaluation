from math import ceil, isclose

import pytest

from app.core.evaluators.rouge_evaluator import (
    RougeEvaluator,
    RougeEvaluatorConfig,
    find_n_grams,
    longest_common_subsequence,
    rouge_l,
    rouge_n,
)

# NOTE:
# Here you'll see a lot of weird and seemingly pointless casting of string to strings.
# This has to do with the fact that ty doesn't appreciate `str` and `LiteralString`
# being used interchangeably.


# ROUGE evaluator evaluate tests
@pytest.mark.asyncio
async def test_rouge_evaluator_evaluate_happypath_1() -> None:
    evaluator = RougeEvaluator(threshold=0.5, timeout=30)
    output = "Not a test"
    config = RougeEvaluatorConfig(reference="This is a test", n_grams=2)

    score = await evaluator.evaluate(output, config)
    assert score.error is None
    assert isclose(round(score.normalised_score, 2), 0.4)


@pytest.mark.asyncio
async def test_rouge_evaluator_evaluate_happypath_2() -> None:
    evaluator = RougeEvaluator(threshold=0.5, timeout=30)
    output = "This will be compared with ROUGE-L."
    config = RougeEvaluatorConfig(reference="Must be compared with ROUGE-L.")

    score = await evaluator.evaluate(output, config)
    assert score.error is None
    assert isclose(round(score.normalised_score, 2), 0.73)


@pytest.mark.asyncio
async def test_rouge_evaluator_evaluate_edgepath_1() -> None:
    evaluator = RougeEvaluator(threshold=0.5, timeout=30)
    output = "This will be compared with ROUGE-L."
    config = RougeEvaluatorConfig(reference="Must be compared with ROUGE-L.", n_grams=0)

    score = await evaluator.evaluate(output, config)
    assert score.error is None
    assert isclose(round(score.normalised_score, 2), 0.73)


@pytest.mark.asyncio
async def test_rouge_evaluator_evaluate_edgepath_2() -> None:
    evaluator = RougeEvaluator(threshold=0.5, timeout=30)
    output = "Short output"
    # The edge case here is the fact that the N gram size is larger than the number of unigrams
    config = RougeEvaluatorConfig(reference="Short reference", n_grams=3)

    score = await evaluator.evaluate(output, config)
    assert score.error is None
    assert isclose(score.normalised_score, 0)


@pytest.mark.asyncio
async def test_rouge_evaluator_evaluate_errorpath_1() -> None:
    evaluator = RougeEvaluator(threshold=0.5, timeout=30)
    output = "Error path test"
    # This should technically never occur since validate_config will not allow negative numbers for n_grams, but let's test it anyways
    config = RougeEvaluatorConfig(reference="This error path should never occur", n_grams=-1)

    score = await evaluator.evaluate(output, config)
    assert score.error is not None
    assert score.error == "N-Gram cannot be negative."


@pytest.mark.asyncio
async def test_rouge_evaluator_evaluate_errorpath_2() -> None:
    evaluator = RougeEvaluator(threshold=0.5, timeout=30)
    output = "Yet another error path test"
    # This should technically never occur since validate_config will not allow an empty refrence, but let's test it anyways
    config = RougeEvaluatorConfig(reference="")

    score = await evaluator.evaluate(output, config)
    assert score.error is not None
    assert score.error == "No reference given."


@pytest.mark.asyncio
async def test_rouge_evaluator_evaluate_errorpath_3() -> None:
    evaluator = RougeEvaluator(threshold=0.5, timeout=30)
    config = RougeEvaluatorConfig(reference="reference")
    text = "Test! Test! Test!"
    lst = []
    limit_exceed = ceil(2400 / len(text)) + 1
    for _ in range(limit_exceed):
        lst.append(text)
    long_output = " ".join(lst)

    result = await evaluator.evaluate(long_output, config)
    assert result.error is not None
    assert result.error.startswith("The given text is too long")


# ROUGE evaluator validate_config tests
def test_rouge_evaluator_validate_config_happypath_1() -> None:
    evaluator = RougeEvaluator(threshold=0.5, timeout=30)
    reference = "This is a test"
    n_grams = 2
    config = {"reference": reference, "n_grams": n_grams}

    bound_config = evaluator.validate_config(config)
    assert bound_config is not None
    assert bound_config.n_grams == n_grams
    assert bound_config.reference == reference


def test_rouge_evaluator_validate_config_happypath_2() -> None:
    evaluator = RougeEvaluator(threshold=0.5, timeout=30)
    reference = "No N-gram specified means ROUGE-L"
    config = {"reference": reference}

    bound_config = evaluator.validate_config(config)
    assert bound_config is not None
    assert bound_config.n_grams is None
    assert bound_config.reference == reference


def test_rouge_evaluator_validate_config_errorpath_1() -> None:
    evaluator = RougeEvaluator(threshold=0.5, timeout=30)
    reference = "Negative integers for N-grams not allowed!"
    n_grams = -1
    config = {"reference": reference, "n_grams": n_grams}

    bound_config = evaluator.validate_config(config)
    assert bound_config is None


def test_rouge_evaluator_validate_config_errorpath_2() -> None:
    evaluator = RougeEvaluator(threshold=0.5, timeout=30)
    reference = ""
    config = {"reference": reference}

    bound_config = evaluator.validate_config(config)
    assert bound_config is None


def test_rouge_evaluator_validate_config_errorpath_3() -> None:
    evaluator = RougeEvaluator(threshold=0.5, timeout=30)
    reference = "wrong_value"
    config = {"wrong_key": reference}

    bound_config = evaluator.validate_config(config)
    assert bound_config is None


# ROUGE-N tests
def test_rouge_n_unigram_happypath() -> None:
    reference = "the cat is on the mat"
    model_output = "the cat and the dog"
    n_gram = 1

    score = rouge_n(model_output, reference, n_gram)

    assert isclose(score.precision, 0.6)
    assert isclose(score.recall, 0.5)
    assert isclose(round(score.f1_score, 2), 0.55)


# Score should be zero since there isn't a single overlapping unigram
def test_rouge_n_unigram_long_example_bad_match_edgecase() -> None:
    reference = "The missile knows where it is at all times. It knows this because it knows where it isn't. By subtracting where it is from where it isn't, or where it isn't from where it is (whichever is greater), it obtains a difference, or deviation. The guidance subsystem uses deviations to generate corrective commands to drive the missile from a position where it is to a position where it isn't, and arriving at a position where it wasn't, it now is. Consequently, the position where it is, is now the position that it wasn't, and it follows that the position that it was, is now the position that it isn't. In the event that the position that it is in is not the position that it wasn't, the system has acquired a variation, the variation being the difference between where the missile is, and where it wasn't. If variation is considered to be a significant factor, it too may be corrected by the GEA. However, the missile must also know where it was. The missile guidance computer scenario works as follows. Because a variation has modified some of the information the missile has obtained, it is not sure just where it is. However, it is sure where it isn't, within reason, and it knows where it was. It now subtracts where it should be from where it wasn't, or vice-versa, and by differentiating this from the algebraic sum of where it shouldn't be, and where it was, it is able to obtain the deviation and its variation, which is called error."
    model_output = "No matches with reference exist here"
    n_gram = 1

    score = rouge_n(model_output, reference, n_gram)

    assert score.precision == 0
    assert score.recall == 0
    assert score.f1_score == 0


# Score should be greater than zero since there is at least some overlapping unigrams
def test_rouge_n_unigram_long_example_partial_match_happypath() -> None:
    reference = "The missile knows where it is at all times. It knows this because it knows where it isn't. By subtracting where it is from where it isn't, or where it isn't from where it is (whichever is greater), it obtains a difference, or deviation. The guidance subsystem uses deviations to generate corrective commands to drive the missile from a position where it is to a position where it isn't, and arriving at a position where it wasn't, it now is. Consequently, the position where it is, is now the position that it wasn't, and it follows that the position that it was, is now the position that it isn't. In the event that the position that it is in is not the position that it wasn't, the system has acquired a variation, the variation being the difference between where the missile is, and where it wasn't. If variation is considered to be a significant factor, it too may be corrected by the GEA. However, the missile must also know where it was. The missile guidance computer scenario works as follows. Because a variation has modified some of the information the missile has obtained, it is not sure just where it is. However, it is sure where it isn't, within reason, and it knows where it was. It now subtracts where it should be from where it wasn't, or vice-versa, and by differentiating this from the algebraic sum of where it shouldn't be, and where it was, it is able to obtain the deviation and its variation, which is called error."
    model_output = "We have a missile somewhere and it knows where it is sometimes."
    n_gram = 1

    score = rouge_n(model_output, reference, n_gram)

    assert score.precision > 0
    assert score.recall > 0
    assert score.f1_score > 0


# NOTE: This is NOT the evaluator itself, it doesn't indicate errors.
# We are expecting zeros across all scores since there is no overlap between reference and the model output.
def test_rouge_n_empty_ref_edgecase() -> None:
    reference = ""
    model_output = "No reference given!"
    n_gram = 2

    score = rouge_n(model_output, reference, n_gram)

    assert score.precision == 0
    assert score.recall == 0
    assert score.f1_score == 0


def test_rouge_n_empty_output_edgecase() -> None:
    reference = "No model output given!"
    model_output = ""
    n_gram = 2

    score = rouge_n(model_output, reference, n_gram)

    assert score.precision == 0
    assert score.recall == 0
    assert score.f1_score == 0


def test_rouge_n_bigram_happypath() -> None:
    reference = "the cat is on the mat"
    model_output = "the cat and the dog"
    n_gram = 2

    score = rouge_n(model_output, reference, n_gram)

    assert isclose(score.precision, 0.25)
    assert isclose(score.recall, 0.2)
    assert isclose(round(score.f1_score, 2), 0.22)


def test_rouge_n_trigram_edgecase() -> None:
    # Not quite obvious why the score here should be zero.
    # Observe the fact that there is no overlap between these trigrams.
    #
    #    "the cat is"
    #    "cat is on"
    #    "is on the"
    #    "on the mat"
    #
    #    "the cat and"
    #    "cat and the"
    #    "and the dog"

    reference = "the cat is on the mat"
    model_output = "the cat and the dog"
    n_gram = 3

    score = rouge_n(model_output, reference, n_gram)

    assert isclose(score.precision, 0)
    assert isclose(score.recall, 0)
    assert isclose(score.f1_score, 0)


# ROUGE-L test
def test_rouge_l_happypath_1() -> None:
    reference = "the cat is on the mat"
    model_output = "the cat and the dog"

    score = rouge_l(model_output, reference)
    assert isclose(score.precision, 0.6)
    assert isclose(score.recall, 0.5)
    assert isclose(round(score.f1_score, 2), 0.55)


def test_rouge_l_happypath_2() -> None:
    reference = "the document states that this is a test"
    model_output = "it states that it is a test in this document"

    lcs = 5

    expected_precision = lcs / 10
    expected_recall = lcs / 8
    expected_score = 2 * (expected_precision * expected_recall) / (expected_precision + expected_recall)

    score = rouge_l(model_output, reference)

    assert lcs == longest_common_subsequence(list(map(str, reference.split())), list(map(str, model_output.split())))
    assert isclose(score.precision, expected_precision)
    assert isclose(score.recall, expected_recall)
    assert isclose(score.f1_score, expected_score)


# LCS algorithm tests
def test_longest_common_subsequence_happypath_1() -> None:
    model_output = "the cat and the dog"
    reference = "the cat is on the mat"

    model_unigrams = list(map(str, model_output.split()))
    reference_unigrams = list(map(str, reference.split()))

    lcs = longest_common_subsequence(model_unigrams, reference_unigrams)
    assert lcs == 3


def test_longest_common_subsequence_happypath_2() -> None:
    model_output = "the missile knows where it is at all times"
    reference = "it doesn't know where it is the missile that all is"

    model_unigrams = list(map(str, model_output.split()))
    reference_unigrams = list(map(str, reference.split()))

    lcs = longest_common_subsequence(model_unigrams, reference_unigrams)
    assert lcs == 4


def test_longest_common_subsequence_edgecase_1() -> None:
    model_output = ""
    reference = ""

    model_unigrams = list(map(str, model_output.split()))
    reference_unigrams = list(map(str, reference.split()))

    lcs = longest_common_subsequence(model_unigrams, reference_unigrams)
    assert lcs == 0


def test_longest_common_subsequence_edgecase_2() -> None:
    model_output = "the reference is empty"
    reference = ""

    model_unigrams = list(map(str, model_output.split()))
    reference_unigrams = list(map(str, reference.split()))

    lcs = longest_common_subsequence(model_unigrams, reference_unigrams)
    assert lcs == 0


def test_longest_common_subsequence_edgecase_3() -> None:
    model_output = ""
    reference = "the model output is empty"

    model_unigrams = list(map(str, model_output.split()))
    reference_unigrams = list(map(str, reference.split()))

    lcs = longest_common_subsequence(model_unigrams, reference_unigrams)
    assert lcs == 0


def test_longest_common_subsequence_edgecase_4() -> None:
    model_output = "exact same string in both"
    reference = "exact same string in both"

    model_unigrams = list(map(str, model_output.split()))
    reference_unigrams = list(map(str, reference.split()))

    lcs = longest_common_subsequence(model_unigrams, reference_unigrams)
    assert lcs == len(model_unigrams)


# NGrams tests
def test_find_n_grams_bigrams_happypath() -> None:
    text = "this contains four unigrams"
    bigrams = find_n_grams(text, 2)

    assert bigrams.contains(("this", "contains"))
    assert bigrams.contains(("contains", "four"))
    assert bigrams.contains(("four", "unigrams"))

    assert bigrams.multiples_of(("this", "contains")) == 1
    assert bigrams.multiples_of(("contains", "four")) == 1
    assert bigrams.multiples_of(("four", "unigrams")) == 1
    assert len(bigrams) == 3


def test_find_n_grams_trigrams_happypath() -> None:
    text = "comma, full-stop. exclamation! question? ran out of punctuation symbols"
    bigrams = find_n_grams(text, 3)

    assert bigrams.contains(("comma,", "full-stop.", "exclamation!"))
    assert bigrams.contains(("full-stop.", "exclamation!", "question?"))
    assert bigrams.contains(("exclamation!", "question?", "ran"))
    assert bigrams.contains(("question?", "ran", "out"))
    assert bigrams.contains(("ran", "out", "of"))
    assert bigrams.contains(("out", "of", "punctuation"))
    assert bigrams.contains(("of", "punctuation", "symbols"))

    assert bigrams.multiples_of(("comma,", "full-stop.", "exclamation!")) == 1
    assert bigrams.multiples_of(("full-stop.", "exclamation!", "question?")) == 1
    assert bigrams.multiples_of(("exclamation!", "question?", "ran")) == 1
    assert bigrams.multiples_of(("question?", "ran", "out")) == 1
    assert bigrams.multiples_of(("ran", "out", "of")) == 1
    assert bigrams.multiples_of(("out", "of", "punctuation")) == 1
    assert bigrams.multiples_of(("of", "punctuation", "symbols")) == 1

    assert len(bigrams) == 7


def test_find_n_grams_duplicates_happypath() -> None:
    text = "the good, the bad and the ugly and the extra and for the sake of the test"
    unigrams = find_n_grams(text, 1)

    assert unigrams.contains(("the",))
    assert unigrams.contains(("good,",))
    assert unigrams.contains(("the",))
    assert unigrams.contains(("bad",))
    assert unigrams.contains(("and",))
    assert unigrams.contains(("the",))
    assert unigrams.contains(("ugly",))

    assert unigrams.multiples_of(("the",)) == 6
    assert unigrams.multiples_of(("and",)) == 3
    assert len(unigrams) == 17


def test_find_n_grams_empty_str_edgecase() -> None:
    text = ""
    bigrams = find_n_grams(text, 2)
    assert len(bigrams) == 0
    assert not bigrams.contains(("", ""))


def test_find_n_grams_too_short_text_edgecase() -> None:
    text = "too short"
    trigrams = find_n_grams(text, 3)
    assert len(trigrams) == 0
    assert not trigrams.contains(("too", "short"))
    assert not trigrams.contains(("too", "short", ""))
