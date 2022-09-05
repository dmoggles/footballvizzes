"""Install packages as defined in this file into the Python environment."""
from typing import Any, Dict
from setuptools import setup, find_namespace_packages

# The version of this tool is based on the following steps:
# https://packaging.python.org/guides/single-sourcing-package-version/
VERSION: Dict[str, Any] = {}

with open("./src/fb_viz/version.py") as fp:
    # pylint: disable=W0122
    exec(fp.read(), VERSION)

setup(
    name="fb_viz",
    author="Dmitry Mogilevsky",
    author_email="dmitry.mogilevsky@gmail.com",
    description="Football Visualisation Tools",
    version=VERSION.get("__version__", "0.0.0"),
    package_dir={"": "src"},
    packages=find_namespace_packages(where="src", exclude=["tests"]),
    install_requires=[
        "setuptools>=45.0",
        "pandas",
        "requests",
        "mplsoccer",
        "seaborn",
        "sklearn",
        "git+http://github.com/dmoggles/footmav",
        "scipy",
    ],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Programming Language :: Python :: 3.0",
        "Topic :: Utilities",
    ],
)
