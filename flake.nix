{
  description = "Python package for creating banks of practice problems.";

  inputs.nixpkgs.url = github:NixOS/nixpkgs/nixos-23.05;

  inputs.panprob.url = github:eldridgejm/panprob/0.1.5;
  inputs.panprob.inputs.nixpkgs.follows = "nixpkgs";

  inputs.dictconfig.url = github:eldridgejm/dictconfig/master;
  inputs.dictconfig.inputs.nixpkgs.follows = "nixpkgs";

  outputs = {
    self,
    nixpkgs,
    panprob,
    dictconfig,
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
              rich
              panprob.defaultPackage.${system}
              dictconfig.defaultPackage.${system}
            ];
            nativeBuildInputs = (with python3Packages; [pytest sphinx pip]) ++ [(python3Packages.sphinx-rtd-theme or python3Packages.sphinx_rtd_theme)];
            pyproject = true;
            build-system = [ python3Packages.setuptools ];
            doCheck = true;
          }
    );

    # Export a truly isolated application (only bin/, no propagatedBuildInputs)
    # This prevents PYTHONPATH pollution when used in mkShell buildInputs
    defaultPackage = forAllSystems (
      system:
        let
          pkgs = import nixpkgs {system = "${system}";};
          app = pkgs.python3Packages.toPythonApplication self.practicebank.${system};
        in
          pkgs.runCommand "practicebank" {
            meta = app.meta or {};
          } ''
            mkdir -p $out/bin
            for f in ${app}/bin/*; do
              ln -s "$f" $out/bin/
            done
          ''
    );

    # Export the library form for consumers who need it as a Python dependency
    lib = forAllSystems (
      system:
        self.practicebank.${system}
    );
  };
}
