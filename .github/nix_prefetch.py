#!/usr/bin/env python3
"""Generate nix/plugins-prefetch.json from plugins/*.json"""

import json
import subprocess
from pathlib import Path

root = Path.cwd()
plugins_dir = root / "plugins"
output_path = root / "nix/plugins-prefetch.json"

result = {}

def run_prefetch(repo):
    cmd = [
        "nix",
        "shell",
        "nixpkgs#nix-prefetch-git",
        "--command",
        "nix-prefetch-git",
        repo,
    ]
    run = subprocess.run(
        cmd,
        check=True,
        text=True,
        capture_output=True,
    )
    return run.stdout

for plugin_file in plugins_dir.iterdir():
    if not plugin_file.is_file():
        continue

    with plugin_file.open() as f:
        meta = json.load(f)

    plugin_id = meta["id"]
    repo = meta["repo"]

    print(f"fetching plugin {plugin_id} from {repo}")

    # Run nix-prefetch-git
    prefetch = json.loads(run_prefetch(repo))

    # Locate plugin.json
    base_path = Path(prefetch["path"])
    sub_path = meta.get("path", "")
    plugin_json = base_path / sub_path / "plugin.json"

    # Attach metadata
    prefetch["meta"] = meta

    # Add version if it exists
    if plugin_json.is_file():
        with plugin_json.open() as f:
            plugin_info = json.load(f)
        if "version" in plugin_info:
            prefetch["meta"]["version"] = plugin_info["version"]

    result[plugin_id] = prefetch

with output_path.open("w") as f:
    json.dump(
        result,
        f,
        sort_keys=True, # prevent order changes to reduce diffs
        indent=2
    )
