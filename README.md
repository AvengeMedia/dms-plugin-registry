# Dank Material Shell Plugins

This repository contains a collection of plugins for [Dank Material Shell](https://github.com/AvengeMedia/DankMaterialShell)

## Contributing

To add your Plugin to the list please read the [contribution guidelines](CONTRIBUTING.md) and create a pull request.

## Installing Plugins

To install a plugin clone the plugin repository into your `~/.config/DankMaterialShell/plugins/` folder and restart your dms session with `dms restart`. NOTE: Some plugins may have additional dependencies that need to be installed manually, please refer to the plugin documentation for more information, some plugins are part of a monorepo and need to be installed by copying the relvant path to the plugins folder.

## Disclaimer

These plugins are created by third-party developers and are not officially supported by the Dank Material Shell team. Use them at your own risk. In case of issues, please contact the plugin author directly.

## Plugins

**Categories:** [Appearance](#appearance) | [Monitoring](#monitoring) | [Utilities](#utilities)

----


### Appearance


#### [WallpaperShuffler](https://github.com/Daniel-42-z/dankmaterialshell-plugins)

Shuffles wallpapers with a given time interval, finds wallpapers recursively inside the specified folder



- author: Daniel-42-z
- compositors: niri, hyprland
- capabilities: set-wallpaper
- dependencies: 
- distro: any



> [!NOTE]
> This plugin is part of a monorepo, please copy the contents of the [WallpaperShuffler](https://github.com/Daniel-42-z/dankmaterialshell-plugins/tree/main/WallpaperShuffler) folder to your `~/.config/DankMaterialShell/plugins/` folder.







----


### Monitoring


#### [PowerUsage](https://github.com/Daniel-42-z/dankmaterialshell-plugins)

Display real-time power consumption from your device



- author: Daniel-42-z
- compositors: niri, hyprland
- capabilities: dankbar-widget
- dependencies: 
- distro: any



> [!NOTE]
> This plugin is part of a monorepo, please copy the contents of the [PowerUsage](https://github.com/Daniel-42-z/dankmaterialshell-plugins/tree/main/PowerUsage) folder to your `~/.config/DankMaterialShell/plugins/` folder.





<details>
<summary>Screenshot</summary>

![screenshot](https://github.com/Daniel-42-z/dankmaterialshell-plugins/raw/main/PowerUsage/screenshot.png)

</details>





----


### Utilities


#### [Calculator](https://github.com/rochacbruno/DankCalculator)

A calculator plugin that evaluates mathematical expressions and copies results to clipboard

<strong>requires DMS version</strong>: <em>>0.1.18</em>

- author: Bruno Cesar Rocha
- compositors: niri, hyprland
- capabilities: launcher
- dependencies: 
- distro: any





<details>
<summary>Screenshot</summary>

![screenshot](https://github.com/rochacbruno/DankCalculator/raw/main/screenshot.png)

</details>




#### [Dank Actions](https://github.com/AvengeMedia/dms-plugins)

Add customizable, scriptable actions to your bar.



- author: Avenge Media
- compositors: niri, hyprland
- capabilities: dankbar-widget
- dependencies: 
- distro: any



> [!NOTE]
> This plugin is part of a monorepo, please copy the contents of the [DankActions](https://github.com/AvengeMedia/dms-plugins/tree/main/DankActions) folder to your `~/.config/DankMaterialShell/plugins/` folder.





<details>
<summary>Screenshot</summary>

![screenshot](https://private-user-images.githubusercontent.com/550752/497937179-36b44c32-69b5-49c9-97d2-87f530e4b7fd.png?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NjAzODk0NTcsIm5iZiI6MTc2MDM4OTE1NywicGF0aCI6Ii81NTA3NTIvNDk3OTM3MTc5LTM2YjQ0YzMyLTY5YjUtNDljOS05N2QyLTg3ZjUzMGU0YjdmZC5wbmc_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjUxMDEzJTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI1MTAxM1QyMDU5MTdaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT1mYzJiYTliN2FiNmFhYzY5MWQyODcxNTJkMzQwNTNiYzQzZjgwZDgxYTQ0ZDQ1Y2I5NTQyODdlNzU4MGU0MWEwJlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCJ9.HP1Lc3rg08ouX4XugxUB3hAu5ZbpDuhKSLy_a0Hk4PU)

</details>




#### [Dank Battery Alerts](https://github.com/AvengeMedia/dms-plugins)

Notify on low battery levels.



- author: Avenge Media
- compositors: niri, hyprland
- capabilities: watch-events, notify
- dependencies: 
- distro: any



> [!NOTE]
> This plugin is part of a monorepo, please copy the contents of the [DankBatteryAlerts](https://github.com/AvengeMedia/dms-plugins/tree/main/DankBatteryAlerts) folder to your `~/.config/DankMaterialShell/plugins/` folder.





<details>
<summary>Screenshot</summary>

![screenshot](https://private-user-images.githubusercontent.com/550752/498391777-4302d886-eb87-41d4-a9a4-1eeaadd787c6.png?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NjAzODk0NTcsIm5iZiI6MTc2MDM4OTE1NywicGF0aCI6Ii81NTA3NTIvNDk4MzkxNzc3LTQzMDJkODg2LWViODctNDFkNC1hOWE0LTFlZWFhZGQ3ODdjNi5wbmc_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjUxMDEzJTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI1MTAxM1QyMDU5MTdaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT04ZGMzNzY1MGZmMGE0OTc0ZTFiOGY3ZjJkNzljNTc5NzkwMDNiYWUxYzc3YTIwYTdhZDVhMDViMmIwMzVkMzk4JlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCJ9.KQZ_pLKHEjCNYsRMOuCUKjl4cYXdQkCAbvkVEfiJaJk)

</details>




#### [Dank Hooks](https://github.com/AvengeMedia/dms-plugins)

Trigger scripts based on various system events.



- author: Avenge Media
- compositors: niri, hyprland
- capabilities: watch-events
- dependencies: 
- distro: any



> [!NOTE]
> This plugin is part of a monorepo, please copy the contents of the [DankHooks](https://github.com/AvengeMedia/dms-plugins/tree/main/DankHooks) folder to your `~/.config/DankMaterialShell/plugins/` folder.





<details>
<summary>Screenshot</summary>

![screenshot](https://private-user-images.githubusercontent.com/550752/498377075-83e89b5b-0636-4b8e-ba29-1fa4d12169a0.png?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NjAzODk0NTcsIm5iZiI6MTc2MDM4OTE1NywicGF0aCI6Ii81NTA3NTIvNDk4Mzc3MDc1LTgzZTg5YjViLTA2MzYtNGI4ZS1iYTI5LTFmYTRkMTIxNjlhMC5wbmc_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjUxMDEzJTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI1MTAxM1QyMDU5MTdaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT1mMjEyNTg4ZTFkNWVkMmM1NjUwNGM4YmFhZjhkYmMwZThmMzc2MmJiYzNiMTBjNmM0MjQxM2Q3N2MxNzQ0YzAwJlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCJ9.Q0n1hLpqhOJQrx0cf5Zjy6J2cgmuj6LlIfiF0CYp4u8)

</details>




#### [Dank Pomodoro Timer](https://github.com/AvengeMedia/dms-plugins)

A customizable Pomodoro timer.



- author: Avenge Media
- compositors: niri, hyprland
- capabilities: dankbar-widget
- dependencies: 
- distro: any



> [!NOTE]
> This plugin is part of a monorepo, please copy the contents of the [DankPomodoroTimer](https://github.com/AvengeMedia/dms-plugins/tree/main/DankPomodoroTimer) folder to your `~/.config/DankMaterialShell/plugins/` folder.





<details>
<summary>Screenshot</summary>

![screenshot](https://private-user-images.githubusercontent.com/550752/497960861-b51b5f78-5215-403c-850f-c7e137097438.png?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NjAzODk0NTcsIm5iZiI6MTc2MDM4OTE1NywicGF0aCI6Ii81NTA3NTIvNDk3OTYwODYxLWI1MWI1Zjc4LTUyMTUtNDAzYy04NTBmLWM3ZTEzNzA5NzQzOC5wbmc_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjUxMDEzJTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI1MTAxM1QyMDU5MTdaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT01NDczMWU4MTQ4ZjU2YjgxNjg2ZmI0ZjA4Y2M0OTBjOGQwZmQ4N2E4NGI5MTg3NmQ4OTMyYTAwYzYxNzBhYzQwJlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCJ9.5seKYp0TcRQZK3egG54ofMFIqOKF7u1EDn3EUl3g8og)

</details>




#### [NiriWindows](https://github.com/rochacbruno/DankNiriWindows)

List and switch to open Niri windows from the launcher

<strong>requires DMS version</strong>: <em>>0.1.18</em>

- author: Bruno Cesar Rocha
- compositors: niri
- capabilities: launcher
- dependencies: 
- distro: any





<details>
<summary>Screenshot</summary>

![screenshot](https://github.com/rochacbruno/DankNiriWindows/raw/main/screenshot.png)

</details>




#### [WorldClock](https://github.com/rochacbruno/WorldClock)

Multiple timezones clock for DankBar

<strong>requires DMS version</strong>: <em>>0.0.28</em>

- author: Bruno Cesar Rocha
- compositors: niri, hyprland
- capabilities: dankbar-widget
- dependencies: moment-js
- distro: any





<details>
<summary>Screenshot</summary>

![screenshot](https://github.com/rochacbruno/WorldClock/raw/main/screenshot.png)

</details>





----

