#!/usr/bin/env python3
"""Handle moderator slash-commands posted as comments on plugin tracking issues.

Commands are honored only when the commenter belongs to the configured moderator team.
Each command maps to a status label that is added to or removed from the issue.
"""

import os
import sys

import requests

API_BASE = "https://api.github.com"

GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "AvengeMedia/dms-plugin-registry")
GITHUB_ORG = os.environ.get("GITHUB_ORG", "AvengeMedia")
MOD_TEAM = os.environ.get("MOD_TEAM", "plugin-moderators")

WRITE_TOKEN = os.environ.get("GITHUB_TOKEN")
MOD_TOKEN = os.environ.get("MOD_TOKEN") or WRITE_TOKEN

ISSUE_NUMBER = os.environ.get("ISSUE_NUMBER")
COMMENT_ID = os.environ.get("COMMENT_ID")
COMMENT_USER = os.environ.get("COMMENT_USER", "")
COMMENT_BODY = os.environ.get("COMMENT_BODY", "")

STATUS_LABELS = {
    "status:broken": ("b60205", "Reported broken"),
    "status:unmaintained": ("fbca04", "No longer maintained"),
    "status:deprecated": ("cccccc", "Deprecated / retired"),
    "status:verified": ("0e8a16", "Reviewed by maintainers"),
}

COMMANDS = {
    "/broken": ("add", "status:broken"),
    "/working": ("remove", "status:broken"),
    "/unmaintained": ("add", "status:unmaintained"),
    "/deprecated": ("add", "status:deprecated"),
    "/verified": ("add", "status:verified"),
}


def api(method: str, path: str, token: str, **kwargs) -> requests.Response:
    url = path if path.startswith("http") else f"{API_BASE}{path}"
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return requests.request(method, url, headers=headers, timeout=30, **kwargs)


def parse_commands(body: str) -> list[tuple[str, str]]:
    actions = []
    seen = set()
    for word in body.split():
        command = COMMANDS.get(word.lower())
        if command and word.lower() not in seen:
            seen.add(word.lower())
            actions.append(command)
    return actions


def is_moderator(username: str) -> bool:
    response = api(
        "GET",
        f"/orgs/{GITHUB_ORG}/teams/{MOD_TEAM}/memberships/{username}",
        MOD_TOKEN,
    )
    if response.status_code != 200:
        return False
    return response.json().get("state") == "active"


def ensure_label(name: str) -> None:
    response = api("GET", f"/repos/{GITHUB_REPOSITORY}/labels/{name}", WRITE_TOKEN)
    if response.status_code == 200:
        return

    color, description = STATUS_LABELS[name]
    api(
        "POST",
        f"/repos/{GITHUB_REPOSITORY}/labels",
        WRITE_TOKEN,
        json={"name": name, "color": color, "description": description},
    )


def apply_action(action: str, label: str) -> None:
    match action:
        case "add":
            ensure_label(label)
            api(
                "POST",
                f"/repos/{GITHUB_REPOSITORY}/issues/{ISSUE_NUMBER}/labels",
                WRITE_TOKEN,
                json={"labels": [label]},
            )
        case "remove":
            api(
                "DELETE",
                f"/repos/{GITHUB_REPOSITORY}/issues/{ISSUE_NUMBER}/labels/{label}",
                WRITE_TOKEN,
            )


def react(content: str) -> None:
    if not COMMENT_ID:
        return
    api(
        "POST",
        f"/repos/{GITHUB_REPOSITORY}/issues/comments/{COMMENT_ID}/reactions",
        WRITE_TOKEN,
        json={"content": content},
    )


def main() -> int:
    actions = parse_commands(COMMENT_BODY)
    if not actions:
        return 0

    if not is_moderator(COMMENT_USER):
        react("confused")
        return 0

    for action, label in actions:
        apply_action(action, label)

    react("+1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
