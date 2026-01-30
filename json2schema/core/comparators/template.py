from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum

import json
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from dataclasses import dataclass, field
from enum import Enum


class ResourceType(Enum):
    JSON = "json"
    SCHEMA = "schema"


@dataclass
class Resource:
    """Объект-ресурс с данными кандидата"""
    content: Any
    id: int
    type: ResourceType
    path: str = ""  # текущий путь внутри ресурса
    
    def __hash__(self):
        return hash((self.id, self.path))


class Comparator:
    """Базовый класс для всех компараторов"""
    
    @property
    def name(self) -> str:
        return self.__class__.__name__
    
    def can_process(self, 
                   schema_resources: List[Resource],
                   json_resources: List[Resource],
                   current_result: Dict,
                   env_path: str) -> bool:
        """Определяет, может ли компаратор обработать текущий слой"""
        raise NotImplementedError()
    
    def get_forbidden_comparators(self) -> List[str]:
        """Возвращает список имен компараторов, которым запрещено обрабатывать этот слой"""
        return []
    
    def process(self,
               schema_resources: List[Resource],
               json_resources: List[Resource],
               current_result: Dict,
               env_path: str) -> Dict:
        """Основная функция обработки слоя"""
        raise NotImplementedError()
    
    @staticmethod
    def get_elements_triggers(result: Dict) -> List[List[int]]:
        """
        Извлекает информацию о триггерах из anyOf/oneOf/allOf
        Возвращает список групп триггеров
        """
        triggers = []
        
        def extract_from_of(of_key: str):
            if of_key in result:
                for item in result[of_key]:
                    if "j2sElementTrigger" in item:
                        triggers.append(item["j2sElementTrigger"])
        
        extract_from_of("anyOf")
        extract_from_of("oneOf")
        extract_from_of("allOf")
        
        return triggers
