from typing import Optional
import transformations.suffix_arr as suffix_arr


# The EOF character separating between the blocks' various EOF values and the blocks themselves:
METADATA_EOF: int = 0


class BWTBlock:
    __slots__ = (
        # Byte data stored in the block
        'data',
        # The EOF character in this particular block:
        'eof'
    )
    # Maximum number of bytes in the block. Has to be 254 to ensure there are always 2 values which don't appear in the
    # data, and one of them is NOT the external EOF character (used by the whole file):
    MAX_BLOCK_SIZE: int = 254
    
    # Set of all byte values, pre-computed:
    __BYTE_VALUES_SET: set[int] = set(range(256))

    def __init__(self, data: bytes, external_eof: Optional[int] = None) -> 'BWTBlock':
        if len(data) > BWTBlock.MAX_BLOCK_SIZE:
            raise ValueError(f"Data size must be less than or equal to {BWTBlock.MAX_BLOCK_SIZE} ({len(data)} given)")
        self.data: bytes = data

        # Find all missing values, and pick the one that isn't the external EOF as the block's EOF:
        missing: set[int] = BWTBlock.__BYTE_VALUES_SET - set(data)

        # Since there are 256 possible byte values, and at most 254 of them are in the data, it is guaranteed that at
        # least 2 unique values are missing:
        m1, m2 = missing.pop(), missing.pop()
        self.eof: int = m1 if external_eof is None or m2 == external_eof else m2

    def __len__(self) -> int:
        return len(self.data)

    def get_bwt(self) -> bytes:
        """
        Computes the BWT of the current block.
        """
        # Initialize a bytearray whose length is equal to the block's length:
        result = bytearray(len(self) + 1)

        # Form the suffix array, and shrink the alphabet size to include only the block's length excluding EOF:
        suffix_array: list[int] = suffix_arr.build_sorted_suffix_array(self.data)

        # Use the indices inside the suffix array to get the last value of data's rotation to that index:
        for byte_idx, sorted_suffix_offset in enumerate(suffix_array):
            if sorted_suffix_offset > 0:
                result[byte_idx] = self.data[sorted_suffix_offset - 1]
            else:
                result[byte_idx] = self.eof
        return bytes(result)


def compute_bwt(data: bytes) -> bytes:
    """
    Performs the Burrows-Wheeler transform on the data. The transformation will add some metadata to successfully
    reconstruct it later.
    Note that the BWT isn't performed for the entire data at once, but instead on chunks of the data.
    :param data: Some data whose BWT will be calculated.
    :return: The Burrows-Wheeler transform of the data.
    """
    # Break the data into blocks:
    blocks: list[BWTBlock] = [
        BWTBlock(data[i:i + BWTBlock.MAX_BLOCK_SIZE], external_eof=METADATA_EOF) for i in
        range(0, len(data), BWTBlock.MAX_BLOCK_SIZE)
    ]

    # Result length calculation is as follows -
    # Let N be the number of blocks, and D be a list where the ith element is the length of the ith block.
    # Total length is the sum of:
    # 1) EOFs for each block, each one byte long - N * 1 = N
    # 2) One metadata EOF - 1
    # 3) Every block's transformation, where each transformation's length is D[i] plus 1 internal EOF -
    #    D[i] + 1 for i in [0, N) = sum(D) + N
    #    Since the sum of every block's length is equal to the length of the total data, we can use that to save 
    #    computation.
    # In total: N + 1 + len(data) + N = 1 + 2N + len(data)
    N = len(blocks)
    total_D = len(data)
    result: bytearray = bytearray(1 + (N << 1) + total_D)

    # Insert the blocks' EOFs to the start of the array, and their BWT to the data section of the array:
    blocks_data_pointer = N + 1  # First non-metadata index
    for block_idx, block in enumerate(blocks):
        result[block_idx] = block.eof

        bwt: bytes = block.get_bwt()
        transform_len = len(bwt)
        result[blocks_data_pointer:blocks_data_pointer + transform_len] = bwt

        blocks_data_pointer += transform_len

    # Insert the metadata EOF:
    result[N] = METADATA_EOF
    return bytes(result)
