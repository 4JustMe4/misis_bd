{
  description = "Database-extra project";

  inputs = {
    # release-24.11 2411-250106 3f0a8ac25fb674611b98089ca3a5dd6480175751
    #nixpkgs.url = "github:nixos/nixpkgs/3f0a8ac25fb674611b98089ca3a5dd6480175751";
    # release-24.11 2411-250330 419ea68a83290cfc41514d9474faa0e06b332346
    nixpkgs.url = "github:nixos/nixpkgs/419ea68a83290cfc41514d9474faa0e06b332346";
  };

  outputs = { self, nixpkgs, ... }@inputs: let
      #supportedSystems = [ "aarch64-darwin" "aarch64-linux" "x86_64-darwin" "x86_64-linux" ];
      supportedSystems = [ "x86_64-linux" ]; # only x86_64 is currently defined
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
      importNixpkgs = (system: import inputs.nixpkgs {
        inherit system;
        overlays = [ self.overlays.default ];
      });

      alpineImageOfficial = ({ dockerTools, ... }: dockerTools.pullImage {
        imageName = "alpine";
        imageDigest ="sha256:1c4eef651f65e2f7daee7ee785882ac164b02b78fb74503052a26dc061c90474";
        os = "linux";
        arch = "x86_64";
        finalImageName = "alpine";
        finalImageTag = "3.21.3";
        sha256 = "sha256-BLd0y9w1FIBJO5o4Nu5Wuv9dtGhgvh+gysULwnR9lOo=";
      });
      redisImageOfficial = ({ dockerTools, ... }: dockerTools.pullImage {
        imageName = "redis";
        imageDigest ="sha256:519f0189dfdee3bc0bad61fb265fe73d864b5c64020e6579ad48a45c49965635";
        os = "linux";
        arch = "x86_64";
        finalImageName = "redis";
        finalImageTag = "7.4.2-alpine3.21";
        sha256 = "sha256-OLdmIch4dPgLVnuVOdbljtWZyDKJszGA1T8OnjKhauc=";
      });
      redisStackServerImageOfficial = ({ dockerTools, ... }: dockerTools.pullImage {
        imageName = "redis/redis-stack-server";
        imageDigest ="sha256:a8d64e9f5bc99dc83f2a807a93f44d59efab0d2c4f09cff03f01b8753842e0cc";
        os = "linux";
        arch = "x86_64";
        finalImageName = "redis/redis-stack-server";
        finalImageTag = "7.4.0-v3";
        sha256 = "sha256-aJXDbqFgdj9WD71b84h7wu1B6w14QNjCpxk7HjmilTk=";
      });

      postgresImageOfficial = ({ dockerTools, ... }: dockerTools.pullImage {
        imageName = "postgres";
        imageDigest = "sha256:0ae695e3d11c7cc82cbed8f3e506233f18cdd40e3fc7622893f6a4d0772a5a09";
        os = "linux";
        arch = "x86_64";
        finalImageName = "postgres";
        finalImageTag = "17.4-alpine3.21";
        sha256 = "sha256-S+MBad6gRuDxLIXqk1P8XJxJjdWWCQToMkGIOUq6g4Y=";
      });
      mongoImageOfficial = ({ dockerTools, ... }: dockerTools.pullImage {
        imageName = "mongo";
        imageDigest = "sha256:3633d9020777dbfe548792a7372a193560d1fecce9fd50892612420e85d601c3";
        os = "linux";
        arch = "x86_64";
        finalImageName = "mongo";
        finalImageTag = "8.0.8-noble";
        sha256 = "sha256-m/SDhK337rT92M/rZXu5FPylkORneqOpaSdq3ZwGgZg=";
      });

      pythonEnv = ({ python312, ... }: python312.withPackages (
        pythonPackages: with pythonPackages; [
          aiofiles
          aiogram
          pymongo
          psycopg
          redis
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

      pythonFiles = { stdenvNoCC, ... }: stdenvNoCC.mkDerivation {
        name = "tgbot-files";
        src = self;
        installPhase = ''
          mkdir -p $out
          cp -Tr $src/bot_v3 $out/bot_srv
          cp -Tr $src/parser $out/bot_parser
        '';
      };

      botImage = ({ lib, stdenvNoCC, dockerTools, buildEnv, python312, ...}@pkgs: let
        lastModifyDate = lib.substring 0 8 self.lastModifiedDate;
        lastModifyTime = lib.substring 8 14 self.lastModifiedDate;
        tagPart2 = lib.substring 0 8 (self.rev or lastModifyTime);
        imageName = "tgbot";
        # YYYYMMDD-<commit-part> or YYYYMMDD-hhmmss
        imageTag = "${lastModifyDate}-${tagPart2}"; 
      in (dockerTools.buildLayeredImage {
          name = imageName;
          # if unset, tag by default refers to the nix input content hash
          tag = imageTag;
          created = lastModifyDate; # YYYYMMDD
          compressor = "none"; # "gz", "zstd".

          maxLayers = 16;
          contents = [
            dockerTools.binSh
            #dockerTools.usrBinEnv
            (pythonFiles pkgs)
            (buildEnv {
              name = "image-root";
              paths = [
                (pythonEnv pkgs) 
              ];
              pathsToLink = [ "/bin" ];
            })
          ];

          config = {
            Cmd = [ "/bin/python3" "./main.py" ];
            WorkingDir = "/bot_srv";
            #Volumes = { "/data" = { }; };
          };

          #diskSize = 1024;
          #buildVMMemorySize = 512;
        }).overrideAttrs (a: a // {
          name = "docker-image-${imageName}-${imageTag}.tar";
        })
      );

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
      alpine    = pkgs.callPackage alpineImageOfficial {};
      redis     = pkgs.callPackage redisImageOfficial {};
      redis-stack-server  = pkgs.callPackage redisStackServerImageOfficial {};
      postgres  = pkgs.callPackage postgresImageOfficial {};
      mongo     = pkgs.callPackage mongoImageOfficial {};
      tgbot = pkgs.callPackage botImage {};
      compose_yaml = pkgs.substituteAll {
        src = ./compose.yaml;
        env = let
          #    <registry>/<project>/<container>:<tag>@<digest>
          # for usual images we use <container>:<tag>@<digest>
          toURI = image: "${image.imageName}:${image.imageTag}@${image.imageDigest}";
          toURInoDigest = image: "${image.imageName}:${image.imageTag}";
        in { # @<name>@ -> ...
          alpine_imageid    = toURI alpine;
          redis_imageid     = toURI redis-stack-server;
          postgres_imageid  = toURI postgres;
          mongo_imageid     = toURI mongo;
          tgbot_imageid     = toURInoDigest tgbot;
        };
      };
      composed = composed_nodb.overrideAttrs (a: a // {
        installPhase = a.installPhase + ''
          cp -T ${alpine} $out/${alpine.name}
          cp -T ${redis-stack-server} $out/${redis-stack-server.name}
          cp -T ${postgres} $out/${postgres.name}
          cp -T ${mongo} $out/${mongo.name}
        '';
      });
      composed_nodb = pkgs.stdenvNoCC.mkDerivation {
        name = "docker-compose-bundle";
        #src = self;
        #src = compose_yaml;
        src = pkgs.lib.fileset.toSource {
          root = ./.; #builtins.toPath self;
          fileset = pkgs.lib.fileset.unions [
            ./defaults.env
            ./compose.prod.yaml
            ./compose.test.yaml
          ];
        };
        phases = ["installPhase" ];
        installPhase = ''
          mkdir -p $out
          cp -T ${tgbot} $out/${tgbot.name}
          cp -T ${compose_yaml} $out/compose.yaml
          cp $src/defaults.env $out/
          cp $src/compose.*.yaml $out/
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


