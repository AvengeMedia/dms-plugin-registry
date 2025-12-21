#!/usr/bin/env python3
"""Validate theme JSON files in the themes/ directory."""

import json
import re
import sys
from pathlib import Path

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

REQUIRED_META_FIELDS = ["id", "name", "version", "author", "description", "dark", "light"]

REQUIRED_COLOR_FIELDS = [
    "primary", "primaryText", "primaryContainer", "secondary",
    "surface", "surfaceText", "surfaceVariant", "surfaceVariantText",
    "surfaceTint", "background", "backgroundText", "outline",
    "surfaceContainer", "surfaceContainerHigh", "error", "warning", "info"
]

HEX_COLOR_PATTERN = re.compile(r'^#[0-9A-Fa-f]{6}$')
CAMEL_CASE_PATTERN = re.compile(r'^[a-z][a-zA-Z0-9]*$')
SEMVER_PATTERN = re.compile(r'^\d+\.\d+\.\d+$')


def is_valid_hex_color(value: str) -> bool:
    return bool(HEX_COLOR_PATTERN.match(value))


def is_camel_case(s: str) -> bool:
    if not s:
        return False
    return bool(CAMEL_CASE_PATTERN.match(s))


def validate_color_scheme(scheme: dict, scheme_name: str) -> list[str]:
    errors = []

    if not isinstance(scheme, dict):
        return [f"{scheme_name} must be an object"]

    for field in REQUIRED_COLOR_FIELDS:
        if field not in scheme:
            errors.append(f"{scheme_name} missing required field: {field}")
            continue

        value = scheme[field]
        if not isinstance(value, str):
            errors.append(f"{scheme_name}.{field} must be a string")
        elif not is_valid_hex_color(value):
            errors.append(f"{scheme_name}.{field} must be a valid hex color (got: {value})")

    return errors


def validate_theme(theme_file: Path) -> list[str]:
    errors = []

    try:
        with open(theme_file, "r") as f:
            theme = json.load(f)
    except json.JSONDecodeError as e:
        return [f"Invalid JSON: {e}"]
    except Exception as e:
        return [f"Failed to read file: {e}"]

    for field in REQUIRED_META_FIELDS:
        if field not in theme:
            errors.append(f"Missing required field: {field}")

    if "id" in theme:
        theme_id = theme["id"]
        if not theme_id:
            errors.append("ID is empty")
        elif not is_camel_case(theme_id):
            errors.append(f"ID '{theme_id}' must be camelCase (start lowercase, alphanumeric only)")

    if "version" in theme:
        version = theme["version"]
        if not version:
            errors.append("version is empty")
        elif not SEMVER_PATTERN.match(version):
            errors.append(f"version '{version}' must be semver format (e.g., 1.0.0)")

    if "name" in theme and (not isinstance(theme["name"], str) or not theme["name"].strip()):
        errors.append("name must be a non-empty string")

    if "author" in theme and (not isinstance(theme["author"], str) or not theme["author"].strip()):
        errors.append("author must be a non-empty string")

    if "description" in theme and (not isinstance(theme["description"], str) or not theme["description"].strip()):
        errors.append("description must be a non-empty string")

    if "dark" in theme:
        errors.extend(validate_color_scheme(theme["dark"], "dark"))

    if "light" in theme:
        errors.extend(validate_color_scheme(theme["light"], "light"))

    return errors


def validate_all_themes(themes_dir: Path) -> bool:
    if not themes_dir.exists():
        print(f"{YELLOW}No themes/ directory found, skipping theme validation{RESET}")
        return True

    theme_dirs = [d for d in themes_dir.iterdir() if d.is_dir() and (d / "theme.json").exists()]
    if not theme_dirs:
        print(f"{YELLOW}No theme folders found in themes/{RESET}")
        return True

    print(f"Validating {len(theme_dirs)} theme(s)...\n")

    all_errors = {}
    seen_ids = {}
    seen_names = {}

    for theme_dir in sorted(theme_dirs):
        theme_file = theme_dir / "theme.json"
        print(f"Checking {theme_dir.name}/theme.json...", end=" ")
        errors = validate_theme(theme_file)

        try:
            with open(theme_file) as f:
                theme = json.load(f)

            theme_id = theme.get("id")
            if theme_id:
                if theme_id in seen_ids:
                    errors.append(f"Duplicate ID '{theme_id}' (also in {seen_ids[theme_id]})")
                else:
                    seen_ids[theme_id] = theme_dir.name

            theme_name = theme.get("name")
            if theme_name:
                if theme_name in seen_names:
                    errors.append(f"Duplicate name '{theme_name}' (also in {seen_names[theme_name]})")
                else:
                    seen_names[theme_name] = theme_dir.name

        except (json.JSONDecodeError, Exception):
            pass

        if errors:
            print(f"{RED}FAILED{RESET}")
            all_errors[theme_dir.name] = errors
        else:
            print(f"{GREEN}OK{RESET}")

    print()
    if all_errors:
        print(f"{RED}Validation failed for {len(all_errors)} theme(s):{RESET}\n")
        for dirname, errors in all_errors.items():
            print(f"{RED}✗ {dirname}{RESET}")
            for error in errors:
                print(f"  - {error}")
            print()
        return False

    print(f"{GREEN}✓ All themes validated successfully!{RESET}")
    return True


def main():
    themes_dir = Path(__file__).parent.parent / "themes"
    success = validate_all_themes(themes_dir)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
