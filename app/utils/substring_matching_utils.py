# This is a slightly modified version of the Knuth-Morris-Pratt algorithm
# https://en.wikipedia.org/wiki/Knuth%E2%80%93Morris%E2%80%93Pratt_algorithm
def kmp_table(haystack: str) -> list[int]:
    """
    Generates the backtracking table used for the Knuth-Morris-Pratt string search algorithm.
    This function solely exists to be used by kmp_search.

    Args:
        haystack (str): The string to generate a backtracking table for.
    Returns:
        list[int]: Backtracking table
    """
    # The KMP search algorithm, always wants to keep moving the pointers forward and minimise backtracking.
    # The table tells if we should backtrack and by how much.
    #
    # -1 is a special value which symbolises that if the character at that index mismatches our needle, then we shouldn't backtrack to it.
    table = [0] * len(haystack)
    table[0] = -1

    # If the current character belongs to a proper suffix that can be created by characters seen earlier
    # in the string, then this keeps track of the index of the character within said suffix.
    cnd = 0

    # Since this is searching for suffixes, we'll start 1 and start checking if it's a suffix of haystack[0]
    for pos in range(1, len(haystack)):
        # If the characters are identical, then each character at haystack[pos] could be treated as a suffix of the prior characters.
        # Thus they all end up with the same index.
        if haystack[pos] == haystack[cnd]:
            table[pos] = table[cnd]
        else:
            # When characters mismatch, we want to run through the entire suffix
            # thus far and determine the index of the character at haystack[pos] within the suffix.
            table[pos] = cnd
            while (cnd >= 0) and (haystack[pos] != haystack[cnd]):
                cnd = table[cnd]
        cnd += 1

    # Needed for correctness
    table[-1] = cnd

    return table


def kmp_search(needle: str, haystack: str) -> tuple[int, int]:
    """
    A modified version of the Knuth-Morris-Pratt algorithm.
    The KMP algorithm can be used for efficiently finding a substring(needle) within another string(haystack).

    This implementation has been modified to return the first occurrence of the needle and to also find partial matches.
    I.e. given the needle "box" and the haystack "hi bob", this algorithm will consider "bo" to be a partial match in the haystack and thus return that.

    Args:
        needle (str): The substring to search for.
        haystack (str): The string to search in.
    Returns:
        tuple[int, int]: The start index of the match and the length.
    """
    # j is the haystack pointer
    # k is the needle pointer
    j = 0
    k = 0
    table = kmp_table(haystack)

    candidate_start = 0
    candidate_len = 0

    while j < len(haystack):
        # If the character at the needle pointer matches the one at the haystack pointer,
        # then we have a match and can advance the pointers.
        if needle[k] == haystack[j]:
            j += 1
            k += 1
            # If the length of the needle pointer matches the length of the needle,
            # then the entire needle has been found within the haystack.
            if k == len(needle):
                return (j - k, len(needle))
        else:
            # Keeping track of the longest prefix of the needle found thus far.
            # This is used to find partial matches(see find_almost_substring for why we want this).
            if k > candidate_len:
                candidate_start = j - k
                candidate_len = k
            # We use the backtracking table to know if whether if we should backtrace or not,
            # thus saving redundant checks.
            k = table[k]
            # There is case where where the table tells us to backtrack to exactly -1(but never lower).
            # -1 is a reserved value which means that the current character cannot be matched and we should just advance the haystack pointer.
            if k < 0:
                j += 1
                k += 1

    # If we get to this point, then the needle in its entirety does not exist in the haystack.
    # This instead determines the longest prefix of needle that exists in the haystack.
    #
    # The code for keeping track of the longest prefix doesn't run on the last iteration.
    # This last check needs to be here to see if the last string we checked is strictly longer than the previous one we've found.
    if k > candidate_len:
        return (j - k, k)
    return (candidate_start, candidate_len)


def find_almost_substring(needle: str, haystack: str) -> str:
    """
    Finds substring(needle) within another string(haystack) if it exists.
    Otherwise, finds an "almost substring" if no actual substring exists.

    An almost substring is defined as a substring that shares a prefix with the needle.
    I.e. needle = "box", haystack = "hi bob", find_almost_substring(needle, haystack) -> "bo".

    Args:
        needle (str): The substring to search for.
        haystack (str): The string to find the needle(substring) in.
    Returns:
        str: The substring if it exists, otherwise a string whose prefix matches the needle
    """
    start, match_len = kmp_search(needle, haystack)
    if len == 0:
        return ""
    return haystack[start : (start + match_len)]
