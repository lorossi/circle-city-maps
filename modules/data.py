from __future__ import annotations

import json


class Data:
    def __init__(self, **kwargs) -> Data:
        for arg in self.__annotations__:
            setattr(self, arg, kwargs.get(arg, None))

        self.__post__init__()

    def to_json(self) -> str:
        return json.dumps(self.__dict__)

    @classmethod
    def from_json(cls, json_string: str) -> Data:
        return cls(**json.loads(json_string))

    def __post__init__(self):
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__dict__})"

    def __str__(self) -> str:
        return self.__repr__()
