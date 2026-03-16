from math import isclose

from app.core.models.rouge_evaluator import (
    find_n_grams,
    longest_common_subsequence,
    rouge_l,
    rouge_n,
)


# ROUGE-N tests
def test_rouge_n_unigram() -> None:
    reference = "the cat is on the mat"
    model_output = "the cat and the dog"
    n_gram = 1

    score = rouge_n(model_output, reference, n_gram)
    assert isclose(score.precision, 0.6)
    assert isclose(score.recall, 0.5)
    assert isclose(round(score.f1_score, 2), 0.55)


def test_rouge_n_bigram() -> None:
    reference = "the cat is on the mat"
    model_output = "the cat and the dog"
    n_gram = 2

    score = rouge_n(model_output, reference, n_gram)
    assert isclose(score.precision, 0.25)
    assert isclose(score.recall, 0.2)
    assert isclose(round(score.f1_score, 2), 0.22)


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

    assert lcs == longest_common_subsequence(reference.split(), model_output.split())
    assert isclose(score.precision, expected_precision)
    assert isclose(score.recall, expected_recall)
    assert isclose(score.f1_score, expected_score)


# HAPPY PATHS
def test_longest_common_subsequence_happypath_1() -> None:
    model_output = "the cat and the dog"
    reference = "the cat is on the mat"

    model_unigrams = model_output.split()
    reference_unigrams = reference.split()

    lcs = longest_common_subsequence(model_unigrams, reference_unigrams)
    assert lcs == 3


def test_longest_common_subsequence_happypath_2() -> None:
    model_output = "the missile knows where it is at all times"
    reference = "it doesn't know where it is the missile that all is"

    model_unigrams = model_output.split()
    reference_unigrams = reference.split()

    lcs = longest_common_subsequence(model_unigrams, reference_unigrams)
    assert lcs == 4


def test_longest_common_subsequence_edgecase_1() -> None:
    model_output = ""
    reference = ""

    model_unigrams = model_output.split()
    reference_unigrams = reference.split()

    lcs = longest_common_subsequence(model_unigrams, reference_unigrams)
    assert lcs == 0


def test_longest_common_subsequence_edgecase_2() -> None:
    model_output = "the reference is empty"
    reference = ""

    model_unigrams = model_output.split()
    reference_unigrams = reference.split()

    lcs = longest_common_subsequence(model_unigrams, reference_unigrams)
    assert lcs == 0


def test_longest_common_subsequence_edgecase_3() -> None:
    model_output = ""
    reference = "the model output is empty"

    model_unigrams = model_output.split()
    reference_unigrams = reference.split()

    lcs = longest_common_subsequence(model_unigrams, reference_unigrams)
    assert lcs == 0


def test_longest_common_subsequence_edgecase_4() -> None:
    model_output = "exact same string in both"
    reference = "exact same string in both"

    model_unigrams = model_output.split()
    reference_unigrams = reference.split()

    lcs = longest_common_subsequence(model_unigrams, reference_unigrams)
    assert lcs == len(model_unigrams)


def test_find_n_grams_bigrams() -> None:
    text = "this contains four unigrams"
    bigrams = find_n_grams(text, 2)

    assert bigrams.contains(("this", "contains"))
    assert bigrams.contains(("contains", "four"))
    assert bigrams.contains(("four", "unigrams"))

    assert bigrams.multiples_of(("this", "contains")) == 1
    assert bigrams.multiples_of(("contains", "four")) == 1
    assert bigrams.multiples_of(("four", "unigrams")) == 1
    assert len(bigrams) == 3


def test_find_n_grams_trigrams() -> None:
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


def test_find_n_grams_duplicates() -> None:
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


# EDGE CASES
def test_find_n_grams_empty_str() -> None:
    text = ""
    bigrams = find_n_grams(text, 2)
    assert len(bigrams) == 0
    assert not bigrams.contains(("", ""))


def test_find_n_grams_too_short_text() -> None:
    text = "too short"
    trigrams = find_n_grams(text, 3)
    assert len(trigrams) == 0
    assert not trigrams.contains(("too", "short"))
    assert not trigrams.contains(("too", "short", ""))
