{
  description = "A local LeetCode harness: scaffold, run and test solutions from the terminal";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs =
    { self, nixpkgs }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f nixpkgs.legacyPackages.${system});
    in
    {
      packages = forAllSystems (
        pkgs:
        let
          python = pkgs.python314;
        in
        {
          leeth = python.pkgs.buildPythonApplication {
            pname = "leeth";
            version = (builtins.fromTOML (builtins.readFile ./pyproject.toml)).project.version;
            pyproject = true;

            src = ./.;

            # nixpkgs' uv_build may lag behind the version pinned in pyproject.toml
            postPatch = ''
              substituteInPlace pyproject.toml \
                --replace-fail '"uv_build>=0.13.0,<0.14"' '"uv_build"'
            '';

            build-system = [ python.pkgs.uv-build ];

            dependencies = [ python.pkgs.icecream ];

            nativeCheckInputs = [ python.pkgs.pytestCheckHook ];

            pythonImportsCheck = [ "leeth" ];

            meta = {
              description = "A local LeetCode harness: scaffold, run and test solutions from the terminal";
              mainProgram = "leeth";
            };
          };

          default = self.packages.${pkgs.stdenv.hostPlatform.system}.leeth;
        }
      );

      apps = forAllSystems (pkgs: {
        default = {
          type = "app";
          program = nixpkgs.lib.getExe self.packages.${pkgs.stdenv.hostPlatform.system}.leeth;
        };
      });

      devShells = forAllSystems (pkgs: {
        default = pkgs.mkShell {
          packages = [
            pkgs.python314
            pkgs.uv
            pkgs.basedpyright
            pkgs.ruff
            pkgs.ty
          ];
        };
      });
    };
}
