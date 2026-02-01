from json2schema.core import Converter, PseudoArrayHandler
from json2schema.core.comparators import TypeComparator, FormatComparator, RequiredComparator, FlagMaker, EmptyComparator, DeleteElement
import time
import json

with open("ClassCatalog.tree.json", "r") as f:
    jsn = json.loads(f.read())

cur = time.time()

conv = Converter(pseudo_handler=PseudoArrayHandler(), base_of="anyOf")
conv.add_json(jsn)


#conv.add_schema({"type": "object", "properties": {"name": {"type": "object", "properties": {"name": {"type": "integer"}}}}})
#conv.add_json([{"name": "fdfddfm"}])
#conv.add_json(["fdfddfm"])
#conv.add_json({"name": "fdfddfm"})
#conv.add_json([{"name": "https://dddd.ru"}])
#conv.add_json([{"empty": {}}]) #
#conv.add_json({"name": "https://dddd.ru"})
#conv.add_json({
#    "name": "alice@example.com",
#    "email": "alice@example.com",
#    "identifier": "3f2504e0-4f89-11d3-9a0c-0305e82c3301",
#    "created": "2024-01-31"
#})
#conv.add_json([
#    #{},  # пустой объект → должен пометиться как empty
#    {"0": {"name": "Alice", "dopvlojenost": {"f": True}}, "1": {"name": "Bob", "dopvlojenost": {"f": 1}}},  # псевдо-массив объектов
#])
#conv.add_json([
#    {"0": 10, "1": 20, "2": 30},  # псевдо-массив примитивов (числа)
#    #{"id": 1, "title": "Test"},  # обычный объект
#    #["apple", "banana", "cherry"],  # массив строк
#    #{"name": "Charlie", "age": 30},  # несовместимый объект с предыдущим
#])
#conv.register(TypeComparator())
conv.register(FormatComparator())
conv.register(RequiredComparator())
#conv.register(FlagMaker())
conv.register(EmptyComparator())
conv.register(DeleteElement())
conv.register(DeleteElement("isPseudoArray"))

result = conv.run()
result_time = time.time()

with open("ClassCatalog.tree.schema.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

from rich.pretty import pprint
pprint(result)
print(f"Затраченное время: {round(result_time-cur, 4)}")
