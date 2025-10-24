#!/usr/bin/env python3
# /// script
# dependencies = [
#   "requests",
#   "jinja2",
# ]
# ///
"""Generate site content from plugins/*.json files."""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests
from jinja2 import Template


# Jinja2 template for plugin markdown content
PLUGIN_TEMPLATE = Template("""---
date: {{ current_date }}
title: {{ plugin.name }}
author: {{ plugin.author }}
tags: {{ tags }}
card_image: {{ screenshot }}
pinned: {{ 'true' if is_official else 'false' }}
---

{{ plugin.description }} <a href="{{ plugin.repo }}" target="_blank" rel="noopener noreferrer"><img src="./static/repo-icon.png" alt="Repository" style="vertical-align: middle; height: 24px;"></a>


{{ release_badge }}

> [!NOTE] installation
> Run `dms plugins install {{ plugin.id }}`  
> <small>or install using the plugins tab on DMS settings</small>

---

| Plugin Information                 | Value                                         |
| ---------------------------------- | --------------------------------------------- |
| id                                 | {{ plugin.id }}                               |
| name                               | {{ plugin.name }}                             |
| author                             | {{ plugin.author }}                           |
| repo                               | [Link]({{ plugin.repo }})                     |
| capabilities                       | {{ plugin.capabilities | join(', ') }}        |
| category                           | {{ plugin.category }}                         |
| compositors                        | {{ plugin.compositors | join(', ') }}         |
| distro                             | {{ plugin.distro | join(', ') }}              |
| dependencies                       | {{ plugin.dependencies | join(', ') }}        |
| requires DMS                       | {{ plugin.requires_dms }}                     |

{{ screenshot_section }}
{{ readme_content }}

""")


def get_default_branch(repo_url: str) -> str:
    """Get the default branch for a repository.

    Args:
        repo_url: Repository URL (GitHub, GitLab, Codeberg, etc.)

    Returns:
        Default branch name, or 'main' if unable to determine
    """
    parsed = urlparse(repo_url)

    # Extract owner/repo from path like /owner/repo or /owner/repo.git
    path_parts = parsed.path.strip("/").rstrip(".git").split("/")
    if len(path_parts) < 2:
        return "main"

    owner, repo = path_parts[0], path_parts[1]

    try:
        if parsed.netloc == "github.com":
            # GitHub API
            api_url = f"https://api.github.com/repos/{owner}/{repo}"
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("default_branch", "main")

        elif parsed.netloc == "gitlab.com" or "gitlab" in parsed.netloc:
            # GitLab API
            project_path = f"{owner}%2F{repo}"
            base_url = f"https://{parsed.netloc}"
            api_url = f"{base_url}/api/v4/projects/{project_path}"
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("default_branch", "main")

        elif parsed.netloc == "codeberg.org" or "gitea" in parsed.netloc or "forgejo" in parsed.netloc:
            # Codeberg/Gitea/Forgejo API
            base_url = f"https://{parsed.netloc}"
            api_url = f"{base_url}/api/v1/repos/{owner}/{repo}"
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("default_branch", "main")

    except requests.RequestException as e:
        print(f"Warning: Failed to fetch default branch for {repo_url}: {e}", file=sys.stderr)

    # Fallback to 'main'
    return "main"


def fetch_readme(repo_url: str, path: Optional[str] = None) -> str:
    """Fetch README.md from a GitHub repository.

    Args:
        repo_url: GitHub repository URL (e.g., https://github.com/author/repo)
        path: Optional subdirectory path for monorepos

    Returns:
        README content as string, or error message if not found
    """
    # Extract owner and repo name from URL
    # https://github.com/author/repo -> author/repo
    parts = repo_url.rstrip('/').split('github.com/')
    if len(parts) != 2:
        return f"<!-- Could not parse repository URL: {repo_url} -->"

    owner_repo = parts[1]

    # Build raw.githubusercontent.com URL
    # Try both main and master branches
    for branch in ['main', 'master']:
        if path:
            # Monorepo: https://raw.githubusercontent.com/author/repo/main/path/README.md
            raw_url = f"https://raw.githubusercontent.com/{owner_repo}/{branch}/{path}/README.md"
        else:
            # Regular repo: https://raw.githubusercontent.com/author/repo/main/README.md
            raw_url = f"https://raw.githubusercontent.com/{owner_repo}/{branch}/README.md"

        try:
            response = requests.get(raw_url, timeout=10)
            if response.status_code == 200:
                return response.text
        except requests.RequestException as e:
            print(f"Warning: Failed to fetch {raw_url}: {e}", file=sys.stderr)
            continue

    return f"<!-- README not found for {repo_url} -->"


def generate_markdown(plugin: dict, plugin_filename: str, current_date: str) -> str:
    """Generate markdown content for a plugin.

    Args:
        plugin: Plugin data dictionary
        plugin_filename: Original JSON filename (without .json extension)
        current_date: Current date in YYYY-MM-DD format

    Returns:
        Markdown content with frontmatter
    """
    import re
    from urllib.parse import quote

    # Fetch README from repository
    readme_content = fetch_readme(
        plugin.get('repo', ''),
        plugin.get('path')
    )

    # If inside readme_content there is a relative image link, we might want to adjust it
    # and add the repo raw URL prefix.
    # so ![image](image.png) becomes ![image](https://raw.githubusercontent.com/author/repo/main/image.png)
    # use regex to match ![alt](url.{png,jpg,jpeg,gif,webp})
    def replace_relative_image(match):
        alt_text = match.group(1)
        img_url = match.group(2)
        if img_url.startswith('http://') or img_url.startswith('https://'):
            return match.group(0)  # leave unchanged
        # Build raw URL
        parts = plugin.get('repo', '').rstrip('/').split('github.com/')
        if len(parts) != 2:
            return match.group(0)  # leave unchanged
        owner_repo = parts[1]
        branch = 'main'  # default to main
        if plugin.get('path'):
            raw_img_url = f"https://raw.githubusercontent.com/{owner_repo}/{branch}/{plugin['path']}/{img_url}"
        else:
            raw_img_url = f"https://raw.githubusercontent.com/{owner_repo}/{branch}/{img_url}"
        return f"![{alt_text}]({raw_img_url})"

    readme_content = re.sub(r'!\[([^\]]*)\]\(([^)]+\.(png|jpg|jpeg|gif|webp))\)', replace_relative_image, readme_content)

    # Build tags list: capabilities + category + compositors + distro
    tags = []
    tags.extend(plugin.get('capabilities', []))
    if 'category' in plugin:
        tags.append(plugin['category'])
    tags.extend(plugin.get('compositors', []))
    tags.extend(plugin.get('distro', []))

    # Format tags as comma-separated string
    tags_str = ', '.join(tags)

    # Build screenshot section
    screenshot = plugin.get("screenshot", "null")
    no_image_on_readme = '![' not in readme_content
    screenshot_section = ""
    if 'screenshot' in plugin and plugin['screenshot'] and no_image_on_readme:
        screenshot_section = f"\n![{plugin['name']} Screenshot]({plugin['screenshot']})\n"

    is_official = plugin.get("author") == "Avenge Media"

    # Build release badge URL
    release_badge = ""
    repo_url = plugin.get('repo', '')
    if repo_url:
        # Get default branch dynamically
        branch = get_default_branch(repo_url)

        # Parse repo URL to get owner/repo
        parts = repo_url.rstrip('/').split('github.com/')
        if len(parts) == 2:
            owner_repo = parts[1]
        else:
            # Handle non-GitHub repos (GitLab, Codeberg, etc.)
            parsed = urlparse(repo_url)
            owner_repo = parsed.path.strip("/").rstrip(".git")

        # Build raw URL for plugin.json
        parsed = urlparse(repo_url)
        if parsed.netloc == "github.com":
            # GitHub raw URL
            if plugin.get('path'):
                plugin_json_url = f"https://raw.githubusercontent.com/{owner_repo}/{branch}/{plugin['path']}/plugin.json"
            else:
                plugin_json_url = f"https://raw.githubusercontent.com/{owner_repo}/{branch}/plugin.json"
        elif parsed.netloc == "gitlab.com" or "gitlab" in parsed.netloc:
            # GitLab raw URL
            base_url = f"https://{parsed.netloc}"
            if plugin.get('path'):
                plugin_json_url = f"{base_url}/{owner_repo}/-/raw/{branch}/{plugin['path']}/plugin.json"
            else:
                plugin_json_url = f"{base_url}/{owner_repo}/-/raw/{branch}/plugin.json"
        elif parsed.netloc == "codeberg.org" or "gitea" in parsed.netloc or "forgejo" in parsed.netloc:
            # Codeberg/Gitea/Forgejo raw URL
            base_url = f"https://{parsed.netloc}"
            if plugin.get('path'):
                plugin_json_url = f"{base_url}/{owner_repo}/raw/branch/{branch}/{plugin['path']}/plugin.json"
            else:
                plugin_json_url = f"{base_url}/{owner_repo}/raw/branch/{branch}/plugin.json"
        else:
            # Unknown hosting service - try GitHub format as fallback
            if plugin.get('path'):
                plugin_json_url = f"https://raw.githubusercontent.com/{owner_repo}/{branch}/{plugin['path']}/plugin.json"
            else:
                plugin_json_url = f"https://raw.githubusercontent.com/{owner_repo}/{branch}/plugin.json"

        # URL encode the plugin.json URL for shields.io
        encoded_url = quote(plugin_json_url, safe='')
        release_badge = f"![RELEASE](https://img.shields.io/badge/dynamic/json?url={encoded_url}&query=version&style=for-the-badge&label=RELEASE&labelColor=101418&color=9ccbfb)"

    # Prepare context for template
    context = {
        'current_date': current_date,
        'plugin': {
            'id': plugin.get("id"),
            'name': plugin.get('name', 'Unknown Plugin'),
            'author': plugin.get('author', 'Unknown Author'),
            'description': plugin.get('description', 'No description available.'),
            'repo': plugin.get('repo', '#'),
            'capabilities': plugin.get('capabilities', []),
            'category': plugin.get('category', 'Uncategorized'),
            'compositors': plugin.get('compositors', []),
            'distro': plugin.get('distro', []),
            'dependencies': plugin.get('dependencies', []),
            'requires_dms': plugin.get('requires_dms', 'N/A'),
        },
        'tags': tags_str,
        'screenshot': screenshot,
        'is_official': is_official,
        'release_badge': release_badge,
        'screenshot_section': screenshot_section,
        'readme_content': readme_content,
    }

    # Render template
    return PLUGIN_TEMPLATE.render(context)


def generate_site_content() -> int:
    """Generate site content for all plugins."""
    repo_root = Path(__file__).parent.parent
    plugins_dir = repo_root / "plugins"
    content_dir = repo_root / "site" / "content"

    # Ensure content directory exists
    content_dir.mkdir(parents=True, exist_ok=True)


    # Process each plugin JSON file
    processed_count = 0
    error_count = 0

    for json_file in plugins_dir.glob("*.json"):
        
        # current date must be the date the json file was last edited
        # 
        # current_date = datetime.now().strftime('%Y-%m-%d')
        current_date = datetime.fromtimestamp(json_file.stat().st_mtime).strftime('%Y-%m-%d')
        
        try:
            # Load plugin data
            with open(json_file) as f:
                plugin_data = json.load(f)

            # Generate output filename based on JSON filename
            # e.g., rochacbruno-calculator.json -> rochacbruno-calculator.md
            output_filename = json_file.stem + ".md"
            output_path = content_dir / output_filename

            # Generate markdown content
            markdown_content = generate_markdown(
                plugin_data,
                json_file.stem,
                current_date
            )

            # Write to file
            with open(output_path, 'w') as f:
                f.write(markdown_content)

            print(f"Generated: {output_filename}")
            processed_count += 1

        except json.JSONDecodeError as e:
            print(f"Error parsing {json_file}: {e}", file=sys.stderr)
            error_count += 1
        except Exception as e:
            print(f"Error processing {json_file}: {e}", file=sys.stderr)
            error_count += 1

    print(f"\nProcessed {processed_count} plugins")
    if error_count > 0:
        print(f"Encountered {error_count} errors", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(generate_site_content())
