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
              [connections.default]
              account = "$SNOWFLAKE_ACCOUNT"
              user = "$SNOWFLAKE_USER"
              password = "$SNOWFLAKE_PASSWORD"
              database = "$SNOWFLAKE_DATABASE"
              schema = "$SNOWFLAKE_SCHEMA"
              warehouse = "$SNOWFLAKE_WAREHOUSE"
              role = "$SNOWFLAKE_ROLE"
              EOF
              ) $@'';
        in
        {
          apps = {
            deploy-streamlit-in-snowflake.program = pkgs.writeShellApplication {
              name = "deploy-streamlit-in-snowflake";
              runtimeInputs = [ snowCli ];
              text = ''
                function exit_trap(){
                  popd
                  popd
                }
                trap exit_trap EXIT # go back to original dir regardless of the exit codes

                PRJ_ROOT=$(git rev-parse --show-toplevel)

                TARGET="$PRJ_ROOT/target"

                pushd "$PRJ_ROOT" # cd to project root directory

                rm -rf "$TARGET"
                cp -rf src "$TARGET"
                pushd "$TARGET"/

                # Create deploy-only config for the query warehouse
                cat >snowflake.local.yml <<EOF
                definition_version: 1
                streamlit:
                  query_warehouse: $SIS_QUERY_WAREHOUSE
                EOF

                # Deploy the application
                # NOTE: the CI variable check prevents the account name from being printed by suppressing all output
                if [ -n "''${CI+x}" ]; then
                    exec &>/dev/null
                fi
                snow streamlit deploy --replace

                # Grant the usage on the created Streamlit to the designated admin role
                cat <<EOF | snow sql -i
                GRANT USAGE ON STREAMLIT $SNOWFLAKE_DATABASE.$SNOWFLAKE_SCHEMA.SENTRY TO ROLE $SIS_GRANT_TO_ROLE;
                EOF
              '';
            };
            tear-down-and-deploy-native-app-in-own-account.program = pkgs.writeShellApplication {
              name = "tear-down-and-deploy-native-app-in-own-account";
              runtimeInputs = [ snowCli pkgs.yq ];
              text = ''
                function exit_trap(){
                  popd
                  popd
                }
                trap exit_trap EXIT # go back to original dir regardless of the exit codes

                PRJ_ROOT=$(git rev-parse --show-toplevel)

                # TARGET="$PRJ_ROOT/target"

                pushd "$PRJ_ROOT" # cd to project root directory

                pushd deployment_models/native-app

                # TODO: handle $CI here

                # Yq is like JQ but for yaml files
                APP_NAME=$(yq --raw-output '."native_app"."application"."name" | ascii_upcase' ./snowflake.yml)

                # NOTE: the CI variable check prevents the account name from being printed by suppressing all output
                if [ -n "''${CI+x}" ]; then
                    exec &>/dev/null
                fi

                snow app teardown
                snow app run

                # Grant the imported privileges automatically
                cat <<EOF | snow sql --stdin
                GRANT IMPORTED PRIVILEGES ON DATABASE IDENTIFIER('"SNOWFLAKE"') TO APPLICATION IDENTIFIER('"''${APP_NAME}"');
                EOF
              '';
            };
          };

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
              ruff.enable = true;
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
                command = "poetry run streamlit run src/Authentication.py";
              }
              {
                help = "Deploy Streamlit to the test account";
                name = "deploy-streamlit-in-snowflake";
                command = "nix run .#deploy-streamlit-in-snowflake";
              }
              {
                help = "Deploy native app to the test account";
                name = "tear-down-and-deploy-native-app-in-own-account";
                command = "nix run .#tear-down-and-deploy-native-app-in-own-account";
              }
            ];
            packages = builtins.attrValues { inherit (pkgs) jc jq; } ++ [ snowCli ];
          };
        };
      # flake = { };
    };
}
