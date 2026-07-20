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

# Pairs mirror what DMS/quickshell actually renders: bars, popouts, and modals
# fill with surfaceContainer, nested cards with surfaceContainerHigh (see
# DankMaterialShell Common/Theme.qml nestedSurface), window bases with surface.
# Body covers the text read constantly; accent covers primary, which DMS draws
# as bar text (Clock widget) and as filled button labels.
BODY_PAIRS = [
    ("surfaceText", "surface"),
    ("surfaceText", "surfaceContainer"),
    ("surfaceText", "surfaceContainerHigh"),
    ("surfaceText", "surfaceContainerHighest"),
    ("surfaceVariantText", "surface"),
    ("surfaceVariantText", "surfaceContainer"),
    ("surfaceVariantText", "surfaceContainerHigh"),
]

ACCENT_PAIRS = [
    ("primaryText", "primary"),
    ("primary", "surfaceContainer"),
]

TEXT_PAIRS = BODY_PAIRS + ACCENT_PAIRS

# Status colors render as standalone icons and badges, so they get the 3:1
# non-text minimum from WCAG 2.2 SC 1.4.11
# https://www.w3.org/TR/WCAG22/#non-text-contrast
# Outline is excluded: it is a divider color that DMS draws at 12% alpha
# (Theme.outlineMedium), which SC 1.4.11 exempts as decorative.
NON_TEXT_PAIRS = [
    ("error", "surfaceContainer"),
    ("warning", "surfaceContainer"),
    ("info", "surfaceContainer"),
]
NON_TEXT_RATIO = 3.0

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


def worst_ratio(scheme, pairs):
    worst = None
    for fg_key, bg_key in pairs:
        fg = parse_hex(scheme.get(fg_key))
        bg = parse_hex(scheme.get(bg_key))
        if fg is None or bg is None:
            continue

        ratio = contrast_ratio(fg, bg)
        if worst is not None and ratio >= worst[0]:
            continue
        worst = (ratio, fg_key, bg_key)

    return worst


def group_report(scheme, pairs):
    worst = worst_ratio(scheme, pairs)
    if worst is None:
        return None

    ratio, fg_key, bg_key = worst
    return {
        "level": level_for_ratio(ratio),
        "minRatio": round(ratio, 2),
        "worstPair": [fg_key, bg_key],
    }


def scheme_report(scheme):
    text = worst_ratio(scheme, TEXT_PAIRS)
    if text is None:
        return None

    min_ratio, fg_key, bg_key = text
    report = {
        "level": level_for_ratio(min_ratio),
        "minRatio": round(min_ratio, 2),
        "worstPair": [fg_key, bg_key],
    }

    body = group_report(scheme, BODY_PAIRS)
    if body:
        report["body"] = body

    accent = group_report(scheme, ACCENT_PAIRS)
    if accent:
        report["accent"] = accent

    non_text = worst_ratio(scheme, NON_TEXT_PAIRS)
    if non_text is None:
        return report

    non_text_ratio, non_text_fg, non_text_bg = non_text
    report["nonText"] = {
        "level": "AA" if non_text_ratio >= NON_TEXT_RATIO else "fail",
        "minRatio": round(non_text_ratio, 2),
        "worstPair": [non_text_fg, non_text_bg],
    }

    # SC 1.4.11 is itself a Level AA criterion, so failing it fails AA outright.
    if non_text_ratio < NON_TEXT_RATIO:
        report["level"] = "fail"
    return report


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


def tier_levels(report, tier):
    levels = {}
    for mode in ("dark", "light"):
        mode_result = report.get(mode)
        if not mode_result:
            continue
        if tier == "all":
            levels[mode] = mode_result["level"]
            continue
        levels[mode] = mode_result.get(tier, {}).get("level")
    return {mode: level for mode, level in levels.items() if level}


def badge_level_label(report):
    # A theme often passes in one mode only, or passes for everything except the
    # accent color, so credit what does pass instead of flattening it all to a
    # single failure.
    for tier, suffix in (("all", ""), ("body", " body")):
        levels = tier_levels(report, tier)
        passing = {m: l for m, l in levels.items() if l != "fail"}
        if not passing:
            continue

        level = min(passing.values(), key=LEVEL_RANK.get)
        if len(passing) == len(levels):
            return level, f"{level}{suffix}"
        return level, f"{level}{suffix} ({next(iter(passing))})"

    return "fail", "below AA"


def badge_markdown(report):
    badge_colors = {"AAA": "brightgreen", "AA": "green", "fail": "lightgrey"}
    level, label = badge_level_label(report)

    # Static badge format: https://shields.io/badges (underscores render as spaces)
    badge_label = label.replace(" ", "_")
    return f"![WCAG {label}](https://img.shields.io/badge/WCAG_contrast-{badge_label}-{badge_colors[level]})"


def markdown_summary(report):
    lines = [
        badge_markdown(report),
        "",
    ]

    for mode in ("dark", "light"):
        mode_result = report.get(mode)
        if not mode_result:
            continue
        lines.append(f"**{mode}** — {group_summary(mode_result)}")
        lines.append("")
    return "\n".join(lines)


def group_summary(mode_result):
    parts = []
    for tier, label in (("body", "body text"), ("accent", "accent"), ("nonText", "status")):
        group = mode_result.get(tier)
        if not group:
            continue
        fg_key, bg_key = group["worstPair"]
        parts.append(
            f"{label} {group['level']} ({group['minRatio']}:1, {fg_key} on {bg_key})"
        )
    return " · ".join(parts)


def print_reports(reports):
    level_colors = {"AAA": GREEN, "AA": GREEN, "fail": RED}
    for slug, report in sorted(reports.items()):
        _, label = badge_level_label(report)
        color = level_colors[report["level"]]
        parts = []
        for mode in ("dark", "light"):
            mode_result = report.get(mode)
            if not mode_result:
                continue
            body = mode_result.get("body", {}).get("level", "n/a")
            accent = mode_result.get("accent", {}).get("level", "n/a")
            parts.append(f"{mode} body {body} / accent {accent}")
        print(f"{slug}: {color}{label}{RESET} — {', '.join(parts)}")


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
    output.add_argument(
        "--write", action="store_true", help="write wcag.json next to each theme.json"
    )
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
        if args.write:
            with open(theme_dir / "wcag.json", "w") as f:
                json.dump(report, f, indent=2)
                f.write("\n")
            print(f"Wrote {theme_dir / 'wcag.json'}")

    if args.write:
        return
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
