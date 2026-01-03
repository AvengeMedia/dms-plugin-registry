# Nix Flake
The registry flake contains packages for all plugins which are updated daily.

## Installation

### With flakes
Add the registry as a flake input:
```nix
{
  inputs = {
    dms-plugin-registry.url = "github:AvengeMedia/dms-plugin-registry";
    dms-plugin-registry.inputs.nixpkgs.follows = "nixpkgs";
  };
}
```

Add the NixOS or Home Manager module:
```nix
{
  # Same module for NixOS and Home Manager
  imports = [ inputs.dms-plugin-registry.modules.default ];
}
```

### Without flakes
Fetch this project with `fetchTarball` then import the module.
```nix
{ pkgs, ... }:
let
  dms-plugin-registry = builtins.fetchTarball "https://github.com/AvengeMedia/dms-plugin-registry/archive/main.tar.gz";

  # Only needed if installing packages manually without NixOS/HM module
  dms-plugin-registry-pkgs = import "${dms-plugin-registry}/nix" { inherit pkgs; };
in
{
  # Add NixOS/HM module
  imports = [ "${dms-plugin-registry}/nix/module.nix" ]; # Same module path for NixOS and Home Manager
}
```

## Usage
Plugin packages are available as flake package outputs or attributes in `default.nix`.
Instead of using packages directly, the recommended way to use this flake is to
import the NixOS or Home Manager module which will add all plugins disabled by default.
Then to use a plugin it just needs to be enabled.

The attribute name for plugins are determined by the `id` property in the plugin registry.
The `id` is the last portion of the url of the "Install" button in the [plugin store](https://danklinux.com/plugins).
For example, the url for the "DankBatteryAlerts" plugin is `dms://plugin/install/dankBatteryAlerts`, so the id is `dankBatteryAlerts`.


Install any plugin package with the NixOS or Home Manager module options:
```nix
{ pkgs, inputs, ... }: {
  programs.dankMaterialShell = {
    plugins = {
      dankBatteryAlerts.enable = true;

      # To manually install a plugin without NixOS/HM module
      # With flakes:
      dankBatteryAlerts.src = inputs.dms-plugin-registry.packages.${pkgs.system}.dankBatteryAlerts;
      # without flakes:
      dankBatteryAlerts.src = dms-plugin-registry-pkgs.dankBatteryAlerts;
    };
  };
}
```
