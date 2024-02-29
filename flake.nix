{
  description = "Description for the project";

  inputs = {
    nixpkgs-unstable.url = "github:NixOS/nixpkgs/nixos-unstable";
    nixpkgs-stable.url = "github:NixOS/nixpkgs/nixos-23.11";
    nixpkgs.follows = "nixpkgs-stable";
    snowcli = {
      url = "github:sfc-gh-vtimofeenko/snowcli-nix-flake";

      inputs = {
        nixpkgs-unstable.follows = "nixpkgs-unstable";
        nixpkgs-stable.follows = "nixpkgs-stable";
        nixpkgs.follows = "nixpkgs";
        # Only using 2x in this flake
        snowcli-src-1x.follows = "";
        snowflake-connector-python-1x.follows = "";
        # development
        devshell.follows = "devshell";
        pre-commit-hooks-nix.follows = "pre-commit-hooks-nix";
        treefmt-nix.follows = "treefmt-nix";
      };
    };

    flake-parts.url = "github:hercules-ci/flake-parts";
    devshell = {
      url = "github:numtide/devshell";
      inputs.nixpkgs.follows = "nixpkgs-unstable";
    };
    pre-commit-hooks-nix = {
      url = "github:cachix/pre-commit-hooks.nix";
      inputs.nixpkgs.follows = "nixpkgs-unstable";
      inputs.nixpkgs-stable.follows = "nixpkgs-stable";
    };
    treefmt-nix = {
      url = "github:numtide/treefmt-nix";
      inputs.nixpkgs.follows = "nixpkgs-unstable";
    };
  };

  outputs =
    inputs@{ flake-parts, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [
        inputs.devshell.flakeModule
        inputs.pre-commit-hooks-nix.flakeModule
        inputs.treefmt-nix.flakeModule
      ];
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "aarch64-darwin"
        "x86_64-darwin"
      ];
      perSystem =
        { config
        , inputs'
        , pkgs
        , ...
        }:
        let
          inherit (pkgs.lib) getExe;
          snowCli = pkgs.writeShellScriptBin "snow"
            ''
              ${pkgs.lib.getExe inputs'.snowcli.packages.snowcli-2x} --config-file <(cat<<EOF
              [connections]
              [connections.dev] # DEFAULT connection name is this
              account = "$SNOWFLAKE_ACCOUNT"
              user = "$SNOWFLAKE_USER"
              database = "$SNOWFLAKE_DB"
              schema = "$SNOWFLAKE_SCHEMA"
              password = "$SNOWFLAKE_PASSWORD"
              EOF
              )'';
        in
        {
          # Development configuration
          treefmt = {
            programs = {
              nixpkgs-fmt.enable = true;
              deadnix = {
                enable = true;
                no-lambda-arg = true;
                no-lambda-pattern-names = true;
                no-underscore = true;
              };
              statix.enable = true;
              isort = {
                enable = true;
                profile = "black";
              };
              ruff = {
                enable = true;
                format = true;
              };
            };
            projectRootFile = "flake.nix";
          };

          pre-commit.settings = {
            hooks = {
              treefmt.enable = true;
              deadnix.enable = true;
              statix.enable = true;
              markdownlint.enable = true;
            };
            settings = {
              deadnix.edit = true;
              statix = {
                ignore = [ ".direnv/" ];
                format = "stderr";
              };
              markdownlint.config.MD041 = false; # Disable "first line should be a heading check"
              treefmt.package = config.treefmt.build.wrapper;
            };
          };

          devShells.pre-commit = config.pre-commit.devShell;
          devshells.default = {
            env = [ ];
            commands = [
              {
                help = "Run local Streamlit";
                name = "local-streamlit";
                command = "poetry run streamlit run src/streamlit_app.py";
              }
              {
                help = "Deploy Streamlit to the test account";
                name = "deploy-streamlit";
                command = "${getExe snowCli}";
              }
            ];
            packages = builtins.attrValues { inherit (pkgs) jc jq; } ++ [ snowCli ];
          };
        };
      # flake = { };
    };
}
