import abc
import re
from typing import Any, Optional

class BaseParser(abc.ABC):
    @abc.abstractmethod
    def parse(self, place: str, **kwargs) -> Optional[Any]:
        pass

    def clean_string(self, string: str) -> str:
        return re.sub(r'\s+|\n+|\t+', ' ', string).strip().replace("ё", "е").lower()