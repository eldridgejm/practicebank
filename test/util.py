import pathlib

import yaml

class Example:
    def __init__(self, root):
        self.root = pathlib.Path(root)
        self.root.mkdir()

    def write_config(self, contents: dict):
        with (self.root / "practicebank.yaml").open("w") as fileob:
            yaml.dump(
                contents,
                fileob,
            )

    def write_problem(
        self, identifier: str, format: str, contents: str, exist_ok=False
    ):
        (self.root / identifier).mkdir(exist_ok=exist_ok)

        match format:
            case "dsctex":
                extension = ".tex"
            case "gsmd":
                extension = ".md"
            case _:
                raise ValueError(f"Unknown format: {format}")

        with (self.root / identifier / f"problem{extension}").open("w") as fileob:
            fileob.write(contents)
