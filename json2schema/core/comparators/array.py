from .template import Comparator

class ArrayItemsComparator(Comparator):
    """Компаратор для обработки элементов массивов"""
    
    def __init__(self):
        self.processed = set()
    
    def can_process(self, schema_resources, json_resources, current_result, env_path):
        # Обрабатываем только один раз на каждом уровне
        if env_path in self.processed:
            return False
            
        # Проверяем, есть ли anyOf в текущем результате
        if "anyOf" in current_result:
            # Проверяем, есть ли хотя бы одна ветвь с типом array
            for branch in current_result["anyOf"]:
                if branch.get("type") == "array":
                    print(f"ArrayItemsComparator: can_process = True (есть anyOf с array), env_path = {env_path}")
                    return True
            print(f"ArrayItemsComparator: can_process = False (anyOf без array), env_path = {env_path}")
            return False
        
        # Иначе проверяем, есть ли массивы среди ресурсов
        all_resources = schema_resources + json_resources
        for resource in all_resources:
            if isinstance(resource.content, list):
                print(f"ArrayItemsComparator: can_process = True (есть массив), env_path = {env_path}")
                return True
        
        print(f"ArrayItemsComparator: can_process = False (нет массивов), env_path = {env_path}")
        return False
    
    def get_forbidden_comparators(self) -> list[str]:
        return []
    
    def process(self, schema_resources, json_resources, current_result, env_path):
        """Обрабатывает элементы массивов"""
        self.processed.add(env_path)
        
        print(f"ArrayItemsComparator: process, env_path = {env_path}")
        print(f"  current_result keys: {list(current_result.keys())}")
        
        # Если есть anyOf, обрабатываем каждую ветвь отдельно
        if "anyOf" in current_result:
            print(f"  Обработка anyOf с {len(current_result['anyOf'])} ветвями")
            result = current_result.copy()
            for i, branch in enumerate(result["anyOf"]):
                print(f"  Ветвь {i}: type = {branch.get('type')}, triggers = {branch.get('j2sElementTrigger', [])}")
                if branch.get("type") == "array":
                    # Получаем триггеры этой ветви
                    trigger_ids = branch.get("j2sElementTrigger", [])
                    # Фильтруем ресурсы по триггерам
                    filtered_schemas = [r for r in schema_resources if r.id in trigger_ids]
                    filtered_jsons = [r for r in json_resources if r.id in trigger_ids]
                    
                    print(f"    Фильтрация ресурсов: схемы {[r.id for r in filtered_schemas]}, JSON {[r.id for r in filtered_jsons]}")
                    
                    # Обрабатываем элементы для этой ветви
                    branch_result = self._process_items(filtered_schemas, filtered_jsons, branch)
                    result["anyOf"][i] = branch_result
            return result
        else:
            # Обычная обработка без anyOf
            print(f"  Обычная обработка (нет anyOf)")
            return self._process_items(schema_resources, json_resources, current_result)
    
    def _process_items(self, schema_resources, json_resources, current_result):
        """Обрабатывает элементы массивов для набора ресурсов"""
        all_items = []
        
        # Обрабатываем схемы
        for resource in schema_resources:
            schema = resource.content
            if isinstance(schema, dict):
                items = schema.get("items")
                if items is not None:
                    print(f"    Схема {resource.id}: items = {items}")
                    all_items.append({
                        "schema": items,
                        "resource_id": resource.id
                    })
        
        # Обрабатываем JSON
        for resource in json_resources:
            json_data = resource.content
            if isinstance(json_data, list) and json_data:
                print(f"    JSON {resource.id}: массив с {len(json_data)} элементами")
                # Для первого элемента массива
                item = json_data[0] if json_data else None
                if item is not None:
                    schema = self._create_schema_from_json(item)
                    print(f"      Первый элемент -> схема: {schema}")
                    all_items.append({
                        "schema": schema,
                        "resource_id": resource.id
                    })
        
        if not all_items:
            print(f"    Нет элементов, возвращаем current_result")
            return current_result
        
        print(f"    Найдены элементы: {len(all_items)}")
        
        # Создаем результат
        result = current_result.copy()
        if "type" not in result:
            result["type"] = "array"
        
        # Группируем элементы по resource_id
        items_by_id = {}
        for item in all_items:
            rid = item["resource_id"]
            if rid not in items_by_id:
                items_by_id[rid] = []
            items_by_id[rid].append(item["schema"])
        
        print(f"    Группировка по ID: {items_by_id.keys()}")
        
        # Если все элементы от одного ресурса
        if len(items_by_id) == 1:
            rid = list(items_by_id.keys())[0]
            schemas = items_by_id[rid]
            
            # Если несколько схем от одного ресурса
            if len(schemas) > 1:
                result["items"] = {
                    "anyOf": [
                        {**schema, "j2sElementTrigger": [rid]}
                        for schema in schemas
                    ]
                }
            else:
                result["items"] = {
                    **schemas[0],
                    "j2sElementTrigger": [rid]
                }
        else:
            # Элементы от разных ресурсов
            result["items"] = {"anyOf": []}
            for rid, schemas in items_by_id.items():
                if len(schemas) > 1:
                    element = {
                        "anyOf": [
                            {**schema, "j2sElementTrigger": [rid]}
                            for schema in schemas
                        ],
                        "j2sElementTrigger": [rid]
                    }
                else:
                    element = {
                        **schemas[0],
                        "j2sElementTrigger": [rid]
                    }
                result["items"]["anyOf"].append(element)
        
        print(f"    Результат: items = {result.get('items', 'нет')}")
        return result
    
    def _create_schema_from_json(self, json_data):
        """Создает схему из JSON-данных"""
        if isinstance(json_data, dict):
            return {"type": "object"}
        elif isinstance(json_data, list):
            return {"type": "array"}
        elif isinstance(json_data, (int, float)):
            if isinstance(json_data, int) or (isinstance(json_data, float) and json_data.is_integer()):
                return {"type": "integer"}
            return {"type": "number"}
        elif isinstance(json_data, str):
            return {"type": "string"}
        elif isinstance(json_data, bool):
            return {"type": "boolean"}
        elif json_data is None:
            return {"type": "null"}
        return {"type": "any"}