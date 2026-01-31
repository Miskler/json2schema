from typing import Dict, List, Optional, Tuple
from .template import ProcessingContext, Comparator

class FlagMaker(Comparator):
    """Визуально показывает где именно могут сработать компораторы"""

    def can_process(self, ctx: ProcessingContext, env: str, node: Dict) -> bool:
        # Обрабатываем объекты и массивы
        return True

    def process(
        self,
        ctx: ProcessingContext,
        env: str,
        node: Dict
    ) -> Tuple[Optional[Dict], Optional[List[Dict]]]:
        return {"Flag": True}, None
