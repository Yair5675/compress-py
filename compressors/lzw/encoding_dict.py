from compressors.lzw.memory_limits import TooManyEncodingsException

class EncodingDict:
    """
    A class representing the dictionary used in the encoding step of the LZW algorithm
    """

    # Error messages:
    __INVALID_DICT_SIZE_TYPE_MSG = 'Max dictionary size must be an integer'
    __INVALID_DICT_SIZE_VALUE_MSG = 'Max dictionary size must be a positive integer'
    __INVALID_QUERY_TYPE_MSG = 'LZW encoder dictionary can only be queried with bytes'
    __EMPTY_QUERY_MSG = 'LZW encoder dictionary cannot be queried with an empty bytes object'
    __SETTING_ASCII_KEYS_MSG = 'Single byte values cannot be changed'
    __INVALID_INDEX_TYPE_MSG = 'LZW encoder dictionary can only use int as a value'
    __QUERY_NOT_FOUND_MSG = "Byte slice '{}' was not saved in the dictionary"

    __slots__ = [
        # A Set holding every key created (optimizes key lookups):
        '__keys_set',

        # The smallest unoccupied index that we can insert to:
        '__unoccupied_idx',

        # The maximum amount of entries in the dictionary (apart from ascii values):
        '__max_size',

        # The multiple bytes values saved in the dictionary:
        '__encoded_values'
    ]

    def __init__(self, max_dict_size: int):
        # Validate type:
        if not isinstance(max_dict_size, int):
            raise TypeError(EncodingDict.__INVALID_DICT_SIZE_TYPE_MSG)
        elif max_dict_size <= 0:
            raise ValueError(EncodingDict.__INVALID_DICT_SIZE_VALUE_MSG)

        # Set the max size:
        self.__max_size = max_dict_size

        # Initialize stuff:
        self.__keys_set: set[bytes] = set()
        self.__unoccupied_idx: int = 256
        self.__encoded_values: dict[bytes, int] = {}

    def __getitem__(self, item: bytes) -> int:
        # Validate the query:
        EncodingDict.__validate_query(item)

        # Check if the item exists as a key:
        if not self.contains_key(item):
            raise KeyError(EncodingDict.__QUERY_NOT_FOUND_MSG.format(item))

        # If it's of length one, return its ascii value. If not, return the saved value:
        return ord(item) if len(item) == 1 else self.__encoded_values[item]

    def insert(self, key: bytes) -> bool:
        """
        Inserts a key into the dictionary. The index that the key will be mapped to will be
        the smallest unoccupied index found.
        If the key was already saved in the dictionary, nothing will change.
        :param key: The key that will be mapped to an index inside the dictionary.
        :return: True if the key was added, false otherwise.
        :raises TypeError: If the key isn't of type bytes
        :raises ValueError: If the key is of length 0.
        :raises TooManyEncodingsException: If, after the insertion of the key, the amount of entries
                                           will exceed the allowed amount.
        """
        # Validate key and make sure it isn't already saved:
        self.__validate_query(key)
        if self.contains_key(key):
            return False

        # Check if there is enough memory:
        if len(self) >= self.max_size:
            raise TooManyEncodingsException()

        # Insert the key:
        self.__encoded_values[key] = self.__unoccupied_idx
        self.__unoccupied_idx += 1
        self.__keys_set.add(key)

        return True

    def __len__(self):
        return len(self.__keys_set)

    def contains_key(self, key: bytes) -> bool:
        is_ascii_value = len(key) == 1 and ord(key) < 256
        return is_ascii_value or key in self.__keys_set

    def clear(self) -> None:
        """
        Deletes every single encoded slice saved in the dictionary, apart from ascii entries which are
        built-in.
        The maximum amount of entries that can be saved in the dictionary is not changed.
        """
        self.__unoccupied_idx = 256
        self.__keys_set.clear()
        self.__encoded_values.clear()

    @staticmethod
    def __validate_query(query) -> None:
        # The query must be a non-empty bytes object:
        if not isinstance(query, bytes):
            raise TypeError(EncodingDict.__INVALID_QUERY_TYPE_MSG)
        elif len(query) == 0:
            raise ValueError(EncodingDict.__EMPTY_QUERY_MSG)

    @property
    def max_size(self) -> int:
        """
        The maximum amount of entries the dictionary can contain, excluding built-in ascii entries.
        This value is final and cannot be changed.
        """
        return self.__max_size
