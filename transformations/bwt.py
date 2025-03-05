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
