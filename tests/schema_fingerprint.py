import argparse
import glob
import hashlib
import json
import os

from genschema import Converter, PseudoArrayHandler
from genschema.comparators import (
    DeleteElement,
    EmptyComparator,
    FormatComparator,
    NoAdditionalProperties,
    RequiredComparator,
)


def _load_datasets(dataset_dir: str) -> list[str]:
    dataset_files = glob.glob(os.path.join(dataset_dir, "*.json"))
    if not dataset_files:
        raise SystemExit(f"No dataset files found in {dataset_dir}")
    return sorted(dataset_files)


def _generate_schema(data: object) -> dict:
    conv = Converter(pseudo_handler=PseudoArrayHandler(), base_of="anyOf")
    conv.add_json(data)
    conv.register(FormatComparator())
    conv.register(RequiredComparator())
    conv.register(EmptyComparator())
    conv.register(NoAdditionalProperties())
    conv.register(DeleteElement())
    conv.register(DeleteElement("isPseudoArray"))
    return conv.run()


def _canonical_json(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate schema fingerprints for datasets")
    parser.add_argument("--dataset-dir", default="tests/datasets")
    parser.add_argument("--out-dir", default="matrix-results")
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    dataset_files = _load_datasets(args.dataset_dir)
    per_dataset = {}
    schemas_jsonl_path = os.path.join(args.out_dir, "schemas.jsonl")

    with open(schemas_jsonl_path, "w", encoding="utf-8") as schemas_file:
        for file_path in dataset_files:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            schema = _generate_schema(data)
            canonical = _canonical_json(schema)
            digest = _sha256(canonical)
            rel_path = os.path.relpath(file_path, args.dataset_dir)
            per_dataset[rel_path] = digest
            schemas_file.write(json.dumps({"dataset": rel_path, "schema": schema}) + "\n")

    summary_path = os.path.join(args.out_dir, "schema-digests.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(per_dataset, f, sort_keys=True, indent=2)
        f.write("\n")

    combined = "\n".join(f"{k}:{v}" for k, v in sorted(per_dataset.items()))
    combined_digest = _sha256(combined)
    combined_path = os.path.join(args.out_dir, "schema-digest.txt")
    with open(combined_path, "w", encoding="utf-8") as f:
        f.write(combined_digest + "\n")

    print(f"Wrote per-dataset digests to {summary_path}")
    print(f"Wrote combined digest to {combined_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
