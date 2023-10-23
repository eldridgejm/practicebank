{
  description = "Python package for creating banks of practice problems.";

  inputs.nixpkgs.url = github:NixOS/nixpkgs/nixos-23.05;

  outputs = {
    self,
    nixpkgs,
  }: let
    supportedSystems = ["x86_64-linux" "x86_64-darwin" "aarch64-darwin"];
    forAllSystems = f: nixpkgs.lib.genAttrs supportedSystems (system: f system);
  in {
    practicebank = forAllSystems (
      system:
        with import nixpkgs {system = "${system}";};
          python3Packages.buildPythonPackage rec {
            name = "practicebank";
            src = ./.;
            propagatedBuildInputs = with python3Packages; [
              pyyaml

              # texsoup
              (
                pkgs.python3Packages.buildPythonPackage rec {
                  pname = "texsoup";
                  version = "0.3.1";
                  name = "${pname}-${version}";
                  src = builtins.fetchurl {
                    url = "https://files.pythonhosted.org/packages/84/58/1c503390ed1a81cdcbff811dbf7a54132994acef8dd2194d55cf657a9e97/TexSoup-0.3.1.tar.gz";
                    sha256 = "02xpvmhy174z6svpghzq4gs2bsyh0jxc2i7mark8ls73mg82lsrz";
                  };
                  doCheck = false;
                }
              )
            ];
            nativeBuildInputs = with python3Packages; [pytest sphinx sphinx_rtd_theme pip];
            doCheck = true;
          }
    );

    defaultPackage = forAllSystems (
      system:
        self.practicebank.${system}
    );
  };
}
