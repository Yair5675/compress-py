import os
import pytest
from collections import deque
from cli.lzw import DictionarySize
from compressors import Compressor
from compressors.lzw import LzwCompressor
from compressors.rle import RleCompressor
from compressors.huffman import HuffmanCompressor
from compressors.lzw.memory_limits import OutOfMemoryStrategy

# Directory holding test files:
TESTS_DIR: str = "testfiles"


@pytest.fixture
def example_files_content() -> deque[bytes]:
    file_contents: deque[bytes] = deque()

    for filename in os.listdir(TESTS_DIR):
        with open(os.path.join(TESTS_DIR, filename), 'rb') as current_file:
            file_contents.append(current_file.read())

    return file_contents


@pytest.mark.parametrize('compressor_name, compressor', [
    ('Huffman', HuffmanCompressor()),

    ('RLE', RleCompressor()),

    ('LZW unlimited memory', LzwCompressor(int(DictionarySize.EXTRA_LARGE), OutOfMemoryStrategy.USE_MINIMUM_REQUIRED)),
    ('LZW extra large memory', LzwCompressor(int(DictionarySize.EXTRA_LARGE), OutOfMemoryStrategy.STOP_STORE)),
    ('LZW large memory', LzwCompressor(int(DictionarySize.LARGE), OutOfMemoryStrategy.STOP_STORE)),
    ('LZW medium memory', LzwCompressor(int(DictionarySize.MEDIUM), OutOfMemoryStrategy.STOP_STORE)),
    ('LZW small memory', LzwCompressor(int(DictionarySize.SMALL), OutOfMemoryStrategy.STOP_STORE))
])
def test_functionality(compressor_name: str, compressor: Compressor, example_files_content: deque[bytes]) -> None:
    for content in example_files_content:
        encoded_content: bytes = compressor.encode(content)
        decoded_content: bytes = compressor.decode(encoded_content)
        assert content == decoded_content
