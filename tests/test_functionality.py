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

import os
import pytest
import random
from collections import deque
from cli.lzw import DictionarySize
from compressors import Compressor
from cli.transforms import Transformation
from compressors.lzw import LzwCompressor
from compressors.rle import RleCompressor
from compressors.huffman import HuffmanCompressor
from compressors.lzw.memory_limits import OutOfMemoryStrategy

# Directory holding test files:
TESTS_DIR: str = "testfiles"


@pytest.fixture
def example_files_content() -> deque[bytes]:
    file_contents: deque[bytes] = deque()
    chosen_tests = random.sample(os.listdir(TESTS_DIR), 5)

    for filename in chosen_tests:
        with open(os.path.join(TESTS_DIR, filename), 'rb') as current_file:
            file_contents.append(current_file.read())

    return file_contents


def transform_data(data: bytes, transformations: list[Transformation], inverse: bool) -> bytes:
    for t in reversed(transformations) if inverse else transformations:
        data = t.decode_date(data) if inverse else t.encode_date(data)
    return data


@pytest.mark.parametrize('compressor_name, compressor, transforms', [
    ('Huffman', HuffmanCompressor(), []),

    ('RLE', RleCompressor(), []),

    ('LZW unlimited memory', LzwCompressor(int(DictionarySize.EXTRA_LARGE), OutOfMemoryStrategy.USE_MINIMUM_REQUIRED), []),
    ('LZW extra large memory', LzwCompressor(int(DictionarySize.EXTRA_LARGE), OutOfMemoryStrategy.STOP_STORE), []),
    ('LZW large memory', LzwCompressor(int(DictionarySize.LARGE), OutOfMemoryStrategy.STOP_STORE), []),
    ('LZW medium memory', LzwCompressor(int(DictionarySize.MEDIUM), OutOfMemoryStrategy.STOP_STORE), []),
    ('LZW small memory', LzwCompressor(int(DictionarySize.SMALL), OutOfMemoryStrategy.STOP_STORE), []),
    
    ('Huffman BWT + MTF', HuffmanCompressor(), [Transformation.BWT, Transformation.MTF]),

    ('RLE BWT + MTF', RleCompressor(), [Transformation.BWT, Transformation.MTF]),

    ('LZW unlimited memory BWT + MTF', LzwCompressor(int(DictionarySize.EXTRA_LARGE), OutOfMemoryStrategy.USE_MINIMUM_REQUIRED), [Transformation.BWT, Transformation.MTF]),
    ('LZW extra large memory BWT + MTF', LzwCompressor(int(DictionarySize.EXTRA_LARGE), OutOfMemoryStrategy.STOP_STORE), [Transformation.BWT, Transformation.MTF]),
    ('LZW large memory BWT + MTF', LzwCompressor(int(DictionarySize.LARGE), OutOfMemoryStrategy.STOP_STORE), [Transformation.BWT, Transformation.MTF]),
    ('LZW medium memory BWT + MTF', LzwCompressor(int(DictionarySize.MEDIUM), OutOfMemoryStrategy.STOP_STORE), [Transformation.BWT, Transformation.MTF]),
    ('LZW small memory BWT + MTF', LzwCompressor(int(DictionarySize.SMALL), OutOfMemoryStrategy.STOP_STORE), [Transformation.BWT, Transformation.MTF]),
])
def test_functionality(compressor_name: str, compressor: Compressor, transforms: list[Transformation], 
                       example_files_content: deque[bytes]) -> None:
    for content in example_files_content:
        t_content = transform_data(content, transforms, inverse=False)
        
        encoded_content: bytes = compressor.encode(t_content)
        decoded_content: bytes = compressor.decode(encoded_content)
        decoded_content = transform_data(decoded_content, transforms, inverse=True)
        
        assert content == decoded_content
