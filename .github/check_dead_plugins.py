#!/usr/bin/env python3
"""Detect plugins whose upstream repository is gone and open a removal PR.

A plugin only counts as gone when the host API answers 404/410/451 on every check
of a run, on REQUIRED_STRIKES consecutive runs, while a control repository on the
same host still answers 200. Anything else (timeouts, 403 rate limits, 5xx, an
unsupported host) is inconclusive and never accrues a strike. Strike state lives
in .github/plugin-health.json.

Confirmed removals get one PR each deleting the registry entry, dropping the nix
prefetch entry and regenerating README.md. Nothing is merged automatically.
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlparse

import requests

import ensure_issues

REPO_ROOT = Path(__file__).parent.parent
PLUGINS_DIR = REPO_ROOT / "plugins"
PREFETCH_PATH = REPO_ROOT / "nix" / "plugins-prefetch.json"
STATE_PATH = REPO_ROOT / ".github" / "plugin-health.json"

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "AvengeMedia/dms-plugin-registry")
BASE_BRANCH = os.environ.get("BASE_BRANCH", "master")
MODERATORS = [m.strip().lstrip("@") for m in os.environ.get("PLUGIN_MODERATORS", "").split(",") if m.strip()]
REQUIRED_STRIKES = int(os.environ.get("REQUIRED_STRIKES", "3"))
MAX_DEAD_PER_RUN = int(os.environ.get("MAX_DEAD_PER_RUN", "5"))
RECHECK_DELAYS = [int(d) for d in os.environ.get("RECHECK_DELAYS", "5,20").split(",") if d.strip()]

ALIVE = "alive"
GONE = "gone"
UNKNOWN = "unknown"
GONE_CODES = {404, 410, 451}

BRANCH_PREFIX = "bot/remove-plugin-"
REMOVAL_LABEL = "plugin-removal"
REMOVAL_LABEL_COLOR = "b60205"

CONTROL_REPOS = {
    "github.com": "https://github.com/AvengeMedia/dms-plugin-registry",
    "gitlab.com": "https://gitlab.com/gitlab-org/gitlab",
    "codeberg.org": "https://codeberg.org/forgejo/forgejo",
}

DRY_RUN = "--dry-run" in sys.argv


def only_filter() -> str:
    for i, arg in enumerate(sys.argv):
        if arg == "--only" and i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return ""


ONLY = only_filter()


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(args, cwd=REPO_ROOT, text=True, capture_output=True)
    if check and result.returncode != 0:
        raise RuntimeError(f"{' '.join(args)} failed:\n{result.stdout}\n{result.stderr}")
    return result


def load_plugins() -> dict[str, dict]:
    plugins = {}
    for json_file in sorted(PLUGINS_DIR.glob("*.json")):
        with open(json_file) as f:
            plugin = json.load(f)
        plugin_id = plugin.get("id")
        if not plugin_id:
            print(f"Skipping {json_file.name}: missing id", file=sys.stderr)
            continue
        plugin["_file"] = json_file
        plugins[plugin_id] = plugin
    return plugins


def load_state() -> dict:
    if not STATE_PATH.is_file():
        return {"plugins": {}}
    with open(STATE_PATH) as f:
        state = json.load(f)
    state.setdefault("plugins", {})
    return state


def save_state(state: dict) -> None:
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2, sort_keys=True)
        f.write("\n")


def repo_parts(repo_url: str) -> tuple[str, str, str]:
    parsed = urlparse(repo_url)
    path = parsed.path.strip("/")
    if path.endswith(".git"):
        path = path[:-4]
    parts = path.split("/")
    if len(parts) < 2:
        return parsed.netloc, "", ""
    return parsed.netloc, parts[0], parts[1]


def api_endpoint(repo_url: str) -> str:
    host, owner, repo = repo_parts(repo_url)
    if not owner or not repo:
        return ""
    if host == "github.com":
        return f"https://api.github.com/repos/{owner}/{repo}"
    if host == "gitlab.com":
        return f"https://gitlab.com/api/v4/projects/{quote(f'{owner}/{repo}', safe='')}"
    if host == "codeberg.org":
        return f"https://codeberg.org/api/v1/repos/{owner}/{repo}"
    return ""


def check_repo(repo_url: str) -> tuple[str, str]:
    endpoint = api_endpoint(repo_url)
    if not endpoint:
        return UNKNOWN, f"no API for {repo_parts(repo_url)[0]}"

    headers = {"Accept": "application/json"}
    if GITHUB_TOKEN and endpoint.startswith("https://api.github.com/"):
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    try:
        response = requests.get(endpoint, headers=headers, timeout=20, allow_redirects=True)
    except requests.RequestException as e:
        return UNKNOWN, f"request failed: {e}"

    if response.status_code == 200:
        return ALIVE, "HTTP 200"
    if response.status_code in GONE_CODES:
        return GONE, f"HTTP {response.status_code}"
    return UNKNOWN, f"HTTP {response.status_code}"


def host_is_healthy(host: str, cache: dict[str, bool]) -> bool:
    if host in cache:
        return cache[host]
    control = CONTROL_REPOS.get(host, "")
    healthy = bool(control) and check_repo(control)[0] == ALIVE
    cache[host] = healthy
    if not healthy:
        print(f"  control repo for {host} is not answering; treating its results as inconclusive")
    return healthy


def confirm_gone(plugin: dict) -> tuple[bool, str]:
    detail = ""
    for delay in RECHECK_DELAYS:
        time.sleep(delay)
        status, detail = check_repo(plugin["repo"])
        if status != GONE:
            return False, detail
    return True, detail


def gh_json(*args: str) -> list | dict:
    result = run("gh", *args, check=False)
    if result.returncode != 0:
        return []
    try:
        return json.loads(result.stdout or "[]")
    except json.JSONDecodeError:
        return []


def open_pr_number(branch: str) -> int:
    prs = gh_json("pr", "list", "--repo", GITHUB_REPOSITORY, "--head", branch, "--state", "open", "--json", "number")
    return prs[0]["number"] if prs else 0


def pr_state(number: int) -> str:
    data = gh_json("pr", "view", str(number), "--repo", GITHUB_REPOSITORY, "--json", "state")
    return data.get("state", "") if isinstance(data, dict) else ""


def ensure_removal_label() -> None:
    run(
        "gh", "label", "create", REMOVAL_LABEL,
        "--repo", GITHUB_REPOSITORY,
        "--color", REMOVAL_LABEL_COLOR,
        "--description", "Upstream repository is gone; needs moderator review",
        "--force",
        check=False,
    )


def prune_prefetch(plugin_id: str) -> bool:
    if not PREFETCH_PATH.is_file():
        return False
    with open(PREFETCH_PATH) as f:
        prefetch = json.load(f)
    if plugin_id not in prefetch:
        return False
    del prefetch[plugin_id]
    with open(PREFETCH_PATH, "w") as f:
        json.dump(prefetch, f, sort_keys=True, indent=2)
    return True


def pr_body(plugin: dict, entry: dict, issue_number: int) -> str:
    host = repo_parts(plugin["repo"])[0]
    lines = [
        f"The upstream repository for **{plugin.get('name', plugin['id'])}** is gone.",
        "",
        f"- **Repository:** {plugin['repo']}",
        f"- **Status:** {entry['status']}",
        f"- **First failed:** {entry['first_failed']}",
        f"- **Consecutive daily checks failed:** {entry['strikes']}",
        "",
        f"Every check answered {entry['status']} while a control repository on {host} answered "
        "HTTP 200 in the same run, so this is not a host outage or a rate limit.",
        "",
        "This PR deletes the registry entry, drops it from `nix/plugins-prefetch.json` and "
        "regenerates `README.md`. On merge the plugin's tracking issue is closed and the plugin "
        "is dropped from every **Related plugins** list that links it.",
        "",
        "**Do not merge** if the repository was renamed, moved or made private on purpose. "
        "Update the `repo` URL in the plugin's registry JSON instead and this PR closes itself "
        "on the next run.",
    ]
    if issue_number:
        lines += ["", f"Tracking issue: #{issue_number}"]
    if MODERATORS:
        lines += ["", " ".join(f"@{m}" for m in MODERATORS)]
    lines += ["", f"<!-- dms-dead-plugin: {plugin['id']} -->"]
    return "\n".join(lines)


def open_removal_pr(plugin: dict, entry: dict, issue_number: int) -> int:
    plugin_id = plugin["id"]
    name = plugin.get("name", plugin_id)
    branch = f"{BRANCH_PREFIX}{plugin_id}"

    existing = open_pr_number(branch)
    if existing:
        print(f"  PR #{existing} already open for {plugin_id}")
        return existing

    if DRY_RUN:
        print(f"  [dry-run] would open removal PR for {plugin_id} ({entry['status']})")
        return 0

    run("git", "checkout", "--force", "-B", branch, f"origin/{BASE_BRANCH}")
    try:
        plugin["_file"].unlink()
        prune_prefetch(plugin_id)
        run(sys.executable, ".github/generate.py")
        run("git", "add", "--all", "plugins", "nix/plugins-prefetch.json", "README.md")
        run(
            "git",
            "-c", "user.name=dms-ci[bot]",
            "-c", "user.email=dms-ci[bot]@users.noreply.github.com",
            "commit", "-m", f"chore: remove {name} plugin (upstream repository gone)",
        )
        run("git", "push", "--force", "origin", f"HEAD:refs/heads/{branch}")

        ensure_removal_label()
        args = [
            "gh", "pr", "create",
            "--repo", GITHUB_REPOSITORY,
            "--base", BASE_BRANCH,
            "--head", branch,
            "--title", f"chore: remove {name} plugin (upstream repository gone)",
            "--body", pr_body(plugin, entry, issue_number),
            "--label", REMOVAL_LABEL,
        ]
        for moderator in MODERATORS:
            args += ["--reviewer", moderator]
        created = run(*args, check=False)
        if created.returncode != 0:
            print(f"  gh pr create failed for {plugin_id}: {created.stderr.strip()}", file=sys.stderr)
    finally:
        run("git", "checkout", "--force", BASE_BRANCH, check=False)
        run("git", "reset", "--hard", f"origin/{BASE_BRANCH}", check=False)

    number = open_pr_number(branch)
    print(f"  opened PR #{number} to remove {plugin_id}")
    return number


def comment_on_issue(issue_number: int, body: str) -> None:
    if not issue_number:
        return
    if DRY_RUN:
        print(f"  [dry-run] would comment on issue #{issue_number}")
        return
    run("gh", "issue", "comment", str(issue_number), "--repo", GITHUB_REPOSITORY, "--body", body, check=False)


def close_stale_pr(plugin_id: str) -> None:
    branch = f"{BRANCH_PREFIX}{plugin_id}"
    number = open_pr_number(branch)
    if not number:
        return
    if DRY_RUN:
        print(f"  [dry-run] would close recovered PR #{number}")
        return
    run(
        "gh", "pr", "close", str(number),
        "--repo", GITHUB_REPOSITORY,
        "--delete-branch",
        "--comment", "The repository is reachable again; closing.",
        check=False,
    )
    print(f"  closed PR #{number}, {plugin_id} is reachable again")


def plugin_issues() -> dict[str, dict]:
    if not GITHUB_TOKEN:
        return {}
    try:
        return ensure_issues.fetch_plugin_issues()
    except Exception as e:
        print(f"Could not load plugin issues: {e}", file=sys.stderr)
        return {}


def main() -> int:
    plugins = load_plugins()
    if ONLY:
        plugins = {ONLY: plugins[ONLY]} if ONLY in plugins else {}
        if not plugins:
            print(f"Plugin '{ONLY}' not found", file=sys.stderr)
            return 1

    state = load_state()
    entries = state["plugins"]
    host_health: dict[str, bool] = {}

    gone: dict[str, tuple[dict, str]] = {}
    recovered: list[str] = []
    inconclusive = 0

    print(f"Checking {len(plugins)} plugin repositories...")
    for plugin_id, plugin in plugins.items():
        status, detail = check_repo(plugin["repo"])

        if status == ALIVE:
            if plugin_id in entries:
                recovered.append(plugin_id)
            continue

        if status == UNKNOWN:
            inconclusive += 1
            print(f"  {plugin_id}: inconclusive ({detail})")
            continue

        if not host_is_healthy(repo_parts(plugin["repo"])[0], host_health):
            inconclusive += 1
            continue

        confirmed, recheck_detail = confirm_gone(plugin)
        if not confirmed:
            inconclusive += 1
            print(f"  {plugin_id}: first check {detail}, recheck {recheck_detail}; not counted")
            continue

        print(f"  {plugin_id}: gone ({detail})")
        gone[plugin_id] = (plugin, detail)

    if len(gone) > MAX_DEAD_PER_RUN:
        print(
            f"::error::{len(gone)} repositories look gone in one run (limit {MAX_DEAD_PER_RUN}); "
            "refusing to touch state or open PRs, this looks like an infrastructure problem",
            file=sys.stderr,
        )
        return 1

    for plugin_id in recovered:
        del entries[plugin_id]
        close_stale_pr(plugin_id)

    if not ONLY:
        for plugin_id in [p for p in entries if p not in plugins]:
            del entries[plugin_id]

    issues = plugin_issues() if gone else {}

    for plugin_id, (plugin, detail) in gone.items():
        entry = entries.get(plugin_id)
        if entry is None or entry.get("repo") != plugin["repo"]:
            entry = {"repo": plugin["repo"], "first_failed": now(), "strikes": 0}
        entry["status"] = detail
        # One strike per day, so re-running the workflow by hand cannot rush a removal.
        if entry.get("last_failed", "")[:10] != now()[:10]:
            entry["strikes"] += 1
        entry["last_failed"] = now()
        entries[plugin_id] = entry

        if entry["strikes"] < REQUIRED_STRIKES:
            print(f"  {plugin_id}: strike {entry['strikes']}/{REQUIRED_STRIKES}, waiting for more runs")
            continue

        if entry.get("dismissed"):
            print(f"  {plugin_id}: removal PR was closed by a moderator, leaving it alone")
            continue

        if entry.get("pr") and pr_state(entry["pr"]) == "CLOSED":
            entry["dismissed"] = True
            print(f"  {plugin_id}: PR #{entry['pr']} was closed without merging, not re-proposing")
            continue

        issue_number = (issues.get(plugin_id) or {}).get("number", 0)
        number = open_removal_pr(plugin, entry, issue_number)
        if number and number != entry.get("pr"):
            entry["pr"] = number
            comment_on_issue(
                issue_number,
                f"The repository for this plugin has answered {detail} on {entry['strikes']} "
                f"consecutive daily checks, so it looks deleted. Removal PR for moderator "
                f"review: #{number}",
            )

    if DRY_RUN:
        print(json.dumps(state, indent=2, sort_keys=True))
    else:
        save_state(state)

    print(
        f"Done: {len(gone)} gone, {len(recovered)} recovered, {inconclusive} inconclusive, "
        f"{len(plugins) - len(gone) - inconclusive} alive"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
