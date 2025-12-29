{ lib, pkgs, ... }:
let
  plugins = import ./default.nix { inherit pkgs; };
in
{
  programs.dankMaterialShell.plugins = lib.mapAttrs (name: plugin: {
    enable = lib.mkDefault false;
    src = plugin;
  }) plugins;
}
