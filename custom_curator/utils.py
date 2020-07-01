import os
from pathlib import Path
import sys
from typing import Union

import flywheel

# Typing shortcut
Container = Union[
    flywheel.Project,
    flywheel.Subject,
    flywheel.Session,
    flywheel.Acquisition,
    flywheel.FileEntry,
    flywheel.AnalysisOutput,
]

PathLike = Union[str, os.PathLike, Path]


def load_converter(curator_path: Union[str, os.PathLike, Path]):
    """Load converter from the file, return the module.

    Args:
        curator_path (Path-like): Path to curator script.

    Returns:
        (module): A python module.
    """
    if isinstance(curator_path, str):
        curator_path = Path(curator_path).resolve()
    if curator_path.is_file():
        old_syspath = sys.path[:]
        try:
            sys.path.append(str(curator_path.parent))
            mod = __import__(curator_path.name.split(".")[0])
            mod.filename = str(curator_path)
        finally:
            sys.path = old_syspath
    else:
        mod = None

    return mod
