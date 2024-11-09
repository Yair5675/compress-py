from queue import PriorityQueue
from typing import Optional, Sequence
from compressors.huffman.identifiers import HuffmanEncoding


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

        # Define 'less than' in order to use the Node class in a priority queue:
        def __lt__(self, other: 'HuffmanTree.Node') -> bool:
            return self.frequency < other.frequency

        def __str__(self):
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

    def get_encodings(self: 'HuffmanTree') -> dict[bytes, int]:
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

        dfs(self.root, 0, 0)
        return encodings

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
