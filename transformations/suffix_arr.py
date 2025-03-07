#     Compress-py  A command-line interface for compressing files
#     Copyright (C) 2025  Yair Ziv
# 
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
# 
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.

# When writing this file, I used the following wonderful guide on the SA-IS algorithm for constructing suffix arrays:
# https://zork.net/~st/jottings/sais.html#the-sa-is-algorithm
# Go check it out!

from enum import Enum
from typing import Union


class SuffixType(str, Enum):
    """
    An enum containing the two types of a suffix: S-type or L-type.
    S-type suffixes are lexicographically smaller than the suffixes to their right.
    L-type suffixes are lexicographically larger than the suffixes to their right.
    Empty suffixes are defined as S-type.
    """
    L = "L"
    S = "S"

    def __repr__(self):
        return self.value


def get_suffixes_types(data: Union[list[int], bytes]) -> list[SuffixType]:
    """
    Given a data block, the function returns the suffix type of every suffix of the data.
    The types are returned as a list where the ith element is the suffix type of the suffix that starts at index i in
    the data.
    The length of the returned list will be len(data) + 1, to include the empty suffix.
    :param data: The data from which the suffix types will be extracted.
    :return: A list where the ith element is the suffix type of the suffix that starts at index i in the data.
    """
    # Initialize the list, default state will be S-Type:
    N = len(data)
    suffixes_types: list[SuffixType] = [SuffixType.S] * (N + 1)  # Empty suffix is always S-type

    # If the data is empty, early return:
    if N == 0:
        return suffixes_types

    # Since the empty suffix is defined as S-Type, the suffix containing the last byte is always L-type:
    suffixes_types[-2] = SuffixType.L

    # Compute the types backwards:
    for offset in range(N - 2, -1, -1):
        # If the current suffix starts with a character lexicographically larger, it's an L type:
        if data[offset] > data[offset + 1]:
            suffixes_types[offset] = SuffixType.L
        # If the two suffixes start with the same character, the current suffix's type will equal the next suffix's:
        elif data[offset] == data[offset + 1]:
            suffixes_types[offset] = suffixes_types[offset + 1]
    return suffixes_types


def compute_bucket_sizes(data: Union[list[int], bytes], alphabet_size: int) -> list[int]:
    """
    In preparation of bucket sort, the function returns the number of suffixes per bucket, where each bucket stores
    suffixes whose first value is the bucket's index.
    :param data: The data which suffixes are derived from, will determine bucket sizes.
    :param alphabet_size: Size of the alphabet used in data (i.e: the number of possible values in a single index of
                          data).
    :return: A list where the ith element is the number of suffixes that start with the data value 'i'.
    """
    bucket_sizes: list[int] = [0] * alphabet_size
    for data_val in data:
        bucket_sizes[data_val] += 1
    return bucket_sizes


def buckets_head_indices(bucket_sizes: list[int]) -> list[int]:
    """
    Given the sizes of each bucket, the function returns a list where each data value is mapped to its bucket index in
    the sorted suffix array.
    Note that offset 0 is always reserved for the empty suffix, so all returned values are larger than 0.
    :param bucket_sizes: The number of suffixes that start with the data value 'i', where 'i' is the index of the
                         current element.
    :return: A list mapping between a data value and the index of its bucket in the final sorted suffix array.
    """
    # Start the offset at 1 to reserve space for the empty suffix:
    offset = 1
    bucket_heads = []
    for size in bucket_sizes:
        bucket_heads.append(offset)
        offset += size
    return bucket_heads


def buckets_tail_indices(bucket_sizes: list[int]) -> list[int]:
    """
    Given the sizes of each bucket, the function returns a list where each data value is mapped to the end of its bucket
    in the sorted suffix array.
    Note that offset 0 is always reserved for the empty suffix, so all returned values are larger than 0.
    :param bucket_sizes: The number of suffixes that start with the data value 'i', where 'i' is the index of the
                         current element.
    :return: A list mapping between a data value and the index of the end of its bucket in the final sorted suffix
             array.
    """
    # Start the offset at 1 to reserve space for the empty suffix:
    offset = 1
    bucket_tails = []
    for size in bucket_sizes:
        offset += size
        bucket_tails.append(offset - 1)  # Don't include the next bucket
    return bucket_tails


def is_lms(suffix_types: list[SuffixType], index: int) -> bool:
    """
    A "Left-Most S" (LMS) character is a character that an S-Type suffix starts at its index, and to its left starts an
    L-Type suffix.
    Given this definition, the function checks if the character at a certain index of some data is an LMS character.
    :param suffix_types: A list where the ith element is the type of the suffix starting at index i.
    :param index: The index of the character checked in the function.
    :return: True if the character at the given index is an LMS character, False otherwise.
    """
    # The first character can never be an LMS character:
    if index == 0:
        return False
    # Check the previous character:
    return suffix_types[index] is SuffixType.S and suffix_types[index - 1] is SuffixType.L


def are_lms_slices_equal(data: Union[list[int], bytes], suffix_types: list[SuffixType], offset1: int, offset2: int) -> bool:
    """
    An LMS slice is a sequence of bytes that start at one LMS character and end at the next (excluding it).
    Given this definition, the function compares two LMS slices - one starting at offset1, the other at offset2 - and
    returns whether they are equal or not.
    :param data: The data both slices are taken from.
    :param suffix_types: A mapping between a byte's index and the type of the suffix starting at that index.
    :param offset1: The start of the first LMS slice to compare.
    :param offset2: The start of the second LMS slice to compare.
    :return: True if the LMS slice starting at offset1 is equal to the LMS slice starting at offset2.
    """
    # Ensure no slice is equal to the empty slice:
    if offset1 == len(data) or offset2 == len(data):
        return False

    # The empty slice is always an LMS character, so we will stop at the final index anyway:
    i = 0
    while True:
        is_lms_1, is_lms_2 = is_lms(suffix_types, offset1 + i), is_lms(suffix_types, offset2 + i)

        # If both ended at the same time, they are equal:
        if i > 0 and is_lms_1 and is_lms_2:
            return True

        # If one ended but not the other:
        if is_lms_1 ^ is_lms_2:
            return False

        # If the current bytes are not equal in value:
        if data[offset1 + i] != data[offset2 + i]:
            return False

        i += 1


def approximate_suffix_array(data: Union[list[int], bytes], bucket_tails: list[int], suffixes_types: list[SuffixType]) -> list[int]:
    """
    Performs bucket-sort on the LMS suffixes in the data, placing them at the right of a sorted suffix array.
    The returned array is only an approximation of the truly sorted suffix array, and will likely return -1 at indices
    where the suffix index could not be computed.
    :param data: Data the suffix array will be formed from.
    :param bucket_tails: A list where the ith element is the last index of a bucket containing suffixes that start with
                         the byte value 'i'.
    :param suffixes_types: The types of every suffix of data that starts at index 'i'.
    :return: An approximated suffix array, may be incomplete and/or sorted incorrectly.
    """
    # Initialize the suffix array:
    suffix_array: list[int] = [-1] * (len(data) + 1)  # Don't forget the empty suffix!

    # Bucket sort all LMS suffixes:
    lms_indices = filter(lambda offset: is_lms(suffixes_types, offset), range(len(data)))
    for i in lms_indices:
        # Get the bucket index of the current suffix:
        bucket_idx = bucket_tails[data[i]]

        # Insert into the bucket index, and decrement it for the next insertion:
        suffix_array[bucket_idx] = i
        bucket_tails[data[i]] -= 1

    # The empty suffix will always be first in the suffix array:
    suffix_array[0] = len(data)
    return suffix_array


def induce_sort_L(data: Union[list[int], bytes], approx_suffix_array: list[int], bucket_heads: list[int], suffix_types: list[SuffixType]) -> None:
    """
    Sorts the L-Type suffixes into their place in the approximated suffix array.
    :param data: The data suffixes are derived from.
    :param approx_suffix_array: The approximated suffix array, containing some suffix indices in their sorted place.
    :param bucket_heads: A mapping between every value in the data and the corresponding bucket's index in the suffix
                         array.
    :param suffix_types: A mapping between an index and the type of the suffix starting at that index.
    """
    # Only go over suffixes in the approximated suffix array, that have an L-Type suffix to their left:
    filtered_suffix_indices = filter(
        lambda i:
            approx_suffix_array[i] != -1 and  # Skip unrecorded suffixes
            approx_suffix_array[i] > 0 and  # Skip the suffix at index 0, it has no suffix to its left
            suffix_types[approx_suffix_array[i] - 1] is SuffixType.L,  # The suffix to the left is L-Type
        range(len(approx_suffix_array))
    )
    for approx_suffix_idx in filtered_suffix_indices:
        # Bucket sort the slices to the left of the recorded:
        left_suffix_idx = approx_suffix_array[approx_suffix_idx] - 1
        bucket_idx = data[left_suffix_idx]
        approx_suffix_array[bucket_heads[bucket_idx]] = left_suffix_idx

        # Increment the bucket head offset:
        bucket_heads[bucket_idx] += 1


def induce_sort_S(data: Union[list[int], bytes], approx_suffix_array: list[int], bucket_tails: list[int], suffix_types: list[SuffixType]) -> None:
    """
    Sorts the S-Type suffixes into their place in the approximated suffix array.
    :param data: The data suffixes are derived from.
    :param approx_suffix_array: The approximated suffix array, containing some suffix indices in their sorted place.
    :param bucket_tails: A mapping between each value in data and its corresponding bucket's index in the approximated
                         suffix array.
    :param suffix_types: A mapping between an index and the type of the suffix starting at that index.
    """
    # Only go over suffixes in the approximated suffix array, that have an S-Type suffix to their left:
    filtered_suffix_indices = filter(
        lambda i:
        approx_suffix_array[i] != -1 and  # Skip unrecorded suffixes
        approx_suffix_array[i] > 0 and  # Skip the suffix at index 0, it has no suffix to its left
        suffix_types[approx_suffix_array[i] - 1] is SuffixType.S,  # The suffix to the left is S-Type

        # Go over the indices from right to left this time:
        range(len(approx_suffix_array) - 1, -1, -1)
    )

    for approx_suffix_idx in filtered_suffix_indices:
        # Bucket sort the slices to the left of the recorded:
        left_suffix_idx = approx_suffix_array[approx_suffix_idx] - 1
        bucket_idx = data[left_suffix_idx]
        approx_suffix_array[bucket_tails[bucket_idx]] = left_suffix_idx

        # Decrement the bucket tail offset:
        bucket_tails[bucket_idx] -= 1


def get_lms_names(data: Union[list[int], bytes], approx_suffix_array: list[int], suffix_types: list[SuffixType]) -> tuple[list[int], int]:
    """
    After approximating the suffix array using induce_sort_S and induce_sort_L, this function goes over the LMS
    slices in the approximated array, gives each LMS substring an integer as a name, and returns a list
    mapping the start index of LMS slices to their name note that not all suffixes are LMS suffixes, and therefor will
    not receive a name. They will be marked with -1.
    Note that if two adjacent and equal LMS slices appear, they will be given the same name.
    Furthermore, since the names will later be used to create a summarized version of the data within a new alphabet,
    the function also returns the SIZE of the alphabet.
    Note also that indices where an LMS substring doesn't start will hold the value -1 in the returned mapping.
    :param data: Data the suffixes are derived from.
    :param approx_suffix_array: An approximated suffix array, having undergone induce_sort_S and induce_sort_L.
    :param suffix_types: A mapping between the start index of a suffix and the type of that suffix.
    :return: A list mapping the start indices of LMS slices to integer names, where indices without an LMS substring
             are mapped to -1, and the size of the new alphabet derived from those names.
    """
    # A mapping between LMS slices' names and the indices they start at (may contain missing values -1):
    lms_names: list[int] = [-1] * (len(data) + 1)

    # The first LMS substring we'll find will always be the empty suffix:
    current_name = 0
    last_lms_offset = approx_suffix_array[0]
    lms_names[last_lms_offset] = current_name

    # Find the other slices (ignore first index as we processed it already):
    lms_suffixes_offsets = filter(lambda offset: is_lms(suffix_types, offset), approx_suffix_array[1:])
    for suffix_offset in lms_suffixes_offsets:
        # Check if this LMS suffix is different from the previous one:
        if not are_lms_slices_equal(data, suffix_types, last_lms_offset, suffix_offset):
            current_name += 1

        # Record the new offset and store the (maybe changed) name:
        last_lms_offset = suffix_offset
        lms_names[suffix_offset] = current_name

    # New alphabet's size will be current_name + 1, since the smallest LMS suffix will be given the name 0:
    alphabet_size = current_name + 1
    return lms_names, alphabet_size


def summarize_suffix_array(lms_names: list[int]) -> tuple[list[int], list[int]]:
    """
    After mapping a unique name to each LMS suffix, the function summarizes information about the LMS suffixes into
    new data within a new alphabet in the following manner:
    1) The names of the non-missing LMS slices are collected and are considered the new data.
    2) The new alphabet is now shrunk to include the LMS names only.
    The function returns two lists: The first is the summarized data, and the second is a mapping between each name in
    the summarized data, and the start index of its corresponding LMS slice.
    :param lms_names: The names assigned to each LMS suffix, where indices which don't start with an LMS suffix are
                      marked with -1.
    :return: The data summary as a list of LMS slices' names, and a mapping between those names and the original start
             index of those slices.
    """
    # Form the summary and names-to-start-indices mapping:
    summary: list[int] = []
    names_to_start_indices: list[int] = []
    # Ignore missing values while still considering their indices (if there were 3 missing values before an actual
    # value, its index will still be 3 even if the first 3 indices weren't processed):
    for index, name in filter(lambda enumeration: enumeration[1] >= 0, enumerate(lms_names)):
        summary.append(name)
        names_to_start_indices.append(index)

    return summary, names_to_start_indices


def get_summary_suffix_array(summary_data: list[int], alphabet_size: int) -> list[int]:
    """
    Given a summary of some data, and the size of the alphabet used in the summary, the function returns the summary's
    sorted suffix array.
    :param summary_data: Summary of some data, whose sorted suffix array will be returned.
    :param alphabet_size: Size of the alphabet used in `summary_data`.
    :return: A sorted suffix array of `summary_data`.
    """
    # If the size of the summarized data is equal to its alphabet size, each suffix was used exactly once, so we can
    # just bucket sort it:
    if len(summary_data) == alphabet_size:
        summary_suffix_array: list[int] = [-1] * (alphabet_size + 1)
        summary_suffix_array[0] = len(summary_data)  # Empty suffix is always first
        for summary_index, summary_value in enumerate(summary_data):
            # Add 1 to summary value since 0 is always the empty suffix:
            summary_suffix_array[summary_value + 1] = summary_index
        return summary_suffix_array

    # If not, the summary data is more complicated so we will need to summarize it again recursively:
    return build_sorted_suffix_array(summary_data, alphabet_size)


def accurate_lms_suffixes_array(
        data: Union[list[int], bytes], bucket_tails: list[int], summary_suffix_array: list[int],
        lms_names_to_start_indices: list[int]
) -> list[int]:
    """
    Given the accurately sorted suffix array of the data's summary, the function accurately sorts the LMS suffixes in
    the upcoming sorted suffix array.
    The calculated value is the accurately sorted suffix array, where LMS suffixes are sorted, but any other suffix is
    marked with -1.
    :param data: The data was suffix array will be constructed.
    :param bucket_tails: A mapping between a data value and the last index of its associated bucket in the sorted suffix
                         array.
    :param summary_suffix_array: The suffix array of the data's summary.
    :param lms_names_to_start_indices: A mapping between the values inside `summary_suffix_array` and their
                                       corresponding suffix indices inside `data`.
    :return: The sorted suffix array for `data`, where only LMS suffixes are placed and others are missing (-1).
    """
    # Suffix array for all LMS suffixes, including the empty suffix:
    sorted_suffix_array = [-1] * (len(data) + 1)

    # First index of the summary suffix array is always the summary's empty suffix. The second is always OUR empty
    # suffix. Therefor, we need to bucket sort all indices but the first two:
    for i in range(len(summary_suffix_array) - 1, 1, -1):
        # Get the original suffix index from the summary:
        suffix_idx = lms_names_to_start_indices[summary_suffix_array[i]]

        # Bucket sort the original suffixes, with the same relative order of the summary:
        bucket_idx = data[suffix_idx]
        sorted_suffix_array[bucket_tails[bucket_idx]] = suffix_idx
        bucket_tails[bucket_idx] -= 1

    # Place the empty suffix first:
    sorted_suffix_array[0] = len(data)
    return sorted_suffix_array


def build_sorted_suffix_array(data: Union[list[int], bytes], alphabet_size: int = 256) -> list[int]:
    """
    Computes a sorted suffix array of `data` using the SA-IS algorithm.
    :param data: Some data whose sorted suffix array will be returned.
    :param alphabet_size: Size of the alphabet used within data, defaults to the byte's alphabet.
    :return: A sorted suffix array of `data`.
    """
    # Get the suffix types:
    suffix_types: list[SuffixType] = get_suffixes_types(data)

    # Compute bucket sizes for later bucket sorting operations:
    bucket_sizes: list[int] = compute_bucket_sizes(data, alphabet_size)
    bucket_heads: list[int] = buckets_head_indices(bucket_sizes)
    bucket_tails: list[int] = buckets_tail_indices(bucket_sizes)

    # As a first step, approximate the suffix array (copy bucket heads and tails since the functions will mutate them):
    approx_suffix_array = approximate_suffix_array(data, bucket_tails.copy(), suffix_types)

    # Use induced sorting to insert all non-LMS suffixes to the approximated suffix array:
    induce_sort_L(data, approx_suffix_array, bucket_heads.copy(), suffix_types)
    induce_sort_S(data, approx_suffix_array, bucket_tails.copy(), suffix_types)

    # Assign unique names to all LMS suffixes:
    lms_names, new_alphabet_size = get_lms_names(data, approx_suffix_array, suffix_types)

    # Summarize info about the LMS suffixes into new data and alphabet:
    summary_data, names_to_lms_indices = summarize_suffix_array(lms_names)

    # Get the sorted suffix array of the summary data:
    summary_suffix_array: list[int] = get_summary_suffix_array(summary_data, new_alphabet_size)

    # Sort LMS suffixes accurately:
    accurately_sorted_lms: list[int] = accurate_lms_suffixes_array(
        data, bucket_tails.copy(), summary_suffix_array, names_to_lms_indices
    )
    
    # Insert other non-LMS suffixes via induced sorting, don't copy bucket heads/tails as we won't use them anymore:
    induce_sort_L(data, accurately_sorted_lms, bucket_heads, suffix_types)
    induce_sort_S(data, accurately_sorted_lms, bucket_tails, suffix_types)
    
    return accurately_sorted_lms
