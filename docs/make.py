"""coBib's API generation."""

import argparse
from pathlib import Path
from textwrap import dedent

import pdoc

from cobib.commands import TutorialCommand

ROOT = Path(__file__).parent

MODULES = [
    Path("src/cobib"),
    Path("plugin/src/cobib_dummy"),
    Path("tests"),
]

parser = argparse.ArgumentParser()
parser.add_argument(
    "modules",
    type=Path,
    default=[ROOT.parent / module for module in MODULES],
    nargs="*",
)
args = parser.parse_args()

pdoc.render.configure(
    docformat="google",
    edit_url_map={
        module.name: f"https://gitlab.com/cobib/cobib/-/blob/master/{module}/" for module in MODULES
    },
    template_directory=ROOT / "jinja",
)

output_directory = ROOT.parent / "build/html"

all_modules = {}
for module_name in pdoc.extract.walk_specs(args.modules):
    module = pdoc.doc.Module.from_name(module_name)

    if module_name == "cobib.commands.tutorial":
        # manually add the tutorial instructions as docstrings to the TutorialCommand.State Enum
        for state in TutorialCommand.State:
            module.get(f"TutorialCommand.{state}").docstring = dedent(state.value)

    all_modules[module_name] = module

for module_name, module in all_modules.items():
    out = pdoc.render.html_module(module, all_modules)

    outfile = output_directory / f"{module.fullname.replace('.', '/')}.html"
    outfile.parent.mkdir(parents=True, exist_ok=True)
    outfile.write_bytes(out.encode())

index = pdoc.render.html_index(all_modules)
(output_directory / "index.html").write_bytes(index.encode())

search = pdoc.render.search_index(all_modules)
(output_directory / "search.js").write_bytes(search.encode())

# apply a fix to the ToC due to the man-page insertion on the main module page
with open(output_directory / "cobib.html", "r", encoding="utf-8") as file:
    lines = file.readlines()

for idx, line in enumerate(lines):
    if "#NAME" in line:
        lines[idx : idx + 2] = lines[idx : idx + 2][::-1]
        break

with open(output_directory / "cobib.html", "w", encoding="utf-8") as file:
    file.writelines(lines)
