#!/usr/bin/env python3
"""Remove one or more plugins from every generated registry entry."""

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGINS_DIR = ROOT / "plugins"
PREFETCH_FILE = ROOT / "nix" / "plugins-prefetch.json"


def plugin_files(plugin_ids: set[str]) -> list[Path]:
    matches = []
    for path in sorted(PLUGINS_DIR.glob("*.json")):
        with path.open() as file:
            metadata = json.load(file)
        if metadata.get("id") in plugin_ids:
            matches.append(path)
    return matches


def prefetch_matches(plugin_ids: set[str]) -> set[str]:
    if not PREFETCH_FILE.is_file():
        return set()

    with PREFETCH_FILE.open() as file:
        entries = json.load(file)

    return {
        key
        for key, entry in entries.items()
        if key in plugin_ids or entry.get("meta", {}).get("id") in plugin_ids
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Purge plugins from plugins/, nix/plugins-prefetch.json, and README.md."
    )
    parser.add_argument("plugin_ids", nargs="+", help="Exact plugin IDs to purge")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be removed"
    )
    args = parser.parse_args()

    plugin_ids = set(args.plugin_ids)
    files = plugin_files(plugin_ids)
    prefetch_keys = prefetch_matches(plugin_ids)
    found_ids = {
        json.loads(path.read_text())["id"] for path in files
    } | prefetch_keys
    missing_ids = sorted(plugin_ids - found_ids)

    if missing_ids:
        parser.error(f"plugin ID not found: {', '.join(missing_ids)}")

    print("Plugin files to remove:")
    for path in files:
        print(f"  {path.relative_to(ROOT)}")
    print(f"Prefetch entries to remove: {', '.join(sorted(prefetch_keys)) or '(none)'}")
    print("README.md will be regenerated.")

    if args.dry_run:
        return 0

    answer = input("Continue? [y/N] ").strip().lower()
    if answer not in {"y", "yes"}:
        print("Cancelled.")
        return 0

    for path in files:
        path.unlink()

    if prefetch_keys:
        with PREFETCH_FILE.open() as file:
            entries = json.load(file)
        for key in prefetch_keys:
            del entries[key]
        PREFETCH_FILE.write_text(json.dumps(entries, sort_keys=True, indent=2))

    subprocess.run(
        [sys.executable, str(ROOT / ".github" / "generate.py")],
        cwd=ROOT,
        check=True,
    )
    print("Purge complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
