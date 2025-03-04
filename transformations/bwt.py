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
