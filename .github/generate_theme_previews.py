#!/usr/bin/env python3
"""Generate SVG preview images for themes."""

import json
from pathlib import Path

PANEL_TEMPLATE = """<g transform="translate({x}, 0)">
  <rect width="240" height="240" fill="{background}"/>
  <rect x="8" y="8" width="224" height="224" rx="8" fill="{surface}"/>
  <rect x="16" y="16" width="208" height="36" rx="6" fill="{surfaceContainer}"/>
  <text x="28" y="40" font-family="system-ui, sans-serif" font-size="12" font-weight="600" fill="{surfaceText}">{name}</text>
  <rect x="16" y="60" width="208" height="72" rx="6" fill="{surfaceContainerHigh}"/>
  <text x="28" y="82" font-family="system-ui, sans-serif" font-size="11" fill="{surfaceText}">Surface Text</text>
  <text x="28" y="98" font-family="system-ui, sans-serif" font-size="10" fill="{outline}">Outline color</text>
  <rect x="28" y="108" width="72" height="18" rx="9" fill="{primary}"/>
  <text x="64" y="120" font-family="system-ui, sans-serif" font-size="9" text-anchor="middle" fill="{primaryText}">Primary</text>
  <rect x="108" y="108" width="48" height="18" rx="4" fill="{secondary}"/>
  <rect x="16" y="140" width="100" height="52" rx="6" fill="{surfaceContainer}"/>
  <rect x="24" y="148" width="84" height="36" rx="4" fill="{background}"/>
  <text x="66" y="170" font-family="system-ui, sans-serif" font-size="9" text-anchor="middle" fill="{backgroundText}">Background</text>
  <rect x="124" y="140" width="100" height="52" rx="6" fill="{surfaceContainer}"/>
  <circle cx="148" cy="166" r="9" fill="{error}"/>
  <circle cx="172" cy="166" r="9" fill="{warning}"/>
  <circle cx="196" cy="166" r="9" fill="{info}"/>
  <rect x="16" y="200" width="208" height="24" rx="4" fill="{surfaceTint}" opacity="0.15"/>
  <text x="120" y="216" font-family="system-ui, sans-serif" font-size="9" text-anchor="middle" fill="{surfaceText}">Surface Tint Overlay</text>
</g>"""

COMBINED_TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" width="484" height="240" viewBox="0 0 484 240">
  {dark_panel}
  <rect x="240" y="0" width="4" height="240" fill="#888"/>
  {light_panel}
</svg>"""

SINGLE_TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" width="240" height="240" viewBox="0 0 240 240">
  {panel}
</svg>"""


def generate_panel(scheme: dict, name: str, x: int) -> str:
    return PANEL_TEMPLATE.format(x=x, name=name, **scheme)


def generate_combined_preview(theme: dict) -> str:
    name = theme.get("name", "Theme")
    dark_panel = generate_panel(theme["dark"], f"{name} (dark)", 0)
    light_panel = generate_panel(theme["light"], f"{name} (light)", 244)
    return COMBINED_TEMPLATE.format(dark_panel=dark_panel, light_panel=light_panel)


def generate_single_preview(scheme: dict, name: str) -> str:
    panel = generate_panel(scheme, name, 0)
    return SINGLE_TEMPLATE.format(panel=panel)


def resolve_variant(base_dark: dict, base_light: dict, variant: dict) -> tuple[dict, dict]:
    dark = {**base_dark, **variant.get("dark", {})}
    light = {**base_light, **variant.get("light", {})}
    return dark, light


def resolve_multi_variant(theme: dict, flavor: dict, accent: dict) -> tuple[dict, str]:
    fid = flavor["id"]
    mode = "dark" if "dark" in flavor else "light"
    base = theme.get(mode, {})
    flavor_colors = flavor.get(mode, {})
    accent_colors = accent.get(fid, {})
    resolved = {**base, **flavor_colors, **accent_colors}
    return resolved, mode


def generate_all_previews(themes_dir: Path) -> None:
    if not themes_dir.exists():
        print("No themes/ directory found")
        return

    theme_dirs = [d for d in themes_dir.iterdir() if d.is_dir() and (d / "theme.json").exists()]
    if not theme_dirs:
        print("No theme folders found")
        return

    for theme_dir in sorted(theme_dirs):
        theme_file = theme_dir / "theme.json"
        try:
            with open(theme_file) as f:
                theme = json.load(f)
        except (json.JSONDecodeError, Exception) as e:
            print(f"Error reading {theme_file}: {e}")
            continue

        if "dark" not in theme or "light" not in theme:
            print(f"Skipping {theme_dir.name}: missing dark or light")
            continue

        theme_name = theme.get("name", theme_dir.name)
        base_dark, base_light = theme["dark"], theme["light"]

        if "variants" in theme:
            variants = theme["variants"]

            if variants.get("type") == "multi":
                defaults = variants.get("defaults", {})
                dark_defaults = defaults.get("dark", {})
                light_defaults = defaults.get("light", {})
                flavors = variants.get("flavors", [])
                accents = variants.get("accents", [])

                for flavor in flavors:
                    fid = flavor["id"]
                    fname = flavor.get("name", fid)

                    for accent in accents:
                        aid = accent["id"]
                        aname = accent.get("name", aid)
                        resolved, mode = resolve_multi_variant(theme, flavor, accent)
                        label = f"{theme_name} {fname} {aname}"

                        svg = generate_single_preview(resolved, label)
                        filename = f"preview-{fid}-{aid}.svg"
                        path = theme_dir / filename
                        with open(path, "w") as f:
                            f.write(svg)
                        print(f"Generated {path}")

                dark_flavor = next((f for f in flavors if f["id"] == dark_defaults.get("flavor")), None)
                dark_accent = next((a for a in accents if a["id"] == dark_defaults.get("accent")), None)
                light_flavor = next((f for f in flavors if f["id"] == light_defaults.get("flavor")), None)
                light_accent = next((a for a in accents if a["id"] == light_defaults.get("accent")), None)

                if dark_flavor and dark_accent:
                    resolved, _ = resolve_multi_variant(theme, dark_flavor, dark_accent)
                    label = f"{theme_name} {dark_flavor.get('name')} {dark_accent.get('name')} (dark)"
                    svg = generate_single_preview(resolved, label)
                    for filename in ["preview.svg", "preview-dark.svg"]:
                        path = theme_dir / filename
                        with open(path, "w") as f:
                            f.write(svg)
                        print(f"Generated {path}")

                if light_flavor and light_accent:
                    resolved, _ = resolve_multi_variant(theme, light_flavor, light_accent)
                    label = f"{theme_name} {light_flavor.get('name')} {light_accent.get('name')} (light)"
                    svg = generate_single_preview(resolved, label)
                    path = theme_dir / "preview-light.svg"
                    with open(path, "w") as f:
                        f.write(svg)
                    print(f"Generated {path}")
            else:
                default_id = variants.get("default")

                for variant in variants.get("options", []):
                    vid = variant["id"]
                    vname = variant.get("name", vid)
                    dark, light = resolve_variant(base_dark, base_light, variant)

                    resolved = {"dark": dark, "light": light, "name": f"{theme_name} {vname}"}
                    combined = generate_combined_preview(resolved)
                    dark_svg = generate_single_preview(dark, f"{theme_name} {vname} (dark)")
                    light_svg = generate_single_preview(light, f"{theme_name} {vname} (light)")

                    files = [
                        (f"preview-{vid}.svg", combined),
                        (f"preview-{vid}-dark.svg", dark_svg),
                        (f"preview-{vid}-light.svg", light_svg),
                    ]
                    if vid == default_id:
                        files += [("preview.svg", combined), ("preview-dark.svg", dark_svg), ("preview-light.svg", light_svg)]

                    for filename, content in files:
                        path = theme_dir / filename
                        with open(path, "w") as f:
                            f.write(content)
                        print(f"Generated {path}")
        else:
            combined = generate_combined_preview(theme)
            dark = generate_single_preview(base_dark, f"{theme_name} (dark)")
            light = generate_single_preview(base_light, f"{theme_name} (light)")

            for filename, content in [("preview.svg", combined), ("preview-dark.svg", dark), ("preview-light.svg", light)]:
                path = theme_dir / filename
                with open(path, "w") as f:
                    f.write(content)
                print(f"Generated {path}")


def main():
    themes_dir = Path(__file__).parent.parent / "themes"
    generate_all_previews(themes_dir)
    print("\nDone!")


if __name__ == "__main__":
    main()
