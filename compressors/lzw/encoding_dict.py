class TooManyEncodingsException(Exception):
    def __init__(self, message="The encoding dictionary reached its maximum size"):
        self.message = message
        super().__init__(message)


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

        # Initialize the key set:
        self.__keys_set: set[bytes] = set()

        # Set the dictionary:
        self.__encoded_values: dict[bytes, int] = {}

    def __getitem__(self, item: bytes) -> int:
        # Validate the query:
        EncodingDict.__validate_query(item)

        # Check if the item exists as a key:
        if not self.contains_key(item):
            raise KeyError(EncodingDict.__QUERY_NOT_FOUND_MSG.format(item))

        # If it's of length one, return its ascii value. If not, return the saved value:
        return ord(item) if len(item) == 1 else self.__encoded_values[item]

    def __setitem__(self, key: bytes, value: int) -> None:
        # Validate key (it's ok if it doesn't exist):
        self.__validate_query(key)

        # Add another limitation - single byte keys cannot be changed (as they are encoded to ascii values):
        if len(key) == 1:
            raise ValueError(EncodingDict.__SETTING_ASCII_KEYS_MSG)

        # Validate value (just needs to be an integer really):
        if not isinstance(value, int):
            raise TypeError(EncodingDict.__INVALID_INDEX_TYPE_MSG)

        # If it's a new value, check for size limitation:
        is_new_key = not self.contains_key(key)
        if len(self) >= self.max_size and is_new_key:
            raise TooManyEncodingsException()

        # Set the value:
        self.__encoded_values[key] = value

        # If it's a new key, add it to the set:
        if is_new_key:
            self.__keys_set.add(key)

    def __len__(self):
        return len(self.__keys_set)

    def contains_key(self, key: bytes) -> bool:
        # Type checking...
        EncodingDict.__validate_query(key)

        # NOW check:
        is_ascii_value = len(key) == 1 and ord(key) < 256
        return is_ascii_value or key in self.__keys_set

    def clear(self) -> None:
        """
        Deletes every single encoded slice saved in the dictionary, apart from ascii entries which are
        built-in.
        The maximum amount of entries that can be saved in the dictionary is not changed.
        """
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
