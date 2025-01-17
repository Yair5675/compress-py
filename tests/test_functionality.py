import os
import unittest
from typing import Union, Any
from cli.lzw import DictionarySize
from compressors import Compressor
from parameterized import parameterized
from compressors.lzw import LzwCompressor
from compressors.rle import RleCompressor
from compressors.huffman import HuffmanCompressor
from compressors.lzw.memory_limits import OutOfMemoryStrategy

# Directory holding test files:
TESTS_DIR: str = "testfiles"


class MockCompressor(Compressor):
    __slots__ = (
        'last_encoded',
    )

    def encode(self, input_data: bytes) -> bytes:
        self.last_encoded = input_data
        return None

    def decode(self, compressed_data: bytes) -> bytes:
        return self.last_encoded


class TestFunctionalityBase(unittest.TestCase):
    """
    High level tests - making sure original data is the same as the decompressed result of each algorithm.
    Test files were taken from: https://corpus.canterbury.ac.nz/descriptions/, specifically "The Canterbury Corpus".
    Other corpora may be added in a future commit.
    """
    __slots__ = (
        # Content of test files:
        'file_contents',
    )

    @classmethod
    def setUpClass(cls):
        cls.file_contents: list[bytes] = []

        for filename in os.listdir(TESTS_DIR):
            with open(os.path.join(TESTS_DIR, filename), 'rb') as current_file:
                cls.file_contents.append(current_file.read())

    @classmethod
    def tearDownClass(cls):
        cls.file_contents = None

    def get_compressor(self, config: Any) -> Compressor:
        """
        Gets the compressor of the current test class. MUST be overridden.
        :param config: Additional info that the test may need to decide which compressor it uses.
        """
        # For the base class, just return an object that returns the last thing it was required to encode:
        return MockCompressor()

    def test_functionality(self, config_name: str = "default config", config: Any = None):
        for contents in self.file_contents:
            self.validate_compressor_result(contents, config)

    def validate_compressor_result(self, org_data: bytes, config: Any) -> None:
        compressor = self.get_compressor(config)

        encoded_data: bytes = compressor.encode(org_data)
        decoded_data: bytes = compressor.decode(encoded_data)

        self.assertEqual(decoded_data, org_data)


class TestFunctionalityHuffman(TestFunctionalityBase):
    def get_compressor(self, config=None) -> Compressor:
        return HuffmanCompressor()


class TestFunctionalityLZW(TestFunctionalityBase):
    # Config is max dictionary size (custom or predetermined) and strategy for running out of memory
    def get_compressor(self, config: tuple[Union[int, DictionarySize], OutOfMemoryStrategy]) -> Compressor:
        if (dict_size := int(config[0])) <= 0:
            raise ValueError("Invalid dictionary size in tests")

        return LzwCompressor(dict_size, config[1])

    @parameterized.expand(input=[
        ("Best compression (no stopper)", (DictionarySize.EXTRA_LARGE, OutOfMemoryStrategy.USE_MINIMUM_REQUIRED)),
        ("Extra large memory", (DictionarySize.EXTRA_LARGE, OutOfMemoryStrategy.STOP_STORE)),
        ("Large memory", (DictionarySize.LARGE, OutOfMemoryStrategy.STOP_STORE)),
        ("Small memory", (DictionarySize.SMALL, OutOfMemoryStrategy.STOP_STORE)),
        ("Medium memory", (DictionarySize.MEDIUM, OutOfMemoryStrategy.STOP_STORE)),
    ])
    def test_functionality(self, config_name: str = "default config", config=None):
        # Override with parameterized to test all LZW configurations:
        super().test_functionality(config_name, config)


class TestFunctionalityRLE(TestFunctionalityBase):
    def get_compressor(self, config: None) -> Compressor:
        return RleCompressor()


if __name__ == '__main__':
    unittest.main()
