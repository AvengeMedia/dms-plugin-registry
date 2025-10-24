---
date: 2025-10-24
title: World Clock
author: Bruno Cesar Rocha
tags: dankbar-widget, utilities, niri, hyprland, any
card_image: https://github.com/rochacbruno/WorldClock/raw/main/screenshot.png
pinned: false
---

Multiple timezones clock for DankBar <a href="https://github.com/rochacbruno/WorldClock" target="_blank" rel="noopener noreferrer"><img src="./static/repo-icon.png" alt="Repository" style="vertical-align: middle; height: 24px;"></a>


![RELEASE](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Frochacbruno%2FWorldClock%2Fmain%2Fplugin.json&query=version&style=for-the-badge&label=RELEASE&labelColor=101418&color=9ccbfb)

> [!NOTE] installation
> Run `dms plugins install worldClock`  
> <small>or install using the plugins tab on DMS settings</small>

---

| Plugin Information                 | Value                                         |
| ---------------------------------- | --------------------------------------------- |
| id                                 | worldClock                               |
| name                               | World Clock                             |
| author                             | Bruno Cesar Rocha                           |
| repo                               | [Link](https://github.com/rochacbruno/WorldClock)                     |
| capabilities                       | dankbar-widget        |
| category                           | utilities                         |
| compositors                        | niri, hyprland         |
| distro                             | any              |
| dependencies                       | moment-js        |
| requires DMS                       | >0.0.28                     |


![World Clock Screenshot](https://github.com/rochacbruno/WorldClock/raw/main/screenshot.png)

# WorldClock Plugin for DMS

A plugin that displays multiple timezones in the DMS bar.

<img alt="WorldClock plugin" src="screenshot.png" />



## Installation

```bash
mkdir -p ~/.config/DankMaterialShell/plugins/
git clone https://github.com/rochacbruno/WorldClock ~/.config/DankMaterialShell/plugins/WorldClock
```

## Usage

1. Open DMS Settings <kbd>Super + , </kbd>
2. Go to the "Plugins" tab
3. Enable the "World Clock" plugin
4. Configure timezones in the plugin settings
5. Add the "worldClock" widget to your DankBar configuration

## Configuration

The plugin stores timezone configurations in the DMS settings. You can add/remove timezones through the plugin settings interface.

### Common Timezone Examples:
- America/New_York (Eastern Time)
- America/Los_Angeles (Pacific Time)
- Europe/London (Greenwich Mean Time)
- Europe/Paris (Central European Time)
- Asia/Tokyo (Japan Standard Time)
- Australia/Sydney (Australian Eastern Time)

## Files

- `plugin.json` - Plugin manifest and metadata
- `WorldClockWidget.qml` - Main widget component
- `WorldClockSettings.qml` - Settings interface
- `timezone-utils.js` - Timezone utility functions
- `moment.js` - Moment.js library (stub - replace with real file)
- `moment-timezone.js` - Moment timezone library (stub - replace with real file)

## Permissions

This plugin requires:
- `settings_read` - To read timezone configurations
- `settings_write` - To save timezone configurations


<img width="792" height="786" alt="Screenshot from 2025-09-30 19-34-34" src="https://github.com/user-attachments/assets/98e03d98-2752-41cf-9678-419a11560031" />
<img width="490" height="574" alt="Screenshot from 2025-09-30 19-34-51" src="https://github.com/user-attachments/assets/87d7b179-8ed5-4ef4-9de1-de27137c8544" />

