import pytest

from app.utils.substring_matching_utils import (
    find_longest_partial_substring,
    kmp_search,
    kmp_table,
)


def test_kmp_table_different() -> None:
    haystack = "abc"
    result = kmp_table(haystack)
    assert result == [-1, 0, 0]


def test_kmp_table_repeating() -> None:
    haystack = "abab"
    result = kmp_table(haystack)
    assert result == [-1, 0, -1, 2]


def test_kmp_table_same_letter() -> None:
    haystack = "aaaa"
    result = kmp_table(haystack)
    assert result == [-1, -1, -1, 3]


def test_kmp_search_full_match() -> None:
    needle = "school"
    haystack = "I go to school"
    result = kmp_search(needle, haystack)
    assert result == (8, 6)


def test_kmp_search_partial_match() -> None:
    needle = "schoolyard"
    haystack = "I go to school"
    result = kmp_search(needle, haystack)
    assert result == (8, 6)


def test_kmp_search_no_match() -> None:
    needle = "xyz"
    haystack = "I took a tour"
    result = kmp_search(needle, haystack)
    assert result == (0, 0)


def test_kmp_search_needle_longer_than_haystack() -> None:
    needle = "schoolyard"
    haystack = "school"
    result = kmp_search(needle, haystack)
    assert result == (0, 6)


def test_kmp_search_empty_needle_raises_value_error() -> None:
    needle = ""
    haystack = "hello"

    with pytest.raises(ValueError, match="needle must not be empty"):
        kmp_search(needle, haystack)


def test_find_longest_partial_substring_full_match() -> None:
    needle = "proper substring"
    haystack = "abc proper proper proper example proper substring distraction proper"
    result = find_longest_partial_substring(needle, haystack)
    assert result == "proper substring"


def test_find_longest_partial_substring_no_match() -> None:
    needle = "does not exist"
    haystack = "yup"
    result = find_longest_partial_substring(needle, haystack)
    assert result == ""


def test_find_longest_partial_substring_partial_match() -> None:
    needle = "love"
    haystack = "I loathe testing"
    result = find_longest_partial_substring(needle, haystack)
    assert result == "lo"


def test_find_longest_partial_substring_case_insensitive() -> None:
    needle = "varying"
    haystack = "vArYiNg CaSe"
    result1 = find_longest_partial_substring(needle, haystack, case_sensitive=True)
    result2 = find_longest_partial_substring(needle, haystack, case_sensitive=False)
    assert result1 == "v"
    assert result2 == "vArYiNg"
