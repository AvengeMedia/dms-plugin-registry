{ pkgs ? import <nixpkgs> { }, lib ? pkgs.lib }:
let
  plugins = builtins.fromJSON (builtins.readFile ./plugins-prefetch.json);
  buildPlugin = name: plugin:
    pkgs.stdenvNoCC.mkDerivation {
      name = plugin.meta.id;
      src = pkgs.fetchgit {
        inherit (plugin) url rev hash;
      };

      preferLocalBuild = true;
      allowSubstitutes = false;
      installPhase = ''
        mkdir -p $out
        cp -r ./${plugin.meta.path or "./"}/* $out
      '';
      meta = {
        inherit (plugin.meta) description;
        homepage = plugin.meta.repo;
        platforms = lib.platforms.all;
      };
    };
in
lib.mapAttrs buildPlugin plugins
