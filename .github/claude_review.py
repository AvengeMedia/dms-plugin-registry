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
REVIEW_DIR = REPO_ROOT / "review"
PR_DIR = REVIEW_DIR / "pr"
SOURCE_DIR = REVIEW_DIR / "src"
DMS_DIR = REVIEW_DIR / "dms"

MARKER = "<!-- claude-review -->"
BOT_LOGIN = "github-actions[bot]"
MAX_OPEN_PRS_PER_AUTHOR = 3
MAX_REVIEWS_PER_PR = 8
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
BLOB_URL = {
    "github.com": "{repo}/blob/{sha}/",
    "gitlab.com": "{repo}/-/blob/{sha}/",
    "codeberg.org": "{repo}/src/commit/{sha}/",
}

SECRET = re.compile(r"sk-ant-|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_|eyJ[\w-]{10,}\.eyJ")
CODE_SPAN = re.compile(r"(`[^`\n]*`)")
MENTION = re.compile(r"@(?=[\w-])")
VERDICTS = {"ready": "ready", "needs-changes": "needs changes", "reject": "recommend closing"}
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


def review_comments(repo: str, pr: int) -> list[dict]:
    pages = gh_json("api", f"repos/{repo}/issues/{pr}/comments", "--paginate", "--slurp")
    return [
        c for page in pages for c in page if c["user"]["login"] == BOT_LOGIN and c["body"].startswith(MARKER)
    ]


def event_targets(repo: str) -> list[int]:
    pr = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())["pull_request"]
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


def backfill_targets(repo: str) -> list[int]:
    prs = gh_json(
        "pr", "list", "--state", "open", "--base", "master", "--limit", "100", "--json", "number,isDraft,author"
    )
    return [
        p["number"]
        for p in prs
        if not p["isDraft"] and not p["author"]["is_bot"] and not review_comments(repo, p["number"])
    ]


def targets() -> None:
    repo = os.environ["GH_REPO"]
    requested = os.environ.get("PR_INPUT", "")
    match os.environ["GITHUB_EVENT_NAME"]:
        case "pull_request_target":
            prs = event_targets(repo)
        case "workflow_dispatch" if requested:
            prs = [int(requested)]
        case _:
            prs = backfill_targets(repo)
    print(f"reviewing: {prs}")
    set_output("prs", json.dumps(prs))


def read_json(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


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


def plugin_entry(stem: str, fetch: bool) -> dict:
    rel = f"plugins/{stem}.json"
    if not (PR_DIR / rel).exists():
        return {"file": rel, "status": "removed"}

    status = "updated" if (REPO_ROOT / rel).exists() else "new"
    plugin = read_json(PR_DIR / rel)
    if plugin is None:
        return {"file": rel, "status": status, "error": "not a valid JSON object, CI reports this"}
    if not fetch:
        return {"file": rel, "status": status, "error": f"over the {MAX_SOURCES} plugin limit, source not fetched"}
    return {"file": rel, "status": status, "source": fetch_source(stem, plugin)}


def fetch_dms() -> str:
    try:
        run("git", "clone", "--depth", "1", "--filter=blob:none", "--sparse", "--quiet", DMS_REPO, str(DMS_DIR),
            timeout=CLONE_TIMEOUT)
        run("git", "sparse-checkout", "set", *DMS_PATHS, cwd=DMS_DIR, timeout=CLONE_TIMEOUT)
        return run("git", "rev-parse", "--short", "HEAD", cwd=DMS_DIR).strip()
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


def context_lines(pr: int, head: str, plugins: list[dict], themes: list[str], dms_sha: str) -> list[str]:
    lines = [
        f"# PR #{pr}",
        "",
        "- PR title, body, author and changed files: review/pr.json",
        "- Diff: review/pr.diff",
        f"- PR head checkout at {head[:7]}: review/pr",
        "- Registry at the base branch: repository root (plugins/, themes/, CONTRIBUTING.md, .github/)",
    ]
    if dms_sha:
        lines.append(
            f"- DMS source at {dms_sha}: review/dms. Plugin guide: review/dms/.agents/skills/dms-plugin-dev/SKILL.md"
        )

    for plugin in plugins:
        lines += ["", f"## {plugin['file']} ({plugin['status']})"]
        if plugin["status"] != "removed":
            lines.append(f"- Entry in this PR: review/pr/{plugin['file']}")
        if plugin["status"] != "new":
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
    pr = int(os.environ["PR"])
    repo = os.environ["GH_REPO"]
    head = run("git", "rev-parse", "HEAD", cwd=PR_DIR).strip()
    info = gh_json("pr", "view", str(pr), "--json", "number,title,body,author,url,baseRefName,files")
    (REVIEW_DIR / "pr.json").write_text(json.dumps(info, indent=2))
    write_diff(pr)

    paths = [f["path"] for f in info["files"]]
    stems = sorted({m.group(1) for p in paths if (m := PLUGIN_FILE.match(p))})
    themes = sorted({m.group(1) for p in paths if (m := THEME_FILE.match(p))})
    plugins = [plugin_entry(stem, fetch=i < MAX_SOURCES) for i, stem in enumerate(stems)]
    sources = [p["source"] for p in plugins if "sha" in p.get("source", {})]
    dms_sha = fetch_dms() if sources else ""

    strip_untrusted(REVIEW_DIR)

    (REVIEW_DIR / "CONTEXT.md").write_text("\n".join(context_lines(pr, head, plugins, themes, dms_sha)) + "\n")
    meta = {"repo": repo, "head": head, "sources": {s["prefix"]: {"blob": s["blob"], "label": s["label"]} for s in sources}}
    (REVIEW_DIR / "meta.json").write_text(json.dumps(meta, indent=2))
    print((REVIEW_DIR / "CONTEXT.md").read_text())


def neutralize(text: str) -> str:
    text = text.replace("<", "&lt;").replace("[", "\\[")
    return MENTION.sub("@​", text)


def plain(text: str, limit: int) -> str:
    text = " ".join(str(text).split())
    if len(text) > limit:
        text = text[: limit - 1].rstrip() + "…"
    spans = CODE_SPAN.split(text)
    return "".join(span if i % 2 else neutralize(span) for i, span in enumerate(spans))


def location(file: str, line: int, meta: dict) -> str:
    file = str(file).strip().removeprefix("./")
    if not file:
        return ""

    line = line if isinstance(line, int) and line > 0 else 0
    anchor, suffix = (f"#L{line}", f":{line}") if line else ("", "")
    bases = [(prefix, source["blob"]) for prefix, source in meta["sources"].items()]
    bases.append(("review/pr/", f"https://github.com/{meta['repo']}/blob/{meta['head']}/"))
    for prefix, blob in bases:
        rest = file.removeprefix(prefix)
        if rest != file and safe_path(rest):
            return f"[`{rest}{suffix}`]({blob}{quote(rest)}{anchor})"

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
    verdict = VERDICTS.get(result["verdict"], "no verdict")
    lines = [MARKER, f"## Claude review: {verdict}", "", plain(result["summary"], 600), ""]

    footprint = plain(result["footprint"], 600)
    if footprint:
        lines += [f"**Footprint:** {footprint}", ""]

    findings = result["findings"][:MAX_FINDINGS]
    lines += [finding_line(f, meta) for f in findings] or ["No issues found."]

    notes = [f"Automated first pass on `{meta['head'][:7]}`, not an approval."]
    notes += [f"Plugin source `{s['label']}`." for s in meta["sources"].values()]
    checked = plain(result["checked"], 300)
    if checked:
        notes.append(f"Checked: {checked}")
    lines += ["", f"<sub>{' '.join(notes)}</sub>"]
    return "\n".join(lines) + "\n"


def post(result_dir: Path) -> None:
    repo = os.environ["GH_REPO"]
    pr = int(os.environ["PR"])
    raw = (result_dir / "result.json").read_text()
    if SECRET.search(raw):
        sys.exit("refusing to post: review output matches a credential pattern")

    body = render(json.loads(raw), json.loads((result_dir / "meta.json").read_text()))
    for comment in review_comments(repo, pr):
        try:
            run("gh", "api", "graphql", "-f", f"query={MINIMIZE}", "-f", f"id={comment['node_id']}")
        except subprocess.CalledProcessError as e:
            print(f"could not minimize {comment['html_url']}: {e.stderr.strip()}")
    run("gh", "pr", "comment", str(pr), "--repo", repo, "--body-file", "-", stdin=body)
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
