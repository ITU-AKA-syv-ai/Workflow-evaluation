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
