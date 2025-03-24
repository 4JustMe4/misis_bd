{
  description = "Database-extra project";

  inputs = {
    # release-24.11 2411-250106 3f0a8ac25fb674611b98089ca3a5dd6480175751
    nixpkgs.url = "github:nixos/nixpkgs/3f0a8ac25fb674611b98089ca3a5dd6480175751";
  };

  outputs = { self, nixpkgs, ... }@inputs: let
      supportedSystems = [ "aarch64-darwin" "aarch64-linux" "x86_64-darwin" "x86_64-linux" ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
      importNixpkgs = (system: import inputs.nixpkgs {
        inherit system;
        overlays = [ self.overlays.default ];
      });

      redisImageOfficial = (pkgs: pkgs.dockerTools.pullImage{
        imageName = "redis";
        imageDigest ="sha256:519f0189dfdee3bc0bad61fb265fe73d864b5c64020e6579ad48a45c49965635";
        os = "linux";
        arch = "x86_64";
        finalImageName = "redis";
        finalImageTag = "alpine3.21";
        sha256 = "sha256-molkn5v2dNVElslcb6wkr9J0dT0Q024Ny7n+u79j6qA=";
      });
      postgresImageOfficial = (pkgs: pkgs.dockerTools.pullImage{
        imageName = "postgres";
        imageDigest = "sha256:432de47662e8b0c9dc420487fa54c12cf0b789f424a8cb1504f20b196220b5cd";
        os = "linux";
        arch = "x86_64";
        finalImageName = "postgres";
        finalImageTag = "14.16-alpine3.20";
        sha256 = "sha256-qTnAdADb3VF9fTqVaQO0b3uuqYsny2JZ9iCy1tqcMT4=";
      });

      pythonEnv = (pkgs: pkgs.python312.withPackages (pythonPackages: with pythonPackages; [
        requests
        xlrd

        aiogram
      ]));

      botImage = (pkgs: with pkgs; dockerTools.buildImage {
        name = "customBotName";
        tag = "latest";
        compressor = "none"; # "gz", "zstd".
        fromImage = null;
        fromImageName = null;
        fromImageTag = "latest";

        copyToRoot = pkgs.buildEnv {
          name = "image-root";
          paths = with pkgs; [
            (pythonEnv pkgs) 
            #bash # not-cached
            #fish
          ];
          pathsToLink = [ "/bin" ];
        };

        config = {
          Cmd = [ "/bin/python3" ];
          WorkingDir = "/data";
          Volumes = { "/data" = { }; };
        };

        diskSize = 1024;
        buildVMMemorySize = 512;
      });


  in rec {
    overlays.default = final: prev: rec {
      system = final.stdenv.hostPlatform.system;
      redisDockerImage    = redisImageOfficial prev;
      postgresDockerImage = postgresImageOfficial prev;
      botPythonEnvironment= prev.callPackage pythonEnv {};
      botDockerImage      = botImage prev;
      #package1 = with inputs.nixpkgs.legacyPackages.${system}; hello;
      #package1 = prev.hello;
    };

    dockerImages = forAllSystems (system: let
      pkgs = importNixpkgs system;

    in rec {
      redis = pkgs.redisDockerImage;
      postgres = pkgs.postgresDockerImage;
      bot = pkgs.botDockerImage;
      composed = pkgs.stdenv.mkDerivation {
        name = "docker-compose-bundle";
        #src = self;
        src = pkgs.lib.fileset.toSource {
          root = ./.; #builtins.toPath self;
          fileset = pkgs.lib.fileset.unions [
            ./compose.yaml
          ];
        };
        phases = [ "unpackPhase" "installPhase" ];
        installPhase = ''
          mkdir -p $out
          cp -T ${redis} $out/${redis.name}
          cp -T ${postgres} $out/${postgres.name}
          cp -T ${bot} $out/${bot.name}
          cp -r $src/compose.yaml $out/
        '';

        meta = {
          description = "Docker compose bundle with images";
          platforms = pkgs.lib.platforms.all;
        };
      };
    });

    devShells = forAllSystems (system: let
      pkgs = importNixpkgs system;
      libPath = with pkgs; lib.makeLibraryPath [
        # load external libraries that you need in your rust project here
      ];
    in rec {
      default = let
        helpers = with pkgs; [ direnv jq docker-compose ];
      in pkgs.mkShell {
        buildInputs = [
        ];
        packages = helpers ++ (with pkgs; [
            (pythonEnv pkgs)
        ]);
      };
    });
  };
}


