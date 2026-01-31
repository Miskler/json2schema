from typing import Dict, Optional, List, Tuple
from .template import ProcessingContext, Comparator, Resource

class EmptyComparator(Comparator):
    """
    Добавляет minItems=0 или minProperties=0 для пустых массивов/объектов,
    если на данном уровне нет кандидатов из непустых схем или JSON.
    """

    def can_process(self, ctx: ProcessingContext, env: str, node: Dict) -> bool:
        t = node.get("type")
        return t == "object" or t == "array"

    def process(
        self,
        ctx: ProcessingContext,
        env: str,
        node: Dict
    ) -> Tuple[Optional[Dict], Optional[List[Dict]]]:

        # Проверяем есть ли непустые кандидаты на этом уровне
        def is_nonempty(r: Resource):
            c = r.content
            if isinstance(c, dict):
                return bool(c)  # не пустой словарь
            if isinstance(c, list):
                return bool(c)  # не пустой список
            return True  # скаляры считаем непустыми

        has_candidates = any(is_nonempty(r) for r in ctx.schemas + ctx.jsons)

        if not has_candidates:
            t = node.get("type")
            if t == "object":
                return {"minProperties": 0}, None
            elif t == "array":
                return {"minItems": 0}, None

        return None, None
