# This is a slightly modified version of the Knuth-Morris-Pratt (KMP) string search algorithm
# The KMP algorithm can be used for efficiently finding a substring(needle) within another string(haystack).
# https://en.wikipedia.org/wiki/Knuth%E2%80%93Morris%E2%80%93Pratt_algorithm


def find_longest_partial_substring(needle: str, haystack: str, case_sensitive: bool = True) -> str:
    """
    Finds substring(needle) within another string(haystack) if it exists.
    Otherwise, finds the longest partial substring.

    A partial match is defined as the longest prefix of 'needle' found consecutively in 'haystack'.
    Example: needle="box", haystack="hi bob" -> returns "bo".

    Args:
        needle (str): The substring to search for.
        haystack (str): The string to find the needle(substring) in.
    Returns:
        str: Full match if found; otherwise, the longest consecutive prefix of 'needle'.
    """
    if needle == "":
        return ""
    start, match_len = kmp_search(needle, haystack, case_sensitive)
    if match_len == 0:  # No match found
        return ""
    return haystack[start : (start + match_len)]


def kmp_search(needle: str, haystack: str, case_sensitive: bool = True) -> tuple[int, int]:
    """
    Searches for the first occurrence of 'needle' in 'haystack' using a modified KMP algorithm.
    This version:
    - Returns the first full occurrence of `needle` in `haystack`.
    - If no full match exists, returns the longest prefix of `needle` found as a partial match.

    Args:
        needle (str): The substring to search for.
        haystack (str): The string to search in.
    Returns:
        tuple[int, int]: The start index of the match and the length.
    Raises:
        ValueError: If `needle` is empty.
    """
    if len(needle) == 0:
        raise ValueError("needle must not be empty")
    j = 0  # pointer in haystack
    k = 0  # pointer in needle
    table = kmp_table(needle)

    cmp = (lambda a, b: a == b) if case_sensitive else (lambda a, b: a.lower() == b.lower())

    candidate_start = 0  # start index of the longest partial match
    candidate_len = 0  # length of the longest partial match

    while j < len(haystack):
        if cmp(needle[k], haystack[j]):  # If the characters match, then we can advance the pointers
            j += 1
            k += 1
            if k == len(needle):  # full match found
                return (j - k, len(needle))
        else:  # Find the longest partial match
            if k > candidate_len:  # update the longest partial match so far
                candidate_start = j - k
                candidate_len = k
            k = table[k]  # backtrack needle pointer using table
            if k < 0:  # cannot backtrack, advance haystack pointer
                j += 1
                k += 1

    # Check if the last partial match found is longer than the current partial match.
    if k > candidate_len:
        return (j - k, k)
    return (
        candidate_start,
        candidate_len,
    )  # If no partial match is found, it returns (0, 0)


def kmp_table(haystack: str) -> list[int]:
    """
    Generates the backtracking table used for the KMP search.

    The table tells the KMP search algorithm how far to jump back in the needle when a mismatch occurs in the search,
    so it can avoid re-checking characters unnecessarily.
    -1 is special: if a mismatch occurs at this index, we simply advance haystack (such that we don't backtrack to it).

    Args:
        haystack (str): The string to generate a backtracking table for.
    Returns:
        list[int]: Backtracking table
    """

    table = [0] * len(haystack)
    table[0] = -1

    cnd = 0  # length of the current candidate substring

    for pos in range(1, len(haystack)):
        # Matches previous prefix, copy backtrack index
        if haystack[pos] == haystack[cnd]:
            table[pos] = table[cnd]
        else:  # Mismatch
            table[pos] = cnd  # Saves the longest prefix of the current candidate substring
            while (cnd >= 0) and (
                haystack[pos] != haystack[cnd]
            ):  # Backtrack through previous prefixes until a match is found or start is reached
                cnd = table[cnd]
        cnd += 1

    table[-1] = cnd  # final adjustment for correctness

    return table
