from enum import Enum
from transformations.mtf import compute_mtf, compute_inverse_mtf
from transformations.bwt import compute_bwt, compute_inverse_bwt


class Transformation(str, Enum):
    BWT = "BWT"
    MTF = "MTF"

    def encode_date(self, data: bytes) -> bytes:
        trs = {Transformation.BWT: compute_bwt, Transformation.MTF: compute_mtf}
        return trs[self](data)
    
    def decode_date(self, encoded_data: bytes) -> bytes:
        trs = {Transformation.BWT: compute_inverse_bwt, Transformation.MTF: compute_inverse_mtf}
        return trs[self](encoded_data)

    def help(self) -> str:
        if self is Transformation.BWT:
            return "Burrows-Wheeler transform, groups similar byte values together to increase compression efficiency"
        if self is Transformation.MTF:
            return \
                "Move-To-Front transform, replaces values with their index in an LRU cache, resulting in multiple zero bits for frequently repeating values"
