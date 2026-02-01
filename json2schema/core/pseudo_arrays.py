from .comparators.template import ProcessingContext
from typing import List, Optional


class PseudoArrayHandlerBase:
    def is_pseudo_array(self, keys: List[str], ctx: ProcessingContext) -> tuple[bool, Optional[str]]:
        return False, None

class PseudoArrayHandler(PseudoArrayHandlerBase):
    def is_pseudo_array(self, keys: List[str], ctx: ProcessingContext) -> tuple[bool, Optional[str]]:
        if not keys:
            return False, None
        try:
            indices = [int(k) for k in keys]
            return True, "^[0-9]+$"
        except ValueError:
            return False, None
