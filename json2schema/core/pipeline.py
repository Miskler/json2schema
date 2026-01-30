from typing import Dict, List, Any
from .comparators.template import Resource, ResourceType, Comparator

class GlobalManager:
    """Глобальный менеджер для рекурсивной обработки схем"""
    
    def __init__(self):
        self.comparators = []
        self.next_id = 0
        self.resources = {}  # id -> Resource
        self.processed_levels = set()  # Для отслеживания обработанных уровней
        
    def add_comparator(self, comparator: Comparator, priority: int):
        """Добавляет компаратор с указанным приоритетом"""
        self.comparators.append((priority, comparator))
        self.comparators.sort(key=lambda x: x[0], reverse=True)
    
    def add_schema(self, schema: Dict) -> int:
        """Добавляет схему и возвращает её ID"""
        resource_id = self.next_id
        self.resources[resource_id] = Resource(
            content=schema,
            id=resource_id,
            type=ResourceType.SCHEMA
        )
        self.next_id += 1
        return resource_id
    
    def add_json(self, json_data: Any) -> int:
        """Добавляет JSON и возвращает его ID"""
        resource_id = self.next_id
        self.resources[resource_id] = Resource(
            content=json_data,
            id=resource_id,
            type=ResourceType.JSON
        )
        self.next_id += 1
        return resource_id
    
    def process(self) -> Dict:
        """Запускает процесс обработки всех ресурсов"""
        # Разделяем ресурсы на схемы и JSON
        schema_resources = [r for r in self.resources.values() if r.type == ResourceType.SCHEMA]
        json_resources = [r for r in self.resources.values() if r.type == ResourceType.JSON]
        
        print(f"=== Начало обработки ===")
        print(f"Схемы: {[r.id for r in schema_resources]}")
        print(f"JSON: {[r.id for r in json_resources]}")
        
        result = self._process_level(schema_resources, json_resources, {}, "")
        
        print(f"=== Конец обработки ===")
        return result
    
    def _process_level(self, 
                      schema_resources: List[Resource],
                      json_resources: List[Resource],
                      current_result: Dict,
                      env_path: str) -> Dict:
        """Обрабатывает один уровень вложенности"""
        
        # Проверяем, не обрабатывали ли уже этот уровень
        level_key = f"{env_path}|{tuple(sorted([r.id for r in schema_resources]))}|{tuple(sorted([r.id for r in json_resources]))}"
        if level_key in self.processed_levels:
            print(f"Пропускаем уже обработанный уровень: {env_path}")
            return current_result
        
        self.processed_levels.add(level_key)
        
        print(f"\n=== Обработка уровня: {env_path or 'корень'} ===")
        print(f"Ресурсы: схемы {[r.id for r in schema_resources]}, JSON {[r.id for r in json_resources]}")
        print(f"Текущий результат: {list(current_result.keys())}")
        
        # Фильтруем ресурсы, которые существуют на этом пути
        filtered_schemas = self._filter_resources_by_path(schema_resources, env_path)
        filtered_jsons = self._filter_resources_by_path(json_resources, env_path)
        
        print(f"После фильтрации: схемы {[r.id for r in filtered_schemas]}, JSON {[r.id for r in filtered_jsons]}")
        
        if not filtered_schemas and not filtered_jsons:
            return current_result
        
        # Применяем компараторы по приоритету
        result = current_result.copy()
        
        for priority, comparator in self.comparators:
            print(f"\n--- Компаратор {comparator.name} (приоритет {priority}) ---")
            
            if comparator.can_process(filtered_schemas, filtered_jsons, result, env_path):
                # Обрабатываем слой
                comparator_result = comparator.process(
                    filtered_schemas, filtered_jsons, result, env_path
                )
                
                print(f"Результат {comparator.name}: {list(comparator_result.keys())}")
                
                # Объединяем результаты
                result = self._merge_results(result, comparator_result)
                print(f"Объединенный результат: {list(result.keys())}")
        
        # Рекурсивная обработка вложенных уровней
        result = self._process_nested_levels(
            filtered_schemas, filtered_jsons, result, env_path
        )
        
        return result
    
    def _merge_results(self, old_result: Dict, new_result: Dict) -> Dict:
        """Объединяет результаты работы компараторов"""
        print(f"  Объединение: old keys = {list(old_result.keys())}, new keys = {list(new_result.keys())}")
        
        # Если new_result пустой или совпадает с old_result
        if not new_result or new_result == old_result:
            return old_result
        
        # Если new_result полностью заменяет old_result
        if old_result and not new_result:
            return old_result
        
        result = new_result.copy()
        
        # Обрабатываем anyOf отдельно
        if "anyOf" in old_result and "anyOf" in new_result:
            # Объединяем anyOf, удаляя дубликаты
            old_anyof = old_result["anyOf"]
            new_anyof = new_result["anyOf"]
            
            print(f"  Объединение anyOf: old {len(old_anyof)} элементов, new {len(new_anyof)} элементов")
            
            # Создаем множество уникальных элементов
            unique_elements = []
            seen = set()
            
            for element in old_anyof + new_anyof:
                # Создаем ключ для сравнения
                triggers = tuple(sorted(element.get("j2sElementTrigger", [])))
                element_type = element.get("type", "")
                key = (triggers, element_type)
                
                if key not in seen:
                    seen.add(key)
                    unique_elements.append(element)
            
            result["anyOf"] = unique_elements
            print(f"  После объединения: {len(result['anyOf'])} уникальных элементов")
        
        return result
    
    def _filter_resources_by_path(self, resources: List[Resource], path: str) -> List[Resource]:
        """Фильтрует ресурсы по пути, извлекая данные на указанном уровне"""
        if not path:
            return resources.copy()
        
        filtered = []
        for resource in resources:
            data = self._get_data_by_path(resource.content, path)
            if data is not None:
                new_resource = Resource(
                    content=data,
                    id=resource.id,
                    type=resource.type,
                    path=path
                )
                filtered.append(new_resource)
        
        return filtered
    
    def _get_data_by_path(self, data: Any, path: str) -> Any:
        """Извлекает данные по пути вида 'properties/name' или 'items/0'"""
        if not path or data is None:
            return data
        
        parts = path.split('/')
        current = data
        
        for part in parts:
            if part == '':
                continue
            
            if isinstance(current, dict):
                if part in current:
                    current = current[part]
                else:
                    return None
            elif isinstance(current, list) and part.isdigit():
                idx = int(part)
                if 0 <= idx < len(current):
                    current = current[idx]
                else:
                    return None
            else:
                return None
        
        return current
    
    def _process_nested_levels(self,
                              schema_resources: List[Resource],
                              json_resources: List[Resource],
                              current_result: Dict,
                              env_path: str) -> Dict:
        """Обрабатывает вложенные уровни (properties, items и т.д.)"""
        print(f"\n>>> Рекурсивная обработка вложенных уровней: {env_path or 'корень'} <<<")
        
        result = current_result.copy()
        
        # Если есть anyOf, обрабатываем каждую ветвь отдельно
        if "anyOf" in result:
            print(f"  Обработка {len(result['anyOf'])} ветвей anyOf")
            for i, branch in enumerate(result["anyOf"]):
                branch_env_path = f"{env_path}/anyOf/{i}" if env_path else f"anyOf/{i}"
                
                # Получаем триггеры для этой ветви
                trigger_ids = branch.get("j2sElementTrigger", [])
                if not trigger_ids:
                    continue
                
                print(f"  Ветвь {i}: триггеры {trigger_ids}, тип {branch.get('type')}")
                
                # Фильтруем ресурсы по триггерам
                filtered_schemas = [
                    r for r in schema_resources 
                    if r.id in trigger_ids and self._get_data_by_path(r.content, branch_env_path) is not None
                ]
                filtered_jsons = [
                    r for r in json_resources
                    if r.id in trigger_ids and self._get_data_by_path(r.content, branch_env_path) is not None
                ]
                
                # Обрабатываем вложенный уровень
                if filtered_schemas or filtered_jsons:
                    branch_result = self._process_level(
                        filtered_schemas, filtered_jsons, branch, branch_env_path
                    )
                    result["anyOf"][i] = branch_result
        
        # Обработка свойств объектов (если нет anyOf)
        elif result.get("type") == "object" and "properties" in result:
            print(f"  Обработка свойств объекта")
            for prop_name, prop_schema in result["properties"].items():
                new_path = f"{env_path}/properties/{prop_name}" if env_path else f"properties/{prop_name}"
                
                # Получаем триггеры для этого свойства
                trigger_ids = prop_schema.get("j2sElementTrigger", [])
                if not trigger_ids:
                    continue
                
                # Фильтруем ресурсы по триггерам
                filtered_schemas = [
                    r for r in schema_resources 
                    if r.id in trigger_ids and self._has_property(r, prop_name, env_path)
                ]
                filtered_jsons = [
                    r for r in json_resources
                    if r.id in trigger_ids and self._has_property(r, prop_name, env_path)
                ]
                
                # Обрабатываем вложенный уровень
                if filtered_schemas or filtered_jsons:
                    prop_result = self._process_level(
                        filtered_schemas, filtered_jsons, prop_schema, new_path
                    )
                    result["properties"][prop_name] = prop_result
        
        # Обработка элементов массивов (если нет anyOf)
        elif result.get("type") == "array" and "items" in result:
            print(f"  Обработка элементов массива")
            items_schema = result["items"]
            
            # Обработка anyOf в items
            if "anyOf" in items_schema:
                for i, item in enumerate(items_schema["anyOf"]):
                    trigger_ids = item.get("j2sElementTrigger", [])
                    if not trigger_ids:
                        continue
                    
                    new_path = f"{env_path}/items/anyOf/{i}" if env_path else f"items/anyOf/{i}"
                    
                    filtered_schemas = [
                        r for r in schema_resources 
                        if r.id in trigger_ids
                    ]
                    filtered_jsons = [
                        r for r in json_resources
                        if r.id in trigger_ids
                    ]
                    
                    # Обрабатываем вложенный уровень
                    if filtered_schemas or filtered_jsons:
                        item_result = self._process_level(
                            filtered_schemas, filtered_jsons, item, new_path
                        )
                        items_schema["anyOf"][i] = item_result
            else:
                # Обычный items
                trigger_ids = items_schema.get("j2sElementTrigger", [])
                if trigger_ids:
                    new_path = f"{env_path}/items" if env_path else "items"
                    
                    filtered_schemas = [
                        r for r in schema_resources 
                        if r.id in trigger_ids
                    ]
                    filtered_jsons = [
                        r for r in json_resources
                        if r.id in trigger_ids
                    ]
                    
                    # Обрабатываем вложенный уровень
                    if filtered_schemas or filtered_jsons:
                        items_result = self._process_level(
                            filtered_schemas, filtered_jsons, items_schema, new_path
                        )
                        result["items"] = items_result
        
        return result
    
    def _has_property(self, resource: Resource, prop_name: str, base_path: str) -> bool:
        """Проверяет, есть ли свойство у ресурса по указанному пути"""
        data = self._get_data_by_path(resource.content, base_path)
        if isinstance(data, dict):
            if resource.type == ResourceType.SCHEMA:
                properties = data.get("properties", {})
                return prop_name in properties
            else:  # JSON
                return prop_name in data
        return False
