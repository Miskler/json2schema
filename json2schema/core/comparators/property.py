from .template import Comparator

class PropertyComparator(Comparator):
    """Компаратор для обработки свойств объектов"""
    
    def __init__(self):
        self.processed = set()
    
    def can_process(self, schema_resources, json_resources, current_result, env_path):
        # Обрабатываем только один раз на каждом уровне
        if env_path in self.processed:
            return False
            
        # Проверяем, есть ли anyOf в текущем результате
        if "anyOf" in current_result:
            # Проверяем, есть ли хотя бы одна ветвь с типом object
            for branch in current_result["anyOf"]:
                if branch.get("type") == "object":
                    print(f"PropertyComparator: can_process = True (есть anyOf с object), env_path = {env_path}")
                    return True
            print(f"PropertyComparator: can_process = False (anyOf без object), env_path = {env_path}")
            return False
        
        # Иначе проверяем, есть ли объекты среди ресурсов
        all_resources = schema_resources + json_resources
        for resource in all_resources:
            if isinstance(resource.content, dict):
                print(f"PropertyComparator: can_process = True (есть объект), env_path = {env_path}")
                return True
        
        print(f"PropertyComparator: can_process = False (нет объектов), env_path = {env_path}")
        return False
    
    def get_forbidden_comparators(self) -> list[str]:
        return []
    
    def process(self, schema_resources, json_resources, current_result, env_path):
        """Обрабатывает свойства объектов"""
        self.processed.add(env_path)
        
        print(f"PropertyComparator: process, env_path = {env_path}")
        print(f"  current_result keys: {list(current_result.keys())}")
        
        # Если есть anyOf, обрабатываем каждую ветвь отдельно
        if "anyOf" in current_result:
            print(f"  Обработка anyOf с {len(current_result['anyOf'])} ветвями")
            result = current_result.copy()
            for i, branch in enumerate(result["anyOf"]):
                print(f"  Ветвь {i}: type = {branch.get('type')}, triggers = {branch.get('j2sElementTrigger', [])}")
                if branch.get("type") == "object":
                    # Получаем триггеры этой ветви
                    trigger_ids = branch.get("j2sElementTrigger", [])
                    # Фильтруем ресурсы по триггерам
                    filtered_schemas = [r for r in schema_resources if r.id in trigger_ids]
                    filtered_jsons = [r for r in json_resources if r.id in trigger_ids]
                    
                    print(f"    Фильтрация ресурсов: схемы {[r.id for r in filtered_schemas]}, JSON {[r.id for r in filtered_jsons]}")
                    
                    # Обрабатываем свойства для этой ветви
                    branch_result = self._process_properties(filtered_schemas, filtered_jsons, branch)
                    result["anyOf"][i] = branch_result
            return result
        else:
            # Обычная обработка без anyOf
            print(f"  Обычная обработка (нет anyOf)")
            return self._process_properties(schema_resources, json_resources, current_result)
    
    def _process_properties(self, schema_resources, json_resources, current_result):
        """Обрабатывает свойства для набора ресурсов"""
        all_properties = {}
        
        # Обрабатываем схемы
        for resource in schema_resources:
            schema = resource.content
            if isinstance(schema, dict):
                properties = schema.get("properties", {})
                print(f"    Схема {resource.id}: properties = {list(properties.keys())}")
                for prop_name, prop_schema in properties.items():
                    if prop_name not in all_properties:
                        all_properties[prop_name] = {
                            "schema_ids": set(),
                            "json_ids": set(),
                            "schemas": []
                        }
                    all_properties[prop_name]["schema_ids"].add(resource.id)
                    all_properties[prop_name]["schemas"].append(prop_schema)
        
        # Обрабатываем JSON
        for resource in json_resources:
            json_data = resource.content
            if isinstance(json_data, dict):
                print(f"    JSON {resource.id}: keys = {list(json_data.keys())}")
                for prop_name in json_data.keys():
                    if prop_name not in all_properties:
                        all_properties[prop_name] = {
                            "schema_ids": set(),
                            "json_ids": set(),
                            "schemas": []
                        }
                    all_properties[prop_name]["json_ids"].add(resource.id)
        
        if not all_properties:
            print(f"    Нет свойств, возвращаем current_result")
            return current_result
        
        print(f"    Найдены свойства: {list(all_properties.keys())}")
        
        # Создаем результат
        result = current_result.copy()
        if "type" not in result:
            result["type"] = "object"
        
        result["properties"] = {}
        required = []
        
        for prop_name, prop_info in all_properties.items():
            # Определяем триггеры для этого свойства
            trigger_ids = list(prop_info["schema_ids"] | prop_info["json_ids"])
            
            print(f"    Свойство '{prop_name}': триггеры {trigger_ids}, схемы {len(prop_info['schemas'])}")
            
            # Если есть схемы для этого свойства
            if prop_info["schemas"]:
                # Если несколько схем, создаем anyOf
                if len(prop_info["schemas"]) > 1:
                    prop_result = {"anyOf": []}
                    for schema, schema_id in zip(prop_info["schemas"], list(prop_info["schema_ids"])):
                        element = {**schema, "j2sElementTrigger": [schema_id]}
                        prop_result["anyOf"].append(element)
                    result["properties"][prop_name] = prop_result
                else:
                    # Одна схема
                    result["properties"][prop_name] = {
                        **prop_info["schemas"][0],
                        "j2sElementTrigger": trigger_ids
                    }
            else:
                # Только JSON данные
                result["properties"][prop_name] = {
                    "j2sElementTrigger": trigger_ids
                }
        
        return result