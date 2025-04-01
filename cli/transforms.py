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

from enum import Enum
from transformations.mtf import compute_mtf, compute_inverse_mtf
from transformations.bwt import compute_bwt, compute_inverse_bwt


class Transformation(str, Enum):
    BWT = "BWT"
    MTF = "MTF"

    def encode_data(self, data: bytes) -> bytes:
        trs = {Transformation.BWT: compute_bwt, Transformation.MTF: compute_mtf}
        return trs[self](data)
    
    def decode_data(self, encoded_data: bytes) -> bytes:
        trs = {Transformation.BWT: compute_inverse_bwt, Transformation.MTF: compute_inverse_mtf}
        return trs[self](encoded_data)

    def help(self) -> str:
        if self is Transformation.BWT:
            return "Burrows-Wheeler transform, groups similar byte values together to increase compression efficiency"
        if self is Transformation.MTF:
            return \
                "Move-To-Front transform, replaces values with their index in an LRU cache, resulting in multiple zero bits for frequently repeating values"
