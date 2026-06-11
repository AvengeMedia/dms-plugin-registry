{
  inputs.nixpkgs.url = "https://channels.nixos.org/nixpkgs-unstable/nixexprs.tar.xz";

  outputs =
    { self, nixpkgs, ... }:
    let
      inherit (nixpkgs) lib;
      systems = [
        "aarch64-darwin"
        "aarch64-linux"
        "x86_64-darwin"
        "x86_64-linux"
      ];
      forEachSystem = lib.genAttrs systems;
      pkgsForEach = nixpkgs.legacyPackages;
    in
    {
      checks = self.packages;
      packages = forEachSystem (system: import ./nix/default.nix { pkgs = pkgsForEach.${system}; });

      nixosModules = {
        dms-plugin-registry = ./nix/module.nix;
        default = self.nixosModules.dms-plugin-registry;
      };
      homeModules = {
        dms-plugin-registry = ./nix/module.nix;
        default = self.homeModules.dms-plugin-registry;
      };

      formatter = lib.genAttrs systems (system: pkgsForEach.${system}.nixfmt);
    };
}
