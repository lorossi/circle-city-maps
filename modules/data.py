"""Module for a generic data class, because default dataclasses are not \
TOML serializable.

Furthermore, I have developed a custom dataclass (also available on PyPI) \
but I don't want to use it here because I don't need such a complexity.
"""

from __future__ import annotations

import json


class Data:
    """Class representing a generic dataclass."""

    def __init__(self, **kwargs) -> Data:
        """Initialise the class.

        Args:
            **kwargs: keyword arguments representing the attributes of the class.

        Returns:
            Data
        """
        for arg in self.__annotations__:
            setattr(self, arg, kwargs.get(arg, None))

        self.__post__init__()

    def __post__init__(self):
        """Post-initialisation method.

        Automatically called after the initialisation of the class.
        """
        pass

    def to_json(self) -> str:
        """Return the object as a JSON string.

        Returns:
            str
        """
        return json.dumps(self.__dict__)

    @classmethod
    def from_json(cls, json_string: str) -> Data:
        """Return the object from a json string.

        Args:
            json_string (str): json string representing the object.

        Returns:
            Data
        """
        return cls(**json.loads(json_string))

    def __repr__(self) -> str:
        """Representation of the object."""
        return f"{self.__class__.__name__}({self.__dict__})"

    def __str__(self) -> str:
        """Representation of the object as a string."""
        return self.__repr__()
