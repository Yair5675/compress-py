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

from typing import Optional
from collections.abc import Iterable


class MTFAlphabet:
    """
    A class representing the alphabet in the MTF transform, allows for efficient movement of byte values to the start
    of the 'recently used' values.
    """
    __slots__ = (
        # Linked list of nodes where each node represents a byte value:
        'recently_used',
    )
    
    def __init__(self, alphabet: Iterable[int] = range(256)) -> 'MTFAlphabet':
        # Construct linked list:
        self.recently_used = ptr = MTFAlphabet.Node(None, None)
        for val in alphabet:
            ptr.next_node = MTFAlphabet.Node(val, None)
            ptr = ptr.next_node
        
        # Disconnect dummy node:
        ptr = self.recently_used.next_node
        self.recently_used.next_node = None
        self.recently_used = ptr
        
    def __getitem__(self, i: int) -> int:
        """
        Returns the ith recently used byte value.
        """
        ptr = self.recently_used
        for _ in range(i):
            ptr = ptr.next_node
        return ptr.byte_val
    
    def get_val_and_update(self, i: int) -> int:
        """
        Returns the ith recently used byte value, while also moving it to the start of the alphabet.
        """
        # If the index is 0, nothing needs to be moved and we can just return the value:
        if i == 0:
            return self.recently_used.byte_val
        
        # Iterate over the nodes (use a dummy node to stop before the actual node we seek):
        dummy = ptr = MTFAlphabet.Node(None, self.recently_used)
        for _ in range(i):
            ptr = ptr.next_node
        
        # Move the node after ptr as the new head:
        new_head = ptr.next_node
        ptr.next_node = new_head.next_node
        new_head.next_node = self.recently_used
        self.recently_used = new_head
        
        # Disconnect dummy:
        dummy.next_node = None
        
        # Return the value:
        return self.recently_used.byte_val
    
    def get_val_idx(self, val: int) -> int:
        """
        Given some value in the alphabet, the index of that value is returned and internally updated to be the first
        index.
        :param val: Some value in the alphabet.
        :return: The old index of value in the alphabet.
        """
        # Iterate over the nodes (use a dummy node to stop before the actual node we seek):
        idx = 0
        dummy = ptr = MTFAlphabet.Node(val, self.recently_used)
        while ptr.next_node is not None and ptr.next_node.byte_val != val:
            ptr = ptr.next_node
            idx += 1
        
        # If we didn't find anything return -1, if we did move the node to the start of the list:
        if ptr.next_node is None:
            dummy.next_node = None
            return -1
        
        # Since dummy's value is already the sought value AND it is already the new head, just disconnect the old node:
        remove = ptr.next_node
        ptr.next_node = remove.next_node
        remove.next_node = None
        
        # And finally set dummy as the new head:
        self.recently_used = dummy
        return idx
    
    def __repr__(self) -> str:
        return repr(self.recently_used)
    
    class Node:
        __slots__ = (
            # Byte value of the current node:
            'byte_val',
            # The next node (or none if there's no next node):
            'next_node'
        )
        
        def __init__(self, val: int, next_node: Optional['MTFAlphabet.Node']) -> 'MTFAlphabet.Node':
            self.byte_val: int = val
            self.next_node: Optional[MTFAlphabet.Node] = next_node
            
        def __repr__(self) -> str:
            return f"{self.byte_val}->{repr(self.next_node)}"


def compute_mtf(data: bytes) -> bytes:
    """
    Computes the Move-To-Front transform of data.
    """
    # Post-transform length is equal to pre-transform length (no metadata):
    result: bytearray = bytearray(len(data))
    
    # Initialize alphabet:
    alphabet = MTFAlphabet()
    
    # For each byte, query the alphabet:
    for i, byte in enumerate(data):
        result[i] = alphabet.get_val_idx(byte)
    
    return bytes(result)


def compute_inverse_mtf(mtf_data: bytes) -> bytes:
    """
    Computes the inverse of the Move-To-Front transform.
    """
    # Post-transform length is equal to pre-transform length (no metadata):
    result: bytearray = bytearray(len(mtf_data))

    # Initialize alphabet:
    alphabet = MTFAlphabet()

    # For each byte, use the index to get the original byte AND update the alphabet 
    for i, mtf_idx in enumerate(mtf_data):
        result[i] = alphabet.get_val_and_update(mtf_idx)

    return bytes(result)
