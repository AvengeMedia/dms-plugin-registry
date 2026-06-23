#!/usr/bin/env python3
"""Reconcile GitHub issues with the plugin registry.

Each plugin gets one tracking issue used as its forum and upvote surface. This script
creates issues for new plugins, reopens issues for plugins that returned, and closes
issues for plugins removed from the registry. Issues are matched back to a plugin via a
hidden ``<!-- dms-plugin-id: <id> -->`` marker in the body.
"""

import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import requests

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "AvengeMedia/dms-plugin-registry")
API_BASE = "https://api.github.com"
DIRECTORY_URL = "https://danklinux.com/plugins"

PLUGIN_LABEL = "plugin"
PLUGIN_LABEL_COLOR = "1f6feb"
MARKER_RE = re.compile(r"<!--\s*dms-plugin-id:\s*([A-Za-z0-9]+)\s*-->")
CREATE_DELAY_SECONDS = 3.0

DRY_RUN = "--dry-run" in sys.argv


def only_filter() -> str:
    for i, arg in enumerate(sys.argv):
        if arg == "--only" and i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return ""


ONLY = only_filter()


def headers() -> dict:
    base = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        base["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return base


def api(method: str, path: str, **kwargs) -> requests.Response:
    url = path if path.startswith("http") else f"{API_BASE}{path}"
    response = requests.request(method, url, headers=headers(), timeout=30, **kwargs)
    response.raise_for_status()
    return response


def load_plugins(plugins_dir: Path) -> dict[str, dict]:
    plugins = {}
    for json_file in sorted(plugins_dir.glob("*.json")):
        with open(json_file) as f:
            plugin = json.load(f)
        plugin_id = plugin.get("id")
        if not plugin_id:
            print(f"Skipping {json_file.name}: missing id", file=sys.stderr)
            continue
        plugins[plugin_id] = plugin
    return plugins


def to_raw(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc == "github.com" and "/blob/" in parsed.path:
        return f"https://raw.githubusercontent.com{parsed.path.replace('/blob/', '/', 1)}"
    return url


def github_handle(plugin: dict) -> str:
    parsed = urlparse(plugin.get("repo", ""))
    if parsed.netloc != "github.com":
        return ""
    parts = parsed.path.strip("/").split("/")
    return parts[0] if parts and parts[0] else ""


def build_title(plugin: dict) -> str:
    name = plugin.get("name", plugin["id"])
    author = plugin.get("author", "Unknown")
    return f"[plugin] {name} by {author}"


def build_body(plugin: dict) -> str:
    lines = []

    description = plugin.get("description", "")
    if description:
        lines += [f"> {description}", ""]

    lines += [f"**Author:** {plugin.get('author', 'Unknown')}"]

    handle = github_handle(plugin)
    if handle:
        lines += [f"**Maintainer:** @{handle}"]

    repo = plugin.get("repo", "")
    if repo:
        lines += [f"**Repository:** {repo}"]

    category = plugin.get("category", "")
    if category:
        lines += [f"**Category:** {category}"]

    compositors = plugin.get("compositors", [])
    if compositors:
        lines += [f"**Compositors:** {', '.join(compositors)}"]

    dependencies = plugin.get("dependencies", [])
    if dependencies:
        lines += [f"**Dependencies:** {', '.join(dependencies)}"]

    lines += ["", f"**Install:** `dms plugins install {plugin['id']}`", ""]

    screenshot = plugin.get("screenshot", "")
    if screenshot:
        lines += [f"![{plugin.get('name', plugin['id'])}]({to_raw(screenshot)})", ""]

    lines += [
        "---",
        "",
        f"👍 **Upvote** this issue to rank this plugin higher in the [directory]({DIRECTORY_URL}).",
        "",
        "Plugin moderators update status with `/broken` `/working` `/unmaintained` `/deprecated` `/verified`.",
        "",
        f"<!-- dms-plugin-id: {plugin['id']} -->",
    ]

    return "\n".join(lines)


def ensure_plugin_label() -> None:
    try:
        api("GET", f"/repos/{GITHUB_REPOSITORY}/labels/{PLUGIN_LABEL}")
        return
    except requests.HTTPError as e:
        if e.response is None or e.response.status_code != 404:
            raise

    if DRY_RUN:
        print(f"[dry-run] would create label '{PLUGIN_LABEL}'")
        return

    api(
        "POST",
        f"/repos/{GITHUB_REPOSITORY}/labels",
        json={"name": PLUGIN_LABEL, "color": PLUGIN_LABEL_COLOR, "description": "Plugin tracking issue"},
    )


def fetch_plugin_issues() -> dict[str, dict]:
    issues = {}
    page = 1
    while True:
        response = api(
            "GET",
            f"/repos/{GITHUB_REPOSITORY}/issues",
            params={"labels": PLUGIN_LABEL, "state": "all", "per_page": 100, "page": page},
        )
        batch = response.json()
        if not batch:
            break

        for issue in batch:
            if "pull_request" in issue:
                continue
            match = MARKER_RE.search(issue.get("body") or "")
            if not match:
                continue
            issues[match.group(1)] = issue

        page += 1

    return issues


def create_issue(plugin: dict) -> None:
    if DRY_RUN:
        print(f"[dry-run] would create issue for '{plugin['id']}': {build_title(plugin)}")
        return

    response = api(
        "POST",
        f"/repos/{GITHUB_REPOSITORY}/issues",
        json={"title": build_title(plugin), "body": build_body(plugin), "labels": [PLUGIN_LABEL]},
    )
    number = response.json()["number"]
    api("POST", f"/repos/{GITHUB_REPOSITORY}/issues/{number}/reactions", json={"content": "+1"})
    time.sleep(CREATE_DELAY_SECONDS)


def sync_issue_content(issue: dict, plugin: dict) -> bool:
    title = build_title(plugin)
    body = build_body(plugin)

    body_matches = (issue.get("body") or "").replace("\r\n", "\n").strip() == body.strip()
    if issue.get("title") == title and body_matches:
        return False

    if DRY_RUN:
        print(f"[dry-run] would update content of issue #{issue['number']} ({plugin['id']})")
        return True

    api(
        "PATCH",
        f"/repos/{GITHUB_REPOSITORY}/issues/{issue['number']}",
        json={"title": title, "body": body},
    )
    return True


def set_issue_state(issue: dict, state: str, comment: str = "") -> None:
    number = issue["number"]
    if DRY_RUN:
        print(f"[dry-run] would set issue #{number} to {state}")
        return

    if comment:
        api("POST", f"/repos/{GITHUB_REPOSITORY}/issues/{number}/comments", json={"body": comment})

    payload = {"state": state}
    if state == "closed":
        payload["state_reason"] = "not_planned"
    api("PATCH", f"/repos/{GITHUB_REPOSITORY}/issues/{number}", json=payload)


def reconcile() -> int:
    if not GITHUB_TOKEN and not DRY_RUN:
        print("GITHUB_TOKEN is required", file=sys.stderr)
        return 1

    plugins_dir = Path(__file__).parent.parent / "plugins"
    plugins = load_plugins(plugins_dir)

    if ONLY:
        plugins = {ONLY: plugins[ONLY]} if ONLY in plugins else {}
        if not plugins:
            print(f"Plugin '{ONLY}' not found", file=sys.stderr)
            return 1

    ensure_plugin_label()
    issues = fetch_plugin_issues()

    created = reopened = closed = updated = 0

    for plugin_id, plugin in plugins.items():
        issue = issues.get(plugin_id)
        if issue is None:
            create_issue(plugin)
            created += 1
            continue
        if issue["state"] == "closed":
            set_issue_state(issue, "open", "Plugin is back in the registry; reopening.")
            reopened += 1
        if sync_issue_content(issue, plugin):
            updated += 1

    if not ONLY:
        for plugin_id, issue in issues.items():
            if plugin_id in plugins:
                continue
            if issue["state"] == "closed":
                continue
            set_issue_state(issue, "closed", "Plugin was removed from the registry; closing.")
            closed += 1

    print(f"Reconciled: {created} created, {reopened} reopened, {updated} updated, {closed} closed")
    return 0


if __name__ == "__main__":
    sys.exit(reconcile())
