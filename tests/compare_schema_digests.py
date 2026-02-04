import argparse
import json
import os
import sys


def _load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _find_artifacts(root: str, prefix: str) -> list[str]:
    if not os.path.isdir(root):
        return []
    return sorted(
        name
        for name in os.listdir(root)
        if name.startswith(prefix) and os.path.isdir(os.path.join(root, name))
    )


def _print_diff(title: str, lines: list[str]) -> None:
    print(title)
    for line in lines:
        print(f"  {line}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare schema digests across matrix")
    parser.add_argument("--artifacts-dir", default="_artifacts")
    parser.add_argument("--artifact-prefix", default="junit-")
    args = parser.parse_args()

    artifacts = _find_artifacts(args.artifacts_dir, args.artifact_prefix)
    if not artifacts:
        print(f"No artifacts found under {args.artifacts_dir}")
        return 1

    digests_by_version = {}
    missing = []
    for name in artifacts:
        digest_path = os.path.join(
            args.artifacts_dir, name, "matrix-results", "schema-digests.json"
        )
        if not os.path.isfile(digest_path):
            missing.append(name)
            continue
        digests_by_version[name] = _load_json(digest_path)

    if missing:
        _print_diff(
            "Missing matrix results for:",
            [f"{name} (schema-digests.json not found)" for name in missing],
        )
        return 1

    if len(digests_by_version) < 2:
        print("Need at least two versions to compare.")
        return 1

    versions = sorted(digests_by_version.keys())
    baseline_version = versions[0]
    baseline = digests_by_version[baseline_version]
    mismatches = []

    baseline_keys = set(baseline.keys())
    for version in versions[1:]:
        keys = set(digests_by_version[version].keys())
        if keys != baseline_keys:
            missing_keys = sorted(baseline_keys - keys)
            extra_keys = sorted(keys - baseline_keys)
            if missing_keys:
                mismatches.append(
                    f"{version} missing datasets: {', '.join(missing_keys)}"
                )
            if extra_keys:
                mismatches.append(
                    f"{version} has extra datasets: {', '.join(extra_keys)}"
                )

    for dataset in sorted(baseline_keys):
        base_digest = baseline[dataset]
        for version in versions[1:]:
            digest = digests_by_version[version].get(dataset)
            if digest != base_digest:
                line = (
                    f"{dataset}: {baseline_version}={base_digest}, "
                    f"{version}={digest}"
                )
                mismatches.append(line)

    if mismatches:
        _print_diff("Schema digest mismatches detected:", mismatches)
        return 1

    print("All schema digests match across matrix.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
