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


def validate_color_scheme(scheme: dict, scheme_name: str, required_fields: list[str] = None) -> list[str]:
    errors = []
    fields = required_fields if required_fields is not None else REQUIRED_COLOR_FIELDS

    if not isinstance(scheme, dict):
        return [f"{scheme_name} must be an object"]

    for field in fields:
        if field not in scheme:
            errors.append(f"{scheme_name} missing required field: {field}")
            continue

        value = scheme[field]
        if not isinstance(value, str):
            errors.append(f"{scheme_name}.{field} must be a string")
        elif not is_valid_hex_color(value):
            errors.append(f"{scheme_name}.{field} must be a valid hex color (got: {value})")

    return errors


def validate_variants(theme: dict) -> list[str]:
    errors = []
    variants = theme.get("variants", {})

    if variants.get("type") == "multi":
        return validate_multi_variants(theme)

    options = variants.get("options", [])
    default_id = variants.get("default")

    if not options:
        errors.append("variants.options must be a non-empty array")
        return errors

    if not default_id:
        errors.append("variants.default is required")

    variant_ids = []
    for i, variant in enumerate(options):
        vid = variant.get("id")
        vname = variant.get("name")

        if not vid:
            errors.append(f"variants.options[{i}] missing required field: id")
        elif not isinstance(vid, str):
            errors.append(f"variants.options[{i}].id must be a string")
        else:
            variant_ids.append(vid)

        if not vname:
            errors.append(f"variants.options[{i}] missing required field: name")

        for mode in ["dark", "light"]:
            base = theme.get(mode, {})
            override = variant.get(mode, {})
            resolved = {**base, **override}
            label = f"variants.options[{i}] ({vid or i}) resolved {mode}"
            errors.extend(validate_color_scheme(resolved, label))

            for key, value in override.items():
                if not is_valid_hex_color(value):
                    errors.append(f"variants.options[{i}].{mode}.{key} must be a valid hex color (got: {value})")

    if default_id and default_id not in variant_ids:
        errors.append(f"variants.default '{default_id}' not found in options")

    return errors


def validate_multi_variants(theme: dict) -> list[str]:
    errors = []
    variants = theme.get("variants", {})
    defaults = variants.get("defaults", {})
    flavors = variants.get("flavors", [])
    accents = variants.get("accents", [])

    if not flavors:
        errors.append("variants.flavors must be a non-empty array")
        return errors

    if not accents:
        errors.append("variants.accents must be a non-empty array")
        return errors

    dark_defaults = defaults.get("dark", {})
    light_defaults = defaults.get("light", {})

    if not dark_defaults:
        errors.append("variants.defaults.dark is required")
    if not light_defaults:
        errors.append("variants.defaults.light is required")

    if dark_defaults and not dark_defaults.get("flavor"):
        errors.append("variants.defaults.dark.flavor is required")
    if dark_defaults and not dark_defaults.get("accent"):
        errors.append("variants.defaults.dark.accent is required")
    if light_defaults and not light_defaults.get("flavor"):
        errors.append("variants.defaults.light.flavor is required")
    if light_defaults and not light_defaults.get("accent"):
        errors.append("variants.defaults.light.accent is required")

    flavor_ids = []
    flavor_modes = {}
    for i, flavor in enumerate(flavors):
        fid = flavor.get("id")
        fname = flavor.get("name")

        if not fid:
            errors.append(f"variants.flavors[{i}] missing required field: id")
        elif not isinstance(fid, str):
            errors.append(f"variants.flavors[{i}].id must be a string")
        else:
            flavor_ids.append(fid)

        if not fname:
            errors.append(f"variants.flavors[{i}] missing required field: name")

        has_dark = "dark" in flavor
        has_light = "light" in flavor
        if not has_dark and not has_light:
            errors.append(f"variants.flavors[{i}] ({fid or i}) must have 'dark' or 'light'")
        if has_dark and has_light:
            errors.append(f"variants.flavors[{i}] ({fid or i}) should have only 'dark' or 'light', not both")

        if fid:
            flavor_modes[fid] = "dark" if has_dark else "light"

    dark_flavor_ids = [f["id"] for f in flavors if "dark" in f]
    light_flavor_ids = [f["id"] for f in flavors if "light" in f]

    if dark_defaults.get("flavor") and dark_defaults["flavor"] not in dark_flavor_ids:
        errors.append(f"variants.defaults.dark.flavor '{dark_defaults['flavor']}' must be a dark flavor")
    if light_defaults.get("flavor") and light_defaults["flavor"] not in light_flavor_ids:
        errors.append(f"variants.defaults.light.flavor '{light_defaults['flavor']}' must be a light flavor")

    accent_ids = []
    for i, accent in enumerate(accents):
        aid = accent.get("id")
        aname = accent.get("name")

        if not aid:
            errors.append(f"variants.accents[{i}] missing required field: id")
        elif not isinstance(aid, str):
            errors.append(f"variants.accents[{i}].id must be a string")
        else:
            accent_ids.append(aid)

        if not aname:
            errors.append(f"variants.accents[{i}] missing required field: name")

        for fid in flavor_ids:
            if fid not in accent:
                errors.append(f"variants.accents[{i}] ({aid or i}) missing flavor key: {fid}")

    if dark_defaults.get("accent") and dark_defaults["accent"] not in accent_ids:
        errors.append(f"variants.defaults.dark.accent '{dark_defaults['accent']}' not found in accents")
    if light_defaults.get("accent") and light_defaults["accent"] not in accent_ids:
        errors.append(f"variants.defaults.light.accent '{light_defaults['accent']}' not found in accents")

    for fi, flavor in enumerate(flavors):
        fid = flavor.get("id")
        if not fid:
            continue
        mode = flavor_modes.get(fid)
        if not mode:
            continue
        flavor_colors = flavor.get(mode, {})

        for ai, accent in enumerate(accents):
            aid = accent.get("id")
            if not aid:
                continue
            accent_colors = accent.get(fid, {})
            resolved = {**theme.get(mode, {}), **flavor_colors, **accent_colors}
            label = f"resolved {fid}+{aid}"
            errors.extend(validate_color_scheme(resolved, label))

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

    if "variants" in theme:
        errors.extend(validate_variants(theme))
    else:
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
