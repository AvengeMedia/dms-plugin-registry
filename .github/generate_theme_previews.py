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


def generate_panel(scheme: dict, name: str, x: int) -> str:
    return PANEL_TEMPLATE.format(x=x, name=name, **scheme)


def generate_combined_preview(theme: dict) -> str:
    name = theme.get("name", "Theme")
    dark = theme["dark"]
    light = theme["light"]

    dark_panel = generate_panel(dark, f"{name} (dark)", 0)
    light_panel = generate_panel(light, f"{name} (light)", 244)

    return COMBINED_TEMPLATE.format(dark_panel=dark_panel, light_panel=light_panel)


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

        svg_content = generate_combined_preview(theme)
        output_path = theme_dir / "preview.svg"

        with open(output_path, "w") as f:
            f.write(svg_content)

        print(f"Generated {output_path}")


def main():
    themes_dir = Path(__file__).parent.parent / "themes"
    generate_all_previews(themes_dir)
    print("\nDone!")


if __name__ == "__main__":
    main()
