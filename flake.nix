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
    in
    {
      checks = self.packages;
      packages = lib.genAttrs systems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        import ./nix/default.nix { inherit pkgs; }
      );
      nixosModules = {
        dms-plugin-registry = ./nix/module.nix;
        default = self.nixosModules.dms-plugin-registry;
      };
      homeModules = {
        dms-plugin-registry = ./nix/module.nix;
        default = self.homeModules.dms-plugin-registry;
      };

      formatter = lib.genAttrs systems (system: nixpkgs.legacyPackages.${system}.nixfmt);
    };
}
