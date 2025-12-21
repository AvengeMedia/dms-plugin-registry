#!/usr/bin/env python3
# /// script
# dependencies = [
#   "jinja2",
# ]
# ///
"""Generate README.md from plugins/*.json and themes/*.json using README_TEMPLATE.md."""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

CAMEL_CASE_PATTERN = re.compile(r'^[a-z][a-zA-Z0-9]*$')
THEME_REQUIRED_FIELDS = ["id", "name", "author", "description", "dark", "light"]


def load_plugins(plugins_dir: Path) -> dict[str, list[dict]]:
    """Load all plugin JSON files and group them by category."""
    categories = defaultdict(list)

    for json_file in plugins_dir.glob("*.json"):
        try:
            with open(json_file) as f:
                plugin_data = json.load(f)
                category = plugin_data.get("category", "uncategorized")
                categories[category].append(plugin_data)
        except json.JSONDecodeError as e:
            print(f"Error parsing {json_file}: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error reading {json_file}: {e}", file=sys.stderr)
            sys.exit(1)

    return categories


def validate_plugin(plugin: dict, filename: str) -> bool:
    """Validate required fields in plugin data."""
    required_fields = ["id", "name", "capabilities", "category", "repo", "author",
                      "description", "dependencies", "compositors", "distro"]

    missing_fields = [field for field in required_fields if field not in plugin]

    if missing_fields:
        print(f"Validation error in {filename}: Missing required fields: {', '.join(missing_fields)}",
              file=sys.stderr)
        return False

    return True


def validate_all_plugins(plugins_dir: Path) -> bool:
    """Validate all plugin JSON files."""
    all_valid = True
    seen_ids = {}
    seen_names = {}

    for json_file in plugins_dir.glob("*.json"):
        try:
            with open(json_file) as f:
                plugin_data = json.load(f)
                if not validate_plugin(plugin_data, json_file.name):
                    all_valid = False

                plugin_id = plugin_data.get("id")
                if plugin_id:
                    if plugin_id in seen_ids:
                        print(f"Duplicate ID '{plugin_id}' found in {json_file.name} "
                              f"(previously in {seen_ids[plugin_id]})", file=sys.stderr)
                        all_valid = False
                    else:
                        seen_ids[plugin_id] = json_file.name

                plugin_name = plugin_data.get("name")
                if plugin_name:
                    if plugin_name in seen_names:
                        print(f"Duplicate name '{plugin_name}' found in {json_file.name} "
                              f"(previously in {seen_names[plugin_name]})", file=sys.stderr)
                        all_valid = False
                    else:
                        seen_names[plugin_name] = json_file.name

        except json.JSONDecodeError as e:
            print(f"JSON parse error in {json_file}: {e}", file=sys.stderr)
            all_valid = False
        except Exception as e:
            print(f"Error reading {json_file}: {e}", file=sys.stderr)
            all_valid = False

    return all_valid


def validate_theme(theme: dict, filename: str) -> bool:
    """Validate required fields in theme data."""
    missing = [f for f in THEME_REQUIRED_FIELDS if f not in theme]
    if missing:
        print(f"Theme validation error in {filename}: Missing fields: {', '.join(missing)}", file=sys.stderr)
        return False

    theme_id = theme.get("id", "")
    if not CAMEL_CASE_PATTERN.match(theme_id):
        print(f"Theme validation error in {filename}: ID '{theme_id}' must be camelCase", file=sys.stderr)
        return False

    return True


def validate_all_themes(themes_dir: Path) -> bool:
    """Validate all theme folders."""
    if not themes_dir.exists():
        return True

    theme_dirs = [d for d in themes_dir.iterdir() if d.is_dir() and (d / "theme.json").exists()]
    if not theme_dirs:
        return True

    all_valid = True
    seen_ids = {}
    seen_names = {}

    for theme_dir in theme_dirs:
        theme_file = theme_dir / "theme.json"
        try:
            with open(theme_file) as f:
                theme_data = json.load(f)
                if not validate_theme(theme_data, f"{theme_dir.name}/theme.json"):
                    all_valid = False

                theme_id = theme_data.get("id")
                if theme_id:
                    if theme_id in seen_ids:
                        print(f"Duplicate theme ID '{theme_id}' found in {theme_dir.name} "
                              f"(previously in {seen_ids[theme_id]})", file=sys.stderr)
                        all_valid = False
                    else:
                        seen_ids[theme_id] = theme_dir.name

                theme_name = theme_data.get("name")
                if theme_name:
                    if theme_name in seen_names:
                        print(f"Duplicate theme name '{theme_name}' found in {theme_dir.name} "
                              f"(previously in {seen_names[theme_name]})", file=sys.stderr)
                        all_valid = False
                    else:
                        seen_names[theme_name] = theme_dir.name

        except json.JSONDecodeError as e:
            print(f"JSON parse error in {theme_file}: {e}", file=sys.stderr)
            all_valid = False
        except Exception as e:
            print(f"Error reading {theme_file}: {e}", file=sys.stderr)
            all_valid = False

    return all_valid


def load_themes(themes_dir: Path) -> list[dict]:
    """Load all theme folders."""
    themes = []

    if not themes_dir.exists():
        return themes

    for theme_dir in themes_dir.iterdir():
        if not theme_dir.is_dir():
            continue
        theme_file = theme_dir / "theme.json"
        if not theme_file.exists():
            continue

        try:
            with open(theme_file) as f:
                theme_data = json.load(f)
                theme_data["_dirname"] = theme_dir.name
                themes.append(theme_data)
        except (json.JSONDecodeError, Exception) as e:
            print(f"Error reading {theme_file}: {e}", file=sys.stderr)
            sys.exit(1)

    return sorted(themes, key=lambda t: t.get("name", ""))


def generate_readme(validate_only: bool = False) -> int:
    """Generate README.md from template and plugin/theme data."""
    repo_root = Path(__file__).parent.parent
    plugins_dir = repo_root / "plugins"
    themes_dir = repo_root / "themes"
    output_file = repo_root / "README.md"

    plugins_valid = validate_all_plugins(plugins_dir)
    themes_valid = validate_all_themes(themes_dir)

    if not plugins_valid or not themes_valid:
        return 1

    if validate_only:
        print("Validation successful!")
        return 0

    categories_dict = load_plugins(plugins_dir)
    sorted_categories = sorted(categories_dict.keys())

    categories = []
    for category_name in sorted_categories:
        plugins = sorted(categories_dict[category_name], key=lambda p: p.get("name", ""))
        categories.append({
            "name": category_name.title(),
            "plugins": plugins
        })

    themes = load_themes(themes_dir)

    env = Environment(loader=FileSystemLoader(repo_root))
    template = env.get_template("README_TEMPLATE.md")

    try:
        rendered = template.render(categories=categories, themes=themes)
    except Exception as e:
        print(f"Error rendering template: {e}", file=sys.stderr)
        return 1

    warning = "<!-- DO NOT EDIT THIS FILE, EDIT README_TEMPLATE.md, this README.md is auto generated. -->"
    rendered = warning + "\n\n" + rendered

    try:
        with open(output_file, "w") as f:
            f.write(rendered)
        print(f"Successfully generated {output_file}")
        return 0
    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    validate_only = "--validate" in sys.argv
    sys.exit(generate_readme(validate_only))
