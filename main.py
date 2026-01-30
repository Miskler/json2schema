from json2schema.core.pipeline import GlobalManager
from json2schema.core.comparators import TypeComparator, PropertyComparator, ArrayItemsComparator
import json

# Assuming the Json2Schema class definition is available as provided earlier
converter = GlobalManager()

converter.add_comparator(TypeComparator(), priority=100)
converter.add_comparator(PropertyComparator(), priority=90)
converter.add_comparator(ArrayItemsComparator(), priority=80)

# Добавляем схемы из примера
converter.add_schema({
    "type": "object",
    "properties": {
        "name": {"type": "integer"}
    }
})
converter.add_json([{"name": "Bob"}])
result = converter.process()

print("Результат:")
print(json.dumps(result, indent=2, ensure_ascii=False))