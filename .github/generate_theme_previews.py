#!/usr/bin/env python3
"""Generate SVG preview images for themes."""

import json
from html import escape as xml_escape
from pathlib import Path

# Mirrors how DankMaterialShell composes a desktop: the bar and popouts fill
# with surfaceContainer, nested cards step up to surfaceContainerHigh, input
# wells drop to surface, and the clock renders primary as accent text.
PANEL_TEMPLATE = """<g transform="translate({x}, 0)">
  <rect width="280" height="240" fill="{background}"/>

  <rect width="280" height="26" fill="{surfaceContainer}"/>
  <rect x="12" y="9" width="20" height="8" rx="4" fill="{primary}"/>
  <circle cx="40" cy="13" r="3" fill="{surfaceVariantText}"/>
  <circle cx="50" cy="13" r="3" fill="{surfaceVariantText}"/>
  <text x="140" y="17" font-family="{font}" font-size="10" font-weight="600" text-anchor="middle" fill="{primary}">9:41</text>
  <circle cx="238" cy="13" r="4" fill="{info}"/>
  <circle cx="252" cy="13" r="4" fill="{warning}"/>
  <circle cx="266" cy="13" r="4" fill="{error}"/>

  <rect x="14" y="38" width="252" height="190" rx="12" fill="{surfaceContainer}" stroke="{outline}" stroke-opacity="0.5"/>
  <text x="28" y="61" font-family="{font}" font-size="12.5" font-weight="600" fill="{surfaceText}">{name}</text>
  <text x="28" y="77" font-family="{font}" font-size="9.5" fill="{surfaceVariantText}">Secondary text</text>

  <rect x="26" y="87" width="228" height="50" rx="8" fill="{surfaceContainerHigh}"/>
  <text x="38" y="105" font-family="{font}" font-size="10" font-weight="500" fill="{surfaceText}">Nested card</text>
  <text x="38" y="120" font-family="{font}" font-size="9" fill="{surfaceVariantText}">Body text on an elevated surface</text>

  <rect x="26" y="145" width="228" height="22" rx="6" fill="{surface}" stroke="{outline}" stroke-opacity="0.4"/>
  <text x="38" y="160" font-family="{font}" font-size="9" fill="{surfaceVariantText}">Search</text>

  <rect x="26" y="175" width="78" height="22" rx="11" fill="{primary}"/>
  <text x="65" y="190" font-family="{font}" font-size="9.5" font-weight="600" text-anchor="middle" fill="{primaryText}">Button</text>
  <rect x="112" y="175" width="70" height="22" rx="11" fill="{primary}" fill-opacity="0.15"/>
  <text x="147" y="190" font-family="{font}" font-size="9.5" font-weight="500" text-anchor="middle" fill="{primary}">Accent</text>
  <rect x="190" y="175" width="64" height="22" rx="11" fill="{surfaceContainerHighest}"/>
  <text x="222" y="190" font-family="{font}" font-size="9.5" text-anchor="middle" fill="{surfaceText}">Chip</text>

  <circle cx="34" cy="212" r="7" fill="{primary}"/>
  <circle cx="54" cy="212" r="7" fill="{secondary}"/>
  <circle cx="74" cy="212" r="7" fill="{error}"/>
  <circle cx="94" cy="212" r="7" fill="{warning}"/>
  <circle cx="114" cy="212" r="7" fill="{info}"/>
</g>"""

COMBINED_TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" width="564" height="240" viewBox="0 0 564 240">
  {dark_panel}
  <rect x="280" y="0" width="4" height="240" fill="#888"/>
  {light_panel}
</svg>"""

SINGLE_TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" width="280" height="240" viewBox="0 0 280 240">
  {panel}
</svg>"""

FONT_STACK = "system-ui, -apple-system, Segoe UI, sans-serif"

PANEL_KEYS = {
    "background", "surface", "surfaceContainer", "surfaceContainerHigh",
    "surfaceContainerHighest", "surfaceText", "surfaceVariantText", "outline",
    "primary", "primaryText", "secondary", "error", "warning", "info",
}


# Fallbacks match DankMaterialShell Common/Theme.qml, which derives missing
# container steps from the ones a theme does define.
PANEL_FALLBACKS = {
    "surfaceContainer": "surface",
    "surfaceContainerHigh": "surfaceContainer",
    "surfaceContainerHighest": "surfaceContainerHigh",
    "surfaceVariantText": "surfaceText",
    "background": "surface",
    "secondary": "primary",
    "info": "primary",
    "warning": "error",
}


def resolve_panel_colors(scheme: dict) -> dict:
    colors = {k: v for k, v in scheme.items() if k in PANEL_KEYS}
    for key in PANEL_KEYS:
        if key in colors:
            continue
        fallback = PANEL_FALLBACKS.get(key)
        while fallback and fallback not in colors:
            fallback = PANEL_FALLBACKS.get(fallback)
        colors[key] = colors.get(fallback, "#808080")
    return colors


def generate_panel(scheme: dict, name: str, x: int) -> str:
    colors = resolve_panel_colors(scheme)
    return PANEL_TEMPLATE.format(
        x=x, name=xml_escape(name), font=FONT_STACK, **colors
    )


def generate_combined_preview(theme: dict) -> str:
    name = theme.get("name", "Theme")
    dark_panel = generate_panel(theme["dark"], f"{name} (dark)", 0)
    light_panel = generate_panel(theme["light"], f"{name} (light)", 284)
    return COMBINED_TEMPLATE.format(dark_panel=dark_panel, light_panel=light_panel)


def generate_single_preview(scheme: dict, name: str) -> str:
    panel = generate_panel(scheme, name, 0)
    return SINGLE_TEMPLATE.format(panel=panel)


def resolve_variant(
    base_dark: dict, base_light: dict, variant: dict
) -> tuple[dict, dict]:
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

    theme_dirs = [
        d for d in themes_dir.iterdir() if d.is_dir() and (d / "theme.json").exists()
    ]
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

                dark_flavor = next(
                    (f for f in flavors if f["id"] == dark_defaults.get("flavor")), None
                )
                dark_accent = next(
                    (a for a in accents if a["id"] == dark_defaults.get("accent")), None
                )
                light_flavor = next(
                    (f for f in flavors if f["id"] == light_defaults.get("flavor")),
                    None,
                )
                light_accent = next(
                    (a for a in accents if a["id"] == light_defaults.get("accent")),
                    None,
                )

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
                    resolved, _ = resolve_multi_variant(
                        theme, light_flavor, light_accent
                    )
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

                    resolved = {
                        "dark": dark,
                        "light": light,
                        "name": f"{theme_name} {vname}",
                    }
                    combined = generate_combined_preview(resolved)
                    dark_svg = generate_single_preview(
                        dark, f"{theme_name} {vname} (dark)"
                    )
                    light_svg = generate_single_preview(
                        light, f"{theme_name} {vname} (light)"
                    )

                    files = [
                        (f"preview-{vid}.svg", combined),
                        (f"preview-{vid}-dark.svg", dark_svg),
                        (f"preview-{vid}-light.svg", light_svg),
                    ]
                    if vid == default_id:
                        files += [
                            ("preview.svg", combined),
                            ("preview-dark.svg", dark_svg),
                            ("preview-light.svg", light_svg),
                        ]

                    for filename, content in files:
                        path = theme_dir / filename
                        with open(path, "w") as f:
                            f.write(content)
                        print(f"Generated {path}")
        else:
            combined = generate_combined_preview(theme)
            dark = generate_single_preview(base_dark, f"{theme_name} (dark)")
            light = generate_single_preview(base_light, f"{theme_name} (light)")

            for filename, content in [
                ("preview.svg", combined),
                ("preview-dark.svg", dark),
                ("preview-light.svg", light),
            ]:
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
