---
date: 2025-10-24
title: Dank Hooks
author: Avenge Media
tags: watch-events, utilities, niri, hyprland, any
card_image: https://raw.githubusercontent.com/AvengeMedia/dms-plugin-registry/master/assets/dank-hooks.png
pinned: true
---

Trigger scripts based on various system events. <a href="https://github.com/AvengeMedia/dms-plugins" target="_blank" rel="noopener noreferrer"><img src="./static/repo-icon.png" alt="Repository" style="vertical-align: middle; height: 24px;"></a>


![RELEASE](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2FAvengeMedia%2Fdms-plugins%2Fmaster%2FDankHooks%2Fplugin.json&query=version&style=for-the-badge&label=RELEASE&labelColor=101418&color=9ccbfb)

> [!NOTE] installation
> Run `dms plugins install dankHooks`  
> <small>or install using the plugins tab on DMS settings</small>

---

| Plugin Information                 | Value                                         |
| ---------------------------------- | --------------------------------------------- |
| id                                 | dankHooks                               |
| name                               | Dank Hooks                             |
| author                             | Avenge Media                           |
| repo                               | [Link](https://github.com/AvengeMedia/dms-plugins)                     |
| capabilities                       | watch-events        |
| category                           | utilities                         |
| compositors                        | niri, hyprland         |
| distro                             | any              |
| dependencies                       |         |
| requires DMS                       | N/A                     |


![Dank Hooks Screenshot](https://raw.githubusercontent.com/AvengeMedia/dms-plugin-registry/master/assets/dank-hooks.png)

# Dank Hooks Plugin

## Available Hooks

### Appearance & Theme

| Hook | Trigger | Hook Name | Value |
|------|---------|-----------|-------|
| **Wallpaper Changed** | When wallpaper changes | `onWallpaperChanged` | Wallpaper file path |
| **Light/Dark Mode Changed** | When switching between modes | `onLightModeChanged` | `light` or `dark` |
| **Theme Changed** | When color theme changes | `onThemeChanged` | Theme name (e.g., `blue`, `red`, `dynamic`) |
| **Night Mode Changed** | When night mode toggles | `onNightModeChanged` | `enabled` or `disabled` |

### Power & Battery

| Hook | Trigger | Hook Name | Value |
|------|---------|-----------|-------|
| **Battery Level Changed** | When battery percentage changes | `onBatteryLevelChanged` | Battery percentage (0-100) |
| **Battery Charging State Changed** | When charging state changes | `onBatteryChargingChanged` | `charging` or `not-charging` |
| **Power Adapter Changed** | When power adapter connects/disconnects | `onBatteryPluggedInChanged` | `plugged-in` or `on-battery` |

### Network

| Hook | Trigger | Hook Name | Value |
|------|---------|-----------|-------|
| **WiFi Connection Changed** | When WiFi connects/disconnects | `onWifiConnectedChanged` | `connected` or `disconnected` |
| **WiFi Network Changed** | When connected WiFi network changes | `onWifiSSIDChanged` | SSID name or `none` |
| **Ethernet Connection Changed** | When Ethernet connects/disconnects | `onEthernetConnectedChanged` | `connected` or `disconnected` |

### Audio

| Hook | Trigger | Hook Name | Value |
|------|---------|-----------|-------|
| **Audio Volume Changed** | When speaker volume changes | `onAudioVolumeChanged` | Volume percentage (0-100) |
| **Audio Mute Changed** | When speakers mute/unmute | `onAudioMuteChanged` | `muted` or `unmuted` |
| **Microphone Mute Changed** | When microphone mutes/unmutes | `onMicMuteChanged` | `muted` or `unmuted` |

### Display & Media

| Hook | Trigger | Hook Name | Value |
|------|---------|-----------|-------|
| **Brightness Changed** | When screen brightness changes | `onBrightnessChanged` | Brightness percentage (0-100) |
| **Media Playback Changed** | When media starts/stops playing | `onMediaPlayingChanged` | `playing` or `paused` |

### System

| Hook | Trigger | Hook Name | Value |
|------|---------|-----------|-------|
| **Do Not Disturb Changed** | When DND mode toggles | `onDoNotDisturbChanged` | `enabled` or `disabled` |

