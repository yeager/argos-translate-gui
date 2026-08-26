import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from setuptools import find_packages, setup
from setuptools.command.build_py import build_py


class BuildPyWithTranslations(build_py):
    """Compile Qt TS catalogs into the build directory."""

    def run(self):
        super().run()
        lrelease = shutil.which("pyside6-lrelease") or shutil.which("lrelease")
        if not lrelease:
            try:
                from PyQt5.QtCore import QLibraryInfo

                bundled = Path(QLibraryInfo.location(QLibraryInfo.BinariesPath)) / "lrelease"
                if bundled.is_file():
                    lrelease = str(bundled)
            except (ImportError, AttributeError):
                pass
        if not lrelease:
            raise RuntimeError("Qt lrelease is required to build translations")

        source_dir = Path(__file__).parent / "translations"
        output_dir = Path(self.build_lib) / "argostranslategui" / "translations"
        output_dir.mkdir(parents=True, exist_ok=True)
        for catalog in sorted(source_dir.glob("argos_translate_*.ts")):
            messages = ET.parse(catalog).getroot().findall(".//message")
            translated = sum(
                1
                for message in messages
                if (translation := message.find("translation")) is not None
                and translation.get("type") != "unfinished"
                and "".join(translation.itertext()).strip()
            )
            if not messages or translated / len(messages) <= 0.20:
                self.announce(
                    f"Skipping {catalog.name}: {translated}/{len(messages)} translated",
                    level=2,
                )
                continue
            output = output_dir / catalog.with_suffix(".qm").name
            subprocess.run([lrelease, str(catalog), "-qm", str(output)], check=True)

with open("requirements.txt") as f:
    required_packages = f.read().splitlines()

with open("README.md") as f:
    long_description = f.read()

# py2app
APP = ["bin/argos-translate-gui"]
DATA_FILES = []
OPTIONS = {"packages": ["sentencepiece"], "iconfile": "argostranslate/img/icon.icns"}

setup(
    name="argostranslategui",
    version="1.6.5",
    description="Graphical user interface for Argos Translate",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Argos Open Technologies, LLC",
    author_email="admin@argosopentech.com",
    url="https://www.argosopentech.com",
    packages=find_packages(),
    install_requires=required_packages,
    include_package_data=True,
    scripts=["bin/argos-translate-gui"],
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"] if sys.platform == "darwin" else [],
    cmdclass={"build_py": BuildPyWithTranslations},
)
