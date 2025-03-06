import util
from collections import deque
from queue import PriorityQueue
from util.bitbuffer import BitBuffer
from typing import Optional, Sequence
from compressors.huffman.encodings import HuffmanEncoding


class InvalidTreeFormat(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class HuffmanTree:
    """
    A binary tree used to assign short identifiers for characters (as usually done in huffman coding).
    """

    class Node:
        __slots__ = [
            # The byte value of the character that the Node represents. Only leaf nodes represent characters, so for
            # nodes that aren't leaves this value will be None:
            '__byte_val',

            # The frequency of the character that the Node represents inside the input data, or the sum of the
            # frequencies of the child nodes:
            '__freq',

            # The left and right children of the node (left is smaller, right is larger):
            '__left', '__right'
        ]

        def __init__(
                self, char: Optional[bytes], frequency: int, left: Optional['HuffmanTree.Node'],
                right: Optional['HuffmanTree.Node']
        ):
            # Assign to properties (type checking done automatically):
            self.char, self.frequency = char, frequency
            self.left, self.right = left, right

        def __eq__(self, other: 'HuffmanTree.Node') -> bool:
            if other is None:
                return False
            elif not isinstance(other, HuffmanTree.Node):
                return False
            else:
                return (self.char == other.char and self.frequency == other.frequency and self.right == other.right and
                        self.left == other.left)

        # Define 'less than' in order to use the Node class in a priority queue:
        def __lt__(self, other: 'HuffmanTree.Node') -> bool:
            return self.frequency < other.frequency

        def __repr__(self):
            if self.char is None:
                return str(self.left) + str(self.right)
            else:
                return chr(self.char[0])

        def is_leaf(self) -> bool:
            """
            Checks if the current node is a leaf node.
            :return: True if the current node has no children, False otherwise.
            """
            return self.left is None and self.right is None

        def get_leaves_count(self):
            """
            Calculates the number of leaves that the current node is connected to.
            :return: Number of leaves children of the current node.
            """
            return (
                    int(self.is_leaf()) +  # Current node
                    (self.left.get_leaves_count() if self.left else 0) +  # Left child
                    (self.right.get_leaves_count() if self.right else 0)  # Right child
            )

        @property
        def char(self) -> Optional[bytes]:
            """
            :return: The byte value of the character that the Node represents if it is a leaf node, or None if the Node
                     isn't a leaf node.
            """
            return self.__byte_val

        @char.setter
        def char(self, value: Optional[bytes]) -> None:
            # Type check:
            if value is not None and not isinstance(value, bytes):
                raise TypeError(f"Expected value of type 'bytes', or None, got {type(value)} instead")
            elif value is not None and len(value) != 1:
                raise ValueError(f"Expected a bytes object of length 1, got length {len(value)} instead")

            # NOW set the value:
            self.__byte_val: Optional[bytes] = value

        @property
        def frequency(self) -> int:
            """
            :return: The frequency of the character that the node represents in the input data. This is only true if
                     the current node is a leaf node. If not, the returned value is the sum of frequencies of the child
                     nodes.
            """
            return self.__freq

        @frequency.setter
        def frequency(self, value: int) -> None:
            if not isinstance(value, int):
                raise TypeError(f"Expected value of type 'int', got {type(value)} instead")
            elif value < 0:
                raise ValueError(f"Expected non-negative value, got {value} instead")

            self.__freq = value

        @property
        def left(self) -> Optional['HuffmanTree.Node']:
            """
            :return: The left child of the current node, or None if the current node is a leaf node.
            """
            return self.__left

        @left.setter
        def left(self, value: Optional['HuffmanTree.Node']) -> None:
            # Type check:
            if value is not None and not isinstance(value, HuffmanTree.Node):
                raise TypeError(f"Expected another HuffmanTree.Node object, or None, got {type(value)} instead")
            self.__left: Optional['HuffmanTree.Node'] = value

        @property
        def right(self) -> Optional['HuffmanTree.Node']:
            """
            :return: The right child of the current node, or None if the current node is a leaf node.
            """
            return self.__right

        @right.setter
        def right(self, value: Optional['HuffmanTree.Node']) -> None:
            # Type check:
            if value is not None and not isinstance(value, HuffmanTree.Node):
                raise TypeError(f"Expected another HuffmanTree.Node object, or None, got {type(value)} instead")
            self.__right: Optional['HuffmanTree.Node'] = value

    __slots__ = [
        # The root node of the huffman tree (an optional node):
        '__root',
    ]

    def __init__(self, byte_frequencies: Sequence[int]):
        """
        Constructs a HuffmanTree object using the given byte frequencies.
        :param byte_frequencies: A sequence of length 256, where each element at index 'i' is the frequency of the byte
                                 with value 'i' in the data.
        :raises ValueError: If the length of the sequence is not exactly 256, or if one of the frequencies is negative.
        """
        # Ensure the length is indeed 256:
        if len(byte_frequencies) != 256:
            raise ValueError(f"Expected a sequence of length 256, got {len(byte_frequencies)} instead")

        # Get a priority queue of nodes based on the frequencies:
        nodes_queue: PriorityQueue['HuffmanTree.Node'] = HuffmanTree.__get_nodes_priority_queue(byte_frequencies)

        # Merge every two least-frequent nodes until there's only one left:
        while nodes_queue.qsize() >= 2:
            # Construct a parent - left child will have a smaller frequency:
            a, b = nodes_queue.get_nowait(), nodes_queue.get_nowait()
            left = min(a, b)
            right = b if left is a else a
            parent = HuffmanTree.Node(None, left.frequency + right.frequency, left, right)

            # Return the parent to the queue:
            nodes_queue.put_nowait(parent)

        # Get the root (if all byte frequencies were zero, the queue is empty and the root is None):
        self.__root: Optional['HuffmanTree.Node'] = None if nodes_queue.empty() else nodes_queue.get_nowait()

    def get_encodings(self: 'HuffmanTree') -> dict[bytes, HuffmanEncoding]:
        """
        Given the current huffman tree, the method assigns each byte value inside it a huffman encoding - a potentially
        shorter value based on the structure of the tree.
        The returned dictionary uses the original byte values as keys, and the huffman encodings as values.
        :return: A dictionary mapping between the original byte values and the shorter huffman encodings that were
                 assigned to them. Since the huffman tree only refers to byte values, the maximum amount of entries in
                 the dictionary is 256.
        """
        # Create the dictionary:
        encodings: dict[bytes, HuffmanEncoding] = {}

        # Use recursion to find leaf nodes:
        def dfs(node: Optional[HuffmanTree.Node], code: int, depth: int):
            if node is not None:
                # if it's a leaf, assign an encoding:
                if node.is_leaf():
                    encodings[node.char] = HuffmanEncoding(depth, code)
                # If not, assign 0 to left and 1 to right:
                else:
                    dfs(node.left, code << 1, depth + 1)
                    dfs(node.right, (code << 1) | 1, depth + 1)

        dfs(self.root, 0, 1)
        return encodings

    def to_bits(self) -> BitBuffer:
        """
        When using the huffman tree, one might want to include it along with any data compressed using it. Therefor,
        this method encodes the tree in the most memory efficient way possible.
        :return: A BitBuffer object containing the serialized huffman tree.
        """
        # Initialize the buffer:
        output = BitBuffer()

        # Ensure root isn't None:
        if self.root is None:
            return output

        # Insert the number of leaves in the tree (minus one) as the first byte:
        output.insert_bits(self.root.get_leaves_count() - 1, 8)

        # Encode the tree using preorder traversal. Encode the byte value of the node (if it is a leaf node) or 0 if it
        # isn't, then another two bits for the two possible children. 0 means no child, 1 means a child exists.
        def preorder(current_node: Optional['HuffmanTree.Node']):
            if current_node is not None:
                # If it's a leaf, output the byte value and 00:
                if current_node.is_leaf():
                    output.insert_bits(current_node.char[0], 8)
                    output.insert_bits(0, 2)
                # If it isn't, place 0 instead of the actual byte value, and 1 or 0 for possible children:
                else:
                    output.insert_bits(0, 8)
                    output.insert_bits(int(current_node.left is not None), 1)  # Left child
                    output.insert_bits(int(current_node.right is not None), 1)  # Right child

                    # Continue to the next:
                    preorder(current_node.left)
                    preorder(current_node.right)

        preorder(self.root)
        return output

    @staticmethod
    def __parse_nodes_data(compressed_data: bytes) -> tuple[list[tuple['HuffmanTree.Node', bool, bool]], int]:
        """
        Given data which whose start is the 'to_bits' method result, this method parses it into information about the
        encoded Huffman tree's nodes.
        Specifically, the function returns a list where every element in that list is the following:
            (the node's value: int, left child exists: bool, right child exists: bool)
        Note that this list represents a preorder traversal of the tree.
        Additionally, the function returns the index of the first bit which WASN'T used in the creation of this list.
        That index should be considered the data start index.
        :param compressed_data: Data prefixed by the result of the 'to_bits' method.
        :return: A list of node information and the data start index.
        """        
        if len(compressed_data) == 0:
            return []
        
        nodes_info: list[tuple['HuffmanTree.Node', bool, bool]] = []
        leaves_count = compressed_data[0] + 1
        bit_offset = 8
        
        node_space = 10  # Number of bits a single node takes up
        while leaves_count > 0 and bit_offset + node_space <= 8 * len(compressed_data):
            # Read node's info:
            value = util.read_bits(compressed_data, bit_offset, 8)
            bit_offset += 8
            has_left, has_right = util.get_bit(compressed_data, bit_offset), util.get_bit(compressed_data, bit_offset + 1)
            bit_offset += 2
            
            # Append node and decrease the number of leaves remaining if necessary:
            nodes_info.append((HuffmanTree.Node(bytes([value]), 0, None, None), has_left, has_right))
            leaves_count -= 1 - (has_left | has_right)
        
        # If not all leaves were found, we have invalid data:
        if leaves_count > 0:
            raise InvalidTreeFormat(f"Expected {compressed_data[0]} leaves to be found, got {compressed_data[0] - leaves_count} instead")
        
        return nodes_info, bit_offset
    
    @staticmethod
    def __form_root_node(nodes_info: list[tuple['HuffmanTree.Node', bool, bool]]) -> 'HuffmanTree.Node':
        """
        Given a list of information about a HuffmanTree's nodes in preorder traversal, the method reconstructs the 
        tree's structure and returns its root node, which is connected to the fully reconstructed tree.
        :param nodes_info: A list with information about each node in the tree. It is expected that this information
                           was recorded in preorder traversal of the tree. Each element in the list is the following:   
                            (the node itself, whether the node had a left child, whether the node had a right child)
        :return: The root node of a HuffmanTree, constructed according to the given nodes' information.
        """
        # Start the tree with a dummy node:
        dummy = HuffmanTree.Node(None, 0, None, None)
        nodes_info.insert(0, (dummy, True, False))  # The actual tree will be the left child of dummy

        parents_idx_stack: deque[HuffmanTree.Node] = deque()
        parents_idx_stack.append(0)

        for node_idx, (current_node, has_left, has_right) in enumerate(nodes_info[1:], start=1):
            # Check if the stack is empty at this point — if so, raise an exception:
            if not parents_idx_stack:
                raise InvalidTreeFormat("Unexpectedly ran out of parent nodes. The tree structure is malformed.")

            # Get parent info:
            parent_node, parent_has_left, parent_has_right = nodes_info[parents_idx_stack[0]]

            # Insert current node to either left or right of parent:
            if parent_has_left and parent_node.left is None:
                parent_node.left = current_node
                # If we set the left child, we remove the parent only if we don't need to set the right child:
                remove_parent = not parent_has_right

            elif parent_has_right:
                parent_node.right = current_node
                # If we set the right child, we either didn't need to set the left one or did already:
                remove_parent = True

            # Remove parent from the stack if they don't need more children:
            if remove_parent:
                parents_idx_stack.popleft()

            # Add the current node's index to the parents stack only if it has children:
            if has_left or has_right:
                parents_idx_stack.appendleft(node_idx)

        # Remove dummy:
        root = dummy.left
        dummy.left = None
        return root

    @staticmethod
    def from_bits(compressed_data: bytes) -> tuple['HuffmanTree', int]:
        """
        Given some compressed data, the method constructs a HuffmanTree object from it.
        The data is expected to start with the output of the 'to_bits' method, any other format will result in a
        nonsensical tree at best, or an exception at worst.
        The method won't necessarily parse the entire data. Once the tree was fully constructed, the index of the first
        bit which doesn't belong to the tree's serialization will be returned, along with the tree itself.
        :return: The tree deserialized from the data, and the data start index.
        """
        # Parse the info:
        nodes_info, data_start = HuffmanTree.__parse_nodes_data(compressed_data)
        
        # Get the root node:
        root = HuffmanTree.__form_root_node(nodes_info)
        
        # Construct the tree object:
        tree = HuffmanTree.__new__(HuffmanTree)
        tree.__root = root
        return tree, data_start

    @property
    def root(self) -> Optional['HuffmanTree.Node']:
        """
        :return: The root node of the huffman tree. If the tree is empty, None is returned.
        """
        return self.__root

    @staticmethod
    def __get_nodes_priority_queue(byte_frequencies: Sequence[int]) -> PriorityQueue['HuffmanTree.Node']:
        # Insert all byte values whose frequency isn't 0 into a priority queue. The queue will be sorted based on the
        # frequency of the byte value:
        nodes: PriorityQueue['HuffmanTree.Node'] = PriorityQueue(maxsize=256)
        for byte_val, byte_freq in enumerate(byte_frequencies):
            if byte_freq != 0:
                node = HuffmanTree.Node(bytes([byte_val]), byte_freq, None, None)
                nodes.put_nowait(node)
        return nodes
