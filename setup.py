"""Custom Curator"""

import os
from setuptools import setup, find_packages

NAME = "custom-curator"
VERSION = os.getenv("0.1.0.dev")

setup(
    name=NAME,
    version=VERSION,
    description="Custom Curation Gear",
    project_urls={"Source": "https://github.com/flywheel-apps/custom-curator"},
    install_requires=[
        "flywheel-gear-toolkit==0.1.0rc4",
        "lxml~=4.5",
        "nibabel~=3.1",
        "pandas~=1.0",
        "Pillow~=7.1",
        "piexif~=1.1",
        "pydicom~=2.0",
        "pypng~=0.0.20",
    ],
    packages=find_packages(),
)
