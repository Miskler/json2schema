import time
from statistics import mean

# ===== genschema (твоя библиотека) =====
from genschema.pipeline import Converter
from genschema.comparators import (
    FormatComparator,
    RequiredComparator,
    EmptyComparator,
    DeleteElement,
)

# ===== genson =====
from genson import SchemaBuilder


# ===== входные данные =====
SCHEMA = {}

import json
with open("tests/datasets/all_doctors_data.json", "r") as f:
    jsn = json.loads(f.read())

JSONS = [
    jsn
]

RUNS = 5000


# ===== genschema прогон =====
def run_genschema():
    conv = Converter()
    conv.add_schema(SCHEMA)

    for j in JSONS:
        conv.add_json(j)

    conv.register(FormatComparator())
    conv.register(RequiredComparator())
    #conv.register(FlagMaker())
    conv.register(EmptyComparator())
    conv.register(DeleteElement())

    return conv.run()


# ===== genson прогон =====
def run_genson():
    builder = SchemaBuilder()
    builder.add_schema(SCHEMA)

    for j in JSONS:
        builder.add_object(j)

    return builder.to_schema()


# ===== бенчмарк =====
def benchmark(fn, runs):
    timings = []

    for _ in range(runs):
        start = time.perf_counter()
        fn()
        timings.append(time.perf_counter() - start)

    return timings


if __name__ == "__main__":
    print(f"Прогонов: {RUNS}\n")

    t1 = benchmark(run_genschema, RUNS)
    t2 = benchmark(run_genson, RUNS)

    avg_genschema = mean(t1)
    avg_genson = mean(t2)

    print("=== РЕЗУЛЬТАТЫ ===")
    print(f"genschema : {avg_genschema:.6f} сек (avg)")
    print(f"genson      : {avg_genson:.6f} сек (avg)")

    if avg_genson > 0:
        print(f"\ngenschema / genson = {avg_genschema / avg_genson:.2f}x")
    
    print("\n")
    from jsonschema_diff import JsonSchemaDiff, ConfigMaker
    from jsonschema_diff.color import HighlighterPipeline
    from jsonschema_diff.color.stages import (
        MonoLinesHighlighter, PathHighlighter, ReplaceGenericHighlighter,
    )
    prop = JsonSchemaDiff(
        config=ConfigMaker.make(),
        colorize_pipeline=HighlighterPipeline([
            MonoLinesHighlighter(),
            ReplaceGenericHighlighter(),
            PathHighlighter(),
        ])
    )

    #prop.compare( # Function accepts both file path and schema dict itself // can be combined
    #    old_schema=run_genschema(),
    #    new_schema=run_genson()
    #)

    # Теперь можно вывести
    #prop.print(with_legend=False)
