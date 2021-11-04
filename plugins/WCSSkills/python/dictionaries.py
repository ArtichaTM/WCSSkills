# ../python/dictionaries.py
from typing import Any

class DefaultDict:
    """ Note: DefaultDict ~ DD (shortcut)

    Dictionary that realizes overall default value and
    adding ignored values

    • If some values r ignored, they won't be shown during
    iterating over DD, DD.values() and others
    • If trying to get missing value, like x['x'] when x = {'y':1},
    DD will return default_key, that by default is None
    • DD can be added to another by simply DD + dict.
    Then all values from dict will transfer to DD

    """

    __slots__ = ('_default_key', 'dict', '_ignored_values', 'position')

    def __init__(self, data=None) -> None:
        """
        Creates dictionary. Data can be added at start

        :param data: dictionary with values
        """
        super().__init__()

        if data is None:
            self.dict = dict()
        else:
            self.dict = dict(data)

        # Key that is equals None, but may be different in
        # different situations
        self._default_key = None

        # Ignored values, like None or 0
        self._ignored_values = []

    def __str__(self) -> str:
        """ Returns all keys that DD has in string"""
        return f"{self.keys()}"

    def __len__(self) -> int:
        """ Returns amount of non-ignored values"""
        return len(self.dict.keys())

    def __getitem__(self, item) -> Any:
        """
        Returns value of key by default, but when key doesn't
        exist it returns default_key, that set by DD.set_default(value)

        :param item: key of needed value
        :return: Value of key or default value
        """

        try: self.dict[item]
        except KeyError: return self.__missing__(item)

    def __setitem__(self, key, value):
        """ Sets an value to key """
        self.dict[key] = value

    def __delitem__(self, key):
        """ Popping item from dict """
        try: return self.dict.pop(key)
        except KeyError: raise KeyError("Key doesn't exist")

    def __missing__(self, key):
        """ If key doesn't exist, return default_key"""
        return self._default_key

    def __iter__(self):

        # Position of iterator
        self.position = 0

        # Returning self
        return self

    def __next__(self):

        # Getting current position
        position = self.position

        # Adding one to self.position
        self.position += 1

        # Trying to return key with current position
        try: return self.keys()[position]

        # Failed. Stop iter then
        except IndexError: raise StopIteration

    def __nonzero__(self):
        """ If there's no entry in dict, return False"""
        if len(self.dict.values()) == 0: return False
        else: return True

    def __add__(self, other):
        """ Adds all items from another dict """

        # Can add only different dictionaries
        if not isinstance(other, dict):
            raise TypeError('Adding to DefaultDict allowed only with dict')

    def __radd__(self, other):
        """ Adds all items to another dict """

        # Can only add different dictionaries
        if not isinstance(other, dict):
            raise TypeError('Adding DefaultDict allowed only to another dict')

        # Adding dictionary items and return them
        return type(other)(**other, **self.dict)

    @property
    def default(self) -> Any:
        """ Return default key"""
        return self._default_key

    def set_default(self, key) -> None:
        """ Sets default key """
        self._default_key = key

    def ignored(self) -> list:
        """ Returns ignored list"""
        return self._ignored_values

    def add_ignored(self, *args) -> None:
        self._ignored_values.extend(args)

    def items(self):
        """ Returns all items of DD like [[key, value], [key, value], ...] """

        # List, that will be returned in the end
        output = []

        # Iterating over all values in dictionary
        for key, value in self.dict.items():

            # If value is ignored -> don't show it
            if value in self._ignored_values:
                continue

            # Adding [key, value] to list
            output.append([key, value])

        # Returning list with keys and values
        return output

    def keys(self):
        """ Returns all keys of DD like [key, key, ...] """

        # List, that will be returned in the end
        output = []

        # Iterating over all values in dictionary
        for key, value in self.dict.items():

            # If value is ignored -> don't show it
            if value in self._ignored_values:
                continue

            # Adding key to list
            output.append(key)

        # Returning list with keys
        return output

    def values(self):
        """ Returns all values of DD like [value, value, ...] """

        # List, that will be returned in the end
        output = []

        # Iterating over all values in dictionary
        for key, value in self.dict.items():

            # If value is ignored -> don't show it
            if value in self._ignored_values:
                continue

            # Adding key to list
            output.append(value)

        # Returning list with keys
        return output

    def clear(self, only_ignored: bool = False):

        # If clearing only ignored values
        if only_ignored:

            # Iterating over all values
            for key, value in self.dict.items():

                # Checking for ignorance
                if value in self._ignored_values:

                    # Ignored, kick it
                    del self.dict[key]

        # Clearing all values
        else:

            # Clearing dict
            self.dict.clear()