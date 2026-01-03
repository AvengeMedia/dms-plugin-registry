{
  outputs = { self, nixpkgs, ... }:
    let
      inherit (nixpkgs) lib;
      systems = [ "aarch64-darwin" "aarch64-linux" "x86_64-darwin" "x86_64-linux" ];
    in
    {
      checks = self.packages;
      packages = lib.genAttrs systems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in import ./nix/default.nix { inherit pkgs; }
      );
      nixosModules.dms-plugin-registry = ./nix/module.nix;
      nixosModules.default = self.nixosModules.dms-plugin-registry;
      homeModules.dms-plugin-registry = ./nix/module.nix;
      homeModules.default = self.homeModules.dms-plugin-registry;
      modules.dms-plugin-registry = ./nix/module.nix;
      modules.default = self.modules.dms-plugin-registry;
    };
}
