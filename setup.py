from pathlib import Path
from setuptools import setup

this_dir = Path(__file__).parent

readme = (this_dir / "README.md").read_text()
with open(this_dir / "requirements.txt") as deps_fobj:
    deps = deps_fobj.readlines()


setup(
    name="rentrylib",
    version="1.0.0",
    url="https://github.com/yntha/rentrylib",
    license="EPL-1.0",
    author="anthy",
    long_description=readme,
    long_description_content_type="text/markdown",
    install_requires=deps,
    author_email="bguznvjk@gmail.com",
    description="A python library for interfacing with the paste-site https://rentry.org",
)
