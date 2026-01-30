from .template import Comparator


class TypeComparator(Comparator):
    """Компаратор для обработки типов данных"""
    
    def __init__(self):
        self.processed = set()
    
    def can_process(self, schema_resources, json_resources, current_result, env_path):
        # Обрабатываем только один раз на каждом уровне
        if env_path in self.processed:
            return False
        return True
    
    def get_forbidden_comparators(self) -> list[str]:
        return []
    
    def process(self, schema_resources, json_resources, current_result, env_path):
        """Обрабатывает типы данных из всех ресурсов"""
        self.processed.add(env_path)
        
        # Проверяем, есть ли уже anyOf в результате
        if "anyOf" in current_result:
            print(f"TypeComparator: уже есть anyOf, пропускаем {env_path}")
            return current_result
        
        type_groups = {}
        
        # Обрабатываем схемы
        for resource in schema_resources:
            schema = resource.content
            if isinstance(schema, dict):
                schema_type = schema.get("type", "any")
            else:
                # Если schema не словарь, определяем тип по структуре
                schema_type = self._infer_type(schema)
            
            if schema_type not in type_groups:
                type_groups[schema_type] = []
            type_groups[schema_type].append(resource.id)
        
        # Обрабатываем JSON
        for resource in json_resources:
            json_data = resource.content
            json_type = self._infer_type(json_data)
            
            if json_type not in type_groups:
                type_groups[json_type] = []
            type_groups[json_type].append(resource.id)
        
        print(f"TypeComparator: type_groups = {type_groups}, env_path = {env_path}")
        
        # Если только один тип, возвращаем его
        if len(type_groups) == 1:
            result = {"type": list(type_groups.keys())[0]}
            print(f"TypeComparator: один тип -> {result}")
            return result
        
        # Если несколько типов, создаем anyOf
        result = {"anyOf": []}
        
        for schema_type, trigger_ids in type_groups.items():
            element = {"type": schema_type, "j2sElementTrigger": trigger_ids}
            result["anyOf"].append(element)
        
        print(f"TypeComparator: несколько типов -> anyOf с {len(result['anyOf'])} элементами")
        return result
    
    def _infer_type(self, data):
        """Определяет тип JSON-данных"""
        if data is None:
            return "null"
        elif isinstance(data, bool):
            return "boolean"
        elif isinstance(data, (int, float)):
            # Проверяем, целое ли число
            if isinstance(data, int) or (isinstance(data, float) and data.is_integer()):
                return "integer"
            return "number"
        elif isinstance(data, str):
            return "string"
        elif isinstance(data, list):
            return "array"
        elif isinstance(data, dict):
            return "object"
        return "any"