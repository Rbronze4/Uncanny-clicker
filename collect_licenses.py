"""Copy the licenses of the actual build environment into the portable app."""
from importlib.metadata import distribution
from pathlib import Path
import shutil
import sys

target = Path(sys.argv[1] if len(sys.argv) > 1 else "dist/UncannyClicker/licenses")
target.mkdir(parents=True, exist_ok=True)
shutil.copytree("assets/licenses", target / "additional", dirs_exist_ok=True)
shutil.copy2(Path(sys.base_prefix) / "LICENSE.txt", target / "Python-LICENSE.txt")
for name in ("customtkinter", "darkdetect", "packaging", "pyinstaller"):
    package = distribution(name)
    for entry in package.files or []:
        if entry.name.lower().startswith(("license", "copying")):
            source = Path(package.locate_file(entry))
            if source.is_file():
                dest = target / name / Path(str(entry))
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, dest)
