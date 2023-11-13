{
  description = "Python package for creating banks of practice problems.";

  inputs.nixpkgs.url = github:NixOS/nixpkgs/nixos-23.05;

  inputs.panprob.url = github:eldridgejm/panprob/main;

  outputs = {
    self,
    nixpkgs,
    panprob
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
              panprob.defaultPackage.${system}
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
