"""coBib's API generation."""

import argparse
import sys
from pathlib import Path
from textwrap import dedent

sys.path.insert(0, ".")

from theme.build import build_html  # type: ignore[import-not-found]

MODULES = [
    Path("src/cobib"),
    Path("plugin/src/cobib_dummy"),
    Path("tests"),
]

parser = argparse.ArgumentParser()
parser.add_argument(
    "modules",
    type=Path,
    nargs="*",
    default=MODULES,
    help="The paths to the modules to document.",
)
args = parser.parse_args()

generator = build_html(args.modules)

for module_name, module, out in generator:
    if out is None:
        # yielded during pre-processing
        if module_name == "cobib.commands.tutorial":
            # manually add the tutorial instructions as docstrings to the TutorialCommand.State Enum
            from cobib.commands import TutorialCommand

            for state in TutorialCommand.State:
                module.get(f"TutorialCommand.{state}").docstring = dedent(state.value)

    else:  # noqa: PLR5501
        # yielded during rendering
        if module_name == "cobib":
            # apply a fix to the ToC due to the man-page insertion on the main module page
            lines = out.splitlines()
            for idx, line in enumerate(lines):
                if "#NAME" in line:
                    lines[idx : idx + 2] = lines[idx : idx + 2][::-1]
                    break
            generator.send("\n".join(lines))

generator.close()
