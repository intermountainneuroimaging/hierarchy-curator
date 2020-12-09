import argparse
import importlib
import logging
import sys
from pathlib import Path

import flywheel
from flywheel_gear_toolkit import GearToolkitContext
from flywheel_gear_toolkit.utils import datatypes, walker

log = logging.getLogger(__name__)


def load_curator(curator_path: datatypes.PathLike):
    """Load curator from the file, return the module.

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
            ## Investigate import statement
            mod = importlib.import_module(curator_path.name.split(".")[0])
            mod.filename = str(curator_path)
        finally:
            sys.path = old_syspath
    else:
        mod = None

    return mod


def get_curator(
    context: GearToolkitContext,
    curator_path: datatypes.PathLike,
    write_report: bool = False,
    **kwargs
):
    """Returns an instantiated curator

    Args:
        client (flywheel.Client): The flywheel sdk client.
        curator_path (Path-like): A path to a curator module.
        **kwargs: Extra keyword arguments.
    """
    curator_mod = load_curator(curator_path)
    curator = curator_mod.Curator(context=context, write_report=write_report, **kwargs)

    return curator


def main(
    context: GearToolkitContext,
    parent: datatypes.Container,
    curator_path: datatypes.PathLike,
    **kwargs
):
    """Curates a flywheel project using a curator.

    Args:
        client (flywheel.Client): The flywheel sdk client.
        project (flywheel.Project): The project to curate.
        curator_path (Path-like): A path to a curator module.
        kwargs (dict): Dictionary of attributes/value to set on curator.
    """
    curator = get_curator(context, curator_path, **kwargs)

    project_walker = walker.Walker(parent, depth_first=curator.depth_first)
    try:
        for container in project_walker.walk():  # pragma: no cover
            curator.curate_container(container)  # Tested in gear toolkit
    except Exception:
        log.error("Uncaught Exception", exc_info=True)
        curator.__del__()


if __name__ == "__main__":  # pragma: no cover
    parser = argparse.ArgumentParser(description="Argument parser for curation")
    parser.add_argument(
        "--api-key", default=None, help="Pass in api key if not logged in with cli"
    )
    parser.add_argument(
        "--curator", "-c", required=True, help="path to curator implementation"
    )
    parser.add_argument("--input-file-one", help="Input file one")
    parser.add_argument("--input-file-two", help="Input file two")
    parser.add_argument("--input-file-three", help="Input file three")
    parser.add_argument("path", help="The resolver path to the project")

    args = parser.parse_args()
    client = flywheel.Client(args.api_key)
    project = client.lookup(args.path)
    main(
        client,
        project,
        args.curator,
        input_file_one=args.input_file_one,
        input_file_two=args.input_file_two,
        input_file_three=args.input_file_three,
    )
