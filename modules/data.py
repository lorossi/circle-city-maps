from __future__ import annotations


class Data:
    def __init__(
        self,
        **kwargs,
    ) -> Data:
        for key, value in kwargs.items():
            if key in self.__annotations__:
                setattr(self, key, value)
            else:
                raise AttributeError(f"Unknown attribute {key}")

        self.__post__init__()

    def __post__init__(self):
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__dict__})"

    def __str__(self) -> str:
        return self.__repr__()
