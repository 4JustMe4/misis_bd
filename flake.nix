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

      redisImageOfficial = ({ dockerTools, ... }: dockerTools.pullImage {
        imageName = "redis";
        imageDigest ="sha256:519f0189dfdee3bc0bad61fb265fe73d864b5c64020e6579ad48a45c49965635";
        os = "linux";
        arch = "x86_64";
        finalImageName = "redis";
        finalImageTag = "alpine3.21";
        sha256 = "sha256-molkn5v2dNVElslcb6wkr9J0dT0Q024Ny7n+u79j6qA=";
      });
      postgresImageOfficial = ({ dockerTools, ... }: dockerTools.pullImage {
        imageName = "postgres";
        imageDigest = "sha256:432de47662e8b0c9dc420487fa54c12cf0b789f424a8cb1504f20b196220b5cd";
        os = "linux";
        arch = "x86_64";
        finalImageName = "postgres";
        finalImageTag = "14.16-alpine3.20";
        sha256 = "sha256-qTnAdADb3VF9fTqVaQO0b3uuqYsny2JZ9iCy1tqcMT4=";
      });
      mongoImageOfficial = ({ dockerTools, ... }: dockerTools.pullImage {
        imageName = "mongo";
        imageDigest = "sha256:0fbe569f105156a412dd7383afdc9d6a784c9acea1367663c384e5e98b2ecc2a";
        os = "linux";
        arch = "x86_64";
        finalImageName = "mongo";
        finalImageTag = "noble";
        sha256 = "sha256-+veJG8vAXIp8huy6ifViQMM9SuB5On5G09r0Yer7knA=";
      });

      pythonEnv = ({ python312, ... }: python312.withPackages (
        pythonPackages: with pythonPackages; [
          aiofiles
          aiogram
          aiohappyeyeballs
          aiohttp
          aiosignal
          annotated-types
          attrs
          certifi
          charset-normalizer
          frozenlist
          idna
          magic-filter
          multidict
          propcache
          pydantic
          pydantic-core
          python-dotenv
          requests
          typing-extensions
          urllib3
          xlrd
          yarl
        ]
      ));

      botImage = ({ dockerTools, buildEnv, python312, ...}@pkgs: dockerTools.buildImage {
        name = "customBotName";
        tag = "latest";
        compressor = "none"; # "gz", "zstd".
        fromImage = null;
        fromImageName = null;
        fromImageTag = "latest";

        copyToRoot = buildEnv {
          name = "image-root";
          paths = [
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


    compresspkg = ({ stdenvNoCC, zstd, ... }: package: stdenvNoCC.mkDerivation {
      src = package; 
      name = package.name + ".tar.zst";
      nativeBuildInputs = [ zstd ];
      buildCommand = ''
        # Create the tar.zst file
        cd $src/
        tar --zstd -cf $out .
      '';
    });

  in rec {
    overlays.default = final: prev: rec {
      system = final.stdenv.hostPlatform.system;
      botPythonEnvironment= prev.callPackage pythonEnv {};
      #botDockerImage      = botImage prev;
      #package1 = with inputs.nixpkgs.legacyPackages.${system}; hello;
      #package1 = prev.hello;
    };

    dockerImages = forAllSystems (system: let
      pkgs = importNixpkgs system;

    in rec {
      redis     = pkgs.callPackage redisImageOfficial {};
      postgres  = pkgs.callPackage postgresImageOfficial {};
      mongo     = pkgs.callPackage mongoImageOfficial {};
      bot = pkgs.callPackage botImage {};
      compose_yaml = pkgs.substituteAll {
        src = ./compose.yaml;
        env = let
          #    <registry>/<project>/<container>:<tag>@<digest>
          # for usual images we use <container>:<tag>@<digest>
          toURI = image: "${image.imageName}:${image.imageTag}@${image.imageDigest}";
        in { # @<name>@ -> ...
          postgres_imageid  = toURI postgres;
          redis_imageid     = toURI redis;
          mongo_imageid     = toURI mongo;
        };
      };
      composed = composed_nodb.overrideAttrs (a: a // {
        installPhase = a.installPhase + ''
          cp -T ${redis} $out/${redis.name}
          cp -T ${postgres} $out/${postgres.name}
          cp -T ${mongo} $out/${mongo.name}
        '';
      });
      composed_nodb = pkgs.stdenvNoCC.mkDerivation {
        name = "docker-compose-bundle";
        #src = self;
        src = compose_yaml;
        #pkgs.lib.fileset.toSource {
        #  root = ./.; #builtins.toPath self;
        #  fileset = pkgs.lib.fileset.union [
        #    ./compose.yaml
        #  ];
        #};
        phases = ["installPhase" ];
        installPhase = ''
          mkdir -p $out
          cp -T ${bot} $out/${bot.name}
          cp -T $src $out/compose.yaml
        '';

        meta = {
          description = "Docker compose bundle with images";
          platforms = pkgs.lib.platforms.all;
        };
      };
      compressed      = (pkgs.callPackage compresspkg {}) composed;
      compressed_nodb = (pkgs.callPackage compresspkg {}) composed_nodb;

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


