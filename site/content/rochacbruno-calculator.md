---
date: 2025-10-24
title: Calculator
author: Bruno Cesar Rocha
tags: launcher, utilities, niri, hyprland, any
card_image: https://github.com/rochacbruno/DankCalculator/raw/main/screenshot.png
pinned: false
---

A calculator plugin that evaluates mathematical expressions and copies results to clipboard <a href="https://github.com/rochacbruno/DankCalculator" target="_blank" rel="noopener noreferrer"><img src="./static/repo-icon.png" alt="Repository" style="vertical-align: middle; height: 24px;"></a>


![RELEASE](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Frochacbruno%2FDankCalculator%2Fmain%2Fplugin.json&query=version&style=for-the-badge&label=RELEASE&labelColor=101418&color=9ccbfb)

> [!NOTE] installation
> Run `dms plugins install calculator`  
> <small>or install using the plugins tab on DMS settings</small>

---

| Plugin Information                 | Value                                         |
| ---------------------------------- | --------------------------------------------- |
| id                                 | calculator                               |
| name                               | Calculator                             |
| author                             | Bruno Cesar Rocha                           |
| repo                               | [Link](https://github.com/rochacbruno/DankCalculator)                     |
| capabilities                       | launcher        |
| category                           | utilities                         |
| compositors                        | niri, hyprland         |
| distro                             | any              |
| dependencies                       |         |
| requires DMS                       | >0.1.18                     |


# Calculator Plugin for DMS Launcher


[![RELEASE](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fgithub.com%2Frochacbruno%2FDankCalculator%2Fraw%2Frefs%2Fheads%2Fmain%2Fplugin.json&query=version&style=for-the-badge&label=RELEASE&labelColor=101418&color=9ccbfb)](https://plugins.danklinux.com/calculator.html)

A launcher plugin that evaluates mathematical expressions and copies results to the clipboard.

![Calculator Plugin Screenshot](https://raw.githubusercontent.com/rochacbruno/DankCalculator/main/screenshot.png)

## Features

- **Real-time calculation**: Type mathematical expressions directly in the launcher
- **Default prefix**: Uses `=` as the default trigger prefix (configurable)
- **Safe evaluation**: Only allows mathematical operations, preventing code injection
- **Clipboard integration**: Press Enter to copy the result to clipboard
- **Multiple operations**: Supports +, -, *, /, ^, %, and parentheses

## Installation

### Via DMS

```bash
dms plugins install Calculator
```

### Via DMS GUI
- Mod + ,
- Go to Plugins Tab
- Choose Browse
- Enable third party
- install Calculator

### Manually

```
cd ~/.config/DankMaterialShell/plugins
git clone https://github.com/rochacbruno/DankCalculator Calculator
```

1. Open DMS Settings (Ctrl+,)
2. Navigate to Plugins tab
3. Click "Scan for Plugins"
4. Enable the "Calculator" plugin with the toggle switch

## Usage

### With Default Settings (= Prefix)

1. Open the launcher (Ctrl+Space)
2. Type the `=` prefix followed by a mathematical expression: `= 3 + 3`
3. The result (`6`) appears as a launcher item
4. Press Enter to copy the result to clipboard

### Customizing the Trigger

You can configure a different trigger prefix or disable it entirely in the settings:

1. Open Settings → Plugins → Calculator
2. Change the trigger to a custom value (e.g., `calc`, `c`, `math`)
3. Or check "No trigger (always active)" to remove the prefix requirement
4. In the launcher, type your configured trigger: `calc 3 + 3` or just `3 + 3` (if no trigger)
5. Press Enter to copy the result

### Adding a keybinding (niri)

```kdl
binds {
      Mod+Shift+C hotkey-overlay-title="Calculator" {
        spawn "dms" "ipc" "call" "spotlight" "openQuery" "=";
    }
}
```

## Supported Operations

- **Addition**: `= 3 + 3` → `6`
- **Subtraction**: `= 10 - 5` → `5`
- **Multiplication**: `= 4 * 7` → `28`
- **Division**: `= 20 / 4` → `5`
- **Exponentiation**: `= 2 ^ 8` → `256`
- **Modulo**: `= 17 % 5` → `2`
- **Parentheses**: `= (5 + 3) * 2` → `16`
- **Decimals**: `= 3.14 * 2` → `6.28`
- **Complex**: `= (10 + 5) * 2 - 3 / 3` → `29`

## Examples

| Expression | Result |
|------------|--------|
| `= 3 + 3` | `6` |
| `= 100 / 4` | `25` |
| `= 2 ^ 10` | `1024` |
| `= (5 + 3) * 2` | `16` |
| `= 3.14159 * 2` | `6.28318` |
| `= 16 ^ 0.5` | `4` (square root) |

## Security

The calculator uses safe expression evaluation:
- Only allows numbers, operators (+, -, *, /, ^, %), parentheses, and dots
- Rejects any expressions with letters or special characters (except operators)
- Prevents code injection by validating input before evaluation

## Files

- `plugin.json` - Plugin manifest
- `CalculatorLauncher.qml` - Main launcher component
- `CalculatorSettings.qml` - Settings UI
- `calculator.js` - Safe expression evaluation logic
- `README.md` - This file

## Configuration

Settings are stored in `~/.config/DankMaterialShell/plugin_settings.json` under the `calculator` plugin key:

```json
{
  "pluginSettings": {
    "calculator": {
      "trigger": "=",
      "noTrigger": false
    }
  }
}
```

## Troubleshooting

**Calculator items don't appear:**
- Make sure the plugin is enabled in Settings → Plugins
- Check that you're typing a valid mathematical expression
- Try disabling "No trigger" and setting a specific trigger

**Result shows wrong value:**
- JavaScript has floating-point precision limitations
- Very large or very small numbers may use scientific notation

**Copy to clipboard doesn't work:**
- Make sure your system clipboard is accessible
- Check console for error messages

## Version

1.0.0

## Author

Bruno Cesar Rocha 

## License

Same as DankMaterialShell

