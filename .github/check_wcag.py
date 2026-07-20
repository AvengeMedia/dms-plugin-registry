#!/usr/bin/env python3
"""Check theme color schemes against WCAG 2.2 contrast requirements."""

import argparse
import json
import sys
from pathlib import Path

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

# Thresholds from WCAG 2.2 SC 1.4.3 / 1.4.6
# https://www.w3.org/TR/WCAG22/#contrast-minimum
AA_RATIO = 4.5
AAA_RATIO = 7.0

TEXT_PAIRS = [
    ("backgroundText", "background"),
    ("surfaceText", "surface"),
    ("surfaceText", "surfaceContainerLowest"),
    ("surfaceText", "surfaceContainerLow"),
    ("surfaceText", "surfaceContainer"),
    ("surfaceText", "surfaceContainerHigh"),
    ("surfaceText", "surfaceContainerHighest"),
    ("surfaceVariantText", "surfaceVariant"),
    ("primaryText", "primary"),
]

LEVEL_RANK = {"fail": 0, "AA": 1, "AAA": 2}


def parse_hex(value):
    if not isinstance(value, str):
        return None
    if len(value) != 7 or not value.startswith("#"):
        return None

    try:
        return tuple(int(value[i : i + 2], 16) for i in (1, 3, 5))
    except ValueError:
        return None


def relative_luminance(rgb):
    # https://www.w3.org/TR/WCAG22/#dfn-relative-luminance
    def linearize(channel):
        channel = channel / 255
        if channel <= 0.03928:
            return channel / 12.92
        return ((channel + 0.055) / 1.055) ** 2.4

    r, g, b = (linearize(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg, bg):
    # https://www.w3.org/TR/WCAG22/#dfn-contrast-ratio
    lighter, darker = sorted(
        (relative_luminance(fg), relative_luminance(bg)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


def level_for_ratio(ratio):
    if ratio >= AAA_RATIO:
        return "AAA"
    if ratio >= AA_RATIO:
        return "AA"
    return "fail"


def scheme_report(scheme):
    ratios = []
    for fg_key, bg_key in TEXT_PAIRS:
        fg = parse_hex(scheme.get(fg_key))
        bg = parse_hex(scheme.get(bg_key))
        if fg is None or bg is None:
            continue
        ratios.append((contrast_ratio(fg, bg), fg_key, bg_key))

    if not ratios:
        return None

    min_ratio, fg_key, bg_key = min(ratios)
    return {
        "level": level_for_ratio(min_ratio),
        "minRatio": round(min_ratio, 2),
        "worstPair": [fg_key, bg_key],
    }


def mode_schemes(theme, mode):
    base = theme.get(mode, {})
    variants = theme.get("variants")
    if not variants:
        return {"": base}, ""

    if variants.get("type") == "multi":
        return multi_variant_schemes(variants, base, mode)

    options = variants.get("options", [])
    if not options:
        return {"": base}, ""

    schemes = {}
    for option in options:
        oid = option.get("id")
        if not oid:
            continue
        schemes[oid] = {**base, **option.get(mode, {})}
    return schemes, variants.get("default", "")


def multi_variant_schemes(variants, base, mode):
    schemes = {}
    for flavor in variants.get("flavors", []):
        fid = flavor.get("id")
        if not fid or mode not in flavor:
            continue
        for accent in variants.get("accents", []):
            aid = accent.get("id")
            if not aid:
                continue
            accent_colors = accent.get(fid) or {}
            schemes[f"{fid}-{aid}"] = {**base, **flavor.get(mode, {}), **accent_colors}

    defaults = variants.get("defaults", {}).get(mode, {})
    default_key = f"{defaults.get('flavor')}-{defaults.get('accent')}"
    return schemes, default_key


def worst_report(reports):
    return min(
        reports.values(),
        key=lambda r: (LEVEL_RANK[r["level"]], r["minRatio"]),
    )


def mode_report(theme, mode):
    schemes, default_key = mode_schemes(theme, mode)
    reports = {}
    for key, scheme in schemes.items():
        report = scheme_report(scheme)
        if report is None:
            continue
        reports[key] = report

    if not reports:
        return None

    primary = dict(reports.get(default_key) or worst_report(reports))
    if len(reports) > 1:
        primary["variants"] = {key: r["level"] for key, r in sorted(reports.items())}
    return primary


def theme_report(theme):
    dark = mode_report(theme, "dark")
    light = mode_report(theme, "light")
    modes = [m for m in (dark, light) if m]
    if not modes:
        return None

    report = {"level": min((m["level"] for m in modes), key=LEVEL_RANK.get)}
    if dark:
        report["dark"] = dark
    if light:
        report["light"] = light
    return report


def markdown_summary(report):
    badge_colors = {"AAA": "brightgreen", "AA": "green", "fail": "lightgrey"}
    level = report["level"]
    label = level if level != "fail" else "below AA"

    # Static badge format: https://shields.io/badges (underscores render as spaces)
    badge_label = label.replace(" ", "_")
    lines = [
        f"![WCAG {label}](https://img.shields.io/badge/WCAG_contrast-{badge_label}-{badge_colors[level]})",
        "",
    ]

    details = []
    for mode in ("dark", "light"):
        mode_result = report.get(mode)
        if not mode_result:
            continue
        fg_key, bg_key = mode_result["worstPair"]
        details.append(
            f"{mode} **{mode_result['level']}** "
            f"(min {mode_result['minRatio']}:1, {fg_key} on {bg_key})"
        )
    lines.append(" · ".join(details))
    lines.append("")
    return "\n".join(lines)


def print_reports(reports):
    level_colors = {"AAA": GREEN, "AA": GREEN, "fail": RED}
    for slug, report in sorted(reports.items()):
        color = level_colors[report["level"]]
        parts = []
        for mode in ("dark", "light"):
            mode_result = report.get(mode)
            if not mode_result:
                continue
            parts.append(
                f"{mode} {mode_result['level']} (min {mode_result['minRatio']}:1)"
            )
        print(f"{slug}: {color}{report['level']}{RESET} — {', '.join(parts)}")


def load_theme(theme_dir):
    theme_file = theme_dir / "theme.json"
    if not theme_file.exists():
        print(f"{YELLOW}Skipping {theme_dir}: no theme.json{RESET}", file=sys.stderr)
        return None

    try:
        with open(theme_file) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"{YELLOW}Skipping {theme_dir}: {e}{RESET}", file=sys.stderr)
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dirs", nargs="*", help="theme directories (default: all)")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true")
    output.add_argument("--markdown", action="store_true")
    args = parser.parse_args()

    if args.dirs:
        theme_dirs = [Path(d) for d in args.dirs]
    else:
        themes_root = Path(__file__).parent.parent / "themes"
        if not themes_root.exists():
            print(f"{YELLOW}No themes/ directory found{RESET}", file=sys.stderr)
            return
        theme_dirs = sorted(
            d for d in themes_root.iterdir() if (d / "theme.json").exists()
        )

    reports = {}
    for theme_dir in theme_dirs:
        theme = load_theme(theme_dir)
        if theme is None:
            continue
        report = theme_report(theme)
        if report is None:
            continue
        reports[theme_dir.name] = report

    if args.json:
        print(json.dumps(reports, indent=2))
        return
    if args.markdown:
        for report in reports.values():
            print(markdown_summary(report))
        return
    print_reports(reports)


if __name__ == "__main__":
    main()
