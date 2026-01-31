from json2schema.core.pipeline import Converter
from json2schema.core.comparators import TypeComparator, FormatComparator, RequiredComparator, FlagMaker, EmptyComparator
import time

cur = time.time()

conv = Converter()
conv.add_schema({"type": "object", "properties": {"name": {"type": "object", "properties": {"name": {"type": "integer"}}}}})
conv.add_json([{"name": "fdfddfm"}])
conv.add_json(["fdfddfm"])
conv.add_json({"name": "fdfddfm"})
conv.add_json([{"name": "https://dddd.ru"}])
conv.add_json([{"empty": {}}]) #
conv.add_json({"name": "https://dddd.ru"})
conv.add_json({
    "name": "alice@example.com",
    "email": "alice@example.com",
    "identifier": "3f2504e0-4f89-11d3-9a0c-0305e82c3301",
    "created": "2024-01-31"
})
conv.register(TypeComparator())
conv.register(FormatComparator())
conv.register(RequiredComparator())
conv.register(FlagMaker())
conv.register(EmptyComparator())

result = conv.run()
result_time = time.time()

from rich.pretty import pprint
pprint(result)
print(f"Затраченное время: {round(result_time-cur, 4)}")
