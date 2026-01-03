{ lib, pkgs, options, ... }:
let
  plugins = import ./default.nix { inherit pkgs; };

  pluginsConfig = lib.mapAttrs (name: plugin: {
    enable = lib.mkDefault false;
    src = plugin;
  }) plugins;

  moduleForStableFlake = lib.optionalAttrs (options ? programs.dankMaterialShell.plugins) {
    programs.dankMaterialShell.plugins = pluginsConfig;
  };

  moduleForFlake = lib.optionalAttrs (options ? programs.dank-material-shell.plugins) {
    programs.dank-material-shell.plugins = pluginsConfig;
  };

  moduleForNixpkgs = lib.optionalAttrs (options ? programs.dms-shell.plugins) {
    programs.dms-shell.plugins = pluginsConfig;
  };
in
lib.mkMerge [
  moduleForStableFlake
  moduleForFlake
  moduleForNixpkgs
]
