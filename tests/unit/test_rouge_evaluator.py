from math import isclose

from app.core.models.rouge_evaluator import (
    find_n_grams,
    rouge_n,
)


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


# HAPPY PATHS
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
