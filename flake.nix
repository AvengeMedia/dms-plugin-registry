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
      nixosModules.nix-dms-plugins = ./nix/module.nix;
      nixosModules.default = self.nixosModules.nix-dms-plugins;
      homeModules.nix-dms-plugins = ./nix/module.nix;
      homeModules.default = self.homeModules.nix-dms-plugins;
      modules.nix-dms-plugins = ./nix/module.nix;
      modules.default = self.modules.nix-dms-plugins;
    };
}
