# parsers/base_parser.py

import abc
from typing import Any, Optional

class BaseParser(abc.ABC):
    @abc.abstractmethod
    def parse(self, place: str, **kwargs) -> Optional[Any]:
        pass
