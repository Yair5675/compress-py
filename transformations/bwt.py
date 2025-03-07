import transformations.suffix_arr as suffix_arr


def find_missing_byte_val(byte_values: bytes) -> int:
    """
    Given a collection of bytes whose length is at most 255, the function returns a byte value not present within the
    given bytes.
    Such value ought to exists, as there are 256 possible byte values yet the given bytes' length is at most 255.
    :param byte_values: A collection of bytes, the returned value will not be contained in this collection. Its length
                        is at most 255.
    :return: A byte value not present within `byte_values`.
    """
    # Check length:
    if len(byte_values) > 255:
        raise ValueError(f"Length of given bytes must be less than 256 ({len(byte_values)} given)")

    # Initialize an INTEGER B with 256 bytes which are all 1:
    B: int = (1 << 256) - 1

    for byte_val in byte_values:
        # Use the byte value as an offset from the least significant bit of B and get the bit at that offset:
        b = (B >> byte_val) & 1

        # Turn this bit into 0 in B:
        B ^= b << byte_val

    # Use int.bit_length() to get the offset of the most significant bit in B which is still a 1 (there must be at least
    # one due to byte_values' length constraints:
    return B.bit_length() - 1


def get_bwt_metadata(eof_offset: int) -> bytearray:
    """
    Given the offset of the EOF character inside the transformation, the function returns the necessary metadata to
    allow the inverse algorithm to reconstruct the original data.
    :param eof_offset: The offset of the EOF character inside the transformation. This offset is assumed to be less than
                        2 to the 2040 power (which I think is a fair request).
    :return: Metadata which should be added before the transformation, without any delimiter in between.
    """
    # The metadata will be structured as follows:
    # 1) Assuming the EOF index we need to store is smaller than 2 ** (8 * 255), it can be represented using 255 bytes
    #    or fewer.
    # 2) Due to this assumption, there will always be at least one byte value which does not appear in the EOF index's
    #    bytes (as mentioned, it is composed of at most 255 bytes, and there are 256 unique byte values).
    # 3) Call this unique byte value that does not appear in the EOF index M. Place M as the first byte of the message
    #    to let the inverse algorithm know what the metadata EOF is.
    # 4) Follow the first M with the EOF index's bytes (big endian), and insert M at the end again to signal the index's
    #    end.
    # This approach supports gigantic file sizes. Even if the base assumption limits the file size, it limits it to such
    # an enormous number we should never realistically break it.
    # Moreover, this approach allows us to transmit the EOF index through the data with constant memory addition (at
    # the worst case, 257 bytes are added, but in such a case this amount is dwarfed by the data's size anyway).
    eof_index_bytes: bytes = eof_offset.to_bytes((eof_offset.bit_length() + 7) // 8, byteorder='big')
    missing_byte_val: int = find_missing_byte_val(eof_index_bytes)

    metadata: bytearray = bytearray(2 + len(eof_index_bytes))
    metadata[0], metadata[-1] = missing_byte_val, missing_byte_val
    metadata[1:-1] = eof_index_bytes

    return metadata


def compute_bwt(data: bytes) -> bytes:
    """
    Performs the Burrows-Wheeler transform on the data. The transformation will add some metadata to successfully
    reconstruct it later.
    Note that the BWT isn't performed for the entire data at once, but instead on chunks of the data.
    :param data: Some data whose BWT will be calculated.
    :return: The Burrows-Wheeler transform of the data.
    """
    # If the data is empty return empty bytes:
    if len(data) == 0:
        return b''

    # Compute suffix array of the data:
    sorted_suffix_array = suffix_arr.build_sorted_suffix_array(data)

    # Compute the BWT of the data WITHOUT adding an EOF, however remember where an EOF should be:
    eof_idx: int = None
    bwt: bytearray = bytearray(len(data))
    for byte_idx, sorted_suffix_offset in enumerate(sorted_suffix_array):
        # If an EOF was found, we skipped an index since we didn't insert it:
        if sorted_suffix_offset > 0:
            bwt[byte_idx - int(eof_idx is not None)] = data[sorted_suffix_offset - 1]
        else:
            eof_idx = byte_idx

    # Add the BWT plus metadata:
    return b''.join((get_bwt_metadata(eof_idx), bwt))


def get_eof_offset(bwt_data: bytes) -> tuple[int, int]:
    """
    Given the result of the `compute_bwt` function, this function extracts the offset of the EOF relative to the start
    of the data from the metadata.
    Additionally, it returns the offset relative to the beginning of the file at which the actual BWT data starts.
    :param bwt_data: BWT of some data along with metadata, the result of a call to `compute_bwt`.
    :return: A tuple containing the EOF's offset relative to the data's start offset, and the data's start offset.
    """
    # If the data is empty, something's not right:
    if len(bwt_data) == 0:
        raise ValueError(f"Cannot extract EOF's offset from nothing")

    # Get the metadata delimiter from the first byte:
    delimiter = bwt_data[0]
    data_ptr = 1
    eof_idx = 0

    while data_ptr < len(bwt_data) and data_ptr < 256:  # EOF's offset is at most 255 bytes long
        # We reached the end of the EOF index:
        if bwt_data[data_ptr] == delimiter:
            break

        # If not, add the current byte and increment the data pointer:
        eof_idx = (eof_idx << 8) | bwt_data[data_ptr]
        data_ptr += 1
    # We didn't break - which means a closing delimiter was not found before the 256 byte or the end of the file:
    else:
        message = "Data ended before metadata EOF was found" if data_ptr >= len(bwt_data) else \
            "Missing metadata EOF, over 255 bytes were read and no delimiter was found"
        raise ValueError(message)

    # If we did break, make sure we processed at least one byte:
    if data_ptr == 1:
        raise ValueError("0 bytes dedicated to EOF index in metadata")
    return eof_idx, data_ptr + 1  # data_ptr currently points to a delimiter


def compute_inverse_bwt(bwt_data: bytes) -> bytes:
    """
    Inverses the Burrows-Wheeler transformation and returns the original data, stripped of any metadata attached to it
    """
    if len(bwt_data) == 0:
        return b''

    # Extract EOF offset from metadata and set a pointer to the BWT's start
    eof_offset, data_ptr = get_eof_offset(bwt_data)

    # Check there are enough bytes in the data:
    if data_ptr + eof_offset > len(bwt_data):  # Since EOF is not actually in the data, it can be equal to len(bwt_data)
        raise ValueError(f"Invalid EOF offset: Data is too small for offset {eof_offset} (data's size is {len(bwt_data) - data_ptr})")

    # Construct a list of (byte, index) pairs, where indices larger than or equal to eof_offset are incremented by 1
    # since the data doesn't actually include the EOF:
    byte_index_pairs = [(byte, index + int(index >= eof_offset)) for index, byte in enumerate(bwt_data[data_ptr:])]

    # Sort the pairs first based on the byte, and then based on the index:
    byte_index_pairs.sort()

    # Add an element to the start that represents the EOF to align all indices:
    byte_index_pairs.insert(0, (None, eof_offset))

    # Treat the pairs list as a linked list, where the index stored in each tuple is the next node to be processed. The
    # start node will be the tuple that, after sorting, is at index eof_offset:
    current_tuple: tuple[int, int] = byte_index_pairs[eof_offset]
    org_data: bytearray = bytearray(len(bwt_data) - data_ptr)
    org_data_offset = 0
    
    # Continue until reaching the EOF:
    while current_tuple[0] is not None:
        org_data[org_data_offset] = current_tuple[0]
        org_data_offset += 1

        current_tuple = byte_index_pairs[current_tuple[1]]

    # If not all nodes were processed, the data was tampered with/malformed:
    if org_data_offset < len(org_data):
        raise ValueError("Malformed data: An incomplete closed loop was created from BWT data")
    return bytes(org_data)
