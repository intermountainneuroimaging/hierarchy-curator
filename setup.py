"""Custom Curator"""

import os
from setuptools import setup, find_packages

NAME = "custom-curator"
VERSION = os.getenv("CI_COMMIT_TAG", "0.1.0.dev")

with open('requirements.txt') as f:
    install_requires = f.read().splitlines()

setup(
    name=NAME,
    version=VERSION,
    description="Custom Curation Gear",
    project_urls={"Source": "https://github.com/flywheel-apps/custom-curator"},
    install_requires=install_requires,
    packages=find_packages(),
)
