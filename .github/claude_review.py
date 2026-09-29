#!/usr/bin/env python3
"""Plumbing for .github/workflows/claude-review.yml. Runs with secrets: never execute anything from a PR or plugin repo."""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

REPO_ROOT = Path(__file__).parent.parent
PLUGINS_DIR = REPO_ROOT / "plugins"
REVIEW_DIR = REPO_ROOT / "review"
PR_DIR = REVIEW_DIR / "pr"
SOURCE_DIR = REVIEW_DIR / "src"
DMS_DIR = REVIEW_DIR / "dms"

MARKER = "<!-- claude-review -->"
BOT_LOGIN = "github-actions[bot]"
PLUGIN_LABEL = "plugin"
MAX_OPEN_PRS_PER_AUTHOR = 3
MAX_REVIEWS_PER_PR = 8
MAX_PLUGIN_BATCH = 25
MAX_SOURCES = 5
MAX_FINDINGS = 15
CLONE_TIMEOUT = 180

DMS_REPO = "https://github.com/AvengeMedia/DankMaterialShell"
DMS_PATHS = [
    ".agents/skills/dms-plugin-dev",
    "quickshell/Common",
    "quickshell/Modules/Plugins",
    "quickshell/PLUGINS",
    "quickshell/Services",
    "quickshell/Widgets",
]
UNTRUSTED_AGENT_CONFIG = {".claude", "CLAUDE.md", "CLAUDE.local.md"}

REPO_URL = re.compile(r"^https://(github\.com|gitlab\.com|codeberg\.org)/([\w.-]+)/([\w.-]+?)(?:\.git)?/?$", re.ASCII)
SAFE_PATH = re.compile(r"^[\w.-]+(?:/[\w.-]+)*$", re.ASCII)
PLUGIN_FILE = re.compile(r"^plugins/(\w[\w.-]*)\.json$", re.ASCII)
THEME_FILE = re.compile(r"^themes/(\w[\w.-]*)/", re.ASCII)
PLUGIN_MARKER = re.compile(r"<!--\s*dms-plugin-id:\s*([A-Za-z0-9]+)\s*-->")
BLOB_URL = {
    "github.com": "{repo}/blob/{sha}/",
    "gitlab.com": "{repo}/-/blob/{sha}/",
    "codeberg.org": "{repo}/src/commit/{sha}/",
}

SECRET = re.compile(r"sk-ant-|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_|eyJ[\w-]{10,}\.eyJ")
CODE_SPAN = re.compile(r"(`[^`\n]*`)")
MENTION = re.compile(r"@(?=[\w-])")
VERDICTS = {
    "pr": {"ready": "ready", "needs-changes": "needs changes", "reject": "recommend closing"},
    "plugin": {"ready": "ready", "needs-changes": "needs changes", "reject": "recommend removal"},
}
SEVERITIES = {"blocker", "issue"}
MINIMIZE = "mutation($id: ID!) { minimizeComment(input: {subjectId: $id, classifier: OUTDATED}) { clientMutationId } }"


def run(*args: str, cwd: Path | None = None, timeout: int | None = None, stdin: str | None = None) -> str:
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_LFS_SKIP_SMUDGE": "1"}
    result = subprocess.run(
        args, cwd=cwd, env=env, timeout=timeout, input=stdin, check=True, capture_output=True, text=True
    )
    return result.stdout


def gh_json(*args: str) -> list | dict:
    return json.loads(run("gh", *args))


def set_output(name: str, value: str) -> None:
    with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        f.write(f"{name}={value}\n")


def safe_path(path: str) -> bool:
    return bool(SAFE_PATH.match(path)) and ".." not in path.split("/")


def read_json(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def event_payload() -> dict:
    return json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())


def review_comments(repo: str, number: int) -> list[dict]:
    pages = gh_json("api", f"repos/{repo}/issues/{number}/comments", "--paginate", "--slurp")
    return [
        c for page in pages for c in page if c["user"]["login"] == BOT_LOGIN and c["body"].startswith(MARKER)
    ]


def registry_stem(plugin_id: str) -> str | None:
    for path in sorted(PLUGINS_DIR.glob("*.json")):
        if (read_json(path) or {}).get("id") == plugin_id:
            return path.stem
    return None


def pr_target(number: int) -> dict:
    return {"kind": "pr", "number": number, "label": f"#{number}", "plugin": ""}


def plugin_target(plugin_id: str, issue: int) -> dict:
    return {"kind": "plugin", "number": issue, "label": plugin_id, "plugin": plugin_id}


def event_prs(repo: str) -> list[int]:
    pr = event_payload()["pull_request"]
    author = pr["user"]["login"]
    if pr["draft"] or pr["user"]["type"] == "Bot":
        return []

    open_prs = gh_json("pr", "list", "--author", author, "--state", "open", "--limit", "100", "--json", "number")
    if len(open_prs) > MAX_OPEN_PRS_PER_AUTHOR:
        print(f"skipping: {author} has {len(open_prs)} open PRs")
        return []

    if len(review_comments(repo, pr["number"])) >= MAX_REVIEWS_PER_PR:
        print(f"skipping: #{pr['number']} already has {MAX_REVIEWS_PER_PR} reviews, dispatch to force one")
        return []

    return [pr["number"]]


def backfill_prs(repo: str) -> list[int]:
    prs = gh_json(
        "pr", "list", "--state", "open", "--base", "master", "--limit", "100", "--json", "number,isDraft,author"
    )
    return [
        p["number"]
        for p in prs
        if not p["isDraft"] and not p["author"]["is_bot"] and not review_comments(repo, p["number"])
    ]


def plugin_issues() -> dict[str, int]:
    issues = gh_json(
        "issue", "list", "--label", PLUGIN_LABEL, "--state", "open", "--limit", "1000", "--json", "number,body"
    )
    return {m.group(1): i["number"] for i in issues if (m := PLUGIN_MARKER.search(i["body"]))}


def plugin_targets(repo: str, requested: str) -> list[dict]:
    issues = plugin_issues()
    if requested != "all":
        ids = requested.replace(",", " ").split()
        unknown = [i for i in ids if i not in issues]
        if unknown:
            print(f"no open tracking issue for: {', '.join(unknown)}")
        return [plugin_target(i, issues[i]) for i in ids if i in issues]

    picked = []
    for plugin_id, issue in sorted(issues.items()):
        if len(picked) >= MAX_PLUGIN_BATCH:
            break
        if not review_comments(repo, issue):
            picked.append(plugin_target(plugin_id, issue))
    return picked


def pick_targets(repo: str) -> list[dict]:
    if os.environ["GITHUB_EVENT_NAME"] == "pull_request_target":
        return [pr_target(n) for n in event_prs(repo)]
    if pr := os.environ.get("PR_INPUT"):
        return [pr_target(int(pr))]
    if plugins := os.environ.get("PLUGINS_INPUT", "").strip():
        return plugin_targets(repo, plugins)
    return [pr_target(n) for n in backfill_prs(repo)]


def targets() -> None:
    picked = pick_targets(os.environ["GH_REPO"])
    print(f"reviewing: {[t['label'] for t in picked]}")
    set_output("targets", json.dumps(picked))


def fetch_source(stem: str, plugin: dict) -> dict:
    match = REPO_URL.match(str(plugin.get("repo", "")))
    if not match:
        return {"error": "repo is not a github.com, gitlab.com or codeberg.org repository URL, source not fetched"}

    host, owner, name = match.groups()
    url = f"https://{host}/{owner}/{name}"
    subdir = str(plugin.get("path", "")).strip("/")
    if subdir and not safe_path(subdir):
        return {"url": url, "error": "path is not a plain relative path, source not fetched"}

    dest = SOURCE_DIR / stem
    try:
        run("git", "clone", "--depth", "1", "--no-tags", "--quiet", "--", f"{url}.git", str(dest), timeout=CLONE_TIMEOUT)
        sha = run("git", "rev-parse", "HEAD", cwd=dest).strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return {"url": url, "error": "clone failed, source not reviewed"}

    plugin_dir = dest / subdir if subdir else dest
    return {
        "url": url,
        "sha": sha,
        "dir": plugin_dir.relative_to(REPO_ROOT).as_posix(),
        "prefix": f"{dest.relative_to(REPO_ROOT).as_posix()}/",
        "blob": BLOB_URL[host].format(repo=url, sha=sha),
        "label": f"{owner}/{name}@{sha[:7]}",
    }


def plugin_entry(stem: str, entry_root: Path, fetch: bool) -> dict:
    rel = f"plugins/{stem}.json"
    entry = entry_root / rel
    if not entry.exists():
        return {"file": rel, "status": "removed"}

    status = "listed" if entry_root == REPO_ROOT else "updated" if (REPO_ROOT / rel).exists() else "new"
    base = {"file": rel, "entry": entry.relative_to(REPO_ROOT).as_posix(), "status": status}
    plugin = read_json(entry)
    if plugin is None:
        return {**base, "error": "not a valid JSON object, CI reports this"}
    if not fetch:
        return {**base, "error": f"over the {MAX_SOURCES} plugin limit, source not fetched"}
    return {**base, "source": fetch_source(stem, plugin)}


def fetch_dms() -> str:
    try:
        run("git", "clone", "--depth", "1", "--filter=blob:none", "--sparse", "--quiet", DMS_REPO, str(DMS_DIR),
            timeout=CLONE_TIMEOUT)
        run("git", "sparse-checkout", "set", *DMS_PATHS, cwd=DMS_DIR, timeout=CLONE_TIMEOUT)
        return run("git", "rev-parse", "HEAD", cwd=DMS_DIR).strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return ""


def strip_untrusted(root: Path) -> None:
    for dirpath, dirnames, filenames in os.walk(root, topdown=False):
        for name in dirnames + filenames:
            path = Path(dirpath, name)
            if path.is_symlink() or (name in UNTRUSTED_AGENT_CONFIG and path.is_file()):
                path.unlink()
            elif name in UNTRUSTED_AGENT_CONFIG:
                shutil.rmtree(path)


def write_diff(pr: int) -> None:
    try:
        diff = run("gh", "pr", "diff", str(pr))
    except subprocess.CalledProcessError:
        diff = "diff unavailable, read the changed files under review/pr instead\n"
    (REVIEW_DIR / "pr.diff").write_text(diff)


def stage_pr(pr: int) -> tuple[str, list[str], list[dict], list[str]]:
    head = run("git", "rev-parse", "HEAD", cwd=PR_DIR).strip()
    info = gh_json("pr", "view", str(pr), "--json", "number,title,body,author,url,baseRefName,files")
    (REVIEW_DIR / "pr.json").write_text(json.dumps(info, indent=2))
    write_diff(pr)

    paths = [f["path"] for f in info["files"]]
    stems = sorted({m.group(1) for p in paths if (m := PLUGIN_FILE.match(p))})
    themes = sorted({m.group(1) for p in paths if (m := THEME_FILE.match(p))})
    plugins = [plugin_entry(stem, PR_DIR, fetch=i < MAX_SOURCES) for i, stem in enumerate(stems)]
    header = [
        f"# Pull request #{pr}",
        "",
        "- PR title, body, author and changed files: review/pr.json",
        "- Diff: review/pr.diff",
        f"- PR head checkout at {head[:7]}: review/pr",
        "- Registry at the base branch: repository root (plugins/, themes/, CONTRIBUTING.md, .github/)",
    ]
    return head, header, plugins, themes


def stage_plugin(issue: int, plugin_id: str) -> tuple[str, list[str], list[dict], list[str]]:
    stem = registry_stem(plugin_id)
    if stem is None:
        sys.exit(f"{plugin_id} is not in plugins/")

    header = [
        f"# Listed plugin {plugin_id}",
        "",
        f"Already in the registry, tracking issue #{issue}. There is no pull request: review its entry and current source.",
        "- Registry: repository root (plugins/, themes/, CONTRIBUTING.md). Its own entry there is not a duplicate.",
    ]
    return "", header, [plugin_entry(stem, REPO_ROOT, fetch=True)], []


def context_lines(header: list[str], plugins: list[dict], themes: list[str], dms_sha: str) -> list[str]:
    lines = list(header)
    if dms_sha:
        lines.append(
            f"- DMS source at {dms_sha[:7]}: review/dms. Plugin guide: review/dms/.agents/skills/dms-plugin-dev/SKILL.md"
        )

    for plugin in plugins:
        lines += ["", f"## {plugin['file']} ({plugin['status']})"]
        if "entry" in plugin:
            lines.append(f"- Entry under review: {plugin['entry']}")
        if plugin["status"] in ("updated", "removed"):
            lines.append(f"- Entry at base: {plugin['file']}")
        if "error" in plugin:
            lines.append(f"- {plugin['error']}")
            continue
        source = plugin.get("source")
        if not source:
            continue
        if "error" in source:
            lines.append(f"- Source {source.get('url', '')}: {source['error']}")
            continue
        lines.append(f"- Source {source['url']} at {source['sha'][:7]}, default branch HEAD, what DMS installs")
        lines.append(f"- Plugin directory: {source['dir']}")

    for slug in themes:
        status = "updated" if (REPO_ROOT / "themes" / slug).exists() else "new"
        lines += ["", f"## themes/{slug} ({status})", f"- In this PR: review/pr/themes/{slug}"]

    return lines


def prepare() -> None:
    kind, number = os.environ["KIND"], int(os.environ["NUMBER"])
    REVIEW_DIR.mkdir(exist_ok=True)
    if kind == "pr":
        head, header, plugins, themes = stage_pr(number)
    else:
        head, header, plugins, themes = stage_plugin(number, os.environ["PLUGIN"])

    sources = [p["source"] for p in plugins if "sha" in p.get("source", {})]
    dms_sha = fetch_dms() if sources else ""
    strip_untrusted(REVIEW_DIR)

    context = "\n".join(context_lines(header, plugins, themes, dms_sha)) + "\n"
    (REVIEW_DIR / "CONTEXT.md").write_text(context)
    meta = {
        "kind": kind,
        "repo": os.environ["GH_REPO"],
        "base": run("git", "rev-parse", "HEAD", cwd=REPO_ROOT).strip(),
        "head": head,
        "dms": dms_sha,
        "sources": {s["prefix"]: {"blob": s["blob"], "label": s["label"]} for s in sources},
    }
    (REVIEW_DIR / "meta.json").write_text(json.dumps(meta, indent=2))
    print(context)


def neutralize(text: str) -> str:
    text = text.replace("<", "&lt;").replace("[", "\\[")
    return MENTION.sub("@​", text)


def plain(text: str, limit: int) -> str:
    text = " ".join(str(text).split())
    if len(text) > limit:
        text = text[: limit - 1].rstrip() + "…"
    spans = CODE_SPAN.split(text)
    return "".join(span if i % 2 else neutralize(span) for i, span in enumerate(spans))


def link_bases(meta: dict) -> list[tuple[str, str]]:
    bases = [(prefix, source["blob"]) for prefix, source in meta["sources"].items()]
    if meta["dms"]:
        bases.append(("review/dms/", f"{DMS_REPO}/blob/{meta['dms']}/"))
    if meta["head"]:
        bases.append(("review/pr/", f"https://github.com/{meta['repo']}/blob/{meta['head']}/"))
    return bases


def location(file: str, line: int, meta: dict) -> str:
    file = str(file).strip().removeprefix("./")
    if not file:
        return ""

    line = line if isinstance(line, int) and line > 0 else 0
    anchor, suffix = (f"#L{line}", f":{line}") if line else ("", "")
    for prefix, blob in link_bases(meta):
        rest = file.removeprefix(prefix)
        if rest != file and safe_path(rest):
            return f"[`{rest}{suffix}`]({blob}{quote(rest)}{anchor})"
    if safe_path(file) and not file.startswith("review/"):
        return f"[`{file}{suffix}`](https://github.com/{meta['repo']}/blob/{meta['base']}/{quote(file)}{anchor})"

    shown = file.replace("`", "")[:200]
    return f"`{shown}{suffix}`"


def finding_line(finding: dict, meta: dict) -> str:
    severity = finding["severity"] if finding["severity"] in SEVERITIES else "issue"
    detail = plain(finding["detail"], 800)
    where = location(finding["file"], finding["line"], meta)
    if not where:
        return f"- **{severity}**: {detail}"
    return f"- **{severity}** {where}: {detail}"


def render(result: dict, meta: dict) -> str:
    verdict = VERDICTS[meta["kind"]].get(result["verdict"], "no verdict")
    lines = [MARKER, f"## Claude review: {verdict}", "", plain(result["summary"], 600), ""]

    footprint = plain(result["footprint"], 600)
    if footprint:
        lines += [f"**Footprint:** {footprint}", ""]

    findings = result["findings"][:MAX_FINDINGS]
    lines += [finding_line(f, meta) for f in findings] or ["No issues found."]

    notes = [
        f"Automated first pass on `{meta['head'][:7]}`, not an approval."
        if meta["kind"] == "pr"
        else "Automated review of the listed plugin, not a moderation decision."
    ]
    notes += [f"Plugin source `{s['label']}`." for s in meta["sources"].values()]
    checked = plain(result["checked"], 300)
    if checked:
        notes.append(f"Checked: {checked}")
    lines += ["", f"<sub>{' '.join(notes)}</sub>"]
    return "\n".join(lines) + "\n"


def post(result_dir: Path) -> None:
    repo = os.environ["GH_REPO"]
    number = int(os.environ["NUMBER"])
    raw = (result_dir / "result.json").read_text()
    if SECRET.search(raw):
        sys.exit("refusing to post: review output matches a credential pattern")

    body = render(json.loads(raw), json.loads((result_dir / "meta.json").read_text()))
    for comment in review_comments(repo, number):
        try:
            run("gh", "api", "graphql", "-f", f"query={MINIMIZE}", "-f", f"id={comment['node_id']}")
        except subprocess.CalledProcessError as e:
            print(f"could not minimize {comment['html_url']}: {e.stderr.strip()}")
    run("gh", "api", "-X", "POST", f"repos/{repo}/issues/{number}/comments", "--input", "-",
        stdin=json.dumps({"body": body}))
    print(body)


def main() -> int:
    match sys.argv[1:]:
        case ["targets"]:
            targets()
        case ["prepare"]:
            prepare()
        case ["post", result_dir]:
            post(Path(result_dir))
        case _:
            sys.exit("usage: claude_review.py targets | prepare | post <result-dir>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
