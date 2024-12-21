class FenwickTree:
    __slots__ = (
        # The list storing the actual data:
        '__data',
    )

    def __init__(self, values: list[int]) -> 'FenwickTree':
        """
        Creates a Fenwick tree from the given data.
        :param values: The values that will be stored in the Fenwick tree.
        """
        # Initialize data to hold all elements of `value` plus one. It allows us to index elements starting with 1,
        # which makes index calculations easier later:
        self.__data = [0] * (len(values) + 1)

        for i in range(1, len(self.__data)):
            # Copy the value from `values`:
            self.__data[i] = values[i - 1]

            # Add it to the parent element:
            parent_idx = i + (i & -i)
            if parent_idx < len(self.__data):
                self.__data[parent_idx] += self.__data[i]

    def get_sum(self, end_idx: int) -> int:
        """
        Calculates the sum of all elements up to `end_idx` in O(log(n)).
        :param end_idx: The method will sum the elements from index 0 up to (but not including) this index.
        :return: The sum of all elements from index 0 up to (but not including) end_idx.
        """
        sum_ = 0

        # Add elements by going to their child:
        while 0 < end_idx < len(self.__data):
            # __data's indices are shifted by one, so end_idx refers to index 'end_idx - 1' here:
            sum_ += self.__data[end_idx]
            end_idx -= end_idx & -end_idx  # This line flips the least significant set bit

        return sum_

    def add(self, idx: int, amount: int) -> None:
        """
        Adds the specified amount to the element at the given index.
        :param idx: The index of the element whose value will change.
        :param amount: The amount to add to the chosen element.
        """
        # Add to the specified element, and his parents:
        shifted_idx = idx + 1
        while 0 < shifted_idx < len(self.__data):
            self.__data[shifted_idx] += amount
            shifted_idx += shifted_idx & -shifted_idx  # This line flips the least significant set bit
